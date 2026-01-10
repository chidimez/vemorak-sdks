import time
from typing import Any

import httpx

from .errors import VemorakSdkError, VmpHttpError, VmpTimeoutError
from .types import (
    AdminBatchItem,
    AdminDeletionReceiptItem,
    AdminEventItem,
    AdminListBatchesResponse,
    AdminListDeletionReceiptsResponse,
    AdminListEventsResponse,
    AdminStatsResponse,
    DeleteResponse,
    DeletionReceiptBundleResponse,
    DeletionReceiptBundleVerification,
    DeletionReceiptResponse,
    EventBundleEvent,
    EventBundleRecompute,
    EventBundleResponse,
    IngestResponse,
    ProofPathItem,
    ProofResponse,
    ProvisionCreateKeyResponse,
    ProvisionListKeyItem,
    ProvisionListKeysResponse,
    ProvisionRevokeKeyResponse,
    PubkeyResponse,
    VerifyBundleResponse,
    VerifyDeletionResponse,
    WaitForBatchOptions,
    WhoAmIResponse,
)
from .validate import (
    assert_limit,
    assert_non_empty,
    assert_scope,
    assert_scope_matches_prefix,
    assert_scope_prefix,
    assert_tenant_id,
    assert_uuid_like,
)


class VmpClient:
    """
    Strict Python SDK for the VMP Rust HTTP API.

    - Auth: Authorization: Bearer <TENANT_API_KEY>
    - Tenant binding enforced by VMP; SDK optionally provides a local guardrail.
    - Optional local scope_prefix guardrail (mirrors server rule Option B).
    """

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        tenant_id: str | None = None,
        timeout_ms: int = 15_000,
        scope_prefix: str | None = None,  # optional local guardrail
    ) -> None:
        assert_non_empty("base_url", base_url)
        assert_non_empty("api_key", api_key)

        if scope_prefix is not None:
            assert_scope_prefix(scope_prefix)

        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._tenant_guardrail = tenant_id
        self._scope_prefix_guardrail = scope_prefix
        self._timeout = httpx.Timeout(timeout_ms / 1000.0)

        self._client = httpx.Client(
            base_url=self._base_url,
            timeout=self._timeout,
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {self._api_key}",
            },
        )

    def close(self) -> None:
        self._client.close()

    def _enforce_tenant(self, tenant_id: str) -> None:
        assert_tenant_id(tenant_id)
        if self._tenant_guardrail and tenant_id != self._tenant_guardrail:
            raise VemorakSdkError(
                f"tenant_id mismatch: client is configured for {self._tenant_guardrail} but request used {tenant_id}"
            )

    def _enforce_scope_prefix(self, scope: str) -> None:
        if self._scope_prefix_guardrail is None:
            return
        assert_scope_matches_prefix(scope, self._scope_prefix_guardrail)

    def _request_json(
        self,
        method: str,
        path: str,
        *,
        query: dict[str, Any] | None = None,
        body: dict[str, Any] | None = None,
        idempotency_key: str | None = None,
        auth: bool = True,
    ) -> dict[str, Any]:
        headers: dict[str, str] = {"Accept": "application/json"}

        if auth:
            headers["Authorization"] = f"Bearer {self._api_key}"

        if idempotency_key:
            headers["x-idempotency-key"] = idempotency_key

        try:
            resp = self._client.request(
                method,
                path,
                params=query,
                json=body if method.upper() != "GET" else None,
                headers=headers,
            )
        except httpx.TimeoutException as e:
            raise VmpTimeoutError("VMP request timed out") from e

        text = resp.text or ""

        if resp.status_code < 200 or resp.status_code >= 300:
            err_str = text.strip() or "unknown error"
            details = None

            try:
                parsed = resp.json()
                if isinstance(parsed, dict):
                    if isinstance(parsed.get("error"), str):
                        err_str = parsed["error"]
                    details = parsed.get("details")
            except Exception:
                pass

            raise VmpHttpError(
                status=resp.status_code,
                error=err_str,
                details=details,
                raw_body_text=text,
            )

        if not text.strip():
            return {}

        return resp.json()

    # -------------------
    # Auth / introspection
    # -------------------

    def whoami(self) -> WhoAmIResponse:
        data = self._request_json("GET", "/v1/whoami", auth=True)
        return WhoAmIResponse(
            tenant_id=data["tenant_id"],
            key_id=str(data["key_id"]),
            allowed_scopes=list(data.get("allowed_scopes") or []),
            scope_prefix=data.get("scope_prefix"),
        )

    # -------------------
    # Core endpoints
    # -------------------

    def ingest(
        self,
        *,
        tenant_id: str,
        scope: str,
        fields: dict[str, Any],
        meta: dict[str, Any] | None = None,
        op: str = "write",
        idempotency_key: str | None = None,
    ) -> IngestResponse:
        self._enforce_tenant(tenant_id)
        assert_scope(scope)
        self._enforce_scope_prefix(scope)

        payload = {
            "tenant_id": tenant_id,
            "scope": scope,
            "op": op,
            "fields": fields,
            "meta": meta or {},
        }

        data = self._request_json("POST", "/v1/ingest", body=payload, idempotency_key=idempotency_key)

        return IngestResponse(
            event_id=data["event_id"],
            event_hash_hex=data["event_hash_hex"],
            prev_hash_hex=data.get("prev_hash_hex"),
            created_at=data["created_at"],
        )

    def delete(
        self,
        *,
        tenant_id: str,
        scope: str,
        target_event_id: str,
        meta: dict[str, Any] | None = None,
    ) -> DeleteResponse:
        self._enforce_tenant(tenant_id)
        assert_scope(scope)
        self._enforce_scope_prefix(scope)
        assert_uuid_like("target_event_id", target_event_id)

        payload = {
            "tenant_id": tenant_id,
            "scope": scope,
            "target_event_id": target_event_id,
            "meta": meta or {},
        }

        data = self._request_json("POST", "/v1/delete", body=payload)

        return DeleteResponse(
            delete_event_id=data["delete_event_id"],
            delete_event_hash_hex=data["delete_event_hash_hex"],
            receipt_id=data["receipt_id"],
            receipt_sig_base64=data["receipt_sig_base64"],
            pubkey_id=data["pubkey_id"],
            pubkey_base64=data["pubkey_base64"],
            pubkey_hex=data["pubkey_hex"],
            created_at=data["created_at"],
        )

    def get_proof(self, event_id: str) -> ProofResponse:
        assert_uuid_like("event_id", event_id)
        data = self._request_json("GET", f"/v1/proof/{event_id}")

        raw_path = data.get("path") or []
        path_items = [
            ProofPathItem(
                sibling_hex=item["sibling_hex"],
                sibling_is_left=bool(item["sibling_is_left"]),
            )
            for item in raw_path
        ]

        return ProofResponse(
            event_id=data["event_id"],
            tenant_id=data["tenant_id"],
            scope=data["scope"],
            batch_id=data.get("batch_id"),
            leaf_index=data.get("leaf_index"),
            leaf_hex=data.get("leaf_hex"),
            root_hex=data.get("root_hex"),
            path=path_items,
            sig_base64=data.get("sig_base64"),
            pubkey_id=data.get("pubkey_id"),
            pubkey_base64=data.get("pubkey_base64"),
            pubkey_hex=data.get("pubkey_hex"),
            batch_created_at=data.get("batch_created_at"),
        )

    def wait_for_batch(self, event_id: str, opts: WaitForBatchOptions | None = None) -> ProofResponse:
        options = opts or WaitForBatchOptions()
        deadline = time.time() + (options.timeout_ms / 1000.0)

        while True:
            proof = self.get_proof(event_id)
            if proof.batch_id is not None:
                return proof

            if time.time() > deadline:
                raise VemorakSdkError(f"wait_for_batch timed out for event_id={event_id}")

            time.sleep(options.poll_interval_ms / 1000.0)

    def get_deletion_receipt(self, receipt_id: str) -> DeletionReceiptResponse:
        assert_uuid_like("receipt_id", receipt_id)
        data = self._request_json("GET", f"/v1/deletion-receipts/{receipt_id}")

        return DeletionReceiptResponse(
            receipt_id=data["receipt_id"],
            tenant_id=data["tenant_id"],
            scope=data["scope"],
            delete_event_id=data["delete_event_id"],
            delete_event_hash_hex=data["delete_event_hash_hex"],
            sig_base64=data["sig_base64"],
            pubkey_id=data["pubkey_id"],
            pubkey_base64=data["pubkey_base64"],
            pubkey_hex=data["pubkey_hex"],
            created_at=data["created_at"],
        )

    def verify_deletion(self, receipt_id: str) -> VerifyDeletionResponse:
        assert_uuid_like("receipt_id", receipt_id)
        data = self._request_json("GET", f"/v1/verify-deletion/{receipt_id}")

        return VerifyDeletionResponse(
            receipt_id=data["receipt_id"],
            valid=bool(data["valid"]),
            tenant_id=data["tenant_id"],
            scope=data["scope"],
            delete_event_id=data["delete_event_id"],
            delete_event_hash_hex=data["delete_event_hash_hex"],
            pubkey_id=data["pubkey_id"],
            pubkey_base64=data["pubkey_base64"],
            pubkey_hex=data["pubkey_hex"],
            created_at=data["created_at"],
        )

    # -------------------
    # Bundles
    # -------------------

    def get_event_bundle(self, event_id: str) -> EventBundleResponse:
        assert_uuid_like("event_id", event_id)
        data = self._request_json("GET", f"/v1/events/{event_id}/bundle")

        ev = data["event"]
        proof = data["proof"]
        recompute = data["recompute"]

        proof_path = proof.get("path") or []
        proof_path_items = [
            ProofPathItem(sibling_hex=p["sibling_hex"], sibling_is_left=bool(p["sibling_is_left"]))
            for p in proof_path
        ]

        proof_obj = ProofResponse(
            event_id=proof["event_id"],
            tenant_id=proof["tenant_id"],
            scope=proof["scope"],
            batch_id=proof.get("batch_id"),
            leaf_index=proof.get("leaf_index"),
            leaf_hex=proof.get("leaf_hex"),
            root_hex=proof.get("root_hex"),
            path=proof_path_items,
            sig_base64=proof.get("sig_base64"),
            pubkey_id=proof.get("pubkey_id"),
            pubkey_base64=proof.get("pubkey_base64"),
            pubkey_hex=proof.get("pubkey_hex"),
            batch_created_at=proof.get("batch_created_at"),
        )

        event_obj = EventBundleEvent(
            id=ev["id"],
            tenant_id=ev["tenant_id"],
            scope=ev["scope"],
            op=ev["op"],
            created_at=ev["created_at"],
            fields=ev.get("fields") or {},
            meta=ev.get("meta") or {},
            event_hash_hex=ev["event_hash_hex"],
            prev_hash_hex=ev.get("prev_hash_hex"),
            fields_canon=ev["fields_canon"],
            meta_canon=ev["meta_canon"],
            c_fields_hex=ev["c_fields_hex"],
            batch_id=ev.get("batch_id"),
            leaf_index=ev.get("leaf_index"),
        )

        recompute_obj = EventBundleRecompute(
            recomputed_event_hash_hex=recompute["recomputed_event_hash_hex"],
            matches_stored=bool(recompute["matches_stored"]),
        )

        return EventBundleResponse(
            kind=data["kind"],
            event=event_obj,
            proof=proof_obj,
            recompute=recompute_obj,
        )

    def get_deletion_receipt_bundle(self, receipt_id: str) -> DeletionReceiptBundleResponse:
        assert_uuid_like("receipt_id", receipt_id)
        data = self._request_json("GET", f"/v1/deletion-receipts/{receipt_id}/bundle")

        receipt = data["receipt"]
        ver = data["verification"]
        delete_event_bundle = data["delete_event_bundle"]

        receipt_obj = DeletionReceiptResponse(
            receipt_id=receipt["receipt_id"],
            tenant_id=receipt["tenant_id"],
            scope=receipt["scope"],
            delete_event_id=receipt["delete_event_id"],
            delete_event_hash_hex=receipt["delete_event_hash_hex"],
            sig_base64=receipt["sig_base64"],
            pubkey_id=receipt["pubkey_id"],
            pubkey_base64=receipt["pubkey_base64"],
            pubkey_hex=receipt["pubkey_hex"],
            created_at=receipt["created_at"],
        )

        ver_obj = DeletionReceiptBundleVerification(
            receipt_id=ver["receipt_id"],
            valid=bool(ver["valid"]),
        )

        # Reuse parsing by calling get_event_bundle-style parsing inline:
        # To keep this strict and minimal, parse delete_event_bundle with helper:
        bundle_obj = self._parse_event_bundle_from_dict(delete_event_bundle)

        return DeletionReceiptBundleResponse(
            kind=data["kind"],
            receipt=receipt_obj,
            verification=ver_obj,
            delete_event_bundle=bundle_obj,
        )

    def _parse_event_bundle_from_dict(self, data: dict[str, Any]) -> EventBundleResponse:
        ev = data["event"]
        proof = data["proof"]
        recompute = data["recompute"]

        proof_path = proof.get("path") or []
        proof_path_items = [
            ProofPathItem(sibling_hex=p["sibling_hex"], sibling_is_left=bool(p["sibling_is_left"]))
            for p in proof_path
        ]

        proof_obj = ProofResponse(
            event_id=proof["event_id"],
            tenant_id=proof["tenant_id"],
            scope=proof["scope"],
            batch_id=proof.get("batch_id"),
            leaf_index=proof.get("leaf_index"),
            leaf_hex=proof.get("leaf_hex"),
            root_hex=proof.get("root_hex"),
            path=proof_path_items,
            sig_base64=proof.get("sig_base64"),
            pubkey_id=proof.get("pubkey_id"),
            pubkey_base64=proof.get("pubkey_base64"),
            pubkey_hex=proof.get("pubkey_hex"),
            batch_created_at=proof.get("batch_created_at"),
        )

        event_obj = EventBundleEvent(
            id=ev["id"],
            tenant_id=ev["tenant_id"],
            scope=ev["scope"],
            op=ev["op"],
            created_at=ev["created_at"],
            fields=ev.get("fields") or {},
            meta=ev.get("meta") or {},
            event_hash_hex=ev["event_hash_hex"],
            prev_hash_hex=ev.get("prev_hash_hex"),
            fields_canon=ev["fields_canon"],
            meta_canon=ev["meta_canon"],
            c_fields_hex=ev["c_fields_hex"],
            batch_id=ev.get("batch_id"),
            leaf_index=ev.get("leaf_index"),
        )

        recompute_obj = EventBundleRecompute(
            recomputed_event_hash_hex=recompute["recomputed_event_hash_hex"],
            matches_stored=bool(recompute["matches_stored"]),
        )

        return EventBundleResponse(
            kind=data["kind"],
            event=event_obj,
            proof=proof_obj,
            recompute=recompute_obj,
        )

    # -------------------
    # Offline verify endpoints (no auth)
    # -------------------

    def verify_event_bundle_offline(self, bundle: dict[str, Any]) -> VerifyBundleResponse:
        data = self._request_json("POST", "/v1/verify/bundle", body=bundle, auth=False)
        return VerifyBundleResponse(ok=bool(data.get("ok")), checks=data.get("checks") or {})

    def verify_deletion_bundle_offline(self, bundle: dict[str, Any]) -> VerifyBundleResponse:
        data = self._request_json("POST", "/v1/verify/deletion-bundle", body=bundle, auth=False)
        return VerifyBundleResponse(ok=bool(data.get("ok")), checks=data.get("checks") or {})

    # -------------------
    # Admin endpoints
    # -------------------

    def admin_list_events(
        self,
        *,
        tenant_id: str,
        scope: str | None = None,
        limit: int | None = None,
    ) -> AdminListEventsResponse:
        self._enforce_tenant(tenant_id)
        if scope is not None:
            assert_scope(scope)
            self._enforce_scope_prefix(scope)
        assert_limit(limit)

        query: dict[str, Any] = {"tenant_id": tenant_id}
        if scope is not None:
            query["scope"] = scope
        if limit is not None:
            query["limit"] = limit

        data = self._request_json("GET", "/v1/admin/events", query=query)
        raw_items = data.get("items") or []

        items = [
            AdminEventItem(
                id=item["id"],
                tenant_id=item["tenant_id"],
                scope=item["scope"],
                op=item["op"],
                created_at=item["created_at"],
                batch_id=item.get("batch_id"),
                leaf_index=item.get("leaf_index"),
            )
            for item in raw_items
        ]

        return AdminListEventsResponse(items=items)

    def admin_list_batches(
        self,
        *,
        tenant_id: str,
        limit: int | None = None,
    ) -> AdminListBatchesResponse:
        self._enforce_tenant(tenant_id)

        query: dict[str, Any] = {"tenant_id": tenant_id}
        if limit is not None:
            if not isinstance(limit, int) or limit < 1:
                raise VemorakSdkError("limit must be a positive integer")
            query["limit"] = limit

        data = self._request_json("GET", "/v1/admin/batches", query=query)
        raw_items = data.get("items") or []

        items = [
            AdminBatchItem(
                id=item["id"],
                tenant_id=item["tenant_id"],
                root_hex=item["root_hex"],
                sig_base64=item.get("sig_base64"),
                pubkey_id=item.get("pubkey_id"),
                pubkey_base64=item.get("pubkey_base64"),
                pubkey_hex=item.get("pubkey_hex"),
                count=int(item["count"]),
                created_at=item["created_at"],
            )
            for item in raw_items
        ]

        return AdminListBatchesResponse(items=items)

    def admin_list_deletion_receipts(
        self,
        *,
        tenant_id: str,
        scope: str | None = None,
        limit: int | None = None,
    ) -> AdminListDeletionReceiptsResponse:
        self._enforce_tenant(tenant_id)
        if scope is not None:
            assert_scope(scope)
            self._enforce_scope_prefix(scope)

        query: dict[str, Any] = {"tenant_id": tenant_id}
        if scope is not None:
            query["scope"] = scope
        if limit is not None:
            if not isinstance(limit, int) or limit < 1:
                raise VemorakSdkError("limit must be a positive integer")
            query["limit"] = limit

        data = self._request_json("GET", "/v1/admin/deletion-receipts", query=query)
        raw_items = data.get("items") or []

        items = [
            AdminDeletionReceiptItem(
                receipt_id=item["receipt_id"],
                tenant_id=item["tenant_id"],
                scope=item["scope"],
                delete_event_id=item["delete_event_id"],
                delete_event_hash_hex=item["delete_event_hash_hex"],
                sig_base64=item["sig_base64"],
                pubkey_id=item["pubkey_id"],
                pubkey_base64=item["pubkey_base64"],
                pubkey_hex=item["pubkey_hex"],
                created_at=item["created_at"],
            )
            for item in raw_items
        ]

        return AdminListDeletionReceiptsResponse(items=items)

    def admin_stats(self) -> AdminStatsResponse:
        data = self._request_json("GET", "/v1/admin/stats")
        return AdminStatsResponse(
            events_total=int(data["events_total"]),
            batches_total=int(data["batches_total"]),
            receipts_total=int(data["receipts_total"]),
        )

    def get_pubkey(self, pubkey_id: str) -> PubkeyResponse:
        assert_non_empty("pubkey_id", pubkey_id)
        data = self._request_json("GET", f"/v1/pubkeys/{pubkey_id}")
        return PubkeyResponse(
            pubkey_id=data["pubkey_id"],
            alg=data["alg"],
            status=data["status"],
            pubkey_base64=data["pubkey_base64"],
            pubkey_hex=data["pubkey_hex"],
        )


class ProvisioningClient:
    """
    Provisioning client for Console backend usage.

    Auth:
      Authorization: Bearer <VMP_CONSOLE_PROVISION_TOKEN>
    """

    def __init__(
        self,
        *,
        base_url: str,
        provision_token: str,
        timeout_ms: int = 15_000,
    ) -> None:
        assert_non_empty("base_url", base_url)
        assert_non_empty("provision_token", provision_token)

        self._base_url = base_url.rstrip("/")
        self._token = provision_token
        self._timeout = httpx.Timeout(timeout_ms / 1000.0)

        self._client = httpx.Client(
            base_url=self._base_url,
            timeout=self._timeout,
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {self._token}",
            },
        )

    def close(self) -> None:
        self._client.close()

    def _request_json(
        self,
        method: str,
        path: str,
        *,
        query: dict[str, Any] | None = None,
        body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        try:
            resp = self._client.request(method, path, params=query, json=body if method != "GET" else None)
        except httpx.TimeoutException as e:
            raise VmpTimeoutError("VMP request timed out") from e

        text = resp.text or ""
        if resp.status_code < 200 or resp.status_code >= 300:
            err_str = text.strip() or "unknown error"
            details = None
            try:
                parsed = resp.json()
                if isinstance(parsed, dict):
                    if isinstance(parsed.get("error"), str):
                        err_str = parsed["error"]
                    details = parsed.get("details")
            except Exception:
                pass
            raise VmpHttpError(status=resp.status_code, error=err_str, details=details, raw_body_text=text)

        if not text.strip():
            return {}
        return resp.json()

    def create_api_key(self, payload: dict[str, Any]) -> ProvisionCreateKeyResponse:
        # Minimal local validations
        assert_tenant_id(payload["tenant_id"])
        if payload.get("scope_prefix") is not None:
            assert_scope_prefix(payload["scope_prefix"])

        data = self._request_json("POST", "/v1/admin/api-keys", body=payload)

        return ProvisionCreateKeyResponse(
            id=data["id"],
            tenant_id=data["tenant_id"],
            name=data["name"],
            scopes=list(data.get("scopes") or []),
            scope_prefix=data.get("scope_prefix"),
            created_at=data["created_at"],
            expires_at=data.get("expires_at"),
            key_prefix=data["key_prefix"],
            secret=data["secret"],
        )

    def revoke_api_key(self, key_id: str) -> ProvisionRevokeKeyResponse:
        assert_uuid_like("id", key_id)
        data = self._request_json("POST", "/v1/admin/api-keys/revoke", body={"id": key_id})
        return ProvisionRevokeKeyResponse(
            id=data["id"],
            tenant_id=data["tenant_id"],
            name=data["name"],
            key_prefix=data["key_prefix"],
            scopes=list(data.get("scopes") or []),
            created_at=data["created_at"],
            expires_at=data.get("expires_at"),
            revoked_at=data["revoked_at"],
        )

    def list_api_keys(self, *, tenant_id: str, limit: int | None = None) -> ProvisionListKeysResponse:
        assert_tenant_id(tenant_id)
        if limit is not None and (not isinstance(limit, int) or limit < 1):
            raise VemorakSdkError("limit must be a positive integer")

        query: dict[str, Any] = {"tenant_id": tenant_id}
        if limit is not None:
            query["limit"] = limit

        data = self._request_json("GET", "/v1/admin/api-keys", query=query)
        items = [
            ProvisionListKeyItem(
                id=i["id"],
                tenant_id=i["tenant_id"],
                name=i["name"],
                key_prefix=i["key_prefix"],
                scopes=list(i.get("scopes") or []),
                created_at=i["created_at"],
                expires_at=i.get("expires_at"),
                revoked_at=i.get("revoked_at"),
            )
            for i in (data.get("items") or [])
        ]
        return ProvisionListKeysResponse(tenant_id=data["tenant_id"], items=items)

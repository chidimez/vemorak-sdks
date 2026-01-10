from dataclasses import dataclass
from typing import Any, Dict, List, Literal, TypedDict

RFC3339 = str
VmpOp = Literal["write", "delete"]


# ----------------------------
# Core VMP requests/responses
# ----------------------------

class IngestRequest(TypedDict, total=False):
    tenant_id: str
    scope: str
    op: VmpOp
    fields: Dict[str, Any]
    meta: Dict[str, Any]


@dataclass(frozen=True)
class IngestResponse:
    event_id: str
    event_hash_hex: str
    prev_hash_hex: str | None
    created_at: RFC3339


class DeleteRequest(TypedDict, total=False):
    tenant_id: str
    scope: str
    target_event_id: str
    meta: Dict[str, Any]


@dataclass(frozen=True)
class DeleteResponse:
    delete_event_id: str
    delete_event_hash_hex: str
    receipt_id: str
    receipt_sig_base64: str
    pubkey_id: str
    pubkey_base64: str
    pubkey_hex: str
    created_at: RFC3339


@dataclass(frozen=True)
class ProofPathItem:
    sibling_hex: str
    sibling_is_left: bool


@dataclass(frozen=True)
class ProofResponse:
    event_id: str
    tenant_id: str
    scope: str
    batch_id: str | None
    leaf_index: int | None
    leaf_hex: str | None
    root_hex: str | None
    path: List[ProofPathItem]
    sig_base64: str | None
    pubkey_id: str | None
    pubkey_base64: str | None
    pubkey_hex: str | None
    batch_created_at: RFC3339 | None


@dataclass(frozen=True)
class DeletionReceiptResponse:
    receipt_id: str
    tenant_id: str
    scope: str
    delete_event_id: str
    delete_event_hash_hex: str
    sig_base64: str
    pubkey_id: str
    pubkey_base64: str
    pubkey_hex: str
    created_at: RFC3339


@dataclass(frozen=True)
class VerifyDeletionResponse:
    receipt_id: str
    valid: bool
    tenant_id: str
    scope: str
    delete_event_id: str
    delete_event_hash_hex: str
    pubkey_id: str
    pubkey_base64: str
    pubkey_hex: str
    created_at: RFC3339


# ----------------------------
# WhoAmI (introspection)
# ----------------------------

@dataclass(frozen=True)
class WhoAmIResponse:
    tenant_id: str
    key_id: str
    allowed_scopes: List[str]
    scope_prefix: str | None


# ----------------------------
# Admin endpoints
# ----------------------------

@dataclass(frozen=True)
class AdminEventItem:
    id: str
    tenant_id: str
    scope: str
    op: VmpOp
    created_at: RFC3339
    batch_id: str | None
    leaf_index: int | None


@dataclass(frozen=True)
class AdminListEventsResponse:
    items: List[AdminEventItem]


@dataclass(frozen=True)
class AdminBatchItem:
    id: str
    tenant_id: str
    root_hex: str
    sig_base64: str | None
    pubkey_id: str | None
    pubkey_base64: str | None
    pubkey_hex: str | None
    count: int
    created_at: RFC3339


@dataclass(frozen=True)
class AdminListBatchesResponse:
    items: List[AdminBatchItem]


@dataclass(frozen=True)
class AdminDeletionReceiptItem:
    receipt_id: str
    tenant_id: str
    scope: str
    delete_event_id: str
    delete_event_hash_hex: str
    sig_base64: str
    pubkey_id: str
    pubkey_base64: str
    pubkey_hex: str
    created_at: RFC3339


@dataclass(frozen=True)
class AdminListDeletionReceiptsResponse:
    items: List[AdminDeletionReceiptItem]


@dataclass(frozen=True)
class AdminStatsResponse:
    events_total: int
    batches_total: int
    receipts_total: int


# ----------------------------
# Pubkey fetch
# ----------------------------

@dataclass(frozen=True)
class PubkeyResponse:
    pubkey_id: str
    alg: Literal["ed25519"]
    status: Literal["active", "inactive", "revoked"]
    pubkey_base64: str
    pubkey_hex: str


# ----------------------------
# Bundles
# ----------------------------

@dataclass(frozen=True)
class EventBundleEvent:
    id: str
    tenant_id: str
    scope: str
    op: VmpOp
    created_at: RFC3339
    fields: Dict[str, Any]
    meta: Dict[str, Any]
    event_hash_hex: str
    prev_hash_hex: str | None
    fields_canon: str
    meta_canon: str
    c_fields_hex: str
    batch_id: str | None
    leaf_index: int | None


@dataclass(frozen=True)
class EventBundleRecompute:
    recomputed_event_hash_hex: str
    matches_stored: bool


@dataclass(frozen=True)
class EventBundleResponse:
    kind: Literal["event.bundle"]
    event: EventBundleEvent
    proof: ProofResponse
    recompute: EventBundleRecompute


@dataclass(frozen=True)
class DeletionReceiptBundleVerification:
    receipt_id: str
    valid: bool


@dataclass(frozen=True)
class DeletionReceiptBundleResponse:
    kind: Literal["deletion_receipt.bundle"]
    receipt: DeletionReceiptResponse
    verification: DeletionReceiptBundleVerification
    delete_event_bundle: EventBundleResponse


# ----------------------------
# Offline verification responses
# ----------------------------

@dataclass(frozen=True)
class VerifyCheckDetail:
    ok: bool
    reason: str | None = None
    recomputed: str | None = None
    stored: str | None = None


@dataclass(frozen=True)
class VerifyBundleResponse:
    ok: bool
    checks: Dict[str, Any]  # keep flexible; server may evolve check keys


# ----------------------------
# Provisioning (Console -> VMP)
# ----------------------------

class ProvisionCreateKeyRequest(TypedDict, total=False):
    tenant_id: str
    label: str
    scopes: List[str]
    scope_prefix: str | None
    expires_at: str | None


@dataclass(frozen=True)
class ProvisionCreateKeyResponse:
    id: str
    tenant_id: str
    name: str
    scopes: List[str]
    scope_prefix: str | None
    created_at: RFC3339
    expires_at: RFC3339 | None
    key_prefix: str
    secret: str


class ProvisionRevokeKeyRequest(TypedDict, total=False):
    id: str


@dataclass(frozen=True)
class ProvisionRevokeKeyResponse:
    id: str
    tenant_id: str
    name: str
    key_prefix: str
    scopes: List[str]
    created_at: RFC3339
    expires_at: RFC3339 | None
    revoked_at: RFC3339


@dataclass(frozen=True)
class ProvisionListKeyItem:
    id: str
    tenant_id: str
    name: str
    key_prefix: str
    scopes: List[str]
    created_at: RFC3339
    expires_at: RFC3339 | None
    revoked_at: RFC3339 | None


@dataclass(frozen=True)
class ProvisionListKeysResponse:
    tenant_id: str
    items: List[ProvisionListKeyItem]


@dataclass(frozen=True)
class WaitForBatchOptions:
    timeout_ms: int = 30_000
    poll_interval_ms: int = 800

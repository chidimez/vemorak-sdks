import type {
    AdminListBatchesRequest,
    AdminListBatchesResponse,
    AdminListDeletionReceiptsRequest,
    AdminListDeletionReceiptsResponse,
    AdminListEventsRequest,
    AdminListEventsResponse,
    AdminStatsResponse,
    DeleteRequest,
    DeleteResponse,
    DeletionReceiptResponse,
    IngestRequest,
    IngestResponse,
    ProofResponse,
    PubkeyResponse,
    VmpClientOptions,
    WaitForBatchOptions,
    VerifyDeletionResponse
} from "./types";

import { httpJson } from "./http";
import {
    assertLimit,
    assertScope,
    assertTenantId,
    assertUuidLike
} from "./validate";
import { VemorakSdkError } from "./errors";

export class VmpClient {
    private readonly baseUrl: string;
    private readonly apiKey: string;
    private readonly tenantId?: string;
    private readonly timeoutMs: number;
    private readonly fetchImpl: typeof fetch;

    constructor(opts: VmpClientOptions) {
        if (!opts) throw new VemorakSdkError("VmpClient options are required");
        if (!opts.baseUrl) throw new VemorakSdkError("baseUrl is required");
        if (!opts.apiKey) throw new VemorakSdkError("apiKey is required");

        this.baseUrl = opts.baseUrl.replace(/\/$/, "");
        this.apiKey = opts.apiKey;
        this.tenantId = opts.tenantId;
        this.timeoutMs = opts.timeoutMs ?? 15_000;
        this.fetchImpl = opts.fetchImpl ?? fetch;
    }

    private enforceTenant(tenant_id: string): void {
        assertTenantId(tenant_id);
        if (this.tenantId && this.tenantId !== tenant_id) {
            throw new VemorakSdkError(
                `tenant_id mismatch: client is configured for ${this.tenantId} but request used ${tenant_id}`
            );
        }
    }

    async ingest(req: IngestRequest): Promise<IngestResponse> {
        this.enforceTenant(req.tenant_id);
        assertScope(req.scope);

        const body = {
            tenant_id: req.tenant_id,
            scope: req.scope,
            op: req.op ?? "write",
            fields: req.fields ?? {},
            meta: req.meta ?? {}
        };

        return httpJson<IngestResponse>(
            this.http(),
            "POST",
            "/v1/ingest",
            { body, idempotencyKey: req.idempotencyKey }
        );
    }

    async delete(req: DeleteRequest): Promise<DeleteResponse> {
        this.enforceTenant(req.tenant_id);
        assertScope(req.scope);
        assertUuidLike("target_event_id", req.target_event_id);

        const body = {
            tenant_id: req.tenant_id,
            scope: req.scope,
            target_event_id: req.target_event_id,
            meta: req.meta ?? {}
        };

        return httpJson<DeleteResponse>(this.http(), "POST", "/v1/delete", { body });
    }

    async getProof(eventId: string): Promise<ProofResponse> {
        assertUuidLike("event_id", eventId);
        return httpJson<ProofResponse>(this.http(), "GET", `/v1/proof/${encodeURIComponent(eventId)}`);
    }

    async getDeletionReceipt(receiptId: string): Promise<DeletionReceiptResponse> {
        assertUuidLike("receipt_id", receiptId);
        return httpJson<DeletionReceiptResponse>(
            this.http(),
            "GET",
            `/v1/deletion-receipts/${encodeURIComponent(receiptId)}`
        );
    }

    async verifyDeletion(receiptId: string): Promise<VerifyDeletionResponse> {
        assertUuidLike("receipt_id", receiptId);
        return httpJson<VerifyDeletionResponse>(
            this.http(),
            "GET",
            `/v1/verify-deletion/${encodeURIComponent(receiptId)}`
        );
    }

    async adminListEvents(req: AdminListEventsRequest): Promise<AdminListEventsResponse> {
        this.enforceTenant(req.tenant_id);
        if (req.scope !== undefined) assertScope(req.scope);
        assertLimit(req.limit);

        return httpJson<AdminListEventsResponse>(this.http(), "GET", "/v1/admin/events", {
            query: {
                tenant_id: req.tenant_id,
                scope: req.scope,
                limit: req.limit ?? 50
            }
        });
    }

    async adminListBatches(req: AdminListBatchesRequest): Promise<AdminListBatchesResponse> {
        this.enforceTenant(req.tenant_id);
        // your contract does not specify clamp for batches limit, keep light validation
        if (req.limit !== undefined && (!Number.isInteger(req.limit) || req.limit < 1)) {
            throw new VemorakSdkError("limit must be a positive integer");
        }

        return httpJson<AdminListBatchesResponse>(this.http(), "GET", "/v1/admin/batches", {
            query: {
                tenant_id: req.tenant_id,
                limit: req.limit
            }
        });
    }

    async adminListDeletionReceipts(
        req: AdminListDeletionReceiptsRequest
    ): Promise<AdminListDeletionReceiptsResponse> {
        this.enforceTenant(req.tenant_id);
        if (req.scope !== undefined) assertScope(req.scope);
        if (req.limit !== undefined && (!Number.isInteger(req.limit) || req.limit < 1)) {
            throw new VemorakSdkError("limit must be a positive integer");
        }

        return httpJson<AdminListDeletionReceiptsResponse>(
            this.http(),
            "GET",
            "/v1/admin/deletion-receipts",
            {
                query: {
                    tenant_id: req.tenant_id,
                    scope: req.scope,
                    limit: req.limit
                }
            }
        );
    }

    async adminStats(): Promise<AdminStatsResponse> {
        return httpJson<AdminStatsResponse>(this.http(), "GET", "/v1/admin/stats");
    }

    async getPubkey(pubkeyId: string): Promise<PubkeyResponse> {
        if (!pubkeyId || pubkeyId.trim().length === 0) {
            throw new VemorakSdkError("pubkey_id must be a non-empty string");
        }

        return httpJson<PubkeyResponse>(
            this.http(),
            "GET",
            `/v1/pubkeys/${encodeURIComponent(pubkeyId)}`
        );
    }

    /**
     * Poll proof until batched (batch_id not null).
     * This is useful for demos where batching is async.
     */
    async waitForBatch(eventId: string, opts?: WaitForBatchOptions): Promise<ProofResponse> {
        const timeoutMs = opts?.timeoutMs ?? 30_000;
        const pollIntervalMs = opts?.pollIntervalMs ?? 800;

        const start = Date.now();
        while (true) {
            const proof = await this.getProof(eventId);
            if (proof.batch_id) return proof;

            if (Date.now() - start > timeoutMs) {
                throw new VemorakSdkError(`waitForBatch timed out for event_id=${eventId}`);
            }

            await sleep(pollIntervalMs);
        }
    }

    private http() {
        return {
            baseUrl: this.baseUrl,
            apiKey: this.apiKey,
            timeoutMs: this.timeoutMs,
            fetchImpl: this.fetchImpl
        };
    }
}

function sleep(ms: number): Promise<void> {
    return new Promise((r) => setTimeout(r, ms));
}

export type RFC3339 = string;

export type VmpOp = "write" | "delete";

export type VmpErrorBody =
    | { error: string; details?: unknown }
    | { error: string }
    | Record<string, unknown>;

export type VmpClientOptions = {
    baseUrl: string;               // https://<vmp-host>
    apiKey: string;                // vmpk_<prefix>.<secret>
    tenantId?: string;             // optional guardrail, not security
    timeoutMs?: number;
    fetchImpl?: typeof fetch;
    userAgent?: string;            // optional, added to meta only if you want
};

export type IngestRequest = {
    tenant_id: string;
    scope: string;
    op?: VmpOp;                     // defaults to write
    fields: Record<string, unknown>;
    meta?: Record<string, unknown>;
    idempotencyKey?: string;        // sent as x-idempotency-key
};

export type IngestResponse = {
    event_id: string;
    event_hash_hex: string;
    prev_hash_hex: string | null;
    created_at: RFC3339;
};

export type DeleteRequest = {
    tenant_id: string;
    scope: string;
    target_event_id: string;        // UUID
    meta?: Record<string, unknown>;
};

export type DeleteResponse = {
    delete_event_id: string;
    delete_event_hash_hex: string;
    receipt_id: string;
    receipt_sig_base64: string;
    pubkey_id: string;
    pubkey_base64: string;
    pubkey_hex: string;
    created_at: RFC3339;
};

export type ProofPathItem = {
    sibling_hex: string;
    sibling_is_left: boolean;
};

export type ProofResponse = {
    event_id: string;
    tenant_id: string;
    scope: string;
    batch_id: string | null;
    leaf_index: number;
    leaf_hex: string | null;
    root_hex: string | null;
    path: ProofPathItem[];
    sig_base64: string | null;
    pubkey_id: string | null;
    pubkey_base64: string | null;
    pubkey_hex: string | null;
    batch_created_at: RFC3339 | null;
};

export type DeletionReceiptResponse = {
    receipt_id: string;
    tenant_id: string;
    scope: string;
    delete_event_id: string;
    delete_event_hash_hex: string;
    sig_base64: string;
    pubkey_id: string;
    pubkey_base64: string;
    pubkey_hex: string;
    created_at: RFC3339;
};

export type VerifyDeletionResponse = {
    receipt_id: string;
    valid: boolean;
    tenant_id: string;
    scope: string;
    delete_event_id: string;
    delete_event_hash_hex: string;
    pubkey_id: string;
    pubkey_base64: string;
    pubkey_hex: string;
    created_at: RFC3339;
};

export type AdminListEventsRequest = {
    tenant_id: string;
    scope?: string;
    limit?: number; // 1..500
};

export type AdminEventItem = {
    id: string;
    tenant_id: string;
    scope: string;
    op: VmpOp;
    created_at: RFC3339;
    batch_id: string | null;
    leaf_index: number;
};

export type AdminListEventsResponse = {
    items: AdminEventItem[];
};

export type AdminListBatchesRequest = {
    tenant_id: string;
    limit?: number;
};

export type AdminBatchItem = {
    id: string;
    tenant_id: string;
    root_hex: string;
    sig_base64: string | null;
    pubkey_id: string | null;
    pubkey_base64: string | null;
    pubkey_hex: string | null;
    count: number;
    created_at: RFC3339;
};

export type AdminListBatchesResponse = {
    items: AdminBatchItem[];
};

export type AdminListDeletionReceiptsRequest = {
    tenant_id: string;
    scope?: string;
    limit?: number;
};

export type AdminDeletionReceiptItem = {
    receipt_id: string;
    tenant_id: string;
    scope: string;
    delete_event_id: string;
    delete_event_hash_hex: string;
    sig_base64: string;
    pubkey_id: string;
    pubkey_base64: string;
    pubkey_hex: string;
    created_at: RFC3339;
};

export type AdminListDeletionReceiptsResponse = {
    items: AdminDeletionReceiptItem[];
};

export type AdminStatsResponse = {
    events_total: number;
    batches_total: number;
    receipts_total: number;
};

export type PubkeyResponse = {
    pubkey_id: string;
    alg: "ed25519";
    status: "active" | "inactive" | "revoked";
    pubkey_base64: string;
    pubkey_hex: string;
};

export type WaitForBatchOptions = {
    timeoutMs?: number;
    pollIntervalMs?: number;
};

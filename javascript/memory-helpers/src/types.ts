export type VmpOp = "write" | "delete";
export type MemoryType = "preference" | "profile_fact" | "task" | "summary";

/**
 * All memory objects MUST be explicit and MUST include a stable memory_id.
 */
export type BaseMemory = {
    memory_type: MemoryType;
    memory_id: string;
};

export type PreferenceMemory = BaseMemory & {
    memory_type: "preference";
    key: string;
    value: string;
};

export type ProfileFactMemory = BaseMemory & {
    memory_type: "profile_fact";
    key: string;
    value: string;
};

export type TaskMemory = BaseMemory & {
    memory_type: "task";
    task_id: string;
    description: string;
    status: "open" | "in_progress" | "done" | "blocked";
};

export type SummaryMemory = BaseMemory & {
    memory_type: "summary";
    scope: string; // e.g. session:xyz
    content: string;
};

export type MemoryObject =
    | PreferenceMemory
    | ProfileFactMemory
    | TaskMemory
    | SummaryMemory;

export type VmpIngestRequest<TFields extends Record<string, unknown> = Record<string, unknown>> = {
    tenant_id: string;
    scope: string;
    op: VmpOp;
    fields: TFields;
    meta?: Record<string, unknown>;
};

export type VmpIngestResponse = {
    event_id: string;
    hash_hex?: string;
    created_at?: string;
    [k: string]: unknown;
};

export type VmpProofResponse = {
    event_id: string;
    tenant_id: string;
    root_hex: string;
    sig_base64?: string | null;
    pubkey_id?: string | null;
    path?: Array<{ sibling_hex: string; side: "L" | "R" }>;
    created_at?: string;
    [k: string]: unknown;
};

/**
 * STRICT delete event fields: always requires memory_type + memory_id.
 * This is what gets appended to the ledger via POST /v1/ingest op=delete.
 */
export type DeleteEventFields = {
    memory_type: MemoryType;
    memory_id: string;
    reason?: string;
};

/**
 * Receipt request: depends on your backend’s /v1/delete contract.
 * Keep it strict around memory_id and scope. Add more fields only if your API needs them.
 */
export type VmpDeleteReceiptRequest = {
    tenant_id: string;
    scope: string;
    memory_type: MemoryType;
    memory_id: string;
    reason?: string;
};

export type VmpDeletionReceipt = {
    receipt_id: string;
    tenant_id: string;
    scope?: string | null;
    delete_event_id: string;
    delete_event_hash_hex: string;
    sig_base64: string;
    pubkey_id?: string | null;
    created_at: string;
    [k: string]: unknown;
};

export type VemorakClientOptions = {
    baseUrl: string;
    apiKey?: string;
    fetchImpl?: typeof fetch;
    defaultMeta?: Record<string, unknown>;
    timeoutMs?: number;
};

import {
    DeleteEventFields,
    MemoryObject,
    VemorakClientOptions,
    VmpDeleteReceiptRequest,
    VmpDeletionReceipt,
    VmpIngestRequest,
    VmpIngestResponse,
    VmpProofResponse
} from "./types";
import { VmpHttpError, VmpTimeoutError } from "./errors";
import { assertMemoryObject, assertNonEmptyString } from "../../sdk/src/validate";

export class VemorakClient {
    private baseUrl: string;
    private apiKey?: string;
    private fetchImpl: typeof fetch;
    private defaultMeta?: Record<string, unknown>;
    private timeoutMs: number;

    constructor(opts: VemorakClientOptions) {
        this.baseUrl = opts.baseUrl.replace(/\/$/, "");
        this.apiKey = opts.apiKey;
        this.fetchImpl = opts.fetchImpl ?? fetch;
        this.defaultMeta = opts.defaultMeta;
        this.timeoutMs = opts.timeoutMs ?? 15_000;
    }

    async ingest<TFields extends Record<string, unknown>>(req: VmpIngestRequest<TFields>): Promise<VmpIngestResponse> {
        assertNonEmptyString("tenant_id", req.tenant_id);
        assertNonEmptyString("scope", req.scope);
        return this.postJson<VmpIngestResponse>("/v1/ingest", {
            ...req,
            meta: { ...(this.defaultMeta ?? {}), ...(req.meta ?? {}) }
        });
    }

    async writeMemory(args: {
        tenant_id: string;
        scope: string;
        memory: MemoryObject;
        meta?: Record<string, unknown>;
    }): Promise<VmpIngestResponse> {
        assertMemoryObject(args.memory);
        return this.ingest<MemoryObject>({
            tenant_id: args.tenant_id,
            scope: args.scope,
            op: "write",
            fields: args.memory,
            meta: args.meta
        });
    }

    /**
     * STRICT: Delete is always typed.
     * This appends a delete event to the VMP ledger (auditable ordering).
     */
    async deleteMemoryEvent(args: {
        tenant_id: string;
        scope: string;
        memory_type: DeleteEventFields["memory_type"];
        memory_id: string;
        reason?: string;
        meta?: Record<string, unknown>;
    }): Promise<VmpIngestResponse> {
        assertNonEmptyString("memory_id", args.memory_id);

        const fields: DeleteEventFields = {
            memory_type: args.memory_type,
            memory_id: args.memory_id,
            reason: args.reason ?? "user_request"
        };

        return this.ingest<DeleteEventFields>({
            tenant_id: args.tenant_id,
            scope: args.scope,
            op: "delete",
            fields,
            meta: args.meta
        });
    }

    /**
     * STRICT: Request a deletion receipt for a typed memory target.
     * This should return a signed receipt from POST /v1/delete.
     */
    async requestDeletionReceipt(req: VmpDeleteReceiptRequest): Promise<VmpDeletionReceipt> {
        assertNonEmptyString("tenant_id", req.tenant_id);
        assertNonEmptyString("scope", req.scope);
        assertNonEmptyString("memory_id", req.memory_id);
        return this.postJson<VmpDeletionReceipt>("/v1/delete", req);
    }

    async getProof(eventId: string): Promise<VmpProofResponse> {
        assertNonEmptyString("eventId", eventId);
        return this.getJson<VmpProofResponse>(`/v1/proof/${encodeURIComponent(eventId)}`);
    }

    private headers(): HeadersInit {
        const h: Record<string, string> = { "Content-Type": "application/json" };
        if (this.apiKey) h["Authorization"] = `Bearer ${this.apiKey}`;
        return h;
    }

    private async getJson<T>(path: string): Promise<T> {
        return this.requestJson<T>(path, { method: "GET" });
    }

    private async postJson<T>(path: string, body: unknown): Promise<T> {
        return this.requestJson<T>(path, { method: "POST", body: JSON.stringify(body) });
    }

    private async requestJson<T>(path: string, init: RequestInit): Promise<T> {
        const controller = new AbortController();
        const t = setTimeout(() => controller.abort(), this.timeoutMs);

        try {
            const res = await this.fetchImpl(this.baseUrl + path, {
                ...init,
                headers: { ...this.headers(), ...(init.headers ?? {}) },
                signal: controller.signal
            });

            const text = await res.text();
            if (!res.ok) throw new VmpHttpError(`VMP request failed: ${init.method ?? "GET"} ${path}`, res.status, text);

            if (!text.trim()) return {} as T;
            return JSON.parse(text) as T;
        } catch (e: any) {
            if (e?.name === "AbortError") throw new VmpTimeoutError("VMP request timed out");
            throw e;
        } finally {
            clearTimeout(t);
        }
    }
}

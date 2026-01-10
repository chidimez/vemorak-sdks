import { VmpHttpError, VmpTimeoutError } from "./errors";

export type HttpOptions = {
    baseUrl: string;
    apiKey: string;
    timeoutMs: number;
    fetchImpl: typeof fetch;
};

export async function httpJson<T>(
    http: HttpOptions,
    method: "GET" | "POST",
    path: string,
    args?: {
        query?: Record<string, string | number | boolean | undefined>;
        body?: unknown;
        idempotencyKey?: string;
    }
): Promise<T> {
    const url = new URL(http.baseUrl.replace(/\/$/, "") + path);

    if (args?.query) {
        for (const [k, v] of Object.entries(args.query)) {
            if (v === undefined) continue;
            url.searchParams.set(k, String(v));
        }
    }

    const controller = new AbortController();
    const t = setTimeout(() => controller.abort(), http.timeoutMs);

    try {
        const headers: Record<string, string> = {
            "Accept": "application/json",
            "Authorization": `Bearer ${http.apiKey}`
        };

        if (method === "POST") headers["Content-Type"] = "application/json";
        if (args?.idempotencyKey) headers["x-idempotency-key"] = args.idempotencyKey;

        const res = await http.fetchImpl(url.toString(), {
            method,
            headers,
            body: method === "POST" ? JSON.stringify(args?.body ?? {}) : undefined,
            signal: controller.signal
        });

        const text = await res.text();

        if (!res.ok) {
            throw VmpHttpError.from(res.status, text);
        }

        if (!text.trim()) return {} as T;
        return JSON.parse(text) as T;
    } catch (e: any) {
        if (e?.name === "AbortError") throw new VmpTimeoutError();
        throw e;
    } finally {
        clearTimeout(t);
    }
}

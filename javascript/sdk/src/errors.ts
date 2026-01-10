import type { VmpErrorBody } from "./types";

export class VemorakSdkError extends Error {
    override name = "VemorakSdkError";
}

export class VmpHttpError extends VemorakSdkError {
    public readonly status: number;
    public readonly error: string;
    public readonly details?: unknown;
    public readonly rawBodyText: string;

    constructor(args: {
        status: number;
        error: string;
        details?: unknown;
        rawBodyText: string;
        message?: string;
    }) {
        super(args.message ?? `VMP request failed (${args.status}): ${args.error}`);
        this.status = args.status;
        this.error = args.error;
        this.details = args.details;
        this.rawBodyText = args.rawBodyText;
    }

    static from(status: number, rawBodyText: string): VmpHttpError {
        let parsed: VmpErrorBody | undefined;
        try {
            parsed = JSON.parse(rawBodyText) as VmpErrorBody;
        } catch {
            parsed = undefined;
        }

        const error =
            (parsed && typeof (parsed as any).error === "string" && (parsed as any).error) ||
            rawBodyText ||
            "unknown error";

        const details = parsed && (parsed as any).details;

        return new VmpHttpError({
            status,
            error,
            details,
            rawBodyText
        });
    }
}

export class VmpTimeoutError extends VemorakSdkError {
    override name = "VmpTimeoutError";
    constructor(message = "VMP request timed out") {
        super(message);
    }
}

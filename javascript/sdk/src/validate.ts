import { VemorakSdkError } from "./errors";

export function assertNonEmpty(name: string, v: unknown): asserts v is string {
    if (typeof v !== "string" || v.trim().length === 0) {
        throw new VemorakSdkError(`${name} must be a non-empty string`);
    }
}

export function assertTenantId(tenantId: string): void {
    assertNonEmpty("tenant_id", tenantId);
    if (tenantId.length > 128) throw new VemorakSdkError("tenant_id must be 1..128 chars");
    if (/\s/.test(tenantId)) throw new VemorakSdkError("tenant_id must not contain spaces");
}

export function assertScope(scope: string): void {
    assertNonEmpty("scope", scope);
    if (scope.length > 128) throw new VemorakSdkError("scope must be 1..128 chars");
    if (!scope.includes(":")) throw new VemorakSdkError("scope must contain ':' for namespacing");
}

export function assertLimit(limit: number | undefined): void {
    if (limit === undefined) return;
    if (!Number.isInteger(limit)) throw new VemorakSdkError("limit must be an integer");
    if (limit < 1 || limit > 500) throw new VemorakSdkError("limit must be within 1..500");
}

export function assertUuidLike(name: string, v: string): void {
    assertNonEmpty(name, v);
    // Soft check: your backend enforces UUID, this just catches obvious mistakes.
    if (!/^[0-9a-fA-F-]{16,}$/.test(v)) {
        throw new VemorakSdkError(`${name} must look like a UUID`);
    }
}

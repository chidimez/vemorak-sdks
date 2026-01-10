import type { MemoryType } from "@vemorak/sdk";

export function prefId(key: string) {
    return `pref:${key.trim()}`;
}

export function factId(key: string) {
    return `fact:${key.trim()}`;
}

export function taskId(taskId: string) {
    return `task:${taskId.trim()}`;
}

export function summaryId(scope: string) {
    return `summary:${scope.trim()}`;
}

export function assertSafeKey(key: string) {
    // Keep keys conservative to avoid weird id bugs in demos.
    // Adjust if you need richer keys.
    if (!/^[a-zA-Z0-9_.:-]+$/.test(key)) {
        throw new Error(`Invalid key "${key}". Use letters, digits, underscore, dot, colon, dash.`);
    }
}

export function deleteTarget(memory_type: MemoryType, memory_id: string) {
    return { memory_type, memory_id };
}

import type { MemoryObject, MemoryType } from "@vemorak/sdk";
import { makePreference, makeProfileFact, makeSummary } from "./make";
import { deleteTarget } from "./ids";

export type ExtractedIntent =
    | { kind: "write"; memory: MemoryObject }
    | { kind: "delete"; target: { memory_type: MemoryType; memory_id: string }; reason?: string }
    | { kind: "recall" }
    | { kind: "unknown"; hint: string };

/**
 * Deterministic, rule-based extractor for demo realism.
 * Keeps the demo from turning into “prompt engineering”.
 */
export function extractIntent(text: string, scope: string): ExtractedIntent {
    const t = text.trim();

    if (/^what do you remember\??$/i.test(t) || /^show (me )?your memory\??$/i.test(t)) {
        return { kind: "recall" };
    }

    // Remember preference: "Remember that I prefer technical explanations"
    if (/^remember that i prefer /i.test(t)) {
        const value = t.replace(/^remember that i prefer /i, "").trim();
        return { kind: "write", memory: makePreference("writing_style", value) };
    }

    // Update preferred language: "Update my preferred language to Rust"
    if (/^(update|actually update) my preferred language to /i.test(t)) {
        const value = t.replace(/^(update|actually update) my preferred language to /i, "").trim();
        return { kind: "write", memory: makePreference("preferred_language", value) };
    }

    // Forget all preferences: "Forget everything about my preferences"
    if (/^forget (everything )?about my preferences\??$/i.test(t)) {
        // In strict mode we need a specific target.
        // For a demo, treat this as deleting a single canonical preference root key,
        // or emit multiple delete targets in the app layer.
        return {
            kind: "delete",
            target: deleteTarget("preference", "pref:writing_style"),
            reason: "user_request"
        };
    }

    // Summary creation: "Summarise this session" etc
    if (/^summari[sz]e (this )?session/i.test(t)) {
        return { kind: "write", memory: makeSummary(scope, "User prefers concise technical explanations.") };
    }

    return {
        kind: "unknown",
        hint: "Try: “Remember that I prefer technical explanations”, “Update my preferred language to Rust”, “What do you remember?”, “Forget everything about my preferences”."
    };
}

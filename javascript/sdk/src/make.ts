import type {
    PreferenceMemory,
    ProfileFactMemory,
    TaskMemory,
    SummaryMemory
} from "@vemorak/sdk";
import { prefId, factId, taskId as mkTaskId, summaryId, assertSafeKey } from "./ids";

export function makePreference(key: string, value: string): PreferenceMemory {
    assertSafeKey(key);
    return {
        memory_type: "preference",
        memory_id: prefId(key),
        key,
        value
    };
}

export function makeProfileFact(key: string, value: string): ProfileFactMemory {
    assertSafeKey(key);
    return {
        memory_type: "profile_fact",
        memory_id: factId(key),
        key,
        value
    };
}

export function makeTask(args: {
    task_id: string;
    description: string;
    status?: TaskMemory["status"];
}): TaskMemory {
    return {
        memory_type: "task",
        memory_id: mkTaskId(args.task_id),
        task_id: args.task_id,
        description: args.description,
        status: args.status ?? "open"
    };
}

export function makeSummary(scope: string, content: string): SummaryMemory {
    return {
        memory_type: "summary",
        memory_id: summaryId(scope),
        scope,
        content
    };
}

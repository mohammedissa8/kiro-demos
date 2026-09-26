# Review: `cmd_complete` in `src/task_manager/cli.py`

`cmd_complete` loads all tasks, linearly scans for the first task whose `id` matches `args.id`, and on a match sets `completed = True`, persists the full list via `store.save(tasks)`, prints a success line, and returns. If no task matches, it prints `Task {id} not found.` to `stderr` and exits with status 1. The handler correctly respects the models/storage/cli layering — it does no direct file I/O, delegates persistence to `TaskStore`, and routes all output through the CLI layer with errors to `stderr` and a non-zero exit, matching the sibling handlers.

**Watch for:** a non-atomic load-modify-save that loses concurrent writes (`likely`), silent no-op on an already-completed task (`confirmed`), and only the first task being completed when duplicate ids exist (`confirmed`).

**Verdict**: NEEDS_CHANGES

---

## Findings

### 1. Non-atomic load-modify-save can lose concurrent writes — severity: medium — confidence: likely

**Lines:** 34–40 (`tasks = store.load()` … `store.save(tasks)`).

**Evidence:** `store.save` (storage.py) opens the target path in `"w"` mode and rewrites the entire file with no locking, no temp-file-and-rename, and no read-back check. `cmd_complete` reads the full list, mutates one element in memory, and writes the whole list back. If a second process runs `add`, `complete`, or `delete` between this handler's `load()` and `save()`, the second process's write is silently clobbered by whichever `save()` lands last (last-writer-wins). The `"w"` truncate also means a crash mid-write can leave `tasks.json` truncated or empty.

**Remediation:** This is partly a storage-layer concern (atomic write via `tempfile` + `os.replace`, and optionally advisory file locking), so the durable fix belongs in `TaskStore.save`. For `cmd_complete` specifically, the risk is inherent to the read-modify-write shape; document the single-writer assumption, and if concurrency is ever in scope, guard the load-modify-save with a lock owned by the storage layer. Note this is a small single-user CLI, so the practical severity is bounded — flagged as medium because the failure is silent.

### 2. Already-completed task is a silent no-op reported as success — severity: low — confidence: confirmed

**Lines:** 35–39.

**Evidence:** The match branch unconditionally sets `t.completed = True` regardless of the prior value. Completing a task that is already completed rewrites the file with identical data and prints `Completed task {id}: {title}`, giving the user no signal that nothing changed. This is a correctness/UX ambiguity rather than a bug, but it can mask mistakes (e.g., user completes the wrong id, sees "Completed", assumes intent was honored).

**Remediation:** Detect the already-completed state before mutating and emit a distinct message (e.g., `Task {id} was already complete.`), and consider skipping the redundant `store.save` when `completed` is already `True` to avoid a pointless rewrite.

### 3. Duplicate ids: only the first match is completed — severity: low — confidence: confirmed

**Lines:** 35–40 (`return` inside the match branch).

**Evidence:** The scan `return`s after the first `t.id == args.id` match, so if the store ever contains two tasks with the same id, only the first is marked complete and the second is left untouched. `TaskStore.next_id` computes `max(id)+1`, which normally prevents collisions, but ids are not enforced unique at the storage or model layer, and a hand-edited `tasks.json` (the file is user-facing per AGENTS.md) or a restored/merged file could reintroduce duplicates. `cmd_delete` (line 47) removes *all* matches via list comprehension, so the two handlers treat duplicate ids inconsistently — complete touches one, delete removes all.

**Remediation:** Decide on a single duplicate-id policy and apply it consistently across handlers. Either enforce id uniqueness in the storage layer, or have `cmd_complete` mark all matching tasks (dropping the early `return` and tracking whether any match was found) to align with `cmd_delete`'s all-match behavior.

### 4. Empty store and missing id both correctly hit the not-found path — severity: info — confidence: confirmed

**Lines:** 41–42.

**Evidence:** When `store.load()` returns `[]` (no file yet, or an empty file), the loop body never executes and control falls through to the not-found branch, printing to `stderr` and exiting 1. A missing but non-empty store behaves identically. This is the correct and expected behavior; the not-found path and exit-code semantics match `cmd_delete` and the AGENTS.md convention (errors to `stderr`, non-zero exit). Recorded as info to confirm the edge cases were checked, not as a defect.

### 5. `sys.exit(1)` vs. `return` control-flow asymmetry — severity: info — confidence: confirmed

**Lines:** 39 (`return` on success) vs. 42 (`sys.exit(1)` on not-found).

**Evidence:** The success path returns normally (letting `main` exit 0 implicitly), while the not-found path calls `sys.exit(1)` directly from the handler. This mirrors `cmd_delete` exactly, so it is consistent within the codebase, but calling `sys.exit` from within a command handler couples the handler to process-exit semantics rather than raising and letting `main` translate the outcome to an exit code. Not a defect given the established pattern; noted for architectural awareness.

**Remediation (optional):** If exit-code handling is ever centralized, have handlers raise a small CLI exception (or return a status) and let `main` map it to `sys.exit`, keeping handlers free of direct process control.

---

## Summary

| # | Title | Severity | Confidence |
|---|-------|----------|------------|
| 1 | Non-atomic load-modify-save loses concurrent writes | medium | likely |
| 2 | Already-completed task is a silent success no-op | low | confirmed |
| 3 | Duplicate ids: only first match completed (inconsistent with `cmd_delete`) | low | confirmed |
| 4 | Empty/missing store correctly hits not-found path | info | confirmed |
| 5 | `sys.exit(1)` vs `return` control-flow asymmetry | info | confirmed |

No critical or high-severity issues. `cmd_complete` is functionally correct for the single-user happy path and adheres to the models/storage/cli layering. The medium finding (concurrency) is largely a storage-layer responsibility; the low findings (already-completed no-op, duplicate-id inconsistency) are the most actionable at the CLI layer.

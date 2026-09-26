# Review: `cmd_delete` (src/task_manager/cli.py)

Deletes the task whose id matches `args.id` by loading all tasks, filtering out the match, and detecting absence through a length comparison between the filtered list and the original. If nothing was removed it reports "Task {id} not found." on stderr and exits 1; otherwise it saves the survivors and prints "Deleted task {id}". The handler is small and its layering is clean — it routes all output through the CLI layer and delegates persistence to `TaskStore`, matching AGENTS.md conventions. The behavioral concerns are entirely about *what happens around* the delete: no confirmation on a destructive, irreversible operation; duplicate-id tasks silently removed en masse; and a non-atomic load-modify-save that can lose concurrent writes.

**Watch for:** irreversible delete with no confirmation prompt (medium); duplicate ids all deleted with a "deleted 1" mental model (medium); lost-update race on concurrent invocations (low, given single-user CLI design).

**Verdict**: NEEDS_CHANGES

## High-level view

The not-found detection is correct and arguably more robust than `cmd_complete`'s early-return loop: comparing `len(remaining)` to `len(tasks)` reliably distinguishes "removed something" from "removed nothing" without assuming id uniqueness. That same robustness, however, masks a semantic gap — if the store contains two tasks with the same id, both are removed and the user is still told "Deleted task {id}" with no hint that more than one row disappeared. Whether that is a bug depends on an invariant (`next_id` hands out `max+1`) that this function does not enforce and cannot rely on, since ids come from disk and the file is user-editable.

The delete is destructive and irreversible — `store.save(remaining)` overwrites `tasks.json` with the survivors and there is no backup, no undo, and no confirmation prompt. For a small personal task tool this may be acceptable, but it is the single most consequential behavior in the command and deserves a conscious decision rather than a silent default.

Persistence is a read-all / modify / write-all cycle with no locking. Two overlapping CLI processes can lose each other's writes (classic lost update). This is inherent to the `TaskStore` design and shared by every mutating handler, so it is out of scope to *fix* here, but it is worth recording as a known limitation of the delete path.

Error propagation from `store.load()` and `store.save()` is unhandled: a corrupt or unreadable `tasks.json` surfaces as an uncaught traceback rather than a clean CLI error, inconsistent with the deliberate stderr-plus-exit-1 style used for not-found.

<details>
<summary>Issues (5)</summary>

1. **No confirmation on destructive delete** — delete is irreversible with no prompt, `--yes` flag, or backup; a mistyped id silently discards a task. Add a confirmation prompt (with a `--force`/`--yes` bypass) or document the no-undo behavior as intentional.
2. **Duplicate ids deleted silently** — `[t for t in tasks if t.id != args.id]` removes *all* matches but always reports "Deleted task {id}"; if the file contains duplicate ids the user loses more than they expect with no indication. Report the number removed, or delete only the first match to match the singular message.
3. **Unhandled load/save errors** — a corrupt/unreadable `tasks.json` raises an uncaught exception (traceback) instead of a clean stderr error + non-zero exit, inconsistent with the not-found path. Wrap the load/save (or centralize in the CLI) to emit a user-facing error.
4. **Lost-update race on concurrent delete** — non-atomic load-modify-save with no locking; two overlapping invocations can clobber each other's writes. Known `TaskStore`-level limitation; document it or add atomic write/locking in the storage layer (not in this handler).
5. **No validation that the store is non-empty vs. not-found** — an empty store and a genuinely-absent id are indistinguishable to the user (both say "not found"). Behaviorally correct; noted as info only, no action required.

</details>

<details>
<summary>Details</summary>

### Duplicate ids are all removed but the message says one (line 49, 54)

Because the filter keeps every task whose id differs from `args.id`, it removes *all* tasks sharing that id, then prints the singular `Deleted task {args.id}`. Under normal operation `next_id` returns `max(id)+1`, so duplicates should not arise — but that invariant is not enforced here and cannot be trusted: ids are read from `tasks.json` (see `TaskStore.load`), the file is plain JSON a user can hand-edit, and `from_dict` performs no uniqueness or range validation. **(likely)** If two tasks end up with id 3, `delete 3` erases both and the user is told only that "task 3" was deleted, with no signal that two rows vanished.

Remediation: either report the count actually removed (`removed = len(tasks) - len(remaining)`; `print(f"Deleted {removed} task(s) with id {args.id}")`), or delete only the first match to make behavior consistent with the singular message. Reporting the count is preferable because it preserves the current "remove all matches" behavior while making it observable.

### Destructive, irreversible delete with no confirmation (lines 53–54)

```python
store.save(remaining)
print(f"Deleted task {args.id}")
```

`save` overwrites `tasks.json` wholesale with the survivors (see `TaskStore.save`, which opens the file in `"w"` mode). There is no confirmation prompt, no `--force`/`--yes` gate, no soft-delete, and no backup of the prior file contents. A single mistyped id — trivially easy since ids are bare integers — permanently discards a task with no undo. **(confirmed)** For a personal CLI this may be an accepted trade-off, but it is the most consequential line in the command and should be a deliberate choice. Remediation: prompt for confirmation on a TTY with a `--yes` bypass for scripting, or (cheaper) write the prior file to a `.bak` before overwriting so a delete is recoverable.

### Unhandled errors from load and save (lines 48, 53)

`store.load()` calls `json.load`, which raises `JSONDecodeError` on a truncated or corrupt file; `store.save()` can raise `OSError` (permissions, full disk, read-only path). Neither is caught anywhere in the delete path or in `main`, so the user sees a raw Python traceback instead of the clean stderr message + exit-1 pattern the not-found branch deliberately follows. **(confirmed)** This is an inconsistency in failure presentation within the same handler: one failure mode (not found) is handled gracefully, the others crash. Remediation belongs in the CLI layer (per AGENTS.md, "route user messages through the CLI layer... errors to stderr with a non-zero exit") — wrap the load/save calls, or add a top-level guard in `main`, to convert storage exceptions into a user-facing error.

### Non-atomic load-modify-save / lost-update race (lines 48–53)

The handler reads the whole file, computes survivors in memory, then writes the whole file back. Two CLI processes running concurrently (e.g. `delete 1` and `add "x"`) can interleave such that the second `save` overwrites the first, silently losing a change. `TaskStore.save` truncates and rewrites with no lock or atomic rename. **(likely)** This is a property of the storage layer, not something `cmd_delete` can fix without violating the layering convention (persistence lives in `storage.py`), so the finding is: document it as a known single-writer assumption, or address it in `TaskStore` via file locking or write-to-temp-then-rename. Given the tool is designed as a single-user CLI, the practical severity is low.

### Layering and conventions (whole function)

`cmd_delete` adheres to AGENTS.md layering (no direct file I/O, output owned by the handler, errors to stderr with non-zero exit). One thing to confirm: its file-level `__audit_id__` is `"task-manager-cli"` (the project name) rather than the module name `"cli"`, whereas the ORG-042 example uses the module's own name (`__audit_id__ = "manager"`). **(possible)** This is a file-level attribute outside the strict scope of `cmd_delete` and applies equally to every module in the project.

</details>

<details>
<summary>File map</summary>

- `src/task_manager/cli.py` — reviewed `cmd_delete` (lines 47–54); no changes made. Read `cmd_add`, `cmd_list`, `cmd_complete`, `build_parser`, `main` for context only.
- `src/task_manager/storage.py` — read for `load`/`save`/`next_id` behavior (context, not modified).
- `src/task_manager/models.py` — read for `Task`/`from_dict` validation behavior (context, not modified).

No source files were modified. This review covers only `cmd_delete`.

</details>

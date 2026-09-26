# CLI Command Handler Review — `src/task_manager/cli.py`

**Date:** 2025-06-13
**Scope:** Consolidated, risk-ranked review of the three mutating command handlers in
`src/task_manager/cli.py` — `cmd_add`, `cmd_complete`, and `cmd_delete`. Each handler
was reviewed independently; this note merges those findings, groups cross-cutting
issues, and ranks everything by severity. No source files were modified.

All three handlers are functionally correct for the documented single-user happy path
and adhere to the AGENTS.md models/storage/cli layering (no direct file I/O, persistence
delegated to `TaskStore`, output routed through the CLI layer). The weaknesses are in
robustness under failure, concurrency, and a few handler-specific UX/semantic gaps —
several of which are properly fixed in `storage.py`/`models.py`, not in the handlers.

---

## Summary of all findings

| Severity | Handler | Finding | Location |
|----------|---------|---------|----------|
| Medium | Cross-cutting (`cmd_add`, `cmd_complete`, `cmd_delete`) | Non-atomic load-modify-save; concurrent invocations lose writes (and can duplicate ids on add) | add 13–16; complete 34–40; delete 48–53 |
| Medium | `cmd_delete` | Destructive, irreversible delete with no confirmation prompt / `--yes` / backup | delete 53–54 |
| Medium | `cmd_delete` | Duplicate ids all removed but message reports a single deletion | delete 49, 54 |
| Low | Cross-cutting (`cmd_add`, `cmd_complete`, `cmd_delete`) | Unhandled `load`/`save` errors surface as raw tracebacks instead of clean stderr + exit 1 | add 13, 16; complete 34, 40; delete 48, 53 |
| Low | `cmd_add` | Title content not validated (empty/whitespace/control chars accepted) | add 14 |
| Low | `cmd_complete` | Already-completed task is a silent no-op reported as success | complete 35–39 |
| Low | `cmd_complete` | Duplicate ids: only the first match completed (inconsistent with `cmd_delete`) | complete 35–40 |
| Info | Cross-cutting (all modules) | `__audit_id__` set to project name `"task-manager-cli"` rather than module name (ORG-042 convention) | file-level |
| Info | `cmd_add` | Priority validity depends solely on argparse `choices`, not the `Task` model | add 14; parser 66 |
| Info | `cmd_complete` | `sys.exit(1)` vs `return` control-flow asymmetry | complete 39 vs 42 |
| Info | `cmd_complete` / `cmd_delete` | Empty store vs. genuinely-missing id both hit not-found path (correct) | complete 41–42; delete |
| Info | `cmd_add` | Models/storage/cli layering respected (error handling is the one convention gap) | add 11–17 |

---

## Findings (sorted by severity)

### MEDIUM

#### M1. Non-atomic load-modify-save — concurrent invocations lose writes (Cross-cutting)

- **Severity:** medium (low in practice for the documented single-user CLI; flagged
  medium because the failure is silent)
- **Affected handlers:** `cmd_add`, `cmd_complete`, `cmd_delete` (all mutating handlers)
- **Location:** `cmd_add` lines 13–16; `cmd_complete` lines 34–40; `cmd_delete` lines 48–53
- **Evidence:** Every mutating handler reads the whole task list, mutates in memory, and
  rewrites the entire file. `TaskStore.save` opens the file in `"w"` mode with no lock,
  no temp-file-and-rename, and no compare-and-swap. Two overlapping CLI processes
  produce a classic read-read-write-write interleaving where the last `save` clobbers
  the first — a change is silently lost (last-writer-wins). For `cmd_add` specifically,
  `next_id` is derived from the stale snapshot, so two racing adds compute the same id,
  producing a duplicate id as well as a lost write. The `"w"` truncate also means a
  crash mid-write can leave `tasks.json` truncated or empty.
- **Remediation:** The durable fix belongs in the storage layer (per AGENTS.md,
  persistence lives in `storage.py`): write to a temp file and `os.replace` it into
  place for atomicity, and/or add advisory file locking (`fcntl.flock`) around the
  read-modify-write. The handlers themselves should not grow file-handling logic. If
  concurrency is out of scope, document the single-writer assumption as a known
  limitation.

#### M2. Destructive, irreversible delete with no confirmation (`cmd_delete`)

- **Severity:** medium
- **Affected handler:** `cmd_delete`
- **Location:** lines 53–54 (`store.save(remaining)` / `print`)
- **Evidence:** `save` overwrites `tasks.json` wholesale with the survivors. There is no
  confirmation prompt, no `--force`/`--yes` gate, no soft-delete, and no backup of the
  prior file. A single mistyped id — trivially easy since ids are bare integers —
  permanently discards a task with no undo. This is the single most consequential
  behavior in the command and is currently a silent default rather than a deliberate
  choice.
- **Remediation:** Prompt for confirmation on a TTY with a `--yes` bypass for scripting,
  or (cheaper) write the prior file contents to a `.bak` before overwriting so a delete
  is recoverable. Alternatively, document the no-undo behavior as an intentional
  trade-off for a personal CLI.

#### M3. Duplicate ids all deleted but message reports one (`cmd_delete`)

- **Severity:** medium
- **Affected handler:** `cmd_delete`
- **Location:** lines 49, 54
- **Evidence:** `[t for t in tasks if t.id != args.id]` removes *all* tasks whose id
  matches, then always prints the singular `Deleted task {id}`. Normally `next_id`
  returns `max(id)+1` so duplicates should not arise, but that invariant is not enforced
  and cannot be trusted: ids are read from a user-editable `tasks.json`, and `from_dict`
  performs no uniqueness or range validation. If two tasks share id 3, `delete 3` erases
  both while the user is told only that "task 3" was deleted, with no signal that two
  rows vanished. (Note: `cmd_complete` treats duplicates the opposite way — it touches
  only the first match — so the two handlers are inconsistent; see L4.)
- **Remediation:** Report the count actually removed
  (`removed = len(tasks) - len(remaining)`; e.g. `Deleted {removed} task(s) with id {id}`),
  or delete only the first match to match the singular message. Reporting the count is
  preferable — it preserves the current "remove all matches" behavior while making it
  observable.

### LOW

#### L1. Unhandled `load`/`save` errors surface as raw tracebacks (Cross-cutting)

- **Severity:** low
- **Affected handlers:** `cmd_add`, `cmd_complete`, `cmd_delete`
- **Location:** `cmd_add` lines 13, 16; `cmd_complete` lines 34, 40; `cmd_delete` lines 48, 53
- **Evidence:** `store.load()` calls `json.load` (raises `JSONDecodeError` on a truncated
  or corrupt file) and `Task.from_dict` does hard `data["id"]`/`data["title"]` lookups
  (raises `KeyError` on missing keys); `store.save()` can raise `OSError` (permissions,
  full disk, read-only path). None of these are caught in the handlers or in `main`, so
  the user sees a raw Python traceback instead of the clean stderr-plus-exit-1 pattern
  the not-found branches deliberately follow. This is a module-wide inconsistency in
  failure presentation — within `cmd_delete`/`cmd_complete`, one failure mode (not
  found) is handled gracefully while the others crash.
- **Remediation:** Per AGENTS.md ("route user messages through the CLI layer... errors
  to stderr with a non-zero exit"), wrap the load/save calls or add a top-level guard in
  `main` that converts storage/parse exceptions into a friendly stderr message and
  `sys.exit(1)`. Root causes for parse/read errors live in `storage.py`/`models.py`; the
  handlers inherit the failure mode.

#### L2. Title content not validated (`cmd_add`)

- **Severity:** low
- **Affected handler:** `cmd_add`
- **Location:** line 14 (`title=args.title`)
- **Evidence:** `argparse` requires the positional `title` to be present but does not
  constrain its content. `python main.py add ""` creates a task with an empty title; a
  title of only spaces, a newline, or terminal control/escape sequences is stored
  verbatim and later echoed by `cmd_list`. This is an input-handling gap rather than a
  security hole (JSON serialization neutralizes injection into the file), but empty
  titles are almost certainly unintended.
- **Remediation:** If empty titles are undesirable, reject blank/whitespace-only titles
  with a stderr message and non-zero exit. Basic presence validation fits in the CLI
  handler; richer rules could live on the `Task` model.

#### L3. Already-completed task is a silent success no-op (`cmd_complete`)

- **Severity:** low
- **Affected handler:** `cmd_complete`
- **Location:** lines 35–39
- **Evidence:** The match branch unconditionally sets `t.completed = True` regardless of
  the prior value. Completing an already-completed task rewrites the file with identical
  data and prints `Completed task {id}: {title}`, giving no signal that nothing changed.
  This can mask mistakes (e.g., the user completes the wrong id, sees "Completed", and
  assumes intent was honored).
- **Remediation:** Detect the already-completed state before mutating and emit a distinct
  message (e.g., `Task {id} was already complete.`); consider skipping the redundant
  `store.save` when `completed` is already `True` to avoid a pointless rewrite.

#### L4. Duplicate ids: only the first match completed (`cmd_complete`)

- **Severity:** low
- **Affected handler:** `cmd_complete` (inconsistent with `cmd_delete` — see M3)
- **Location:** lines 35–40 (`return` inside the match branch)
- **Evidence:** The scan `return`s after the first `t.id == args.id` match, so if the
  store contains two tasks with the same id, only the first is marked complete and the
  second is untouched. `next_id` normally prevents collisions, but uniqueness is not
  enforced at the storage or model layer, and a hand-edited or merged `tasks.json` could
  reintroduce duplicates. `cmd_delete` removes *all* matches, so the two handlers treat
  duplicate ids inconsistently — complete touches one, delete removes all.
- **Remediation:** Decide on a single duplicate-id policy and apply it consistently.
  Either enforce id uniqueness in the storage layer, or drop the early `return` and mark
  all matching tasks (tracking whether any match was found) to align with `cmd_delete`.

### INFO

#### I1. `__audit_id__` uses project name, not module name (Cross-cutting)

- **Severity:** info
- **Affected:** all modules (file-level attribute; observed in `cli.py`)
- **Location:** file-level
- **Evidence:** The file-level `__audit_id__` is `"task-manager-cli"` (the project name)
  rather than the module name (`"cli"`), whereas the ORG-042 convention example uses the
  module's own name (`__audit_id__ = "manager"`). This is a file-level attribute outside
  the strict scope of any single handler and applies equally to every module.
- **Remediation:** If ORG-042 intends the module name, set each module's `__audit_id__`
  to its own module name. Confirm the intended convention.

#### I2. Priority validity depends solely on argparse `choices` (`cmd_add`)

- **Severity:** info
- **Affected handler:** `cmd_add`
- **Location:** line 14 (`priority=args.priority`); parser line 66 (`choices=VALID_PRIORITIES`)
- **Evidence:** `cmd_add` passes `args.priority` straight to `Task` with no
  re-validation. It is safe *only* because `build_parser` constrains the flag with
  `choices=VALID_PRIORITIES` and defaults to `"medium"`. `Task.__init__` does not
  validate priority, so any caller invoking `cmd_add` with an out-of-range priority
  (a test, or a future non-argparse entry point) would create an invalid task. This is
  an observation about a coupling, not a bug in the current flow.
- **Remediation:** Optional — enforce `priority in VALID_PRIORITIES` on the `Task` model
  so validity does not depend solely on the parser configuration.

#### I3. `sys.exit(1)` vs `return` control-flow asymmetry (`cmd_complete`)

- **Severity:** info
- **Affected handler:** `cmd_complete` (mirrored in `cmd_delete`)
- **Location:** line 39 (`return` on success) vs. line 42 (`sys.exit(1)` on not-found)
- **Evidence:** The success path returns normally (letting `main` exit 0 implicitly)
  while the not-found path calls `sys.exit(1)` directly from the handler. This mirrors
  `cmd_delete` exactly, so it is consistent within the codebase, but calling `sys.exit`
  from within a handler couples it to process-exit semantics rather than raising and
  letting `main` translate the outcome.
- **Remediation (optional):** If exit-code handling is ever centralized, have handlers
  raise a small CLI exception (or return a status) and let `main` map it to `sys.exit`.

#### I4. Empty store vs. missing id both correctly hit not-found (`cmd_complete` / `cmd_delete`)

- **Severity:** info
- **Affected handlers:** `cmd_complete`, `cmd_delete`
- **Location:** `cmd_complete` lines 41–42; `cmd_delete` not-found branch
- **Evidence:** When `store.load()` returns `[]` (no file yet, or empty), the scan/filter
  never matches and control falls through to the not-found branch (stderr + exit 1). A
  genuinely-absent id behaves identically. This is correct and matches the AGENTS.md
  convention; recorded to confirm the edge cases were checked, not as a defect.
- **Remediation:** None required.

#### I5. Layering respected (`cmd_add`)

- **Severity:** info
- **Affected handler:** `cmd_add` (representative; all three comply)
- **Location:** lines 11–17
- **Evidence:** `cmd_add` does no direct file I/O (persistence via `store.load`/`save`),
  constructs data via the `Task` model, and owns only orchestration + user-facing output.
  This is the intended shape and should be preserved. The one divergence from the
  project's own stated convention is error handling (see L1).
- **Remediation:** None — preserve the layering; address the error-handling gap in L1.

---

## Overall risk

No critical or high-severity issues were found. All three handlers are functionally
correct for the documented single-user happy path and respect the models/storage/cli
layering.

The dominant theme is a **cross-cutting robustness gap**: the non-atomic
load-modify-save (M1) and unhandled storage/parse errors (L1) affect every mutating
handler and are best fixed in the storage layer (atomic temp-file-and-rename, optional
locking, and a top-level error boundary in `main`) rather than in the handlers
themselves. `cmd_delete` carries the most handler-specific weight: an irreversible
delete with no confirmation (M2) and silent mass-deletion of duplicate ids (M3). The
remaining low/info items are UX and consistency refinements (already-completed no-op,
duplicate-id policy divergence between complete and delete, title validation, and the
ORG-042 `__audit_id__` naming question).

Practical severity is bounded by the single-user CLI design, but the highest-value work
is (1) adding atomic writes + an error boundary in the storage/CLI layers, and (2)
making `cmd_delete` safer and more transparent about what it removes.

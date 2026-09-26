# Review: `cmd_add` (src/task_manager/cli.py)

Scope: the `cmd_add` handler only (lines 11–17), with the rest of the module and the
`models`/`storage` layers read for context. No source files were modified.

```python
def cmd_add(store, args):
    """Add a new task with the given title and priority, then save it."""
    tasks = store.load()
    task = Task(id=store.next_id(tasks), title=args.title, priority=args.priority)
    tasks.append(task)
    store.save(tasks)
    print(f"Added task {task.id}: {task.title} [{task.priority}]")
```

For each finding: title, severity, line(s), evidence, remediation.

---

## 1. Non-atomic load-modify-save (race condition / lost writes)

- **Severity:** medium (low for the documented single-user CLI use case; medium if
  invoked concurrently by scripts or multiple shells sharing one `tasks.json`)
- **Lines:** 13–16 (`store.load()` … `store.save(tasks)`)
- **Evidence:** `cmd_add` reads the whole list, appends in memory, then rewrites the
  entire file. There is no file lock, no compare-and-swap, and `next_id` is derived
  from the snapshot read at line 13. Two `add` processes racing produce a classic
  read-read-write-write interleaving: both compute the same `next_id`, both write the
  full list, and the second `save` clobbers the first — one task is silently lost and
  two tasks can share an id. `TaskStore.save` (storage.py) truncates and rewrites in
  place (`open("w")`), so there is no append-only safety net.
- **Remediation:** For the stated single-user scope this is acceptable and can be
  documented as a known limitation. If concurrency is a real concern, add locking or
  atomic replace *in the storage layer* (per AGENTS.md, persistence belongs in
  `storage.py`): e.g. an OS advisory lock (`fcntl.flock`) around a read-modify-write,
  or write to a temp file and `os.replace` it into place. `cmd_add` itself should not
  grow file-handling logic.

## 2. `save` can raise after the task is constructed — partial-work failure mode

- **Severity:** low
- **Lines:** 16 (`store.save(tasks)`), 17 (`print`)
- **Evidence:** If `store.save` raises (disk full, permission denied, path not
  writable, JSON serialization error), the exception propagates uncaught out of
  `cmd_add` → `main` → interpreter, producing a raw traceback on stderr and a non-zero
  exit. No task is persisted (good — `save` rewrites atomically enough that a failed
  write leaves the old file, though a mid-write crash could truncate it, see finding 1
  remediation). The user-facing failure is an unhandled stack trace rather than a clean
  error message, which is inconsistent with the project's own convention.
- **Remediation:** Per AGENTS.md ("errors to stderr with a non-zero exit, matching
  existing handlers"), wrap the save in a try/except that prints a friendly message to
  `stderr` and calls `sys.exit(1)`, matching the style used in `cmd_complete` /
  `cmd_delete`. Note those handlers don't guard `save` either, so this is a
  module-wide gap, not unique to `cmd_add`.

## 3. `load` can raise on a corrupt or malformed `tasks.json`

- **Severity:** low
- **Lines:** 13 (`store.load()`)
- **Evidence:** `store.load()` → `_read_raw()` calls `json.load`, and
  `Task.from_dict` does `data["id"]` / `data["title"]` with hard `KeyError` on missing
  keys. A hand-edited or truncated `tasks.json` makes `cmd_add` fail with a
  `json.JSONDecodeError` or `KeyError` traceback before any add work happens. Again
  surfaced as a raw traceback rather than a handled CLI error.
- **Remediation:** Handle read/parse errors at the CLI boundary (or normalize them in
  the storage layer) and emit a clear stderr message with `sys.exit(1)`. Root cause is
  in `storage`/`models`; `cmd_add` inherits the failure mode.

## 4. Title is not validated — empty / whitespace / control-character titles accepted

- **Severity:** low
- **Lines:** 14 (`title=args.title`)
- **Evidence:** `argparse` requires the positional `title` to be present but does not
  constrain its content. `python main.py add ""` creates a task with an empty title;
  a title of only spaces, a newline, or terminal control/escape sequences is stored
  verbatim and later echoed by `cmd_list`. This is an input-handling gap rather than a
  security hole (JSON serialization neutralizes injection into the file), but empty
  titles are almost certainly unintended.
- **Remediation:** If empty titles are undesirable, reject blank/whitespace-only titles
  with a stderr message and non-zero exit. Given the layering conventions, basic
  presence validation fits in the CLI handler; richer rules could live on the `Task`
  model.

## 5. Priority correctness — safe here, but only because of the parser

- **Severity:** info
- **Lines:** 14 (`priority=args.priority`), parser 66 (`choices=VALID_PRIORITIES`)
- **Evidence:** `cmd_add` passes `args.priority` straight to `Task` with no
  re-validation. It is safe *only* because `build_parser` constrains the flag with
  `choices=VALID_PRIORITIES` and defaults to `"medium"`. `Task.__init__` itself does
  not validate priority, so any caller invoking `cmd_add` with an out-of-range
  `args.priority` (e.g. a test, or a future non-argparse entry point) would create an
  invalid task. This is an observation about a coupling, not a bug in the current flow.
- **Remediation:** Optional — enforce `priority in VALID_PRIORITIES` on the `Task`
  model (models.py) so validity does not depend solely on the parser configuration.

## 6. Layering adherence — compliant

- **Severity:** info
- **Lines:** 11–17
- **Evidence:** `cmd_add` correctly respects the AGENTS.md separation: it does no file
  I/O directly (all persistence goes through `store.load`/`store.save`), constructs
  data via the `Task` model, and owns only orchestration + user-facing output
  (`print`). This is the intended shape and should be preserved. The one place it
  diverges from the project's own stated convention is error handling (findings 2–3):
  AGENTS.md says user errors should go to stderr with a non-zero exit, and `cmd_add`
  currently lets exceptions escape as tracebacks.

---

## Summary (risk-ranked)

| # | Finding | Severity |
|---|---------|----------|
| 1 | Non-atomic load-modify-save; concurrent adds lose writes / duplicate ids | medium |
| 2 | `save` failure surfaces as an uncaught traceback, not a clean CLI error | low |
| 3 | Corrupt/malformed `tasks.json` makes `load` raise a raw traceback | low |
| 4 | Title content unvalidated (empty/whitespace/control chars accepted) | low |
| 5 | Priority validity depends solely on the argparse `choices`, not the model | info |
| 6 | Models/storage/cli layering respected (error-handling convention is the gap) | info |

`cmd_add` is functionally correct for the documented single-user happy path. The real
weaknesses are robustness under failure and concurrency, and several fixes belong in
`storage.py`/`models.py` rather than in the handler, consistent with the AGENTS.md
layering rules.

# Gaps Filled — Status Note

Date: 2026-09-25

Three project gaps were filled in parallel by separate subagents, then verified.

## What was added

| Area | File | Result |
|------|------|--------|
| Unit tests — models | `tests/test_models.py` | 9 tests, all passing |
| Unit tests — storage | `tests/test_storage.py` | 9 tests, all passing (temp-file isolated) |
| Documentation | `docs/OVERVIEW.md` | Architecture, module responsibilities, usage, conventions |

All work uses the Python standard library only (`unittest`, no third-party deps),
consistent with the project's dependency policy. No source files were modified.

### `tests/test_models.py`
Covers `Task` construction (defaults and explicit values), `to_dict` completeness
and JSON-serializability, `from_dict` round-tripping and default-filling for missing
optional keys, `KeyError` on missing required keys (`id`/`title`), and the contents of
`VALID_PRIORITIES`. Does not assert priority validation, because `models.py` does not
implement it.

### `tests/test_storage.py`
Covers `TaskStore.load` on a missing file (returns `[]`), `save`→`load` round-trips
(including empty list), on-disk JSON validity, and `next_id` (1 when empty, `max+1`
otherwise). Every filesystem test is confined to a `tempfile` temp directory created in
`setUp` and removed in `tearDown`; the real `tasks.json` is never touched.

### `docs/OVERVIEW.md`
Documents what the CLI does, the `src/` layout and the models/storage/cli layer
separation (with a command-flow diagram), per-module responsibilities, concrete
usage examples for `add`/`list`/`complete`/`delete`, and the project conventions.
Grounded in the actual source.

## Verification

- `tests/test_models.py` — `python3 -m unittest tests.test_models` → **9 OK**.
- `tests/test_storage.py` — `python3 -m unittest tests.test_storage` → **9 OK**.
- Full suite (`unittest discover`) → 21 tests, **3 failures**, all in the
  pre-existing `tests/test_list_completion_marker.py` (see below). The 18 tests
  added by this task all pass.

## Known items (not introduced by this task)

1. **Expected failing tests — `tests/test_list_completion_marker.py`.** These are the
   bug-condition exploration tests from the `list-completion-marker-inverted` spec.
   They are *designed to fail* on the current code because the `cmd_list` bug
   (inverted marker + unreachable render loop) has not been fixed yet. They will pass
   once that spec's fix is implemented. This is the intended pre-fix state, not a
   regression from the work added here.

2. **storage.py malformed-JSON handling.** `src/task_manager/AGENTS.md` states storage
   should "raise clear, specific errors on malformed or unreadable JSON," but
   `storage.py` calls `json.load` directly and lets a raw `json.JSONDecodeError`
   (a `ValueError` subclass) propagate. `tests/test_storage.py` asserts the *actual*
   behavior (`ValueError`) and documents the gap; `docs/OVERVIEW.md` describes the real
   behavior rather than the aspirational convention. Worth addressing in the code
   separately.

# Implementation Plan

## Overview

This plan fixes the inverted completion marker and unreachable render loop in `cmd_list` using the exploratory bugfix workflow. It follows a linear sequence: first write a bug condition exploration test that fails on the unfixed code (proving the bug), then write preservation tests that pass on the unfixed code (capturing behavior to protect), then implement the fix, and finally re-run both to confirm the bug is resolved without regressions.

## Tasks

- [-] 1. Write bug condition exploration test
  - **Property 1: Bug Condition** - Marker Matches Completion State
  - **CRITICAL**: This test MUST FAIL on unfixed code - failure confirms the bug exists
  - **DO NOT attempt to fix the test or the code when it fails**
  - **NOTE**: This test encodes the expected behavior - it will validate the fix when it passes after implementation
  - **GOAL**: Surface counterexamples that demonstrate the bug exists and confirm the root cause (the dead render loop, not just the inverted ternary)
  - **Scoped PBT Approach**: The bug is deterministic (`isBugCondition(X)` returns true for every rendered task). Scope the property to concrete, reproducible cases: one completed task and one incomplete task, plus a mixed non-empty list. Use `unittest` (Python standard library only — no external deps).
  - Populate a `TaskStore` (pointed at a temp `tasks.json`) with known tasks, invoke `cmd_list`, and capture stdout to assert on emitted lines (assertions stay at the CLI/output boundary per project layering)
  - Test that a completed task (e.g. id 1, title "Write the report", priority "high") renders exactly `[x] 1. Write the report (high)` (from Bug Condition + Expected Behavior 2.1 in design)
  - Test that an incomplete task (e.g. id 2, title "Buy milk", priority "low") renders exactly `[ ] 2. Buy milk (low)` (from Expected Behavior 2.2 in design)
  - Test that a mixed non-empty list prints exactly one correctly-marked line per task in load order
  - The test assertions match the Expected Behavior Properties from design: `X.completed IMPLIES line starts with "[x] "` AND `NOT X.completed IMPLIES line starts with "[ ] "` AND line ends with `{id}. {title} ({priority})`
  - Run test on UNFIXED code
  - **EXPECTED OUTCOME**: Test FAILS (this is correct - it proves the bug exists). Because the `for t in tasks:` loop is dead code (nested inside `if not tasks:` after its `return`), the non-empty store prints **zero** task lines
  - Document counterexamples found to understand root cause (e.g. "cmd_list with a non-empty store prints no task lines because the render loop is unreachable; the inverted ternary `mark = ' ' if t.completed else 'x'` is masked by the dead loop")
  - Mark task complete when test is written, run, and failure is documented
  - _Requirements: 1.1, 1.2, 2.1, 2.2_

- [~] 2. Write preservation property tests (BEFORE implementing fix)
  - **Property 2: Preservation** - Non-Marker Output Unchanged
  - **IMPORTANT**: Follow observation-first methodology — run the UNFIXED code, record actual outputs, then assert those outputs. Use `unittest` (Python standard library only)
  - **Segment note**: The id/title/priority segment cannot be observed on unfixed code (dead render loop prints nothing). Per the design's Preservation Test Plan, assert the segment against its specification — requirement 3.1's `{id}. {title} ({priority})` format — as part of the fix-checking line assertion, rather than against pre-fix observed output
  - Observe: with an empty store, `cmd_list` prints `No tasks yet.` on unfixed code — write a test asserting this message is printed and no task lines follow (validates 3.2)
  - Observe: `cmd_add` output/side effects on unfixed code (e.g. `Added task {id}: {title} [{priority}]` and the task persisted to the store) — write a test capturing that behavior (validates 3.3)
  - Observe: `cmd_complete` output/side effects on unfixed code — success path (`Completed task {id}: {title}` and `completed=True` persisted) and not-found path (`Task {id} not found.` to stderr with non-zero exit) — write tests capturing that behavior (validates 3.3)
  - Observe: `cmd_delete` output/side effects on unfixed code — success path (`Deleted task {id}` and task removed) and not-found path (`Task {id} not found.` to stderr with non-zero exit) — write tests capturing that behavior (validates 3.3)
  - Write property-based-style tests over varying id, title, priority, and completion values where practical (stdlib generators/parametrization) to strengthen the id/title/priority segment guarantee from Preservation Requirements in design
  - Run tests on UNFIXED code
  - **EXPECTED OUTCOME**: Tests PASS (this confirms baseline behavior to preserve). The empty-list and add/complete/delete paths are reachable and correct today
  - Mark task complete when tests are written, run, and passing on unfixed code
  - _Requirements: 3.1, 3.2, 3.3_

- [ ] 3. Fix for inverted completion marker and unreachable render loop in `cmd_list`

  - [~] 3.1 Implement the fix in `cmd_list` (`src/task_manager/cli.py`)
    - Dedent the `for t in tasks:` render loop out of the `if not tasks:` block to function-body indentation so it executes after the early `return` (makes list rendering reachable — the decisive defect)
    - Correct the marker ternary: change `mark = " " if t.completed else "x"` to `mark = "x" if t.completed else " "` so completed tasks render `[x]` and incomplete tasks render `[ ]`
    - Preserve the print format exactly: `print(f"[{mark}] {t.id}. {t.title} ({t.priority})")` — only the value of `mark` and the reachability of the loop change
    - Add a docstring to `cmd_list` matching the package convention that every public function has a docstring (e.g. `"""List all tasks with a completion marker, id, title, and priority."""`)
    - Do NOT modify `models.py`, `storage.py`, or the `cmd_add`/`cmd_complete`/`cmd_delete` handlers
    - _Bug_Condition: isBugCondition(X) returns true for every task rendered by `list` (from design)_
    - _Expected_Behavior: expectedBehavior(result) — `X.completed IMPLIES marker = "[x]"` AND `NOT X.completed IMPLIES marker = "[ ]"`, line emitted, id/title/priority segment intact (from design)_
    - _Preservation: id/title/priority `{id}. {title} ({priority})` segment, "No tasks yet." message, and `add`/`complete`/`delete` commands unchanged (from design)_
    - _Requirements: 2.1, 2.2, 3.1, 3.2, 3.3_

  - [~] 3.2 Verify bug condition exploration test now passes
    - **Property 1: Expected Behavior** - Marker Matches Completion State
    - **IMPORTANT**: Re-run the SAME test from task 1 - do NOT write a new test
    - The test from task 1 encodes the expected behavior; when it passes, it confirms the expected behavior is satisfied
    - Run the bug condition exploration test from step 1
    - **EXPECTED OUTCOME**: Test PASSES (confirms the render loop is now reachable and markers match completion state — bug is fixed)
    - _Requirements: 2.1, 2.2_

  - [~] 3.3 Verify preservation tests still pass
    - **Property 2: Preservation** - Non-Marker Output Unchanged
    - **IMPORTANT**: Re-run the SAME tests from task 2 - do NOT write new tests
    - Run the preservation property tests from step 2
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions — empty-list message, id/title/priority segment, and add/complete/delete unchanged)
    - Confirm all tests still pass after the fix (no regressions)
    - _Requirements: 3.1, 3.2, 3.3_

- [~] 4. Checkpoint - Ensure all tests pass
  - Run the full test suite and ensure all tests pass
  - Confirm the exploration test (task 1) now passes and preservation tests (task 2) still pass
  - Ask the user if questions arise

## Notes

- Tasks are executed in linear sequence: exploration test (Task 1) and preservation tests (Task 2) are both written and run BEFORE the fix — Task 1 must FAIL on unfixed code, Task 2 must PASS on unfixed code.
- Task 3.1 implements the fix based on the understanding surfaced by Tasks 1 and 2; Task 3.2 re-runs Task 1's test (must now pass) and Task 3.3 re-runs Task 2's tests (must still pass).
- Task 4 is the final checkpoint and depends on Tasks 3.2 and 3.3 both succeeding.
- Use `unittest` from the Python standard library only — no external dependencies are added.

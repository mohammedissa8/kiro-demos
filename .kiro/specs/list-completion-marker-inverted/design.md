# List Completion Marker Inverted Bugfix Design

## Overview

The `list` command renders each task line with a leading completion marker that
is supposed to be `[x]` for completed tasks and `[ ]` for incomplete tasks. Two
defects in `cmd_list` (`src/task_manager/cli.py`) prevent this:

1. **Inverted marker ternary.** The marker is computed as
   `mark = " " if t.completed else "x"`, which emits `[ ]` for completed tasks
   and `[x]` for incomplete tasks — the reverse of the intended convention.

2. **Unreachable render loop (dead code).** The `for t in tasks:` loop is
   indented one level too deep, placing it *inside* the `if not tasks:` block
   and *after* that block's `return`. As a result the loop never executes:
   when the list is empty the function returns first, and when the list is
   non-empty the `if` block (and therefore the nested loop) is skipped
   entirely. Today `list` prints nothing at all when tasks exist.

The second defect is decisive for this fix. If we corrected only the inverted
ternary, observed behavior would not change, because the marker code is never
reached. The fix must **dedent the loop** out of the `if not tasks:` block so
it runs after the early return, **and** correct the ternary so the marker
reflects the true completion state. The rest of each line — id, title, and
priority — and all other command behavior must be preserved.

The change is confined to `cmd_list` in `cli.py`, honoring the project layering
convention that all rendering and user-facing output lives in the CLI layer.

## Glossary

- **Bug_Condition (C)**: The condition that triggers the bug — a task is being
  rendered by the `list` command. Because the render loop is dead and the
  marker is inverted, every rendered task is affected, so `C(X)` holds for all
  tasks passed to the list renderer.
- **Property (P)**: The desired behavior — a completed task renders `[x]` and an
  incomplete task renders `[ ]`, with the id/title/priority segment intact, and
  the line is actually emitted (loop reachable).
- **Preservation**: Behavior that must remain unchanged — the
  `{id}. {title} ({priority})` segment of each line, the "No tasks yet."
  empty-list message, and the `add`, `complete`, and `delete` commands.
- **cmd_list**: The command handler in `src/task_manager/cli.py` that loads
  tasks from the store and prints one line per task.
- **t.completed**: The boolean flag on the `Task` dataclass that determines
  whether a task is done; it drives the marker rendering.
- **F**: The original (unfixed) `list` behavior — the render loop is
  unreachable, so no task lines are printed; had it run, it would emit inverted
  markers.
- **F'**: The fixed `list` behavior — the render loop runs and emits `[x]` for
  completed and `[ ]` for incomplete tasks, with all other output identical
  to the intended design.

## Bug Details

### Bug Condition

The bug manifests whenever the `list` command renders tasks. There are two
compounding causes: the render loop is unreachable (indented inside the
`if not tasks:` block after its `return`), and the marker ternary is inverted.
Both must be addressed for the observable behavior to become correct.

**Formal Specification:**
```
FUNCTION isBugCondition(X)
  INPUT: X of type Task (a task being rendered by `list`)
  OUTPUT: boolean

  // The marker is inverted for every rendered task, and the render loop
  // is dead code, so the bug condition holds for all tasks.
  RETURN true
END FUNCTION
```

### Examples

- **Completed task, expected vs actual**: A task with `completed = True`,
  id 1, title "Write the report", priority "high" should render
  `[x] 1. Write the report (high)`. Because the loop is dead code, the current
  output prints *nothing* for this task. (Even if the loop ran, the inverted
  ternary would produce `[ ] 1. Write the report (high)`.)

- **Incomplete task, expected vs actual**: A task with `completed = False`,
  id 2, title "Buy milk", priority "low" should render
  `[ ] 2. Buy milk (low)`. Current output: nothing printed (dead loop). If the
  loop ran, the inverted ternary would produce `[x] 2. Buy milk (low)`.

- **Multiple tasks**: With one completed and one incomplete task present,
  `list` currently prints no task lines at all. Expected: one correctly-marked
  line per task, in load order.

- **Edge case — empty list**: With no tasks, `list` prints `No tasks yet.` and
  returns. This is correct today and must be preserved unchanged.

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
- The id/title/priority segment of each task line must remain in the exact
  `{id}. {title} ({priority})` format that follows the marker.
- The empty-list path must continue to print `No tasks yet.` and return without
  printing any task lines.
- The `add`, `complete`, and `delete` commands must produce their existing
  output and side effects unchanged.

**Scope:**
The fix is limited to making the render loop reachable and correcting the
marker for completed vs incomplete tasks. The following must be completely
unaffected:
- The empty-list message and its early-return control flow.
- The formatting of the id, title, and priority portion of each line.
- The `add`, `complete`, and `delete` command handlers.
- Persistence (`TaskStore.load`/`save`) and the `Task` model — no changes there.

## Hypothesized Root Cause

Based on inspection of `cmd_list`, the causes are confirmed by reading the
source (not merely hypothesized):

1. **Incorrect indentation of the render loop (dead code)**: The
   `for t in tasks:` loop is nested inside the `if not tasks:` block and placed
   after its `return`. Python never reaches it: the empty case returns early,
   and the non-empty case skips the `if` body. This is why `list` prints
   nothing when tasks exist. The loop must be dedented to function-body level so
   it runs after the early return.

2. **Inverted completion-marker ternary**: `mark = " " if t.completed else "x"`
   assigns the empty marker to completed tasks and the checked marker to
   incomplete tasks. The operands must be swapped to
   `mark = "x" if t.completed else " "`.

3. **Interaction between the two**: The dead-code defect masks the marker
   defect. A fix targeting only the ternary would not change observed behavior,
   so both must be corrected together for the bug to be resolved and verifiable.

## Correctness Properties

Property 1: Bug Condition - Marker Matches Completion State

_For any_ task rendered by the `list` command (isBugCondition returns true), the
fixed `cmd_list` SHALL print exactly one line for that task in which the marker
is `[x]` when `t.completed` is true and `[ ]` when `t.completed` is false,
followed by the unchanged `{id}. {title} ({priority})` segment.

**Validates: Requirements 2.1, 2.2**

Property 2: Preservation - Non-Marker Output Unchanged

_For any_ behavior outside the per-task marker — the id/title/priority segment
of each line, the "No tasks yet." empty-list message, and the `add`,
`complete`, and `delete` commands — the fixed code SHALL produce exactly the
same output and behavior as intended, preserving all non-marker functionality.

**Validates: Requirements 3.1, 3.2, 3.3**

## Fix Implementation

### Changes Required

**File**: `src/task_manager/cli.py`

**Function**: `cmd_list`

**Specific Changes**:

1. **Dedent the render loop out of the `if not tasks:` block**: Move
   `for t in tasks:` and its body to the function-body indentation level so it
   executes after the early `return`, making the list rendering reachable.

2. **Correct the marker ternary**: Change
   `mark = " " if t.completed else "x"` to
   `mark = "x" if t.completed else " "` so completed tasks render `[x]` and
   incomplete tasks render `[ ]`.

3. **Preserve the print format**: Keep the line format exactly as
   `print(f"[{mark}] {t.id}. {t.title} ({t.priority})")` — only the value of
   `mark` and the reachability of the loop change.

4. **Remove the now-obsolete `# BUG: inverted` comment** on the marker line for
   clarity, since the defect is resolved.

5. **Add a module-conventions-compliant docstring to `cmd_list`** (the handler
   currently lacks one), matching the sibling `cmd_*` handlers and the package
   requirement that every public function has a docstring.

The corrected structure:

```python
def cmd_list(store, args):
    """List all tasks with a completion marker, id, title, and priority."""
    tasks = store.load()
    if not tasks:
        print("No tasks yet.")
        return
    for t in tasks:
        mark = "x" if t.completed else " "
        print(f"[{mark}] {t.id}. {t.title} ({t.priority})")
```

No changes are made to `models.py`, `storage.py`, or any other command handler.

## Testing Strategy

### Validation Approach

The testing strategy follows a two-phase approach: first, surface
counterexamples that demonstrate the bug on the unfixed code, then verify the
fix produces correct markers for both completion states and preserves all
non-marker behavior. Tests exercise `cmd_list` output via captured stdout,
keeping all assertions at the CLI/output boundary consistent with the project's
layering conventions.

### Exploratory Bug Condition Checking

**Goal**: Surface counterexamples that demonstrate the bug BEFORE implementing
the fix, and confirm the root cause. In particular, confirm that the dead-code
defect (unreachable loop) — not just the inverted ternary — is responsible for
the observed behavior. If a counterexample refutes this, we must re-hypothesize.

**Test Plan**: Populate the store with known tasks, run `cmd_list`, capture
stdout, and assert on the emitted lines. Run against the UNFIXED code to observe
that no task lines are printed (dead loop), then reason about what the marker
would be once the loop is reachable.

**Test Cases**:
1. **Completed task renders checked marker**: Add a completed task, run `list`,
   assert a line `[x] {id}. {title} ({priority})` is printed (will fail on
   unfixed code — nothing is printed).
2. **Incomplete task renders empty marker**: Add an incomplete task, run `list`,
   assert a line `[ ] {id}. {title} ({priority})` is printed (will fail on
   unfixed code — nothing is printed).
3. **Non-empty list prints one line per task**: Add two tasks, run `list`,
   assert two task lines are printed in load order (will fail on unfixed code —
   zero lines printed).
4. **Edge case — empty list message**: With no tasks, run `list`, assert
   `No tasks yet.` is printed and no task lines follow (passes on unfixed code;
   guards against regression).

**Expected Counterexamples**:
- On unfixed code, `list` prints no task lines for a non-empty store because the
  render loop is unreachable.
- Possible causes: loop indented inside the `if not tasks:` block after
  `return` (dead code); inverted marker ternary (masked by the dead loop).

### Fix Checking

**Goal**: Verify that for all inputs where the bug condition holds (every
rendered task), the fixed function produces the expected marker and line.

**Pseudocode:**
```
FOR ALL X WHERE isBugCondition(X) DO
  line := renderListLine_fixed(X)      // one line emitted by cmd_list for task X
  ASSERT (X.completed IMPLIES line starts with "[x] ")
     AND (NOT X.completed IMPLIES line starts with "[ ] ")
     AND line ends with f"{X.id}. {X.title} ({X.priority})"
END FOR
```

### Preservation Checking

**Goal**: Verify that for all behavior where the bug condition does NOT apply —
i.e., the non-marker portions of output and the other commands — the fixed code
produces the same result as the original.

**Pseudocode:**
```
FOR ALL behavior B WHERE B is non-marker output DO
  ASSERT F(B) = F'(B)
END FOR

// Concretely:
ASSERT F'(empty list)  = "No tasks yet."            // unchanged
ASSERT F'(add)         = F(add)                      // unchanged output/side effects
ASSERT F'(complete)    = F(complete)                 // unchanged
ASSERT F'(delete)      = F(delete)                   // unchanged
ASSERT f"{id}. {title} ({priority})" segment unchanged for each rendered line
```

**Testing Approach**: Property-based testing is recommended for preservation
checking because:
- It generates many task configurations automatically across the input domain
  (varying id, title, priority, and completion state).
- It catches edge cases that manual unit tests might miss (e.g., unusual titles
  or priority values).
- It provides strong guarantees that the id/title/priority segment and the
  empty-list message are unchanged for all inputs.

**Test Plan**: Because the render loop is dead on unfixed code, the
id/title/priority segment cannot be observed pre-fix. The intended segment
format is fixed by requirement 3.1 (`{id}. {title} ({priority})`), so
preservation tests assert against that specification. For the empty-list message
and the `add`/`complete`/`delete` commands, observe behavior on the unfixed code
first (those paths are reachable and correct today), then write tests capturing
that behavior.

**Test Cases**:
1. **Id/title/priority segment preserved**: For any task, assert the fixed line
   ends with `{id}. {title} ({priority})` exactly (validates 3.1).
2. **Empty-list message preserved**: Observe `No tasks yet.` on unfixed code
   with an empty store, then assert it still prints unchanged after the fix
   (validates 3.2).
3. **Add command preserved**: Observe `add` output/side effects on unfixed code,
   then assert unchanged after the fix (validates 3.3).
4. **Complete and delete commands preserved**: Observe `complete` and `delete`
   output/side effects (including not-found stderr + non-zero exit) on unfixed
   code, then assert unchanged after the fix (validates 3.3).

### Unit Tests

- Test that a completed task renders `[x] {id}. {title} ({priority})`.
- Test that an incomplete task renders `[ ] {id}. {title} ({priority})`.
- Test that a mixed non-empty list prints one correctly-marked line per task in
  load order.
- Test the empty-list path prints `No tasks yet.` with no task lines.

### Property-Based Tests

- Generate random tasks (varying id, title, priority, completion) and assert the
  marker matches completion state and the trailing segment equals
  `{id}. {title} ({priority})` (fix checking + segment preservation).
- Generate random non-empty lists and assert exactly one line is printed per
  task, in order (loop-reachability correctness).
- Generate random stores and assert `add`/`complete`/`delete` output is
  unchanged relative to the observed pre-fix behavior (preservation).

### Integration Tests

- Full flow: `add` a completed and an incomplete task, then `list`, and assert
  both lines appear with correct markers and correct id/title/priority.
- Context flow: `add` → `complete` → `list` and assert the completed task now
  renders `[x]` while others render `[ ]`.
- `delete` a task then `list` and assert the remaining tasks render correctly
  and the deleted task's line is absent.

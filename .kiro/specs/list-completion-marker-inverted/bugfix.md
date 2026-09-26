# Bugfix Requirements Document

## Introduction

The `list` command in the task manager CLI renders an inverted completion
marker for each task. Completed tasks are displayed with `[ ]` (the empty
marker) while incomplete tasks are displayed with `[x]` (the checked marker).
This is the reverse of the intended convention, where `[x]` signals a completed
task and `[ ]` signals an incomplete one. The inversion misleads users about
which tasks are done, undermining the core purpose of the list view. The
remainder of each line — the task id, title, and priority — is rendered
correctly and must be preserved by the fix.

## Bug Analysis

### Current Behavior (Defect)

When the user runs the `list` command, the completion marker at the start of
each task line is inverted relative to the task's actual completion state.

1.1 WHEN the `list` command is run and a task is completed THEN the system displays the marker `[ ]` for that task
1.2 WHEN the `list` command is run and a task is not completed THEN the system displays the marker `[x]` for that task

### Expected Behavior (Correct)

The completion marker must reflect the task's actual completion state, using
`[x]` for completed tasks and `[ ]` for incomplete tasks.

2.1 WHEN the `list` command is run and a task is completed THEN the system SHALL display the marker `[x]` for that task
2.2 WHEN the `list` command is run and a task is not completed THEN the system SHALL display the marker `[ ]` for that task

### Unchanged Behavior (Regression Prevention)

The rest of the list output, and all other command behavior, must remain
exactly as it is today.

3.1 WHEN the `list` command is run THEN the system SHALL CONTINUE TO display each task's id, title, and priority in the existing `{id}. {title} ({priority})` format after the marker
3.2 WHEN the `list` command is run and there are no tasks THEN the system SHALL CONTINUE TO display "No tasks yet."
3.3 WHEN the `add`, `complete`, or `delete` commands are run THEN the system SHALL CONTINUE TO produce their existing output and behavior unchanged

## Bug Condition

The bug affects the rendered marker for a single task during `list`. The input
to the affected behavior is a task's completion flag.

### Bug Condition Function

```pascal
FUNCTION isBugCondition(X)
  INPUT: X of type Task
  OUTPUT: boolean

  // The marker is inverted for every task rendered by `list`,
  // regardless of completion state.
  RETURN true
END FUNCTION
```

The marker rendering is incorrect for both completion states, so the bug
condition holds for all tasks passed to the list renderer.

### Property Specification (Fix Checking)

```pascal
// Property: Fix Checking - Marker matches completion state
FOR ALL X WHERE isBugCondition(X) DO
  marker ← renderMarker'(X)
  ASSERT (X.completed IMPLIES marker = "[x]")
     AND (NOT X.completed IMPLIES marker = "[ ]")
END FOR
```

### Preservation Goal (Preservation Checking)

```pascal
// Property: Preservation Checking - Non-marker output is unchanged
FOR ALL X WHERE NOT isBugCondition(X) DO
  ASSERT F(X) = F'(X)
END FOR
```

Because `isBugCondition` holds for all rendered tasks, preservation is
expressed against the portions of behavior outside the marker: the id, title,
and priority segment of each line, the empty-list message, and the `add`,
`complete`, and `delete` commands must all produce identical output before
(`F`) and after (`F'`) the fix.

**Key Definitions:**
- **F**: The original (unfixed) `list` rendering — emits `[ ]` for completed and `[x]` for incomplete tasks.
- **F'**: The fixed `list` rendering — emits `[x]` for completed and `[ ]` for incomplete tasks, with all other output identical to F.

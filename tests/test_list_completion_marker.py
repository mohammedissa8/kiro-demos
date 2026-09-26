"""Bug condition exploration test for the inverted list completion marker.

This test encodes the *expected* behavior of the ``list`` command's completion
marker (Property 1: Bug Condition - Marker Matches Completion State):

    X.completed        IMPLIES line starts with "[x] "
    NOT X.completed    IMPLIES line starts with "[ ] "
    line ends with     f"{id}. {title} ({priority})"

It is EXPECTED TO FAIL on the unfixed code, and that failure confirms the bug
exists. Do not "fix" this test to make it pass on unfixed code.

Assertions are kept at the CLI/output boundary: we populate a ``TaskStore``
pointed at a temporary ``tasks.json``, invoke ``cmd_list``, capture stdout, and
assert on the emitted lines. No source under ``src/`` is modified.
"""
import io
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

# Mirror main.py's src-layout shim so ``task_manager`` is importable without
# installing the project.
_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from task_manager.cli import cmd_list  # noqa: E402
from task_manager.models import Task  # noqa: E402
from task_manager.storage import TaskStore  # noqa: E402


class _Args:
    """Minimal stand-in for the argparse Namespace passed to command handlers."""


def _run_cmd_list(tasks):
    """Populate a temp-backed TaskStore with ``tasks`` and capture cmd_list output.

    Returns the list of non-empty stdout lines emitted by ``cmd_list``.
    """
    with tempfile.TemporaryDirectory() as tmp:
        store = TaskStore(path=str(Path(tmp) / "tasks.json"))
        store.save(tasks)
        buf = io.StringIO()
        with redirect_stdout(buf):
            cmd_list(store, _Args())
        return [line for line in buf.getvalue().splitlines() if line != ""]


class ListCompletionMarkerBugConditionTest(unittest.TestCase):
    """Marker must match completion state for every rendered task."""

    def test_completed_task_renders_checked_marker(self):
        """A completed task renders exactly ``[x] 1. Write the report (high)``."""
        task = Task(id=1, title="Write the report", completed=True, priority="high")
        lines = _run_cmd_list([task])
        self.assertEqual(
            lines,
            ["[x] 1. Write the report (high)"],
            "completed task should render a single '[x] ...' line",
        )

    def test_incomplete_task_renders_empty_marker(self):
        """An incomplete task renders exactly ``[ ] 2. Buy milk (low)``."""
        task = Task(id=2, title="Buy milk", completed=False, priority="low")
        lines = _run_cmd_list([task])
        self.assertEqual(
            lines,
            ["[ ] 2. Buy milk (low)"],
            "incomplete task should render a single '[ ] ...' line",
        )

    def test_mixed_list_renders_one_correct_line_per_task_in_order(self):
        """A mixed non-empty list prints one correctly-marked line per task in load order."""
        tasks = [
            Task(id=1, title="Write the report", completed=True, priority="high"),
            Task(id=2, title="Buy milk", completed=False, priority="low"),
        ]
        lines = _run_cmd_list(tasks)

        # One line per task, in load order.
        self.assertEqual(len(lines), len(tasks), "one line should be printed per task")

        for task, line in zip(tasks, lines):
            expected_marker = "[x] " if task.completed else "[ ] "
            self.assertTrue(
                line.startswith(expected_marker),
                f"line {line!r} should start with {expected_marker!r} for completed={task.completed}",
            )
            expected_tail = f"{task.id}. {task.title} ({task.priority})"
            self.assertTrue(
                line.endswith(expected_tail),
                f"line {line!r} should end with {expected_tail!r}",
            )


if __name__ == "__main__":
    unittest.main()

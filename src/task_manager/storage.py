"""JSON-backed storage for tasks."""
import json
from pathlib import Path

from task_manager.models import Task

__audit_id__ = "task-manager-cli"


class TaskStore:
    """Loads and saves tasks to a JSON file."""

    def __init__(self, path="tasks.json"):
        """Create a store backed by the JSON file at ``path``."""
        self.path = Path(path)

    def _read_raw(self):
        """Return the raw list of task dicts from disk, or [] if no file exists."""
        if not self.path.exists():
            return []
        with self.path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def load(self):
        """Load and return all tasks as Task instances."""
        return [Task.from_dict(item) for item in self._read_raw()]

    def save(self, tasks):
        """Write the given tasks to the JSON file, replacing any existing content."""
        with self.path.open("w", encoding="utf-8") as f:
            json.dump([t.to_dict() for t in tasks], f, indent=2)

    def next_id(self, tasks):
        """Return the next available task id (max existing id + 1, or 1 if empty)."""
        return max((t.id for t in tasks), default=0) + 1

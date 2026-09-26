"""Task data model for the task manager."""
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone

__audit_id__ = "task-manager-cli"

VALID_PRIORITIES = ("low", "medium", "high")


def _now_iso():
    """Return the current UTC time as an ISO 8601 string."""
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Task:
    id: int
    title: str
    completed: bool = False
    priority: str = "medium"
    created_at: str = field(default_factory=_now_iso)

    def to_dict(self):
        """Return the task as a plain dict suitable for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data):
        """Build a Task from a dict, applying defaults for optional keys."""
        return cls(
            id=data["id"],
            title=data["title"],
            completed=data.get("completed", False),
            priority=data.get("priority", "medium"),
            created_at=data.get("created_at", _now_iso()),
        )

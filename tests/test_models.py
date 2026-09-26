"""Unit tests for the task_manager.models module.

Uses only the Python standard-library ``unittest`` framework.
"""
import json
import os
import sys
import unittest

# Mirror main.py: put <workspace>/src on the import path before importing.
sys.path.insert(
    0,
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"),
)

from task_manager.models import Task, VALID_PRIORITIES  # noqa: E402


class TestTaskConstruction(unittest.TestCase):
    """Tests for constructing Task instances."""

    def test_defaults(self):
        """A Task built with only required fields applies documented defaults."""
        task = Task(id=1, title="Write the report")
        self.assertEqual(task.id, 1)
        self.assertEqual(task.title, "Write the report")
        self.assertFalse(task.completed)
        self.assertEqual(task.priority, "medium")
        self.assertIsInstance(task.created_at, str)
        self.assertNotEqual(task.created_at, "")

    def test_explicit_values(self):
        """Explicitly supplied field values are stored as given."""
        task = Task(
            id=42,
            title="Ship it",
            completed=True,
            priority="high",
            created_at="2024-01-01T00:00:00+00:00",
        )
        self.assertEqual(task.id, 42)
        self.assertEqual(task.title, "Ship it")
        self.assertTrue(task.completed)
        self.assertEqual(task.priority, "high")
        self.assertEqual(task.created_at, "2024-01-01T00:00:00+00:00")


class TestSerialization(unittest.TestCase):
    """Tests for to_dict / from_dict serialization."""

    def test_to_dict_contains_all_fields(self):
        """to_dict returns a dict with every field and correct values."""
        task = Task(
            id=7,
            title="Task 7",
            completed=True,
            priority="low",
            created_at="2024-05-05T12:00:00+00:00",
        )
        data = task.to_dict()
        self.assertIsInstance(data, dict)
        self.assertEqual(
            data,
            {
                "id": 7,
                "title": "Task 7",
                "completed": True,
                "priority": "low",
                "created_at": "2024-05-05T12:00:00+00:00",
            },
        )

    def test_to_dict_is_json_serializable(self):
        """The dict produced by to_dict can be serialized with json.dumps."""
        task = Task(id=3, title="JSON friendly")
        encoded = json.dumps(task.to_dict())
        decoded = json.loads(encoded)
        self.assertEqual(decoded["id"], 3)
        self.assertEqual(decoded["title"], "JSON friendly")

    def test_from_dict_round_trips(self):
        """from_dict on to_dict output reproduces an equal Task."""
        original = Task(
            id=9,
            title="Round trip",
            completed=True,
            priority="high",
            created_at="2024-06-06T06:06:06+00:00",
        )
        restored = Task.from_dict(original.to_dict())
        self.assertEqual(restored, original)

    def test_from_dict_applies_defaults_for_missing_optional_keys(self):
        """from_dict fills in defaults when optional keys are absent."""
        task = Task.from_dict({"id": 5, "title": "Only required"})
        self.assertEqual(task.id, 5)
        self.assertEqual(task.title, "Only required")
        self.assertFalse(task.completed)
        self.assertEqual(task.priority, "medium")
        self.assertIsInstance(task.created_at, str)
        self.assertNotEqual(task.created_at, "")

    def test_from_dict_requires_id(self):
        """A missing required 'id' key raises KeyError."""
        with self.assertRaises(KeyError):
            Task.from_dict({"title": "No id"})

    def test_from_dict_requires_title(self):
        """A missing required 'title' key raises KeyError."""
        with self.assertRaises(KeyError):
            Task.from_dict({"id": 1})


class TestValidPriorities(unittest.TestCase):
    """Tests for the VALID_PRIORITIES constant."""

    def test_contains_expected_values(self):
        """VALID_PRIORITIES contains low, medium and high."""
        self.assertIn("low", VALID_PRIORITIES)
        self.assertIn("medium", VALID_PRIORITIES)
        self.assertIn("high", VALID_PRIORITIES)


if __name__ == "__main__":
    unittest.main()

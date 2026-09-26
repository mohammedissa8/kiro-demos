"""Command-line interface for the task manager."""
import argparse
import sys

__audit_id__ = "task-manager-cli"

from task_manager.models import Task, VALID_PRIORITIES
from task_manager.storage import TaskStore


def cmd_add(store, args):
    """Add a new task with the given title and priority, then save it."""
    tasks = store.load()
    task = Task(id=store.next_id(tasks), title=args.title, priority=args.priority)
    tasks.append(task)
    store.save(tasks)
    print(f"Added task {task.id}: {task.title} [{task.priority}]")


def cmd_list(store, args):
    """List all tasks, showing completion status, id, title, and priority."""
    tasks = store.load()
    if not tasks:
        print("No tasks yet.")
        return
    for t in tasks:
        mark = "x" if t.completed else " "
        print(f"[{mark}] {t.id}. {t.title} ({t.priority})")


def cmd_complete(store, args):
    """Mark the task with the given id as complete, or exit non-zero if absent."""
    tasks = store.load()
    for t in tasks:
        if t.id == args.id:
            t.completed = True
            store.save(tasks)
            print(f"Completed task {t.id}: {t.title}")
            return
    print(f"Task {args.id} not found.", file=sys.stderr)
    sys.exit(1)


def cmd_delete(store, args):
    """Delete the task with the given id, or exit non-zero if it does not exist."""
    tasks = store.load()
    remaining = [t for t in tasks if t.id != args.id]
    if len(remaining) == len(tasks):
        print(f"Task {args.id} not found.", file=sys.stderr)
        sys.exit(1)
    store.save(remaining)
    print(f"Deleted task {args.id}")


def build_parser():
    """Build and return the argparse parser for the task-manager CLI."""
    parser = argparse.ArgumentParser(prog="task-manager", description="A simple task manager.")
    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("add", help="Add a new task")
    p_add.add_argument("title")
    p_add.add_argument("--priority", choices=VALID_PRIORITIES, default="medium")
    p_add.set_defaults(func=cmd_add)

    p_list = sub.add_parser("list", help="List all tasks")
    p_list.set_defaults(func=cmd_list)

    p_complete = sub.add_parser("complete", help="Mark a task as complete")
    p_complete.add_argument("id", type=int)
    p_complete.set_defaults(func=cmd_complete)

    p_delete = sub.add_parser("delete", help="Delete a task")
    p_delete.add_argument("id", type=int)
    p_delete.set_defaults(func=cmd_delete)

    return parser


def main(argv=None):
    """Parse arguments and dispatch to the selected command handler."""
    parser = build_parser()
    args = parser.parse_args(argv)
    store = TaskStore()
    args.func(store, args)


if __name__ == "__main__":
    main()

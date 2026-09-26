# AGENTS.md

## Overview
Task Manager CLI is a small command-line application for tracking tasks. Each task has a title, a priority (low/medium/high), a completion flag, and a creation timestamp. Tasks are persisted to a local JSON file, and users manage them through `add`, `list`, `complete`, and `delete` subcommands.

## Tech Stack
- Language: Python 3 (uses `dataclasses`, `datetime`, `pathlib`, type hints).
- Standard library only — `argparse` (CLI parsing), `json` (persistence), `dataclasses` (the task model). No external dependencies (`requirements.txt` is empty by design).
- `src/` layout; `main.py` is a shim that puts `src/` on the import path.

## Architecture
- `src/task_manager/models.py` — Defines the `Task` dataclass and `VALID_PRIORITIES`, plus `to_dict`/`from_dict` serialization. Pure data, no I/O.
- `src/task_manager/storage.py` — `TaskStore` reads/writes the JSON file and assigns IDs (`load`, `save`, `next_id`). Owns all persistence.
- `src/task_manager/cli.py` — `argparse` parser and the `cmd_*` command handlers. Orchestrates models + storage; owns all user-facing output.
- `main.py` — Entry point that calls `task_manager.cli.main`.

## Running
```
python main.py add "Write the report" --priority high
python main.py list
python main.py complete 1
python main.py delete 1
```
Tasks are stored in `tasks.json` in the current working directory (created on first `add`).

## Conventions for Editing
- Preserve the models / storage / cli layer separation: keep data logic in `models.py`, all file I/O in `storage.py`, and argument parsing plus output in `cli.py`. Do not read/write files from models or CLI handlers directly.
- Keep it dependency-free — use only the Python standard library.
- Add a docstring to every public module, class, and function.
- Route user messages through the CLI layer (`print`, and errors to `stderr` with a non-zero exit, matching existing handlers).

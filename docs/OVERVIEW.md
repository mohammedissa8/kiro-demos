# Task Manager CLI — Project Overview

## 1. Overview

Task Manager CLI is a small command-line application for tracking tasks. Each
task carries:

- a **title** (free text),
- a **priority** — one of `low`, `medium`, or `high` (default `medium`),
- a **completion flag** (`completed`, default `False`), and
- a **creation timestamp** (`created_at`, an ISO-8601 UTC string set when the task is created).

Tasks are persisted to a local JSON file (`tasks.json`) and managed through four
subcommands: `add`, `list`, `complete`, and `delete`. The application uses the
Python standard library only — there are no external dependencies.

## 2. Architecture

The project uses a `src/` layout with a clear three-layer separation. The
importable package lives under `src/task_manager/`, and `main.py` at the repo
root is a thin entry-point shim.

- **`models.py` — pure data, no I/O.** Defines the `Task` dataclass, the
  `VALID_PRIORITIES` constant, and `to_dict` / `from_dict` serialization
  helpers. It performs no file, network, or other I/O.
- **`storage.py` — owns all persistence.** `TaskStore` reads and writes the JSON
  file and assigns IDs (`load`, `save`, `next_id`). All file access is confined
  to this layer.
- **`cli.py` — argument parsing and user-facing output.** Builds the `argparse`
  parser and holds the `cmd_*` command handlers. It orchestrates the models and
  storage layers and owns everything printed to the user (`stdout`, and errors
  to `stderr` with a non-zero exit).
- **`main.py` — entry-point shim.** Inserts `src/` onto `sys.path` so
  `python main.py` works without installing the project, then calls
  `task_manager.cli.main`.

### Command flow

```
              python main.py <command> ...
                        │
                        ▼
   main.py  ── puts src/ on sys.path, calls ──►  cli.main()
                        │
                        ▼
               cli.build_parser()  ── parses argv ──►  args.func
                        │
                        ▼
              cmd_add / cmd_list / cmd_complete / cmd_delete
                    │                         │
       reads/writes │                         │ constructs/serializes
                    ▼                         ▼
          storage.TaskStore            models.Task
        (load / save / next_id)   (VALID_PRIORITIES, to_dict/from_dict)
                    │
                    ▼
                tasks.json
```

A command handler loads tasks through `TaskStore`, works with `Task` objects,
saves back through `TaskStore`, and prints the outcome. Data logic stays in
`models.py`, persistence in `storage.py`, and parsing plus output in `cli.py`.

## 3. Module Responsibilities

### `src/task_manager/models.py`

Pure data model, no I/O.

- **`VALID_PRIORITIES`** — the tuple `("low", "medium", "high")`, used by the CLI
  to constrain the `--priority` choices.
- **`Task`** — a `@dataclass` with fields `id: int`, `title: str`,
  `completed: bool = False`, `priority: str = "medium"`, and
  `created_at: str`, where `created_at` defaults to the current UTC time as an
  ISO-8601 string (via an internal `_now_iso()` helper using
  `datetime.now(timezone.utc).isoformat()`).
  - **`to_dict()`** — returns the task as a plain `dict` (via `dataclasses.asdict`).
  - **`from_dict(data)`** — classmethod that rebuilds a `Task` from a dict,
    defaulting `completed` to `False`, `priority` to `"medium"`, and
    `created_at` to a fresh timestamp when those keys are absent.

### `src/task_manager/storage.py`

JSON-backed persistence. Owns all file access.

- **`TaskStore`** — constructed with a `path` (default `"tasks.json"`), stored as
  a `pathlib.Path`.
  - **`load()`** — reads the JSON file and returns a list of `Task` objects
    (each built with `Task.from_dict`). If the file does not exist, returns an
    empty list.
  - **`save(tasks)`** — writes the given tasks to the JSON file as an array of
    dicts (`indent=2`, UTF-8).
  - **`next_id(tasks)`** — returns the next integer id: the maximum existing id
    plus one, or `1` when there are no tasks (`default=0` plus one).
  - **`_read_raw()`** — internal helper that returns the parsed JSON list (or an
    empty list when the file is missing).

### `src/task_manager/cli.py`

Argument parsing and all user-facing output.

- **`build_parser()`** — creates the `argparse.ArgumentParser` (prog
  `task-manager`) with a required subcommand and registers the four
  subcommands, wiring each to its handler via `set_defaults(func=...)`:
  - `add` — positional `title`, optional `--priority` (choices from
    `VALID_PRIORITIES`, default `medium`).
  - `list` — no arguments.
  - `complete` — positional `id` (`int`).
  - `delete` — positional `id` (`int`).
- **`cmd_add(store, args)`** — loads tasks, creates a `Task` with a freshly
  assigned id (`store.next_id`), appends and saves it, and prints
  `Added task <id>: <title> [<priority>]`.
- **`cmd_list(store, args)`** — loads tasks and prints each as
  `[ ] <id>. <title> (<priority>)` (using `x` inside the brackets for completed
  tasks). Prints `No tasks yet.` when the list is empty.
- **`cmd_complete(store, args)`** — finds the task by id, sets `completed = True`,
  saves, and prints `Completed task <id>: <title>`. If no task matches, prints
  `Task <id> not found.` to `stderr` and exits with status `1`.
- **`cmd_delete(store, args)`** — removes the task with the matching id and saves
  the remainder, printing `Deleted task <id>`. If no task matches, prints
  `Task <id> not found.` to `stderr` and exits with status `1`.
- **`main(argv=None)`** — builds the parser, parses `argv`, constructs a
  `TaskStore`, and dispatches to the selected handler (`args.func(store, args)`).

### `main.py`

Entry-point shim for the `src/` layout. Inserts `src/` onto `sys.path` (so
`python main.py` runs without installing the package), imports
`task_manager.cli.main`, and calls it when run as a script. The module docstring
notes that a packaged project would instead use `pip install -e .` and drop this
shim.

## 4. Usage

Run the CLI through `main.py`. Tasks are stored in `tasks.json` in the **current
working directory**, created on the first `add`.

Add a task (priority defaults to `medium`):

```
python main.py add "Write the quarterly report"
```

Add a task with an explicit priority (`low` | `medium` | `high`):

```
python main.py add "Write the quarterly report" --priority high
```

List all tasks (completed tasks are marked with `x`):

```
python main.py list
```

Mark a task complete by its numeric id:

```
python main.py complete 1
```

Delete a task by its numeric id:

```
python main.py delete 1
```

## 5. Conventions

- **Standard library only.** The project depends solely on the Python standard
  library (`argparse`, `json`, `dataclasses`, `datetime`, `pathlib`);
  `requirements.txt` is empty by design.
- **Docstrings on public surface.** Every public module, class, and function
  keeps a docstring.
- **Layer separation.** Data logic stays in `models.py` (no I/O), all file access
  stays in `storage.py`, and argument parsing plus user-facing output stay in
  `cli.py`. A function's responsibility is never widened across the
  models / storage / cli boundary.
- **User messaging through the CLI layer.** Handlers print results to `stdout`
  and route errors to `stderr` with a non-zero exit code.

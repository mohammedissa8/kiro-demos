# Task Manager CLI (Java)

A small command-line task manager that stores tasks in a local JSON file. This is a
Java port of the Python `task-manager` CLI in the repository root, preserving the same
commands, output, and on-disk JSON format.

Uses the Java standard library only — **no external dependencies**. The JSON reading and
writing is hand-written (see `storage/Json.java`) to keep the project dependency-free,
mirroring the standard-library-only design of the Python original.

## Requirements

- JDK 17 or newer.

## Build & Run

Maven is configured, but the project has no dependencies, so plain `javac`/`java` works too.

### With `javac` / `java`

```sh
# compile
javac -d out $(find src/main/java -name '*.java')

# run
java -cp out com.example.taskmanager.Main add "Write the quarterly report" --priority high
java -cp out com.example.taskmanager.Main list
java -cp out com.example.taskmanager.Main complete 1
java -cp out com.example.taskmanager.Main delete 1
```

### With Maven

```sh
mvn package
java -jar target/task-manager.jar list
```

Tasks are saved to `tasks.json` in the current directory.

## Commands

| Command | Description |
|---------|-------------|
| `add <title> [--priority low\|medium\|high]` | Add a new task (default priority: `medium`). |
| `list` | List all tasks with their completion status. |
| `complete <id>` | Mark a task complete. Exits `1` if the id is not found. |
| `delete <id>` | Delete a task. Exits `1` if the id is not found. |

Invalid arguments (unknown command, bad priority, non-integer id) print an error to
`stderr` and exit `2`.

## Architecture

The Java port keeps the same three-layer separation as the Python version:

- `model/` — `Task` and `Priority`. Pure data, no I/O. `toMap`/`fromMap` handle serialization.
- `storage/` — `TaskStore` owns all file I/O (`load`, `save`, `nextId`); `Json` is the
  minimal dependency-free JSON reader/writer.
- `cli/` — `Cli` parses arguments and owns all user-facing output (stdout for messages,
  stderr for errors). `Main` is the thin entry point.

# Task Manager CLI

A small command-line task manager that stores tasks in a local JSON file. Uses the Python standard library only — no external dependencies.

## Run

```
python main.py add "Write the quarterly report" --priority high
python main.py list
python main.py complete 1
python main.py delete 1
```

Tasks are saved to `tasks.json` in the current directory.

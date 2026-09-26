# Task Manager CLI — Release Notes (v1.0)

## What's New

Task Manager CLI is a small, fast command-line tool for tracking your tasks. This release gives you everything you need to add tasks, see what's on your plate, mark work done, and clear out tasks you no longer need — all from the terminal, with no extra software to install.

Your tasks are saved automatically to a local `tasks.json` file in whatever directory you run the tool from, so your list is always right where you left it.

## Commands

You interact with the tool through `python main.py` followed by a command.

### Add a task

Create a new task, optionally setting its priority:

```
python main.py add "Write the quarterly report" --priority high
```

- `--priority` accepts a priority level for the task (for example, `high`).

### List your tasks

Show all of your current tasks:

```
python main.py list
```

### Complete a task

Mark a task as done by its number:

```
python main.py complete 1
```

### Delete a task

Remove a task by its number:

```
python main.py delete 1
```

## Installation & Upgrade

There is nothing extra to install. The tool uses only the Python standard library, so as long as you have Python available, you can run it directly:

```
python main.py list
```

To upgrade, replace your existing copy of the tool with the new version. Your `tasks.json` file is not touched by the update, so your saved tasks carry over.

## Things to Know

- Your tasks are stored in a file named `tasks.json` in the current directory. If you run the tool from a different folder, it will look for (or create) the task list there.
- Because the task list is tied to the directory you run from, run the commands from the same folder each time to see the same list.

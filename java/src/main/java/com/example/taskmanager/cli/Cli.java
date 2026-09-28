package com.example.taskmanager.cli;

import com.example.taskmanager.model.Priority;
import com.example.taskmanager.model.Task;
import com.example.taskmanager.storage.TaskStore;

import java.io.PrintStream;
import java.util.List;

/**
 * Command-line interface for the task manager.
 *
 * <p>Owns argument parsing and all user-facing output. Orchestrates the model and storage
 * layers: normal messages go to stdout, errors go to stderr, and failures exit non-zero —
 * matching the behavior of the original Python CLI.
 */
public final class Cli {

    private static final String PROG = "task-manager";

    private final TaskStore store;
    private final PrintStream out;
    private final PrintStream err;

    /**
     * Create a CLI backed by the default task store, writing to {@code System.out}/{@code System.err}.
     */
    public Cli() {
        this(new TaskStore(), System.out, System.err);
    }

    /**
     * Create a CLI with explicit collaborators, primarily for testing.
     *
     * @param store the task store to use for persistence
     * @param out   the stream for normal output
     * @param err   the stream for error output
     */
    public Cli(TaskStore store, PrintStream out, PrintStream err) {
        this.store = store;
        this.out = out;
        this.err = err;
    }

    /**
     * Parse arguments, dispatch to the selected command, and return a process exit code.
     *
     * @param argv the command-line arguments
     * @return {@code 0} on success, non-zero on error
     */
    public int run(String[] argv) {
        if (argv.length == 0) {
            err.println(usage());
            err.println(PROG + ": error: the following arguments are required: command");
            return 2;
        }

        String command = argv[0];
        String[] rest = new String[argv.length - 1];
        System.arraycopy(argv, 1, rest, 0, rest.length);

        try {
            return switch (command) {
                case "add" -> cmdAdd(rest);
                case "list" -> cmdList(rest);
                case "complete" -> cmdComplete(rest);
                case "delete" -> cmdDelete(rest);
                case "-h", "--help" -> {
                    out.println(usage());
                    yield 0;
                }
                default -> {
                    err.println(usage());
                    err.println(PROG + ": error: argument command: invalid choice: '" + command
                            + "' (choose from add, list, complete, delete)");
                    yield 2;
                }
            };
        } catch (UsageException e) {
            err.println(e.getMessage());
            return 2;
        }
    }

    /**
     * Add a new task with the given title and priority, then save it.
     *
     * @param args the arguments following the {@code add} subcommand
     * @return the exit code ({@code 0} on success)
     */
    private int cmdAdd(String[] args) {
        String title = null;
        Priority priority = Priority.DEFAULT;

        for (int i = 0; i < args.length; i++) {
            String arg = args[i];
            if (arg.equals("--priority")) {
                if (i + 1 >= args.length) {
                    throw new UsageException(PROG + " add: error: argument --priority: expected one argument");
                }
                priority = parsePriority(args[++i]);
            } else if (arg.startsWith("--priority=")) {
                priority = parsePriority(arg.substring("--priority=".length()));
            } else if (title == null) {
                title = arg;
            } else {
                throw new UsageException(PROG + " add: error: unrecognized arguments: " + arg);
            }
        }

        if (title == null) {
            throw new UsageException(PROG + " add: error: the following arguments are required: title");
        }

        List<Task> tasks = store.load();
        Task task = new Task(store.nextId(tasks), title, priority);
        tasks.add(task);
        store.save(tasks);
        out.println("Added task " + task.getId() + ": " + task.getTitle() + " [" + task.getPriority().value() + "]");
        return 0;
    }

    /**
     * List all tasks, showing completion status, id, title, and priority.
     *
     * @param args the arguments following the {@code list} subcommand
     * @return the exit code ({@code 0} on success)
     */
    private int cmdList(String[] args) {
        List<Task> tasks = store.load();
        if (tasks.isEmpty()) {
            out.println("No tasks yet.");
            return 0;
        }
        for (Task t : tasks) {
            String mark = t.isCompleted() ? "x" : " ";
            out.println("[" + mark + "] " + t.getId() + ". " + t.getTitle() + " (" + t.getPriority().value() + ")");
        }
        return 0;
    }

    /**
     * Mark the task with the given id as complete, or return non-zero if it is absent.
     *
     * @param args the arguments following the {@code complete} subcommand
     * @return the exit code ({@code 0} on success, {@code 1} if not found)
     */
    private int cmdComplete(String[] args) {
        int id = parseIdArg(args, "complete");
        List<Task> tasks = store.load();
        for (Task t : tasks) {
            if (t.getId() == id) {
                t.setCompleted(true);
                store.save(tasks);
                out.println("Completed task " + t.getId() + ": " + t.getTitle());
                return 0;
            }
        }
        err.println("Task " + id + " not found.");
        return 1;
    }

    /**
     * Delete the task with the given id, or return non-zero if it does not exist.
     *
     * @param args the arguments following the {@code delete} subcommand
     * @return the exit code ({@code 0} on success, {@code 1} if not found)
     */
    private int cmdDelete(String[] args) {
        int id = parseIdArg(args, "delete");
        List<Task> tasks = store.load();
        List<Task> remaining = new java.util.ArrayList<>();
        for (Task t : tasks) {
            if (t.getId() != id) {
                remaining.add(t);
            }
        }
        if (remaining.size() == tasks.size()) {
            err.println("Task " + id + " not found.");
            return 1;
        }
        store.save(remaining);
        out.println("Deleted task " + id);
        return 0;
    }

    /**
     * Parse a required integer id positional argument for a subcommand.
     *
     * @param args    the subcommand arguments
     * @param command the subcommand name, used in error messages
     * @return the parsed id
     */
    private int parseIdArg(String[] args, String command) {
        if (args.length == 0) {
            throw new UsageException(PROG + " " + command + ": error: the following arguments are required: id");
        }
        try {
            return Integer.parseInt(args[0]);
        } catch (NumberFormatException e) {
            throw new UsageException(PROG + " " + command + ": error: argument id: invalid int value: '" + args[0] + "'");
        }
    }

    /**
     * Parse and validate a {@code --priority} value against the allowed choices.
     *
     * @param value the raw priority string
     * @return the parsed priority
     */
    private Priority parsePriority(String value) {
        try {
            return Priority.fromValue(value);
        } catch (IllegalArgumentException e) {
            throw new UsageException(PROG + " add: error: argument --priority: invalid choice: '" + value
                    + "' (choose from " + Priority.choices() + ")");
        }
    }

    /**
     * Return the top-level usage string.
     *
     * @return the usage line for the program
     */
    private String usage() {
        return "usage: " + PROG + " [-h] {add,list,complete,delete} ...";
    }

    /** Signals an argument-parsing error that should exit with code 2. */
    private static final class UsageException extends RuntimeException {
        UsageException(String message) {
            super(message);
        }
    }
}

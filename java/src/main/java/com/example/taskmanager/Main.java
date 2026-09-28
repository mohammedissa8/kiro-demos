package com.example.taskmanager;

import com.example.taskmanager.cli.Cli;

/**
 * Entry point for the task manager CLI.
 *
 * <p>Thin shim that delegates to {@link Cli} and translates the returned code into the
 * process exit status, mirroring the Python {@code main.py} entry point.
 */
public final class Main {

    private Main() {
    }

    /**
     * Program entry point.
     *
     * @param args the command-line arguments
     */
    public static void main(String[] args) {
        int exitCode = new Cli().run(args);
        if (exitCode != 0) {
            System.exit(exitCode);
        }
    }
}

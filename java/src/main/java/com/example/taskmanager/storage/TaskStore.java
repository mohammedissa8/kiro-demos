package com.example.taskmanager.storage;

import com.example.taskmanager.model.Task;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

/**
 * JSON-backed storage for tasks.
 *
 * <p>Owns all persistence: loading tasks from disk, saving them back, and assigning ids.
 * No other layer reads or writes the task file.
 */
public final class TaskStore {

    private final Path path;

    /**
     * Create a store backed by the JSON file at the default location ({@code tasks.json}).
     */
    public TaskStore() {
        this("tasks.json");
    }

    /**
     * Create a store backed by the JSON file at the given path.
     *
     * @param path the path to the JSON file used for persistence
     */
    public TaskStore(String path) {
        this.path = Path.of(path);
    }

    /**
     * Return the raw list of task maps from disk, or an empty list if no file exists.
     *
     * @return the parsed task maps
     */
    @SuppressWarnings("unchecked")
    private List<Map<String, Object>> readRaw() {
        if (!Files.exists(path)) {
            return new ArrayList<>();
        }
        try {
            String content = Files.readString(path, StandardCharsets.UTF_8);
            if (content.isBlank()) {
                return new ArrayList<>();
            }
            Object parsed = Json.parse(content);
            List<Map<String, Object>> result = new ArrayList<>();
            for (Object item : (List<Object>) parsed) {
                result.add((Map<String, Object>) item);
            }
            return result;
        } catch (IOException e) {
            throw new UncheckedIOException("Failed to read tasks from " + path, e);
        }
    }

    /**
     * Load and return all tasks as {@link Task} instances.
     *
     * @return the list of stored tasks
     */
    public List<Task> load() {
        List<Task> tasks = new ArrayList<>();
        for (Map<String, Object> item : readRaw()) {
            tasks.add(Task.fromMap(item));
        }
        return tasks;
    }

    /**
     * Write the given tasks to the JSON file, replacing any existing content.
     *
     * @param tasks the tasks to persist
     */
    public void save(List<Task> tasks) {
        List<Object> raw = new ArrayList<>();
        for (Task task : tasks) {
            raw.add(task.toMap());
        }
        try {
            Files.writeString(path, Json.write(raw), StandardCharsets.UTF_8);
        } catch (IOException e) {
            throw new UncheckedIOException("Failed to write tasks to " + path, e);
        }
    }

    /**
     * Return the next available task id (max existing id + 1, or 1 if empty).
     *
     * @param tasks the current tasks
     * @return the next id to assign
     */
    public int nextId(List<Task> tasks) {
        int max = 0;
        for (Task task : tasks) {
            if (task.getId() > max) {
                max = task.getId();
            }
        }
        return max + 1;
    }
}

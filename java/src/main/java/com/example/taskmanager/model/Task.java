package com.example.taskmanager.model;

import java.time.Instant;
import java.util.LinkedHashMap;
import java.util.Map;

/**
 * Task data model for the task manager.
 *
 * <p>Pure data with no I/O: the model only knows how to hold task fields and convert
 * itself to and from a plain {@link Map} for serialization. Persistence lives in the
 * storage layer.
 */
public final class Task {

    private final int id;
    private final String title;
    private boolean completed;
    private final Priority priority;
    private final String createdAt;

    /**
     * Create a task with all fields specified.
     *
     * @param id        the unique task id
     * @param title     the task title
     * @param completed whether the task is complete
     * @param priority  the task priority
     * @param createdAt the ISO-8601 creation timestamp
     */
    public Task(int id, String title, boolean completed, Priority priority, String createdAt) {
        this.id = id;
        this.title = title;
        this.completed = completed;
        this.priority = priority;
        this.createdAt = createdAt;
    }

    /**
     * Create a new, incomplete task with the current UTC time as its creation timestamp.
     *
     * @param id       the unique task id
     * @param title    the task title
     * @param priority the task priority
     */
    public Task(int id, String title, Priority priority) {
        this(id, title, false, priority, nowIso());
    }

    /**
     * Return the current UTC time as an ISO-8601 string.
     *
     * @return the current instant formatted as ISO-8601
     */
    private static String nowIso() {
        return Instant.now().toString();
    }

    /** @return the unique task id */
    public int getId() {
        return id;
    }

    /** @return the task title */
    public String getTitle() {
        return title;
    }

    /** @return whether the task is complete */
    public boolean isCompleted() {
        return completed;
    }

    /**
     * Set the completion flag on this task.
     *
     * @param completed the new completion state
     */
    public void setCompleted(boolean completed) {
        this.completed = completed;
    }

    /** @return the task priority */
    public Priority getPriority() {
        return priority;
    }

    /** @return the ISO-8601 creation timestamp */
    public String getCreatedAt() {
        return createdAt;
    }

    /**
     * Return the task as a plain, ordered map suitable for JSON serialization.
     *
     * @return an ordered map of the task's fields
     */
    public Map<String, Object> toMap() {
        Map<String, Object> map = new LinkedHashMap<>();
        map.put("id", id);
        map.put("title", title);
        map.put("completed", completed);
        map.put("priority", priority.value());
        map.put("created_at", createdAt);
        return map;
    }

    /**
     * Build a Task from a map, applying defaults for optional keys.
     *
     * @param data a map of task fields (typically parsed from JSON)
     * @return the reconstructed task
     */
    public static Task fromMap(Map<String, Object> data) {
        int id = ((Number) data.get("id")).intValue();
        String title = (String) data.get("title");
        boolean completed = data.containsKey("completed") && Boolean.TRUE.equals(data.get("completed"));
        Priority priority = data.containsKey("priority")
                ? Priority.fromValue((String) data.get("priority"))
                : Priority.DEFAULT;
        String createdAt = data.containsKey("created_at") ? (String) data.get("created_at") : nowIso();
        return new Task(id, title, completed, priority, createdAt);
    }
}

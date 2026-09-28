package com.example.taskmanager.model;

/**
 * The priority levels a task can have.
 *
 * <p>Mirrors the Python {@code VALID_PRIORITIES} tuple ({@code low}, {@code medium},
 * {@code high}). The wire/display value is always the lowercase name.
 */
public enum Priority {
    LOW,
    MEDIUM,
    HIGH;

    /** The default priority applied when none is specified. */
    public static final Priority DEFAULT = MEDIUM;

    /**
     * Return the lowercase string form of this priority, as stored in JSON and shown to users.
     *
     * @return the lowercase priority name (e.g. {@code "medium"})
     */
    public String value() {
        return name().toLowerCase();
    }

    /**
     * Parse a priority from its lowercase string form.
     *
     * @param text the priority name, case-insensitive (e.g. {@code "high"})
     * @return the matching {@link Priority}
     * @throws IllegalArgumentException if {@code text} is not a valid priority
     */
    public static Priority fromValue(String text) {
        if (text == null) {
            throw new IllegalArgumentException("priority must not be null");
        }
        for (Priority p : values()) {
            if (p.value().equals(text.toLowerCase())) {
                return p;
            }
        }
        throw new IllegalArgumentException("invalid priority: " + text);
    }

    /**
     * Return the choices string for help/usage output, e.g. {@code "low, medium, high"}.
     *
     * @return a comma-separated list of the valid lowercase priority values
     */
    public static String choices() {
        StringBuilder sb = new StringBuilder();
        for (Priority p : values()) {
            if (sb.length() > 0) {
                sb.append(", ");
            }
            sb.append(p.value());
        }
        return sb.toString();
    }
}

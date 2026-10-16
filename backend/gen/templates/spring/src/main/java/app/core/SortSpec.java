package app.core;

/** ?sort=field or ?sort=-field. The default is newest first (id descending). */
public record SortSpec(String field, boolean desc) {
    public static final SortSpec DEFAULT = new SortSpec("id", true);
}

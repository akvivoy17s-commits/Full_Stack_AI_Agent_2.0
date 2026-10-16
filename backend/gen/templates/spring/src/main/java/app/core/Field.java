package app.core;

import java.util.List;

/** One entity field as written to schema.json (type: string|text|email|url|int|float|bool|datetime|enum|ref). */
public record Field(String name, String type, boolean required, boolean unique, List<String> values, String ref, boolean fk, boolean index, String onDelete) {
    public Field {
        values = values == null ? List.of() : List.copyOf(values);
    }
}

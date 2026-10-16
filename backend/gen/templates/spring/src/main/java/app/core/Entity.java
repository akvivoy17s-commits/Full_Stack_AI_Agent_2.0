package app.core;

import java.util.List;

/** One entity of the app spec. read / write: public | user | owner | admin. */
public record Entity(String name, String table, String path, List<Field> fields, String read, String write, List<String> searchable,
                     List<String> sensitive, String ownerField, boolean isUser, boolean internal, List<String> ops) {
    public Entity {
        fields = fields == null ? List.of() : List.copyOf(fields);
        searchable = searchable == null ? List.of() : List.copyOf(searchable);
        sensitive = sensitive == null ? List.of() : List.copyOf(sensitive);
        ops = ops == null ? List.of() : List.copyOf(ops);
    }
}

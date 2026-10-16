package app.core;

import java.util.Map;

/** The whole spec-derived contract (src/main/resources/schema.json): single source of truth for validation, routes and tests. */
public record Schema(String db, boolean auth, boolean refresh, java.util.List<String> roles, String adminRole, String defaultRole,
                     Map<String, Entity> entities, java.util.List<Map<String, Object>> seed) {
    public Schema {
        roles = roles == null ? java.util.List.of() : java.util.List.copyOf(roles);
        entities = entities == null ? Map.of() : Map.copyOf(entities);
        seed = seed == null ? java.util.List.of() : java.util.List.copyOf(seed);
    }

    public boolean mongo() { return "mongodb".equals(db); }
}

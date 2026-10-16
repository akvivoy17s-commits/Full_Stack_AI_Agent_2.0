package app.seed;

import app.core.Entity;
import app.core.Schema;
import app.data.Repo;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.regex.Pattern;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.ApplicationArguments;
import org.springframework.boot.ApplicationRunner;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.stereotype.Component;

/** `--seed=admin` creates the first admin from ADMIN_EMAIL / ADMIN_PASSWORD; `--seed=sample` adds a few fake rows per entity (idempotent). Then the process exits. */
@Component
public class SeedRunner implements ApplicationRunner {
    private static final Pattern EMAIL = Pattern.compile("^[^\\s@]+@[^\\s@]+\\.[^\\s@]{2,}$");
    private final Schema schema;
    private final Repo repo;
    @Value("${ADMIN_EMAIL:}") private String adminEmail;
    @Value("${ADMIN_PASSWORD:}") private String adminPassword;
    @Value("${APP_ENV:development}") private String env;
    @Value("${ALLOW_SAMPLE_DATA:false}") private boolean allowSample;
    @Value("${BCRYPT_ROUNDS:12}") private int rounds;

    public SeedRunner(Schema schema, Repo repo) {
        this.schema = schema;
        this.repo = repo;
    }

    @Override public void run(ApplicationArguments args) {
        List<String> what = args.getOptionValues("seed");
        if (what == null) return;
        int code = 0;
        try {
            if (what.contains("admin")) admin();
            if (what.contains("sample")) sample();
            if (!what.contains("admin") && !what.contains("sample")) throw new IllegalStateException("Use --seed=admin or --seed=sample");
        } catch (RuntimeException e) {
            System.err.println("Seed failed: " + e.getMessage());
            code = 1;
        }
        System.exit(code);
    }

    private Map<String, Object> adminRow() {
        return schema.auth() ? repo.findOne(schema.entities().get("User"), Map.of("email", adminEmail.strip().toLowerCase()), false) : null;
    }

    private void admin() {
        if (!schema.auth()) throw new IllegalStateException("This project has no sign-in");
        String email = adminEmail.strip().toLowerCase();
        if (!EMAIL.matcher(email).matches() || adminPassword.length() < 8 || adminPassword.getBytes(StandardCharsets.UTF_8).length > 72 || adminPassword.startsWith("<"))
            throw new IllegalStateException("Set ADMIN_EMAIL and ADMIN_PASSWORD (8-72 characters) in .env first");
        Entity u = schema.entities().get("User");
        if (repo.findOne(u, Map.of("email", email), false) != null) { System.out.println("That account already exists; nothing changed."); return; }
        Map<String, Object> d = new LinkedHashMap<>();
        d.put("email", email);
        d.put("name", "Administrator");
        d.put("password_hash", new BCryptPasswordEncoder(rounds).encode(adminPassword));
        d.put("role", schema.adminRole());
        if (u.fields().stream().anyMatch(f -> f.name().equals("created_at"))) d.put("created_at", Instant.now().toString());
        repo.create(u, d);
        System.out.println("Admin created: " + email);
    }

    @SuppressWarnings("unchecked")
    private void sample() {
        if (env.equals("production") && !allowSample) throw new IllegalStateException("Refusing to add sample data in production (set ALLOW_SAMPLE_DATA=true to override)");
        Map<String, List<Object>> ids = new LinkedHashMap<>();
        Map<String, Object> admin = adminRow();
        if (admin != null) ids.put("User", List.of(admin.get("id")));
        for (Map<String, Object> plan : schema.seed()) {
            String name = (String) plan.get("entity");
            Entity e = schema.entities().get(name);
            Repo.Page existing = repo.list(e, Map.of(), new app.core.ListQuery(1, 100, null, Map.of(), app.core.SortSpec.DEFAULT));
            if (existing.total() > 0) {                       // keep what is there and let later entities point at it
                ids.put(name, existing.rows().stream().map(r -> r.get("id")).sorted((a, b) -> String.valueOf(a).compareTo(String.valueOf(b))).limit(3).toList());
                System.out.println("Skipped " + name + ": it already has data.");
                continue;
            }
            List<Map<String, Object>> rows = (List<Map<String, Object>>) plan.get("rows");
            List<String> refs = new ArrayList<>();
            for (Map<String, Object> r : rows) for (Object v : r.values()) if (v instanceof Map<?, ?> m) refs.add(String.valueOf(((List<?>) m.get("$ref")).get(0)));
            if (refs.contains("User") && admin == null) { System.out.println("Skipped " + name + ": it points at a user; run --seed=admin first."); continue; }
            if (refs.stream().anyMatch(r -> !ids.containsKey(r))) { System.out.println("Skipped " + name + ": it needs records of another entity first."); continue; }
            List<Object> made = new ArrayList<>();
            for (Map<String, Object> r : rows) {
                Map<String, Object> d = new LinkedHashMap<>();
                for (var en : r.entrySet()) {
                    Object v = en.getValue();
                    if (v instanceof Map<?, ?> m) { List<?> ref = (List<?>) m.get("$ref"); v = ids.get(String.valueOf(ref.get(0))).get(((Number) ref.get(1)).intValue()); }
                    d.put(en.getKey(), v);
                }
                made.add(repo.create(e, d).get("id"));
            }
            ids.put(name, made);
            System.out.println("Added " + rows.size() + " " + name + " record(s).");
        }
    }
}

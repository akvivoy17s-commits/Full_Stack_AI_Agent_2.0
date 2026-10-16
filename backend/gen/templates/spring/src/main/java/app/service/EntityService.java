package app.service;

import app.core.ApiException;
import app.core.AuthContext;
import app.core.Entity;
import app.core.Field;
import app.core.ListQuery;
import app.core.Principal;
import app.core.Schema;
import app.core.Validator;
import app.data.Repo;
import java.time.Instant;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.springframework.stereotype.Service;

/** Spec-driven CRUD with server-side access rules: public | user | owner | admin. Other users' records answer 404, never 403. */
@Service
public class EntityService {
    private final Schema schema;
    private final Validator validator;
    private final Repo repo;
    private final AuthContext auth;

    public EntityService(Schema schema, Validator validator, Repo repo, AuthContext auth) {
        this.schema = schema;
        this.validator = validator;
        this.repo = repo;
        this.auth = auth;
    }

    /** The entity behind /api/{path}; 404 when there is none, 405 when this operation is not part of the spec. */
    public Entity entity(String path, String op) {
        Entity e = schema.entities().values().stream().filter(x -> !x.internal() && x.path().equals(path) && !x.ops().isEmpty()).findFirst()
                .orElseThrow(() -> new ApiException(404, "not_found", "Route not found"));
        if (!e.ops().contains(op)) throw new ApiException(405, "method_not_allowed", "Method not allowed");
        return e;
    }

    private boolean admin(Principal p) { return p != null && schema.adminRole().equals(p.role()); }

    private Principal guard(String level) {
        if (level.equals("public")) {
            try { return auth.current(); } catch (ApiException e) { return null; }     // a bad token does not matter on a public route
        }
        Principal p = auth.current();
        if (p == null) throw new ApiException(401, "unauthorized", "Authentication required");
        if (level.equals("admin") && !admin(p)) throw new ApiException(403, "forbidden", "You do not have access to this resource");
        return p;
    }

    private static boolean has(Entity e, String n) { return e.fields().stream().anyMatch(f -> f.name().equals(n)); }

    private Map<String, Object> load(Entity e, String rawId, String level, Principal p) {
        Object id = repo.parseId(rawId);
        Map<String, Object> rec = id == null ? null : repo.get(e, id, false);
        boolean mine = level.equals("owner") && e.ownerField() != null && !admin(p) ? String.valueOf(rec == null ? null : rec.get(e.ownerField())).equals(p.id()) : true;
        if (rec == null || !mine) throw new ApiException(404, "not_found", "Record not found");
        return rec;
    }

    private void checkRefs(Entity e, Map<String, Object> data) {
        Map<String, String> errors = new LinkedHashMap<>();
        for (Field f : e.fields()) {
            if (!f.type().equals("ref") || data.get(f.name()) == null) continue;
            Entity target = schema.entities().get(f.ref());
            if (target == null || repo.get(target, data.get(f.name()), false) == null) errors.put(f.name(), "refers to a record that does not exist");
        }
        if (!errors.isEmpty()) throw new ApiException(400, "validation_failed", "Invalid input", errors);
    }

    public Map<String, Object> list(Entity e, Map<String, List<String>> query) {
        Principal p = guard(e.read());
        ListQuery q = validator.parseList(e, query);
        Map<String, Object> where = new LinkedHashMap<>();
        if (e.read().equals("owner") && e.ownerField() != null && !admin(p)) where.put(e.ownerField(), repo.parseId(p.id()));
        Repo.Page r = repo.list(e, where, q);
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("data", r.rows());
        out.put("page", q.page());
        out.put("limit", q.limit());
        out.put("total", r.total());
        return out;
    }

    public Map<String, Object> get(Entity e, String id) { return load(e, id, e.read(), guard(e.read())); }

    public Map<String, Object> create(Entity e, Object body) {
        Principal p = guard(e.write());
        Map<String, Object> data = validator.validateBody(e, body, false);
        checkRefs(e, data);
        if (e.ownerField() != null && p != null) data.put(e.ownerField(), repo.parseId(p.id()));
        if (has(e, "created_at")) data.put("created_at", Instant.now().toString());
        return repo.create(e, data);
    }

    public Map<String, Object> update(Entity e, String rawId, Object body) {
        Principal p = guard(e.write());
        load(e, rawId, e.write(), p);
        Map<String, Object> data = validator.validateBody(e, body, true);
        checkRefs(e, data);
        if (has(e, "updated_at")) data.put("updated_at", Instant.now().toString());
        return repo.update(e, repo.parseId(rawId), data);
    }

    public void delete(Entity e, String rawId) {
        Principal p = guard(e.write());
        load(e, rawId, e.write(), p);
        repo.remove(e, repo.parseId(rawId));
    }
}

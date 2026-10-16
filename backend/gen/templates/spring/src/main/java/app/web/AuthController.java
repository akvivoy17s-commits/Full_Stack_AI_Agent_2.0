package app.web;

import app.core.ApiException;
import app.core.AuthContext;
import app.core.Entity;
import app.core.Jwt;
import app.core.Principal;
import app.core.Schema;
import app.data.Repo;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.SecureRandom;
import java.time.Instant;
import java.util.Base64;
import java.util.HexFormat;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.regex.Pattern;
import org.springframework.http.ResponseEntity;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/** Sign-up, sign-in, rotating single-use refresh tokens, sign-out, current user. Same contract as the other generated backends. */
@RestController
@RequestMapping("/api/auth")
public class AuthController {
    private static final Pattern EMAIL = Pattern.compile("^[^\\s@]+@[^\\s@]+\\.[^\\s@]{2,}$");
    private static final SecureRandom RANDOM = new SecureRandom();
    private final Schema schema;
    private final Repo repo;
    private final AuthContext auth;
    private final AuthSettings cfg;
    private final BCryptPasswordEncoder bcrypt;
    private final String dummy;

    public AuthController(Schema schema, Repo repo, AuthContext auth, AuthSettings cfg) {
        this.schema = schema;
        this.repo = repo;
        this.auth = auth;
        this.cfg = cfg;
        this.bcrypt = new BCryptPasswordEncoder(cfg.rounds());
        this.dummy = bcrypt.encode("not-a-real-password");      // equalises timing for unknown emails
    }

    private Entity user() { return schema.entities().get("User"); }
    private static boolean str(Object v, int max) { return v instanceof String s && s.length() <= max; }
    private static String sha(String t) { return HexFormat.of().formatHex(sha256(t)); }
    private static byte[] sha256(String t) {
        try { return MessageDigest.getInstance("SHA-256").digest(t.getBytes(StandardCharsets.UTF_8)); } catch (Exception e) { throw new IllegalStateException(e); }
    }
    @SuppressWarnings("unchecked")
    private static Map<String, Object> map(Object body) { return body instanceof Map<?, ?> ? (Map<String, Object>) body : Map.of(); }
    private static ApiException invalidToken() { return new ApiException(401, "invalid_token", "Invalid refresh token"); }

    private Map<String, Object> issue(Map<String, Object> u) {
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("user", u);
        out.put("accessToken", Jwt.sign(cfg.secret(), String.valueOf(u.get("id")), String.valueOf(u.get("role")), cfg.accessSeconds(), Instant.now().getEpochSecond()));
        out.put("tokenType", "Bearer");
        out.put("expiresIn", cfg.accessSeconds());
        if (schema.refresh()) {
            byte[] b = new byte[48];
            RANDOM.nextBytes(b);
            String raw = Base64.getUrlEncoder().withoutPadding().encodeToString(b);
            Map<String, Object> row = new LinkedHashMap<>();
            row.put("user_id", u.get("id"));
            row.put("token_hash", sha(raw));
            row.put("expires_at", Instant.now().plusSeconds(cfg.refreshSeconds()).toString());
            repo.create(schema.entities().get("RefreshToken"), row);
            out.put("refreshToken", raw);
        }
        return out;
    }

    @PostMapping("/register")
    public ResponseEntity<Map<String, Object>> register(@RequestBody(required = false) Object body) {
        Map<String, Object> b = map(body);
        Map<String, String> errors = new LinkedHashMap<>();
        if (!str(b.get("email"), 255) || !EMAIL.matcher(((String) b.get("email")).strip()).matches()) errors.put("email", "must be a valid email");
        if (!str(b.get("name"), 255) || ((String) b.get("name")).isBlank()) errors.put("name", "is required (max 255 characters)");
        if (!str(b.get("password"), 200) || ((String) b.get("password")).length() < 8 || ((String) b.get("password")).getBytes(StandardCharsets.UTF_8).length > 72) errors.put("password", "must be 8-72 characters");
        for (String k : b.keySet()) if (!List.of("email", "name", "password").contains(k)) errors.put(k, "is not an accepted field");
        if (!errors.isEmpty()) throw new ApiException(400, "validation_failed", "Invalid input", errors);
        Map<String, Object> data = new LinkedHashMap<>();
        data.put("email", ((String) b.get("email")).strip().toLowerCase());
        data.put("name", ((String) b.get("name")).strip());
        data.put("password_hash", bcrypt.encode((String) b.get("password")));
        data.put("role", schema.defaultRole());          // never client-controlled; the first admin comes from `--seed=admin`
        if (user().fields().stream().anyMatch(f -> f.name().equals("created_at"))) data.put("created_at", Instant.now().toString());
        return ResponseEntity.status(201).body(issue(repo.create(user(), data)));
    }

    @PostMapping("/login")
    public Map<String, Object> login(@RequestBody(required = false) Object body) {
        Map<String, Object> b = map(body);
        if (!str(b.get("email"), 255) || !str(b.get("password"), 200)) throw new ApiException(400, "validation_failed", "email and password must be text");
        Map<String, Object> raw = repo.findOne(user(), Map.of("email", ((String) b.get("email")).strip().toLowerCase()), true);
        boolean ok = bcrypt.matches((String) b.get("password"), raw == null ? dummy : String.valueOf(raw.get("password_hash")));
        if (raw == null || !ok) throw new ApiException(401, "invalid_credentials", "Invalid email or password");
        return issue(repo.get(user(), raw.get("id"), false));
    }

    @PostMapping("/refresh")
    public Map<String, Object> refresh(@RequestBody(required = false) Object body) {
        if (!schema.refresh()) throw new ApiException(404, "not_found", "Route not found");
        Object t = map(body).get("refreshToken");
        if (!str(t, 200)) throw invalidToken();
        Entity rt = schema.entities().get("RefreshToken");
        Map<String, Object> where = Map.of("token_hash", sha((String) t));
        Map<String, Object> row = repo.findOne(rt, where, true);
        // delete first, then check: a token works once, even for concurrent requests
        if (row == null || repo.removeWhere(rt, where) != 1 || Instant.parse(String.valueOf(row.get("expires_at"))).isBefore(Instant.now())) throw invalidToken();
        Map<String, Object> u = repo.get(user(), row.get("user_id"), false);
        if (u == null) throw invalidToken();
        return issue(u);
    }

    @PostMapping("/logout")
    public ResponseEntity<Void> logout(@RequestBody(required = false) Object body) {
        Principal p = auth.current();
        if (p == null) throw new ApiException(401, "unauthorized", "Authentication required");
        if (schema.refresh()) {
            Map<String, Object> where = new LinkedHashMap<>();
            where.put("user_id", repo.parseId(p.id()));
            Object t = map(body).get("refreshToken");
            if (str(t, 200)) where.put("token_hash", sha((String) t));          // without a token: sign out everywhere
            repo.removeWhere(schema.entities().get("RefreshToken"), where);
        }
        return ResponseEntity.noContent().build();
    }

    @GetMapping("/me")
    public Map<String, Object> me() {
        Principal p = auth.current();
        if (p == null) throw new ApiException(401, "unauthorized", "Authentication required");
        Object id = repo.parseId(p.id());
        Map<String, Object> u = id == null ? null : repo.get(user(), id, false);
        if (u == null) throw new ApiException(401, "invalid_token", "Account no longer exists");
        return Map.of("user", u);
    }
}

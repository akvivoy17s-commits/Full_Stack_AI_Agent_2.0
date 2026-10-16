package app;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import app.core.ApiException;
import app.core.ClientIp;
import app.core.Entity;
import app.core.Field;
import app.core.RateLimiter;
import app.core.Validator;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;

class ValidatorTest {
    static Field f(String n, String t, boolean req) { return new Field(n, t, req, false, List.of("a", "b"), null, false, false, null); }
    final Validator v = new Validator(false);
    final Entity e = new Entity("Item", "items", "items", List.of(f("title", "string", true), f("kind", "enum", false), f("qty", "int", false), f("secret", "string", false), f("owner_id", "ref", false)),
            "public", "user", List.of("title"), List.of("secret"), "owner_id", false, false, List.of("list", "get", "create", "update", "delete"));

    @Test void acceptsValidBodyAndTrims() {
        assertEquals(Map.of("title", "Hi", "qty", 3L), v.validateBody(e, Map.of("title", "  Hi ", "qty", 3), false));
    }

    @Test void rejectsUnknownSensitiveAndOwnerFields() {
        ApiException ex = assertThrows(ApiException.class, () -> v.validateBody(e, Map.of("title", "x", "secret", "y", "owner_id", 1, "role", "admin"), false));
        assertEquals(400, ex.status());
        assertEquals(Map.of("secret", "is not an accepted field", "owner_id", "is not an accepted field", "role", "is not an accepted field"), ex.details());
    }

    @Test void requiredAndTypes() {
        assertThrows(ApiException.class, () -> v.validateBody(e, Map.of(), false));
        v.validateBody(e, Map.of(), true);
        assertFalse(v.one(f("n", "int", true), true).ok());
        assertFalse(v.one(f("n", "int", true), 2147483648L).ok());
        assertTrue(v.one(f("n", "url", true), "https://example.com/x").ok());
        assertFalse(v.one(f("n", "url", true), "javascript:alert(1)").ok());
        assertFalse(v.one(f("n", "enum", true), "c").ok());
    }

    @Test void limiterAndClientIp() {
        RateLimiter r = new RateLimiter();
        assertTrue(r.allow("k", 2, 0) && r.allow("k", 2, 1));
        assertFalse(r.allow("k", 2, 2));
        assertTrue(r.allow("k", 2, RateLimiter.WINDOW_MS + 5));
        assertEquals("9.9.9.9", ClientIp.resolve("9.9.9.9", "1.1.1.1", 0));
        assertEquals("2.2.2.2", ClientIp.resolve("9.9.9.9", "6.6.6.6, 2.2.2.2", 1));
    }
}

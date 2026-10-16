package app;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNull;

import app.integrations.Cache;
import org.junit.jupiter.api.Test;

class CacheTest {
    @Test
    void memoryCacheStoresAndInvalidatesByVersion() {
        Cache c = new Cache(30, "");
        assertEquals("memory", c.backend());
        String v1 = c.version();
        c.set("r:" + v1 + ":x", "{\"a\":1}");
        assertEquals("{\"a\":1}", c.get("r:" + v1 + ":x"));
        c.invalidate();
        assertNull(c.get("r:" + c.version() + ":x"));
    }
}

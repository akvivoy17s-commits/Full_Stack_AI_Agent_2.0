package app.integrations;

import java.util.LinkedHashMap;
import java.util.Map;
import java.util.concurrent.atomic.AtomicLong;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import redis.clients.jedis.JedisPooled;

/** Read cache: Redis when REDIS_URL is set and reachable, otherwise a small in-memory TTL map. A cache failure never fails a request. */
@Component
public class Cache {
    private static final Logger LOG = LoggerFactory.getLogger(Cache.class);
    private record Entry(String value, long exp) {}

    private final int ttl;
    private final String url;
    private final AtomicLong memVer = new AtomicLong(1);
    private final Map<String, Entry> mem = new LinkedHashMap<>(16, 0.75f, false) {
        @Override protected boolean removeEldestEntry(Map.Entry<String, Entry> e) { return size() > 500; }
    };
    private JedisPooled redis;
    private long retryAt;

    public Cache(@Value("${CACHE_TTL_SECONDS:30}") int ttl, @Value("${REDIS_URL:}") String url) {
        this.ttl = Math.max(1, ttl);
        this.url = url == null ? "" : url.trim();
    }

    private synchronized JedisPooled client() {
        if (url.isEmpty() || System.currentTimeMillis() < retryAt) return redis;
        if (redis == null) {
            try {
                JedisPooled c = new JedisPooled(url);
                c.ping();
                redis = c;
            } catch (RuntimeException e) {
                LOG.warn("Redis unavailable, using the in-memory cache");
                retryAt = System.currentTimeMillis() + 30_000;
            }
        }
        return redis;
    }

    private synchronized void down() { redis = null; retryAt = System.currentTimeMillis() + 30_000; }

    public String backend() { return client() != null ? "redis" : "memory"; }

    public String version() {
        JedisPooled r = client();
        if (r != null) { try { String v = r.get("cache:ver"); return v == null ? "0" : v; } catch (RuntimeException e) { down(); } }
        return String.valueOf(memVer.get());
    }

    public String get(String key) {
        JedisPooled r = client();
        if (r != null) { try { return r.get(key); } catch (RuntimeException e) { down(); return null; } }
        synchronized (mem) {
            Entry e = mem.get(key);
            if (e == null || e.exp() < System.currentTimeMillis()) { mem.remove(key); return null; }
            return e.value();
        }
    }

    public void set(String key, String value) {
        JedisPooled r = client();
        if (r != null) { try { r.setex(key, ttl, value); } catch (RuntimeException e) { down(); } return; }
        synchronized (mem) { mem.put(key, new Entry(value, System.currentTimeMillis() + ttl * 1000L)); }
    }

    /** Any successful write bumps the version, so every cached read becomes unreachable at once (entries then expire by TTL). */
    public void invalidate() {
        memVer.incrementAndGet();
        JedisPooled r = client();
        if (r != null) { try { r.incr("cache:ver"); } catch (RuntimeException e) { down(); } }
    }
}

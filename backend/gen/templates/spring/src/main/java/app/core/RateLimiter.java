package app.core;

import java.util.HashMap;
import java.util.Map;

/** Fixed-window limiter, in memory and per process. Behind several instances use a shared store (see README). */
public final class RateLimiter {
    public static final long WINDOW_MS = 15 * 60 * 1000L;
    private record Bucket(int n, long reset) {}

    private final Map<String, Bucket> buckets = new HashMap<>();

    public synchronized boolean allow(String key, int limit, long now) {
        if (buckets.size() > 5000) buckets.values().removeIf(b -> b.reset <= now);
        Bucket b = buckets.get(key);
        if (b == null || b.reset <= now) {
            buckets.put(key, new Bucket(1, now + WINDOW_MS));
            return true;
        }
        buckets.put(key, new Bucket(b.n + 1, b.reset));
        return b.n + 1 <= limit;
    }
}

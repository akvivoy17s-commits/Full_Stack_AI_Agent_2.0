package app.checkout;

import app.integrations.Cache;
import app.integrations.Events;
import org.springframework.beans.factory.ObjectProvider;
import org.springframework.stereotype.Component;

/** Writes outside the CRUD routes (checkout, payment webhooks) must still invalidate cached reads and announce the change. */
@Component
public class Notify {
    private final ObjectProvider<Cache> cache;
    private final ObjectProvider<Events> events;

    public Notify(ObjectProvider<Cache> cache, ObjectProvider<Events> events) {
        this.cache = cache;
        this.events = events;
    }

    /** pairs: entity, op, entity, op ... */
    public void changed(String... pairs) {
        Cache c = cache.getIfAvailable();
        if (c != null) c.invalidate();
        Events ev = events.getIfAvailable();
        if (ev != null) for (int i = 0; i + 1 < pairs.length; i += 2) ev.emit(pairs[i], pairs[i + 1]);
    }
}

package app.integrations;

import java.util.List;
import java.util.Map;
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.function.Consumer;
import org.springframework.stereotype.Component;

/** In-process change announcements: metadata only ({entity, op}), never record data. */
@Component
public class Events {
    private final List<Consumer<Map<String, String>>> listeners = new CopyOnWriteArrayList<>();

    public void listen(Consumer<Map<String, String>> l) { listeners.add(l); }

    public void emit(String entity, String op) {
        Map<String, String> msg = Map.of("entity", entity, "op", op);
        for (Consumer<Map<String, String>> l : listeners) {
            try { l.accept(msg); } catch (RuntimeException ignored) { /* one bad listener must not break a request */ }
        }
    }
}

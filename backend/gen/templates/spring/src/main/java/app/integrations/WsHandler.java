package app.integrations;

import app.core.Schema;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.annotation.PreDestroy;
import java.io.IOException;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.ConcurrentHashMap;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.socket.CloseStatus;
import org.springframework.web.socket.PingMessage;
import org.springframework.web.socket.TextMessage;
import org.springframework.web.socket.WebSocketSession;
import org.springframework.web.socket.handler.TextWebSocketHandler;

/** /ws: with sign-in the client must send {"type":"auth","token":"<access token>"} within 5 s; then it receives {"type":"change","entity","op"}. */
@Component
public class WsHandler extends TextWebSocketHandler {
    private final ObjectMapper json = new ObjectMapper();
    private final Set<WebSocketSession> sessions = ConcurrentHashMap.newKeySet();
    private final Set<String> authed = ConcurrentHashMap.newKeySet();
    private final ScheduledExecutorService timer = Executors.newSingleThreadScheduledExecutor(r -> { Thread t = new Thread(r, "ws-timer"); t.setDaemon(true); return t; });
    private final WsTokens tokens;
    private final boolean needsAuth;
    private final int maxClients;

    public WsHandler(Events events, WsTokens tokens, Schema schema, @Value("${WS_MAX_CLIENTS:500}") int maxClients) {
        this.tokens = tokens;
        this.needsAuth = schema.auth();
        this.maxClients = maxClients;
        events.listen(this::broadcast);
        timer.scheduleAtFixedRate(this::ping, 30, 30, TimeUnit.SECONDS);
    }

    private void send(WebSocketSession s, String text) {
        try { synchronized (s) { if (s.isOpen()) s.sendMessage(new TextMessage(text)); } } catch (IOException | RuntimeException e) { drop(s); }
    }

    private void drop(WebSocketSession s) {
        sessions.remove(s);
        authed.remove(s.getId());
        try { s.close(CloseStatus.SERVER_ERROR); } catch (IOException | RuntimeException ignored) { /* already closed */ }
    }

    private void broadcast(Map<String, String> msg) {
        String text;
        try { text = json.writeValueAsString(Map.of("type", "change", "entity", msg.get("entity"), "op", msg.get("op"))); } catch (IOException e) { return; }
        for (WebSocketSession s : sessions) if (authed.contains(s.getId())) send(s, text);
    }

    private void ping() {
        for (WebSocketSession s : sessions) {
            try { synchronized (s) { if (s.isOpen()) s.sendMessage(new PingMessage()); } } catch (IOException | RuntimeException e) { drop(s); }
        }
    }

    @Override
    public void afterConnectionEstablished(WebSocketSession s) throws Exception {
        if (sessions.size() >= maxClients) { s.close(new CloseStatus(1013, "busy")); return; }
        s.setTextMessageSizeLimit(2048);
        sessions.add(s);
        if (!needsAuth) { authed.add(s.getId()); return; }
        timer.schedule(() -> {
            if (sessions.contains(s) && !authed.contains(s.getId())) {
                try { s.close(new CloseStatus(4401, "auth required")); } catch (IOException | RuntimeException ignored) { /* gone */ }
            }
        }, 5, TimeUnit.SECONDS);
    }

    @Override
    protected void handleTextMessage(WebSocketSession s, TextMessage message) throws Exception {
        if (authed.contains(s.getId())) return;
        try {
            JsonNode n = json.readTree(message.getPayload());
            if ("auth".equals(n.path("type").asText()) && tokens.valid(n.path("token").asText(null))) {
                authed.add(s.getId());
                send(s, "{\"type\":\"ready\"}");
                return;
            }
        } catch (IOException ignored) { /* falls through */ }
        s.close(new CloseStatus(4401, "invalid token"));
    }

    @Override
    public void afterConnectionClosed(WebSocketSession s, CloseStatus status) {
        sessions.remove(s);
        authed.remove(s.getId());
    }

    @PreDestroy
    void stop() { timer.shutdownNow(); }
}

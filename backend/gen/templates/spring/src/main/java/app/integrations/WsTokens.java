package app.integrations;

import app.core.Jwt;
import app.web.AuthSettings;
import java.time.Instant;
import org.springframework.stereotype.Component;

/** Verifies the access token a WebSocket client sends in its first message. */
@Component
public class WsTokens {
    private final AuthSettings cfg;

    public WsTokens(AuthSettings cfg) { this.cfg = cfg; }

    public boolean valid(String token) { return token != null && Jwt.verify(cfg.secret(), token, Instant.now().getEpochSecond()) != null; }
}

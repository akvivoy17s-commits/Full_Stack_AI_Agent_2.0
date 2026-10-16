package app.integrations;

import app.AppConfig;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.socket.config.annotation.EnableWebSocket;
import org.springframework.web.socket.config.annotation.WebSocketConfigurer;
import org.springframework.web.socket.config.annotation.WebSocketHandlerRegistry;

/** Only the origins in CORS_ORIGINS may open /ws (a missing Origin header, i.e. a non-browser client, is allowed). */
@Configuration
@EnableWebSocket
public class WsConfig implements WebSocketConfigurer {
    private final WsHandler handler;
    private final AppConfig cfg;

    public WsConfig(WsHandler handler, AppConfig cfg) { this.handler = handler; this.cfg = cfg; }

    @Override
    public void registerWebSocketHandlers(WebSocketHandlerRegistry reg) {
        reg.addHandler(handler, "/ws").setAllowedOrigins(cfg.corsOrigins().toArray(new String[0]));
    }
}

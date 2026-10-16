package app;

import jakarta.annotation.PostConstruct;
import java.util.Arrays;
import java.util.List;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

/** Environment settings (PORT, CORS_ORIGINS, TRUST_PROXY, APP_ENV). Invalid values stop the start-up with a readable message. */
@Component
public class AppConfig {
    @Value("${app.env:development}") private String env;
    @Value("${app.cors-origins:}") private String corsOrigins;
    @Value("${app.trust-proxy:0}") private String trustProxy;
    @Value("${server.port:8000}") private int port;

    public boolean isTest() { return "test".equals(env); }
    public List<String> corsOrigins() { return Arrays.stream(corsOrigins.split(",")).map(String::trim).filter(s -> !s.isEmpty()).toList(); }
    public int trustedProxies() { return trustProxy.matches("[0-9]{1,2}") ? Integer.parseInt(trustProxy) : 0; }

    @PostConstruct
    void validate() {
        StringBuilder errs = new StringBuilder();
        if (port < 1 || port > 65535) errs.append("PORT must be a valid port number; ");
        if (corsOrigins().isEmpty()) errs.append("CORS_ORIGINS must list the allowed browser origins (comma separated); ");
        if (!trustProxy.matches("[0-9]{1,2}")) errs.append("TRUST_PROXY must be the number of proxies in front of the API (0 = none); ");
        if (errs.length() > 0) throw new IllegalStateException("Invalid configuration: " + errs.toString().strip());
    }
}

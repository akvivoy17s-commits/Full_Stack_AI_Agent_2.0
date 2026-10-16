package app.web;

import app.core.ApiException;
import app.core.AuthContext;
import app.core.Jwt;
import app.core.Principal;
import jakarta.servlet.http.HttpServletRequest;
import java.time.Instant;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import org.springframework.stereotype.Component;
import org.springframework.web.context.request.RequestContextHolder;
import org.springframework.web.context.request.ServletRequestAttributes;

/** Reads `Authorization: Bearer <jwt>`. No header = anonymous (null); a bad or expired token = 401 invalid_token. */
@Component
public class JwtAuth implements AuthContext {
    private static final Pattern BEARER = Pattern.compile("^Bearer (.+)$", Pattern.CASE_INSENSITIVE);
    private final AuthSettings cfg;

    public JwtAuth(AuthSettings cfg) { this.cfg = cfg; }

    @Override public Principal current() {
        if (!(RequestContextHolder.getRequestAttributes() instanceof ServletRequestAttributes a)) return null;
        HttpServletRequest req = a.getRequest();
        String h = req.getHeader("Authorization");
        if (h == null) return null;
        Matcher m = BEARER.matcher(h);
        Jwt.Claims c = m.matches() ? Jwt.verify(cfg.secret(), m.group(1), Instant.now().getEpochSecond()) : null;
        if (c == null) throw new ApiException(401, "invalid_token", "Invalid or expired token");
        return new Principal(c.sub(), c.role());
    }
}

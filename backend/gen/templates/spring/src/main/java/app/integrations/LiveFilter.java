package app.integrations;

import app.core.ApiException;
import app.core.AuthContext;
import app.core.Entity;
import app.core.Schema;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HashMap;
import java.util.HexFormat;
import java.util.Map;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.Ordered;
import org.springframework.core.annotation.Order;
import org.springframework.stereotype.Component;
import org.springframework.web.context.request.RequestAttributes;
import org.springframework.web.context.request.RequestContextHolder;
import org.springframework.web.context.request.ServletRequestAttributes;
import org.springframework.web.filter.OncePerRequestFilter;
import org.springframework.web.util.ContentCachingResponseWrapper;

/** On /api/{entity}: caches GET reads per caller (X-Cache), and after every successful write invalidates the cache and announces {entity, op}. */
@Component
@Order(Ordered.HIGHEST_PRECEDENCE + 4)
public class LiveFilter extends OncePerRequestFilter {
    private static final Map<String, String> OPS = Map.of("POST", "create", "PUT", "update", "DELETE", "delete");
    private final Map<String, String> byPath = new HashMap<>();
    private final Cache cache;
    private final Events events;
    private final AuthContext auth;
    private final boolean cacheOn;

    public LiveFilter(Schema schema, Cache cache, Events events, AuthContext auth, @Value("${app.cache:false}") boolean cacheOn) {
        this.cache = cache;
        this.events = events;
        this.auth = auth;
        this.cacheOn = cacheOn;
        for (Entity e : schema.entities().values()) if (!e.internal()) byPath.put(e.path(), e.name());
    }

    private static String sha(String s) {
        try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(s.getBytes(StandardCharsets.UTF_8))).substring(0, 16); }
        catch (NoSuchAlgorithmException e) { throw new IllegalStateException(e); }
    }

    /** A cached answer must never outlive the caller's right to read it: a bad or expired token goes to the API (which answers 401). */
    private boolean tokenOk(HttpServletRequest req) {
        RequestAttributes prev = RequestContextHolder.getRequestAttributes();
        RequestContextHolder.setRequestAttributes(new ServletRequestAttributes(req));
        try { auth.current(); return true; } catch (ApiException e) { return false; } finally { RequestContextHolder.setRequestAttributes(prev); }
    }

    @Override
    protected void doFilterInternal(HttpServletRequest req, HttpServletResponse res, FilterChain chain) throws ServletException, IOException {
        String[] seg = req.getRequestURI().split("/");
        String entity = seg.length >= 3 && "api".equals(seg[1]) ? byPath.get(seg[2]) : null;
        if (entity == null) { chain.doFilter(req, res); return; }
        String method = req.getMethod();
        if ("GET".equals(method) && cacheOn) {
            String authz = req.getHeader("Authorization");
            if (authz != null && !tokenOk(req)) { chain.doFilter(req, res); return; }
            String key = "r:" + cache.version() + ":" + sha(authz == null ? "" : authz) + ":" + req.getRequestURI() + "?" + req.getQueryString();
            String hit = cache.get(key);
            if (hit != null) {
                res.setHeader("X-Cache", "HIT");
                res.setStatus(200);
                res.setContentType("application/json;charset=UTF-8");
                res.getOutputStream().write(hit.getBytes(StandardCharsets.UTF_8));
                return;
            }
            res.setHeader("X-Cache", "MISS");
            ContentCachingResponseWrapper wrap = new ContentCachingResponseWrapper(res);
            try {
                chain.doFilter(req, wrap);
                String type = wrap.getContentType();
                if (wrap.getStatus() == 200 && type != null && type.contains("json")) cache.set(key, new String(wrap.getContentAsByteArray(), StandardCharsets.UTF_8));
            } finally { wrap.copyBodyToResponse(); }
        } else if (OPS.containsKey(method)) {
            chain.doFilter(req, res);
            if (res.getStatus() < 400) {
                if (cacheOn) cache.invalidate();
                events.emit(entity, OPS.get(method));
            }
        } else chain.doFilter(req, res);
    }
}

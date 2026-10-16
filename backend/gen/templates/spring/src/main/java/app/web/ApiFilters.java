package app.web;

import app.AppConfig;
import app.core.ClientIp;
import app.core.Entity;
import app.core.Json;
import app.core.RateLimiter;
import app.core.Schema;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import org.springframework.core.Ordered;
import org.springframework.core.annotation.Order;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

/** The cross-cutting request filters, in order: security headers, CORS, body size, rate limits. */
public final class ApiFilters {
    private ApiFilters() {}

    static void fail(HttpServletResponse res, int status, String code, String message) throws IOException {
        res.setStatus(status);
        res.setContentType("application/json;charset=UTF-8");
        res.getOutputStream().write(Json.error(code, message).getBytes(StandardCharsets.UTF_8));
    }

    @Component
    @Order(Ordered.HIGHEST_PRECEDENCE)
    public static class SecurityHeaders extends OncePerRequestFilter {
        @Override
        protected void doFilterInternal(HttpServletRequest req, HttpServletResponse res, FilterChain chain) throws ServletException, IOException {
            res.setHeader("X-Content-Type-Options", "nosniff");
            res.setHeader("X-Frame-Options", "DENY");
            res.setHeader("Referrer-Policy", "no-referrer");
            res.setHeader("Content-Security-Policy", "default-src 'none'; frame-ancestors 'none'");
            res.setHeader("Strict-Transport-Security", "max-age=15552000; includeSubDomains");
            res.setHeader("Cache-Control", "no-store");
            chain.doFilter(req, res);
        }
    }

    @Component
    @Order(Ordered.HIGHEST_PRECEDENCE + 1)
    public static class Cors extends OncePerRequestFilter {
        private final List<String> origins;

        Cors(AppConfig cfg) { this.origins = cfg.corsOrigins(); }

        @Override
        protected void doFilterInternal(HttpServletRequest req, HttpServletResponse res, FilterChain chain) throws ServletException, IOException {
            String origin = req.getHeader("Origin");
            boolean allowed = origin != null && origins.contains(origin);
            if (origin != null) res.addHeader("Vary", "Origin");
            if (allowed) res.setHeader("Access-Control-Allow-Origin", origin);
            if ("OPTIONS".equals(req.getMethod()) && req.getHeader("Access-Control-Request-Method") != null) {
                if (allowed) {
                    res.setHeader("Access-Control-Allow-Methods", "GET,POST,PUT,DELETE");
                    res.setHeader("Access-Control-Allow-Headers", "Content-Type,Authorization");
                    res.setHeader("Access-Control-Max-Age", "600");
                }
                res.setStatus(204);
                return;
            }
            chain.doFilter(req, res);
        }
    }

    /** Rejects requests that DECLARE more than 100 kB (chunked bodies are not counted: also limit the size at the proxy). */
    @Component
    @Order(Ordered.HIGHEST_PRECEDENCE + 2)
    public static class BodyLimit extends OncePerRequestFilter {
        static final long MAX = 100 * 1024;

        @Override
        protected void doFilterInternal(HttpServletRequest req, HttpServletResponse res, FilterChain chain) throws ServletException, IOException {
            if (req.getContentLengthLong() > MAX /*UPLOAD_EXEMPT*/) {
                fail(res, 413, "payload_too_large", "Request body is too large");
                return;
            }
            chain.doFilter(req, res);
        }
    }

    /** 600 requests / 15 min per client for the whole API; 20 for sign-in routes; 30 for public write forms. */
    @Component
    @Order(Ordered.HIGHEST_PRECEDENCE + 3)
    public static class RateLimit extends OncePerRequestFilter {
        private final RateLimiter limiter = new RateLimiter();
        private final AppConfig cfg;
        private final List<String> publicPosts = new ArrayList<>();
        private final boolean auth;

        RateLimit(AppConfig cfg, Schema schema) {
            this.cfg = cfg;
            this.auth = schema.auth();
            for (Entity e : schema.entities().values()) if ("public".equals(e.write())) publicPosts.add("/api/" + e.path());
        }

        private boolean over(String name, String ip, int limit) {
            return !cfg.isTest() && !limiter.allow(name + ":" + ip, limit, System.currentTimeMillis());
        }

        @Override
        protected void doFilterInternal(HttpServletRequest req, HttpServletResponse res, FilterChain chain) throws ServletException, IOException {
            String ip = ClientIp.resolve(req.getRemoteAddr(), req.getHeader("X-Forwarded-For"), cfg.trustedProxies());
            String path = req.getRequestURI();
            boolean post = "POST".equals(req.getMethod());
            boolean limited = over("api", ip, 600)
                    || (auth && post && path.startsWith("/api/auth/") && over("auth", ip, 20))
                    || (post && publicPosts.contains(path) && over("public", ip, 30));
            if (limited) {
                fail(res, 429, "rate_limited", "Too many requests, try again later");
                return;
            }
            chain.doFilter(req, res);
        }
    }
}

import app.core.*;
import java.util.*;

/** Runs the Spring-free classes of the generated project with plain javac + java (no Maven, no network). Prints OK or exits 1. */
public class CoreCheck {
    static int fails;
    static void t(boolean c, String m) { if (!c) { fails++; System.out.println("FAIL " + m); } }
    static Field f(String n, String ty, boolean r) { return new Field(n, ty, r, false, List.of("a", "b"), null, false, false, null); }

    public static void main(String[] a) {
        String S = "test-secret-test-secret-test-secret-0123", tok = Jwt.sign(S, "7", "user", 60, 1000);
        t(Jwt.verify(S, tok, 1010) != null && Jwt.verify(S, tok, 1010).sub().equals("7") && Jwt.verify(S, tok, 1010).role().equals("user"), "jwt round trip");
        t(Jwt.verify(S, tok, 1060) == null, "jwt expired");
        t(Jwt.verify("other-secret-other-secret-other-1234", tok, 1010) == null, "jwt wrong key");
        String[] p = tok.split("\\.");
        t(Jwt.verify(S, p[0] + "." + p[1] + "A." + p[2], 1010) == null, "jwt tampered");
        String none = Base64.getUrlEncoder().withoutPadding().encodeToString("{\"alg\":\"none\"}".getBytes());
        t(Jwt.verify(S, none + "." + p[1] + ".", 1010) == null, "jwt alg none");
        t(Jwt.verify(S, "a.b", 1010) == null && Jwt.verify(S, "", 1010) == null, "jwt garbage");
        Validator v = new Validator(false), mv = new Validator(true);
        Entity e = new Entity("Item", "items", "items", List.of(f("title", "string", true), f("kind", "enum", false), f("qty", "int", false), f("ok", "bool", false), f("secret", "string", false),
                f("owner_id", "ref", false), f("when", "datetime", false), f("mail", "email", false), f("price", "float", false), f("course_id", "ref", false)), "public", "user", List.of("title"), List.of("secret"),
                "owner_id", false, false, List.of("list"));
        Map<String, Object> in = new LinkedHashMap<>();
        in.put("title", "  Hi "); in.put("qty", 3); in.put("when", "2024-05-01T10:00:00+02:00"); in.put("mail", " A@B.CO "); in.put("price", 2);
        Map<String, Object> out = v.validateBody(e, in, false);
        t("Hi".equals(out.get("title")) && Long.valueOf(3).equals(out.get("qty")), "trim/int");
        t("2024-05-01T08:00:00Z".equals(out.get("when")), "date " + out.get("when"));
        t("a@b.co".equals(out.get("mail")), "email lower");
        try { v.validateBody(e, Map.of("title", "x", "secret", "y", "owner_id", 1, "role", "admin", "id", 4), false); t(false, "unknown fields"); }
        catch (ApiException x) { t(x.status() == 400 && x.details().size() == 4, "details " + x.details()); }
        try { v.validateBody(e, List.of(), false); t(false, "array body"); } catch (ApiException x) { t(x.code().equals("validation_failed"), "array"); }
        try { v.validateBody(e, Map.of(), false); t(false, "required"); } catch (ApiException x) { t("is required".equals(x.details().get("title")), "required msg"); }
        v.validateBody(e, Map.of(), true);
        t(!v.one(f("n", "int", true), true).ok(), "bool is not int");
        t(!v.one(f("n", "int", true), 2147483648L).ok(), "int32 limit");
        t(v.one(f("n", "int", true), 2.0).ok(), "2.0 is int");
        t(!v.one(f("n", "int", true), 2.5).ok(), "2.5 not int");
        t(!v.one(f("n", "float", true), true).ok(), "bool not float");
        t(v.one(f("n", "url", true), "https://example.com/x").ok(), "url ok");
        t(!v.one(f("n", "url", true), "javascript:alert(1)").ok() && !v.one(f("n", "url", true), "ftp://x.y").ok() && !v.one(f("n", "url", true), "http://").ok(), "url bad");
        t(!v.one(f("n", "enum", true), "c").ok(), "enum");
        t(!v.one(f("n", "string", true), "   ").ok() && !v.one(f("n", "string", true), "x".repeat(256)).ok(), "string");
        t(!v.one(f("n", "datetime", true), "yesterday").ok() && v.one(f("n", "datetime", true), "2024-05-01").ok(), "datetime");
        t(!v.one(f("n", "ref", true), 0).ok() && v.one(f("n", "ref", true), 7).ok() && !v.one(f("n", "ref", true), "7").ok(), "ref sql");
        t(mv.one(f("n", "ref", true), "0123456789abcdef01234567").ok() && !mv.one(f("n", "ref", true), 7).ok(), "ref mongo");
        // list parsing
        ListQuery q = v.parseList(e, Map.of("page", List.of("2"), "limit", List.of("500"), "q", List.of(" hi "), "kind", List.of("a"), "ok", List.of("true"), "course_id", List.of("5")));
        t(q.page() == 2 && q.limit() == 100 && "hi".equals(q.q()) && "a".equals(q.filters().get("kind")) && Boolean.TRUE.equals(q.filters().get("ok")) && Long.valueOf(5).equals(q.filters().get("course_id")), "list " + q);
        t(v.parseList(e, Map.of()).limit() == 20, "default limit");
        t(v.parseList(e, Map.of()).sort().equals(SortSpec.DEFAULT), "default sort is -id");
        t(v.parseList(e, Map.of("sort", List.of("-id"))).sort().desc(), "sort -id");
        for (String bad : new String[] {"nope", "-", ""}) {
            try { v.parseList(e, Map.of("sort", List.of(bad))); t(false, "bad sort " + bad); } catch (ApiException x) { t(x.status() == 400, "bad sort code"); }
        }
        try { v.parseList(e, Map.of("sort", List.of("id", "-id"))); t(false, "repeated sort"); } catch (ApiException x) { t(x.status() == 400, "repeated sort code"); }
        for (Map<String, List<String>> bad : List.of(Map.of("page", List.of("0")), Map.of("limit", List.of("x")), Map.of("page", List.of("1", "2")), Map.of("kind", List.of("zzz")), Map.of("kind", List.of("a", "b")),
                Map.of("q", List.of("x".repeat(101))), Map.of("course_id", List.of("abc")))) {
            try { v.parseList(e, bad); t(false, "bad query " + bad); } catch (ApiException x) { t(x.status() == 400, "bad query code"); }
        }
        // limiter, ip, json
        RateLimiter r = new RateLimiter();
        t(r.allow("k", 2, 0) && r.allow("k", 2, 1) && !r.allow("k", 2, 2) && r.allow("k", 2, RateLimiter.WINDOW_MS + 5) && r.allow("other", 2, 2), "limiter");
        t("9.9.9.9".equals(ClientIp.resolve("9.9.9.9", "1.1.1.1", 0)) && "2.2.2.2".equals(ClientIp.resolve("9.9.9.9", "6.6.6.6, 2.2.2.2", 1)) && "9.9.9.9".equals(ClientIp.resolve("9.9.9.9", null, 2)), "ip");
        t(Json.error("c", "a\"b\n").equals("{\"error\":{\"code\":\"c\",\"message\":\"a\\\"b\\n\"}}"), "json " + Json.error("c", "a\"b\n"));
        Map<String, Object> env = Json.envelope("x", "y", null);
        t(((Map<?, ?>) env.get("error")).get("code").equals("x") && !((Map<?, ?>) env.get("error")).containsKey("details"), "envelope");
        ApiException ex = new ApiException(404, "nf", "m");
        t(ex.getStackTrace().length == 0, "no stack trace");
        System.out.println(fails == 0 ? "OK" : "FAILED " + fails);
        System.exit(fails == 0 ? 0 : 1);
    }
}

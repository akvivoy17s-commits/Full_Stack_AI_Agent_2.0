package app.core;

import java.math.BigDecimal;
import java.math.BigInteger;
import java.net.URI;
import java.time.Instant;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.OffsetDateTime;
import java.time.ZoneOffset;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.regex.Pattern;

/** Spec-driven input validation. Same rules and messages as the other generated backends. */
public final class Validator {
    static final Pattern EMAIL = Pattern.compile("^[^\\s@]+@[^\\s@]+\\.[^\\s@]{2,}$");
    static final Pattern OBJECT_ID = Pattern.compile("^[a-f0-9]{24}$", Pattern.CASE_INSENSITIVE);
    static final long INT32 = 2147483647L;                  // ids and `int` fields are 32-bit columns in every SQL database we generate for
    static final Set<String> SERVER_SET = Set.of("id", "created_at", "updated_at");

    /** Result of checking one value: either the normalised value or an error text. */
    public record Checked(Object value, String error) {
        public boolean ok() { return error == null; }
    }

    private final boolean mongo;

    public Validator(boolean mongo) { this.mongo = mongo; }

    private static Checked bad(String err) { return new Checked(null, err); }
    private static Checked good(Object v) { return new Checked(v, null); }

    private static Long asInt(Object v) {
        if (v instanceof Integer || v instanceof Long || v instanceof Short || v instanceof Byte) return ((Number) v).longValue();
        if (v instanceof BigInteger b && b.bitLength() < 63) return b.longValue();
        if (v instanceof Double || v instanceof Float || v instanceof BigDecimal) {
            double d = ((Number) v).doubleValue();
            if (Double.isFinite(d) && d == Math.floor(d) && Math.abs(d) < 1e15) return (long) d;
        }
        return null;
    }

    private static boolean isInt(Object v) {
        Long n = asInt(v);
        return n != null && Math.abs(n) <= INT32;
    }

    private static Instant parseDate(String s) {
        String t = s.trim();
        try { return OffsetDateTime.parse(t).toInstant(); } catch (RuntimeException ignored) { /* try the next shape */ }
        try { return LocalDateTime.parse(t).toInstant(ZoneOffset.UTC); } catch (RuntimeException ignored) { /* try the next shape */ }
        try { return LocalDate.parse(t).atStartOfDay().toInstant(ZoneOffset.UTC); } catch (RuntimeException ignored) { return null; }
    }

    /** Checks ONE value against its field definition. */
    public Checked one(Field f, Object v) {
        switch (f.type()) {
            case "string", "text" -> {
                if (!(v instanceof String s)) return bad("must be text");
                String t = s.strip();
                int max = f.type().equals("text") ? 20000 : 255;
                if (f.required() && t.isEmpty()) return bad("is required");
                return t.length() > max ? bad("must be at most " + max + " characters") : good(t);
            }
            case "email" -> {
                return v instanceof String s && s.length() <= 255 && EMAIL.matcher(s.strip()).matches() ? good(s.strip().toLowerCase()) : bad("must be a valid email");
            }
            case "url" -> {
                try {
                    if (!(v instanceof String s) || s.length() > 2048) throw new IllegalArgumentException();
                    URI u = new URI(s.strip());
                    if (u.getHost() == null || !(u.getScheme().equalsIgnoreCase("http") || u.getScheme().equalsIgnoreCase("https"))) throw new IllegalArgumentException();
                    return good(s.strip());
                } catch (Exception e) {
                    return bad("must be an http(s) URL");
                }
            }
            case "int" -> { return isInt(v) ? good(asInt(v)) : bad("must be a whole number between -2147483647 and 2147483647"); }
            case "float" -> { return v instanceof Number n && !(v instanceof Boolean) && Double.isFinite(n.doubleValue()) ? good(n) : bad("must be a number"); }
            case "bool" -> { return v instanceof Boolean ? good(v) : bad("must be true or false"); }
            case "datetime" -> {
                Instant i = v instanceof String s ? parseDate(s) : null;
                return i != null ? good(i.toString()) : bad("must be an ISO date-time");
            }
            case "enum" -> { return v instanceof String s && f.values().contains(s) ? good(s) : bad("must be one of: " + String.join(", ", f.values())); }
            case "ref" -> {
                boolean ok = mongo ? v instanceof String s && OBJECT_ID.matcher(s).matches() : isInt(v) && asInt(v) > 0;
                return ok ? good(mongo ? v : asInt(v)) : bad("must be a valid id");
            }
            default -> { return bad("has an unsupported type"); }
        }
    }

    /** Fields a client may write: sensitive columns, server-set timestamps and the owner link never are. */
    private static boolean writable(Entity e, Field f) {
        return !e.sensitive().contains(f.name()) && !f.name().equals(e.ownerField()) && !SERVER_SET.contains(f.name());
    }

    @SuppressWarnings("unchecked")
    public Map<String, Object> validateBody(Entity e, Object body, boolean partial) {
        if (!(body instanceof Map<?, ?>)) throw new ApiException(400, "validation_failed", "Body must be a JSON object");
        Map<String, Object> input = (Map<String, Object>) body;
        List<Field> fields = e.fields().stream().filter(f -> writable(e, f)).toList();
        Set<String> names = new java.util.HashSet<>();
        fields.forEach(f -> names.add(f.name()));
        Map<String, String> errors = new LinkedHashMap<>();
        Map<String, Object> data = new LinkedHashMap<>();
        for (String k : input.keySet()) if (!names.contains(k)) errors.put(k, "is not an accepted field");
        for (Field f : fields) {
            if (!input.containsKey(f.name())) {
                if (!partial && f.required()) errors.put(f.name(), "is required");
                continue;
            }
            Object v = input.get(f.name());
            if (v == null) {
                if (f.required()) errors.put(f.name(), "is required"); else data.put(f.name(), null);
                continue;
            }
            Checked r = one(f, v);
            if (r.ok()) data.put(f.name(), r.value()); else errors.put(f.name(), r.error());
        }
        if (!errors.isEmpty()) throw new ApiException(400, "validation_failed", "Invalid input", errors);
        return data;
    }

    private static int num(List<String> v, int dflt, long max) {
        if (v == null) return dflt;
        if (v.size() != 1 || !v.get(0).matches("[0-9]{1,15}") || Long.parseLong(v.get(0)) < 1)
            throw new ApiException(400, "validation_failed", "page and limit must be positive integers");
        return (int) Math.min(Long.parseLong(v.get(0)), max);
    }

    /** ?page, ?limit (max 100), ?q (searches the searchable text fields) and exact filters on ref / enum / bool fields. */
    public ListQuery parseList(Entity e, Map<String, List<String>> query) {
        int page = num(query.get("page"), 1, 1_000_000), limit = num(query.get("limit"), 20, 100);
        String q = null;
        if (query.containsKey("q")) {
            List<String> v = query.get("q");
            if (v.size() != 1 || v.get(0).length() > 100) throw new ApiException(400, "validation_failed", "q must be text up to 100 characters");
            q = v.get(0).strip().isEmpty() ? null : v.get(0).strip();
        }
        Map<String, Object> filters = new LinkedHashMap<>();
        for (Field f : e.fields()) {
            if (!Set.of("ref", "enum", "bool").contains(f.type()) || !query.containsKey(f.name())) continue;
            List<String> raw = query.get(f.name());
            if (raw.size() != 1) throw new ApiException(400, "validation_failed", f.name() + " must be a single value");
            Object v = raw.get(0);
            if (f.type().equals("bool")) v = raw.get(0).equals("true") ? Boolean.TRUE : raw.get(0).equals("false") ? Boolean.FALSE : raw.get(0);
            else if (f.type().equals("ref") && !mongo) v = raw.get(0).matches("[0-9]{1,15}") ? (Object) Long.valueOf(raw.get(0)) : raw.get(0);
            Checked r = one(f, v);
            if (!r.ok()) throw new ApiException(400, "validation_failed", f.name() + " " + r.error());
            filters.put(f.name(), r.value());
        }
        SortSpec sort = SortSpec.DEFAULT;
        if (query.containsKey("sort")) {
            List<String> sv = query.get("sort");
            if (sv.size() != 1) throw new ApiException(400, "validation_failed", "sort must be a single value");
            boolean desc = sv.get(0).startsWith("-");
            String name = desc ? sv.get(0).substring(1) : sv.get(0);
            boolean ok = name.equals("id") || e.fields().stream().anyMatch(f -> f.name().equals(name) && !f.type().equals("text") && !e.sensitive().contains(f.name()));
            if (!ok) throw new ApiException(400, "validation_failed", "sort must be id or a non-text field name, optionally prefixed with - for descending");
            sort = new SortSpec(name, desc);
        }
        return new ListQuery(page, limit, q, filters, sort);
    }
}

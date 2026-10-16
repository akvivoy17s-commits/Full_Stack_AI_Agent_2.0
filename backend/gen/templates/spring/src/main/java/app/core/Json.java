package app.core;

import java.util.Map;

/** Tiny JSON writer for the few places that answer without Jackson (servlet filters). */
public final class Json {
    private Json() {}

    public static String quote(String s) {
        StringBuilder b = new StringBuilder("\"");
        for (char c : s.toCharArray()) {
            switch (c) {
                case '"' -> b.append("\\\"");
                case '\\' -> b.append("\\\\");
                case '\n' -> b.append("\\n");
                case '\r' -> b.append("\\r");
                case '\t' -> b.append("\\t");
                default -> { if (c < 0x20) b.append(String.format("\\u%04x", (int) c)); else b.append(c); }
            }
        }
        return b.append('"').toString();
    }

    public static String error(String code, String message) {
        return "{\"error\":{\"code\":" + quote(code) + ",\"message\":" + quote(message) + "}}";
    }

    /** The error envelope as a map (used by ErrorHandler). */
    public static Map<String, Object> envelope(String code, String message, Map<String, String> details) {
        Map<String, Object> e = new java.util.LinkedHashMap<>();
        e.put("code", code);
        e.put("message", message);
        if (details != null && !details.isEmpty()) e.put("details", details);
        return Map.of("error", e);
    }
}

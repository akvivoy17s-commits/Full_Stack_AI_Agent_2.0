package app.integrations;

import java.nio.charset.StandardCharsets;

/** File type from the file's own bytes (never from the client's Content-Type or file name). */
public final class UploadKinds {
    private UploadKinds() {}

    public record Kind(String ext, String mime) {}

    private static boolean starts(byte[] b, int off, String ascii) {
        byte[] s = ascii.getBytes(StandardCharsets.ISO_8859_1);
        if (b.length < off + s.length) return false;
        for (int i = 0; i < s.length; i++) if (b[off + i] != s[i]) return false;
        return true;
    }

    /** null = not an accepted type (PNG, JPEG, GIF, WebP, PDF). */
    public static Kind detect(byte[] b) {
        if (b.length > 8 && (b[0] & 0xff) == 0x89 && starts(b, 1, "PNG\r\n\u001a\n")) return new Kind("png", "image/png");
        if (b.length > 3 && (b[0] & 0xff) == 0xff && (b[1] & 0xff) == 0xd8 && (b[2] & 0xff) == 0xff) return new Kind("jpg", "image/jpeg");
        if (b.length > 6 && (starts(b, 0, "GIF87a") || starts(b, 0, "GIF89a"))) return new Kind("gif", "image/gif");
        if (b.length > 12 && starts(b, 0, "RIFF") && starts(b, 8, "WEBP")) return new Kind("webp", "image/webp");
        if (b.length > 5 && starts(b, 0, "%PDF-")) return new Kind("pdf", "application/pdf");
        return null;
    }

    public static Kind byExt(String ext) {
        return switch (ext) {
            case "png" -> new Kind("png", "image/png");
            case "jpg" -> new Kind("jpg", "image/jpeg");
            case "gif" -> new Kind("gif", "image/gif");
            case "webp" -> new Kind("webp", "image/webp");
            case "pdf" -> new Kind("pdf", "application/pdf");
            default -> null;
        };
    }
}

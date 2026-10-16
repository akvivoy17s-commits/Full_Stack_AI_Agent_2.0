package app.core;

import java.nio.charset.StandardCharsets;
import java.security.GeneralSecurityException;
import java.security.MessageDigest;
import java.util.Base64;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;

/** HS256 JSON Web Tokens with the JDK only. verify() accepts HS256 and nothing else (no "none", no algorithm switching) and requires an exp claim. */
public final class Jwt {
    public record Claims(String sub, String role) {}

    private static final Pattern ALG = Pattern.compile("\"alg\"\\s*:\\s*\"HS256\"");
    private static final Pattern EXP = Pattern.compile("\"exp\"\\s*:\\s*([0-9]{1,15})");
    private static final Pattern SUB = Pattern.compile("\"sub\"\\s*:\\s*\"([^\"\\\\]{1,100})\"");
    private static final Pattern ROLE = Pattern.compile("\"role\"\\s*:\\s*\"([^\"\\\\]{1,100})\"");
    private static final Base64.Encoder B64 = Base64.getUrlEncoder().withoutPadding();
    private Jwt() {}

    private static byte[] mac(String secret, String data) throws GeneralSecurityException {
        Mac m = Mac.getInstance("HmacSHA256");
        m.init(new SecretKeySpec(secret.getBytes(StandardCharsets.UTF_8), "HmacSHA256"));
        return m.doFinal(data.getBytes(StandardCharsets.US_ASCII));
    }

    private static String esc(String v) { return v.replace("\\", "\\\\").replace("\"", "\\\""); }

    public static String sign(String secret, String sub, String role, long ttlSeconds, long nowSeconds) {
        try {
            String json = "{\"role\":\"" + esc(role) + "\",\"sub\":\"" + esc(sub) + "\",\"iat\":" + nowSeconds + ",\"exp\":" + (nowSeconds + ttlSeconds) + "}";
            String head = B64.encodeToString("{\"alg\":\"HS256\",\"typ\":\"JWT\"}".getBytes(StandardCharsets.UTF_8));
            String data = head + "." + B64.encodeToString(json.getBytes(StandardCharsets.UTF_8));
            return data + "." + B64.encodeToString(mac(secret, data));
        } catch (GeneralSecurityException e) {
            throw new IllegalStateException("could not sign token", e);
        }
    }

    /** The claims, or null for anything that is not a valid, unexpired token signed with this secret. The signature is checked before the body is read. */
    public static Claims verify(String secret, String token, long nowSeconds) {
        try {
            String[] p = token.split("\\.", -1);
            if (p.length != 3 || token.length() > 4096) return null;
            if (!ALG.matcher(new String(Base64.getUrlDecoder().decode(p[0]), StandardCharsets.UTF_8)).find()) return null;
            if (!MessageDigest.isEqual(mac(secret, p[0] + "." + p[1]), Base64.getUrlDecoder().decode(p[2]))) return null;
            String body = new String(Base64.getUrlDecoder().decode(p[1]), StandardCharsets.UTF_8);
            Matcher exp = EXP.matcher(body), sub = SUB.matcher(body), role = ROLE.matcher(body);
            if (!exp.find() || !sub.find() || !role.find() || Long.parseLong(exp.group(1)) <= nowSeconds) return null;
            return new Claims(sub.group(1), role.group(1));
        } catch (RuntimeException | GeneralSecurityException e) {
            return null;
        }
    }
}

package app.payments;

import java.nio.charset.StandardCharsets;
import java.security.GeneralSecurityException;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.regex.Pattern;
import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;

/** Webhook signature checks (pure Java). Always computed over the exact raw bytes, compared in constant time. */
public final class PayCrypto {
    public static final long STRIPE_TOLERANCE_SEC = 300;
    private static final Pattern HEX64 = Pattern.compile("[0-9a-fA-F]{64}");

    private PayCrypto() {}

    public static String hmacHex(byte[] secret, byte[] data) {
        try {
            Mac mac = Mac.getInstance("HmacSHA256");
            mac.init(new SecretKeySpec(secret, "HmacSHA256"));
            return HexFormat.of().formatHex(mac.doFinal(data));
        } catch (GeneralSecurityException e) {
            throw new IllegalStateException(e);
        }
    }

    private static boolean same(String a, String b) {
        return MessageDigest.isEqual(a.getBytes(StandardCharsets.UTF_8), b.getBytes(StandardCharsets.UTF_8));
    }

    /** Stripe-Signature: t=<unix>,v1=<hex>[,v1=<hex>...] over "<t>." + raw body; replay window 5 minutes. */
    public static boolean stripe(byte[] raw, String header, String secret, long nowSec) {
        if (secret == null || secret.isEmpty() || header == null) return false;
        long ts = Long.MIN_VALUE;
        java.util.List<String> sigs = new java.util.ArrayList<>();
        for (String part : header.split(",")) {
            int i = part.indexOf('=');
            if (i < 0) continue;
            String k = part.substring(0, i).trim(), v = part.substring(i + 1).trim();
            if (k.equals("t")) {
                try { ts = Long.parseLong(v); } catch (NumberFormatException e) { return false; }
            } else if (k.equals("v1")) sigs.add(v);
        }
        if (ts == Long.MIN_VALUE || sigs.isEmpty() || Math.abs(nowSec - ts) > STRIPE_TOLERANCE_SEC) return false;
        byte[] prefix = (ts + ".").getBytes(StandardCharsets.UTF_8), data = new byte[prefix.length + raw.length];
        System.arraycopy(prefix, 0, data, 0, prefix.length);
        System.arraycopy(raw, 0, data, prefix.length, raw.length);
        String want = hmacHex(secret.getBytes(StandardCharsets.UTF_8), data);
        boolean ok = false;
        for (String s : sigs) ok |= same(want, s.toLowerCase());
        return ok;
    }

    /** X-Razorpay-Signature: hex HMAC-SHA256 of the raw body. */
    public static boolean razorpay(byte[] raw, String header, String secret) {
        if (secret == null || secret.isEmpty() || header == null || !HEX64.matcher(header).matches()) return false;
        return same(hmacHex(secret.getBytes(StandardCharsets.UTF_8), raw), header.toLowerCase());
    }
}

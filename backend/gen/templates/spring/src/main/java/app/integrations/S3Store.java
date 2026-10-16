package app.integrations;

import app.core.ApiException;
import java.net.URI;
import java.net.URLEncoder;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.time.Duration;
import java.time.ZoneOffset;
import java.time.ZonedDateTime;
import java.time.format.DateTimeFormatter;
import java.util.HexFormat;
import java.util.TreeMap;
import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

/**
 * S3-compatible object storage (AWS S3, MinIO, Cloudflare R2, DigitalOcean Spaces) with Signature V4, no SDK.
 * The bucket stays PRIVATE: files are only served through the API, which applies the same sign-in rule as local uploads.
 */
@Component
public class S3Store implements ObjectStore {
    private static final DateTimeFormatter STAMP = DateTimeFormatter.ofPattern("yyyyMMdd'T'HHmmss'Z'").withZone(ZoneOffset.UTC);
    private final HttpClient http = HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(10)).build();
    private final String endpoint, bucket, region, keyId, secret;

    public S3Store(@Value("${S3_ENDPOINT:}") String endpoint, @Value("${S3_BUCKET:}") String bucket, @Value("${S3_REGION:us-east-1}") String region,
                   @Value("${S3_ACCESS_KEY_ID:}") String keyId, @Value("${S3_SECRET_ACCESS_KEY:}") String secret) {
        this.endpoint = endpoint;
        this.bucket = bucket;
        this.region = region.isBlank() ? "us-east-1" : region;
        this.keyId = keyId;
        this.secret = secret;
    }

    private boolean configured() {
        for (String v : new String[] {endpoint, bucket, keyId, secret}) if (v == null || v.isBlank() || v.startsWith("your-")) return false;
        return true;
    }

    static byte[] hmac(byte[] key, String data) {
        try {
            Mac mac = Mac.getInstance("HmacSHA256");
            mac.init(new SecretKeySpec(key, "HmacSHA256"));
            return mac.doFinal(data.getBytes(StandardCharsets.UTF_8));
        } catch (Exception e) { throw new IllegalStateException(e); }
    }

    static String sha(byte[] d) {
        try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(d)); } catch (Exception e) { throw new IllegalStateException(e); }
    }

    static String enc(String s) {
        return URLEncoder.encode(s, StandardCharsets.UTF_8).replace("+", "%20").replace("*", "%2A").replace("%7E", "~");
    }

    /** The Authorization header value for a request with no query string and only the three required signed headers. */
    static String authorization(String method, String host, String path, String payloadHash, String amzDate, String region, String keyId, String secret) {
        TreeMap<String, String> h = new TreeMap<>();
        h.put("host", host);
        h.put("x-amz-content-sha256", payloadHash);
        h.put("x-amz-date", amzDate);
        StringBuilder canonHeaders = new StringBuilder();
        h.forEach((k, v) -> canonHeaders.append(k).append(':').append(v).append('\n'));
        String signed = String.join(";", h.keySet());
        String[] parts = path.split("/", -1);
        StringBuilder p = new StringBuilder();
        for (int i = 0; i < parts.length; i++) p.append(i == 0 ? "" : "/").append(enc(parts[i]));
        String canonical = String.join("\n", method, p.toString(), "", canonHeaders.toString(), signed, payloadHash);
        String day = amzDate.substring(0, 8);
        String scope = day + "/" + region + "/s3/aws4_request";
        String toSign = String.join("\n", "AWS4-HMAC-SHA256", amzDate, scope, sha(canonical.getBytes(StandardCharsets.UTF_8)));
        byte[] k = hmac(hmac(hmac(hmac(("AWS4" + secret).getBytes(StandardCharsets.UTF_8), day), region), "s3"), "aws4_request");
        String sig = HexFormat.of().formatHex(hmac(k, toSign));
        return "AWS4-HMAC-SHA256 Credential=" + keyId + "/" + scope + ", SignedHeaders=" + signed + ", Signature=" + sig;
    }

    /** AWS endpoints use the virtual-hosted style (bucket.host); every other S3-compatible service uses path style (host/bucket). */
    static String[] target(String endpoint, String bucket, String key) {
        URI u = URI.create(endpoint);
        String hostPort = u.getPort() > 0 ? u.getHost() + ":" + u.getPort() : u.getHost();
        boolean aws = u.getHost() != null && (u.getHost().equals("amazonaws.com") || u.getHost().endsWith(".amazonaws.com"));
        return aws ? new String[] {u.getScheme() + "://" + bucket + "." + hostPort + "/" + key, bucket + "." + hostPort, "/" + key}
                   : new String[] {u.getScheme() + "://" + hostPort + "/" + bucket + "/" + key, hostPort, "/" + bucket + "/" + key};
    }

    private HttpResponse<byte[]> send(String method, String key, byte[] body, String contentType) {
        if (!configured()) throw new ApiException(503, "storage_unavailable", "File storage is not configured");
        try {
            String[] t = target(endpoint, bucket, key);
            byte[] payload = body == null ? new byte[0] : body;
            String ph = sha(payload);
            String date = STAMP.format(ZonedDateTime.now(ZoneOffset.UTC));
            HttpRequest.Builder b = HttpRequest.newBuilder(URI.create(t[0])).timeout(Duration.ofSeconds(15))
                    .header("x-amz-content-sha256", ph).header("x-amz-date", date)
                    .header("Authorization", authorization(method, t[1], t[2], ph, date, region, keyId, secret));
            if (contentType != null) b.header("Content-Type", contentType);
            b.method(method, body == null ? HttpRequest.BodyPublishers.noBody() : HttpRequest.BodyPublishers.ofByteArray(body));
            return http.send(b.build(), HttpResponse.BodyHandlers.ofByteArray());
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            throw new ApiException(502, "storage_unreachable", "The file storage could not be reached");
        } catch (java.io.IOException | IllegalArgumentException e) {
            throw new ApiException(502, "storage_unreachable", "The file storage could not be reached");
        }
    }

    @Override
    public void put(String key, byte[] body, String contentType) {
        int s = send("PUT", key, body, contentType).statusCode();
        if (s < 200 || s > 299) throw new ApiException(502, "storage_error", "The file storage rejected the request");
    }

    @Override
    public byte[] get(String key) {
        HttpResponse<byte[]> r = send("GET", key, null, null);
        if (r.statusCode() == 404) return null;
        if (r.statusCode() < 200 || r.statusCode() > 299) throw new ApiException(502, "storage_error", "The file storage rejected the request");
        return r.body();
    }
}

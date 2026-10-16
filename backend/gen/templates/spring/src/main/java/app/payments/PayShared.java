package app.payments;

import app.checkout.Money;
import app.checkout.Notify;
import app.core.ApiException;
import app.core.Schema;
import app.data.SqlRepo;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Component;
import org.springframework.transaction.support.TransactionTemplate;

/** Order access and HTTP calls shared by every provider. The amount always comes from the caller's own stored order, never from the client. */
@Component
public class PayShared {
    public record Order(long id, String status, double total, Object userId) {}

    private static final HttpClient HTTP = HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(10)).build();
    private final JdbcTemplate jdbc;
    private final TransactionTemplate tx;
    private final SqlRepo repo;
    private final Schema schema;
    private final Notify notify;
    final ObjectMapper json;

    public PayShared(JdbcTemplate jdbc, TransactionTemplate tx, SqlRepo repo, Schema schema, Notify notify, ObjectMapper json) {
        this.jdbc = jdbc;
        this.tx = tx;
        this.repo = repo;
        this.schema = schema;
        this.notify = notify;
        this.json = json;
    }

    /** "<set>" is what .env.example holds for secrets, "your-..." for the other values. */
    public static boolean placeholder(String v) { return v == null || v.isBlank() || v.startsWith("your-") || v.startsWith("<"); }
    public static ApiException unavailable() { return new ApiException(503, "payments_unavailable", "Payments are not configured"); }
    public static ApiException rejected() { return new ApiException(502, "payment_provider_error", "The payment provider rejected the request"); }
    public static ApiException invalidSignature() { return new ApiException(400, "invalid_signature", "Invalid webhook signature"); }

    public Object parseId(Object raw) { return raw instanceof Number || raw instanceof String ? repo.parseId(raw) : null; }

    @SuppressWarnings("unchecked")
    public Map<String, Object> parse(byte[] raw) {
        try {
            Object v = json.readValue(raw, Object.class);
            return v instanceof Map ? (Map<String, Object>) v : null;
        } catch (IOException e) {
            throw new ApiException(400, "invalid_json", "Request body is not valid JSON");
        }
    }

    private String qt() {
        String t = schema.entities().get("Order").table();
        return switch (schema.db()) { case "mysql" -> "`" + t + "`"; case "mssql" -> "[" + t + "]"; default -> "\"" + t + "\""; };
    }

    private String qc(String c) {
        return switch (schema.db()) { case "mysql" -> "`" + c + "`"; case "mssql" -> "[" + c + "]"; default -> "\"" + c + "\""; };
    }

    public Order get(Object id) {
        List<Map<String, Object>> r = jdbc.queryForList("SELECT " + qc("id") + ", " + qc("status") + ", " + qc("total") + ", " + qc("user_id") + " FROM " + qt() + " WHERE " + qc("id") + " = ?", id);
        if (r.isEmpty()) return null;
        Map<String, Object> o = r.get(0);
        return new Order(((Number) o.get("id")).longValue(), String.valueOf(o.get("status")), ((Number) o.get("total")).doubleValue(), o.get("user_id"));
    }

    /** {orderId, minorUnits}: the caller's own order, still pending, chargeable. */
    public long[] payable(String userId, Object orderId) {
        Object uid = repo.parseId(userId), oid = parseId(orderId);
        if (uid == null || oid == null) throw new ApiException(400, "validation_failed", "orderId is required", Map.of("orderId", "required"));
        Order o = get(oid);
        if (o == null || !(o.userId() instanceof Number n) || n.longValue() != ((Number) uid).longValue()) throw new ApiException(404, "not_found", "Order not found");
        if (!"pending".equals(o.status())) throw new ApiException(409, "order_not_payable", "This order is not awaiting payment");
        long minor = Money.toCents(o.total());
        if (minor < 50) throw new ApiException(409, "invalid_amount", "This order total cannot be charged");
        return new long[] {o.id(), minor};
    }

    /** Idempotent: only a pending order whose total (minor units) equals the amount actually paid becomes paid. */
    public boolean markPaid(Object orderId, Object paidMinor) {
        if (orderId == null || !(paidMinor instanceof Integer || paidMinor instanceof Long)) return false;
        long paid = ((Number) paidMinor).longValue();
        Boolean done = tx.execute(s -> {
            Order o = get(orderId);
            if (o == null || !"pending".equals(o.status()) || Money.toCents(o.total()) != paid) return false;
            return jdbc.update("UPDATE " + qt() + " SET " + qc("status") + " = 'paid' WHERE " + qc("id") + " = ? AND " + qc("status") + " = 'pending'", orderId) == 1;
        });
        if (Boolean.TRUE.equals(done)) notify.changed("Order", "update");
        return Boolean.TRUE.equals(done);
    }

    public record Resp(boolean ok, Map<String, Object> body) {}

    /** One bounded HTTPS POST (10 s). An unreachable provider is a 502. */
    @SuppressWarnings("unchecked")
    public Resp post(String url, Map<String, String> headers, byte[] body) {
        HttpRequest.Builder b = HttpRequest.newBuilder(URI.create(url)).timeout(Duration.ofSeconds(10)).POST(HttpRequest.BodyPublishers.ofByteArray(body));
        headers.forEach(b::header);
        try {
            HttpResponse<byte[]> r = HTTP.send(b.build(), HttpResponse.BodyHandlers.ofByteArray());
            Map<String, Object> out = new LinkedHashMap<>();
            try {
                Object v = r.body().length == 0 ? null : json.readValue(r.body(), Object.class);
                if (v instanceof Map) out = (Map<String, Object>) v;
            } catch (IOException ignored) { /* non-JSON error body */ }
            return new Resp(r.statusCode() / 100 == 2, out);
        } catch (IOException e) {
            throw new ApiException(502, "payment_provider_unreachable", "The payment provider could not be reached");
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            throw new ApiException(502, "payment_provider_unreachable", "The payment provider could not be reached");
        }
    }
}

package app.payments;

import static app.payments.PayShared.invalidSignature;
import static app.payments.PayShared.placeholder;
import static app.payments.PayShared.rejected;
import static app.payments.PayShared.unavailable;

import app.checkout.Money;
import java.nio.charset.StandardCharsets;
import java.util.Base64;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

/** PayPal Orders v2 over plain HTTPS. PayPal verifies its own webhook signature; approved orders are captured on the server. */
@Component
public class PaypalPay implements PayProvider {
    private final PayShared pay;
    private final String id, secret, hookId, env, currency;
    private String token = "";
    private long tokenExp;

    public PaypalPay(PayShared pay, @Value("${PAYPAL_CLIENT_ID:}") String id, @Value("${PAYPAL_CLIENT_SECRET:}") String secret,
                     @Value("${PAYPAL_WEBHOOK_ID:}") String hookId, @Value("${PAYPAL_ENV:sandbox}") String env, @Value("${PAYPAL_CURRENCY:usd}") String currency) {
        this.pay = pay;
        this.id = id;
        this.secret = secret;
        this.hookId = hookId;
        this.env = env;
        this.currency = currency.toLowerCase();
    }

    private String base() { return "live".equals(env) ? "https://api-m.paypal.com" : "https://api-m.sandbox.paypal.com"; }
    private boolean configured() { return !placeholder(id) && !placeholder(secret); }

    private synchronized String accessToken() {
        if (!token.isEmpty() && tokenExp > System.currentTimeMillis() + 30_000) return token;
        String auth = Base64.getEncoder().encodeToString((id + ":" + secret).getBytes(StandardCharsets.UTF_8));
        PayShared.Resp r = pay.post(base() + "/v1/oauth2/token", Map.of("Authorization", "Basic " + auth, "Content-Type", "application/x-www-form-urlencoded"),
                "grant_type=client_credentials".getBytes(StandardCharsets.UTF_8));
        if (!r.ok() || !(r.body().get("access_token") instanceof String t)) throw rejected();
        token = t;
        tokenExp = System.currentTimeMillis() + (long) (r.body().get("expires_in") instanceof Number n ? n.doubleValue() * 1000 : 300_000);
        return token;
    }

    private PayShared.Resp api(String path, Map<String, Object> body, String requestId) {
        Map<String, String> h = new LinkedHashMap<>();
        h.put("Authorization", "Bearer " + accessToken());
        h.put("Content-Type", "application/json");
        if (requestId != null) h.put("PayPal-Request-Id", requestId);
        try { return pay.post(base() + path, h, pay.json.writeValueAsBytes(body)); } catch (com.fasterxml.jackson.core.JsonProcessingException e) { throw rejected(); }
    }

    static Long minor(Object v) {
        try { return Money.toCents(Double.parseDouble(String.valueOf(v))); } catch (RuntimeException e) { return null; }
    }

    @Override public Map<String, Object> intent(String userId, Object orderId) {
        if (!configured()) throw unavailable();
        long[] o = pay.payable(userId, orderId);
        Map<String, Object> amount = Map.of("currency_code", currency.toUpperCase(), "value", String.format(java.util.Locale.ROOT, "%d.%02d", o[1] / 100, o[1] % 100));
        PayShared.Resp r = api("/v2/checkout/orders", Map.of("intent", "CAPTURE", "purchase_units", List.of(Map.of("custom_id", String.valueOf(o[0]), "amount", amount))), "order-" + o[0] + "-" + o[1]);
        if (!r.ok() || !(r.body().get("id") instanceof String pid)) throw rejected();
        String href = null;
        if (r.body().get("links") instanceof List<?> links) {
            for (Object l : links) {
                if (l instanceof Map<?, ?> m && ("payer-action".equals(m.get("rel")) || "approve".equals(m.get("rel")))) { href = String.valueOf(m.get("href")); break; }
            }
        }
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("paypalOrderId", pid);
        out.put("approveUrl", href);
        out.put("orderId", o[0]);
        out.put("amount", o[1] / 100.0);
        out.put("currency", currency);
        return out;
    }

    private boolean verified(Map<String, String> h, Map<String, Object> event) {
        if (h.get("paypal-transmission-id") == null || h.get("paypal-transmission-sig") == null || h.get("paypal-cert-url") == null) return false;
        Map<String, Object> b = new LinkedHashMap<>();
        b.put("auth_algo", h.get("paypal-auth-algo"));
        b.put("cert_url", h.get("paypal-cert-url"));
        b.put("transmission_id", h.get("paypal-transmission-id"));
        b.put("transmission_sig", h.get("paypal-transmission-sig"));
        b.put("transmission_time", h.get("paypal-transmission-time"));
        b.put("webhook_id", hookId);
        b.put("webhook_event", event);
        PayShared.Resp r = api("/v1/notifications/verify-webhook-signature", b, null);
        return r.ok() && "SUCCESS".equals(r.body().get("verification_status"));
    }

    @Override public void webhook(byte[] raw, Map<String, String> headers) {
        if (!configured() || placeholder(hookId)) throw unavailable();
        Map<String, Object> event = pay.parse(raw);
        if (event == null || !verified(headers, event)) throw invalidSignature();
        Map<?, ?> r = event.get("resource") instanceof Map<?, ?> m ? m : Map.of();
        String cur = currency.toUpperCase(), kind = String.valueOf(event.get("event_type"));
        if ("PAYMENT.CAPTURE.COMPLETED".equals(kind) && r.get("amount") instanceof Map<?, ?> a && cur.equals(a.get("currency_code")) && "COMPLETED".equals(r.get("status"))) {
            pay.markPaid(pay.parseId(r.get("custom_id")), minor(a.get("value")));
        } else if ("CHECKOUT.ORDER.APPROVED".equals(kind) && r.get("id") != null) {
            // capture only an order we created: same stored order, same amount, still pending
            Map<?, ?> unit = r.get("purchase_units") instanceof List<?> u && !u.isEmpty() && u.get(0) instanceof Map<?, ?> um ? um : Map.of();
            Object oid = pay.parseId(unit.get("custom_id"));
            PayShared.Order order = oid == null ? null : pay.get(oid);
            Map<?, ?> ua = unit.get("amount") instanceof Map<?, ?> m ? m : Map.of();
            if (order != null && "pending".equals(order.status()) && cur.equals(ua.get("currency_code")) && java.util.Objects.equals(minor(ua.get("value")), Money.toCents(order.total()))) {
                api("/v2/checkout/orders/" + r.get("id") + "/capture", Map.of(), "capture-" + r.get("id"));      // PayPal-Request-Id keeps the capture idempotent
            }
        }
    }
}

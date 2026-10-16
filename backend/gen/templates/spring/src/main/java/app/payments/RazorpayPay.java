package app.payments;

import static app.payments.PayShared.invalidSignature;
import static app.payments.PayShared.placeholder;
import static app.payments.PayShared.rejected;
import static app.payments.PayShared.unavailable;

import java.nio.charset.StandardCharsets;
import java.util.Base64;
import java.util.LinkedHashMap;
import java.util.Map;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

/** Razorpay Orders API over plain HTTPS (amounts in paise). */
@Component
public class RazorpayPay implements PayProvider {
    private final PayShared pay;
    private final String keyId, secret, hook, currency;

    public RazorpayPay(PayShared pay, @Value("${RAZORPAY_KEY_ID:}") String keyId, @Value("${RAZORPAY_KEY_SECRET:}") String secret,
                       @Value("${RAZORPAY_WEBHOOK_SECRET:}") String hook, @Value("${RAZORPAY_CURRENCY:inr}") String currency) {
        this.pay = pay;
        this.keyId = keyId;
        this.secret = secret;
        this.hook = hook;
        this.currency = currency.toLowerCase();
    }

    @Override public Map<String, Object> intent(String userId, Object orderId) {
        if (placeholder(keyId) || placeholder(secret)) throw unavailable();
        long[] o = pay.payable(userId, orderId);
        String auth = Base64.getEncoder().encodeToString((keyId + ":" + secret).getBytes(StandardCharsets.UTF_8));
        Map<String, Object> req = new LinkedHashMap<>();
        req.put("amount", o[1]);
        req.put("currency", currency.toUpperCase());
        req.put("receipt", "order-" + o[0]);
        req.put("notes", Map.of("order_id", String.valueOf(o[0])));
        byte[] body;
        try { body = pay.json.writeValueAsBytes(req); } catch (com.fasterxml.jackson.core.JsonProcessingException e) { throw rejected(); }
        PayShared.Resp r = pay.post("https://api.razorpay.com/v1/orders", Map.of("Authorization", "Basic " + auth, "Content-Type", "application/json"), body);
        if (!r.ok() || !(r.body().get("id") instanceof String id)) throw rejected();
        Map<String, Object> out = new LinkedHashMap<>();       // key id is public by design (the checkout widget needs it); the secret never leaves the server
        out.put("razorpayOrderId", id);
        out.put("keyId", keyId);
        out.put("orderId", o[0]);
        out.put("amount", o[1] / 100.0);
        out.put("currency", currency);
        return out;
    }

    @Override public void webhook(byte[] raw, Map<String, String> headers) {
        if (placeholder(hook)) throw unavailable();
        if (!PayCrypto.razorpay(raw, headers.get("x-razorpay-signature"), hook)) throw invalidSignature();
        Map<String, Object> event = pay.parse(raw);
        if (event == null || !"payment.captured".equals(event.get("event"))) return;
        Object p = event.get("payload") instanceof Map<?, ?> pl && pl.get("payment") instanceof Map<?, ?> pm ? pm.get("entity") : null;
        if (!(p instanceof Map<?, ?> e) || !(e.get("notes") instanceof Map<?, ?> notes)) return;
        if (!currency.equalsIgnoreCase(String.valueOf(e.get("currency")))) return;
        pay.markPaid(pay.parseId(notes.get("order_id")), e.get("amount"));
    }
}

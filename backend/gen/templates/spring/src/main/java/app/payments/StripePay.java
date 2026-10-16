package app.payments;

import static app.payments.PayShared.invalidSignature;
import static app.payments.PayShared.placeholder;
import static app.payments.PayShared.rejected;
import static app.payments.PayShared.unavailable;

import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.util.LinkedHashMap;
import java.util.Map;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

/** Stripe over plain HTTPS (no SDK). */
@Component
public class StripePay implements PayProvider {
    private final PayShared pay;
    private final String key, hook, currency;

    public StripePay(PayShared pay, @Value("${STRIPE_SECRET_KEY:}") String key, @Value("${STRIPE_WEBHOOK_SECRET:}") String hook,
                     @Value("${STRIPE_CURRENCY:usd}") String currency) {
        this.pay = pay;
        this.key = key;
        this.hook = hook;
        this.currency = currency.toLowerCase();
    }

    private static String enc(String s) { return URLEncoder.encode(s, StandardCharsets.UTF_8); }

    @Override public Map<String, Object> intent(String userId, Object orderId) {
        if (placeholder(key)) throw unavailable();
        long[] o = pay.payable(userId, orderId);
        String body = "amount=" + o[1] + "&currency=" + enc(currency) + "&" + enc("metadata[order_id]") + "=" + o[0] + "&" + enc("automatic_payment_methods[enabled]") + "=true";
        PayShared.Resp r = pay.post("https://api.stripe.com/v1/payment_intents", Map.of("Authorization", "Bearer " + key,
                "Content-Type", "application/x-www-form-urlencoded", "Idempotency-Key", "order-" + o[0] + "-" + o[1]), body.getBytes(StandardCharsets.UTF_8));
        if (!r.ok() || !(r.body().get("client_secret") instanceof String secret)) throw rejected();
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("clientSecret", secret);
        out.put("orderId", o[0]);
        out.put("amount", o[1] / 100.0);
        out.put("currency", currency);
        return out;
    }

    @Override @SuppressWarnings("unchecked")
    public void webhook(byte[] raw, Map<String, String> headers) {
        if (placeholder(hook)) throw unavailable();
        if (!PayCrypto.stripe(raw, headers.get("stripe-signature"), hook, System.currentTimeMillis() / 1000)) throw invalidSignature();
        Map<String, Object> event = pay.parse(raw);
        if (event == null || !"payment_intent.succeeded".equals(event.get("type"))) return;
        Object data = event.get("data");
        Object obj = data instanceof Map<?, ?> d ? d.get("object") : null;
        if (!(obj instanceof Map<?, ?> o)) return;
        Object meta = o.get("metadata");
        pay.markPaid(pay.parseId(meta instanceof Map<?, ?> m ? m.get("order_id") : null), o.get("amount_received"));
    }
}

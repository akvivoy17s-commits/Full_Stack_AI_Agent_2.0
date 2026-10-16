package app.payments;

import app.core.ApiException;
import app.core.AuthContext;
import app.core.Principal;
import java.util.Locale;
import java.util.Map;
import java.util.TreeMap;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class PaymentsController {
    private final PayProvider provider;
    private final AuthContext auth;

    public PaymentsController(PayProvider provider, AuthContext auth) {
        this.provider = provider;
        this.auth = auth;
    }

    /** Start a payment for one of your pending orders (amount read from the order) */
    @PostMapping("/api/payments/intent")
    public ResponseEntity<Map<String, Object>> intent(@RequestBody(required = false) Object body) {
        Principal who = auth.current();
        if (who == null) throw new ApiException(401, "unauthorized", "Authentication required");
        return ResponseEntity.status(201).body(provider.intent(who.id(), body instanceof Map<?, ?> m ? m.get("orderId") : null));
    }

    /** Payment provider webhook (signature verified over the exact raw body) */
    @PostMapping("/api/payments/webhook")
    public Map<String, Object> webhook(@RequestBody(required = false) byte[] raw, @RequestHeader Map<String, String> headers) {
        Map<String, String> lower = new TreeMap<>();
        headers.forEach((k, v) -> lower.put(k.toLowerCase(Locale.ROOT), v));
        provider.webhook(raw == null ? new byte[0] : raw, lower);
        return Map.of("received", true);
    }
}

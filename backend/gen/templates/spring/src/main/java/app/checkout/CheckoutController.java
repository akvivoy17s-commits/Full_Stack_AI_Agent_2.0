package app.checkout;

import app.core.AuthContext;
import java.util.Map;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class CheckoutController {
    private final CheckoutService svc;
    private final AuthContext auth;

    public CheckoutController(CheckoutService svc, AuthContext auth) {
        this.svc = svc;
        this.auth = auth;
    }

    /** Create an order from cart items (server-side prices and stock) */
    @PostMapping("/api/checkout")
    public ResponseEntity<Map<String, Object>> checkout(@RequestBody(required = false) Object body) {
        return ResponseEntity.status(201).body(Map.of("order", svc.create(auth.current(), body)));
    }
}

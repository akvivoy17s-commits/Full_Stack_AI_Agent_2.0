package app;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import app.checkout.Money;
import app.core.ApiException;
import app.payments.PayCrypto;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;

class CheckoutMathTest {
    private static Object id(Object v) {
        String s = String.valueOf(v);
        return s.matches("[0-9]{1,9}") && Long.parseLong(s) > 0 ? (Object) Long.parseLong(s) : null;
    }

    private static Map<String, Object> item(Object pid, Object qty) {
        return Map.of("productId", pid, "quantity", qty);
    }

    @Test
    void centsAreExact() {
        assertEquals(1999, Money.toCents(19.99));
        assertEquals(30, Money.toCents(0.1 + 0.2));
        assertEquals(268, Money.toCents(2.675));
    }

    @Test
    void cartItemsAreValidatedAndMerged() {
        Map<Long, Integer> q = Money.parseItems(Map.of("items", List.of(item(1, 2), Map.of("product_id", "1", "quantity", 3), item(2, 1))), CheckoutMathTest::id);
        assertEquals(Map.of(1L, 5, 2L, 1), q);
        List<Object> bad = new ArrayList<>(List.of(item(1, 0), item(1, 1.5), item(1, true), item(0, 1), item(1, 100), "x"));
        for (Object line : bad) {
            ApiException e = assertThrows(ApiException.class, () -> Money.parseItems(Map.of("items", List.of(line)), CheckoutMathTest::id), String.valueOf(line));
            assertEquals(400, e.status());
        }
        assertThrows(ApiException.class, () -> Money.parseItems(Map.of("items", List.of()), CheckoutMathTest::id));
        assertThrows(ApiException.class, () -> Money.parseItems(null, CheckoutMathTest::id));
        assertThrows(ApiException.class, () -> Money.parseItems(Map.of("items", List.of(item(1, 99), item(1, 1))), CheckoutMathTest::id));
        assertThrows(ApiException.class, () -> Money.parseItems(Map.of("items", java.util.Collections.nCopies(51, item(1, 1))), CheckoutMathTest::id));
    }

    @Test
    void webhookSignaturesAreChecked() {
        byte[] raw = "{\"a\":1}".getBytes(StandardCharsets.UTF_8);
        long now = 1_700_000_000L;
        String stripe = "t=" + now + ",v1=" + PayCrypto.hmacHex("whsec_x".getBytes(StandardCharsets.UTF_8), (now + ".{\"a\":1}").getBytes(StandardCharsets.UTF_8));
        assertTrue(PayCrypto.stripe(raw, stripe, "whsec_x", now));
        assertFalse(PayCrypto.stripe(raw, stripe, "whsec_x", now + 301));          // stale
        assertFalse(PayCrypto.stripe("{\"a\":2}".getBytes(StandardCharsets.UTF_8), stripe, "whsec_x", now));   // tampered
        assertFalse(PayCrypto.stripe(raw, stripe, "other", now));
        assertFalse(PayCrypto.stripe(raw, "", "whsec_x", now));
        String rz = PayCrypto.hmacHex("rzp".getBytes(StandardCharsets.UTF_8), raw);
        assertTrue(PayCrypto.razorpay(raw, rz, "rzp"));
        assertFalse(PayCrypto.razorpay(raw, rz, "nope"));
        assertFalse(PayCrypto.razorpay(raw, "00", "rzp"));
        assertFalse(PayCrypto.razorpay(raw, rz, ""));
    }
}

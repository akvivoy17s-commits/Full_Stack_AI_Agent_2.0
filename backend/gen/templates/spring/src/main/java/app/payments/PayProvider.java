package app.payments;

import java.util.Map;

/** One payment provider (Stripe, Razorpay or PayPal; only the one the app uses is generated). */
public interface PayProvider {
    /** Starts a payment for the caller's own pending order; the amount is read from the stored order. */
    Map<String, Object> intent(String userId, Object orderId);

    /** headers: lower-case names. The signature is checked over the exact raw bytes before anything is parsed. */
    void webhook(byte[] raw, Map<String, String> headers);
}

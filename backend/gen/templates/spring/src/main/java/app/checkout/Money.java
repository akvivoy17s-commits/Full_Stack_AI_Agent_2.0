package app.checkout;

import app.core.ApiException;
import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.function.Function;

/** Pure helpers (no Spring): minor units and cart validation. The client never supplies a price or a total. */
public final class Money {
    public static final long MAX_CENTS = 1_000_000_000_000L;

    private Money() {}

    public static long toCents(double price) {
        return new BigDecimal(Double.toString(price)).movePointRight(2).setScale(0, RoundingMode.HALF_UP).longValueExact();
    }

    private static ApiException bad(String message, String key, String code) {
        return new ApiException(400, "validation_failed", message, key == null ? null : Map.of(key, code));
    }

    /** body = {items:[{productId, quantity}]} -> productId -> quantity (merged). 1..50 lines, quantity 1..99 per product. */
    public static Map<Long, Integer> parseItems(Object body, Function<Object, Object> parseId) {
        Object items = body instanceof Map<?, ?> m ? m.get("items") : null;
        if (!(items instanceof List<?> list) || list.isEmpty() || list.size() > 50) {
            throw bad("items must be an array containing 1 to 50 items", "items", "invalid_item_count");
        }
        Map<Long, Integer> qty = new LinkedHashMap<>();
        for (Object line : list) {
            if (!(line instanceof Map<?, ?> l)) throw bad("Each item must contain productId and quantity", null, null);
            Object raw = l.containsKey("productId") ? l.get("productId") : l.get("product_id");
            Object n = l.get("quantity");
            Object pid = raw instanceof Number || raw instanceof String ? parseId.apply(raw) : null;
            if (pid == null || !(n instanceof Integer || n instanceof Long) || ((Number) n).longValue() < 1 || ((Number) n).longValue() > 99) {
                throw bad("Invalid productId or quantity", "item", "invalid_product_or_quantity");
            }
            int sum = qty.merge(((Number) pid).longValue(), ((Number) n).intValue(), Integer::sum);
            if (sum > 99) throw bad("A product quantity cannot exceed 99", null, null);
        }
        return qty;
    }
}

package app.checkout;

import app.core.ApiException;
import app.core.Entity;
import app.core.Principal;
import app.core.Schema;
import app.data.SqlRepo;
import java.time.Instant;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.support.TransactionTemplate;

/** One transaction: prices and stock come from the database, stock is decremented with a conditional UPDATE (no overselling under concurrency),
 *  and any exception rolls the whole order back. */
@Service
public class CheckoutService {
    private final JdbcTemplate jdbc;
    private final TransactionTemplate tx;
    private final SqlRepo repo;
    private final Schema schema;
    private final Notify notify;

    public CheckoutService(JdbcTemplate jdbc, TransactionTemplate tx, SqlRepo repo, Schema schema, Notify notify) {
        this.jdbc = jdbc;
        this.tx = tx;
        this.repo = repo;
        this.schema = schema;
        this.notify = notify;
    }

    private String qn(String n) {
        return switch (schema.db()) { case "mysql" -> "`" + n + "`"; case "mssql" -> "[" + n + "]"; default -> "\"" + n + "\""; };
    }

    private boolean has(Entity e, String field) {
        return e.fields().stream().anyMatch(f -> f.name().equals(field));
    }

    private static boolean truthy(Object v) {
        return v instanceof Boolean b ? b : v instanceof Number n && n.intValue() != 0;
    }

    public Map<String, Object> create(Principal who, Object body) {
        Object uid = who == null ? null : repo.parseId(who.id());
        if (uid == null) throw new ApiException(401, "unauthorized", "A valid signed-in user is required");
        Map<Long, Integer> qty = Money.parseItems(body, repo::parseId);
        Entity P = schema.entities().get("Product"), O = schema.entities().get("Order"), OI = schema.entities().get("OrderItem");
        Instant now = Instant.now();
        Map<String, Object> out = tx.execute(status -> {
            List<Long> ids = new ArrayList<>(qty.keySet());
            String marks = String.join(",", ids.stream().map(i -> "?").toList());
            String db = schema.db();
            String cols = qn("id") + ", " + qn("price") + ", " + qn("stock") + (has(P, "active") ? ", " + qn("active") : "");
            String sql = "SELECT " + cols + " FROM " + qn(P.table()) + ("mssql".equals(db) ? " WITH (UPDLOCK, ROWLOCK)" : "")
                    + " WHERE " + qn("id") + " IN (" + marks + ")" + ("postgresql".equals(db) || "mysql".equals(db) ? " FOR UPDATE" : "");
            Map<Long, Map<String, Object>> rows = new LinkedHashMap<>();
            for (Map<String, Object> r : jdbc.queryForList(sql, ids.toArray())) rows.put(((Number) r.get("id")).longValue(), r);
            if (rows.size() != ids.size()) throw new ApiException(400, "invalid_product", "One or more products do not exist");
            long total = 0;
            List<long[]> lines = new ArrayList<>();
            for (Map.Entry<Long, Integer> q : qty.entrySet()) {
                Map<String, Object> p = rows.get(q.getKey());
                if (has(P, "active") && !truthy(p.get("active"))) throw new ApiException(409, "product_unavailable", "One or more products are no longer available");
                if (!(p.get("stock") instanceof Number stock) || stock.longValue() < q.getValue()) {
                    throw new ApiException(409, "insufficient_stock", "There is not enough stock for one or more products");
                }
                if (!(p.get("price") instanceof Number price) || price.doubleValue() < 0 || price.doubleValue() >= Money.MAX_CENTS) {
                    throw new ApiException(409, "invalid_price", "A product has an invalid server-side price");
                }
                long cents = Money.toCents(price.doubleValue());
                total += cents * q.getValue();
                if (total > Money.MAX_CENTS) throw new ApiException(400, "total_too_large", "Order total is too large");
                lines.add(new long[] {q.getKey(), q.getValue(), cents});
            }
            Map<String, Object> od = new LinkedHashMap<>();
            if (has(O, "user_id")) od.put("user_id", uid);
            if (has(O, "status")) od.put("status", "pending");
            if (has(O, "total")) od.put("total", total / 100.0);
            if (has(O, "created_at")) od.put("created_at", now.toString());
            long orderId = ((Number) repo.create(O, od).get("id")).longValue();
            for (long[] l : lines) {                      // conditional update: no overselling even when requests race
                String up = "UPDATE " + qn(P.table()) + " SET " + qn("stock") + " = " + qn("stock") + " - ? WHERE " + qn("id") + " = ? AND " + qn("stock") + " >= ?";
                if (jdbc.update(up, l[1], l[0], l[1]) != 1) throw new ApiException(409, "insufficient_stock", "Stock changed during checkout; please retry");
            }
            for (long[] l : lines) {
                Map<String, Object> row = new LinkedHashMap<>();
                if (has(OI, "order_id")) row.put("order_id", orderId);
                if (has(OI, "product_id")) row.put("product_id", l[0]);
                if (has(OI, "user_id")) row.put("user_id", uid);
                if (has(OI, "quantity")) row.put("quantity", l[1]);
                if (has(OI, "unit_price")) row.put("unit_price", l[2] / 100.0);
                repo.create(OI, row);
            }
            Map<String, Object> res = new LinkedHashMap<>();
            res.put("orderId", orderId);
            res.put("total", total / 100.0);
            res.put("items", lines.size());
            res.put("status", "pending");
            res.put("created_at", now.toString());
            return res;
        });
        notify.changed("Order", "create", "Product", "update");
        return out;
    }
}

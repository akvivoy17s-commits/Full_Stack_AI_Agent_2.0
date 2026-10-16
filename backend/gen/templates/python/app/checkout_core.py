"""Transactional checkout for SQL databases. The server reads prices and stock; client-provided totals are never trusted."""
from datetime import datetime, timezone
from decimal import ROUND_HALF_UP, Decimal

import sqlalchemy as sa

from . import schema
from .db.sql import E, TABLES, _in, _mapped
from .errors import ApiError

MAX_CENTS = 10**12


def _has(entity: str, field: str) -> bool:
    return any(f["name"] == field for f in E[entity]["fields"])


def parse_items(db, items) -> dict[int, int]:
    if not isinstance(items, list) or not 1 <= len(items) <= 50:
        raise ApiError(400, "validation_failed", "items must be an array containing 1 to 50 items", {"items": "invalid_item_count"})
    qty: dict[int, int] = {}
    for line in items:
        if not isinstance(line, dict):
            raise ApiError(400, "validation_failed", "Each item must contain productId and quantity")
        pid = db.parse_id(line.get("productId", line.get("product_id")))
        n = line.get("quantity")
        if pid is None or isinstance(n, bool) or not isinstance(n, int) or not 1 <= n <= 99:
            raise ApiError(400, "validation_failed", "Invalid productId or quantity", {"item": "invalid_product_or_quantity"})
        qty[pid] = qty.get(pid, 0) + n
        if qty[pid] > 99:
            raise ApiError(400, "validation_failed", "A product quantity cannot exceed 99")
    return qty


def to_cents(price) -> int:
    return int((Decimal(repr(float(price))) * 100).quantize(Decimal(1), rounding=ROUND_HALF_UP))


def create_order(db, user_id, items) -> dict:
    if not getattr(db, "engine", None):
        raise ApiError(503, "checkout_unavailable", "Transactional checkout is not configured for this database")
    uid = db.parse_id(user_id)
    if uid is None:
        raise ApiError(401, "unauthorized", "A valid signed-in user is required")
    qty = parse_items(db, items)
    P, O, OI = TABLES["Product"], TABLES["Order"], TABLES["OrderItem"]
    now = datetime.now(timezone.utc)
    with _mapped(), db.engine.begin() as c:                       # any error below rolls the whole order back
        q = sa.select(P).where(P.c.id.in_(list(qty)))
        if schema.SCHEMA["db"] != "sqlite":
            q = q.with_for_update()
        rows = {r.id: r for r in c.execute(q)}
        if len(rows) != len(qty):
            raise ApiError(400, "invalid_product", "One or more products do not exist")
        lines, total = [], 0
        for pid, n in qty.items():
            p = rows[pid]
            if _has("Product", "active") and not p.active:
                raise ApiError(409, "product_unavailable", "One or more products are no longer available")
            if not isinstance(p.stock, int) or p.stock < n:
                raise ApiError(409, "insufficient_stock", "There is not enough stock for one or more products")
            if p.price is None or not 0 <= float(p.price) < MAX_CENTS:
                raise ApiError(409, "invalid_price", "A product has an invalid server-side price")
            cents = to_cents(p.price)
            total += cents * n
            if total > MAX_CENTS:
                raise ApiError(400, "total_too_large", "Order total is too large")
            lines.append((pid, n, cents))
        od = {}
        for k, v in (("user_id", uid), ("status", "pending"), ("total", total / 100), ("created_at", now)):
            if _has("Order", k):
                od[k] = v
        order_id = c.execute(sa.insert(O).values(**_in(E["Order"], od))).inserted_primary_key[0]
        for pid, n, _ in lines:                                    # conditional update: no overselling even when requests race
            if c.execute(sa.update(P).where(P.c.id == pid, P.c.stock >= n).values(stock=P.c.stock - n)).rowcount != 1:
                raise ApiError(409, "insufficient_stock", "Stock changed during checkout; please retry")
        for pid, n, cents in lines:
            row = {k: v for k, v in (("order_id", order_id), ("product_id", pid), ("user_id", uid), ("quantity", n), ("unit_price", cents / 100)) if _has("OrderItem", k)}
            c.execute(sa.insert(OI).values(**_in(E["OrderItem"], row)))
    if schema.SCHEMA["integrations"]["cache"]:
        from . import cache
        cache.invalidate()
    return {"orderId": order_id, "total": total / 100, "items": len(lines), "status": "pending", "created_at": now.isoformat().replace("+00:00", "Z")}

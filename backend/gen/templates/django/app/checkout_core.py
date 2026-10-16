"""Transactional checkout for SQL databases (Django ORM). The server reads prices and stock; client-provided totals are never trusted."""
from datetime import datetime, timezone
from decimal import ROUND_HALF_UP, Decimal

from django.db.models import F

from . import models, schema
from .db.django_orm import E, _in, _mapped, _model
from .errors import ApiError

MAX_CENTS = 10**12
K = models.KEYS


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
    uid = db.parse_id(user_id)
    if uid is None:
        raise ApiError(401, "unauthorized", "A valid signed-in user is required")
    qty = parse_items(db, items)
    P, O, OI = _model("Product"), _model("Order"), _model("OrderItem")
    kp = K["Product"]
    now = datetime.now(timezone.utc)
    with _mapped():                                                # any error below rolls the whole order back (transaction.atomic)
        rows = {r["id"]: r for r in P.objects.select_for_update().filter(pk__in=list(qty)).values()}      # row locks where the database has them
        if len(rows) != len(qty):
            raise ApiError(400, "invalid_product", "One or more products do not exist")
        lines, total = [], 0
        for pid, n in qty.items():
            p = rows[pid]
            if _has("Product", "active") and not p[kp["active"]]:
                raise ApiError(409, "product_unavailable", "One or more products are no longer available")
            stock, price = p[kp["stock"]], p[kp["price"]]
            if isinstance(stock, bool) or not isinstance(stock, int) or stock < n:
                raise ApiError(409, "insufficient_stock", "There is not enough stock for one or more products")
            if price is None or not 0 <= float(price) < MAX_CENTS:
                raise ApiError(409, "invalid_price", "A product has an invalid server-side price")
            cents = to_cents(price)
            total += cents * n
            if total > MAX_CENTS:
                raise ApiError(400, "total_too_large", "Order total is too large")
            lines.append((pid, n, cents))
        od = {k: v for k, v in (("user_id", uid), ("status", "pending"), ("total", total / 100), ("created_at", now)) if _has("Order", k)}
        order_id = O.objects.create(**_in(E["Order"], od)).pk
        for pid, n, _ in lines:                                    # conditional update: no overselling even when requests race
            if P.objects.filter(**{"pk": pid, kp["stock"] + "__gte": n}).update(**{kp["stock"]: F(kp["stock"]) - n}) != 1:
                raise ApiError(409, "insufficient_stock", "Stock changed during checkout; please retry")
        for pid, n, cents in lines:
            row = {k: v for k, v in (("order_id", order_id), ("product_id", pid), ("user_id", uid), ("quantity", n), ("unit_price", cents / 100)) if _has("OrderItem", k)}
            OI.objects.create(**_in(E["OrderItem"], row))
    if schema.SCHEMA["integrations"]["cache"]:
        from . import cache
        cache.invalidate()
    return {"orderId": order_id, "total": total / 100, "items": len(lines), "status": "pending", "created_at": now.isoformat().replace("+00:00", "Z")}

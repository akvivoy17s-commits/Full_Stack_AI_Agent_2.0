"""Helpers shared by every payment provider. The amount always comes from the caller's own stored order, never from the client."""
import json
import urllib.error
import urllib.request

import sqlalchemy as sa

from . import schema
from .checkout_core import to_cents
from .db.sql import TABLES
from .errors import ApiError


def placeholder(v) -> bool:
    return not v or str(v).startswith("your-")


def unavailable() -> ApiError:
    return ApiError(503, "payments_unavailable", "Payments are not configured")


def rejected() -> ApiError:
    return ApiError(502, "payment_provider_error", "The payment provider rejected the request")


def unreachable() -> ApiError:
    return ApiError(502, "payment_provider_unreachable", "The payment provider could not be reached")


def parse_json(raw: bytes):
    try:
        return json.loads(raw.decode("utf-8"))
    except ValueError:
        raise ApiError(400, "invalid_json", "Request body is not valid JSON") from None


def request_json(url: str, *, data: bytes | None = None, headers: dict | None = None, method: str = "POST") -> tuple[bool, dict]:
    """One bounded HTTPS call (10 s). Returns (ok, json body); an unreachable provider raises 502."""
    req = urllib.request.Request(url, data=data, method=method, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:                     # nosec: fixed https provider URLs
            return True, json.loads(r.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        try:
            return False, json.loads(e.read().decode() or "{}")
        except ValueError:
            return False, {}
    except (urllib.error.URLError, TimeoutError, ValueError):
        raise unreachable() from None


def get_order(db, order_id):
    O = TABLES["Order"]
    with db.engine.connect() as c:
        return c.execute(sa.select(O).where(O.c.id == order_id)).first()


def payable_order(db, user_id, order_id) -> tuple[int, int, float]:
    uid, oid = db.parse_id(user_id), db.parse_id(order_id)
    if uid is None or oid is None:
        raise ApiError(400, "validation_failed", "orderId is required", {"orderId": "required"})
    O = TABLES["Order"]
    with db.engine.connect() as c:
        order = c.execute(sa.select(O).where(O.c.id == oid, O.c.user_id == uid)).first()
    if not order:
        raise ApiError(404, "not_found", "Order not found")
    if order.status != "pending":
        raise ApiError(409, "order_not_payable", "This order is not awaiting payment")
    minor = to_cents(order.total)
    if minor < 50:
        raise ApiError(409, "invalid_amount", "This order total cannot be charged")
    return oid, minor, minor / 100


def mark_paid(db, order_id, paid_minor) -> bool:
    """Idempotent: only a pending order whose total (minor units) equals the amount actually paid becomes paid."""
    if order_id is None or isinstance(paid_minor, bool) or not isinstance(paid_minor, int):
        return False
    O = TABLES["Order"]
    done = False
    with db.engine.begin() as c:
        order = c.execute(sa.select(O).where(O.c.id == order_id)).first()
        if order and order.status == "pending" and to_cents(order.total) == paid_minor:
            done = c.execute(sa.update(O).where(O.c.id == order_id, O.c.status == "pending").values(status="paid")).rowcount == 1
    if done and schema.SCHEMA["integrations"]["cache"]:
        from . import cache
        cache.invalidate()
    return done

"""PayPal Orders v2, called with the standard library (no SDK). After the buyer approves, the verified CHECKOUT.ORDER.APPROVED webhook
captures the payment on the server and PAYMENT.CAPTURE.COMPLETED marks the order paid."""
import base64
import json
import threading
import time

from .config import cfg
from .errors import ApiError
from .pay_shared import get_order, mark_paid, parse_json, payable_order, placeholder, rejected, request_json, unavailable
from .checkout_core import to_cents

_token = {"value": "", "exp": 0.0}
_lock = threading.Lock()


def _base() -> str:
    return "https://api-m.paypal.com" if cfg.paypal_env == "live" else "https://api-m.sandbox.paypal.com"


def _configured() -> bool:
    return not placeholder(cfg.paypal_client_id) and not placeholder(cfg.paypal_client_secret)


def _access_token() -> str:
    with _lock:
        if _token["value"] and _token["exp"] > time.time() + 30:
            return _token["value"]
        auth = base64.b64encode(f"{cfg.paypal_client_id}:{cfg.paypal_client_secret}".encode()).decode()
        ok, data = request_json(f"{_base()}/v1/oauth2/token", data=b"grant_type=client_credentials", headers={"Authorization": f"Basic {auth}", "Content-Type": "application/x-www-form-urlencoded"})
        if not ok or not data.get("access_token"):
            raise rejected()
        _token.update(value=data["access_token"], exp=time.time() + float(data.get("expires_in") or 300))
        return _token["value"]


def _api(path: str, body: dict, request_id: str | None = None) -> tuple[bool, dict]:
    headers = {"Authorization": f"Bearer {_access_token()}", "Content-Type": "application/json"}
    if request_id:
        headers["PayPal-Request-Id"] = request_id
    return request_json(_base() + path, data=json.dumps(body).encode(), headers=headers)


def _verified(headers: dict, event) -> bool:
    """PayPal verifies its own signature (and certificate URL); we only forward the headers and the parsed event."""
    if not all(headers.get(k) for k in ("paypal-transmission-id", "paypal-transmission-sig", "paypal-cert-url")):
        return False
    ok, data = _api("/v1/notifications/verify-webhook-signature", {
        "auth_algo": headers.get("paypal-auth-algo"), "cert_url": headers["paypal-cert-url"], "transmission_id": headers["paypal-transmission-id"],
        "transmission_sig": headers["paypal-transmission-sig"], "transmission_time": headers.get("paypal-transmission-time"), "webhook_id": cfg.paypal_webhook_id, "webhook_event": event})
    return ok and data.get("verification_status") == "SUCCESS"


def _minor(v):
    try:
        return to_cents(float(v))
    except (TypeError, ValueError):
        return None


def create_intent(db, user_id, order_id) -> dict:
    if not _configured():
        raise unavailable()
    oid, minor, total = payable_order(db, user_id, order_id)
    ok, data = _api("/v2/checkout/orders", {"intent": "CAPTURE", "purchase_units": [{"custom_id": str(oid), "amount": {"currency_code": cfg.paypal_currency.upper(), "value": f"{minor / 100:.2f}"}}]}, f"order-{oid}-{minor}")
    if not ok or not data.get("id"):
        raise rejected()
    link = next((l for l in data.get("links", []) if l.get("rel") in ("payer-action", "approve")), None)
    return {"paypalOrderId": data["id"], "approveUrl": link.get("href") if link else None, "orderId": oid, "amount": total, "currency": cfg.paypal_currency}


def handle_webhook(db, raw: bytes, headers: dict) -> None:
    if not _configured() or placeholder(cfg.paypal_webhook_id):
        raise unavailable()
    event = parse_json(raw)
    if not isinstance(event, dict) or not _verified(headers, event):
        raise ApiError(400, "invalid_signature", "Invalid webhook signature")
    r, cur, kind = event.get("resource") or {}, cfg.paypal_currency.upper(), event.get("event_type")
    amount = r.get("amount") or {}
    if kind == "PAYMENT.CAPTURE.COMPLETED" and amount.get("currency_code") == cur and r.get("status") == "COMPLETED":
        mark_paid(db, db.parse_id(r.get("custom_id")), _minor(amount.get("value")))
    elif kind == "CHECKOUT.ORDER.APPROVED" and r.get("id"):
        unit = (r.get("purchase_units") or [{}])[0]                     # capture only an order we created: same stored order, amount, still pending
        oid = db.parse_id(unit.get("custom_id"))
        order = get_order(db, oid) if oid is not None else None
        ua = unit.get("amount") or {}
        if order and order.status == "pending" and ua.get("currency_code") == cur and _minor(ua.get("value")) == to_cents(order.total):
            _api(f"/v2/checkout/orders/{r['id']}/capture", {}, f"capture-{r['id']}")        # PayPal-Request-Id keeps the capture idempotent

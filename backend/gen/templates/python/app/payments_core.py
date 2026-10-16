"""Stripe, called with the standard library (no SDK). The amount always comes from the stored order, never from the client."""
import hashlib
import hmac
import time
import urllib.parse

from .config import cfg
from .errors import ApiError
from .pay_shared import mark_paid, parse_json, payable_order, placeholder, rejected, request_json, unavailable

TOLERANCE_SEC = 300


def verify_signature(raw: bytes, header: str, secret: str, now: float | None = None) -> bool:
    parts = dict(p.strip().split("=", 1) for p in (header or "").split(",") if "=" in p)
    try:
        ts = int(parts.get("t", ""))
    except ValueError:
        return False
    if abs((now if now is not None else time.time()) - ts) > TOLERANCE_SEC or not parts.get("v1"):
        return False
    want = hmac.new(secret.encode(), f"{ts}.".encode() + raw, hashlib.sha256).hexdigest()
    return hmac.compare_digest(want, parts["v1"])


def create_intent(db, user_id, order_id) -> dict:
    if placeholder(cfg.stripe_secret_key):
        raise unavailable()
    oid, cents, total = payable_order(db, user_id, order_id)
    body = urllib.parse.urlencode({"amount": cents, "currency": cfg.stripe_currency, "metadata[order_id]": oid, "automatic_payment_methods[enabled]": "true"}).encode()
    ok, data = request_json("https://api.stripe.com/v1/payment_intents", data=body, headers={
        "Authorization": f"Bearer {cfg.stripe_secret_key}", "Content-Type": "application/x-www-form-urlencoded", "Idempotency-Key": f"order-{oid}-{cents}"})
    if not ok or not data.get("client_secret"):
        raise rejected()
    return {"clientSecret": data["client_secret"], "orderId": oid, "amount": total, "currency": cfg.stripe_currency}


def handle_webhook(db, raw: bytes, headers: dict) -> None:
    """headers: lower-case names. The signature is checked over the exact raw bytes before anything is parsed."""
    if not cfg.stripe_webhook_secret:
        raise unavailable()
    if not verify_signature(raw, headers.get("stripe-signature", ""), cfg.stripe_webhook_secret):
        raise ApiError(400, "invalid_signature", "Invalid webhook signature")
    event = parse_json(raw) or {}
    obj = (event.get("data") or {}).get("object") or {}
    if event.get("type") == "payment_intent.succeeded":
        mark_paid(db, db.parse_id((obj.get("metadata") or {}).get("order_id")), obj.get("amount_received"))

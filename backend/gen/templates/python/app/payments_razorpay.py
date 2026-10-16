"""Razorpay, called with the standard library (no SDK). The amount comes from the stored order, in paise."""
import base64
import hashlib
import hmac
import json
import re

from .config import cfg
from .errors import ApiError
from .pay_shared import mark_paid, parse_json, payable_order, placeholder, rejected, request_json, unavailable


def verify_signature(raw: bytes, header: str, secret: str) -> bool:
    if not secret or not isinstance(header, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", header):
        return False
    return hmac.compare_digest(hmac.new(secret.encode(), raw, hashlib.sha256).hexdigest(), header.lower())


def create_intent(db, user_id, order_id) -> dict:
    if placeholder(cfg.razorpay_key_id) or placeholder(cfg.razorpay_key_secret):
        raise unavailable()
    oid, minor, total = payable_order(db, user_id, order_id)
    auth = base64.b64encode(f"{cfg.razorpay_key_id}:{cfg.razorpay_key_secret}".encode()).decode()
    ok, data = request_json("https://api.razorpay.com/v1/orders", headers={"Authorization": f"Basic {auth}", "Content-Type": "application/json"},
                            data=json.dumps({"amount": minor, "currency": cfg.razorpay_currency.upper(), "receipt": f"order-{oid}", "notes": {"order_id": str(oid)}}).encode())
    if not ok or not data.get("id"):
        raise rejected()
    # key_id is public by design (the checkout widget needs it); the secret never leaves the server.
    return {"razorpayOrderId": data["id"], "keyId": cfg.razorpay_key_id, "orderId": oid, "amount": total, "currency": cfg.razorpay_currency}


def handle_webhook(db, raw: bytes, headers: dict) -> None:
    if placeholder(cfg.razorpay_webhook_secret):
        raise unavailable()
    if not verify_signature(raw, headers.get("x-razorpay-signature", ""), cfg.razorpay_webhook_secret):
        raise ApiError(400, "invalid_signature", "Invalid webhook signature")
    event = parse_json(raw) or {}
    p = (((event.get("payload") or {}).get("payment") or {}).get("entity")) or {}
    if event.get("event") == "payment.captured" and isinstance(p.get("notes"), dict) and str(p.get("currency", "")).lower() == cfg.razorpay_currency:
        mark_paid(db, db.parse_id(p["notes"].get("order_id")), p.get("amount"))

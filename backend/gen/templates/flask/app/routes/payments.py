from flask import Blueprint, request

from ..deps import current_user, get_db, json_body


def make_blueprint() -> Blueprint:
    bp = Blueprint("payments", __name__)

    @bp.post("/intent")
    def intent():
        """Start a payment for one of your pending orders (amount read from the order)"""
        from .. import payments_core
        user = current_user()
        body = json_body() or {}
        return payments_core.create_intent(get_db(), user["id"], body.get("orderId") if isinstance(body, dict) else None), 201

    @bp.post("/webhook")
    def webhook():
        """Payment provider webhook (signature verified)"""
        from .. import payments_core
        payments_core.handle_webhook(get_db(), request.get_data(), {k.lower(): v for k, v in request.headers.items()})
        return {"received": True}

    return bp

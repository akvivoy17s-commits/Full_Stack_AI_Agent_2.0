from flask import Blueprint

from ..deps import current_user, get_db, json_body


def make_blueprint() -> Blueprint:
    bp = Blueprint("checkout", __name__)

    @bp.post("")
    def checkout():
        """Create an order from cart items (server-side prices and stock)"""
        from .. import checkout_core
        user = current_user()
        body = json_body() or {}
        return {"order": checkout_core.create_order(get_db(), user["id"], body.get("items") if isinstance(body, dict) else None)}, 201

    return bp

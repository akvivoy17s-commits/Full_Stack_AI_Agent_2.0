from . import checkout_core
from .deps import current_user, get_db
from .views import json_body, only, respond


@only("POST")
def checkout(request):
    """Create an order from cart items (server-side prices and stock)"""
    user = current_user(request)
    body = json_body(request) or {}
    return respond({"order": checkout_core.create_order(get_db(), user["id"], body.get("items") if isinstance(body, dict) else None)}, 201)

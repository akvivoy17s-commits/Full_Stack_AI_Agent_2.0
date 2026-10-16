from django.views.decorators.csrf import csrf_exempt

from . import payments_core
from .deps import current_user, get_db
from .views import json_body, only, respond


@only("POST")
def intent(request):
    """Start a payment for one of your pending orders (amount read from the order)"""
    user = current_user(request)
    body = json_body(request) or {}
    return respond(payments_core.create_intent(get_db(), user["id"], body.get("orderId") if isinstance(body, dict) else None), 201)


@csrf_exempt
@only("POST")
def webhook(request):
    """Payment provider webhook (signature verified over the exact raw body)"""
    payments_core.handle_webhook(get_db(), request.body, {k.lower(): v for k, v in request.headers.items()})
    return respond({"received": True})

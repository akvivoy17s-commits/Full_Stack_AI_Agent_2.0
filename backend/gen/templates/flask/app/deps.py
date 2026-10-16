import json
from functools import wraps

from flask import current_app, request

from . import schema
from .errors import ApiError
from .ratelimit import Limiter, pick_ip

AUTH_LIMIT, PUBLIC_LIMIT, API_LIMIT = Limiter(20), Limiter(30), Limiter(600)


def client_ip() -> str:
    return pick_ip(request.remote_addr, request.headers.get("X-Forwarded-For"))


def rate_limit(limiter: Limiter):
    def wrap(fn):
        @wraps(fn)
        def inner(*a, **k):
            limiter.enforce(client_ip())
            return fn(*a, **k)
        return inner
    return wrap


def get_db():
    return current_app.extensions["db"]


def json_body():
    """Parsed JSON body, or None when the body is empty. A body that is not valid JSON is a 400."""
    raw = request.get_data(cache=True)
    if not raw.strip():
        return None
    try:
        return json.loads(raw)
    except ValueError:
        raise ApiError(400, "invalid_json", "Request body is not valid JSON") from None


def current_user() -> dict:
    """Verifies the bearer token (HS256 only) and returns {"id", "role"}."""
    header = request.headers.get("Authorization", "")
    if not schema.SCHEMA["auth"] or header[:7].lower() != "bearer " or not header[7:].strip():
        raise ApiError(401, "unauthorized", "Authentication required")
    from .security import decode_access
    return decode_access(header[7:].strip())


def require_admin() -> dict:
    from .service import is_admin
    user = current_user()
    if not is_admin(user):
        raise ApiError(403, "forbidden", "You do not have access to this resource")
    return user


def user_for(level: str):
    """Access levels come from the app spec: public | user | owner | admin. 'owner' is finished per record in service.py."""
    return (lambda: None) if level == "public" else require_admin if level == "admin" else current_user

from functools import wraps

from . import schema
from .errors import ApiError
from .ratelimit import Limiter, pick_ip

AUTH_LIMIT, PUBLIC_LIMIT, API_LIMIT = Limiter(20), Limiter(30), Limiter(600)
_db = None


def client_ip(request) -> str:
    return pick_ip(request.META.get("REMOTE_ADDR"), request.headers.get("X-Forwarded-For"))


def rate_limit(limiter: Limiter):
    def wrap(fn):
        @wraps(fn)
        def inner(request, *a, **k):
            limiter.enforce(client_ip(request))
            return fn(request, *a, **k)
        return inner
    return wrap


def get_db():
    """The data layer (None when the app has no database). The adapter is stateless: Django manages the connections."""
    global _db
    if _db is None and schema.SCHEMA["db"]:
        from .db import connect
        _db = connect()
    return _db


def current_user(request) -> dict:
    """Verifies the bearer token (HS256 only) and returns {"id", "role"}."""
    header = request.headers.get("Authorization", "")
    if not schema.SCHEMA["auth"] or header[:7].lower() != "bearer " or not header[7:].strip():
        raise ApiError(401, "unauthorized", "Authentication required")
    from .security import decode_access
    return decode_access(header[7:].strip())


def require_admin(request) -> dict:
    from .service import is_admin
    user = current_user(request)
    if not is_admin(user):
        raise ApiError(403, "forbidden", "You do not have access to this resource")
    return user


def user_for(level: str):
    """Access levels come from the app spec: public | user | owner | admin. 'owner' is finished per record in service.py."""
    return (lambda request: None) if level == "public" else require_admin if level == "admin" else current_user

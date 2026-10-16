from fastapi import Depends, Request

from . import schema
from .errors import ApiError
from .ratelimit import Limiter, pick_ip

AUTH_LIMIT, PUBLIC_LIMIT, API_LIMIT = Limiter(20), Limiter(30), Limiter(600)


def client_ip(request: Request) -> str:
    return pick_ip(request.client.host if request.client else None, request.headers.get("x-forwarded-for"))


def rate_limit(limiter: Limiter):
    def dep(request: Request) -> None:
        limiter.enforce(client_ip(request))
    return dep


def get_db(request: Request):
    return request.app.state.db


def anonymous():
    return None


def current_user(request: Request) -> dict:
    """Verifies the bearer token (HS256 only) and returns {"id", "role"}."""
    header = request.headers.get("authorization", "")
    if not schema.SCHEMA["auth"] or header[:7].lower() != "bearer " or not header[7:].strip():
        raise ApiError(401, "unauthorized", "Authentication required")
    from .security import decode_access
    return decode_access(header[7:].strip())


def require_admin(user: dict = Depends(current_user)) -> dict:
    from .service import is_admin
    if not is_admin(user):
        raise ApiError(403, "forbidden", "You do not have access to this resource")
    return user


def user_dep(level: str):
    """Access levels come from the app spec: public | user | owner | admin. 'owner' is finished per record in service.py."""
    return anonymous if level == "public" else require_admin if level == "admin" else current_user

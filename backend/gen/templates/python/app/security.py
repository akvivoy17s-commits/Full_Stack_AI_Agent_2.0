import hashlib
import secrets
import time

import bcrypt
import jwt

from .config import cfg
from .errors import ApiError

_DUMMY = None


def hash_password(pw: str) -> str:
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt(rounds=cfg.bcrypt_rounds)).decode()


def verify_password(pw: str, hashed: str | None) -> bool:
    """Always does one bcrypt comparison, so unknown emails cost the same time as wrong passwords."""
    global _DUMMY
    if _DUMMY is None:
        _DUMMY = hash_password("not-a-real-password")
    try:
        ok = bcrypt.checkpw(pw.encode(), (hashed or _DUMMY).encode())
    except ValueError:
        return False
    return bool(hashed) and ok


def sign_access(user: dict) -> str:
    now = int(time.time())
    payload = {"sub": str(user["id"]), "role": user["role"], "iat": now, "exp": now + round(cfg.access_ttl_min * 60)}
    return jwt.encode(payload, cfg.jwt_secret, algorithm="HS256")


def decode_access(token: str) -> dict:
    """HS256 only; expiry and subject are required. Returns {"id", "role"}."""
    try:
        p = jwt.decode(token, cfg.jwt_secret, algorithms=["HS256"], options={"require": ["exp", "sub"]})
    except jwt.PyJWTError:
        raise ApiError(401, "invalid_token", "Invalid or expired token") from None
    return {"id": str(p["sub"]), "role": p.get("role")}


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def new_refresh_token() -> str:
    return secrets.token_urlsafe(48)

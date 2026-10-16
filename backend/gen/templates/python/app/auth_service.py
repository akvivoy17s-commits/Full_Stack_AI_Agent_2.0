"""Framework-independent authentication: sign-up, sign-in, rotating single-use refresh tokens, sign-out."""
from datetime import datetime, timedelta, timezone

from . import schema, validation as V
from .config import cfg
from .errors import ApiError, validation_failed
from .security import hash_password, new_refresh_token, sha256, sign_access, verify_password

USER = "User"
S = schema.SCHEMA
_INVALID = ApiError(401, "invalid_credentials", "Invalid email or password")
_BAD_REFRESH = ApiError(401, "invalid_token", "Invalid refresh token")


def _text(v, mx) -> bool:
    return isinstance(v, str) and len(v) <= mx


def _issue(db, user: dict) -> dict:
    out = {"user": user, "accessToken": sign_access(user), "tokenType": "Bearer", "expiresIn": round(cfg.access_ttl_min * 60)}
    if S["refresh"]:
        raw = new_refresh_token()
        exp = datetime.now(timezone.utc) + timedelta(days=cfg.refresh_ttl_days)
        db.create("RefreshToken", {"user_id": db.parse_id(user["id"]), "token_hash": sha256(raw), "expires_at": V.iso(exp)})
        out["refreshToken"] = raw
    return out


def register(db, body) -> dict:
    b = body if isinstance(body, dict) else {}
    errors = {}
    if not _text(b.get("email"), 255) or not V.EMAIL.match(b["email"].strip()):
        errors["email"] = "must be a valid email"
    if not _text(b.get("name"), 255) or not b["name"].strip():
        errors["name"] = "is required (max 255 characters)"
    if not _text(b.get("password"), 200) or len(b["password"]) < 8 or len(b["password"].encode()) > 72:
        errors["password"] = "must be 8-72 characters"
    errors.update({k: "is not an accepted field" for k in b if k not in ("email", "name", "password")})
    if errors:
        raise validation_failed(details=errors)
    email = b["email"].strip().lower()
    if db.find_one(USER, {"email": email}):
        raise ApiError(409, "conflict", "A record with the same unique value already exists")
    data = {"email": email, "name": b["name"].strip(), "password_hash": hash_password(b["password"]),
            "role": S["defaultRole"]}  # never client-controlled; the first admin comes from the seed script
    if any(f["name"] == "created_at" for f in S["entities"][USER]["fields"]):
        data["created_at"] = V.now_iso()
    return _issue(db, db.create(USER, data))


def login(db, body) -> dict:
    b = body if isinstance(body, dict) else {}
    if not _text(b.get("email"), 255) or not _text(b.get("password"), 200):
        raise validation_failed("email and password must be text")
    u = db.find_one(USER, {"email": b["email"].strip().lower()}, raw=True)
    if not verify_password(b["password"], u["password_hash"] if u else None) or not u:
        raise _INVALID
    return _issue(db, db.clean(USER, u))


def refresh(db, body) -> dict:
    t = body.get("refreshToken") if isinstance(body, dict) else None
    if not _text(t, 200):
        raise _BAD_REFRESH
    h = sha256(t)
    row = db.find_one("RefreshToken", {"token_hash": h})
    # delete first, then check: a token works once, even under concurrent requests
    if not row or db.remove_where("RefreshToken", {"token_hash": h}) != 1 or V.parse_dt(row["expires_at"]) < datetime.now(timezone.utc):
        raise _BAD_REFRESH
    user = db.get(USER, row["user_id"])
    if not user:
        raise _BAD_REFRESH
    return _issue(db, user)


def logout(db, user: dict, body) -> None:
    if S["refresh"]:
        where = {"user_id": db.parse_id(user["id"])}
        t = body.get("refreshToken") if isinstance(body, dict) else None
        if _text(t, 200):
            where["token_hash"] = sha256(t)
        db.remove_where("RefreshToken", where)  # without a token: sign out everywhere


def me(db, user: dict) -> dict:
    u = db.get(USER, db.parse_id(user["id"]))
    if not u:
        raise ApiError(401, "invalid_token", "Account no longer exists")
    return {"user": u}

"""Typed validation driven by schema.py. Same rules and messages for every framework."""
import math
import re
from datetime import datetime, timezone
from urllib.parse import urlparse

from . import schema
from .errors import validation_failed

EMAIL = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]{2,}$")
OBJECT_ID = re.compile(r"^[a-f0-9]{24}$", re.I)
MONGO = schema.SCHEMA["db"] == "mongodb"
INT32 = 2147483647  # ids and `int` fields are 32-bit columns in every SQL database we generate for


def parse_dt(s):
    try:
        d = datetime.fromisoformat(s.strip().replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None
    return (d if d.tzinfo else d.replace(tzinfo=timezone.utc)).astimezone(timezone.utc)


def iso(d: datetime) -> str:
    return d.astimezone(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def now_iso() -> str:
    return iso(datetime.now(timezone.utc))


def _int(v) -> bool:
    return isinstance(v, int) and not isinstance(v, bool) and abs(v) <= INT32


def one(f: dict, v):
    """Checks ONE value against its field definition. Returns (True, normalised) or (False, message)."""
    t = f["type"]
    if t in ("string", "text"):
        if not isinstance(v, str):
            return False, "must be text"
        s, mx = v.strip(), (20000 if t == "text" else 255)
        if f["required"] and not s:
            return False, "is required"
        return (False, f"must be at most {mx} characters") if len(s) > mx else (True, s)
    if t == "email":
        ok = isinstance(v, str) and len(v) <= 255 and EMAIL.match(v.strip())
        return (True, v.strip().lower()) if ok else (False, "must be a valid email")
    if t == "url":
        try:
            u = urlparse(v)
            if isinstance(v, str) and len(v) <= 2048 and u.scheme in ("http", "https") and u.netloc:
                return True, v.strip()
        except ValueError:
            pass
        return False, "must be an http(s) URL"
    if t == "int":
        if isinstance(v, float) and v.is_integer():
            v = int(v)
        return (True, v) if _int(v) else (False, "must be a whole number between -2147483647 and 2147483647")
    if t == "float":
        ok = isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)
        return (True, v) if ok else (False, "must be a number")
    if t == "bool":
        return (True, v) if isinstance(v, bool) else (False, "must be true or false")
    if t == "datetime":
        d = parse_dt(v) if isinstance(v, str) else None
        return (True, iso(d)) if d else (False, "must be an ISO date-time")
    if t == "enum":
        return (True, v) if isinstance(v, str) and v in f["values"] else (False, "must be one of: " + ", ".join(f["values"]))
    if t == "ref":
        ok = (isinstance(v, str) and OBJECT_ID.match(v)) if MONGO else (_int(v) and v > 0)
        return (True, v) if ok else (False, "must be a valid id")
    return False, "has an unsupported type"


def writable(e: dict, f: dict) -> bool:
    """Sensitive columns, server-set timestamps and the owner link are never client-controlled."""
    return f["name"] not in e["sensitive"] and f["name"] != e["ownerField"] and f["name"] not in ("id", "created_at", "updated_at")


def validate_body(e: dict, body, partial: bool) -> dict:
    if not isinstance(body, dict):
        raise validation_failed("Body must be a JSON object")
    fields = [f for f in e["fields"] if writable(e, f)]
    names = {f["name"] for f in fields}
    errors, data = {}, {}
    for k in body:
        if k not in names:
            errors[k] = "is not an accepted field"
    for f in fields:
        n = f["name"]
        if n not in body:
            if not partial and f["required"]:
                errors[n] = "is required"
            continue
        v = body[n]
        if v is None:
            if f["required"]:
                errors[n] = "is required"
            else:
                data[n] = None
            continue
        ok, r = one(f, v)
        if ok:
            data[n] = r
        else:
            errors[n] = r
    if errors:
        raise validation_failed(details=errors)
    return data


def _num(query: dict, key: str, default: int, mx: int) -> int:
    if key not in query:
        return default
    vals = query[key]
    if len(vals) != 1 or not re.fullmatch(r"[0-9]+", vals[0]) or int(vals[0]) < 1:
        raise validation_failed("page and limit must be positive integers")
    return min(int(vals[0]), mx)


def parse_list(e: dict, query: dict) -> dict:
    """query maps each parameter to the list of its values. Supports ?page, ?limit (max 100), ?q and exact filters on ref / enum / bool fields."""
    page, limit = _num(query, "page", 1, 10**6), _num(query, "limit", 20, 100)
    q = None
    if "q" in query:
        if len(query["q"]) != 1 or len(query["q"][0]) > 100:
            raise validation_failed("q must be text up to 100 characters")
        q = query["q"][0].strip() or None
    filters = {}
    for f in e["fields"]:
        if f["type"] not in ("ref", "enum", "bool") or f["name"] not in query:
            continue
        vals = query[f["name"]]
        if len(vals) != 1:
            raise validation_failed(f"{f['name']} must be a single value")
        v = vals[0]
        if f["type"] == "bool":
            v = True if v == "true" else False if v == "false" else v
        elif f["type"] == "ref" and not MONGO and re.fullmatch(r"[0-9]+", v):
            v = int(v)
        ok, r = one(f, v)
        if not ok:
            raise validation_failed(f"{f['name']} {r}")
        filters[f["name"]] = r
    sort = {"field": "id", "dir": "desc"}
    if "sort" in query:
        if len(query["sort"]) != 1:
            raise validation_failed("sort must be a single value")
        raw = query["sort"][0]
        desc = raw.startswith("-")
        name = raw[1:] if desc else raw
        if not (name == "id" or any(f["name"] == name and f["type"] != "text" and name not in e["sensitive"] for f in e["fields"])):
            raise validation_failed("sort must be id or a non-text field name, optionally prefixed with - for descending")
        sort = {"field": name, "dir": "desc" if desc else "asc"}
    return {"page": page, "limit": limit, "q": q, "filters": filters, "sort": sort}

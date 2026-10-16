"""Framework-neutral helpers for the cache and live-update layers."""
import hashlib

from . import schema

OPS = {"POST": "create", "PUT": "update", "DELETE": "delete"}
_BY_PATH = {e["path"]: e["name"] for e in schema.SCHEMA["entities"].values() if not e.get("internal")}


def entity_for(path: str) -> str | None:
    parts = path.strip("/").split("/")
    return _BY_PATH.get(parts[1]) if len(parts) >= 2 and parts[0] == "api" else None


def read_key(version: str, authorization: str, url: str) -> str:
    who = hashlib.sha256((authorization or "").encode()).hexdigest()[:16]
    return f"r:{version}:{who}:{url}"

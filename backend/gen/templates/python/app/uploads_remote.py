"""Uploads to a private bucket (S3-compatible or Firebase Storage): the type comes from the file's magic bytes, never from the client's Content-Type or file name. Stored under a random name."""
import re
import secrets

from . import storage_remote as store
from .config import cfg
from .errors import ApiError

KINDS = [  # (extension, mime, test)
    ("png", "image/png", lambda b: b[:8] == b"\x89PNG\r\n\x1a\n"),
    ("jpg", "image/jpeg", lambda b: b[:3] == b"\xff\xd8\xff"),
    ("gif", "image/gif", lambda b: b[:6] in (b"GIF87a", b"GIF89a")),
    ("webp", "image/webp", lambda b: b[:4] == b"RIFF" and b[8:12] == b"WEBP"),
    ("pdf", "application/pdf", lambda b: b[:5] == b"%PDF-"),
]
NAME = re.compile(r"^[0-9a-f]{32}\.(png|jpg|gif|webp|pdf)$")
HEADERS = {"X-Content-Type-Options": "nosniff", "Content-Security-Policy": "default-src 'none'; sandbox", "Cache-Control": "private, max-age=3600"}


def save(data: bytes) -> dict:
    if not data:
        raise ApiError(400, "validation_failed", "Send the file as the request body")
    if len(data) > cfg.upload_max_bytes:
        raise ApiError(413, "payload_too_large", "The file is too large")
    kind = next((k for k in KINDS if len(data) > 12 and k[2](data)), None)
    if not kind:
        raise ApiError(415, "unsupported_type", "Only PNG, JPEG, GIF, WebP and PDF files are accepted")
    name = f"{secrets.token_hex(16)}.{kind[0]}"
    store.put(f"uploads/{name}", data, kind[1])      # private bucket; the type is the one found from the bytes
    return {"name": name, "url": f"/api/uploads/{name}", "size": len(data), "type": kind[1]}


def read(name: str) -> tuple[bytes, str]:
    if not NAME.match(name):
        raise ApiError(404, "not_found", "File not found")
    data = store.get(f"uploads/{name}")
    if data is None:
        raise ApiError(404, "not_found", "File not found")
    return data, next(k[1] for k in KINDS if name.endswith("." + k[0]))

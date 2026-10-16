"""Phase 1 security layer: request guards, path rules, URL validation. One module, used by main.py / schemas / files."""
import hmac
import ipaddress
import socket
from urllib.parse import urlparse

from starlette.requests import Request
from starlette.responses import JSONResponse

from backend import config

UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
OPEN_PATHS = {"/health"}                                   # always reachable (no token)
SANDBOX_PREFIXES = ("/preview/", "/projects/")             # /projects/{pid}/shot/... is checked by suffix below
BLOCKED_HOSTS = {"metadata.google.internal", "metadata", "instance-data"}


def is_agent_path(path: str) -> bool:
    """True if a relative path touches the agent's private `.agent` directory (case-insensitive: Windows/macOS)."""
    return any(p.strip().lower() == ".agent" for p in path.replace("\\", "/").split("/"))


def validate_base_url(value: str) -> str:
    """Model-endpoint URL rules (anti-SSRF). LAN/loopback Ollama hosts stay allowed; cloud-metadata/link-local targets do not."""
    v = value.strip()
    u = urlparse(v)
    if u.scheme not in ("http", "https") or not u.hostname:
        raise ValueError("must be an http(s) URL, e.g. http://localhost:11434")
    if u.username or u.password:
        raise ValueError("credentials in the URL are not allowed (use environment variables)")
    host = u.hostname.lower()
    if host in BLOCKED_HOSTS:
        raise ValueError("this host is not allowed")
    try:
        infos = {i[4][0] for i in socket.getaddrinfo(host, u.port or 80, proto=socket.IPPROTO_TCP)}
    except (socket.gaierror, UnicodeError):
        infos = set()                                       # unresolved now (e.g. Ollama not started): the connection error is reported later
    for raw in infos:
        ip = ipaddress.ip_address(raw.split("%")[0])
        if isinstance(ip, ipaddress.IPv6Address):            # DNS64/NAT64 (64:ff9b::/96) and IPv4-mapped: judge the embedded IPv4
            if ip in ipaddress.ip_network("64:ff9b::/96"):
                ip = ipaddress.IPv4Address(int(ip) & 0xFFFFFFFF)
            elif ip.ipv4_mapped:
                ip = ip.ipv4_mapped
        if ip.is_link_local or ip.is_unspecified or ip.is_multicast or (ip.is_reserved and not ip.is_loopback):
            raise ValueError(f"link-local/unspecified/metadata addresses are not allowed (host '{host}' resolved to {ip}). Use http://localhost:11434 for Ollama, or check your hosts file / DNS / VPN / ad-blocker if this is a cloud API host")
    return v.rstrip("/")


def _deny(code: int, msg: str) -> JSONResponse:
    return JSONResponse({"detail": msg}, status_code=code)


async def guard(request: Request, call_next):
    """Order: host check -> optional API token -> Origin check (CSRF) -> response hardening."""
    path = request.url.path
    host = request.headers.get("host", "").rsplit(":", 1)[0].lower()
    if "*" not in config.ALLOWED_HOSTS and host not in config.ALLOWED_HOSTS:
        return _deny(400, "host not allowed")                                # DNS-rebinding defence
    if config.API_TOKEN and request.method != "OPTIONS" and path not in OPEN_PATHS:
        auth = request.headers.get("authorization", "")
        got = request.headers.get("x-api-token") or (auth[7:] if auth.lower().startswith("bearer ") else "") or request.query_params.get("token", "")
        if not hmac.compare_digest(got.encode(), config.API_TOKEN.encode()):
            return _deny(401, "missing or invalid API token")
    if request.method in UNSAFE_METHODS:
        origin = request.headers.get("origin")
        if origin is not None and origin not in config.CORS_ORIGINS:         # browsers always send Origin; "null" = sandboxed page
            return _deny(403, "origin not allowed")
    resp = await call_next(request)
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["Referrer-Policy"] = "no-referrer"
    if path.startswith("/preview/") or "/shot/" in path:
        # Generated pages are untrusted: opaque origin (no cookies/storage access to the API origin); CORS lets module scripts load.
        resp.headers["Content-Security-Policy"] = "sandbox allow-scripts allow-forms allow-popups allow-modals"
        resp.headers["Access-Control-Allow-Origin"] = "*"
    return resp
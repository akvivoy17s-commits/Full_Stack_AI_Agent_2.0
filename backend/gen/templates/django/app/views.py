"""HTTP layer only: every view maps the request onto service.py / auth_service.py, which hold the rules."""
import html
import json
from pathlib import Path
from functools import wraps

from django.core.exceptions import RequestDataTooBig
from django.http import HttpResponse, JsonResponse

from . import schema
from .deps import AUTH_LIMIT, PUBLIC_LIMIT, client_ip, current_user, get_db, rate_limit, user_for
from .errors import ApiError
from .middleware import error_response

S = schema.SCHEMA
if S["db"]:
    from . import service
if S["auth"]:
    from . import auth_service


def respond(data: dict, status: int = 200) -> JsonResponse:
    return JsonResponse(data, status=status)


def no_content() -> HttpResponse:
    return HttpResponse(status=204)


def not_allowed(allowed) -> JsonResponse:
    res = error_response(ApiError(405, "method_not_allowed", "Method not allowed"))
    res["Allow"] = ", ".join(sorted(allowed))
    return res


def only(*allowed):
    def wrap(fn):
        @wraps(fn)
        def inner(request, *a, **k):
            ok = request.method in allowed or (request.method == "HEAD" and "GET" in allowed)    # HEAD works wherever GET does (health probes)
            return fn(request, *a, **k) if ok else not_allowed(allowed)
        return inner
    return wrap


def json_body(request):
    """Parsed JSON body, or None when the body is empty. A body that is not valid JSON is a 400."""
    try:
        raw = request.body
    except RequestDataTooBig:
        raise ApiError(413, "payload_too_large", "Request body is too large") from None
    if not raw.strip():
        return None
    try:
        return json.loads(raw)
    except (ValueError, RecursionError):
        raise ApiError(400, "invalid_json", "Request body is not valid JSON") from None


# ------------------------------------------------------------------ error pages (urls.py handler400 / handler404 / handler500)
def bad_request(request, exception=None):
    return error_response(ApiError(400, "bad_request", "Bad request"))


def not_found(request, exception=None):
    return error_response(ApiError(404, "not_found", "Route not found"))


def server_error(request):
    return error_response(ApiError(500, "internal_error", "Something went wrong"))


# ------------------------------------------------------------------ health
@only("GET")
def health(request):
    """Liveness and database check"""
    db = get_db()
    try:
        if db:
            db.ping()
    except Exception:  # noqa: BLE001  any driver error means "down"
        return respond({"status": "degraded", "db": "down"}, 503)
    return respond({"status": "ok", **({"db": "up"} if db else {})})


# ------------------------------------------------------------------ auth
limited = rate_limit(AUTH_LIMIT)


@only("POST")
@limited
def auth_register(request):
    """Create an account (body: email, name, password)"""
    return respond(auth_service.register(get_db(), json_body(request)), 201)


@only("POST")
@limited
def auth_login(request):
    """Sign in (body: email, password)"""
    return respond(auth_service.login(get_db(), json_body(request)))


@only("POST")
@limited
def auth_refresh(request):
    """Exchange a refresh token for new tokens (single use)"""
    return respond(auth_service.refresh(get_db(), json_body(request)))


@only("POST")
def auth_logout(request):
    """Sign out (body: refreshToken, optional)"""
    user = current_user(request)
    auth_service.logout(get_db(), user, json_body(request))
    return no_content()


@only("GET")
def auth_me(request):
    """The signed-in user"""
    return respond(auth_service.me(get_db(), current_user(request)))


# ------------------------------------------------------------------ generic CRUD, one pair of views for every entity of the spec
def collection(request, name):
    e, ops = S["entities"][name], S["entities"][name]["ops"]
    allowed = [m for m, o in (("GET", "list"), ("POST", "create")) if o in ops]
    if request.method == "GET" and "list" in ops:
        user = user_for(e["read"])(request)
        return respond(service.list_records(get_db(), e, dict(request.GET.lists()), user))
    if request.method == "POST" and "create" in ops:
        if e["write"] == "public":
            PUBLIC_LIMIT.enforce(client_ip(request))
        user = user_for(e["write"])(request)
        return respond(service.create_record(get_db(), e, json_body(request), user), 201)
    return not_allowed(allowed)


def item(request, name, rid):
    e, ops = S["entities"][name], S["entities"][name]["ops"]
    allowed = [m for m, o in (("GET", "get"), ("PUT", "update"), ("DELETE", "delete")) if o in ops]
    if request.method == "GET" and "get" in ops:
        return respond(service.get_record(get_db(), e, rid, user_for(e["read"])(request)))
    if request.method in ("PUT", "DELETE") and {"PUT": "update", "DELETE": "delete"}[request.method] in ops:
        if e["write"] == "public":
            PUBLIC_LIMIT.enforce(client_ip(request))
        user = user_for(e["write"])(request)
        if request.method == "PUT":
            return respond(service.update_record(get_db(), e, rid, json_body(request), user))
        service.delete_record(get_db(), e, rid, user)
        return no_content()
    return not_allowed(allowed)


# ------------------------------------------------------------------ API reference (generated from the spec; Django has no built-in interactive docs)
def _doc(e: dict) -> str:
    fields = ", ".join(f"{f['name']} ({f['type']}{'' if not f['required'] else ', required'})" for f in e["fields"]
                       if f["name"] not in e["sensitive"] and f["name"] != e["ownerField"] and f["name"] not in ("id", "created_at", "updated_at"))
    return f"Accepted fields: {fields or 'none'}. Read access: {e['read']}. Write access: {e['write']}."


def routes() -> list[tuple[str, str, str]]:
    out = [("GET", "/api/health", health.__doc__ or "")]
    if S["auth"]:
        out += [("POST", "/api/auth/register", auth_register.__doc__), ("POST", "/api/auth/login", auth_login.__doc__),
                ("POST", "/api/auth/logout", auth_logout.__doc__), ("GET", "/api/auth/me", auth_me.__doc__)]
        if S["refresh"]:
            out.append(("POST", "/api/auth/refresh", auth_refresh.__doc__))
    if S.get("checkout"):
        out.append(("POST", "/api/checkout", "Create an order from cart items (server-side prices and stock)"))
    if S["integrations"]["payments"]:
        out += [("POST", "/api/payments/intent", "Start a payment for one of your pending orders (amount read from the order)"),
                ("POST", "/api/payments/webhook", "Payment provider webhook (signature verified)")]
    for e in S["entities"].values() if S["db"] else []:
        if e["internal"]:
            continue
        base, ops, n = "/api/" + e["path"], e["ops"], e["name"]
        out += [(m, p, s) for m, p, o, s in (("GET", base, "list", f"List {n} records. {_doc(e)}"), ("POST", base, "create", f"Create a {n} record. {_doc(e)}"),
                                             ("GET", base + "/{id}", "get", f"Get one {n} record"), ("PUT", base + "/{id}", "update", f"Update a {n} record. {_doc(e)}"),
                                             ("DELETE", base + "/{id}", "delete", f"Delete a {n} record")) if o in ops]
    return sorted(out, key=lambda r: (r[1], r[0]))


API_DOC = json.loads((Path(__file__).resolve().parent.parent / "openapi.json").read_text(encoding="utf-8"))


@only("GET")
def openapi(request):
    """OpenAPI description (the same document in every generated backend)"""
    return respond(API_DOC)


@only("GET")
def docs(request):
    """API reference page"""
    rows = "".join(f"<tr><td><b>{m}</b></td><td><code>{html.escape(p)}</code></td><td>{html.escape(s)}</td></tr>" for m, p, s in routes())
    page = (f"<!doctype html><meta charset=utf-8><title>{html.escape(S['title'])} - API</title>"
            "<style>body{font:15px system-ui;margin:2rem auto;max-width:60rem;padding:0 1rem}td{padding:.35rem .6rem;border-bottom:1px solid #ddd;vertical-align:top}</style>"
            f"<h1>{html.escape(S['title'])} - API</h1><p>Machine readable: <a href=/api/openapi.json>/api/openapi.json</a></p><table>{rows}</table>")
    return HttpResponse(page, content_type="text/html; charset=utf-8")

import atexit
import html
import json
from pathlib import Path
import logging

from flask import Flask, jsonify, make_response, request
from werkzeug.exceptions import HTTPException

from . import schema
from .config import cfg
from .deps import API_LIMIT, client_ip
from .errors import ApiError

log = logging.getLogger("app")
MAX_BODY = 100 * 1024
METHODS = "GET, POST, PUT, DELETE"
HEADERS = "Content-Type, Authorization"
HTTP_CODES = {400: "bad_request", 404: "not_found", 405: "method_not_allowed", 413: "payload_too_large", 415: "unsupported_media_type"}


def _json(status: int, code: str, message: str, details: dict | None = None):
    return jsonify(ApiError(status, code, message, details).body()), status


def create_app(db=None) -> Flask:
    """Pass `db` in tests. Otherwise the database is opened here and closed when the process exits."""
    cfg.validate()
    app = Flask(__name__)
    app.url_map.strict_slashes = False
    app.config["MAX_CONTENT_LENGTH"] = max(MAX_BODY, cfg.upload_max_bytes) if schema.SCHEMA["integrations"]["uploads"] else MAX_BODY
    app.json.sort_keys = False
    if db is None and schema.SCHEMA["db"]:
        from .db import connect
        db = connect()
        if cfg.auto_migrate or schema.SCHEMA["db"] == "mongodb":
            db.migrate()
        atexit.register(db.close)
    app.extensions["db"] = db

    @app.before_request
    def _guard():
        if not request.path.startswith("/api"):
            return None
        origin = request.headers.get("Origin")
        if request.method == "OPTIONS" and origin and "Access-Control-Request-Method" in request.headers:
            return make_response("", 204)             # CORS preflight; headers are added in _headers
        API_LIMIT.enforce(client_ip())
        if (request.content_length or 0) > MAX_BODY and request.path != "/api/uploads":
            return _json(413, "payload_too_large", "Request body is too large")
        return None

    @app.after_request
    def _headers(res):
        res.headers.update({"X-Content-Type-Options": "nosniff", "X-Frame-Options": "DENY", "Referrer-Policy": "no-referrer"})
        origin = request.headers.get("Origin")
        if request.path.startswith("/api"):
            res.headers["Cache-Control"] = "no-store"
            if origin and origin in cfg.cors_origins:
                res.headers["Access-Control-Allow-Origin"] = origin
                res.headers.add("Vary", "Origin")
                if request.method == "OPTIONS":
                    res.headers.update({"Access-Control-Allow-Methods": METHODS, "Access-Control-Allow-Headers": HEADERS, "Access-Control-Max-Age": "600"})
        return res

    @app.errorhandler(ApiError)
    def _api_error(e: ApiError):
        return jsonify(e.body()), e.status

    @app.errorhandler(HTTPException)
    def _http_error(e: HTTPException):
        code = e.code or 500
        msg = {404: "Route not found", 413: "Request body is too large"}.get(code, e.description)
        return _json(code, HTTP_CODES.get(code, "http_error"), msg)

    @app.errorhandler(Exception)
    def _unexpected(e: Exception):
        log.error("%s %s failed: %s", request.method, request.path, e, exc_info=True)  # details stay in the log, never in the response
        return _json(500, "internal_error", "Something went wrong")

    @app.get("/api/health")
    def health():
        """Liveness and database check"""
        try:
            if app.extensions["db"]:
                app.extensions["db"].ping()
        except Exception:  # noqa: BLE001  any driver error means "down"
            return {"status": "degraded", "db": "down"}, 503
        extra = {}
        if schema.SCHEMA["integrations"]["cache"]:
            from . import cache
            extra["cache"] = cache.backend()
        return {"status": "ok", **({"db": "up"} if app.extensions["db"] else {}), **extra}

    if schema.SCHEMA["auth"]:
        from .routes import auth
        app.register_blueprint(auth.make_blueprint(), url_prefix="/api/auth")
    if schema.SCHEMA["db"]:
        from .routes import crud
        app.register_blueprint(crud.make_blueprint(), url_prefix="/api")

    if schema.SCHEMA["integrations"]["cache"]:
        from .live import install
        install(app)
    if schema.SCHEMA["integrations"]["uploads"]:
        from .routes import uploads
        app.register_blueprint(uploads.make_blueprint(), url_prefix="/api/uploads")
    if schema.SCHEMA["checkout"]:
        from .routes import checkout
        app.register_blueprint(checkout.make_blueprint(), url_prefix="/api/checkout")
    if schema.SCHEMA["integrations"]["payments"]:
        from .routes import payments
        app.register_blueprint(payments.make_blueprint(), url_prefix="/api/payments")

    API_DOC = json.loads((Path(__file__).resolve().parent.parent / "openapi.json").read_text(encoding="utf-8"))

    def routes() -> list[tuple[str, str, str]]:
        out = []
        for r in sorted(app.url_map.iter_rules(), key=lambda r: (r.rule, sorted(r.methods))):
            if r.rule.startswith("/api/") and r.endpoint != "static" and not r.rule.startswith(("/api/docs", "/api/openapi")):
                summary = (app.view_functions[r.endpoint].__doc__ or "").strip()
                out += [(m, r.rule.replace("<rid>", "{id}"), summary) for m in sorted(r.methods - {"HEAD", "OPTIONS"})]
        return out

    @app.get("/api/openapi.json")
    def openapi():
        """OpenAPI description (the same document in every generated backend)"""
        return API_DOC

    @app.get("/api/docs")
    def docs():
        """API reference page"""
        rows = "".join(f"<tr><td><b>{m}</b></td><td><code>{html.escape(p)}</code></td><td>{html.escape(s)}</td></tr>" for m, p, s in routes())
        page = (f"<!doctype html><meta charset=utf-8><title>{html.escape(schema.SCHEMA['title'])} - API</title>"
                "<style>body{font:15px system-ui;margin:2rem auto;max-width:60rem;padding:0 1rem}td{padding:.35rem .6rem;border-bottom:1px solid #ddd;vertical-align:top}</style>"
                f"<h1>{html.escape(schema.SCHEMA['title'])} - API</h1><p>Machine readable: <a href=/api/openapi.json>/api/openapi.json</a></p><table>{rows}</table>")
        return page, 200, {"Content-Type": "text/html; charset=utf-8"}

    return app

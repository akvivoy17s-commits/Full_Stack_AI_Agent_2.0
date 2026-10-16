import json
import logging
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as HttpException

from . import schema
from .config import cfg
from .deps import API_LIMIT, client_ip
from .errors import ApiError

log = logging.getLogger("app")
MAX_BODY = 100 * 1024


def _json(status: int, code: str, message: str, details: dict | None = None) -> JSONResponse:
    return JSONResponse(ApiError(status, code, message, details).body(), status_code=status)


def create_app(db=None) -> FastAPI:
    """Pass `db` in tests. Otherwise the database is opened on startup and closed on shutdown."""
    cfg.validate()
    own_db = db is None and bool(schema.SCHEMA["db"])

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if own_db:
            from .db import connect
            app.state.db = connect()
            if cfg.auto_migrate or schema.SCHEMA["db"] == "mongodb":
                app.state.db.migrate()
        yield
        if own_db:
            app.state.db.close()

    app = FastAPI(title=schema.SCHEMA["title"], version="1.0.0", lifespan=lifespan, docs_url="/api/docs", redoc_url=None,
                  openapi_url="/api/openapi.json")
    app.state.db = db
    _doc = json.loads((Path(__file__).resolve().parent.parent / "openapi.json").read_text(encoding="utf-8"))   # same document in every generated backend
    app.openapi = lambda: _doc
    app.add_middleware(CORSMiddleware, allow_origins=cfg.cors_origins, allow_methods=["GET", "POST", "PUT", "DELETE"],
                       allow_headers=["Content-Type", "Authorization"], allow_credentials=False)

    if schema.SCHEMA["integrations"]["cache"] or schema.SCHEMA["integrations"]["ws"]:
        from .live import install
        install(app)                                  # installed first, so it sits inside the rate limiter and security headers

    @app.middleware("http")
    async def basics(request: Request, call_next):
        if request.url.path.startswith("/api"):
            try:
                API_LIMIT.enforce(client_ip(request))
            except ApiError as e:
                return JSONResponse(e.body(), status_code=e.status)
            if int(request.headers.get("content-length") or 0) > (cfg.upload_max_bytes if request.url.path == "/api/uploads" else MAX_BODY):
                return _json(413, "payload_too_large", "Request body is too large")
        res = await call_next(request)
        res.headers.update({"X-Content-Type-Options": "nosniff", "X-Frame-Options": "DENY", "Referrer-Policy": "no-referrer"})
        if request.url.path.startswith("/api"):
            res.headers["Cache-Control"] = "no-store"
        return res

    @app.exception_handler(ApiError)
    async def _api_error(request: Request, e: ApiError):
        return JSONResponse(e.body(), status_code=e.status)

    @app.exception_handler(RequestValidationError)
    async def _bad_request(request: Request, e: RequestValidationError):
        errs = e.errors()
        if any(x.get("type") == "json_invalid" for x in errs):
            return _json(400, "invalid_json", "Request body is not valid JSON")
        return _json(400, "validation_failed", "Invalid input", {".".join(str(p) for p in x["loc"][1:]) or "body": x["msg"] for x in errs})

    @app.exception_handler(HttpException)
    async def _http_error(request: Request, e: HttpException):
        code = {404: "not_found", 405: "method_not_allowed"}.get(e.status_code, "http_error")
        return _json(e.status_code, code, "Route not found" if e.status_code == 404 else str(e.detail))

    @app.exception_handler(Exception)
    async def _unexpected(request: Request, e: Exception):
        log.error("%s %s failed: %s", request.method, request.url.path, e, exc_info=True)  # details stay in the log, never in the response
        return _json(500, "internal_error", "Something went wrong")

    @app.get("/api/health", tags=["health"], summary="Liveness and database check")
    def health():
        try:
            if app.state.db:
                app.state.db.ping()
        except Exception:  # noqa: BLE001  any driver error means "down"
            return JSONResponse({"status": "degraded", "db": "down"}, status_code=503)
        extra = {}
        if schema.SCHEMA["integrations"]["cache"]:
            from . import cache
            extra["cache"] = cache.backend()
        return {"status": "ok", **({"db": "up"} if app.state.db else {}), **extra}

    if schema.SCHEMA["auth"]:
        from .routes import auth
        app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
    if schema.SCHEMA["db"]:
        from .routes import crud
        app.include_router(crud.router, prefix="/api")
    if schema.SCHEMA["integrations"]["uploads"]:
        from .routes import uploads
        app.include_router(uploads.router, prefix="/api/uploads", tags=["uploads"])
    if schema.SCHEMA["checkout"]:
        from .routes import checkout
        app.include_router(checkout.router, prefix="/api/checkout", tags=["checkout"])
    if schema.SCHEMA["integrations"]["payments"]:
        from .routes import payments
        app.include_router(payments.router, prefix="/api/payments", tags=["payments"])
    return app

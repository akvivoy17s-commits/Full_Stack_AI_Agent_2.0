"""Django settings. Everything comes from environment variables (see .env.example); no secret lives in this file.
This is a JSON API: no sessions, no admin site, no templates and no cookies, so there is no CSRF surface (clients send a bearer token)."""
import hashlib
import os
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from . import schema
from .config import cfg

BASE_DIR = Path(__file__).resolve().parent.parent
cfg.validate()

DEBUG = False   # never enable: the technical error page would leak settings and source code
# Nothing in this project uses Django's signing, sessions or CSRF; the key is derived so that no extra secret has to be configured.
SECRET_KEY = hashlib.sha256(("django-unused:" + cfg.jwt_secret).encode()).hexdigest()
ALLOWED_HOSTS = [h.strip() for h in os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1,[::1]").split(",") if h.strip()]
if cfg.env == "test":
    ALLOWED_HOSTS.append("testserver")

INSTALLED_APPS = ["app.apps.ApiConfig"] if schema.SCHEMA["db"] else []
MIDDLEWARE = ["app.middleware.ApiMiddleware"] + (["app.live.LiveMiddleware"] if schema.SCHEMA["integrations"]["cache"] else [])
ROOT_URLCONF = "app.urls"
WSGI_APPLICATION = "app.wsgi.application"
DEFAULT_AUTO_FIELD = "django.db.models.AutoField"
APPEND_SLASH = False
USE_TZ = False            # datetimes are stored as naive UTC in every database, like the other generated backends
TIME_ZONE = "UTC"
DATA_UPLOAD_MAX_MEMORY_SIZE = max(100 * 1024, cfg.upload_max_bytes) if schema.SCHEMA["integrations"]["uploads"] else 100 * 1024   # larger bodies are answered with 413 (middleware keeps 100 kB for every route but /api/uploads)


def _database() -> dict:
    db = schema.SCHEMA["db"]
    url = cfg.database_url
    if db == "sqlite":
        if not url.startswith("sqlite:///"):
            raise RuntimeError("DATABASE_URL for SQLite must look like sqlite:///./app.db")
        path = url[len("sqlite:///"):]
        return {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:" if path == ":memory:" else str(Path(path))}
    u = urlparse(url)
    scheme = u.scheme.split("+")[0]
    name, host, port = unquote(u.path.lstrip("/")), u.hostname or "", str(u.port or "")
    base = {"NAME": name, "USER": unquote(u.username or ""), "PASSWORD": unquote(u.password or ""), "HOST": host, "PORT": port,
            "CONN_MAX_AGE": 60, "CONN_HEALTH_CHECKS": True}
    if db == "postgresql" and scheme in ("postgres", "postgresql"):
        opts = {}
        if cfg.database_ssl or parse_qs(u.query).get("sslmode") == ["require"]:
            opts["sslmode"] = "require"
        return {"ENGINE": "django.db.backends.postgresql", **base, "OPTIONS": opts}
    if db == "mssql" and scheme in ("mssql", "sqlserver"):
        opts = {"driver": os.environ.get("MSSQL_ODBC_DRIVER", "ODBC Driver 18 for SQL Server")}
        if not cfg.database_ssl:
            opts["extra_params"] = "TrustServerCertificate=yes"      # local/dev servers use self-signed certificates
        return {"ENGINE": "mssql", **base, "OPTIONS": opts}
    if db == "mysql" and scheme == "mysql":
        import pymysql
        pymysql.version_info = (2, 2, 1, "final", 0)   # Django checks the mysqlclient version; PyMySQL (pure Python) answers for it
        pymysql.install_as_MySQLdb()
        return {"ENGINE": "django.db.backends.mysql", **base, "OPTIONS": {"charset": "utf8mb4"}}
    raise RuntimeError(f"DATABASE_URL does not match the generated database ({db})")


DATABASES = {"default": _database()} if schema.SCHEMA["db"] else {}

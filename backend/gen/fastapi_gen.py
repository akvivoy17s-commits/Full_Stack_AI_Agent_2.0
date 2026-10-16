"""FastAPI (Python) generator. Static code comes from templates/python (framework-neutral core, shared with Flask)
and templates/fastapi (web layer); only schema.py and the manifests are built here."""
import json
import pprint
from pathlib import Path

from backend.gen import model as M
from backend.gen import openapi

ROOT = Path(__file__).parent / "templates"
ROOTS = (ROOT / "python", ROOT / "fastapi")
DRIVER = {"sqlite": [], "postgresql": ["psycopg[binary]>=3.2,<4"], "mysql": ["PyMySQL>=1.1,<2"], "mssql": ["pymssql>=2.3,<3"]}
BASE = ["fastapi>=0.115,<1", "uvicorn[standard]>=0.30,<1", "python-dotenv>=1.0,<2"]
LABEL = "FastAPI"
# Template names that pytest must not collect while it scans this repository; they get their real names in the generated project.
RENAME = {"tests/_test_api.py": "tests/test_api.py", "tests/_conftest.py": "tests/conftest.py"}
VENV = "python -m venv .venv && source .venv/bin/activate   # Windows: .venv\\Scripts\\activate"


def I_pay(m: dict) -> bool:
    return bool(m["integrations"]["payments"])


def schema_py(m: dict, spec: dict) -> str:
    body = {"title": spec.get("purpose", "App")[:80], "db": m["db"], "auth": m["auth"], "refresh": m["auth"] and m["refresh"], "roles": m["roles"],
            "adminRole": m["adminRole"], "defaultRole": m["defaultRole"], "entities": {e["name"]: e for e in m["entities"]}, "seed": m["seed"], "integrations": m["integrations"], "checkout": bool(m.get("checkout"))}
    return ("# Generated from the app spec (entities, fields, access rules). Single source of truth for validation, routes and tests.\n"
            "SCHEMA = " + pprint.pformat(body, width=110, sort_dicts=False) + "\n")


ALEMBIC_INI = "[alembic]\nscript_location = migrations\n"

ALEMBIC_ENV = '''"""Alembic environment. `python -m scripts.migrate` (and AUTO_MIGRATE) apply the migrations through the app's own connection.
CLI: alembic upgrade head  |  alembic revision --autogenerate -m "describe the change"  |  alembic upgrade head --sql  (prints the SQL, no database needed)"""
from alembic import context

from app.config import cfg
from app.db import sql

config = context.config
if context.is_offline_mode():
    context.configure(url=cfg.sql_url, target_metadata=sql.metadata, literal_binds=True, dialect_opts={"paramstyle": "named"})
    with context.begin_transaction():
        context.run_migrations()
else:
    connection = config.attributes.get("connection")
    own = connection is None
    if own:
        connection = sql.connect().engine.connect()
    context.configure(connection=connection, target_metadata=sql.metadata)
    with context.begin_transaction():
        context.run_migrations()
    if own:
        connection.commit()
        connection.close()
'''

ALEMBIC_MAKO = '''"""${message}"""
from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

revision = ${repr(up_revision)}
down_revision = ${repr(down_revision)}
branch_labels = None
depends_on = None


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}
'''


def _sa_type(f: dict, db: str) -> str:
    t = f["type"]
    if t in ("ref", "int"):
        return "sa.Integer()"
    if t in ("string", "email"):
        return "sa.String(255)"
    if t == "enum":
        return "sa.String(64)"
    if t == "url":
        return "sa.String(2048)"
    if t == "text":
        return {"mysql": "mysql.MEDIUMTEXT()", "mssql": 'mssql.NVARCHAR("max")'}.get(db, "sa.Text()")
    if t == "float":
        return "sa.Float(53)"
    if t == "bool":
        return "sa.Boolean()"
    return "mssql.DATETIME2()" if db == "mssql" else "sa.DateTime()"


def initial_migration(m: dict) -> str:
    """The first Alembic revision, written out in full (not derived from the models at run time), so later model edits never change it."""
    db, ups, idx, downs = m["db"], [], [], []
    table_of = {e["name"]: e["table"] for e in m["entities"]}
    for e in m["entities"]:
        cols = ['sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True)']
        extra = []
        for f in e["fields"]:
            args = [json.dumps(f["name"]), _sa_type(f, db)]
            if f["type"] == "ref" and f.get("fk"):
                args.append(f'sa.ForeignKey("{table_of[f["ref"]]}.id", ondelete={json.dumps(f["onDelete"])})')
            args.append(f"nullable={not f['required']}")
            filtered = db == "mssql" and f["unique"] and not f["required"]    # SQL Server: one NULL per unique index -> filtered unique index instead
            if f["unique"] and not filtered:
                args.append("unique=True")
            cols.append(f"sa.Column({', '.join(args)})")
            if filtered:
                idx.append(f'    op.create_index("uq_{e["table"]}_{f["name"]}", "{e["table"]}", ["{f["name"]}"], unique=True, mssql_where=sa.text("[{f["name"]}] IS NOT NULL"))')
            elif f.get("index"):
                idx.append(f'    op.create_index("ix_{e["table"]}_{f["name"]}", "{e["table"]}", ["{f["name"]}"])')
        ups.append(f'    op.create_table(\n        "{e["table"]}",\n        ' + ",\n        ".join(cols) + ",\n    )")
        downs.append(f'    op.drop_table("{e["table"]}")')
    head = "from alembic import op\nimport sqlalchemy as sa\n" + {"mysql": "from sqlalchemy.dialects import mysql\n", "mssql": "from sqlalchemy.dialects import mssql\n"}.get(db, "")
    return ('"""Initial schema (generated from the app spec). Edit later changes into NEW revisions: alembic revision --autogenerate -m "..." """\n' + head +
            '\nrevision = "0001"\ndown_revision = None\nbranch_labels = None\ndepends_on = None\n\n\ndef upgrade() -> None:\n' + "\n".join(ups) + "\n" + "\n".join(idx)
            + "\n\n\ndef downgrade() -> None:\n" + "\n".join(reversed(downs)) + "\n")


def alembic_files(m: dict) -> dict[str, str]:
    return {"backend/alembic.ini": ALEMBIC_INI, "backend/migrations/env.py": ALEMBIC_ENV, "backend/migrations/script.py.mako": ALEMBIC_MAKO,
            "backend/migrations/versions/0001_initial.py": initial_migration(m)}


def requirements(m: dict, dev: bool = False, base: list[str] | None = None) -> str:
    req = list(base or BASE)
    if m["sql"]:
        req += ["sqlalchemy>=2.0.30,<3", "alembic>=1.13,<2"] + DRIVER[m["db"]]
    elif m["db"] == "mongodb":
        req.append("pymongo>=4.8,<5")
    if m["integrations"]["cache"]:
        req.append("redis>=5,<6")
    if m["auth"]:
        req += ["PyJWT>=2.8,<3", "bcrypt>=4.1,<6"]
    if m["integrations"]["uploads"] and m.get("storage") == "firebase-storage":
        req.append("firebase-admin>=6.5,<7")
    return "\n".join((["-r requirements.txt", "pytest>=8,<9", "httpx>=0.27,<1"] if dev else req)) + "\n"


def commands(m: dict) -> dict:
    steps = ["cd backend", VENV.split("   #")[0], "pip install -r requirements-dev.txt", "cp .env.example .env"]
    steps += ["python -m scripts.seed_admin"] if m["auth"] else (["python -m scripts.migrate"] if m["db"] else [])
    return {"run": " && ".join(steps + ["python -m app"]), "test": "cd backend && python -m pytest"}


def env_lines(spec: dict, m: dict) -> list[str]:
    more = {"APP_ENV": ("Runtime mode: development (auto-reload) or production", "development"),
            "HOST": ("Interface to listen on (use 0.0.0.0 in containers)", "127.0.0.1")}
    I = m["integrations"]
    if I["cache"]:
        more["CACHE_TTL_SECONDS"] = ("Seconds a cached read stays valid (any write invalidates all cached reads)", "30")
    if I["uploads"]:
        more["UPLOAD_MAX_BYTES"] = ("Maximum upload size in bytes", "5242880")
        if m.get("storage") == "firebase-storage":
            more.update(M.FB_STORAGE_ENV)
    if I["payments"]:
        more[M.PAY_CUR[m.get("paymentProvider") or "stripe"][0]] = ("Three-letter ISO currency for payments", M.PAY_CUR[m.get("paymentProvider") or "stripe"][1])
    if I["ws"]:
        more["WS_MAX_CLIENTS"] = ("Maximum simultaneous WebSocket clients", "500")
    if m["db"] == "postgresql":
        more["DATABASE_SSL"] = ("Set to true to require SSL for PostgreSQL", "false")
    return M.env_lines(spec, m, {}, {"seed": "python -m scripts.seed_admin", "migrate": "python -m scripts.migrate"}, more)


def readme(m: dict, spec: dict, label: str = LABEL) -> str:
    db = {"sqlite": "SQLite (file)", "postgresql": "PostgreSQL", "mysql": "MySQL", "mssql": "SQL Server", "mongodb": "MongoDB", None: "none"}[m["db"]]
    steps = ["cd backend", VENV, "pip install -r requirements-dev.txt", "cp .env.example .env   # then edit the values"]
    if m["auth"]:
        steps.append("python -m scripts.seed_admin   # creates the tables and the first admin from ADMIN_EMAIL / ADMIN_PASSWORD")
    elif m["sql"]:
        steps.append("python -m scripts.migrate      # optional in development when AUTO_MIGRATE=true")
    steps += ["python -m app          # http://127.0.0.1:8000  ·  API docs: /api/docs", "python -m pytest"]
    I = m["integrations"]
    integ = "".join(f"- {t}\n" for k, t in (
        ("cache", "Cache: GET reads of CRUD resources are cached per caller (`X-Cache: HIT|MISS`, `CACHE_TTL_SECONDS`); any successful write invalidates all cached reads. Redis when `REDIS_URL` is reachable, otherwise in-memory."),
        ("uploads", "Uploads: `POST /api/uploads` with the raw file as the body (PNG/JPEG/GIF/WebP/PDF, type checked from file bytes, `UPLOAD_MAX_BYTES`); `GET /api/uploads/{name}`. " + M.UPLOAD_README[m.get("storage") or "local"]),
        ("checkout", "Checkout: `POST /api/checkout {items:[{productId, quantity}]}` creates a pending order in one transaction; prices and stock are read from the database (never from the client), stock is decremented with a conditional update so concurrent orders cannot oversell."),
        ("payments", M.PAY_README[m.get("paymentProvider") or "stripe"]),
        ("ws", "WebSocket `/ws`: send `{\"type\":\"auth\",\"token\":\"<access token>\"}` first; the server then pushes `{type:\"change\", entity, op}` after writes. Refetch over the REST API.")) if (m.get("checkout") if k == "checkout" else I[k]))
    integ = "## Integrations\n" + integ + "\n" if integ else ""
    routes = "\n".join(f"- `{r}`" for r in m["manifest"])
    notes = "\n".join(f"- {n}" for n in m["warnings"] + [f"Not generated yet: {x}." for x in m["not_generated"]]) or "- none"
    auth = (f"- Sign-up always creates role `{m['defaultRole']}`; admins come from `python -m scripts.seed_admin`.\n- Access token (HS256, short lived) + single-use rotating refresh token (stored hashed).\n"
            "- Responses: `{user, accessToken, refreshToken, tokenType, expiresIn}`.") if m["auth"] else "- No authentication in this app."
    extra = "  Tests for PostgreSQL / MySQL / MongoDB need `TEST_DATABASE_URL` pointing at a disposable database." if m["db"] and m["db"] != "sqlite" else ""
    schema_note = ("Schema changes are Alembic migrations in `migrations/versions/` (the first one is generated; `python -m scripts.migrate` and AUTO_MIGRATE apply them). After editing the spec or the models: `alembic revision --autogenerate -m \"change\"` then `alembic upgrade head`. Sample data: `python -m scripts.seed_sample`."
                   if m["sql"] else "Indexes are created on startup." if m["db"] == "mongodb" else "")
    return f"""# {spec['purpose'][:80]} - API

{label} + {db}. Generated from the app spec; routes, validation and tests follow `app/schema.py`. Python 3.11 or newer.

## Run
```bash
{chr(10).join(steps)}
```
Health check: `GET /api/health`.{extra}
{schema_note}

## Layout
`app/service.py` + `app/auth_service.py` hold the rules (access control, validation, tokens) and know nothing about the web framework; `app/routes/` only maps HTTP onto them; `app/db/` is the data layer.

## Routes
{routes}

Lists accept `?page`, `?limit` (max 100), `?q` and exact filters on reference / enum / boolean fields, and return `{{data, page, limit, total}}`.
Errors are always `{{error: {{code, message, details?}}}}`.

## Security
{auth}
- Authorization is enforced on the server for every route (public / user / owner / admin). Other users' records return 404.
- Explicit CORS origins (`CORS_ORIGINS`), security headers, requests that declare more than 100 kB are rejected, rate limits (in memory, per process) on auth and public forms, no stack traces in responses.
- Unknown fields are rejected; every value is type-checked; queries are parameterised.
- Secrets live in `.env` only (never commit it). Put the API behind HTTPS in production, set `TRUST_PROXY` to the number of proxies in front of it, and limit request body size at the proxy too.

{integ}## Notes
{notes}
"""


def add_remote_storage(files: dict, m: dict) -> None:
    """storage=s3 / firebase-storage: uploads_core.py is replaced by the private-bucket version and the matching store is shipped as storage_remote.py."""
    st = m.get("storage")
    if m["integrations"]["uploads"] and st in ("s3", "firebase-storage"):
        src = "storage_s3.py" if st == "s3" else "storage_firebase.py"
        files["backend/app/uploads_core.py"] = (ROOT / "python" / "app" / "uploads_remote.py").read_text(encoding="utf-8")
        files["backend/app/storage_remote.py"] = (ROOT / "python" / "app" / src).read_text(encoding="utf-8")


def _skip(rel: str, m: dict) -> bool:
    if rel == "app/db/sql.py":
        return not m["sql"]
    if rel == "app/db/mongo.py":
        return m["db"] != "mongodb"
    if rel in ("app/db/__init__.py", "app/service.py", "app/validation.py", "app/routes/crud.py", "scripts/migrate.py", "scripts/seed_sample.py"):
        return not m["db"]
    I = m["integrations"]
    if rel in ("app/cache.py",):
        return not (I["cache"] or I["ws"])        # live.py imports it
    if rel in ("app/live_core.py",):
        return not (I["cache"] or I["ws"])
    if rel in ("app/checkout_core.py", "app/routes/checkout.py"):
        return not m.get("checkout")
    if rel in ("app/payments_core.py", "app/pay_shared.py", "app/routes/payments.py"):
        return not I["payments"]
    if rel in ("app/payments_razorpay.py", "app/payments_paypal.py"):
        return True                                          # copied over payments_core.py by generate() for that provider
    if rel in ("app/uploads_core.py", "app/routes/uploads.py"):
        return not I["uploads"]
    if rel in ("app/uploads_remote.py", "app/storage_s3.py", "app/storage_firebase.py"):
        return True                                          # copied by generate() for storage=s3 / firebase-storage
    if rel == "app/live.py":
        return not (I["cache"] or I["ws"])
    if rel in ("app/auth_service.py", "app/security.py", "app/routes/auth.py", "scripts/seed_admin.py"):
        return not m["auth"]
    return False


def generate(spec: dict, stack: dict, m: dict, key: str = "fastapi", roots: tuple = ROOTS, base: list[str] | None = None, label: str = LABEL) -> dict[str, str]:
    files = {}
    for root in roots:
        for p in sorted(root.rglob("*.py")):
            rel = p.relative_to(root).as_posix()
            if "__pycache__" not in rel and not _skip(rel, m):
                files[f"backend/{RENAME.get(rel, rel)}"] = p.read_text(encoding="utf-8")
    files["backend/scripts/__init__.py"] = ""
    if m["sql"]:
        files.update(alembic_files(m))
    files["backend/app/schema.py"] = schema_py(m, spec)
    if I_pay(m) and (m.get("paymentProvider") or "stripe") != "stripe":
        files["backend/app/payments_core.py"] = (ROOT / "python" / "app" / f"payments_{m['paymentProvider']}.py").read_text(encoding="utf-8")
    add_remote_storage(files, m)
    files["backend/openapi.json"] = openapi.dumps(m, spec)
    files["backend/requirements.txt"] = requirements(m, base=base)
    files["backend/requirements-dev.txt"] = requirements(m, dev=True)
    files["backend/pytest.ini"] = "[pytest]\ntestpaths = tests\npythonpath = .\n"
    files["backend/.env.example"] = "\n".join(env_lines(spec, m)) + "\n"
    files["backend/.gitignore"] = ".venv\n__pycache__\n.env\n*.db\n.pytest_cache\n"
    files["backend/README.md"] = readme(m, spec, label)
    files["backend/.agent-manifest.json"] = json.dumps({"generator": key, "db": m["db"], "routes": m["manifest"]}, indent=1) + "\n"
    if not m["db"]:
        files.pop("backend/scripts/__init__.py")
    return files

"""Django (Python) generator. The framework-neutral core (templates/python: validation, service, auth_service, security, ratelimit)
is shared with FastAPI and Flask; templates/django is the web layer + the Django ORM adapter. Built here: schema.py, models.py,
migrations/0001_initial.py (both from the same field definitions), requirements, .env.example, README."""
import json
import keyword
import re

from backend.gen import fastapi_gen as F
from backend.gen import model as M
from backend.gen import openapi

ROOTS = (F.ROOT / "python", F.ROOT / "django")
DJANGO = "Django>=5.2,<6"
BASE = [DJANGO, "waitress>=3.0,<4", "python-dotenv>=1.0,<2"]
DRIVER = {"sqlite": [], "postgresql": ["psycopg[binary]>=3.2,<4"], "mysql": ["PyMySQL>=1.1,<2"], "mssql": ["mssql-django>=1.5,<2", "pyodbc>=5,<6"]}
LABEL = "Django"
# Names a model field must not take (they are attributes of django.db.models.Model); such API fields get an `f_` attribute and keep their column name.
RESERVED = {"objects", "pk", "id", "save", "delete", "clean", "full_clean", "check", "refresh_from_db", "serializable_value", "validate_unique",
            "validate_constraints", "get_deferred_fields", "from_db", "asave", "adelete", "arefresh_from_db", "prepare_database_save", "unique_error_message",
            "date_error_message", "DoesNotExist", "MultipleObjectsReturned", "Meta", "clean_fields", "get_constraints", "get_field", "pre_save"}
commands = F.commands


def _attr(name: str) -> str:
    bad = name in RESERVED or keyword.iskeyword(name) or name.endswith("_") or "__" in name or name[0].isdigit() or name.startswith("get_")
    return "f_" + re.sub(r"_+", "_", name).strip("_") if bad else name


def _stem(name: str) -> str:
    return name[:-3] if name.endswith("_id") and len(name) > 3 else name


def _fk(f: dict) -> bool:
    return f["type"] == "ref" and bool(f.get("fk"))


def attr(f: dict) -> str:
    """Name of the model attribute holding the value of API field `f` (a foreign key's value lives in `<field>_id`)."""
    return _attr(_stem(f["name"])) + "_id" if _fk(f) else _attr(f["name"])


def field_src(e: dict, f: dict, ents: dict) -> str:
    """Source of one Django field. Used by models.py AND the migration, so the two cannot drift apart."""
    t, kw = f["type"], []
    if _fk(f):
        on = "CASCADE" if e["internal"] else "PROTECT" if f["required"] else "SET_NULL"
        kw = [f'to="app.{ents[f["ref"]]["name"]}"', f"on_delete=models.{on}", 'related_name="+"']
        cls = "ForeignKey"
    else:
        cls = {"string": "CharField", "enum": "CharField", "email": "CharField", "url": "CharField", "text": "TextField", "int": "IntegerField", "ref": "IntegerField",
               "float": "FloatField", "bool": "BooleanField", "datetime": "DateTimeField"}[t]
        mx = {"string": 255, "enum": 64, "email": 255, "url": 2048}.get(t)
        if mx:
            kw.append(f"max_length={mx}")
        if f.get("index"):
            kw.append("db_index=True")
    if not f["required"]:
        kw.append("null=True")
    if f["unique"]:
        kw.append("unique=True")
    if _fk(f) or attr(f) != f["name"]:          # the column keeps the API name (a foreign key `course_id` lives in field `course`)
        kw.append(f'db_column="{f["name"]}"')
    return f"models.{cls}({', '.join(kw)})"


def _fields(e: dict, ents: dict) -> list[tuple[str, str]]:
    return [(_attr(_stem(f["name"])) if _fk(f) else attr(f), field_src(e, f, ents)) for f in e["fields"]]


def models_py(m: dict) -> str:
    ents = {e["name"]: e for e in m["entities"]}
    out = ["# Generated from the app spec (app/schema.py). Field kinds, constraints and column names match the other generated backends.",
           "from django.db import models", ""]
    for e in m["entities"]:
        out += ["", f"class {e['name']}(models.Model):"]
        out += [f"    {n} = {src}" for n, src in _fields(e, ents)] or ["    pass"]
        out += ["", "    class Meta:", f'        db_table = "{e["table"]}"', ""]
    keys = {e["name"]: {f["name"]: attr(f) for f in e["fields"]} for e in m["entities"]}
    out += ["", "# API field name -> model attribute (used by app/db/django_orm.py)", "KEYS = " + json.dumps(keys, indent=2)]
    return "\n".join(out) + "\n"


def migration_py(m: dict) -> str:
    ents, ops = {e["name"]: e for e in m["entities"]}, []
    for e in m["entities"]:       # parents first (model.build sorts them), so every foreign key points at an existing table
        cols = ['("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID"))']
        cols += [f'("{n}", {src})' for n, src in _fields(e, ents)]
        ops.append(f'        migrations.CreateModel(\n            name="{e["name"]}",\n            fields=[\n                ' + ",\n                ".join(cols)
                   + f',\n            ],\n            options={{"db_table": "{e["table"]}"}},\n        ),')
    return ("# Generated from the app spec. Applied with `python -m scripts.migrate` (or `python manage.py migrate`).\n"
            "# Once this has run against a real database, change models.py and use `python manage.py makemigrations` instead of regenerating this file.\n"
            "from django.db import migrations, models\n\n\nclass Migration(migrations.Migration):\n    initial = True\n    dependencies = []\n    operations = [\n"
            + "\n".join(ops) + "\n    ]\n")


def requirements(m: dict, dev: bool = False) -> str:
    if dev:
        return "-r requirements.txt\npytest>=8,<9\n"
    req = list(BASE) + DRIVER.get(m["db"], []) + (["redis>=5,<6"] if m["integrations"]["cache"] else [])
    if m["auth"]:
        req += ["PyJWT>=2.8,<3", "bcrypt>=4.1,<6"]
    if m["integrations"]["uploads"] and m.get("storage") == "firebase-storage":
        req.append("firebase-admin>=6.5,<7")
    return "\n".join(req) + "\n"


def env_lines(spec: dict, m: dict) -> list[str]:
    more = {"APP_ENV": ("Runtime mode: development (auto-reload) or production", "development"),
            "HOST": ("Interface to listen on (use 0.0.0.0 in containers)", "127.0.0.1"),
            "ALLOWED_HOSTS": ("Host names this API is served under (comma separated); other Host headers are rejected", "localhost,127.0.0.1")}
    more.update(M.integ_env(m))
    if m["db"] == "postgresql":
        more["DATABASE_SSL"] = ("Set to true to require SSL for PostgreSQL", "false")
    return M.env_lines(spec, m, {}, {"seed": "python -m scripts.seed_admin", "migrate": "python -m scripts.migrate"}, more)


def readme(m: dict, spec: dict) -> str:
    db = {"sqlite": "SQLite (file)", "postgresql": "PostgreSQL", "mysql": "MySQL", "mssql": "SQL Server", None: "none"}[m["db"]]
    steps = ["cd backend", F.VENV, "pip install -r requirements-dev.txt", "cp .env.example .env   # then edit the values"]
    if m["auth"]:
        steps.append("python -m scripts.seed_admin   # applies the migrations and creates the first admin from ADMIN_EMAIL / ADMIN_PASSWORD")
    elif m["db"]:
        steps.append("python -m scripts.migrate      # optional in development when AUTO_MIGRATE=true")
    steps += ["python -m app          # http://127.0.0.1:8000  ·  route reference: /api/docs", "python -m pytest"]
    routes = "\n".join(f"- `{r}`" for r in m["manifest"])
    notes = "\n".join(f"- {n}" for n in m["warnings"] + [f"Not generated yet: {x}." for x in m["not_generated"]]) or "- none"
    auth = (f"- Sign-up always creates role `{m['defaultRole']}`; admins come from `python -m scripts.seed_admin`.\n- Access token (HS256, short lived) + single-use rotating refresh token (stored hashed).\n"
            "- Responses: `{user, accessToken, refreshToken, tokenType, expiresIn}`.") if m["auth"] else "- No authentication in this app."
    extra = "  Tests for PostgreSQL / MySQL need `TEST_DATABASE_URL` pointing at a disposable database." if m["db"] in ("postgresql", "mysql") else ""
    schema_note = ("Models are in `app/models.py` and the first migration in `app/migrations/0001_initial.py`, both generated from the spec. Once the migration has been applied to a real database, "
                   "change `models.py` and run `python manage.py makemigrations && python manage.py migrate`; regenerating the project would rewrite `0001` only while you have not edited it.") if m["db"] else ""
    return f"""# {spec['purpose'][:80]} - API

Django + {db}. Generated from the app spec; routes, validation and tests follow `app/schema.py`. Python 3.11 or newer.

## Run
```bash
{chr(10).join(steps)}
```
Health check: `GET /api/health`. Django commands: `python manage.py check | migrate | makemigrations`.{extra}
{schema_note}

## Layout
`app/service.py` + `app/auth_service.py` hold the rules (access control, validation, tokens) and know nothing about Django; `app/views.py` + `app/urls.py` only map HTTP onto them; `app/db/django_orm.py` is the data layer (Django ORM); `app/middleware.py` handles hosts, CORS, rate limits, security headers and the error envelope.

## Routes
{routes}

Lists accept `?page`, `?limit` (max 100), `?q` and exact filters on reference / enum / boolean fields, and return `{{data, page, limit, total}}`.
Errors are always `{{error: {{code, message, details?}}}}`.

## Security
{auth}
- Authorization is enforced on the server for every route (public / user / owner / admin). Other users' records return 404.
- `DEBUG` is off and cannot be switched on from the environment; `ALLOWED_HOSTS` is checked on every request; explicit CORS origins (`CORS_ORIGINS`); security headers; requests that declare more than 100 kB are rejected; rate limits (in memory, per process) on auth and public forms; no stack traces in responses.
- No sessions or cookies, so Django's CSRF protection is not needed (clients send a bearer token). Django's admin site is not generated.
- Unknown fields are rejected; every value is type-checked; queries go through the ORM (parameterised).
- Secrets live in `.env` only (never commit it). Put the API behind HTTPS in production, set `TRUST_PROXY` to the number of proxies in front of it, and limit request body size at the proxy too.

{M.integ_readme(m)}## Notes
{notes}
"""


def _skip(rel: str, m: dict) -> bool:
    if rel in ("app/db/sql.py", "app/db/mongo.py"):
        return True
    if rel in ("app/db/__init__.py", "app/db/django_orm.py", "app/service.py", "app/validation.py", "scripts/migrate.py", "scripts/seed_sample.py"):
        return not m["db"]
    I = m["integrations"]
    if rel == "app/cache.py":
        return not I["cache"]
    if rel in ("app/live.py", "app/live_core.py"):
        return not I["cache"]
    if rel in ("app/uploads_core.py", "app/uploads_views.py"):
        return not I["uploads"]
    if rel in ("app/uploads_remote.py", "app/storage_s3.py", "app/storage_firebase.py"):
        return True                                          # copied by generate() for storage=s3 / firebase-storage
    if rel in ("app/checkout_core.py", "app/checkout_views.py"):
        return not m.get("checkout")
    if rel in ("app/payments_core.py", "app/pay_shared.py", "app/payments_views.py"):
        return not I["payments"]
    if rel in ("app/payments_razorpay.py", "app/payments_paypal.py"):
        return True                                          # copied over payments_core.py by generate() for that provider
    if rel in ("app/auth_service.py", "app/security.py", "scripts/seed_admin.py"):
        return not m["auth"]
    return False


def generate(spec: dict, stack: dict, m: dict) -> dict[str, str]:
    files = {}
    for root in ROOTS:          # later roots win: templates/django/app/db/__init__.py replaces the core's SQLAlchemy / MongoDB switch
        for p in sorted(root.rglob("*.py")):
            rel = p.relative_to(root).as_posix()
            if "__pycache__" not in rel and not _skip(rel, m):
                files[f"backend/{F.RENAME.get(rel, rel)}"] = p.read_text(encoding="utf-8")
    files["backend/app/schema.py"] = F.schema_py(m, spec)
    if m["db"]:
        files["backend/app/models.py"] = models_py(m)
        files["backend/app/migrations/__init__.py"] = ""
        files["backend/app/migrations/0001_initial.py"] = migration_py(m)
        files["backend/scripts/__init__.py"] = ""
    if m["integrations"]["payments"] and (m.get("paymentProvider") or "stripe") != "stripe":
        files["backend/app/payments_core.py"] = (F.ROOT / "python" / "app" / f"payments_{m['paymentProvider']}.py").read_text(encoding="utf-8")
    F.add_remote_storage(files, m)
    files["backend/requirements.txt"] = requirements(m)
    files["backend/requirements-dev.txt"] = requirements(m, dev=True)
    files["backend/pytest.ini"] = "[pytest]\ntestpaths = tests\npythonpath = .\n"
    files["backend/.env.example"] = "\n".join(env_lines(spec, m)) + "\n"
    files["backend/.gitignore"] = ".venv\n__pycache__\n.env\n*.db\n.pytest_cache\n"
    files["backend/README.md"] = readme(m, spec)
    files["backend/openapi.json"] = openapi.dumps(m, spec)
    files["backend/.agent-manifest.json"] = json.dumps({"generator": "django", "db": m["db"], "routes": m["manifest"]}, indent=1) + "\n"
    return files

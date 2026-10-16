"""Phase 4 part 2: Django generator (rule based). Django itself is not installed in the build sandbox, so the generated web layer (urls, views,
middleware, deps) runs here against a minimal stand-in for django.http / django.urls, with the SHARED generated test suite (tests/test_api.py)
executed on top of it. models.py and the migration are compared field by field. The Django ORM adapter, `manage.py` and the real
Django test client are NOT executed here: run `python -m pytest` in a generated project."""
import ast
import json
import os
import re
import sys
import types
from urllib.parse import parse_qs

import pytest

from backend.gen import django_gen as D
from backend.gen import model, stage
from backend.spec import compose
from backend.stack import catalog as C
from backend.stack.resolver import resolve
from backend.tools.project_files import ProjectFiles
from gen_helpers import BRIEF, STORE, FakeDb, build, load_project, stack_for, unload

DJ_DBS = ["sqlite", "postgresql", "mysql"]


def dbuild(db, brief=BRIEF, **kw):
    return build(db, brief, backend="django", **kw)


def generate(pid, db, brief=BRIEF, **extra):
    st = stack_for(db, brief, backend="django", **extra)
    spec = compose.build(brief, st)
    pf = ProjectFiles(pid)
    return pf, spec, st, stage.run(pf, spec, st)


# ------------------------------------------------------------------ readiness is per combination
def test_ready_combinations_and_honest_gaps():
    for db in DJ_DBS:
        assert C.generator_gaps(stack_for(db, backend="django")) == [], db
    st = stack_for("sqlite", backend="django")
    assert st["orm"] == "django-orm" and C.status("backend", "django", st) == "ready" and stage.coverage(st)["ready"] is True
    assert C.generator_gaps({**st, "auth": "oauth2"}) and not C.generator_gaps({**st, "cache": "redis"}) and C.generator_gaps({**st, "ai": "python-service"})
    assert C.generator_gaps({**st, "database": "mssql"}) == []                                   # phase 3 of the v2 upgrade: SQL Server is generated
    r = resolve("manual", {"frontend": "react", "frontend_lang": "ts", "backend": "django", "backend_lang": "py", "database": "mongodb"}, BRIEF)
    assert not r["ok"]                                                                       # Django has no first-party MongoDB support: the rules refuse it
    assert C.status("backend", "spring", {"backend": "spring", "database": "sqlite"}) == "ready"   # Spring Boot generator finished in v2 phase 5
    assert C.BACKEND_TESTS["django"] == "pytest"


# ------------------------------------------------------------------ generated project
@pytest.mark.parametrize("db", DJ_DBS)
def test_generates_complete_django_project(db):
    spec, st, m, files = dbuild(db)
    for need in ("manage.py", "requirements.txt", "requirements-dev.txt", "pytest.ini", ".env.example", ".gitignore", "README.md", "app/settings.py", "app/urls.py",
                 "app/views.py", "app/middleware.py", "app/deps.py", "app/wsgi.py", "app/__main__.py", "app/apps.py", "app/models.py", "app/migrations/__init__.py",
                 "app/migrations/0001_initial.py", "app/db/__init__.py", "app/db/django_orm.py", "app/schema.py", "app/service.py", "app/auth_service.py",
                 "app/validation.py", "scripts/seed_admin.py", "scripts/migrate.py", "tests/conftest.py", "tests/test_api.py"):
        assert f"backend/{need}" in files, need
    req = files["backend/requirements.txt"]
    assert "Django>=5.2,<6" in req and "PyJWT" in req and "bcrypt" in req and "waitress" in req and "sqlalchemy" not in req.lower() and "djangorestframework" not in req
    assert ("psycopg" in req) == (db == "postgresql") and ("PyMySQL" in req) == (db == "mysql")
    assert "app/db/sql.py" not in " ".join(files) and "app/db/mongo.py" not in " ".join(files)
    assert "sqlalchemy" not in files["backend/app/db/__init__.py"] and "django_orm" in files["backend/app/db/__init__.py"]
    assert not any(t for rel, t in files.items() if rel.endswith(".py") and re.search(r"^\s*(import|from) (flask|fastapi|sqlalchemy|pymongo)\b", t, re.M))
    assert files["backend/pytest.ini"] == "[pytest]\ntestpaths = tests\npythonpath = .\n" and "pytest" in files["backend/requirements-dev.txt"]
    for rel, text in files.items():
        if rel.endswith(".py"):
            compile(text, rel, "exec")


def test_no_database_means_health_and_docs_only():
    pf, spec, st, out = generate("dj-nodb", "none", "simple landing page")
    tree = set(pf.tree())
    assert out["generated"] and out["generator"] == "django"
    for gone in ("backend/app/models.py", "backend/app/migrations/0001_initial.py", "backend/app/service.py", "backend/app/db/django_orm.py", "backend/app/auth_service.py",
                 "backend/app/validation.py", "backend/scripts/seed_admin.py", "backend/scripts/migrate.py"):
        assert gone not in tree, gone
    assert "PyJWT" not in pf.read("backend/requirements.txt") and "ADMIN_EMAIL" not in pf.read("backend/.env.example")


def test_database_without_auth_has_no_sign_in():
    spec, st, m, files = dbuild("sqlite", "portfolio website with contact form", auth="none")
    assert "backend/app/auth_service.py" not in files and "backend/app/security.py" not in files and "backend/scripts/seed_admin.py" not in files
    assert "PyJWT" not in files["backend/requirements.txt"] and "auth_register" in files["backend/app/views.py"] and "if S[\"auth\"]:" in files["backend/app/urls.py"]


def test_env_example_has_placeholders_only_and_django_variables():
    spec, st, m, files = dbuild("postgresql")
    env = files["backend/.env.example"]
    assert "JWT_SECRET=<generate-a-long-random-string>" in env and "DATABASE_URL=postgresql://user:password@localhost" in env and "ALLOWED_HOSTS=localhost,127.0.0.1" in env
    assert "DATABASE_SSL=false" in env and "VITE_" not in env and ".env\n" in files["backend/.gitignore"]


def test_security_defaults_are_in_the_generated_code():
    spec, st, m, files = dbuild("sqlite")
    s, mw = files["backend/app/settings.py"], files["backend/app/middleware.py"]
    assert "DEBUG = False" in s and "DATA_UPLOAD_MAX_MEMORY_SIZE" in s and "100 * 1024" in s and 'MIDDLEWARE = ["app.middleware.ApiMiddleware"]' in s   # v2 phase 6 appends LiveMiddleware only when cache is on
    assert "CsrfViewMiddleware" not in s and "SessionMiddleware" not in s and "django.contrib" not in s
    assert "request.get_host()" in mw and "cfg.cors_origins" in mw and "nosniff" in mw and "exc_info=exc" in mw
    assert "algorithms=[\"HS256\"]" in files["backend/app/security.py"] and "ProtectedError" in files["backend/app/db/django_orm.py"]
    assert "__icontains" in files["backend/app/db/django_orm.py"] and "hash_password" in files["backend/scripts/seed_admin.py"]


# ------------------------------------------------------------------ models and migration are built from the same definitions
class _F:
    def __init__(self, *a, **k):
        self.cls, self.args, self.kw = type(self).__name__, a, k

    def sig(self):
        return (self.cls, self.args, tuple(sorted(self.kw.items())))


def _fake_models_and_migrations():
    models = types.ModuleType("django.db.models")
    for n in ("CharField", "TextField", "IntegerField", "FloatField", "BooleanField", "DateTimeField", "ForeignKey", "AutoField"):
        setattr(models, n, type(n, (_F,), {}))
    models.CASCADE, models.PROTECT, models.SET_NULL = "CASCADE", "PROTECT", "SET_NULL"
    reg = {}

    class Model:
        def __init_subclass__(cls, **kw):
            reg[cls.__name__] = ([(k, v) for k, v in vars(cls).items() if isinstance(v, _F)], cls.Meta.db_table)
    models.Model = Model
    migs = types.ModuleType("django.db.migrations")
    migs.Migration = type("Migration", (), {})
    migs.CreateModel = type("CreateModel", (), {"__init__": lambda self, name, fields, options: self.__dict__.update(name=name, fields=fields, options=options)})
    db = types.ModuleType("django.db")
    db.models, db.migrations = models, migs
    return {"django": types.ModuleType("django"), "django.db": db, "django.db.models": models, "django.db.migrations": migs}, reg


@pytest.mark.parametrize("brief", [BRIEF, STORE])
def test_models_and_migration_agree(brief):
    spec, st, m, files = dbuild("postgresql", brief)
    mods, reg = _fake_models_and_migrations()
    saved = {k: sys.modules.get(k) for k in mods}
    sys.modules.update(mods)
    try:
        ns, ns2 = {}, {}
        exec(compile(files["backend/app/models.py"], "models.py", "exec"), ns)
        exec(compile(files["backend/app/migrations/0001_initial.py"], "0001.py", "exec"), ns2)
    finally:
        for k, v in saved.items():
            sys.modules.pop(k, None)
            if v is not None:
                sys.modules[k] = v
    ops = ns2["Migration"].operations
    assert [o.name for o in ops] == [e["name"] for e in m["entities"]] == list(reg)                          # parents first, same set
    seen = set()
    for o in ops:
        fields, table = reg[o.name]
        assert o.fields[0][0] == "id" and o.fields[0][1].cls == "AutoField"
        assert [(n, f.sig()) for n, f in o.fields[1:]] == [(n, f.sig()) for n, f in fields] and o.options == {"db_table": table}
        for _n, f in fields:
            if f.cls == "ForeignKey":
                assert f.kw["to"].removeprefix("app.") in seen                                                # the target table exists already
        seen.add(o.name)
    keys = ns["KEYS"]
    ent = {e["name"]: e for e in m["entities"]}
    for name, mp in keys.items():
        assert set(mp) == {f["name"] for f in ent[name]["fields"]}
        for f in ent[name]["fields"]:
            col = next((fl for n, fl in reg[name][0] if n == mp[f["name"]].removesuffix("_id") or n == mp[f["name"]]), None)
            assert col is not None, (name, f["name"])
            if f["type"] == "ref" and f.get("fk"):
                assert col.kw["db_column"] == f["name"] and mp[f["name"]] == f["name"]                       # `course_id` -> field `course`, attribute `course_id`
                assert col.kw["on_delete"] == ("PROTECT" if f["required"] else "SET_NULL") or name == "RefreshToken"
            assert (col.kw.get("null") is True) == (not f["required"]) and (col.kw.get("unique") is True) == bool(f["unique"])


def test_attribute_names_avoid_django_model_clashes():
    f = lambda name, t="string", **kw: {"name": name, "type": t, "required": True, "unique": False, **kw}      # noqa: E731
    assert D.attr(f("title")) == "title" and D.attr(f("save")) == "f_save" and D.attr(f("class")) == "f_class" and D.attr(f("get_x")) == "f_get_x"
    assert D.attr(f("course_id", "ref", fk=True)) == "course_id" and D.attr(f("owner", "ref", fk=True)) == "owner_id" and D.attr(f("tag_id", "ref")) == "tag_id"
    e = {"name": "T", "internal": False}
    assert 'db_column="save"' in D.field_src(e, f("save"), {}) and "db_column" not in D.field_src(e, f("title"), {})
    assert D.field_src({"name": "T", "internal": True}, f("user_id", "ref", fk=True, ref="User"), {"User": {"name": "User"}}).count("CASCADE") == 1


# ------------------------------------------------------------------ the generated web layer, run against a stand-in for django.http / django.urls
class _Exc(Exception):
    pass


class SuspiciousOperation(_Exc):
    pass


class DisallowedHost(SuspiciousOperation):
    pass


class RequestDataTooBig(SuspiciousOperation):
    pass


class PermissionDenied(_Exc):
    pass


class Http404(_Exc):
    pass


class HttpResponse:
    def __init__(self, content=b"", status=200, content_type=None):
        self.status_code, self.content, self.headers = status, content.encode() if isinstance(content, str) else content, {}
        if content_type:
            self.headers["Content-Type"] = content_type

    def __setitem__(self, k, v):
        self.headers[k] = v

    def __getitem__(self, k):
        return self.headers[k]

    def json(self):
        return json.loads(self.content)


class JsonResponse(HttpResponse):
    def __init__(self, data, status=200):
        super().__init__(json.dumps(data), status, "application/json")


class _CI(dict):
    def __init__(self, d):
        super().__init__({k.lower(): v for k, v in d.items()})

    def get(self, k, default=None):
        return super().get(k.lower(), default)

    def __contains__(self, k):
        return super().__contains__(k.lower())


class _Query(dict):
    def lists(self):
        return list(self.items())


class Req:
    def __init__(self, method, url, body=b"", headers=None, host="testserver", too_big=False):
        path, _, qs = url.partition("?")
        self.method, self.path, self._body, self.host, self.too_big = method, path, body, host, too_big
        self.META, self.headers, self.GET = {"REMOTE_ADDR": "10.0.0.7"}, _CI(headers or {}), _Query(parse_qs(qs))

    @property
    def body(self):
        if self.too_big:
            raise RequestDataTooBig()
        return self._body

    def get_host(self):
        if self.host not in ("testserver", "localhost"):
            raise DisallowedHost()
        return self.host


def _fake_django():
    mods = {n: types.ModuleType(n) for n in ("django", "django.core", "django.core.exceptions", "django.http", "django.urls")}
    ex = mods["django.core.exceptions"]
    ex.SuspiciousOperation, ex.DisallowedHost, ex.RequestDataTooBig, ex.PermissionDenied = SuspiciousOperation, DisallowedHost, RequestDataTooBig, PermissionDenied
    mods["django.http"].Http404, mods["django.http"].HttpResponse, mods["django.http"].JsonResponse = Http404, HttpResponse, JsonResponse
    mods["django.urls"].re_path = lambda pattern, view, kwargs=None: (re.compile(pattern), view, kwargs or {})
    return mods


class Web:
    """Loads a generated Django project's web layer and serves requests through its middleware, like Django's handler would."""

    def __init__(self, db="sqlite", brief=STORE, with_db=True, **kw):
        self.saved = {k: sys.modules.get(k) for k in list(sys.modules) if k == "django" or k.startswith("django.")}
        for k in self.saved:
            del sys.modules[k]
        sys.modules.update(_fake_django())
        self.path, self.schema = load_project(db, brief, backend="django", **kw)
        import importlib
        self.urls, self.views = importlib.import_module("app.urls"), importlib.import_module("app.views")
        self.mw, self.deps = importlib.import_module("app.middleware"), importlib.import_module("app.deps")
        self.db = FakeDb(self.schema) if with_db and self.schema["db"] else None
        self.deps._db = self.db
        self.handler = self.mw.ApiMiddleware(self._dispatch)

    def _dispatch(self, request):
        path = request.path.lstrip("/")
        for rx, view, kw in self.urls.urlpatterns:
            hit = rx.match(path)
            if hit:
                try:
                    return view(request, **{**hit.groupdict(), **kw})
                except Exception as exc:  # noqa: BLE001  mirrors Django: view exceptions go to process_exception first
                    res = self.handler.process_exception(request, exc)
                    if res is None:
                        raise
                    return res
        return self.views.not_found(request, Http404())

    def send(self, req):
        return self.handler(req)

    def call(self, method, path, body=None, token=None, raw=None):
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        data = raw if raw is not None else b"" if body is None else json.dumps(body).encode()
        res = self.send(Req(method, path, data, headers))
        try:
            return res.status_code, res.json()
        except ValueError:
            return res.status_code, None

    def close(self):
        unload(self.path)
        for k in [k for k in sys.modules if k == "django" or k.startswith("django.")]:
            del sys.modules[k]
        sys.modules.update({k: v for k, v in self.saved.items() if v is not None})


def _load_generated_tests(web, files):
    ns = {"__name__": "generated_test_api"}
    exec(compile(files["backend/tests/test_api.py"], "test_api.py", "exec"), ns)
    return types.SimpleNamespace(**ns)


@pytest.mark.parametrize("brief", [BRIEF, STORE])
def test_generated_test_suite_passes_on_the_web_layer(brief):
    """The same tests/test_api.py a user gets runs here against urls + views + middleware + deps, with an in-memory database."""
    spec, st, m, files = dbuild("sqlite", brief)
    w = Web("sqlite", brief)
    try:
        t = _load_generated_tests(w, files)
        t.test_health(w.call)
        t.test_unknown_route_is_json_404(w.call)
        t.test_invalid_json_is_a_client_error(w.call)
        t.test_register_login_me_refresh_logout(w.call)
        t.test_login_rejects_non_string_credentials(w.call)
        if hasattr(t, "test_user_list_is_admin_only_and_hides_password_hashes"):
            t.test_user_list_is_admin_only_and_hides_password_hashes(w.db, w.call)
        assert t.ENTITIES
        for e in t.ENTITIES:
            t.test_entity_access_rules_and_crud(w.db, w.call, e)
    finally:
        w.close()


def test_routes_equal_the_spec_contract_and_405_has_allow_header():
    spec, st, m, files = dbuild("sqlite", STORE)
    w = Web("sqlite", STORE)
    try:
        listed = {f"{mth} {p}" for mth, p, _ in w.views.routes() if not p.startswith(("/api/docs", "/api/openapi"))}
        assert listed == set(m["manifest"])
        res = w.send(Req("GET", "/api/auth/login"))
        assert res.status_code == 405 and res.headers["Allow"] == "POST" and res.json()["error"]["code"] == "method_not_allowed"
        assert w.send(Req("GET", "/api/docs")).headers["Content-Type"].startswith("text/html") and "/api/orders" in w.send(Req("GET", "/api/docs")).content.decode()
        assert w.send(Req("GET", "/api/openapi.json")).json()["paths"]["/api/health"]["get"]
        assert w.call("GET", "/api/products/")[0] == 200                                                         # optional trailing slash
    finally:
        w.close()


def test_middleware_host_cors_headers_and_error_envelope():
    w = Web("sqlite", STORE)
    try:
        bad = w.send(Req("GET", "/api/health", host="evil.example"))
        assert bad.status_code == 400 and bad.json()["error"]["code"] == "bad_request"
        ok = w.send(Req("GET", "/api/health", headers={"Origin": "http://localhost:5173"}))
        assert ok.status_code == 200 and ok.headers["Access-Control-Allow-Origin"] == "http://localhost:5173" and ok.headers["Vary"] == "Origin"
        assert ok.headers["X-Content-Type-Options"] == "nosniff" and ok.headers["X-Frame-Options"] == "DENY" and ok.headers["Cache-Control"] == "no-store"
        assert "Access-Control-Allow-Origin" not in w.send(Req("GET", "/api/health", headers={"Origin": "http://evil.example"})).headers
        pre = w.send(Req("OPTIONS", "/api/products", headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "POST"}))
        assert pre.status_code == 204 and "POST" in pre.headers["Access-Control-Allow-Methods"] and pre.headers["Access-Control-Max-Age"] == "600"
        big = w.send(Req("POST", "/api/auth/login", too_big=True))
        assert big.status_code == 413 and big.json()["error"]["code"] == "payload_too_large"
        w.deps._db = None                                                                                          # an unexpected failure becomes a plain 500
        w.views.service.list_records = lambda *a, **k: 1 / 0
        w.deps._db = w.db
        res = w.send(Req("GET", "/api/products"))
        assert res.status_code == 500 and res.json() == {"error": {"code": "internal_error", "message": "Something went wrong"}}
        assert w.mw.ApiMiddleware(None).process_exception(Req("GET", "/api/x"), Http404()) is None               # Django maps these itself
        w.db.ping = lambda: (_ for _ in ()).throw(RuntimeError("down"))
        assert w.call("GET", "/api/health") == (503, {"status": "degraded", "db": "down"})
    finally:
        w.close()


def test_no_database_web_layer_serves_health_and_404_only():
    w = Web("none", "simple landing page", auth="none")
    try:
        assert w.call("GET", "/api/health") == (200, {"status": "ok"})
        assert w.call("GET", "/api/courses")[0] == 404 and w.call("POST", "/api/auth/login", {})[0] == 404
    finally:
        w.close()


# ------------------------------------------------------------------ settings (importable without Django)
def _settings(db, url, **env):
    os.environ.update({"ALLOWED_HOSTS": env.pop("hosts", "")} if "hosts" in env else {})
    path, _ = load_project(db, STORE, backend="django")
    os.environ["DATABASE_URL"] = url
    for k, v in env.items():
        os.environ[k] = v
    import importlib
    return path, importlib.import_module("app.settings")


def test_settings_parse_database_urls():
    cases = [("sqlite", "sqlite:///:memory:", "django.db.backends.sqlite3", {"NAME": ":memory:"}),
             ("sqlite", "sqlite:///./app.db", "django.db.backends.sqlite3", {"NAME": os.path.join(".", "app.db").lstrip("./") or "app.db"}),
             ("postgresql", "postgresql://u:p%40ss@db.example:5433/shop?sslmode=require", "django.db.backends.postgresql",
              {"NAME": "shop", "USER": "u", "PASSWORD": "p@ss", "HOST": "db.example", "PORT": "5433", "OPTIONS": {"sslmode": "require"}}),
             ("postgresql", "postgres://u:p@localhost/shop", "django.db.backends.postgresql", {"HOST": "localhost", "PORT": "", "OPTIONS": {}})]
    for db, url, engine, expect in cases:
        path, s = _settings(db, url)
        try:
            d = s.DATABASES["default"]
            assert d["ENGINE"] == engine and all(d[k] == v for k, v in expect.items()), (url, d)
            assert s.DEBUG is False and s.INSTALLED_APPS == ["app.apps.ApiConfig"] and s.USE_TZ is False and s.MIDDLEWARE == ["app.middleware.ApiMiddleware"]
            assert "testserver" in s.ALLOWED_HOSTS and "localhost" in s.ALLOWED_HOSTS and len(s.SECRET_KEY) == 64
        finally:
            unload(path)
    py = types.ModuleType("pymysql")
    py.install_as_MySQLdb = lambda: setattr(py, "installed", True)
    sys.modules["pymysql"] = py
    try:
        path, s = _settings("mysql", "mysql://root:pw@127.0.0.1:3306/shop")
        d = s.DATABASES["default"]
        assert d["ENGINE"] == "django.db.backends.mysql" and d["PORT"] == "3306" and d["OPTIONS"] == {"charset": "utf8mb4"} and py.installed
        unload(path)
    finally:
        del sys.modules["pymysql"]
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"
    for db, url in (("postgresql", "mysql://u:p@h/db"), ("sqlite", "postgresql://u:p@h/db")):
        try:
            _settings(db, url)
            raise AssertionError("mismatch accepted")
        except RuntimeError as exc:
            assert "DATABASE_URL" in str(exc)
        finally:
            for n in [n for n in sys.modules if n == "app" or n.startswith("app.")]:
                del sys.modules[n]
            sys.path[:] = [p for p in sys.path if not p.endswith("backend") or "tmp" not in p]
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"


# ------------------------------------------------------------------ pipeline: idempotent, keeps user edits
def test_regeneration_is_idempotent_and_keeps_user_edits():
    pf, spec, st, out = generate("dj-edit", "sqlite")
    again = stage.run(pf, spec, st)
    assert again["written"] == [] and again["kept"] == []
    pf.write("backend/app/views.py", pf.read("backend/app/views.py") + "\n# my change\n")
    third = stage.run(pf, spec, st)
    assert third["kept"] == ["backend/app/views.py"] and "# my change" in pf.read("backend/app/views.py")
    assert out["commands"]["run"].endswith("python -m scripts.seed_admin && python -m app") and out["commands"]["test"] == "cd backend && python -m pytest"
    assert out["routes"] == len(model.build(spec, st)["manifest"])


def test_generated_conftest_starts_django_lazily_and_head_is_allowed():
    spec, st, m, files = dbuild("postgresql")
    tree = ast.parse(files["backend/tests/conftest.py"])
    top = [n for n in tree.body if isinstance(n, ast.Expr) and "setup" in ast.unparse(n)]
    assert top == [] and "def _setup" in files["backend/tests/conftest.py"]          # a skipped PostgreSQL suite must not import the settings
    w = Web("sqlite", STORE)
    try:
        assert w.send(Req("HEAD", "/api/health")).status_code == 200 and w.send(Req("HEAD", "/api/auth/login")).status_code == 405
    finally:
        w.close()


def test_readme_matches_the_project():
    spec, st, m, files = dbuild("mysql")
    r = files["backend/README.md"]
    assert "Django + MySQL" in r and "python manage.py makemigrations" in r and "python -m scripts.seed_admin" in r and "TEST_DATABASE_URL" in r
    assert all(f"`{route}`" in r for route in m["manifest"]) and "DEBUG" in r and "admin site is not generated" in r
    ast.parse(files["backend/app/urls.py"])

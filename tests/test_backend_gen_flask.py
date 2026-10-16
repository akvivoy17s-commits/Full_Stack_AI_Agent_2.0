"""Phase 3C: Flask generator (rule based). Same framework-neutral core as FastAPI (covered in test_backend_gen_fastapi.py); here the
Flask web layer is executed over real HTTP calls (Flask test client) against an in-memory database. The generated project's own pytest suite
(real SQLite) runs only when Flask, SQLAlchemy, bcrypt, PyJWT and pytest are installed."""
import importlib.util
import json
import os
import py_compile
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

from backend.gen import flask_gen, stage
from backend.gen import model as _model
from backend.spec import compose
from backend.stack import catalog as C
from backend.tools.project_files import ProjectFiles
from gen_helpers import BRIEF, DBS, STORE, FakeDb, build, load_project, stack_for, unload

PW = "Passw0rd!long"
ORIGIN = "http://localhost:5173"


def fbuild(db, brief=BRIEF, **kw):
    return build(db, brief, backend="flask", **kw)


# ------------------------------------------------------------------ readiness is per combination
def test_ready_combinations_and_honest_gaps():
    for db in DBS:
        assert C.generator_gaps(stack_for(db, backend="flask")) == [], db
    assert C.status("backend", "flask", stack_for("sqlite", backend="flask")) == "ready"
    assert any("MongoEngine" in g or "mongoengine" in g.lower() for g in C.generator_gaps({**stack_for("mongodb", backend="flask"), "orm": "mongoengine"}))
    assert C.generator_gaps({**stack_for("sqlite", backend="flask"), "auth": "oauth2"})
    assert stage.coverage(stack_for("mysql", backend="flask"))["ready"] is True
    assert C.status("backend", "spring", {"backend": "spring", "database": "sqlite"}) == "ready"   # Spring Boot generator finished in v2 phase 5
    assert stack_for("sqlite", backend="flask")["orm"] == "sqlalchemy" and stack_for("mongodb", backend="flask")["orm"] == "pymongo"


# ------------------------------------------------------------------ generated project
@pytest.mark.parametrize("db", DBS)
def test_generates_complete_flask_project_that_compiles(db):
    spec, st, m, files = fbuild(db)
    for need in ("backend/app/main.py", "backend/app/deps.py", "backend/app/schema.py", "backend/app/service.py", "backend/app/auth_service.py",
                 "backend/app/routes/crud.py", "backend/app/routes/auth.py", "backend/tests/test_api.py", "backend/tests/conftest.py",
                 "backend/requirements.txt", "backend/.env.example", "backend/README.md", "backend/scripts/seed_admin.py", "backend/scripts/migrate.py"):
        assert need in files, need
    req = files["backend/requirements.txt"]
    assert "flask>=3" in req and "waitress" in req and "fastapi" not in req and "uvicorn" not in req
    assert ("pymongo" in req) == (db == "mongodb") and ("sqlalchemy" in req) == (db != "mongodb")
    assert not any("fastapi" in t.lower() or "starlette" in t.lower() for rel, t in files.items() if rel.endswith(".py"))   # no FastAPI leaks into the Flask project
    tmp = Path(tempfile.mkdtemp())
    try:
        for rel, text in files.items():
            if rel.endswith(".py"):
                fp = tmp / rel
                fp.parent.mkdir(parents=True, exist_ok=True)
                fp.write_text(text, encoding="utf-8")
                py_compile.compile(str(fp), doraise=True)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_no_database_means_health_only_api():
    spec, st, m, files = fbuild("none", "simple landing page")
    assert "backend/app/main.py" in files and "backend/app/service.py" not in files and "backend/app/routes/crud.py" not in files
    assert files["backend/requirements.txt"].splitlines()[:3] == flask_gen.BASE and "sqlalchemy" not in files["backend/requirements.txt"]


def test_database_without_auth_has_no_auth_code():
    spec, st, m, files = fbuild("sqlite", "portfolio website with contact form", auth="none")
    assert "backend/app/routes/crud.py" in files and "backend/app/security.py" not in files and "backend/app/routes/auth.py" not in files
    assert "PyJWT" not in files["backend/requirements.txt"] and "bcrypt" not in files["backend/requirements.txt"]


def test_readme_env_and_manifest_describe_flask():
    spec, st, m, files = fbuild("postgresql", STORE)
    assert files["backend/README.md"].startswith("# ") and "Flask + PostgreSQL" in files["backend/README.md"] and "route reference: /api/docs" in files["backend/README.md"]
    env = files["backend/.env.example"]
    assert "JWT_SECRET=<generate-a-long-random-string>" in env and "DATABASE_URL=postgresql://user:password@localhost" in env and "npm" not in env
    manifest = json.loads(files["backend/.agent-manifest.json"])
    assert manifest["generator"] == "flask" and set(manifest["routes"]) == set(m["manifest"]) and ("checkout" in m["not_generated"]) == (m["db"] == "mongodb")


def test_stage_run_writes_files_reports_commands_and_keeps_user_edits():
    st = stack_for("sqlite", backend="flask")
    spec = compose.build(BRIEF, st)
    pf = ProjectFiles("gen-flask-sqlite")
    out = stage.run(pf, spec, st)
    assert out["generated"] and out["generator"] == "flask" and out["routes"] > 10 and "python -m app" in out["commands"]["run"]
    assert stage.run(pf, spec, st)["written"] == []
    pf.write("backend/app/main.py", pf.read("backend/app/main.py") + "\n# my change\n")
    assert stage.run(pf, spec, st)["kept"] == ["backend/app/main.py"]
    st2 = {**st, "backend_lang": "js"}
    assert stage.run(ProjectFiles("gen-flask-bad"), compose.build(BRIEF, st2), st2)["generated"] is False


def test_switching_generator_keeps_both_states_honest():
    pf = ProjectFiles("gen-switch")
    st = stack_for("sqlite", backend="flask")
    spec = compose.build(BRIEF, st)
    assert stage.run(pf, spec, st)["generator"] == "flask" and stage.status(pf)["generator"] == "flask"


# ------------------------------------------------------------------ the Flask web layer, over HTTP, with an in-memory database
@pytest.fixture()
def api():
    pytest.importorskip("flask")
    path, S = load_project(brief=STORE, backend="flask")
    try:
        from app.main import create_app
        from app.security import hash_password
        db = FakeDb(S)
        client = create_app(db).test_client()

        def call(method, url, body=None, token=None, raw=None, headers=None):
            h = {"Authorization": f"Bearer {token}"} if token else {}
            h.update(headers or {})
            if raw is not None:
                res = client.open(url, method=method, data=raw, headers={**h, "Content-Type": "application/json"})
            else:
                res = client.open(url, method=method, json=body, headers=h)
            return res.status_code, res.get_json(silent=True), res

        def user(role=None):
            email = f"u{len(db.rows['User']) + 1}@example.com"
            if role:
                db.create("User", {"email": email, "name": "Seeded", "password_hash": hash_password(PW), "role": role})
            else:
                assert call("POST", "/api/auth/register", {"email": email, "name": "T", "password": PW})[0] == 201
            s, b, _ = call("POST", "/api/auth/login", {"email": email, "password": PW})
            assert s == 200
            return b["accessToken"]

        yield S, db, call, user
    finally:
        unload(path)


def _vals(S, db, e, api=True):
    out = {}
    for f in e["fields"]:
        if not f["required"] or (api and (f["name"] == e["ownerField"] or f["name"] in e["sensitive"] or f["name"] == "created_at")):
            continue
        out[f["name"]] = (db.create(f["ref"], _vals(S, db, S["entities"][f["ref"]], False))["id"] if f["type"] == "ref" else f["values"][0] if f["type"] == "enum"
                          else "2030-01-01T00:00:00.000Z" if f["type"] == "datetime"
                          else {"int": 3, "float": 1.5, "bool": True, "email": f"x{len(out)}@e.io", "url": "https://e.io"}.get(f["type"], f"v{len(out)}"))
    return out


def test_http_errors_are_json_and_headers_are_set(api):
    S, db, call, user = api
    s, b, res = call("GET", "/api/health")
    assert s == 200 and b == {"status": "ok", "db": "up"} and res.headers["X-Content-Type-Options"] == "nosniff" and res.headers["Cache-Control"] == "no-store"
    s, b, _ = call("GET", "/api/nope")
    assert s == 404 and b["error"]["code"] == "not_found"
    s, b, _ = call("POST", "/api/health")
    assert s == 405 and b["error"]["code"] == "method_not_allowed"
    s, b, _ = call("POST", "/api/auth/login", raw=b"{not json")
    assert s == 400 and b["error"]["code"] == "invalid_json"
    s, b, _ = call("POST", "/api/auth/login", raw=b"x" * (101 * 1024))
    assert s == 413 and b["error"]["code"] == "payload_too_large"
    s, b, _ = call("POST", "/api/auth/register", {"email": "bad", "name": "", "password": "x"})
    assert s == 400 and set(b["error"]["details"]) == {"email", "name", "password"}
    assert call("POST", "/api/auth/login", {"email": {"$ne": "x"}, "password": {"$ne": "x"}})[0] == 400


def test_http_cors_allows_only_listed_origins(api):
    S, db, call, user = api
    s, _, res = call("OPTIONS", "/api/health", headers={"Origin": ORIGIN, "Access-Control-Request-Method": "POST"})
    assert s == 204 and res.headers["Access-Control-Allow-Origin"] == ORIGIN and "Authorization" in res.headers["Access-Control-Allow-Headers"]
    s, _, res = call("OPTIONS", "/api/health", headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "POST"})
    assert "Access-Control-Allow-Origin" not in res.headers
    _, _, res = call("GET", "/api/health", headers={"Origin": ORIGIN})
    assert res.headers["Access-Control-Allow-Origin"] == ORIGIN and "Origin" in res.headers["Vary"]
    _, _, res = call("GET", "/api/health", headers={"Origin": "https://evil.example"})
    assert "Access-Control-Allow-Origin" not in res.headers


def test_http_auth_flow_and_token_rules(api):
    S, db, call, user = api
    s, b, _ = call("POST", "/api/auth/register", {"email": "A@Example.com", "name": "A", "password": PW})
    assert s == 201 and b["user"]["role"] == S["defaultRole"] and "password_hash" not in b["user"]
    assert call("POST", "/api/auth/register", {"email": "a@example.com", "name": "A", "password": PW})[0] == 409
    assert call("POST", "/api/auth/register", {"email": "b@example.com", "name": "B", "password": PW, "role": S["adminRole"]})[0] == 400
    assert call("POST", "/api/auth/login", {"email": "a@example.com", "password": "wrong-password"})[0] == 401
    s, b, _ = call("POST", "/api/auth/login", {"email": "a@example.com", "password": PW})
    access, refresh = b["accessToken"], b["refreshToken"]
    assert call("GET", "/api/auth/me")[0] == 401 and call("GET", "/api/auth/me", token="not-a-token")[0] == 401
    assert call("GET", "/api/auth/me", token=access)[1]["user"]["email"] == "a@example.com"
    s, b, _ = call("POST", "/api/auth/refresh", {"refreshToken": refresh})
    assert s == 200 and b["refreshToken"] != refresh
    assert call("POST", "/api/auth/refresh", {"refreshToken": refresh})[0] == 401          # single use
    assert call("POST", "/api/auth/logout", {}, token=access)[0] == 204
    assert call("POST", "/api/auth/refresh", {"refreshToken": b["refreshToken"]})[0] == 401   # signed out everywhere
    import jwt
    forged = jwt.encode({"sub": "1", "role": S["adminRole"], "exp": 4102444800}, "some-other-secret-" + "y" * 32, algorithm="HS256")
    assert call("GET", "/api/auth/me", token=forged)[0] == 401


def test_http_entity_access_rules_follow_the_spec(api):
    S, db, call, user = api
    E = S["entities"]
    admin, u1, u2 = user(S["adminRole"]), user(), user()
    product, order = E["Product"], E["Order"]
    pp, op = f"/api/{product['path']}", f"/api/{order['path']}"
    assert product["read"] == "public" and product["write"] == "admin" and order["read"] == "owner"
    assert call("GET", pp)[0] == 200 and call("GET", f"{pp}?q=nothing-matches-this")[1]["total"] == 0
    assert call("POST", pp, _vals(S, db, product))[0] == 401 and call("POST", pp, _vals(S, db, product), token=u1)[0] == 403
    assert call("POST", pp, {**_vals(S, db, product), "bogus": 1}, token=admin)[0] == 400
    s, made, _ = call("POST", pp, _vals(S, db, product), token=admin)
    assert s == 201 and call("GET", f"{pp}/{made['id']}")[0] == 200 and call("GET", f"{pp}/abc")[0] == 404
    assert call("PUT", f"{pp}/{made['id']}", {}, token=admin)[0] == 200 and call("DELETE", f"{pp}/{made['id']}", token=u1)[0] == 403
    assert call("DELETE", f"{pp}/{made['id']}", token=admin)[0] == 204 and call("GET", f"{pp}/{made['id']}")[0] == 404
    assert call("GET", op)[0] == 401
    s, mine, _ = call("POST", op, _vals(S, db, order), token=u1)
    assert s == 201 and call("GET", f"{op}/{mine['id']}", token=u1)[0] == 200
    assert call("GET", f"{op}/{mine['id']}", token=u2)[0] == 404 and call("PUT", f"{op}/{mine['id']}", {}, token=u2)[0] == 404   # other users' records do not exist
    assert call("GET", f"{op}/{mine['id']}", token=admin)[0] == 200
    assert [call("GET", op, token=t)[1]["total"] for t in (u1, u2, admin)] == [1, 0, 1]
    assert call("POST", op, {**_vals(S, db, order), order["ownerField"]: 999}, token=u1)[0] == 400       # owner link is never client-controlled
    s, lst, _ = call("GET", f"{op}?limit=500", token=admin)
    assert s == 200 and lst["limit"] == 100 and call("GET", f"{op}?limit=0", token=admin)[0] == 400


def test_http_unexpected_errors_do_not_leak_details(api):
    S, db, call, user = api
    admin = user(S["adminRole"])
    db.list_page = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("secret connection string postgres://u:p@h/db"))
    s, b, _ = call("GET", f"/api/{S['entities']['Product']['path']}")
    assert s == 500 and b == {"error": {"code": "internal_error", "message": "Something went wrong"}}
    db.ping = lambda: (_ for _ in ()).throw(RuntimeError("down"))
    assert call("GET", "/api/health")[0:2] == (503, {"status": "degraded", "db": "down"})


def test_http_docs_list_every_manifest_route(api):
    S, db, call, user = api
    s, spec, _ = call("GET", "/api/openapi.json")
    assert s == 200 and spec["openapi"].startswith("3.") and "/api/auth/login" in spec["paths"] and "post" in spec["paths"]["/api/auth/login"]
    _, _, res = call("GET", "/api/docs")
    page = res.get_data(as_text=True)
    assert res.status_code == 200 and res.mimetype == "text/html" and "/api/auth/refresh" in page and f"/api/{S['entities']['Product']['path']}/{{id}}" in page


# ------------------------------------------------------------------ the generated project's own suite, with real dependencies
@pytest.mark.skipif(not all(importlib.util.find_spec(x) for x in ("flask", "sqlalchemy", "bcrypt", "jwt", "pytest")),
                    reason="needs flask, sqlalchemy, bcrypt, PyJWT, pytest")
@pytest.mark.parametrize("brief", [BRIEF, STORE, "portfolio website with contact form"])
def test_generated_flask_project_runs_its_own_test_suite_on_sqlite(brief):
    spec, st, m, files = fbuild("sqlite", brief)
    tmp = Path(tempfile.mkdtemp())
    try:
        for rel, text in files.items():
            fp = tmp / rel
            fp.parent.mkdir(parents=True, exist_ok=True)
            fp.write_text(text, encoding="utf-8")
        env = {k: v for k, v in os.environ.items() if k not in ("DATABASE_URL", "TEST_DATABASE_URL")}
        res = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"], cwd=tmp / "backend", env=env, capture_output=True, text=True, timeout=300)
        assert res.returncode == 0, res.stdout[-3000:] + res.stderr[-1000:]
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ------------------------------------------------------------------ regression: found while building 3C (shared model, affects Express and FastAPI too)
def test_signup_role_is_never_the_administrator_role():
    """The store spec has roles [customer, admin]; the default used to be roles[-1] = admin, so every sign-up became an administrator."""
    for backend in ("express", "fastapi", "flask"):
        for brief in (BRIEF, STORE):
            st = stack_for("sqlite", brief, backend=backend)
            m = model_for(brief, st)
            assert m["defaultRole"] != m["adminRole"], (backend, brief, m["roles"])
    assert model_for(STORE, stack_for("sqlite", STORE, backend="flask"))["defaultRole"] == "customer"
    only_admin = {"roles": ["admin"]}
    spec = compose.build(STORE, stack_for("sqlite", STORE, backend="flask"))
    m = _model.build({**spec, **only_admin}, stack_for("sqlite", STORE, backend="flask"))
    assert m["defaultRole"] == "user" and any("only the 'admin' role" in w for w in m["warnings"])


def model_for(brief, st):
    return _model.build(compose.build(brief, st), st)

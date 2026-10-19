"""Phase 3B: FastAPI generator (rule based). The generated project's framework-independent core (validation, access rules,
authentication) is executed here against an in-memory database; its own pytest suite runs only when FastAPI, SQLAlchemy,
bcrypt, PyJWT and httpx are installed."""
import importlib
import importlib.util
import json
import os
import py_compile
import shutil
import subprocess
import sys
import tempfile
import types
from pathlib import Path

import pytest

from backend.gen import express, fastapi_gen, model, stage
from backend.spec import compose
from backend.stack import catalog as C
from backend.stack.resolver import resolve
from backend.tools.project_files import ProjectFiles

from gen_helpers import BRIEF, DBS, STORE, FakeDb, build, load_project, stack_for, unload  # noqa: E402,F401

# ------------------------------------------------------------------ readiness is per combination
def test_ready_combinations_and_honest_gaps():
    for db in DBS:
        assert C.generator_gaps(stack_for(db)) == [], db
    assert C.status("backend", "fastapi", stack_for("sqlite")) == "ready"
    assert any("Motor" in g for g in C.generator_gaps({**stack_for("mongodb"), "orm": "motor"}))
    assert any("SQLModel" in g for g in C.generator_gaps({**stack_for("sqlite"), "orm": "sqlmodel"}))
    assert C.generator_gaps({**stack_for("sqlite"), "auth": "oauth2"})
    assert C.status("backend", "flask", stack_for("sqlite", backend="flask")) == "ready"      # Flask arrived in phase 3C
    assert stage.coverage(stack_for("postgresql"))["ready"] is True


def test_default_orm_for_fastapi_matches_what_is_generated():
    assert stack_for("sqlite")["orm"] == "sqlalchemy" and stack_for("mongodb")["orm"] == "pymongo"


# ------------------------------------------------------------------ generated project
@pytest.mark.parametrize("db", DBS)
def test_generates_complete_project_that_compiles(db):
    spec, st, m, files = build(db)
    for need in ("backend/app/main.py", "backend/app/schema.py", "backend/app/service.py", "backend/app/auth_service.py", "backend/app/routes/crud.py",
                 "backend/app/routes/auth.py", "backend/tests/test_api.py", "backend/tests/conftest.py", "backend/requirements.txt",
                 "backend/.env.example", "backend/README.md", "backend/scripts/seed_admin.py", "backend/scripts/migrate.py"):
        assert need in files, need
    assert ("backend/app/db/mongo.py" in files) == (db == "mongodb") and ("backend/app/db/sql.py" in files) == (db != "mongodb")
    req = files["backend/requirements.txt"]
    assert ("pymongo" in req) == (db == "mongodb") and ("sqlalchemy" in req) == (db != "mongodb")
    assert {"postgresql": "psycopg", "mysql": "PyMySQL"}.get(db, "\0") in req or db in ("sqlite", "mongodb")
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
    spec, st, m, files = build("none", "simple landing page")
    assert "backend/app/main.py" in files
    for gone in ("backend/app/db/sql.py", "backend/app/service.py", "backend/app/routes/crud.py", "backend/app/security.py", "backend/scripts/migrate.py"):
        assert gone not in files, gone
    assert files["backend/requirements.txt"].splitlines()[:3] == fastapi_gen.BASE and "sqlalchemy" not in files["backend/requirements.txt"]


def test_database_without_auth_has_no_auth_code():
    spec, st, m, files = build("sqlite", "portfolio website with contact form", auth="none")
    assert "backend/app/routes/crud.py" in files and "backend/app/security.py" not in files and "backend/app/routes/auth.py" not in files
    assert "PyJWT" not in files["backend/requirements.txt"] and "bcrypt" not in files["backend/requirements.txt"]


def test_env_example_has_placeholders_only_and_python_commands():
    spec, st, m, files = build("postgresql")
    env = files["backend/.env.example"]
    assert "JWT_SECRET=<generate-a-long-random-string>" in env and "DATABASE_URL=postgresql://user:password@localhost" in env
    assert "python -m scripts.seed_admin" in env and "npm" not in env and "VITE_" not in env and "APP_ENV=development" in env
    assert ".env\n" in files["backend/.gitignore"]
    assert "MONGODB_URI=mongodb://" in build("mongodb")[3]["backend/.env.example"]


def test_routes_in_the_manifest_match_the_spec_contract():
    for db in DBS:
        spec, st, m, files = build(db, STORE)
        manifest = json.loads(files["backend/.agent-manifest.json"])
        assert manifest["generator"] == "fastapi" and set(manifest["routes"]) == set(m["manifest"]) and "GET /api/health" in m["manifest"]
        assert ("checkout" in m["not_generated"]) == (db == "mongodb")      # 6H.1: SQL databases get checkout


def test_stage_run_writes_files_reports_commands_and_keeps_user_edits():
    st = stack_for("sqlite")
    spec = compose.build(BRIEF, st)
    pf = ProjectFiles("gen-fastapi-sqlite")
    out = stage.run(pf, spec, st)
    assert out["generated"] and out["generator"] == "fastapi" and out["routes"] > 10
    assert "python -m app" in out["commands"]["run"] and out["commands"]["test"] == "cd backend && python -m pytest"
    assert stage.run(pf, spec, st)["written"] == []
    pf.write("backend/app/main.py", pf.read("backend/app/main.py") + "\n# my change\n")
    assert stage.run(pf, spec, st)["kept"] == ["backend/app/main.py"] and "# my change" in pf.read("backend/app/main.py")
    st2 = {**st, "backend_lang": "js"}
    gone = stage.run(ProjectFiles("gen-fastapi-bad"), compose.build(BRIEF, st2), st2)
    assert gone["generated"] is False and gone["gaps"]


# ------------------------------------------------------------------ fixes found while building 3B (Express generator, phase 3A)
def test_express_reads_mongodb_uri_named_in_env_example():
    st = stack_for("mongodb", backend="express")
    spec = compose.build(BRIEF, st)
    ex = express.generate(spec, st, model.build(spec, st))
    assert "MONGODB_URI=" in ex["backend/.env.example"] and "env.MONGODB_URI" in ex["backend/src/config.js"]


def test_express_with_database_but_without_auth_ships_jsonwebtoken():
    st = stack_for("sqlite", "portfolio website with contact form", backend="express", auth="none")
    spec = compose.build("portfolio website with contact form", st)
    ex = express.generate(spec, st, model.build(spec, st))
    deps = json.loads(ex["backend/package.json"])["dependencies"]
    assert "jsonwebtoken" in deps and "bcryptjs" not in deps      # middleware/auth.js requires it in every app with a database


# ------------------------------------------------------------------ the generated core, executed
def test_validation_rules_follow_the_schema():
    path, S = load_project()
    try:
        from app import validation as V
        from app.errors import ApiError
        product = S["entities"]["Product"]
        with pytest.raises(ApiError) as e:
            V.validate_body(product, {"bogus": 1}, False)
        d = e.value.details
        assert e.value.status == 400 and d["bogus"] == "is not an accepted field" and any(v == "is required" for v in d.values())
        assert V.validate_body(product, {}, True) == {}
        with pytest.raises(ApiError):
            V.validate_body(product, [], False)
        field = {"name": "x", "type": "int", "required": True, "unique": False}
        assert V.one(field, 5) == (True, 5) and V.one(field, True)[0] is False and V.one(field, 2 ** 40)[0] is False and V.one(field, "5")[0] is False
        assert V.one({**field, "type": "float"}, float("nan"))[0] is False and V.one({**field, "type": "bool"}, 1)[0] is False
        assert V.one({**field, "type": "email"}, " A@B.io ") == (True, "a@b.io") and V.one({**field, "type": "url"}, "javascript:alert(1)")[0] is False
        assert V.one({**field, "type": "datetime"}, "2030-01-01T01:00:00+01:00") == (True, "2030-01-01T00:00:00.000Z")
        assert V.one({**field, "type": "enum", "values": ["a"]}, "b")[0] is False and V.one({**field, "type": "ref"}, 0)[0] is False
        assert V.parse_list(product, {})["limit"] == 20 and V.parse_list(product, {"limit": ["500"]})["limit"] == 100
        for bad in ({"limit": ["0"]}, {"page": ["x"]}, {"limit": ["1", "2"]}, {"q": ["x" * 101]}):
            with pytest.raises(ApiError):
                V.parse_list(product, bad)
    finally:
        unload(path)


def test_access_rules_ownership_and_auth_flow_with_fake_database():
    path, S = load_project()
    try:
        from app import auth_service as A, service as svc
        from app.errors import ApiError
        from app.security import decode_access, hash_password
        db, E = FakeDb(S), S["entities"]

        def values(e, api=True):
            out = {}
            for f in e["fields"]:
                if not f["required"] or (api and (f["name"] == e["ownerField"] or f["name"] in e["sensitive"] or f["name"] == "created_at")):
                    continue
                out[f["name"]] = (db.create(f["ref"], values(E[f["ref"]], False))["id"] if f["type"] == "ref" else f["values"][0] if f["type"] == "enum"
                                  else hash_password("x") if f["name"] == "password_hash" else "2030-01-01T00:00:00.000Z" if f["type"] == "datetime"
                                  else {"int": 3, "float": 1.5, "bool": True, "email": f"x{len(out)}@e.io", "url": "https://e.io"}.get(f["type"], f"v{len(out)}"))
            return out

        def status(fn, *a):
            try:
                fn(*a)
                return 200
            except ApiError as err:
                return err.status

        # sign-up / sign-in / refresh rotation / sign-out
        pw = "Passw0rd!long"
        a = A.register(db, {"email": "A@Example.com", "name": "A", "password": pw})
        assert a["user"]["role"] == S["defaultRole"] and "password_hash" not in a["user"] and a["tokenType"] == "Bearer"
        assert decode_access(a["accessToken"]) == {"id": str(a["user"]["id"]), "role": S["defaultRole"]}
        assert status(A.register, db, {"email": "a@example.com", "name": "A", "password": pw}) == 409
        assert status(A.register, db, {"email": "b@example.com", "name": "B", "password": pw, "role": S["adminRole"]}) == 400
        assert status(A.register, db, {"email": "bad", "name": "", "password": "x"}) == 400
        assert status(A.login, db, {"email": "a@example.com", "password": "wrong-password"}) == 401
        assert status(A.login, db, {"email": {"$ne": "x"}, "password": {"$ne": "x"}}) == 400
        assert status(A.login, db, {"email": "nobody@example.com", "password": pw}) == 401
        login = A.login(db, {"email": "a@example.com", "password": pw})
        assert A.me(db, {"id": str(login["user"]["id"]), "role": "user"})["user"]["email"] == "a@example.com"
        new = A.refresh(db, {"refreshToken": login["refreshToken"]})
        assert new["refreshToken"] != login["refreshToken"] and status(A.refresh, db, {"refreshToken": login["refreshToken"]}) == 401   # single use
        A.logout(db, {"id": str(a["user"]["id"]), "role": "user"}, {})
        assert status(A.refresh, db, {"refreshToken": new["refreshToken"]}) == 401
        with pytest.raises(ApiError) as e:
            decode_access("not-a-token")
        assert e.value.status == 401

        # owner-scoped orders
        order = E["Order"]
        assert order["read"] == "owner" and order["ownerField"] == "user_id"
        u1, u2 = {"id": "1", "role": "user"}, {"id": "2", "role": "user"}
        admin = {"id": "99", "role": S["adminRole"]}
        db.create("User", {**values(E["User"], False), "email": "x@x.io"})
        # Checkout is the customer-facing order creator; generic order CRUD is admin-only.
        mine = db.create("Order", {"user_id": 1, "status": "pending", "total": 1.5, "created_at": "2030-01-01T00:00:00.000Z"})
        assert mine["user_id"] == 1
        assert status(svc.get_record, db, order, mine["id"], u1) == 200 and status(svc.get_record, db, order, mine["id"], admin) == 200
        assert status(svc.get_record, db, order, mine["id"], u2) == 404            # other users cannot see it
        assert status(svc.update_record, db, order, mine["id"], {}, u2) == 404 and status(svc.delete_record, db, order, mine["id"], u2) == 404
        assert status(svc.update_record, db, order, mine["id"], {}, u1) == 403 and status(svc.delete_record, db, order, mine["id"], u1) == 403
        assert svc.list_records(db, order, {}, u2)["total"] == 0 and svc.list_records(db, order, {}, u1)["total"] == 1 and svc.list_records(db, order, {}, admin)["total"] == 1
        assert status(svc.get_record, db, order, "abc", admin) == 404 and status(svc.get_record, db, order, "999999999", admin) == 404
        assert status(svc.create_record, db, order, {**values(order), "user_id": 2}, u1) == 403   # generic order creation is admin-only; checkout creates customer orders
        item = E["OrderItem"]                                   # has a client-writable reference (order_id)
        ref = next(f["name"] for f in item["fields"] if f["type"] == "ref" and f["name"] != item["ownerField"])
        assert status(svc.create_record, db, item, {**values(item), ref: 123456}, u1) == 400
        svc.delete_record(db, order, mine["id"], admin)
        assert status(svc.get_record, db, order, mine["id"], u1) == 404

        # admin-only writes, public reads
        product = E["Product"]
        assert product["read"] == "public" and product["write"] == "admin"
        assert svc.list_records(db, product, {"q": ["nothing-matches"]}, None)["total"] == 0
    finally:
        unload(path)


@pytest.mark.skipif(not all(importlib.util.find_spec(x) for x in ("fastapi", "sqlalchemy", "bcrypt", "jwt", "httpx", "pytest")),
                    reason="needs fastapi, sqlalchemy, bcrypt, PyJWT, httpx, pytest")
@pytest.mark.parametrize("brief", [BRIEF, STORE, "portfolio website with contact form"])
def test_generated_project_runs_its_own_test_suite_on_sqlite(brief):
    spec, st, m, files = build("sqlite", brief)
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

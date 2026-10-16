"""Phase 3A: Express backend generator (rule based). Pure Python; JS checks run only when Node is installed."""
import json
import shutil
import subprocess

import pytest

from backend.gen import model, stage
from backend.spec import compose
from backend.stack import catalog as C
from backend.stack.resolver import resolve
from backend.tools.project_files import ProjectFiles

NODE = shutil.which("node")
BRIEF = "college management system with student login and courses"
DBS = ["sqlite", "postgresql", "mysql", "mongodb"]


def stack_for(db, brief=BRIEF, **extra):
    prefs = {"frontend": "react", "frontend_lang": "ts", "backend": "express", "backend_lang": "js", "database": db,
             "auth": "jwt" if db != "none" else "none", **extra}
    r = resolve("manual", prefs, brief)
    assert r["ok"], r["errors"]
    return r["stack"]


def generate(tmp_pid, db, brief=BRIEF, **extra):
    st = stack_for(db, brief, **extra)
    spec = compose.build(brief, st)
    pf = ProjectFiles(tmp_pid)
    return pf, spec, st, stage.run(pf, spec, st)


# ------------------------------------------------------------------ readiness is per combination
def test_ready_combinations_and_honest_gaps():
    assert C.generator_gaps(stack_for("sqlite")) == []
    assert C.status("backend", "express", stack_for("mongodb")) == "ready"
    ts = {**stack_for("sqlite"), "backend_lang": "ts"}
    assert any("js only" in g for g in C.generator_gaps(ts)) and C.status("backend", "express", ts).startswith("planned")
    assert C.status("database", "mssql", {"backend": "express", "database": "mssql"}) == "ready"
    assert C.status("database", "mssql", {"backend": "go", "database": "mssql"}).startswith("planned")
    assert C.status("backend", "go", {"backend": "go", "database": "mysql"}).startswith("planned")
    assert C.status("database", "mysql", {"backend": "go", "database": "mysql"}).startswith("planned")
    assert any("Prisma" in g for g in C.generator_gaps({**stack_for("sqlite"), "orm": "prisma"}))
    assert C.generator_gaps({"backend": "express", "database": "sqlite", "auth": "oauth2"})


def test_unsupported_stack_generates_nothing_and_says_why():
    st = {**stack_for("sqlite"), "backend_lang": "ts"}
    out = stage.run(ProjectFiles("gen-unsupported"), compose.build(BRIEF, st), st)
    assert out["generated"] is False and out["gaps"]
    assert not any(p.startswith("backend/") for p in ProjectFiles("gen-unsupported").tree())
    assert stage.coverage({"backend": "none"})["ready"] is False


# ------------------------------------------------------------------ generated project
@pytest.mark.parametrize("db", DBS)
def test_generates_complete_project_for_each_database(db):
    pf, spec, st, out = generate(f"gen-{db}", db)
    assert out["generated"] and out["routes"] > 10
    tree = set(pf.tree())
    for need in ("backend/package.json", "backend/.env.example", "backend/README.md", "backend/src/app.js", "backend/src/server.js", "backend/src/schema.js",
                 "backend/src/routes/auth.js", "backend/src/routes/crud.js", "backend/tests/api.test.js", "backend/scripts/seed-admin.js"):
        assert need in tree, need
    pkg = json.loads(pf.read("backend/package.json"))["dependencies"]
    assert ("mongoose" in pkg) == (db == "mongodb") and ("knex" in pkg) == (db != "mongodb")
    assert {"sqlite": "better-sqlite3", "postgresql": "pg", "mysql": "mysql2"}.get(db, "mongoose") in pkg
    assert ("backend/migrations/001_init.js" in tree) == (db != "mongodb")
    assert ("backend/src/db/mongo.js" in tree) == (db == "mongodb") and ("backend/src/db/sql.js" in tree) == (db != "mongodb")


def test_no_database_means_health_only_api():
    pf, spec, st, out = generate("gen-nodb", "none", "simple landing page")
    tree = set(pf.tree())
    assert out["generated"] and "backend/src/routes/crud.js" not in tree and "backend/src/db/sql.js" not in tree
    assert "backend/migrations/001_init.js" not in tree and "backend/scripts/seed-admin.js" not in tree
    assert set(json.loads(pf.read("backend/package.json"))["dependencies"]) == {"express", "cors", "helmet", "express-rate-limit", "dotenv"}


def test_env_example_has_placeholders_only_and_no_public_vars():
    pf, spec, st, out = generate("gen-env", "postgresql")
    env = pf.read("backend/.env.example")
    assert "JWT_SECRET=<generate-a-long-random-string>" in env and "DATABASE_URL=postgresql://user:password@localhost" in env
    assert "VITE_" not in env and "ADMIN_PASSWORD=<choose-a-strong-password>" in env
    assert ".env\n" in pf.read("backend/.gitignore")


def test_routes_match_the_spec_contract():
    """Every spec route is either generated or reported as not generated yet; nothing extra is invented."""
    for db in DBS:
        st = stack_for(db, "online store with products cart and orders")
        spec = compose.build("online store with products cart and orders", st)
        m = model.build(spec, st)
        expected = {"GET /api/health"}
        for e in m["entities"]:
            base = f"/api/{e['path']}"
            for op in e["ops"]:
                expected.add({"list": f"GET {base}", "get": f"GET {base}/{{id}}", "create": f"POST {base}", "update": f"PUT {base}/{{id}}", "delete": f"DELETE {base}/{{id}}"}[op])
        if m["auth"]:
            expected |= {"POST /api/auth/register", "POST /api/auth/login", "POST /api/auth/logout", "GET /api/auth/me"} | ({"POST /api/auth/refresh"} if m["refresh"] else set())
        if db != "mongodb":
            expected.add("POST /api/checkout")
        assert expected == set(m["manifest"]), (db, expected ^ set(m["manifest"]))
        assert ("checkout" in m["not_generated"]) == (db == "mongodb")
        assert m["checkout"] == (db != "mongodb")


def test_checkout_generator_is_complete_for_sql_and_honest_for_mongodb():
    for db in DBS:
        pf, spec, st, out = generate(f"gen-checkout-{db}", db, "online store with products cart and orders")
        tree = set(pf.tree())
        schema_text = pf.read("backend/src/schema.js")
        schema_obj = json.loads(schema_text[schema_text.index("{"):].rstrip(";\n"))
        assert schema_obj["checkout"] == (db != "mongodb")
        assert ("backend/src/routes/checkout.js" in tree) == (db != "mongodb")
        if db == "mongodb":
            assert "checkout" in out["not_generated"]
        else:
            route = pf.read("backend/src/routes/checkout.js")
            assert "transaction" in route and "forUpdate" in route and "server-side price" in route
            assert "if (db && schema.checkout)" in pf.read("backend/src/app.js")


def test_access_rules_and_owner_scoping_come_from_the_spec():
    st = stack_for("sqlite", "online store with products cart and orders")
    spec = compose.build("online store with products cart and orders", st)
    m = {e["name"]: e for e in model.build(spec, st)["entities"]}
    assert m["Product"]["read"] == "public" and m["Product"]["write"] == "admin"
    assert m["Order"]["ownerField"] == "user_id" and m["Order"]["read"] == "owner"
    assert m["OrderItem"]["ownerField"] == "user_id" and m["OrderItem"]["read"] == "owner"
    assert m["User"]["ops"] == ["list"] and "password_hash" in m["User"]["sensitive"]
    assert m["RefreshToken"]["internal"] and m["RefreshToken"]["ops"] == []


def test_migration_orders_parents_first_with_foreign_keys():
    pf, spec, st, out = generate("gen-mig", "mysql")
    mig = pf.read("backend/migrations/001_init.js")
    assert mig.index('createTable("departments"') < mig.index('createTable("courses"')
    assert ".references('id').inTable(\"departments\")" in mig and ".unique()" in mig
    assert mig.count("createTable") == mig.count("dropTableIfExists")
    pf2, *_ = generate("gen-mig-pg", "postgresql")
    assert "useTz: true" in pf2.read("backend/migrations/001_init.js")


# ------------------------------------------------------------------ user edits and idempotency
def test_regeneration_is_idempotent_and_keeps_user_edits():
    pf, spec, st, out = generate("gen-edit", "sqlite")
    again = stage.run(pf, spec, st)
    assert again["written"] == [] and again["kept"] == []
    pf.write("backend/src/app.js", pf.read("backend/src/app.js") + "\n// my change\n")
    third = stage.run(pf, spec, st)
    assert third["kept"] == ["backend/src/app.js"] and "// my change" in pf.read("backend/src/app.js")
    assert stage.status(pf)["generated"] and stage.status(ProjectFiles("gen-never"))["generated"] is False


# ------------------------------------------------------------------ JavaScript checks (need Node)
@pytest.mark.skipif(not NODE, reason="node not installed")
@pytest.mark.parametrize("db", DBS)
def test_generated_javascript_has_valid_syntax(db):
    pf, *_ = generate(f"gen-js-{db}", db)
    for rel in pf.tree():
        if rel.endswith(".js"):
            r = subprocess.run([NODE, "--check", str(pf.root / rel)], capture_output=True, text=True)
            assert r.returncode == 0, f"{rel}: {r.stderr[:300]}"


CHECK = r"""
const assert = require('node:assert/strict');
const { validateBody, parseList } = require('./src/lib/validate');
const s = require('./src/schema');
const course = s.entities.Course;
const bad = (fn) => { try { fn(); } catch (e) { return e.details || e.message; } throw new Error('expected failure'); };
// required, unknown and server-controlled fields
assert.ok(bad(() => validateBody(course, {}, false)).code);
assert.ok(bad(() => validateBody(course, { code: 'C1', title: 'T', bogus: 1 }, false)).bogus);
assert.deepEqual(validateBody(course, { code: ' C1 ', title: 'T' }, false), { code: 'C1', title: 'T' });
assert.ok(bad(() => validateBody(course, { code: 'C1', title: 'T', credits: '3' }, false)).credits);
assert.ok(bad(() => validateBody(course, { code: 'C1', title: 'T', department_id: 0 }, false)).department_id);
assert.deepEqual(validateBody(course, { credits: null }, true), { credits: null });
assert.ok(bad(() => validateBody(course, { code: null }, true)).code);
assert.ok(bad(() => validateBody(course, 'text', false)));
assert.ok(bad(() => validateBody(course, [1], false)));
// the User entity: password_hash and created_at are never client-writable
const u = s.entities.User;
assert.ok(bad(() => validateBody(u, { email: 'a@b.co', name: 'n', password_hash: 'x', role: 'admin' }, false)).password_hash);
assert.ok(bad(() => validateBody(u, { created_at: '2020-01-01' }, true)).created_at);
// list parsing: bounds, operator injection, filters
assert.deepEqual(parseList(course, {}), { page: 1, limit: 20, q: undefined, filters: {}, sort: { field: 'id', dir: 'desc' } });
assert.equal(parseList(course, { limit: '1000' }).limit, 100);
assert.ok(bad(() => parseList(course, { page: '0' })));
assert.ok(bad(() => parseList(course, { q: { $ne: 'x' } })));
assert.ok(bad(() => parseList(course, { department_id: { $ne: 1 } })));
assert.equal(parseList(course, { department_id: '3' }).filters.department_id, 3);
console.log('ok');
"""


@pytest.mark.skipif(not NODE, reason="node not installed")
def test_generated_validation_logic_runs_in_node():
    pf, *_ = generate("gen-validate", "sqlite")
    r = subprocess.run([NODE, "-e", CHECK], cwd=str(pf.root / "backend"), capture_output=True, text=True)
    assert r.returncode == 0 and r.stdout.strip() == "ok", r.stderr[-600:]

"""Phase 4 part 1: NestJS generator (rule based). Pure Python; TypeScript syntax checks run only when Node + TypeScript are installed.
The generated project's own Jest suite (real SQLite) needs `npm install`; it is not run here."""
import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

from backend.gen import model, stage
from backend.gen import nest as N
from backend.spec import compose
from backend.stack import catalog as C
from backend.tools.project_files import ProjectFiles
from gen_helpers import BRIEF, DBS, STORE, build, stack_for

NODE = shutil.which("node")
TSC = shutil.which("tsc")


def nbuild(db, brief=BRIEF, **kw):
    return build(db, brief, backend="nestjs", **kw)


def generate(pid, db, brief=BRIEF, **extra):
    st = stack_for(db, brief, backend="nestjs", **extra)
    spec = compose.build(brief, st)
    pf = ProjectFiles(pid)
    return pf, spec, st, stage.run(pf, spec, st)


# ------------------------------------------------------------------ readiness is per combination
def test_ready_combinations_and_honest_gaps():
    for db in DBS:
        assert C.generator_gaps(stack_for(db, backend="nestjs")) == [], db
    st = stack_for("sqlite", backend="nestjs")
    assert st["orm"] == "typeorm" and stack_for("mongodb", backend="nestjs")["orm"] == "mongoose"
    assert C.status("backend", "nestjs", st) == "ready" and stage.coverage(st)["ready"] is True
    assert any("Prisma" in g for g in C.generator_gaps({**st, "orm": "prisma"}))                 # not generated yet -> reported
    assert C.generator_gaps({**st, "auth": "oauth2"}) and not C.generator_gaps({**st, "cache": "redis"})   # Redis cache is generated since v2 phase 6
    assert C.generator_gaps({**st, "database": "mssql"}) == []                                   # phase 3 of the v2 upgrade: SQL Server is generated
    assert C.status("backend", "spring", {"backend": "spring", "database": "sqlite"}) == "ready"   # Spring Boot generator finished in v2 phase 5


# ------------------------------------------------------------------ generated project
@pytest.mark.parametrize("db", DBS)
def test_generates_complete_nest_project(db):
    spec, st, m, files = nbuild(db)
    for need in ("package.json", "tsconfig.json", "tsconfig.build.json", "nest-cli.json", ".env.example", ".gitignore", "README.md", "src/main.ts", "src/bootstrap.ts",
                 "src/app.module.ts", "src/schema.ts", "src/config.ts", "src/db/connect.ts", "src/db/db.module.ts", "src/crud/crud.controller.ts",
                 "src/crud/crud.service.ts", "src/auth/auth.controller.ts", "src/auth/auth.service.ts", "src/auth/access.ts", "src/scripts/seed-admin.ts",
                 "src/scripts/migrate.ts", "test/api.e2e-spec.ts", "test/setup-env.ts"):
        assert f"backend/{need}" in files, need
    pkg = json.loads(files["backend/package.json"])
    deps = pkg["dependencies"]
    assert (("mongoose" in deps) == (db == "mongodb")) and (("typeorm" in deps) == (db != "mongodb"))
    assert {"sqlite": "better-sqlite3", "postgresql": "pg", "mysql": "mysql2"}.get(db, "mongoose") in deps
    assert {"@nestjs/common", "@nestjs/core", "@nestjs/jwt", "bcryptjs", "helmet"} <= set(deps) and "knex" not in deps and "express-rate-limit" not in deps
    assert pkg["scripts"]["test"] == "jest --runInBand" and "seed:admin" in pkg["scripts"]
    sql = db != "mongodb"
    assert ("backend/src/migrations/001-init.ts" in files) == sql and ("backend/src/db/typeorm.db.ts" in files) == sql
    assert ("backend/src/db/mongoose.db.ts" in files) == (not sql)
    assert files["backend/src/db/connect.ts"].strip().endswith(f"'./{'typeorm' if sql else 'mongoose'}.db';")
    mod = files["backend/src/app.module.ts"]
    assert "AuthModule" in mod and "CrudModule" in mod and "APP_FILTER" in mod and "APP_GUARD" in mod
    assert not any(t for rel, t in files.items() if rel.endswith(".ts") and re.search(r"from '(knex|fastapi|flask)'|require\('express'\)", t))


def test_no_database_means_health_only_api():
    pf, spec, st, out = generate("nest-nodb", "none", "simple landing page")
    tree = set(pf.tree())
    assert out["generated"] and out["generator"] == "nestjs"
    for gone in ("crud", "auth", "scripts", "migrations"):
        assert not any(t.startswith(f"backend/src/{gone}/") for t in tree), gone
    assert not {"backend/src/db/typeorm.db.ts", "backend/src/db/mongoose.db.ts", "backend/src/common/validate.ts"} & tree
    assert "import { Db } from './db'" in pf.read("backend/src/db/connect.ts") and "AuthModule" not in pf.read("backend/src/app.module.ts")
    assert set(json.loads(pf.read("backend/package.json"))["dependencies"]) == set(N.COMMON)


def test_database_without_auth_keeps_guards_but_no_sign_in():
    spec, st, m, files = nbuild("sqlite", "portfolio website with contact form", auth="none")
    assert "backend/src/auth/access.ts" in files and "backend/src/auth/auth.service.ts" not in files and "backend/src/scripts/seed-admin.ts" not in files
    deps = json.loads(files["backend/package.json"])["dependencies"]
    assert "@nestjs/jwt" in deps and "bcryptjs" not in deps and "AuthModule" not in files["backend/src/app.module.ts"]
    assert "ADMIN_PASSWORD" not in files["backend/.env.example"]


def test_env_example_has_placeholders_only_and_no_public_vars():
    spec, st, m, files = nbuild("postgresql")
    env = files["backend/.env.example"]
    assert "JWT_SECRET=<generate-a-long-random-string>" in env and "DATABASE_URL=postgresql://user:password@localhost" in env
    assert "VITE_" not in env and "ADMIN_PASSWORD=<choose-a-strong-password>" in env and ".env\n" in files["backend/.gitignore"]


def test_schema_ts_matches_the_spec_contract():
    """src/schema.ts is the single source of truth for routes: its entities and ops must equal the model built from the spec."""
    for db in ("sqlite", "mongodb"):
        spec, st, m, files = nbuild(db, STORE)
        text = files["backend/src/schema.ts"]
        body = json.loads(text[text.index("SCHEMA = ") + 9:text.index(" as unknown as Schema")])
        assert body["db"] == db and body["auth"] and body["defaultRole"] != body["adminRole"]
        assert list(body["entities"]) == [e["name"] for e in m["entities"]]                     # parents first
        assert {n: e["ops"] for n, e in body["entities"].items()} == {e["name"]: e["ops"] for e in m["entities"]}
        assert body["entities"]["Order"]["ownerField"] == "user_id" and body["entities"]["Product"]["write"] == "admin"
        assert "password_hash" in body["entities"]["User"]["sensitive"]
        assert any("/api/orders" in r for r in m["manifest"]) and ("checkout" in m["not_generated"]) == (db == "mongodb")   # 6H.3: Nest has checkout on SQL


def test_security_defaults_are_in_the_generated_code():
    spec, st, m, files = nbuild("sqlite")
    boot, svc = files["backend/src/bootstrap.ts"], files["backend/src/auth/auth.service.ts"]
    assert "helmet()" in boot and "limit: '100kb'" in boot and "enableCors" in boot and "cfg.validate()" in boot
    assert "role: SCHEMA.defaultRole" in svc and "randomBytes(48)" in svc and "createHash('sha256')" in svc
    assert "algorithms: ['HS256']" in files["backend/src/auth/access.ts"]
    assert "unknown entity" in files["backend/src/db/typeorm.db.ts"] and "ESCAPE '!'" in files["backend/src/db/typeorm.db.ts"]


# ------------------------------------------------------------------ user edits and idempotency
def test_regeneration_is_idempotent_and_keeps_user_edits():
    pf, spec, st, out = generate("nest-edit", "sqlite")
    again = stage.run(pf, spec, st)
    assert again["written"] == [] and again["kept"] == []
    pf.write("backend/src/main.ts", pf.read("backend/src/main.ts") + "\n// my change\n")
    third = stage.run(pf, spec, st)
    assert third["kept"] == ["backend/src/main.ts"] and "// my change" in pf.read("backend/src/main.ts")
    assert "npm run start:dev" in out["commands"]["run"] and out["commands"]["test"] == "cd backend && npm test"


# ------------------------------------------------------------------ TypeScript syntax (needs Node + TypeScript)
@pytest.mark.skipif(not (NODE and TSC), reason="node / typescript not installed")
@pytest.mark.parametrize("db", ["sqlite", "mongodb", "none"])
def test_generated_typescript_has_valid_syntax(db):
    ts_dir = Path(TSC).resolve().parent.parent
    spec, st, m, files = nbuild(db, BRIEF if db != "none" else "simple landing page") if db != "none" else nbuild("none", "simple landing page")
    script = ("const ts=require(process.argv[1]);const f=JSON.parse(require('fs').readFileSync(0,'utf8'));let bad=[];"
              "for(const [n,t] of Object.entries(f)){const r=ts.transpileModule(t,{reportDiagnostics:true,fileName:n,compilerOptions:{experimentalDecorators:true}});"
              "for(const d of r.diagnostics) bad.push(n+': '+ts.flattenDiagnosticMessageText(d.messageText,' '));}"
              "console.log(JSON.stringify(bad));")
    r = subprocess.run([NODE, "-e", script, str(ts_dir)], input=json.dumps({k: v for k, v in files.items() if k.endswith(".ts")}), capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, r.stderr
    assert json.loads(r.stdout) == []

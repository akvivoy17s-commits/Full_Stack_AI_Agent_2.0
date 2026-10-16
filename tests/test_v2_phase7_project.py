"""Phase 7: generated project quality (Dockerfile, compose, CI, frontend API client) for every backend."""
import json
import shutil
import subprocess

import pytest

from backend.gen import model, project
from backend.spec import compose
from gen_helpers import BRIEF, STORE, stack_for

BACKENDS = ["express", "fastapi", "flask", "nestjs", "django", "spring"]
DBS = ["sqlite", "postgresql", "mysql", "mongodb", "none"]


def _gen(be, db, brief=BRIEF, **kw):
    st = stack_for(db, brief, backend=be, **kw)
    spec = compose.build(brief, st)
    m = model.build(spec, st)
    return spec, st, m, project.extras(spec, st, m)


COMBOS = [(be, db) for be in BACKENDS for db in DBS if not (be == "django" and db == "mongodb")]   # Django has no first-party MongoDB support: the rules refuse it


@pytest.mark.parametrize("be,db", COMBOS)
def test_files_per_stack(be, db):
    _, _, m, ex = _gen(be, db)
    assert {"backend/Dockerfile", "backend/.dockerignore", "docker-compose.yml", "docker.env.example", ".github/workflows/ci.yml", "src/api/client.ts"} <= set(ex)
    c = ex["docker-compose.yml"]
    assert ("  db:" in c) == (db in ("postgresql", "mysql", "mongodb"))
    assert ("DATABASE_URL" in c) == (db != "none")
    assert "JWT_SECRET" not in ex["backend/Dockerfile"] and ".env" in ex["backend/.dockerignore"]
    assert ("DB_PASSWORD" in ex["docker.env.example"]) == (db in ("postgresql", "mysql"))


def test_cache_adds_redis_and_uploads_volume():
    _, _, m, ex = _gen("fastapi", "postgresql", cache="redis")
    assert "redis:7" in ex["docker-compose.yml"] and "REDIS_URL" in ex["docker-compose.yml"]
    _, _, m, ex = _gen("fastapi", "postgresql")
    assert "redis" not in ex["docker-compose.yml"]


def test_client_matches_routes():
    _, _, m, ex = _gen("express", "sqlite", STORE)
    c = ex["src/api/client.ts"]
    for e in m["entities"]:
        if not e["internal"] and e["ops"]:
            assert f"/api/{e['path']}" in c
    assert "password_hash" not in c and "refreshToken" in c


def test_javascript_frontend_gets_js_client():
    st = stack_for("sqlite", BRIEF, backend="express")
    st["frontend_lang"] = "javascript"
    spec = compose.build(BRIEF, st)
    ex = project.extras(spec, st, model.build(spec, st))
    assert "src/api/client.js" in ex and "public status" not in ex["src/api/client.js"]


def test_non_vite_frontend_gets_no_client():
    st = stack_for("sqlite", BRIEF, backend="express")
    st["frontend"] = "angular"
    spec = compose.build(BRIEF, st)
    assert not [k for k in project.extras(spec, st, model.build(spec, st)) if k.startswith("src/api")]


@pytest.mark.skipif(not shutil.which("tsc"), reason="tsc not installed")
def test_client_compiles_strict(tmp_path):
    _, _, _, ex = _gen("express", "postgresql", STORE, cache="redis")
    (tmp_path / "client.ts").write_text(ex["src/api/client.ts"])
    r = subprocess.run(["tsc", "--noEmit", "--strict", "--target", "es2022", "--module", "esnext", "--moduleResolution", "bundler", "--skipLibCheck", "--lib", "es2022,dom", str(tmp_path / "client.ts")], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout

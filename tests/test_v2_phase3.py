"""V2 phase 3: database layer (indexes, FK rules, Alembic migration, sample seed, SQL Server). Runs real SQLite; SQL Server is checked as generated SQL only."""
import json
import os
import subprocess
import sys

import pytest

pytest.importorskip("sqlalchemy")
pytest.importorskip("alembic")
from gen_helpers import STORE, build  # noqa: E402

ENV = {"JWT_SECRET": "x" * 48, "CORS_ORIGINS": "http://localhost:5173", "ADMIN_EMAIL": "admin@example.com", "ADMIN_PASSWORD": "Passw0rd-long"}


def _write(tmp_path, db, backend="fastapi"):
    spec, st, m, files = build(db, STORE, backend=backend)
    for rel, text in files.items():
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
    return m, tmp_path / "backend"


def _run(cwd, code, url, mod=None):
    env = {**os.environ, **ENV, "DATABASE_URL": url, "PYTHONPATH": str(cwd)}
    args = [sys.executable, "-m", mod] if mod else [sys.executable, "-c", code]
    return subprocess.run(args, cwd=cwd, env=env, capture_output=True, text=True, timeout=120)


def test_model_rules_are_shared():
    _, _, m, _ = build("postgresql", STORE)
    prod = next(e for e in m["entities"] if e["name"] == "Product")
    f = {x["name"]: x for x in prod["fields"]}
    assert f["category_id"]["index"] and f["category_id"]["onDelete"] == "SET NULL" and not f["description"]["index"]
    assert [s["entity"] for s in m["seed"]] == ["Category", "Product", "Order", "OrderItem"]
    assert m["seed"][1]["rows"][0]["category_id"] == {"$ref": ["Category", 0]}
    _, _, ms, _ = build("mssql", STORE)
    assert all(x.get("onDelete") != "SET NULL" for e in ms["entities"] for x in e["fields"])      # SQL Server: NO ACTION instead
    assert json.dumps(m["seed"]) == json.dumps(build("postgresql", STORE)[2]["seed"])               # deterministic


@pytest.mark.parametrize("backend", ["fastapi", "flask"])
def test_alembic_matches_models_and_seed_is_idempotent(tmp_path, backend):
    _, be = _write(tmp_path, "sqlite", backend)
    url = f"sqlite:///{tmp_path}/t.db"
    drift = ("from app.db import connect, sql\nfrom alembic.migration import MigrationContext\nfrom alembic.autogenerate import compare_metadata\n"
             "d = connect(); d.migrate()\nwith d.engine.connect() as c:\n    print(json.dumps([str(x) for x in compare_metadata(MigrationContext.configure(c), sql.metadata)]))\n")
    r = _run(be, "import json\n" + drift, url)
    assert r.returncode == 0, r.stderr
    assert json.loads(r.stdout.strip().splitlines()[-1]) == []
    assert _run(be, "", url, "scripts.seed_sample").returncode == 0
    assert _run(be, "", url, "scripts.seed_admin").returncode == 0
    assert "Added 3 OrderItem" in _run(be, "", url, "scripts.seed_sample").stdout
    again = _run(be, "", url, "scripts.seed_sample").stdout
    assert "Nothing to add" in again
    chk = _run(be, "import sqlite3\nc=sqlite3.connect(r'%s/t.db')\nprint(c.execute('pragma foreign_key_check').fetchall(), c.execute('select count(*) from order_items').fetchone()[0])" % tmp_path, url)
    assert chk.stdout.strip() == "[] 3"


def test_sql_server_offline_sql(tmp_path):
    pytest.importorskip("pymssql")
    m, be = _write(tmp_path, "mssql")
    r = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head", "--sql"], cwd=be, capture_output=True, text=True,
        env={**os.environ, **ENV, "DATABASE_URL": "mssql://sa:pw@localhost:1433/app", "PYTHONPATH": str(be)}, timeout=120)
    assert r.returncode == 0, r.stderr
    sql = r.stdout
    assert "DATETIME2" in sql and "NVARCHAR(max)" in sql and "IDENTITY" in sql and "ON DELETE NO ACTION" in sql and "SET NULL" not in sql
    assert "CREATE INDEX ix_products_category_id" in sql

"""Shared helpers for the Python backend generator tests (FastAPI 3B, Flask 3C, Django 4.2): stack building, an in-memory database with the same
interface as the generated app/db adapters, and a loader that imports a generated project's `app` package."""
import importlib
import os
import shutil
import sys
import tempfile
import types
from pathlib import Path

import pytest

from backend.gen import django_gen, fastapi_gen, flask_gen, model, nest, spring_gen
from backend.spec import compose
from backend.stack.resolver import resolve

BRIEF = "college management system with student login and courses"
STORE = "online store with products cart and orders"
DBS = ["sqlite", "postgresql", "mysql", "mongodb"]
GENS = {"fastapi": fastapi_gen, "flask": flask_gen, "nestjs": nest, "django": django_gen, "spring": spring_gen}


def stack_for(db, brief=BRIEF, backend="fastapi", auth=None, **extra):
    prefs = {"frontend": "react", "frontend_lang": "ts", "backend": backend, "backend_lang": {"express": "js", "nestjs": "ts", "spring": "java"}.get(backend, "py"), "database": db,
             "auth": auth or ("jwt" if db != "none" else "none"), **extra}
    r = resolve("manual", prefs, brief)
    assert r["ok"], r["errors"]
    return r["stack"]


def build(db, brief=BRIEF, backend="fastapi", **kw):
    st = stack_for(db, brief, backend=backend, **kw)
    spec = compose.build(brief, st)
    m = model.build(spec, st)
    return spec, st, m, GENS[backend].generate(spec, st, m)


class FakeDb:
    """In-memory stand-in with the same interface as app/db/sql.py, to run service.py and auth_service.py without a database server."""

    def __init__(self, schema):
        self.E, self.rows, self.seq = schema["entities"], {n: {} for n in schema["entities"]}, {n: 0 for n in schema["entities"]}

    @staticmethod
    def parse_id(v):
        if isinstance(v, bool):
            return None
        if isinstance(v, str) and v.isascii() and v.isdigit():
            v = int(v)
        return v if isinstance(v, int) and 0 < v <= 2147483647 else None

    def _out(self, n, rec, raw=False):
        if rec is None:
            return None
        return {"id": rec["id"], **{f["name"]: rec.get(f["name"]) for f in self.E[n]["fields"] if raw or f["name"] not in self.E[n]["sensitive"]}}

    def ping(self):
        return True

    def clean(self, n, rec):
        return {k: v for k, v in rec.items() if k not in self.E[n]["sensitive"]}

    def get(self, n, rid):
        i = self.parse_id(rid)
        return None if i is None else self._out(n, self.rows[n].get(i))

    def find_one(self, n, where, raw=False):
        return next((self._out(n, r, raw) for r in self.rows[n].values() if all(r.get(k) == v for k, v in where.items())), None)

    def list_page(self, n, page, limit, q, filters, where, sort=None):
        e = self.E[n]
        rows = [r for r in self.rows[n].values() if all(r.get(k) == v for k, v in {**filters, **where}.items())
                and (not q or not e["searchable"] or any(q.lower() in str(r.get(s, "")).lower() for s in e["searchable"]))]
        f, d = (sort or {}).get("field", "id"), (sort or {}).get("dir", "desc")
        rows.sort(key=lambda r: -r["id"])
        if f != "id" or d == "asc":
            rows.sort(key=lambda r: (r.get(f) is None, r.get(f)), reverse=d == "desc")
        return {"rows": [self._out(n, r) for r in rows[(page - 1) * limit:page * limit]], "total": len(rows)}

    def create(self, n, data):
        from app.errors import ApiError
        for f in self.E[n]["fields"]:
            if f["unique"] and data.get(f["name"]) is not None and any(r.get(f["name"]) == data[f["name"]] for r in self.rows[n].values()):
                raise ApiError(409, "conflict", "A record with the same unique value already exists")
        self.seq[n] += 1
        rec = {"id": self.seq[n], **{f["name"]: None for f in self.E[n]["fields"]}, **data}
        self.rows[n][rec["id"]] = rec
        return self._out(n, rec)

    def update(self, n, rid, data):
        self.rows[n][rid].update(data)
        return self.get(n, rid)

    def remove(self, n, rid):
        self.rows[n].pop(rid, None)

    def remove_where(self, n, where):
        hit = [i for i, r in self.rows[n].items() if all(r.get(k) == v for k, v in where.items())]
        for i in hit:
            del self.rows[n][i]
        return len(hit)


def _stub(name, **attrs):
    mod = types.ModuleType(name)
    mod.__dict__.update(attrs)
    sys.modules[name] = mod


def load_project(db="sqlite", brief=STORE, backend="fastapi", **kw):
    """Writes the generated project to a temp dir and imports its `app` package with a test environment."""
    pytest.importorskip("jwt")
    for name in [n for n in sys.modules if n == "app" or n.startswith("app.")]:
        del sys.modules[name]
    try:
        importlib.import_module("dotenv")
    except ImportError:
        _stub("dotenv", load_dotenv=lambda *a, **k: None)
    try:
        importlib.import_module("bcrypt")
    except ImportError:   # NOT real hashing: only lets the logic run where bcrypt is missing
        _stub("bcrypt", gensalt=lambda rounds=4: b"s", hashpw=lambda pw, salt: b"h:" + pw, checkpw=lambda pw, h: h == b"h:" + pw)
    spec, st, m, files = build(db, brief, backend=backend, **kw)
    tmp = Path(tempfile.mkdtemp())
    for rel, text in files.items():
        fp = tmp / rel
        fp.parent.mkdir(parents=True, exist_ok=True)
        fp.write_text(text, encoding="utf-8")
    os.environ.update({"APP_ENV": "test", "JWT_SECRET": "test-secret-" + "x" * 40, "CORS_ORIGINS": "http://localhost:5173", "DATABASE_URL": "sqlite:///:memory:"})
    sys.path.insert(0, str(tmp / "backend"))
    return tmp / "backend", importlib.import_module("app.schema").SCHEMA


def unload(path):
    sys.path.remove(str(path))
    for name in [n for n in sys.modules if n == "app" or n.startswith("app.")]:
        del sys.modules[name]
    shutil.rmtree(path.parent, ignore_errors=True)

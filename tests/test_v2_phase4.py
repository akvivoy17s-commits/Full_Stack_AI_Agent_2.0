"""V2 phase 4: backend core consistency. Shared OpenAPI document in all 5 generators, ?sort in every list endpoint (validation + data layers)."""
import json
import subprocess
import tempfile
from pathlib import Path

import pytest

from backend.gen import express, model, openapi
from backend.spec import compose
from gen_helpers import STORE, build, load_project, stack_for, unload

BACKENDS = ["fastapi", "flask", "django", "nestjs"]


def _refs(node, found):
    if isinstance(node, dict):
        for k, v in node.items():
            if k == "$ref":
                found.add(v)
            else:
                _refs(v, found)
    elif isinstance(node, list):
        for v in node:
            _refs(v, found)


def _doc(files):
    return json.loads(files["backend/openapi.json"])


@pytest.mark.parametrize("db", ["sqlite", "mongodb"])
def test_openapi_same_in_all_generators_and_valid(db):
    docs = {}
    backends = [b for b in BACKENDS if not (db == "mongodb" and b == "django")]   # Django has no MongoDB support
    for b in backends:
        spec, st, m, files = build(db, STORE, backend=b)
        docs[b] = files["backend/openapi.json"]
    st = stack_for(db, STORE, backend="express")
    spec = compose.build(STORE, st)
    m = model.build(spec, st)
    docs["express"] = express.generate(spec, st, m)["backend/openapi.json"]
    # fastapi/flask/django/nestjs use identical model, so the document must be byte-identical (express may add /api/checkout)
    base = docs["fastapi"]
    assert all(docs[b] == base for b in backends)
    d = json.loads(docs["express"])
    assert d["openapi"] == "3.0.3" and d["paths"] and d["components"]["schemas"]["Error"]
    # every $ref resolves
    found = set()
    _refs(d, found)
    for r in found:
        node = d
        for part in r.removeprefix("#/").split("/"):
            node = node[part]
    # every generated route is documented
    for line in m["manifest"]:
        method, path = line.split(" ", 1)
        assert method.lower() in d["paths"].get(path, {}), line
    # sort is documented on every list
    lists = [op for p, ops in d["paths"].items() for mth, op in ops.items() if mth == "get" and "parameters" in op and any(x["name"] == "page" for x in op["parameters"])]
    assert lists and all(any(x["name"] == "sort" for x in op["parameters"]) for op in lists)
    # secrets never appear
    assert "password_hash" not in docs["express"]


def _fake_service(backend="flask"):
    path, schema = load_project("sqlite", STORE, backend=backend)
    return path, schema


def test_python_sort_parse_and_order():
    path, schema = _fake_service("flask")
    try:
        import importlib
        v = importlib.import_module("app.validation")
        e = schema["entities"]["Product"]
        name = next(f["name"] for f in e["fields"] if f["type"] in ("string",) and f["name"] not in e["sensitive"])
        assert v.parse_list(e, {})["sort"] == {"field": "id", "dir": "desc"}
        assert v.parse_list(e, {"sort": ["-" + name]})["sort"] == {"field": name, "dir": "desc"}
        assert v.parse_list(e, {"sort": [name]})["sort"] == {"field": name, "dir": "asc"}
        text = next((f["name"] for f in e["fields"] if f["type"] == "text"), None)
        bad = ["nope", "-nope", "", "id;drop", "password_hash"] + ([text] if text else [])
        for b in bad:
            with pytest.raises(Exception) as ei:
                v.parse_list(e, {"sort": [b]})
            assert "sort" in str(getattr(ei.value, "message", ei.value)).lower() or ei.value.status == 400
        with pytest.raises(Exception):
            v.parse_list(e, {"sort": ["a", "b"]})
        # user entity: sensitive fields cannot be sorted on
        u = schema["entities"]["User"]
        for s in u["sensitive"]:
            with pytest.raises(Exception):
                v.parse_list(u, {"sort": [s]})
    finally:
        unload(path)


def test_python_sort_end_to_end_with_fake_db():
    from gen_helpers import FakeDb
    path, schema = _fake_service("flask")
    try:
        import importlib
        svc = importlib.import_module("app.service")
        e = schema["entities"]["Product"]
        db = FakeDb(schema)
        names = ["b", "c", "a"]
        for n in names:
            db.create("Product", {f["name"]: (n if f["type"] in ("string", "text") else 1 if f["type"] == "int" else 1.0 if f["type"] == "float" else True if f["type"] == "bool" else None)
                                  for f in e["fields"] if f["required"] and f["type"] != "ref"})
        sf = next(f["name"] for f in e["fields"] if f["type"] == "string")
        admin = {"id": 1, "role": "admin"}
        asc = [r[sf] for r in svc.list_records(db, e, {"sort": [sf]}, admin)["data"]]
        desc = [r[sf] for r in svc.list_records(db, e, {"sort": ["-" + sf]}, admin)["data"]]
        assert asc == sorted(asc) and desc == sorted(desc, reverse=True) and asc == desc[::-1]
        default = [r["id"] for r in svc.list_records(db, e, {}, admin)["data"]]
        assert default == sorted(default, reverse=True)
    finally:
        unload(path)


def test_express_and_nest_parselist_sort():
    st = stack_for("sqlite", STORE, backend="express")
    spec = compose.build(STORE, st)
    m = model.build(spec, st)
    tmp = Path(tempfile.mkdtemp())
    for rel, text in express.generate(spec, st, m).items():
        p = tmp / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    code = """
const { parseList } = require('./src/lib/validate');
const s = require('./src/schema');
const e = s.entities.Product;
const f = e.fields.find((x) => x.type === 'string').name;
const out = {};
out.def = parseList(e, {}).sort;
out.asc = parseList(e, { sort: f }).sort;
out.desc = parseList(e, { sort: '-' + f }).sort;
const bad = ['nope', '-nope', '', 'id;drop', ...e.fields.filter((x) => x.type === 'text').map((x) => x.name), ...(s.entities.User ? [] : [])];
out.rejected = bad.every((b) => { try { parseList(e, { sort: b }); return false; } catch (err) { return err.status === 400 || err.statusCode === 400; } });
try { parseList(e, { sort: ['a', 'b'] }); out.arr = false; } catch (err) { out.arr = true; }
console.log(JSON.stringify({ f, ...out }));
"""
    r = subprocess.run(["node", "-e", code], cwd=tmp / "backend", capture_output=True, text=True, timeout=60)
    if "Cannot find module" in r.stderr:
        pytest.skip("express dependencies not installed")
    assert r.returncode == 0, r.stderr
    o = json.loads(r.stdout)
    assert o["def"] == {"field": "id", "dir": "desc"} and o["asc"] == {"field": o["f"], "dir": "asc"} and o["desc"]["dir"] == "desc"
    assert o["rejected"] and o["arr"]


def test_flask_http_sort_errors_and_openapi():
    """Over real HTTP (Flask test client, in-memory db): ?sort works, bad sort gives the standard error body, /api/openapi.json is the shared document."""
    pytest.importorskip("flask")
    from gen_helpers import FakeDb
    path, S = load_project(brief=STORE, backend="flask")
    try:
        from app.main import create_app
        from app.security import hash_password
        db = FakeDb(S)
        c = create_app(db).test_client()
        db.create("User", {"email": "a@example.com", "name": "A", "password_hash": hash_password("Passw0rd!long"), "role": "admin"})
        tok = c.post("/api/auth/login", json={"email": "a@example.com", "password": "Passw0rd!long"}).get_json()["accessToken"]
        h = {"Authorization": f"Bearer {tok}"}
        e = S["entities"]["Product"]
        sf = next(f["name"] for f in e["fields"] if f["type"] == "string")
        body = {f["name"]: ("x" if f["type"] in ("string", "text") else 1 if f["type"] == "int" else 1.5 if f["type"] == "float" else True)
                for f in e["fields"] if f["required"] and f["type"] not in ("ref", "enum", "email", "url", "datetime")}
        for n in ("b", "c", "a"):
            r = c.post("/api/" + e["path"], json={**body, sf: n}, headers=h)
            assert r.status_code == 201, r.get_json()
        got = lambda q: [x[sf] for x in c.get(f"/api/{e['path']}?{q}", headers=h).get_json()["data"]]
        assert got(f"sort={sf}") == ["a", "b", "c"] and got(f"sort=-{sf}") == ["c", "b", "a"]
        r = c.get(f"/api/{e['path']}?sort=nope", headers=h)
        j = r.get_json()
        assert r.status_code == 400 and j["error"]["code"] == "validation_failed" and "sort" in j["error"]["message"]
        spec = c.get("/api/openapi.json").get_json()
        assert spec == json.loads((path / "openapi.json").read_text(encoding="utf-8")) and f"/api/{e['path']}" in spec["paths"]
        assert c.get("/api/docs").status_code == 200
    finally:
        unload(path)

"""Phase 1: technology selection HTTP API (needs FastAPI, like the other API tests)."""
import time

from fastapi.testclient import TestClient

from backend.main import app
from backend.memory import project_store
from backend.storage import db

client = TestClient(app)


def _wait(tid, timeout=20):
    end = time.time() + timeout
    while time.time() < end:
        t = client.get(f"/tasks/{tid}").json()
        if t["status"] in db.TERMINAL:
            return t
        time.sleep(0.1)
    raise AssertionError("task did not finish")


def test_catalog_lists_every_category_with_status():
    c = client.get("/stack/catalog").json()
    assert {"frontend", "backend", "database", "auth", "cache", "storage", "ai", "testing", "deploy"} <= set(c["fields"])
    assert next(o for o in c["fields"]["backend"] if o["id"] == "spring")["status"] == "ready"      # Spring Boot generator finished in v2 phase 5


def test_resolve_returns_stack_reasons_and_filtered_options():
    r = client.post("/stack/resolve", json={"mode": "hybrid", "prefs": {"backend": "django"}, "brief": "Online store with checkout"}).json()
    assert r["ok"] and r["stack"]["backend"] == "django" and r["reasons"]["database"]
    mongo = next(o for o in r["options"]["database"] if o["id"] == "mongodb")
    assert not mongo["allowed"]
    assert client.post("/stack/resolve", json={"mode": "bogus"}).status_code == 422


def test_legacy_project_creation_is_unchanged_and_has_a_stack():
    pid = client.post("/projects", json={"brief": "fitness app landing page", "framework": "react"}).json()["project_id"]
    cfg = client.get(f"/projects/{pid}/stack").json()
    assert cfg["stack"]["frontend"] == "react" and cfg["stack"]["backend"] == "none" and not cfg["blocking"]


def test_incompatible_selection_is_rejected_with_reasons():
    r = client.post("/projects", json={"brief": "My blog platform", "mode": "hybrid", "prefs": {"backend": "django", "database": "mongodb"}})
    assert r.status_code == 422 and r.json()["detail"]["errors"]


def test_changing_frontend_after_generation_needs_confirmation():
    pid = client.post("/projects", json={"brief": "Portfolio website", "mode": "hybrid", "prefs": {"frontend": "react", "frontend_lang": "ts"}}).json()["project_id"]
    st = project_store.load(pid)
    st.sections_done = ["hero"]
    project_store.save(st)
    assert client.put(f"/projects/{pid}/stack", json={"prefs": {"frontend": "vue"}}).status_code == 409
    ok = client.put(f"/projects/{pid}/stack", json={"prefs": {"frontend": "vue"}, "confirm": True}).json()
    assert ok["requires_regenerate"] and project_store.load(pid).sections_done == []


def test_generation_is_refused_for_a_frontend_without_generator():
    pid = client.post("/projects", json={"brief": "College portal", "mode": "hybrid", "prefs": {"frontend": "angular"}}).json()["project_id"]
    t = _wait(client.post(f"/projects/{pid}/tasks", json={"kind": "generate"}).json()["id"])
    assert t["status"] == "failed" and "Angular" in t["error"]

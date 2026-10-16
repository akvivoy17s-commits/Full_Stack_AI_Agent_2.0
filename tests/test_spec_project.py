"""Spec + project memory on real projects: creation, API, pipeline wiring, drift detection, no secrets."""
import json
import time

from fastapi.testclient import TestClient

from backend.agent import orchestrator, planner
from backend.main import app
from backend.memory import project_store
from backend.spec import compose as B
from backend.spec import memory as M
from backend.storage import db
from backend.tools.project_files import ProjectFiles

client = TestClient(app)


def _wait(tid, timeout=30):
    end = time.time() + timeout
    while time.time() < end:
        t = client.get(f"/tasks/{tid}").json()
        if t["status"] in db.TERMINAL:
            return t
        time.sleep(0.1)
    raise AssertionError("task did not finish")


def _new(brief, **kw):
    r = client.post("/projects", json={"brief": brief, **kw})
    assert r.status_code == 200, r.text
    return r.json()


def test_creation_builds_spec_and_memory_without_tokens():
    r = _new("College management system with student attendance", mode="hybrid", prefs={"backend": "spring", "database": "mysql"})
    pid = r["project_id"]
    assert r["spec"]["kind"] == "management" and "Student" in r["spec"]["entities"] and r["spec"]["routes"] > 10
    spec = client.get(f"/projects/{pid}/spec").json()
    assert spec["stack"]["backend"] == "spring" and spec["data"]["database"] == "mysql"
    mem = client.get(f"/projects/{pid}/memory").json()
    assert mem["check"]["consistent"] and mem["memory"]["stack"]["backend"] == "spring"
    topics = {d["topic"] for d in mem["memory"]["decisions"]}
    assert {"frontend", "backend", "database"} <= topics
    assert next(d for d in mem["memory"]["decisions"] if d["topic"] == "backend")["by"] == "user"
    cmds = mem["memory"]["conventions"]["commands"]["backend"]
    assert cmds["dev"] == "./mvnw spring-boot:run" and cmds["verified"] is True           # Spring generator is ready (v2 phase 5): verified follows catalog status
    assert ProjectFiles(pid).hash(".agent/spec.json")


def test_legacy_request_without_mode_unchanged_but_has_spec():
    r = _new("fitness landing page")
    assert "spec" not in r and set(r) == {"project_id"}
    spec = client.get(f"/projects/{r['project_id']}/spec").json()
    assert spec["stack"]["frontend"] == "html" and spec["api"]["routes"] == []


def test_preview_is_stateless_and_validates():
    ok = client.post("/spec/preview", json={"brief": "online store with login", "mode": "automatic"}).json()
    assert ok["ok"] and ok["spec"]["kind"] == "ecommerce" and ok["resolution"]["stack"]["backend"] != "none"
    before = len(client.get("/projects").json())
    bad = client.post("/spec/preview", json={"brief": "x", "mode": "manual", "prefs": {"frontend": "html", "frontend_lang": "ts"}}).json()
    assert bad["ok"] is False and bad["spec"] is None and bad["resolution"]["errors"]
    assert len(client.get("/projects").json()) == before
    assert client.post("/spec/preview", json={"brief": "", "mode": "automatic"}).status_code == 422
    assert client.post("/spec/preview", json={"brief": "store with login", "overrides": {"nope": 1}}).status_code == 422


def test_overrides_persist_and_survive_a_rebuild():
    pid = _new("online store with login and checkout", mode="automatic")["project_id"]
    r = client.put(f"/projects/{pid}/spec", json={"overrides": {"features": ["Wishlist", "Gift cards"]}})
    assert r.status_code == 200 and r.json()["features"] == ["Wishlist", "Gift cards"]
    stack = client.get(f"/projects/{pid}/stack").json()["stack"]
    client.put(f"/projects/{pid}/stack", json={"mode": "hybrid", "prefs": {**stack, "database": "mysql"}})
    spec = client.get(f"/projects/{pid}/spec").json()
    assert spec["features"] == ["Wishlist", "Gift cards"] and spec["data"]["database"] == "mysql"   # edits kept, stack change applied
    assert any(d["topic"] == "database" and d["decision"] == "MySQL" for d in client.get(f"/projects/{pid}/memory").json()["memory"]["decisions"])
    assert client.put(f"/projects/{pid}/spec", json={"overrides": {"pages": []}}).status_code == 422
    assert client.put(f"/projects/{pid}/spec", json={"overrides": {}}).json()["features"] != ["Wishlist", "Gift cards"]


def test_stack_change_updates_spec_and_memory_and_records_the_decision():
    pid = _new("analytics dashboard with login", mode="automatic")["project_id"]
    mem0 = client.get(f"/projects/{pid}/memory").json()["memory"]
    r = client.put(f"/projects/{pid}/stack", json={"mode": "hybrid", "prefs": {"backend": "fastapi", "database": "postgresql"}})
    assert r.status_code == 200, r.text
    mem = client.get(f"/projects/{pid}/memory").json()
    assert mem["check"]["consistent"] and mem["memory"]["stack"]["backend"] == "fastapi"
    be = [d for d in mem["memory"]["decisions"] if d["topic"] == "backend"]
    assert be[-1]["decision"] == "Python + FastAPI" and len(mem["memory"]["decisions"]) >= len(mem0["decisions"])


def test_decisions_are_deduplicated_redacted_and_capped():
    pid = _new("portfolio site")["project_id"]
    a = client.post(f"/projects/{pid}/decisions", json={"topic": "naming", "decision": "kebab-case files"}).json()
    b = client.post(f"/projects/{pid}/decisions", json={"topic": "naming", "decision": "kebab-case files"}).json()
    assert a["recorded"] and not b["recorded"]
    c = client.post(f"/projects/{pid}/decisions", json={"topic": "keys", "decision": "use api_key=sk-abcdefghijklmnop1234567890"}).json()
    assert "sk-abcdefghijklmnop" not in json.dumps(c) and "[REDACTED]" in json.dumps(c)
    for i in range(60):
        client.post(f"/projects/{pid}/decisions", json={"topic": f"t{i}", "decision": "d"})
    assert len(client.get(f"/projects/{pid}/memory").json()["memory"]["decisions"]) == M.MAX_DECISIONS


def test_memory_has_no_secrets_for_a_full_stack_project():
    pid = _new("online store with login and razorpay payments", mode="automatic")["project_id"]
    raw = ProjectFiles(pid).read(".agent/memory.json") + ProjectFiles(pid).read(".agent/spec.json")
    for forbidden in ("sk-", "BEGIN PRIVATE KEY", "postgres://", "AKIA"):
        assert forbidden not in raw
    spec = json.loads(ProjectFiles(pid).read(".agent/spec.json"))
    assert all(v["placeholder"] for v in spec["env"]) and not any("password@" in json.dumps(v) and v["scope"] == "public" for v in spec["env"])


def test_drift_detection_and_sync():
    pid = _new("personal portfolio")["project_id"]
    s = project_store.load(pid)
    pf = ProjectFiles(pid)
    pf.write("index.html", "<h1>x</h1>")
    s.sections_done = ["hero"]
    project_store.save(s)
    chk = client.get(f"/projects/{pid}/memory").json()["check"]
    assert not chk["consistent"] and any(d["kind"] == "files" for d in chk["drift"])
    s.brief = "personal portfolio for a photographer"                  # brief changed -> spec is stale
    project_store.save(s)
    kinds = {d["kind"] for d in M.check(s)["drift"]}
    assert "spec" in kinds
    after = client.post(f"/projects/{pid}/memory/sync").json()
    assert after["check"]["consistent"], after["check"]
    (pf.root / "index.html").unlink()
    s = project_store.load(pid)
    assert any("index.html" in d["msg"] for d in M.check(s)["drift"])


def test_ensure_skips_rebuild_when_nothing_changed():
    pid = _new("personal portfolio")["project_id"]
    s = project_store.load(pid)
    spec1, changed1 = B.ensure(s)
    spec2, changed2 = B.ensure(s)
    assert not changed1 and not changed2 and spec1 == spec2
    s.brief += " with a blog"
    assert B.ensure(s)[1] is True


def test_stale_invalid_overrides_never_block_generation():
    pid = _new("personal portfolio")["project_id"]
    pf = ProjectFiles(pid)
    spec = json.loads(pf.read(".agent/spec.json"))
    spec["overrides"] = {"pages": []}
    pf.write(".agent/spec.json", json.dumps(spec))
    s = project_store.load(pid)
    out, changed = B.ensure(s)
    assert changed and out["overrides"] == {}


def test_pipeline_wires_spec_into_generation_and_report():
    pid = _new("Analytics dashboard for a sales team", mode="automatic", prefs={})["project_id"]
    s = project_store.load(pid)
    # Keep this pipeline test fully offline: React verification invokes npm install,
    # which needs an external package registry. HTML generation exercises the same
    # spec/memory/verification wiring without an unrelated network dependency.
    s.stack_config["stack"].update({"frontend": "html", "frontend_lang": "js", "backend": "none", "backend_lang": "none", "database": "none", "orm": "none", "auth": "none"})
    s.stack = "html"
    project_store.save(s)
    tid = client.post(f"/projects/{pid}/tasks", json={"kind": "generate"}).json()["id"]
    t = _wait(tid)
    assert t["status"] == "succeeded", t
    events = client.get(f"/tasks/{tid}/events").json()
    assert any(e["stage"] == "spec" and "dashboard" in e["msg"] for e in events)
    r = client.get(f"/projects/{pid}").json()
    rep = json.loads(ProjectFiles(pid).read(".agent/report.json"))
    assert rep["spec"]["kind"] == "dashboard" and rep["spec"]["memory_consistent"] is True
    assert project_store.load(pid).layout == "dashboard"
    assert M.check(project_store.load(pid))["consistent"]


def test_layout_follows_the_spec_kind_but_never_overrides_the_style_tag():
    assert planner.layout_for("college management portal", "management") == "app"      # data-management apps get the real app shell (autopilot phase 5)
    assert planner.layout_for("my work", "portfolio") == "portfolio"
    assert planner.layout_for("anything", None) == "landing"
    assert planner.layout_for("college portal\n\nDesign style: Premium SaaS. Animation intensity: medium", "management") == "app"   # data-management kinds always get the app shell; a style tag only restyles it
    assert planner.layout_for("x\n\nDesign style: Analytics dashboard. Animation intensity: low", "landing") == "dashboard"


def test_unknown_project_and_busy_project_are_rejected():
    assert client.get("/projects/nope/spec").status_code == 404
    assert client.get("/projects/nope/memory").status_code == 404
    pid = _new("personal portfolio")["project_id"]
    db.create_task("busy-task-1", pid, "generate", {})                      # an unfinished task blocks spec edits
    assert client.put(f"/projects/{pid}/spec", json={"overrides": {}}).status_code == 409
    assert client.post(f"/projects/{pid}/memory/sync").status_code == 409

import io
import time
import zipfile

import httpx
import pytest
from fastapi.testclient import TestClient

from backend.agent import context, llm, schemas, tasks
from backend.main import app
from backend.storage import checkpoints, db
from backend.tools.project_files import ProjectFiles
from backend.tools.redact import redact

client = TestClient(app)


def _project(brief="fitness app landing page"):
    r = client.post("/projects", json={"brief": brief})
    assert r.status_code == 200, r.text
    return r.json()["project_id"]


def _wait(tid, timeout=20):
    end = time.time() + timeout
    while time.time() < end:
        t = client.get(f"/tasks/{tid}").json()
        if t["status"] in db.TERMINAL:
            return t
        time.sleep(0.1)
    raise AssertionError("task did not finish")


# ---- API validation
def test_health_and_validation():
    assert client.get("/health").json()["ok"] is True
    assert client.post("/projects", json={"brief": "x"}).status_code == 422
    assert client.get("/projects/nope/tasks").status_code == 404
    pid = _project()
    assert client.post(f"/projects/{pid}/tasks", json={"kind": "bogus"}).status_code == 422
    assert client.post(f"/projects/{pid}/tasks", json={"kind": "edit"}).status_code == 422
    assert client.post(f"/projects/{pid}/tasks", json={"kind": "generate", "force": True}).status_code == 400


def test_settings_validation_and_audit():
    assert client.put("/settings", json={"ollama_base_url": "ftp://x"}).status_code == 422
    assert client.put("/settings", json={"max_repair_loops": 99}).status_code == 422
    r = client.put("/settings", json={"ollama_model": "qwen2.5-coder:7b", "max_repair_loops": 3})
    assert r.status_code == 200 and r.json()["max_repair_loops"] == 3


# ---- Ollama failures (real HTTP errors, mocked transport)
def test_ollama_offline_status(monkeypatch):
    def boom(*a, **k):
        raise httpx.ConnectError("refused")
    monkeypatch.setattr(httpx, "get", boom)
    st = client.get("/ollama/status").json()
    assert st["reachable"] is False and "ollama serve" in st["error"]
    assert client.get("/ollama/models").status_code == 503


def test_ollama_status_model_missing(monkeypatch):
    class R:
        def raise_for_status(self): pass
        def json(self): return {"models": [{"name": "llama3:latest"}]}
    monkeypatch.setattr(httpx, "get", lambda *a, **k: R())
    st = llm.status()
    assert st["reachable"] and not st["model_available"] and "ollama pull" in st["error"]


def test_invalid_model_response_retries_then_fails(monkeypatch):
    monkeypatch.setattr("backend.config.MOCK_LLM", False)
    calls = []

    def fake_chat(system, user, model, max_tokens, s):
        calls.append(user)
        return "this is not json", {"in": 1, "out": 1}
    monkeypatch.setattr(llm, "_chat", fake_chat)
    with pytest.raises(llm.OllamaError) as e:
        llm.call_json("section", "sys", "SECTION: hero", schema=schemas.SectionOut)
    assert e.value.code == "bad_response" and len(calls) == 2 and "invalid" in calls[1]


def test_schema_rejects_wrong_shape(monkeypatch):
    monkeypatch.setattr("backend.config.MOCK_LLM", False)
    replies = iter(['{"html": "x"}', '{"html": "<section id=\\"a\\">ok content</section>", "css": ""}'])
    monkeypatch.setattr(llm, "_chat", lambda *a, **k: (next(replies), {"in": 5, "out": 7}))
    data, usage = llm.call_json("section", "s", "u", schema=schemas.SectionOut)
    assert data["html"].startswith("<section") and usage == {"in": 10, "out": 14}


# ---- file safety
@pytest.mark.parametrize("bad", ["../x.txt", "..\\x.txt", "/etc/passwd", "C:\\win.ini", "a/../../b", "a\0b"])
def test_path_traversal_blocked(bad):
    pid = _project()
    with pytest.raises(ValueError):
        ProjectFiles(pid).write(bad, "x")
    assert client.get(f"/projects/{pid}/file", params={"path": bad}).status_code == 404


def test_atomic_write_leaves_no_temp():
    pid = _project()
    pf = ProjectFiles(pid)
    pf.write("a/b.txt", "hi")
    assert pf.read("a/b.txt") == "hi" and not list(pf.root.rglob("*.tmp"))


def test_redaction():
    t = redact("api_key=sk-abcdefghijklmnop1234 Authorization: Bearer abc123456789 password: hunter2222")
    assert "sk-abc" not in t and "hunter2222" not in t and "abc123456789" not in t


# ---- tasks end to end (mock model)
def test_generate_task_streams_and_records():
    pid = _project()
    r = client.post(f"/projects/{pid}/tasks", json={"kind": "generate"})
    assert r.status_code == 202
    tid = r.json()["id"]
    t = _wait(tid)
    assert t["status"] in ("succeeded", "completed_with_issues") and t["checkpoint_id"]
    stages = {e["stage"] for e in client.get(f"/tasks/{tid}/events").json()}
    assert {"queue", "checkpoint", "plan", "code", "done"} <= stages
    sse = client.get(f"/tasks/{tid}/stream").text
    assert "event: progress" in sse and "event: end" in sse
    assert client.get(f"/projects/{pid}/summaries").json()
    assert "index.html" in ProjectFiles(pid).tree()


def test_project_busy_returns_409():
    pid = _project()
    db.create_task("busy1", pid, "generate", {})
    r = client.post(f"/projects/{pid}/tasks", json={"kind": "verify"})
    assert r.status_code == 409
    db.update_task("busy1", status="failed")


def test_cancellation_stops_task(monkeypatch):
    pid = _project()
    started = []

    def slow(pid_, force=False, tr=None):
        started.append(1)
        for _ in range(100):
            context.check()
            time.sleep(0.05)
        return {}
    monkeypatch.setattr("backend.agent.orchestrator.run", slow)
    tid = client.post(f"/projects/{pid}/tasks", json={"kind": "generate"}).json()["id"]
    while not started:
        time.sleep(0.05)
    assert client.post(f"/tasks/{tid}/cancel").status_code == 200
    assert _wait(tid)["status"] == "cancelled"


def test_ollama_offline_fails_task_with_clear_message(monkeypatch):
    pid = _project()
    monkeypatch.setattr("backend.config.MOCK_LLM", False)

    def offline(*a, **k):
        raise llm.OllamaError("offline", "Ollama is not reachable at http://localhost:11434. Start it with: ollama serve")
    monkeypatch.setattr(llm, "_chat", offline)
    t = _wait(client.post(f"/projects/{pid}/tasks", json={"kind": "generate"}).json()["id"])
    assert t["status"] == "failed" and "[offline]" in t["error"]


def test_repair_loops_respect_setting(monkeypatch):
    from backend.agent import orchestrator
    pid = _project()
    client.put("/settings", json={"max_repair_loops": 2})
    client.post(f"/projects/{pid}/tasks", json={"kind": "generate"})
    _wait(db.list_tasks(pid)[0]["id"])
    seen = []
    monkeypatch.setattr("backend.engines.repair_engine.fix", lambda pf, st, fx, *a: (seen.append(1), {"in": 0, "out": 0})[1])
    monkeypatch.setattr(orchestrator, "collect_issues", lambda pf, st, wb, *a: ([{"sid": "hero", "msg": "bad"}], "skipped", {}))
    res = orchestrator.verify(pid)
    # A no-op repair is fingerprinted; retrying the same source does not create progress.
    assert len(seen) == 1 and res["issues"]
    assert any(x.get("outcome") == "no_progress_same_source" for x in res.get("repair_log", []))
    client.put("/settings", json={"max_repair_loops": 3})


# ---- checkpoints / restore / export
def test_checkpoint_restore_requires_confirm_and_keeps_safety_copy():
    pid = _project()
    pf = ProjectFiles(pid)
    pf.write("index.html", "<html>v1</html>")
    cid = client.post(f"/projects/{pid}/checkpoints").json()["id"]
    pf.write("index.html", "<html>v2</html>")
    pf.write("extra.txt", "x")
    assert client.post(f"/projects/{pid}/checkpoints/{cid}/restore").status_code == 400
    r = client.post(f"/projects/{pid}/checkpoints/{cid}/restore", params={"confirm": True})
    assert r.status_code == 200
    assert pf.read("index.html") == "<html>v1</html>" and "extra.txt" not in pf.tree()
    assert any("before restore" in c["label"] for c in client.get(f"/projects/{pid}/checkpoints").json())
    assert client.post(f"/projects/{pid}/checkpoints/zzz/restore", params={"confirm": True}).status_code == 404


def test_restore_rejects_malicious_archive():
    pid = _project()
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("../evil.txt", "x")
    p = checkpoints.config.CHECKPOINT_DIR / pid
    p.mkdir(parents=True, exist_ok=True)
    (p / "evil.zip").write_bytes(buf.getvalue())
    db.add_checkpoint("evil", pid, "evil", None, p / "evil.zip", 1)
    r = client.post(f"/projects/{pid}/checkpoints/evil/restore", params={"confirm": True})
    assert r.status_code == 400 and "unsafe" in r.json()["detail"]


def test_export_excludes_agent_internals():
    pid = _project()
    ProjectFiles(pid).write("index.html", "<html></html>")
    ProjectFiles(pid).write(".agent/state.json", "{}")
    r = client.get(f"/projects/{pid}/export")
    assert r.status_code == 200
    names = zipfile.ZipFile(io.BytesIO(r.content)).namelist()
    assert "index.html" in names and not any(n.startswith(".agent") for n in names)


def test_recover_interrupted_tasks():
    pid = _project()
    db.create_task("stale1", pid, "generate", {})
    db.update_task("stale1", status="running")
    assert db.recover_interrupted() >= 1
    assert db.get_task("stale1")["status"] == "failed"

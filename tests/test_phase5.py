"""Phase 5: repo understanding + persistent task memory."""
import os
os.environ["MOCK_LLM"] = "1"
os.environ["USE_BROWSER"] = "0"
import pytest
from fastapi.testclient import TestClient

from backend.agent.state import AgentState
from backend.main import app
from backend.memory import project_store, task_memory
from backend.repo import mapper
from backend.storage import db
from backend.tools.project_files import ProjectFiles

c = TestClient(app)


def _proj(pid):
    project_store.save(AgentState(pid, "demo app"))
    db.upsert_project(pid, "demo app")
    pf = ProjectFiles(pid)
    pf.write("backend/app/main.py", "from .service import make\nimport os\n\nclass App:\n    pass\n\ndef run():\n    return make()\n")
    pf.write("backend/app/service.py", "def make():\n    return 1\n\nasync def later():\n    pass\n")
    pf.write("backend/requirements.txt", "fastapi==0.1\npytest>=7\n")
    pf.write("backend/tests/test_main.py", "from app.main import run\n")
    pf.write("src/main.tsx", "import App from './App'\nimport React from 'react'\nexport const x = 1\n")
    pf.write("src/App.tsx", "export default function App() { return null }\nexport function Helper() {}\n")
    pf.write("package.json", '{"name":"web","scripts":{"dev":"vite","build":"vite build"},"dependencies":{"react":"1"}}')
    # Simulate an existing local secrets file; the public ProjectFiles API correctly blocks writing it.
    (pf.root / ".env").write_text("SECRET_KEY=supersecret123456", encoding="utf-8")
    pf.write("broken.py", "def (:\n")
    return pf


def test_map_symbols_imports_and_secrets():
    pf = _proj("p5a")
    m = mapper.build("p5a")
    assert "backend/app/main.py" in m["files"] and ".env" not in m["files"]          # secrets never mapped
    assert m["files"]["backend/app/main.py"]["sym"] == ["App", "run"]
    assert m["files"]["backend/app/service.py"]["sym"] == ["make", "later"]
    assert "backend/app/service.py" in m["files"]["backend/app/main.py"]["use"]       # relative py import resolved
    assert "src/App.tsx" in m["files"]["src/main.tsx"]["use"]                         # relative ts import resolved
    assert set(m["files"]["src/App.tsx"]["sym"]) >= {"App", "Helper"}
    assert m["files"]["broken.py"]["sym"] == []                                       # syntax error tolerated
    assert "src/main.tsx" in m["entries"] and "backend/app/main.py" in m["entries"]
    kinds = {x["kind"] for x in m["manifests"]}
    assert kinds == {"npm", "pip"} and "backend/tests/test_main.py" in m["tests"]
    assert m["langs"]["py"] >= 3 and any(p == "backend/app/service.py" for p, _ in m["hubs"])
    assert "supersecret" not in mapper.compact("p5a") and len(mapper.compact("p5a", 300)) <= 300


def test_incremental_and_stale():
    pf = _proj("p5b")
    m1 = mapper.build("p5b")
    assert not mapper.stale("p5b")
    pf.write("backend/app/service.py", "def make():\n    return 2\n\ndef extra():\n    pass\n")
    assert mapper.stale("p5b")
    m2 = mapper.get("p5b")                                                             # auto-rebuild when stale
    assert m2["files"]["backend/app/service.py"]["sym"] == ["make", "extra"]
    assert m2["files"]["src/App.tsx"] is not None and m2["files"]["src/App.tsx"]["h"] == m1["files"]["src/App.tsx"]["h"]
    assert not mapper.stale("p5b")


def test_search_and_outline():
    _proj("p5c")
    hits = mapper.search("p5c", "helper app")
    assert hits[0]["path"] == "src/App.tsx" or any(h["path"] == "src/App.tsx" for h in hits)
    assert mapper.search("p5c", "zzzzqq") == [] and mapper.search("p5c", "") == []
    assert mapper.outline("p5c", "nope") is None


def test_task_memory_lifecycle():
    _proj("p5d")
    task_memory.record_task("p5d", "t1", "generate", {"issues": ["nav overlaps hero"], "sections_done": ["a"], "sections_total": 2})
    assert [r["text"] for r in db.list_memory("p5d", "next", "open")] == ["Resolve: nav overlaps hero"]
    task_memory.record_task("p5d", "t1", "generate", {"issues": ["nav overlaps hero"]})        # duplicate not stored twice
    assert len(db.list_memory("p5d", "next")) == 1
    ctx = task_memory.context("p5d")
    assert "OPEN: Resolve: nav overlaps hero" in ctx and "FAILED:" in ctx and "LANGS:" in ctx
    task_memory.record_task("p5d", "t2", "verify", {"issues": []})                             # clean run closes unresolved items
    assert db.list_memory("p5d", "next", "open") == []
    task_memory.record_task("p5d", "t3", "edit", None, "RuntimeError: boom")
    assert any("boom" in r["text"] for r in db.list_memory("p5d", "failure"))
    r = task_memory.resume("p5d")
    assert r["next"] and "repo_stale" in r


def test_memory_cap_redaction_and_validation():
    _proj("p5e")
    for i in range(db.MEM_CAP + 20):
        db.add_memory("p5e", "t", "note", f"n{i}")
    assert len(db.list_memory("p5e", limit=1000)) == db.MEM_CAP
    db.add_memory("p5e", "t", "note", "api key sk-abcdefghijklmnopqrstuvwxyz0123456789 leaked")
    assert "sk-abcdefghijklmnopqrstuvwxyz" not in db.list_memory("p5e", limit=1)[0]["text"]
    assert db.add_memory("p5e", "t", "bogus", "x") is None and db.add_memory("p5e", "t", "note", "  ") is None


def test_api():
    _proj("p5f")
    r = c.get("/projects/p5f/repo").json()
    assert r["stats"]["files"] >= 8 and "files" not in r
    assert "files" in c.get("/projects/p5f/repo?full=true").json()
    assert c.post("/projects/p5f/repo/refresh?force=true").status_code == 200
    assert c.get("/projects/p5f/repo/search", params={"q": "service"}).json()[0]["path"].endswith("service.py")
    assert c.get("/projects/p5f/repo/file", params={"path": "src/App.tsx"}).status_code == 200
    assert c.get("/projects/p5f/repo/file", params={"path": "x"}).status_code == 404
    mid = c.post("/projects/p5f/memory/tasks", json={"kind": "next", "text": "add auth tests"}).json()["id"]
    assert c.post("/projects/p5f/memory/tasks", json={"kind": "failure", "text": "nope"}).status_code == 422
    assert [x["text"] for x in c.get("/projects/p5f/memory/tasks?status=open").json()] == ["add auth tests"]
    assert c.get("/projects/p5f/resume").json()["next"][0]["id"] == mid
    assert "OPEN: add auth tests" in c.get("/projects/p5f/context").json()["context"]
    assert c.post(f"/projects/p5f/memory/tasks/{mid}/close").status_code == 200
    assert c.post(f"/projects/p5f/memory/tasks/{mid}/close").status_code == 404
    assert c.get("/projects/nope/repo").status_code == 404
    assert c.get("/projects/..%2Fx/repo").status_code == 404


def test_task_pipeline_records_memory():
    """Real generate task (mock LLM): repo map + task memory are produced by the task runner."""
    from backend.agent import tasks
    project_store.save(AgentState("p5g", "fitness app landing page"))
    db.upsert_project("p5g", "fitness app landing page")
    t = tasks.submit("p5g", "generate", {"force": True})
    import time
    for _ in range(300):
        if db.get_task(t["id"])["status"] in db.TERMINAL:
            break
        time.sleep(0.1)
    assert db.get_task(t["id"])["status"] in ("succeeded", "completed_with_issues")
    assert mapper.load("p5g") and mapper.load("p5g")["stats"]["files"] > 0
    assert any(r["kind"] == "note" and r["text"].startswith("generate") for r in db.list_memory("p5g"))

"""Security and behavior tests for the project-aware debugger API."""
from fastapi.testclient import TestClient

from backend import config
from backend.main import app
from backend.tools.project_files import ProjectFiles
from backend.storage import db

client = TestClient(app)
HEADERS = {"Origin": config.CORS_ORIGINS[0]}


def _project() -> str:
    r = client.post("/projects", json={"brief": "Debugger API regression project"}, headers=HEADERS)
    assert r.status_code == 200, r.text
    return r.json()["project_id"]


def test_debug_apply_safe_patch_and_checkpoint(monkeypatch):
    pid = _project()
    pf = ProjectFiles(pid)
    pf.write("src/App.tsx", "export const label = 'Broken';\n")

    def fake_call(_kind, _system, _user, _model, _tokens):
        return ({"summary": "The label is wrong.",
                 "diagnostics": [{"severity": "warning", "file": "src/App.tsx", "line": 1, "message": "Unexpected label"}],
                 "patches": [{"file": "src/App.tsx", "old": "'Broken'", "new": "'Fixed'", "reason": "Correct the literal"}]},
                {"in": 12, "out": 6})

    monkeypatch.setattr("backend.api.debug.llm.call_json", fake_call)
    r = client.post(f"/projects/{pid}/debug", json={"error_text": "src/App.tsx:1 unexpected label", "apply_fixes": True}, headers=HEADERS)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["summary"] == "The label is wrong."
    assert data["applied"][0]["file"] == "src/App.tsx"
    assert "Fixed" in pf.read("src/App.tsx")
    assert any("checkpoint" in row["label"].lower() for row in db.list_checkpoints(pid))


def test_debug_analyze_only_does_not_change_files(monkeypatch):
    pid = _project()
    pf = ProjectFiles(pid)
    pf.write("src/App.tsx", "export const label = 'Keep';\n")

    def fake_call(_kind, _system, _user, _model, _tokens):
        return ({"summary": "Found a likely issue.", "diagnostics": [],
                 "patches": [{"file": "src/App.tsx", "old": "'Keep'", "new": "'Changed'", "reason": "test"}]}, {"in": 1, "out": 1})

    monkeypatch.setattr("backend.api.debug.llm.call_json", fake_call)
    r = client.post(f"/projects/{pid}/debug", json={"error_text": "src/App.tsx is wrong", "apply_fixes": False}, headers=HEADERS)
    assert r.status_code == 200, r.text
    assert pf.read("src/App.tsx").find("'Keep'") >= 0
    assert not r.json()["applied"]
    assert r.json()["rejected"]


def test_debug_rejects_patch_to_unprovided_or_protected_file(monkeypatch):
    pid = _project()
    pf = ProjectFiles(pid)
    pf.write("src/App.tsx", "export const label = 'Keep';\n")
    pf.write("src/other.ts", "export const secret = 'unique-value';\n")

    def fake_call(_kind, _system, _user, _model, _tokens):
        return ({"summary": "Test", "diagnostics": [],
                 "patches": [{"file": "src/other.ts", "old": "'unique-value'", "new": "'edited'", "reason": "must not touch an unshared file"}]}, {"in": 1, "out": 1})

    monkeypatch.setattr("backend.api.debug.llm.call_json", fake_call)
    r = client.post(f"/projects/{pid}/debug", json={"error_text": "src/App.tsx has issue", "apply_fixes": True}, headers=HEADERS)
    assert r.status_code == 200, r.text
    assert "unique-value" in pf.read("src/other.ts")
    assert not r.json()["applied"]

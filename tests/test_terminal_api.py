"""Terminal API allows reviewed command shapes only; it never invokes a shell."""
from fastapi.testclient import TestClient

from backend import config
from backend.main import app

client = TestClient(app)
HEADERS = {"Origin": config.CORS_ORIGINS[0]}


def _project() -> str:
    r = client.post("/projects", json={"brief": "Terminal API testing website"}, headers=HEADERS)
    assert r.status_code == 200, r.text
    return r.json()["project_id"]


def test_terminal_rejects_shell_operators():
    pid = _project()
    r = client.post(f"/projects/{pid}/terminal", json={"args": ["npm", "run", "build;", "echo", "bad"]}, headers=HEADERS)
    assert r.status_code == 400


def test_terminal_requires_explicit_permission_for_install(monkeypatch):
    pid = _project()
    monkeypatch.setattr("backend.api.terminal.terminal_tools.allowed", lambda args: args == ["npm", "install", "--no-audit"])
    r = client.post(f"/projects/{pid}/terminal", json={"args": ["npm", "install", "--no-audit"]}, headers=HEADERS)
    assert r.status_code == 400 and "confirm=true" in r.text
    monkeypatch.setattr("backend.api.terminal.terminal_tools.run", lambda args, cwd, timeout, max_out: {"code": 0, "out": "ok"})
    r = client.post(f"/projects/{pid}/terminal", json={"args": ["npm", "install", "--no-audit"], "confirm": True}, headers=HEADERS)
    assert r.status_code == 200, r.text
    assert r.json()["ok"] is True

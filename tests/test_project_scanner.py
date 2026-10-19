"""Regression tests for bounded, secret-safe project scanning."""
from fastapi.testclient import TestClient

from backend import config
from backend.main import app
from backend.tools.project_files import ProjectFiles

client = TestClient(app)
HEADERS = {"Origin": config.CORS_ORIGINS[0]}


def _project() -> str:
    r = client.post("/projects", json={"brief": "Project scan testing website"}, headers=HEADERS)
    assert r.status_code == 200, r.text
    return r.json()["project_id"]


def test_project_scan_detects_stack_entry_and_routes():
    pid = _project()
    pf = ProjectFiles(pid)
    pf.write("package.json", '{"name":"scan-fixture","scripts":{"build":"vite build"},"dependencies":{"react":"18.0.0","vite":"5.0.0"}}')
    pf.write("src/main.tsx", "import React from 'react';\n")
    pf.write("src/App.tsx", "export default function App() { return <Route path='/dashboard' /> }\n")
    pf.write("backend/main.py", "@app.get('/healthz')\ndef healthz():\n    return {'ok': True}\n")
    secret_path = pf.root / ".env"
    secret_path.write_text("API_SECRET=must-not-appear", encoding="utf-8")

    r = client.get(f"/projects/{pid}/scan", headers=HEADERS)
    secret_path.unlink(missing_ok=True)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["files_scanned"] >= 4
    assert "React" in data["frameworks"]
    assert "src/main.tsx" in data["entry_points"]
    assert "/dashboard" in data["routes"]
    assert any(x["path"] == "/healthz" and x["method"] == "GET" for x in data["api_endpoints"])
    assert ".env" not in str(data) and "must-not-appear" not in str(data)

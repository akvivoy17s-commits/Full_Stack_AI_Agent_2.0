"""Phase 3A backend generation through the API (needs fastapi, like the other API tests)."""
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)
EXPRESS = {"frontend": "react", "frontend_lang": "ts", "backend": "express", "backend_lang": "js", "database": "sqlite", "auth": "jwt"}


def _new(prefs):
    r = client.post("/projects", json={"brief": "college management system with student login and courses", "mode": "manual", "prefs": prefs})
    assert r.status_code == 200, r.text
    return r.json()["project_id"]


def test_endpoint_generates_backend_for_a_covered_stack():
    pid = _new(EXPRESS)
    assert client.get(f"/projects/{pid}/backend").json()["coverage"]["ready"] is True
    out = client.post(f"/projects/{pid}/backend").json()
    assert out["generated"] and out["routes"] > 10 and "npm test" in out["commands"]["test"]
    files = client.get(f"/projects/{pid}/files").json()
    assert "backend/src/app.js" in files and "backend/.env.example" in files and ".env" not in files
    assert client.post(f"/projects/{pid}/backend").json()["written"] == []          # second run changes nothing
    assert client.get(f"/projects/{pid}/backend").json()["last"]["generated"] is True


def test_endpoint_reports_gaps_for_an_uncovered_stack():
    pid = _new({**EXPRESS, "backend_lang": "ts"})
    out = client.post(f"/projects/{pid}/backend").json()
    assert out["generated"] is False and any("js only" in g for g in out["gaps"])
    assert not any(f.startswith("backend/") for f in client.get(f"/projects/{pid}/files").json())


def test_endpoint_generates_fastapi_backend():
    pid = _new({**EXPRESS, "backend": "fastapi", "backend_lang": "py"})
    assert client.get(f"/projects/{pid}/backend").json()["coverage"]["ready"] is True
    out = client.post(f"/projects/{pid}/backend").json()
    assert out["generated"] and out["generator"] == "fastapi" and "pytest" in out["commands"]["test"]
    files = client.get(f"/projects/{pid}/files").json()
    assert "backend/app/main.py" in files and "backend/requirements.txt" in files and ".env" not in files


def test_automatic_selection_uses_a_backend_generator_that_is_ready():
    r = client.post("/projects", json={"brief": "Interactive analytics dashboard with team login and user management", "mode": "automatic", "prefs": {}})
    assert r.status_code == 200, r.text
    pid = r.json()["project_id"]
    stack = client.get(f"/projects/{pid}/stack").json()["stack"]
    assert stack["backend"] in {"express", "nestjs", "fastapi", "flask", "django"}
    coverage = client.get(f"/projects/{pid}/backend").json()["coverage"]
    assert coverage["ready"] is True, coverage
    generated = client.post(f"/projects/{pid}/backend").json()
    assert generated["generated"] is True and generated["written"]
    assert client.get(f"/projects/{pid}/memory").json()["check"]["consistent"] is True

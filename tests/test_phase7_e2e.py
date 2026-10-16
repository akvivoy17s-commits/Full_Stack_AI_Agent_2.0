"""Phase 7: frontend <-> backend contract and end-to-end checks of generated backends (real files, real processes, no mocks of the generators)."""
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.tools.project_files import ProjectFiles

client = TestClient(app)
ROOT = Path(__file__).resolve().parents[1]
BRIEF = "college management system with student login and courses"
BASE = {"frontend": "react", "frontend_lang": "ts", "database": "sqlite", "auth": "jwt"}
STACKS = {
    "fastapi": {**BASE, "backend": "fastapi", "backend_lang": "py"},
    "flask": {**BASE, "backend": "flask", "backend_lang": "py"},
    "express": {**BASE, "backend": "express", "backend_lang": "js"},
}


def _routes():
    # openapi paths include routers added with include_router on every FastAPI version
    return [re.compile("^" + re.sub(r"\{[^}]+\}", "[^/]+", p) + "$") for p in app.openapi()["paths"]]


def test_frontend_api_client_only_calls_existing_backend_routes():
    src = (ROOT / "frontend/src/services/api.ts").read_text(encoding="utf-8")
    paths = set()
    for m in re.finditer(r"`\$\{B\}(/[^`?]*)", src):
        paths.add(m.group(1))
    for m in re.finditer(r"post\(\s*[`']([^`'?]*)", src):
        paths.add(m.group(1))
    paths = {re.sub(r"\$\{[^}]+\}", "x", p) for p in paths if p.startswith("/")}
    assert len(paths) > 25, paths
    routes = _routes()
    missing = sorted(p for p in paths if not any(r.match(p) for r in routes))
    assert not missing, f"frontend calls routes the backend does not have: {missing}"


def _project(prefs):
    r = client.post("/projects", json={"brief": BRIEF, "mode": "manual", "prefs": prefs})
    assert r.status_code == 200, r.text
    pid = r.json()["project_id"]
    out = client.post(f"/projects/{pid}/backend").json()
    assert out["generated"], out
    return pid, out


def _dump(pid, dest: Path):
    for f in client.get(f"/projects/{pid}/files").json():
        if f.startswith("backend/"):
            t = dest / f
            t.parent.mkdir(parents=True, exist_ok=True)
            t.write_text(client.get(f"/projects/{pid}/file", params={"path": f}).json()["content"], encoding="utf-8")
    return dest / "backend"


@pytest.mark.parametrize("name", ["fastapi", "flask"])
def test_generated_python_backend_passes_its_own_tests(name, tmp_path):
    for mod in ("sqlalchemy", "bcrypt", "jwt", "flask" if name == "flask" else "fastapi"):
        pytest.importorskip(mod, reason="generated backend dependencies (backend/requirements.txt) are not installed")
    pid, out = _project(STACKS[name])
    root = _dump(pid, tmp_path)
    assert subprocess.run([sys.executable, "-m", "compileall", "-q", str(root)], capture_output=True).returncode == 0
    r = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "tests"], cwd=root, capture_output=True, text=True, timeout=240)
    assert r.returncode == 0, (r.stdout + r.stderr)[-2500:]


@pytest.mark.skipif(not shutil.which("node"), reason="node not installed")
def test_generated_express_backend_is_valid_javascript(tmp_path):
    pid, out = _project(STACKS["express"])
    root = _dump(pid, tmp_path)
    js = [p for p in root.rglob("*.js") if "node_modules" not in p.parts]
    assert js
    bad = [str(p.relative_to(root)) for p in js if subprocess.run(["node", "--check", str(p)], capture_output=True).returncode != 0]
    assert not bad, bad


def test_backend_endpoint_reports_user_edits_kept_and_frontend_fields_exist():
    pid, first = _project(STACKS["fastapi"])
    path = "backend/app/main.py"
    cur = client.get(f"/projects/{pid}/file", params={"path": path}).json()["content"]
    ProjectFiles(pid).write(path, cur + "\n# user edit\n")          # the HTTP editor only allows html/css/js/json/md/svg/txt
    again = client.post(f"/projects/{pid}/backend").json()
    assert path in again["kept"]
    assert "# user edit" in client.get(f"/projects/{pid}/file", params={"path": path}).json()["content"]
    for k in ("generated", "generator", "database", "files", "written", "kept", "routes", "not_generated", "warnings", "commands"):
        assert k in again, k          # BackendResult fields used by BackendPanel.tsx
    info = client.get(f"/projects/{pid}/backend").json()
    assert set(info["coverage"]) >= {"backend", "ready", "gaps", "note"} and info["last"]["generated"] is True

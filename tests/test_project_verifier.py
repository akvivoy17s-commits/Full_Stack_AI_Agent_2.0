"""Regression tests for the backend verification report."""
import json
import uuid

import pytest

from backend.tools import project_verifier
from backend.tools.project_files import ProjectFiles


@pytest.fixture
def pf(tmp_path, monkeypatch):
    monkeypatch.setattr("backend.tools.project_files.GENERATED_DIR", tmp_path)
    return ProjectFiles("verify-" + uuid.uuid4().hex[:8])


def test_static_backend_verification_parses_contracts_and_python(pf):
    pf.write("backend/app/main.py", "def health():\n    return {'ok': True}\n")
    pf.write("backend/openapi.json", json.dumps({"openapi": "3.0.0", "info": {"title": "Demo", "version": "1"}, "paths": {}}))
    pf.write("backend/.agent-manifest.json", json.dumps({"generator": "fastapi", "routes": []}))

    report = project_verifier.verify_backend(pf)

    assert report["status"] == "passed"
    assert {c["name"] for c in report["checks"]} >= {
        "backend static syntax + JSON", "backend generation manifest", "OpenAPI contract"
    }
    assert report["issues"] == []
    assert any(c["status"] == "skipped" and "Deep check not requested" in c["detail"] for c in report["checks"])


def test_static_backend_verification_reports_invalid_python_and_openapi(pf):
    pf.write("backend/app/broken.py", "def broken(:\n    pass\n")
    pf.write("backend/openapi.json", json.dumps({"paths": {}}))

    report = project_verifier.verify_backend(pf)

    assert report["status"] == "failed"
    assert any(i["file"] == "backend/app/broken.py" and "syntax error" in i["message"] for i in report["issues"])
    assert any(i["file"] == "backend/openapi.json" and "OpenAPI" in i["message"] for i in report["issues"])


def test_deep_checks_run_declared_scripts_only_when_dependencies_exist(pf, monkeypatch):
    pf.write("backend/package.json", json.dumps({"name": "demo", "scripts": {"build": "tsc", "test": "node --test"}}))
    (pf.root / "backend" / "node_modules").mkdir()
    pf.write("backend/src/server.js", "console.log('ok')\n")

    calls = []
    monkeypatch.setattr(project_verifier.shutil, "which", lambda name: "/tool" if name == "node" else None)
    def fake_run(args, cwd, timeout=30, max_out=2000):
        calls.append((args, cwd))
        return {"code": 0, "out": "ok"}
    monkeypatch.setattr(project_verifier.terminal, "run", fake_run)

    report = project_verifier.verify_backend(pf, deep=True)

    assert ( ["npm", "run", "build"], str(pf.root / "backend") ) in calls
    assert ( ["npm", "run", "test"], str(pf.root / "backend") ) in calls
    assert any(c["name"] == "backend npm build" and c["status"] == "passed" for c in report["checks"])
    assert any(c["name"] == "backend npm test" and c["status"] == "passed" for c in report["checks"])
    assert not report["blocking_issues"]


def test_deep_checks_do_not_install_missing_node_dependencies(pf, monkeypatch):
    pf.write("backend/package.json", json.dumps({"name": "demo", "scripts": {"test": "node --test"}}))
    calls = []
    monkeypatch.setattr(project_verifier.shutil, "which", lambda _name: None)
    monkeypatch.setattr(project_verifier.terminal, "run", lambda *a, **k: calls.append(a) or {"code": 0, "out": ""})

    report = project_verifier.verify_backend(pf, deep=True)

    assert not calls
    assert any(c["name"] == "backend npm scripts" and c["status"] == "skipped" and "not installed" in c["detail"] for c in report["checks"])
    assert report["blocking_issues"] == []

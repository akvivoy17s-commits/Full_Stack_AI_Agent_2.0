"""Phase 1: file + endpoint security hardening."""
import io
import os
import zipfile

import pytest
from fastapi.testclient import TestClient

from backend import config, security
from backend.main import app
from backend.storage import db
from backend.tools.project_files import ProjectFiles

client = TestClient(app)
GOOD = {"Origin": config.CORS_ORIGINS[0]}


def _pid():
    return client.post("/projects", json={"brief": "security test site"}).json()["project_id"]


# ---- paths
@pytest.mark.parametrize("p", [".agent/x.json", ".Agent/x.json", ".AGENT\\x.json", "a/.agent/x.txt"])
def test_agent_dir_not_writable_any_case(p):
    pid = _pid()
    assert client.put(f"/projects/{pid}/file", json={"path": p.replace(".json", ".txt"), "content": "x"}, headers=GOOD).status_code == 400


@pytest.mark.parametrize("p", ["a.txt:stream", "C:/x.txt", "../x.txt", "/etc/passwd", "a/../../x.txt"])
def test_traversal_and_streams_rejected(p):
    pf = ProjectFiles(_pid())
    with pytest.raises(ValueError):
        pf.write(p, "x")


def test_agent_files_not_readable_via_api():
    pid = _pid()
    assert client.get(f"/projects/{pid}/file", params={"path": ".agent/state.json"}).status_code == 404
    assert client.get(f"/projects/{pid}/file", params={"path": ".AGENT/state.json"}).status_code == 404


def test_oversized_save_and_read_rejected(monkeypatch):
    pid = _pid()
    big = "a" * (config.MAX_FILE_BYTES + 1)
    assert client.put(f"/projects/{pid}/file", json={"path": "a.txt", "content": big}, headers=GOOD).status_code == 422
    ProjectFiles(pid).write("ok.txt", "hello")
    monkeypatch.setattr(config, "MAX_READ_BYTES", 3)
    assert client.get(f"/projects/{pid}/file", params={"path": "ok.txt"}).status_code == 413


def test_symlinks_not_exported_or_listed(tmp_path):
    pid = _pid()
    pf = ProjectFiles(pid)
    pf.write("index.html", "<html></html>")
    secret = tmp_path / "secret.txt"
    secret.write_text("TOP-SECRET")
    try:
        os.symlink(secret, pf.root / "link.txt")
    except (OSError, NotImplementedError):
        pytest.skip("symlinks unavailable")
    assert "link.txt" not in pf.tree()
    z = zipfile.ZipFile(io.BytesIO(client.get(f"/projects/{pid}/export").content))
    assert "link.txt" not in z.namelist() and b"TOP-SECRET" not in b"".join(z.read(n) for n in z.namelist())


# ---- origin / CSRF
def test_cross_origin_and_sandboxed_writes_blocked():
    pid = _pid()
    for origin in ("http://evil.example", "null"):
        r = client.post(f"/projects/{pid}/checkpoints", headers={"Origin": origin})
        assert r.status_code == 403
    assert client.post(f"/projects/{pid}/checkpoints", headers=GOOD).status_code == 201
    assert client.post(f"/projects/{pid}/checkpoints").status_code == 201          # non-browser clients (no Origin) still work
    assert client.get(f"/projects/{pid}", headers={"Origin": "http://evil.example"}).status_code == 200   # reads: CORS already hides the body


def test_preview_is_sandboxed_untrusted_content():
    pid = _pid()
    ProjectFiles(pid).write("index.html", "<script>fetch('/projects')</script>")
    r = client.get(f"/preview/{pid}/index.html")
    assert r.status_code == 200
    assert "sandbox" in r.headers["content-security-policy"] and "allow-same-origin" not in r.headers["content-security-policy"]
    assert r.headers["x-content-type-options"] == "nosniff"


# ---- host + token
def test_host_header_allowlist():
    assert client.get("/health", headers={"Host": "evil.example"}).status_code == 400
    assert client.get("/health", headers={"Host": "localhost:8000"}).status_code == 200


def test_api_token_when_configured(monkeypatch):
    monkeypatch.setattr(config, "API_TOKEN", "s3cret-token")
    assert client.get("/projects").status_code == 401
    assert client.get("/projects", headers={"X-API-Token": "wrong"}).status_code == 401
    assert client.get("/projects", headers={"X-API-Token": "s3cret-token"}).status_code == 200
    assert client.get("/projects", headers={"Authorization": "Bearer s3cret-token"}).status_code == 200
    assert client.get("/projects?token=s3cret-token").status_code == 200
    assert client.get("/health").status_code == 200


# ---- SSRF / settings
@pytest.mark.parametrize("u", ["http://169.254.169.254/latest", "http://metadata.google.internal", "http://user:pw@localhost:11434",
                               "ftp://localhost", "http://0.0.0.0:11434", "file:///etc/passwd"])
def test_bad_model_urls_rejected(u):
    assert client.put("/settings", json={"ollama_base_url": u}, headers=GOOD).status_code == 422
    assert client.post("/ollama/check", json={"base_url": u}, headers=GOOD).status_code == 422


def test_good_model_urls_accepted():
    assert security.validate_base_url("http://localhost:11434/") == "http://localhost:11434"
    assert security.validate_base_url("http://192.168.1.20:11434") == "http://192.168.1.20:11434"


# ---- concurrency + error hygiene
def test_legacy_mutators_blocked_while_task_running():
    pid = _pid()
    db.create_task("busy-p1", pid, "generate", {})
    db.update_task("busy-p1", status="running")
    assert client.post(f"/projects/{pid}/generate", headers=GOOD).status_code == 409
    assert client.post(f"/projects/{pid}/verify", headers=GOOD).status_code == 409
    assert client.put(f"/projects/{pid}/file", json={"path": "a.txt", "content": "x"}, headers=GOOD).status_code == 409
    db.update_task("busy-p1", status="failed")


def test_unhandled_errors_do_not_leak(monkeypatch):
    pid = _pid()
    def boom(_p): raise RuntimeError("/home/secret/path sk-abcdefghijklmnopqrstuvwxyz")
    monkeypatch.setattr("backend.main.project_store.load", boom)
    r = TestClient(app, raise_server_exceptions=False).get(f"/projects/{pid}")
    assert r.status_code == 500 and r.json() == {"detail": "internal error"}

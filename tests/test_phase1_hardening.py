"""Phase 1 hardening: secret-file guard, protected dirs, bounded tree, public endpoints."""
import pytest
from backend.tools.project_files import ProjectFiles, is_secret


@pytest.fixture
def pf(tmp_path, monkeypatch):
    monkeypatch.setattr("backend.tools.project_files.GENERATED_DIR", tmp_path)
    return ProjectFiles("p1")


@pytest.mark.parametrize("name,secret", [(".env", True), ("a/.env.local", True), (".env.production", True), (".env.example", False),
                                         ("x/server.pem", True), ("id_rsa", True), (".npmrc", True), ("src/app.js", False)])
def test_is_secret(name, secret):
    assert is_secret(name) is secret


def test_secret_read_write_blocked(pf):
    with pytest.raises(ValueError):
        pf.write(".env", "KEY=1")
    with pytest.raises(ValueError):
        pf.read("backend/.env.local")
    pf.write("backend/.env.example", "KEY=your-key")      # templates are allowed


def test_protected_dirs_and_traversal(pf):
    for bad in ("node_modules/x.js", ".git/config", "../x.txt", "/etc/passwd", "a/../../x"):
        with pytest.raises(ValueError):
            pf.write(bad, "x")
    pf.write(".agent/memory.json", "{}")                 # internal state still writable by the agent itself


def test_tree_hides_secrets_and_ignored(pf):
    pf.write("a.js", "1")
    pf.write("sub/b.js", "2")
    (pf.root / ".env").write_text("SECRET=1")
    (pf.root / "node_modules").mkdir()
    (pf.root / "node_modules" / "m.js").write_text("x")
    assert pf.tree() == ["a.js", "sub/b.js"]


def test_read_size_limit(pf, monkeypatch):
    pf.write("big.txt", "x")
    monkeypatch.setattr("backend.tools.project_files.MAX_FILE_BYTES", 0)
    with pytest.raises(ValueError):
        pf.read("big.txt")

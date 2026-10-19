"""Phase 2: expanded allowlisted runner — real executions, injection rejection, env scrubbing, check detection."""
import pytest
from backend.tools import terminal as T


@pytest.mark.parametrize("cmd", [
    ["python", "-m", "py_compile", "app/main.py"], ["python", "-m", "pytest", "-q", "tests"], ["python", "-m", "pytest"], ["python", "-m", "pytest", "-q", "-x", "-p", "no:cacheprovider", "tests"],
    ["python", "-m", "compileall", "-q", "."], ["python", "-m", "ruff", "check", "."],
    [".venv/Scripts/python.exe", "-m", "pytest", "-q", "-p", "no:cacheprovider", "tests"],
    [".venv/bin/python", "-m", "compileall", "-q", "."], ["go", "test", "./..."],
    ["mvn", "-q", "-B", "test"], ["npm", "run", "lint"], ["npm", "test"], ["dotnet", "build", "--nologo", "-v", "q"]])
def test_allowed_shapes(cmd):
    assert T.allowed(cmd)


@pytest.mark.parametrize("cmd", [
    ["python", "-c", "import os"], ["python", "script.py"], ["python", "-m", "pip", "install", "x"], ["python", "-m", "py_compile", "../x.py"],
    [".venv/../outside/python", "-m", "pytest"], [".venv/Scripts/python.exe", "-c", "import os"],
    ["python", "-m", "py_compile", "/etc/x.py"], ["python", "-m", "pytest", "--rootdir=/"], ["python", "-m", "pytest", "-c", "/tmp/x.ini"],
    ["python", "-m", "pytest", "--co"], ["python", "-m", "pytest", "-p", "evil"], ["python", "-m", "pytest", "-p"], ["python", "-m", "pytest", "../x"], ["go", "run", "main.go"], ["mvn", "exec:exec"],
    ["npm", "run", "postinstall"], ["npm", "exec", "x"], ["node", "--check", "../x.js"], ["rm", "-rf", "/"], ["bash", "-c", "ls"], []])
def test_rejected_shapes(cmd):
    assert not T.allowed(cmd)


def test_real_py_compile_and_pytest(tmp_path):
    (tmp_path / "ok.py").write_text("x = 1\n")
    (tmp_path / "bad.py").write_text("def f(:\n")
    (tmp_path / "test_a.py").write_text("def test_a():\n    assert 1 == 1\n")
    assert T.run(["python", "-m", "py_compile", "ok.py"], str(tmp_path))["code"] == 0
    bad = T.run(["python", "-m", "py_compile", "bad.py"], str(tmp_path))
    assert bad["code"] != 0 and "SyntaxError" in bad["out"]
    r = T.run(["python", "-m", "pytest", "-q", "-p", "no:cacheprovider"], str(tmp_path), timeout=60)
    assert r["code"] == 0 and "1 passed" in r["out"]


def test_env_scrubbed(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-secretsecretsecret1234")
    monkeypatch.setenv("MY_TOKEN", "tok-abcdefgh12345")
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:password@localhost/db")
    monkeypatch.setenv("PYTHONPATH", "/untrusted/modules")
    monkeypatch.setenv("NODE_OPTIONS", "--require=/untrusted/preload.js")
    monkeypatch.setenv("KEEP_ME", "yes")
    e = T._env()
    assert "OPENAI_API_KEY" not in e and "MY_TOKEN" not in e and "DATABASE_URL" not in e
    assert "PYTHONPATH" not in e and "NODE_OPTIONS" not in e and e["KEEP_ME"] == "yes" and e["CI"] == "1"


def test_unknown_command_raises():
    with pytest.raises(ValueError):
        T.run(["rm", "-rf", "/"], ".")


def test_detect_checks(tmp_path):
    (tmp_path / "package.json").write_text('{"scripts":{"build":"x","lint":"y"}}')
    (tmp_path / "tsconfig.json").write_text("{}")
    (tmp_path / "app.py").write_text("x=1")
    (tmp_path / "tests").mkdir()
    (tmp_path / "go.mod").write_text("module x")
    c = T.detect_checks(tmp_path)
    assert ["npm", "run", "build"] in c and ["npm", "run", "lint"] in c and ["npx", "tsc", "--noEmit"] in c
    assert ["python", "-m", "compileall", "-q", "."] in c and any(x[:3] == ["python", "-m", "pytest"] for x in c)
    assert ["go", "build", "./..."] in c and all(T.allowed(x) for x in c)
    assert T.detect_checks(tmp_path / "empty-missing") == []

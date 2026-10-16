"""Sandboxed command runner: strict allowlist of exact command shapes, no shell, timeout, cancellable, process-tree cleanup."""
import os
import re
import shutil
import signal
import subprocess
import sys
from pathlib import Path

from backend.agent import context
from backend.tools.redact import redact

NPM_FLAGS = {"--no-audit", "--no-fund", "--prefer-offline", "--loglevel=error", "--legacy-peer-deps"}


PY = {"python", "python3", "py"}
PYTEST_FLAGS = {"-q", "-x", "--maxfail=1", "--tb=short"}
_SECRET_ENV = re.compile(r"(?i)(key|token|secret|passw|credential|auth)")


def _rel_ok(a: str, suffix: tuple = ()) -> bool:
    """Relative path argument: no traversal, no absolute path, no option injection."""
    a = a.replace("\\", "/")
    return bool(a) and not a.startswith(("-", "/", "~")) and ".." not in a.split("/") and not re.match(r"^[A-Za-z]:", a) \
        and "\0" not in a and (not suffix or a.endswith(suffix))


def allowed(args: list[str]) -> bool:
    """Only these exact shapes may run (the model can never choose a command)."""
    if not args:
        return False
    exe, rest = args[0], args[1:]
    if exe == "node":
        return len(rest) == 2 and rest[0] == "--check" and _rel_ok(rest[1], (".js", ".mjs", ".cjs"))
    if exe == "npm":
        if rest[:1] in (["install"], ["ci"]):
            return set(rest[1:]) <= NPM_FLAGS
        return rest in (["run", "build"], ["run", "typecheck"], ["run", "lint"], ["run", "test"], ["test"])
    if exe == "npx":
        return rest == ["tsc", "--noEmit"]
    if exe in PY:
        if len(rest) == 3 and rest[:2] == ["-m", "py_compile"]:
            return _rel_ok(rest[2], (".py",))
        if rest[:2] == ["-m", "compileall"]:
            return rest[2:] in ([], ["-q"], ["-q", "."]) or (len(rest) == 4 and rest[2] == "-q" and _rel_ok(rest[3]))
        if rest[:2] == ["-m", "pytest"]:
            tail, paths, i = rest[2:], [], 0
            while i < len(tail):
                a = tail[i]
                if a == "-p":                                   # only the one harmless plugin switch; `-p evil` would import code
                    if tail[i + 1:i + 2] != ["no:cacheprovider"]:
                        return False
                    i += 2
                    continue
                if a in PYTEST_FLAGS:
                    i += 1
                    continue
                if not _rel_ok(a):
                    return False
                paths.append(a)
                i += 1
            return len(paths) <= 3
        if rest[:3] == ["-m", "ruff", "check"]:
            return rest[3:] in ([], ["."])
        return False
    if exe == "go":
        return rest in (["build", "./..."], ["vet", "./..."], ["test", "./..."])
    if exe == "mvn":
        return rest in (["-q", "-B", "compile"], ["-q", "-B", "test"], ["-B", "-q", "test"])
    if exe == "dotnet":
        return rest in (["build", "--nologo", "-v", "q"], ["test", "--nologo", "-v", "q"])
    return False


def _env() -> dict:
    """Child environment without credentials: build/test commands never need the host's secrets."""
    e = {k: v for k, v in os.environ.items() if not _SECRET_ENV.search(k)}
    e.update({"CI": "1", "PYTHONDONTWRITEBYTECODE": "1", "NO_COLOR": "1"})
    return e


def detect_checks(root: Path) -> list[list[str]]:
    """Checks that actually apply to a project directory (only shapes the runner allows). Missing tools are reported at run time."""
    root, out = Path(root), []
    pkg = root / "package.json"
    if pkg.is_file():
        txt = pkg.read_text(encoding="utf-8", errors="replace")
        if not (root / "node_modules").is_dir():
            out.append(["npm", "install", "--no-audit", "--no-fund", "--loglevel=error"])
        for name in ("typecheck", "lint", "build", "test"):
            if f'"{name}"' in txt:
                out.append(["npm", "run", name])
        if "typecheck" not in txt and (root / "tsconfig.json").is_file():
            out.append(["npx", "tsc", "--noEmit"])
    if any(root.glob("*.py")) or any(root.glob("*/*.py")) or (root / "requirements.txt").is_file():
        out.append(["python", "-m", "compileall", "-q", "."])
        if (root / "tests").is_dir() or any(root.glob("test_*.py")):
            out.append(["python", "-m", "pytest", "-q", "-x", "--tb=short", "-p", "no:cacheprovider"])
    if (root / "go.mod").is_file():
        out += [["go", "build", "./..."], ["go", "vet", "./..."], ["go", "test", "./..."]]
    if (root / "pom.xml").is_file():
        out.append(["mvn", "-q", "-B", "test"])
    if any(root.glob("*.sln")) or any(root.glob("*.csproj")):
        out.append(["dotnet", "build", "--nologo", "-v", "q"])
    return [c for c in out if allowed(c)]


def _kill_tree(p: subprocess.Popen) -> None:
    try:
        if os.name == "nt":
            subprocess.run(["taskkill", "/T", "/F", "/PID", str(p.pid)], capture_output=True, timeout=10)
        else:
            os.killpg(os.getpgid(p.pid), signal.SIGKILL)
    except (OSError, subprocess.SubprocessError):
        p.kill()


def run(args: list[str], cwd: str, timeout: int = 30, max_out: int = 2000) -> dict:
    if not allowed(args):
        raise ValueError(f"command not allowed: {args[:2]}")
    exe = sys.executable if args[0] in PY else shutil.which(args[0])
    if not exe:
        return {"code": 127, "out": f"{args[0]} not found"}
    kw = {"start_new_session": True} if os.name != "nt" else {"creationflags": getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)}
    p = subprocess.Popen([exe, *args[1:]], cwd=cwd, env=_env(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, errors="replace", **kw)
    waited = 0.0
    try:
        while True:
            try:
                out, _ = p.communicate(timeout=0.5)
                return {"code": p.returncode, "out": redact((out or "")[-max_out:])}
            except subprocess.TimeoutExpired:
                waited += 0.5
                context.check()                         # task cancelled -> finally kills the process tree
                if waited >= timeout:
                    _kill_tree(p)
                    p.communicate()
                    return {"code": 124, "out": "timeout"}
    finally:
        if p.poll() is None:
            _kill_tree(p)
            p.communicate()

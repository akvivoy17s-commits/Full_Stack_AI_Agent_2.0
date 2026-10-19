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
_SECRET_ENV = re.compile(r"(?i)(key|token|secret|passw|credential|auth|database_url|db_url|connection_string|dsn)")
_UNSAFE_ENV_NAMES = {
    # Prevent interpreter/module preload settings from injecting code into build/test processes.
    "PYTHONPATH", "PYTHONHOME", "NODE_OPTIONS", "NODE_PATH", "RUBYOPT", "PERL5OPT",
    "JAVA_TOOL_OPTIONS", "JDK_JAVA_OPTIONS", "MAVEN_OPTS", "DOTNET_STARTUP_HOOKS",
    "LD_PRELOAD", "LD_LIBRARY_PATH", "DYLD_INSERT_LIBRARIES", "DYLD_LIBRARY_PATH",
}


def _rel_ok(a: str, suffix: tuple = ()) -> bool:
    """Relative path argument: no traversal, no absolute path, no option injection."""
    a = a.replace("\\", "/")
    return bool(a) and not a.startswith(("-", "/", "~")) and ".." not in a.split("/") and not re.match(r"^[A-Za-z]:", a) \
        and "\0" not in a and (not suffix or a.endswith(suffix))


def _is_python_executable(value: str) -> bool:
    """Accept the host Python or a known virtualenv interpreter path within the project."""
    normalized = value.replace("\\", "/").lower()
    return value in PY or normalized in {".venv/scripts/python.exe", ".venv/bin/python", ".venv/bin/python3"}


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
    if _is_python_executable(exe):
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
    # Parser/compiler-only invocations. These exact forms never execute the built
    # application and validate paths with the same traversal/option-injection guard.
    if exe == "cargo":
        return rest in (["check", "--offline", "--locked"], ["test", "--offline", "--locked"])
    if exe == "tsc":
        return rest in (["--noEmit", "--pretty", "false"], ["--noEmit"])
    if exe == "dart":
        return rest == ["analyze"]
    if exe == "php":
        return len(rest) == 2 and rest[0] == "-l" and _rel_ok(rest[1], (".php",))
    if exe == "ruby":
        return len(rest) == 2 and rest[0] == "-c" and _rel_ok(rest[1], (".rb",))
    if exe == "bash":
        return len(rest) == 2 and rest[0] == "-n" and _rel_ok(rest[1], (".sh", ".bash"))
    if exe == "swiftc":
        return len(rest) == 2 and rest[0] == "-typecheck" and _rel_ok(rest[1], (".swift",))
    if exe in {"gcc", "clang"}:
        return len(rest) == 2 and rest[0] == "-fsyntax-only" and _rel_ok(rest[1], (".c", ".h"))
    if exe in {"g++", "clang++", "c++"}:
        return len(rest) == 2 and rest[0] == "-fsyntax-only" and _rel_ok(rest[1], (".cc", ".cpp", ".cxx", ".hh", ".hpp", ".hxx"))
    if exe == "mvn":
        return rest in (["-q", "-B", "compile"], ["-q", "-B", "test"], ["-B", "-q", "test"])
    if exe == "dotnet":
        return rest in (["build", "--nologo", "-v", "q"], ["test", "--nologo", "-v", "q"])
    return False


def _env() -> dict:
    """Child environment without credentials: build/test commands never need the host's secrets."""
    e = {k: v for k, v in os.environ.items()
         if not _SECRET_ENV.search(k) and k.upper() not in _UNSAFE_ENV_NAMES}
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


def _clip_output(text: str, limit: int) -> str:
    """Bound logs while retaining both the command header and the final diagnostic/stack trace."""
    if limit <= 0:
        return ""
    if len(text) <= limit:
        return text
    marker = "\n... [command output truncated; beginning and end preserved] ...\n"
    if limit <= len(marker) + 2:
        return text[-limit:]
    room = limit - len(marker)
    head = room // 2
    tail = room - head
    return text[:head] + marker + (text[-tail:] if tail else "")


def run(args: list[str], cwd: str, timeout: int = 30, max_out: int = 2000) -> dict:
    if not allowed(args):
        raise ValueError(f"command not allowed: {args[:2]}")
    if args[0] in PY:
        exe = sys.executable
    elif _is_python_executable(args[0]):
        # Resolve only the two explicit venv layouts. Do not accept arbitrary executable
        # paths or command strings from the model; the path is always relative to cwd.
        venv_exe = (Path(cwd).resolve() / Path(*args[0].replace("\\", "/").split("/")))
        exe = str(venv_exe) if venv_exe.is_file() else None
    else:
        exe = shutil.which(args[0])
    if not exe:
        return {"code": 127, "out": f"{args[0]} not found"}
    kw = {"start_new_session": True} if os.name != "nt" else {"creationflags": getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)}
    p = subprocess.Popen([exe, *args[1:]], cwd=cwd, env=_env(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, errors="replace", **kw)
    waited = 0.0
    try:
        while True:
            try:
                out, _ = p.communicate(timeout=0.5)
                return {"code": p.returncode, "out": redact(_clip_output(out or "", max_out))}
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

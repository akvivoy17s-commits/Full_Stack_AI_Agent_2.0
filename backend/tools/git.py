"""Small, allowlisted Git operations scoped to one managed project directory."""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from backend import config
from backend.tools.project_files import ProjectFiles, is_secret
from backend.tools.redact import redact

MAX_OUTPUT = 12_000


def _run(root: Path, args: list[str], timeout: int = 8, env_extra: dict | None = None) -> dict:
    exe = shutil.which("git")
    if not exe:
        return {"ok": False, "code": 127, "output": "Git is not installed or is not on PATH."}
    env = {k: v for k, v in os.environ.items() if not any(s in k.lower() for s in ("token", "password", "secret", "credential", "private_key"))}
    env.update({"GIT_TERMINAL_PROMPT": "0", "GIT_OPTIONAL_LOCKS": "0", "GCM_INTERACTIVE": "Never"})
    env.update(env_extra or {})
    try:
        p = subprocess.run([exe, "-C", str(root), *args], stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace", timeout=timeout,
                           env=env, check=False)
        return {"ok": p.returncode == 0, "code": p.returncode, "output": redact((p.stdout or "")[-MAX_OUTPUT:])}
    except subprocess.TimeoutExpired:
        return {"ok": False, "code": 124, "output": "Git command timed out."}
    except OSError as exc:
        return {"ok": False, "code": 1, "output": f"Git command failed ({type(exc).__name__})."}


def _repo(root: Path) -> bool:
    return _run(root, ["rev-parse", "--is-inside-work-tree"], timeout=3)["output"].strip() == "true"


def status(pid: str) -> dict:
    root = ProjectFiles(pid).root
    if not _repo(root):
        return {"initialized": False, "available": shutil.which("git") is not None, "branch": None,
                "clean": None, "changes": [], "summary": "This project is not inside a Git working tree."}
    status_result = _run(root, ["status", "--porcelain=v1", "--branch", "--untracked-files=normal"])
    branch_result = _run(root, ["branch", "--show-current"])
    if not status_result["ok"]:
        return {"initialized": True, "available": True, "error": status_result["output"]}
    lines = status_result["output"].splitlines()
    branch = branch_result["output"].strip() if branch_result["ok"] else ""
    changes = []
    for line in lines:
        if not line or line.startswith("##"):
            continue
        code, _, path = line[:2], line[2:3], line[3:].strip()
        # Git may quote paths containing unusual characters. Display only a name/status, never content.
        path = path.strip('"')
        changes.append({"code": code, "path": path[:300], "secret": is_secret(path)})
    return {"initialized": True, "available": True, "branch": branch, "clean": len(changes) == 0,
            "changes": changes[:300], "summary": "Working tree clean." if not changes else f"{len(changes)} changed/untracked path(s)."}


def diff(pid: str, path: str | None = None) -> dict:
    pf = ProjectFiles(pid)
    root = pf.root
    if not _repo(root):
        return {"available": False, "diff": "This project is not inside a Git working tree."}
    args = ["diff", "--no-ext-diff", "--no-color", "--unified=2", "--"]
    if path:
        rel = path.replace("\\", "/").strip()
        if not rel or rel.startswith("/") or ".." in rel.split("/") or ":" in rel or is_secret(rel):
            raise ValueError("invalid or protected diff path")
        pf._guard(rel)
        args.append(rel)
    result = _run(root, args, timeout=8)
    return {"available": True, "ok": result["ok"], "diff": result["output"],
            "note": "Shows tracked working-tree changes only; untracked files appear in status until added."}


def log(pid: str, limit: int = 10) -> dict:
    root = ProjectFiles(pid).root
    if not _repo(root):
        return {"available": False, "commits": []}
    r = _run(root, ["log", f"-{max(1, min(limit, 30))}", "--oneline", "--decorate=no"])
    return {"available": True, "commits": r["output"].splitlines() if r["ok"] else [], "error": None if r["ok"] else r["output"]}


def create_branch(pid: str, name: str, confirm: bool) -> dict:
    if not confirm:
        raise ValueError("confirm=true is required before creating a branch")
    if len(name) > 100 or not name.strip() or name.startswith("-") or any(c.isspace() for c in name):
        raise ValueError("enter a valid branch name without spaces")
    root = ProjectFiles(pid).root
    if not _repo(root):
        raise ValueError("this project is not inside a Git working tree")
    state = status(pid)
    if state.get("clean") is not True:
        raise ValueError("create a branch only after committing or stashing current changes; working tree is not clean")
    validate = _run(root, ["check-ref-format", "--branch", name])
    if not validate["ok"]:
        raise ValueError("invalid branch name")
    result = _run(root, ["switch", "-c", name], timeout=10)
    if not result["ok"]:
        raise ValueError(result["output"] or "Git could not create the branch")
    return {"branch": name, "created": True}


def commit(pid: str, message: str, paths: list[str], confirm: bool) -> dict:
    if not confirm:
        raise ValueError("confirm=true is required before committing")
    message = message.strip()
    if not message or len(message) > 200:
        raise ValueError("commit message must be between 1 and 200 characters")
    if not paths or len(paths) > 30:
        raise ValueError("select between 1 and 30 files to commit")
    pf = ProjectFiles(pid)
    root = pf.root
    if not _repo(root):
        raise ValueError("this project is not inside a Git working tree")
    clean_paths: list[str] = []
    for path in paths:
        rel = path.replace("\\", "/").strip()
        if not rel or rel.startswith("/") or ".." in rel.split("/") or ":" in rel or is_secret(rel):
            raise ValueError(f"invalid or secret file path: {path[:80]}")
        target = pf._guard(rel)
        if target.is_symlink() or not target.is_file():
            raise ValueError(f"not an ordinary project file: {rel}")
        clean_paths.append(rel)
    # Use a temporary index so unrelated staged user changes are never silently committed.
    config.TMP_DIR.mkdir(parents=True, exist_ok=True)
    fd, index_path = tempfile.mkstemp(prefix="git-index-", dir=str(config.TMP_DIR))
    os.close(fd)
    index = Path(index_path)
    index.unlink(missing_ok=True)  # Git must create a valid index; an empty tempfile is not a valid Git index.
    try:
        env = {"GIT_INDEX_FILE": str(index)}
        head = _run(root, ["rev-parse", "--verify", "HEAD"], env_extra=env)
        read_tree = _run(root, ["read-tree", "HEAD"] if head["ok"] else ["read-tree", "--empty"], env_extra=env)
        if not read_tree["ok"]:
            raise ValueError("could not create an isolated Git staging area")
        add = _run(root, ["add", "--", *clean_paths], env_extra=env)
        if not add["ok"]:
            raise ValueError(add["output"] or "Git could not stage the selected files")
        check = _run(root, ["diff", "--cached", "--check"], env_extra=env)
        if not check["ok"]:
            raise ValueError("staged diff has whitespace errors: " + check["output"][:500])
        # Disable repo-local hooks for this user-confirmed, scoped commit; no shell is invoked.
        hooks = config.TMP_DIR / "empty-git-hooks"
        hooks.mkdir(parents=True, exist_ok=True)
        result = _run(root, ["-c", f"core.hooksPath={hooks}", "commit", "-m", message], timeout=20, env_extra=env)
        if not result["ok"]:
            raise ValueError(result["output"] or "Git commit failed")
        oid = _run(root, ["rev-parse", "--short", "HEAD"])
        return {"committed": True, "commit": oid["output"].strip(), "message": message, "files": clean_paths}
    finally:
        index.unlink(missing_ok=True)

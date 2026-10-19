import hashlib
import os
import re
import tempfile
from pathlib import Path
from backend.config import GENERATED_DIR, MAX_FILE_BYTES

IGNORE = {".agent", "node_modules", ".git", "dist", ".venv", "venv", "__pycache__", ".pytest_cache", "build", "target"}
NO_WRITE_DIRS = {"node_modules", ".git", ".venv", "venv", "__pycache__", "dist", "build", "target"}  # generated tools do not overwrite installed/build outputs
SAFE_ENV_SUFFIX = (".example", ".sample", ".template", ".dist")
SECRET_EXT = {".pem", ".key", ".p12", ".pfx", ".keystore", ".jks"}
SECRET_NAMES = {"id_rsa", "id_ed25519", "id_ecdsa", ".npmrc", ".pypirc", ".netrc", "credentials.json", "serviceaccount.json"}
MAX_TREE = 2000


def is_secret(rel: str) -> bool:
    """True for files that commonly hold credentials (.env, keys, tokens). Templates like .env.example are fine."""
    n = rel.replace("\\", "/").rsplit("/", 1)[-1].lower()
    if n == ".env" or (n.startswith(".env.") and not n.endswith(SAFE_ENV_SUFFIX)):
        return True
    return n in SECRET_NAMES or any(n.endswith(e) for e in SECRET_EXT)


class ProjectFiles:
    """Sandboxed file access for one generated project."""

    def __init__(self, project_id: str):
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", project_id):
            raise ValueError("invalid project id")
        # A project id is one path segment, and the resolved project directory must
        # remain a direct child of GENERATED_DIR. Never trust a pre-existing symlink
        # at generated_projects/<id>.
        base = Path(GENERATED_DIR).resolve()
        candidate = base / project_id
        if candidate.is_symlink():
            raise ValueError("project directory may not be a symlink")
        candidate.mkdir(parents=True, exist_ok=True)
        if candidate.is_symlink():
            raise ValueError("project directory may not be a symlink")
        self.root = candidate.resolve()
        if self.root.parent != base:
            raise ValueError("project directory escapes generated projects")

    def _safe(self, rel: str) -> Path:
        r = rel.replace("\\", "/")
        if "\0" in rel or r.startswith("/") or re.match(r"^[A-Za-z]:", r) or ":" in r or ".." in r.split("/"):
            raise ValueError("path escapes project")
        p = (self.root / r).resolve()
        if p != self.root and self.root not in p.parents:
            raise ValueError("path escapes project")
        return p

    def _guard(self, rel: str, write: bool = False) -> Path:
        p = self._safe(rel)
        if is_secret(rel):
            raise ValueError("protected file (secrets)")
        if write and NO_WRITE_DIRS & {part.lower() for part in rel.replace("\\", "/").split("/")}:
            raise ValueError("protected directory")
        return p

    def write(self, rel: str, content: str) -> str:
        if len(content.encode()) > MAX_FILE_BYTES:
            raise ValueError("file too large")
        p = self._guard(rel, write=True)
        p.parent.mkdir(parents=True, exist_ok=True)
        # Use a unique temporary file in the destination directory. A predictable
        # `<name>.tmp` path could already be a symlink and redirect the write outside
        # the project before os.replace() is reached.
        fd, tmp_name = tempfile.mkstemp(prefix=f".{p.name}.", suffix=".tmp", dir=str(p.parent))
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="") as f:
                f.write(content)
            os.replace(tmp_name, p)
        finally:
            try:
                os.unlink(tmp_name)
            except OSError:
                pass
        return self.hash(rel)

    def read(self, rel: str, max_chars: int | None = None) -> str:
        p = self._guard(rel)
        if p.stat().st_size > MAX_FILE_BYTES:
            raise ValueError("file too large")
        t = p.read_text(encoding="utf-8")
        return t[:max_chars] if max_chars else t

    def patch(self, rel: str, old: str, new: str) -> bool:
        """Replace one exact, unique snippet. Returns False if not found / ambiguous."""
        t = self.read(rel)
        if t.count(old) != 1:
            return False
        self.write(rel, t.replace(old, new))
        return True

    def hash(self, rel: str) -> str:
        return hashlib.md5(self._safe(rel).read_bytes()).hexdigest()[:8]

    def tree(self) -> list[str]:
        out = []
        for dp, dns, fns in os.walk(self.root):             # prune ignored dirs instead of walking node_modules
            dns[:] = sorted(d for d in dns if d.lower() not in IGNORE and not (Path(dp) / d).is_symlink())
            for f in sorted(fns):
                fp = Path(dp) / f
                if fp.is_symlink():                         # never list/follow symlinks (could point outside the project)
                    continue
                rel = fp.relative_to(self.root).as_posix()
                if not is_secret(rel):
                    out.append(rel)
                if len(out) >= MAX_TREE:
                    return sorted(out)
        return sorted(out)

    def snippet(self, rel: str, around: str, radius: int = 600) -> str:
        """Return a small window around `around` (for token-cheap repairs)."""
        t = self.read(rel)
        i = t.find(around)
        if i < 0:
            return t[: radius * 2]
        return t[max(0, i - radius): i + radius]

    def apply_ops(self, ops: list[dict]) -> list[str]:
        """Apply LLM-produced ops. Returns list of error strings (empty = all ok)."""
        errs = []
        for op in ops:
            try:
                if op.get("op") == "write":
                    self.write(op["path"], op["content"])
                elif op.get("op") == "patch":
                    if not self.patch(op["path"], op["old"], op["new"]):
                        errs.append(f"patch failed: {op['path']}")
                else:
                    errs.append(f"unknown op: {op.get('op')}")
            except Exception as e:  # noqa: BLE001
                errs.append(f"{op.get('path', '?')}: {e}")
        return errs

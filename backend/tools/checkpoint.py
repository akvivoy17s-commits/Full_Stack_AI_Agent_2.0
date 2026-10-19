"""Small, path-scoped, atomic source checkpoints for generated-project repairs.

A checkpoint only covers the paths the repair operation is allowed to touch. It never
walks outside the project root, follows symlinks, or snapshots installed/build folders.
"""
from __future__ import annotations

import os
import re
import tempfile
from pathlib import Path

from backend.config import MAX_FILE_BYTES
from backend.tools.project_files import is_secret


def _safe_path(root: Path, rel: str) -> Path:
    if not isinstance(rel, str) or not rel or "\0" in rel:
        raise ValueError("checkpoint path must be a non-empty relative path")
    normalized = rel.replace("\\", "/")
    if normalized.startswith("/") or re.match(r"^[A-Za-z]:", normalized) or ":" in normalized:
        raise ValueError("checkpoint path must be relative")
    if ".." in normalized.split("/"):
        raise ValueError("checkpoint path traversal is not allowed")
    if is_secret(normalized):
        raise ValueError("secret files cannot be checkpointed")
    candidate = root / normalized
    # Resolve existing parents to detect traversal through a symlink directory.
    resolved = candidate.resolve(strict=False)
    if resolved != root and root not in resolved.parents:
        raise ValueError("checkpoint path escapes project root")
    current = root
    for part in Path(normalized).parts:
        current = current / part
        if current.is_symlink():
            raise ValueError("checkpoint does not follow symlinks")
    return candidate


def capture(root: str | Path, paths: list[str] | tuple[str, ...] | set[str]) -> dict[str, bytes | None]:
    """Capture listed source paths. None marks a path that did not exist before repair."""
    base = Path(root).resolve()
    if not base.is_dir() or Path(root).is_symlink():
        raise ValueError("checkpoint root must be an existing non-symlink directory")
    result: dict[str, bytes | None] = {}
    total = 0
    for rel in sorted(set(paths)):
        target = _safe_path(base, rel)
        if not target.exists():
            result[rel.replace("\\", "/")] = None
            continue
        if not target.is_file():
            raise ValueError(f"checkpoint target is not a file: {rel}")
        payload = target.read_bytes()
        if len(payload) > MAX_FILE_BYTES:
            raise ValueError(f"checkpoint target exceeds the file-size limit: {rel}")
        # Project repair targets are UTF-8 text. Avoid silently taking a partial snapshot
        # of binary data that the repair engines are not expected to edit.
        if b"\0" in payload:
            raise ValueError(f"binary file cannot be checkpointed: {rel}")
        try:
            payload.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError(f"non-UTF-8 source cannot be checkpointed: {rel}") from exc
        total += len(payload)
        if total > MAX_FILE_BYTES * 4:
            raise ValueError("checkpoint exceeds the total source-size limit")
        result[rel.replace("\\", "/")] = payload
    return result


def restore(root: str | Path, snapshot: dict[str, bytes | None]) -> list[str]:
    """Atomically restore a captured path set; remove only files created at those paths."""
    base = Path(root).resolve()
    if not base.is_dir() or Path(root).is_symlink():
        raise ValueError("checkpoint root must be an existing non-symlink directory")
    restored: list[str] = []
    for rel, payload in snapshot.items():
        target = _safe_path(base, rel)
        if payload is None:
            if target.is_file() and not target.is_symlink():
                target.unlink()
                restored.append(rel)
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(prefix=f".{target.name}.", suffix=".rollback", dir=str(target.parent))
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, target)
            restored.append(rel)
        finally:
            try:
                os.unlink(temporary)
            except OSError:
                pass
    return restored

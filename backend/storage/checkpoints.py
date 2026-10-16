"""Project checkpoints (zip snapshots) and safe export. Files live under DATA_DIR, never inside the agent's source."""
import os
import shutil
import uuid
import zipfile
from pathlib import Path

from backend import config
from backend.storage import db
from backend.tools.project_files import ProjectFiles

SKIP_DIRS = {"node_modules", ".git", "dist"}


def _files(root: Path, skip_agent: bool):
    for p in sorted(root.rglob("*")):
        rel = p.relative_to(root)
        parts = set(rel.parts)
        if not p.is_file() or p.is_symlink() or parts & SKIP_DIRS:    # symlinks are never followed into archives
            continue
        if rel.parts[0] == ".agent" and (skip_agent or (len(rel.parts) > 1 and rel.parts[1] == "shots")):
            continue
        yield p, rel


def _zip(root: Path, dest: Path, skip_agent: bool) -> int:
    tmp = dest.with_suffix(".part")
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
        for p, rel in _files(root, skip_agent):
            z.write(p, rel.as_posix())
    os.replace(tmp, dest)
    return dest.stat().st_size


def create(pid: str, label: str, task_id: str | None = None) -> dict:
    root = ProjectFiles(pid).root
    cid = uuid.uuid4().hex[:10]
    d = config.CHECKPOINT_DIR / pid
    d.mkdir(parents=True, exist_ok=True)
    dest = d / f"{cid}.zip"
    size = _zip(root, dest, skip_agent=False)
    db.add_checkpoint(cid, pid, label, task_id, dest, size)
    for old in db.list_checkpoints(pid)[config.MAX_CHECKPOINTS:]:       # prune oldest
        row = db.get_checkpoint(pid, old["id"])
        Path(row["path"]).unlink(missing_ok=True)
        db.delete_checkpoint(old["id"])
    return {"id": cid, "label": label, "size": size}


def _safe_members(z: zipfile.ZipFile, root: Path) -> list[zipfile.ZipInfo]:
    total, out = 0, []
    for m in z.infolist():
        name = m.filename.replace("\\", "/")
        if name.endswith("/"):
            continue
        if name.startswith("/") or ":" in name or ".." in name.split("/"):
            raise ValueError(f"unsafe path in archive: {name}")
        if root not in (root / name).resolve().parents:
            raise ValueError(f"unsafe path in archive: {name}")
        total += m.file_size
        out.append(m)
    if total > config.MAX_ZIP_BYTES:
        raise ValueError("archive too large")
    return out


def restore(pid: str, cid: str) -> dict:
    row = db.get_checkpoint(pid, cid)
    if not row or not Path(row["path"]).is_file():
        raise FileNotFoundError("checkpoint not found")
    safety = create(pid, f"before restore {cid}")                       # always keep a way back
    root = ProjectFiles(pid).root
    stage = config.TMP_DIR / f"restore-{uuid.uuid4().hex[:8]}"
    stage.mkdir(parents=True)
    try:
        with zipfile.ZipFile(row["path"]) as z:
            for m in _safe_members(z, stage.resolve()):
                z.extract(m, stage)
        for child in list(root.iterdir()):                              # replace current contents
            shutil.rmtree(child) if child.is_dir() and not child.is_symlink() else child.unlink()
        for child in stage.iterdir():
            shutil.move(str(child), str(root / child.name))
    finally:
        shutil.rmtree(stage, ignore_errors=True)
    db.audit("restore", pid, f"checkpoint {cid} (safety {safety['id']})")
    return {"restored": cid, "safety_checkpoint": safety["id"]}


def export(pid: str) -> Path:
    root = ProjectFiles(pid).root
    dest = config.EXPORT_DIR / f"{pid}-{uuid.uuid4().hex[:6]}.zip"
    _zip(root, dest, skip_agent=True)
    for old in sorted(config.EXPORT_DIR.glob("*.zip"), key=lambda p: p.stat().st_mtime)[:-10]:
        old.unlink(missing_ok=True)
    db.audit("export", pid, dest.name)
    return dest

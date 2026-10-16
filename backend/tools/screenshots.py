"""Screenshots live in <project>/.agent/shots, named <task-id|manual>-<viewport>.png (so each belongs to a project AND a task)."""
import re

from backend.agent import context

KEEP = 12


def _dir(pf):
    d = pf.root / ".agent" / "shots"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _tag() -> str:
    c = context.current()
    return re.sub(r"[^a-z0-9]", "", c.task_id.lower())[:16] if c else "manual"


def take(page, pf, name: str) -> str:
    fn = f"{_tag()}-{name}.png"
    page.screenshot(path=str(_dir(pf) / fn), full_page=True)
    return fn


def prune(pf) -> None:
    files = sorted(_dir(pf).glob("*.png"), key=lambda p: p.stat().st_mtime, reverse=True)
    for p in files[KEEP:]:
        p.unlink(missing_ok=True)


def list_shots(pf) -> list[str]:
    d = pf.root / ".agent" / "shots"
    return [p.name for p in sorted(d.glob("*.png"), key=lambda p: p.stat().st_mtime, reverse=True)] if d.exists() else []

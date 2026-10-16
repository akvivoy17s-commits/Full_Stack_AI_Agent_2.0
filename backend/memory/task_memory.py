"""Persistent task memory: what each task did, what failed, what is still open. Rule-based, zero LLM tokens.

Rows live in SQLite (`task_memory`) so they survive restarts; `context()` returns a small prompt block (repo map + open work).
"""
from backend.repo import mapper
from backend.storage import db

NEXT_PREFIX = "Resolve: "


def record_task(pid: str, tid: str, kind: str, res: dict | None = None, error: str = "") -> None:
    """Called when a task ends: one summary note, failures for each issue/error, `next` items for unresolved issues."""
    res = res or {}
    issues = [str(i) for i in (res.get("issues") or [])]
    if error:
        db.add_memory(pid, tid, "failure", f"{kind} failed: {error}")
        db.add_memory(pid, tid, "next", f"Retry {kind} after fixing: {error[:120]}")
        return
    done, total = len(res.get("sections_done") or []), res.get("sections_total") or 0
    db.add_memory(pid, tid, "note", f"{kind} ok: {done}/{total} sections, {len(issues)} issue(s), {res.get('repairs') or 0} repair(s)")
    for i in issues[:5]:
        db.add_memory(pid, tid, "failure", f"{kind}: {i[:200]}")
        db.add_memory(pid, tid, "next", NEXT_PREFIX + i[:200])
    if not issues and kind in ("generate", "edit", "verify"):
        db.close_memory(pid, prefix=NEXT_PREFIX)                   # clean run: earlier unresolved issues are fixed


def add(pid: str, kind: str, text: str, task_id: str = "") -> int | None:
    return db.add_memory(pid, task_id, kind, text)


def context(pid: str, budget: int = 1500) -> str:
    """Repo map + open next-steps + recent failures, for LLM prompts. Empty string when the project has nothing yet."""
    try:
        repo = mapper.compact(pid, budget // 2)
    except (OSError, ValueError):
        repo = ""
    nxt = [r["text"] for r in db.list_memory(pid, "next", "open", 5)]
    bad = [r["text"] for r in db.list_memory(pid, "failure", "", 3)]
    dec = [r["text"] for r in db.list_memory(pid, "decision", "", 3)]
    parts = [repo] if repo else []
    for label, rows in (("OPEN", nxt), ("FAILED", bad), ("DECIDED", dec)):
        if rows:
            parts.append(f"{label}: " + " | ".join(r[:120] for r in rows))
    return "\n".join(parts)[:budget]


def resume(pid: str) -> dict:
    """Where did we stop? Last task, open next-steps, repo staleness. Lets work resume without redoing anything."""
    last = (db.list_tasks(pid, 1) or [None])[0]
    return {"last_task": last, "active": db.active_task(pid), "next": db.list_memory(pid, "next", "open", 10),
            "recent_failures": db.list_memory(pid, "failure", "", 5), "decisions": db.list_memory(pid, "decision", "", 5),
            "repo_stale": mapper.stale(pid)}

"""Task execution tracking (0 LLM tokens): ordered steps, percent complete, and an evidence-based verdict.

Steps are stored in SQLite (task_steps) so a page reload or SSE reconnect can rebuild the exact progress view.
Outside a task (tests, scripts) the tracker still works in memory and simply writes nothing to the DB.
"""
from contextlib import contextmanager

from backend.agent import context
from backend.storage import db

STEPS = {
    "generate": [("analyze", "Analyze requirements and stack"), ("plan", "Plan sections, design and motion"), ("design", "Scaffold design system"),
                 ("backend", "Generate backend"), ("code", "Generate frontend sections"), ("verify", "Run checks and bounded repair")],
    "edit": [("edit", "Apply requested edit"), ("verify", "Static verification")],
    "verify": [("verify", "Run checks and bounded repair")],
    "test": [("verify", "Browser, accessibility and build checks")],
}
DONE = ("done", "skipped", "issues")       # states that count as finished for the percent bar


class Tracker:
    def __init__(self, kind: str):
        self.tid = (context.current().task_id if context.current() else "")
        self.steps = [{"key": k, "title": t, "status": "pending", "detail": ""} for k, t in STEPS.get(kind, STEPS["verify"])]
        if self.tid:
            db.set_steps(self.tid, [(s["key"], s["title"]) for s in self.steps])

    def _set(self, key: str, status: str, detail: str = "") -> None:
        for s in self.steps:
            if s["key"] == key:
                s["status"], s["detail"] = status, detail
                break
        else:
            raise KeyError(f"unknown step '{key}'")
        if self.tid:
            db.update_step(self.tid, key, status, detail)
        n = sum(1 for s in self.steps if s["status"] in DONE)
        context.progress("step", f"[{n}/{len(self.steps)}] {key}: {status}" + (f" - {detail}" if detail else ""),
                         "error" if status == "failed" else ("warn" if status == "issues" else "info"))

    def skip(self, key: str, reason: str) -> None:
        self._set(key, "skipped", reason)

    @contextmanager
    def step(self, key: str):
        """Run one step. Result (set via the yielded dict) -> done | skipped | issues; exceptions -> failed/cancelled, then re-raised."""
        context.check()
        self._set(key, "running")
        out = {"status": "done", "detail": ""}
        try:
            yield out
        except context.Cancelled:
            self._set(key, "cancelled", "task cancelled")
            raise
        except BaseException as e:  # noqa: BLE001 - recorded, then re-raised unchanged
            self._set(key, "failed", f"{type(e).__name__}: {e}"[:200])
            raise
        self._set(key, out["status"], out["detail"])

    def percent(self) -> int:
        return percent(self.steps)


def percent(steps: list[dict]) -> int:
    return round(100 * sum(1 for s in steps if s["status"] in DONE) / len(steps)) if steps else 0


def snapshot(tid: str, task_status: str | None = None) -> dict:
    steps = db.list_steps(tid)
    pct = 100 if task_status in ("succeeded", "completed_with_issues") else percent(steps)
    cur = next((s["key"] for s in steps if s["status"] == "running"), None)
    return {"task_id": tid, "percent": pct, "current": cur, "steps": steps}


def verdict(steps: list[dict], issues: list, analysis: dict | None = None, backend_note: str = "") -> dict:
    """PASS only with evidence: every step finished, nothing unresolved, nothing promised-but-not-built."""
    reasons: list[str] = []
    if any(s["status"] in ("failed", "cancelled") for s in steps):
        bad = next(s for s in steps if s["status"] in ("failed", "cancelled"))
        return {"verdict": "FAIL", "reasons": [f"step '{bad['key']}' {bad['status']}: {bad['detail']}"[:200]]}
    a = analysis or {}
    if a.get("blocking"):
        return {"verdict": "BLOCKED", "reasons": [f"needs your answer: {q['question']}"[:200] for q in a["blocking"]]}
    if issues:
        reasons.append(f"{len(issues)} unresolved issue(s) after bounded repair")
    pend = [s for s in steps if s["status"] == "pending"]
    if pend:
        reasons.append("steps not run: " + ", ".join(s["key"] for s in pend))
    cnt = a.get("counts") or {}
    if cnt.get("planned"):
        reasons.append(f"{cnt['planned']} requirement(s) need generators that are not available yet")
    if cnt.get("gap"):
        reasons.append(f"{cnt['gap']} requirement(s) cannot be met by the selected stack")
    if backend_note:
        reasons.append(backend_note)
    return {"verdict": "PARTIAL" if reasons else "PASS", "reasons": reasons}

"""Background task manager: bounded thread pool, per-project lock, cancellation, progress events, auto-checkpoints."""
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor

from backend.agent import context, llm, progress
from backend.memory import task_memory
from backend.repo import mapper
from backend.storage import checkpoints, db

_lock = threading.Lock()
_pool: ThreadPoolExecutor | None = None
_pool_size = 0
_ctx: dict[str, context.TaskContext] = {}
RISKY = {"generate", "edit", "verify"}            # snapshot the last known state before these run ("test" never edits files)


def _get_pool() -> ThreadPoolExecutor:
    global _pool, _pool_size
    want = db.get_settings()["max_concurrency"]
    if _pool is None or want != _pool_size:
        if _pool:
            _pool.shutdown(wait=False)
        _pool, _pool_size = ThreadPoolExecutor(max_workers=want, thread_name_prefix="agent"), want
    return _pool


def _remember(pid: str, tid: str, kind: str, res: dict | None, error: str = "") -> None:
    """Refresh the repo map and store task memory. Never lets a memory problem change the task outcome."""
    try:
        if kind != "test":
            mapper.build(pid)
        task_memory.record_task(pid, tid, kind, res, error)
    except Exception as e:  # noqa: BLE001
        db.add_event(tid, "memory", f"memory update skipped: {type(e).__name__}", "warn")


def _runner(kind: str, pid: str, p: dict):
    """Run one task kind with step tracking; the result carries steps, percent and an evidence-based verdict."""
    from backend.agent import orchestrator
    tr = progress.Tracker(kind)
    if kind == "generate":
        res = orchestrator.run(pid, p.get("force", False), tr)
    elif kind in ("verify", "test"):                     # "test": browser + a11y + build checks only, never edits files
        with tr.step("verify") as o:
            res = orchestrator.verify(pid, do_repair=p.get("repair", True) if kind == "verify" else False, with_browser=True if kind == "test" else None)
            o["status"] = "issues" if res["issues"] else "done"
            o["detail"] = f"{len(res['issues'])} issue(s)"
    elif kind == "edit":
        res = orchestrator.edit(pid, p["section"], p["instruction"], tr)
    else:
        raise ValueError(f"unknown task kind {kind}")
    res["steps"], res["percent"] = tr.steps, tr.percent()
    res["outcome"] = progress.verdict(tr.steps, res.get("issues") or [], res.get("analysis"), res.get("backend_note", ""))
    return res


def submit(pid: str, kind: str, params: dict) -> dict:
    with _lock:
        busy = db.active_task(pid)
        if busy:
            raise RuntimeError(f"project busy: task {busy['id']} ({busy['kind']}) is {busy['status']}")
        tid = uuid.uuid4().hex[:12]
        task = db.create_task(tid, pid, kind, params)
        _ctx[tid] = context.TaskContext(tid, lambda stage, msg, lvl="info": db.add_event(tid, stage, msg, lvl))
    db.add_event(tid, "queue", f"Task {kind} queued")
    _get_pool().submit(_run, tid, pid, kind, params)
    return task


def _run(tid: str, pid: str, kind: str, params: dict) -> None:
    ctx = _ctx[tid]
    context.bind(ctx)
    try:
        if ctx.cancel.is_set():
            raise context.Cancelled()
        db.update_task(tid, status="running", started_at=time.time())
        if kind in RISKY:
            cp = checkpoints.create(pid, f"before {kind}", tid)
            db.update_task(tid, checkpoint_id=cp["id"])
            context.progress("checkpoint", f"Saved checkpoint {cp['id']}")
        res = _runner(kind, pid, params)
        issues = res.get("issues") or []
        usage = res.get("usage") or {}
        db.add_summary(pid, tid, {"kind": kind, "phase": res.get("phase"), "issues": issues, "browser": res.get("browser"),
                                  "repairs": res.get("repairs"), "checks": (res.get("report") or {}).get("counts"),
                                  "warnings": (res.get("warnings") or [])[:5], "sections": f"{len(res.get('sections_done', []))}/{res.get('sections_total', 0)}",
                                  "verdict": (res.get("outcome") or {}).get("verdict")})
        _remember(pid, tid, kind, res)                    # before the terminal status: pollers and the next task never see a finished task without its repo map/memory
        db.update_task(tid, status="completed_with_issues" if issues else "succeeded", result=res,
                       tokens_in=usage.get("in", 0), tokens_out=usage.get("out", 0), finished_at=time.time())
        oc = res.get("outcome") or {}
        context.progress("done", f"{oc.get('verdict', 'DONE')}: " + ("; ".join(oc.get("reasons") or []) or "all steps and checks passed"),
                         "warn" if oc.get("verdict") != "PASS" else "info")
    except context.Cancelled:
        db.update_task(tid, status="cancelled", finished_at=time.time())
        context.progress("cancelled", "Task cancelled. Files written so far are kept; use the checkpoint to roll back.", "warn")
    except llm.OllamaError as e:
        db.update_task(tid, status="failed", error=f"[{e.code}] {e}", finished_at=time.time())
        context.progress("error", f"[{e.code}] {e}", "error")
    except Exception as e:  # noqa: BLE001
        _remember(pid, tid, kind, None, f"{type(e).__name__}: {e}")
        db.update_task(tid, status="failed", error=f"{type(e).__name__}: {e}", finished_at=time.time())
        context.progress("error", f"{type(e).__name__}: {e}", "error")
    finally:
        context.bind(None)
        _ctx.pop(tid, None)


def cancel(tid: str) -> dict | None:
    t = db.get_task(tid)
    if not t:
        return None
    ctx = _ctx.get(tid)
    if t["status"] in ("queued", "running") and ctx:
        ctx.cancel.set()
        db.add_event(tid, "cancel", "Cancellation requested", "warn")
    return db.get_task(tid)

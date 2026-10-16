import asyncio
import json
import re

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, StreamingResponse

from backend.spec import compose as spec_engine
from backend.agent import progress, requirements, tasks
from backend.agent.schemas import TaskCreate
from backend.storage import checkpoints, db

router = APIRouter()


def _project(pid: str):
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", pid) or not db.get_project(pid):
        raise HTTPException(404, "project not found")


def _task(tid: str) -> dict:
    t = db.get_task(tid)
    if not t:
        raise HTTPException(404, "task not found")
    return t


@router.post("/projects/{pid}/tasks", status_code=202)
def create_task(pid: str, body: TaskCreate):
    _project(pid)
    if body.kind == "generate" and body.force and not body.confirm:
        raise HTTPException(400, "Regenerating everything replaces existing sections: resend with confirm=true")
    if body.kind == "edit" and (not body.section or len(body.instruction) < 3):
        raise HTTPException(422, "edit needs 'section' and 'instruction'")
    try:
        return tasks.submit(pid, body.kind, body.model_dump(exclude={"kind", "confirm"}))
    except RuntimeError as e:
        raise HTTPException(409, str(e))


@router.get("/projects/{pid}/tasks")
def list_tasks(pid: str, limit: int = 30):
    _project(pid)
    return db.list_tasks(pid, max(1, min(limit, 100)))


@router.get("/tasks/{tid}")
def get_task(tid: str):
    return _task(tid)


@router.get("/tasks/{tid}/events")
def task_events(tid: str, after: int = 0):
    _task(tid)
    return db.events_after(tid, after)


@router.get("/tasks/{tid}/progress")
def task_progress(tid: str):
    """Ordered steps + percent + current step (rebuilds the progress view after a reload)."""
    t = _task(tid)
    out = progress.snapshot(tid, t["status"])
    out["status"], out["outcome"] = t["status"], (t.get("result") or {}).get("outcome")
    return out


@router.get("/projects/{pid}/requirements")
def project_requirements(pid: str):
    """Requirement analysis of the current app spec: covered / planned / gap, plus open questions."""
    _project(pid)
    spec = spec_engine.load(pid)
    if not spec:
        raise HTTPException(404, "no spec yet: run a generate task first")
    return requirements.analyze(spec)


@router.get("/tasks/{tid}/stream")
async def stream(tid: str, after: int = 0):
    """Server-sent events: progress rows until the task reaches a terminal state."""
    _task(tid)

    async def gen():
        last, idle = after, 0
        while True:
            rows = await asyncio.to_thread(db.events_after, tid, last)
            for r in rows:
                last = r["id"]
                yield f"id: {r['id']}\nevent: progress\ndata: {json.dumps(r)}\n\n"
            t = await asyncio.to_thread(db.get_task, tid)
            if t["status"] in db.TERMINAL and not rows:
                yield f"event: end\ndata: {json.dumps({'status': t['status'], 'error': t['error']})}\n\n"
                return
            idle = 0 if rows else idle + 1
            if idle and idle % 30 == 0:
                yield ": keep-alive\n\n"
            await asyncio.sleep(0.5)

    return StreamingResponse(gen(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@router.post("/tasks/{tid}/cancel")
def cancel_task(tid: str):
    _task(tid)
    return tasks.cancel(tid)


@router.get("/projects/{pid}/summaries")
def summaries(pid: str):
    _project(pid)
    return db.list_summaries(pid)


@router.get("/projects/{pid}/checkpoints")
def list_checkpoints(pid: str):
    _project(pid)
    return db.list_checkpoints(pid)


@router.post("/projects/{pid}/checkpoints", status_code=201)
def make_checkpoint(pid: str, label: str = "manual"):
    _project(pid)
    return checkpoints.create(pid, label[:80])


@router.post("/projects/{pid}/checkpoints/{cid}/restore")
def restore_checkpoint(pid: str, cid: str, confirm: bool = False):
    _project(pid)
    if not confirm:
        raise HTTPException(400, "Restore replaces current project files (a safety checkpoint is kept): resend with confirm=true")
    if db.active_task(pid):
        raise HTTPException(409, "project has a running task; cancel it first")
    try:
        return checkpoints.restore(pid, cid)
    except FileNotFoundError:
        raise HTTPException(404, "checkpoint not found")
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.get("/projects/{pid}/export")
def export_project(pid: str):
    _project(pid)
    p = checkpoints.export(pid)
    return FileResponse(p, media_type="application/zip", filename=f"{pid}.zip")


@router.get("/projects/{pid}/report")
def latest_report(pid: str):
    """Latest structured test report (checks passed/failed/skipped, a11y findings, vision note, repair log)."""
    _project(pid)
    from backend.tools.project_files import ProjectFiles
    try:
        return json.loads(ProjectFiles(pid).read(".agent/report.json"))
    except FileNotFoundError:
        raise HTTPException(404, "no report yet: run Verify or Test")


@router.get("/projects/{pid}/repairs")
def repairs(pid: str, limit: int = 60):
    _project(pid)
    return db.list_repair_attempts(pid, max(1, min(limit, 200)))

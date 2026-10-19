"""A bounded IDE terminal runner: shell-free and restricted to vetted command shapes."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.agent import context
from backend.api.tasks import _project
from backend.storage import db
from backend.tools import terminal as terminal_tools
from backend.tools.project_files import ProjectFiles
from backend.tools.redact import redact

router = APIRouter()


class TerminalRequest(BaseModel):
    args: list[str] = Field(min_length=1, max_length=16)
    timeout: int = Field(default=30, ge=1, le=180)
    confirm: bool = False


@router.post("/projects/{pid}/terminal")
def run_terminal(pid: str, body: TerminalRequest):
    _project(pid)
    if db.active_task(pid):
        raise HTTPException(409, "project has a running task; cancel it first")
    args = [str(a) for a in body.args]
    if any(len(a) > 300 or "\x00" in a for a in args):
        raise HTTPException(422, "invalid command arguments")
    if args[0] in ("npm",) and args[1:2] in (["install"], ["ci"]) and not body.confirm:
        raise HTTPException(400, "Dependency installation changes the environment and may use the network. Resend with confirm=true.")
    if not terminal_tools.allowed(args):
        raise HTTPException(400, {
            "message": "This terminal only accepts approved command shapes; shell operators and arbitrary scripts are disabled.",
            "examples": ["npm run build", "npm run typecheck", "npm run lint", "npm test",
                         "python -m pytest -q", "python -m compileall -q .", "npx tsc --noEmit"],
        })
    root = ProjectFiles(pid).root
    context.check()
    result = terminal_tools.run(args, cwd=str(root), timeout=body.timeout, max_out=8000)
    db.audit("terminal_run", pid, " ".join(args[:4])[:200] + f" code={result['code']}")
    return {"args": args, "cwd": root.name, "code": result["code"], "out": redact(result["out"])[:8000],
            "ok": result["code"] == 0, "timed_out": result["code"] == 124}

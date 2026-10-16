"""Backend generation API (rule based, no LLM calls)."""
from fastapi import APIRouter, HTTPException

from backend import spec as spec_engine
from backend.memory import project_store
from backend.spec import memory as spec_memory
from backend.api.stack import _state
from backend.gen import stage
from backend.storage import db
from backend.tools.project_files import ProjectFiles

router = APIRouter()


@router.get("/projects/{pid}/backend")
def get_backend(pid: str):
    """Coverage for the project's stack + what was generated last time."""
    s = _state(pid)
    stack = (s.stack_config or {}).get("stack")
    return {"coverage": stage.coverage(stack), "last": stage.status(ProjectFiles(pid))}


@router.post("/projects/{pid}/backend")
def generate_backend(pid: str):
    """(Re)generate the backend from the current spec. Files the user edited are kept and listed under `kept`."""
    s = _state(pid)
    if db.active_task(pid):
        raise HTTPException(409, "project has a running task; cancel it first")
    stack = (s.stack_config or {}).get("stack")
    if not stack:
        raise HTTPException(404, "this project has no stack configuration yet")
    spec, _ = spec_engine.ensure(s)
    result = stage.run(ProjectFiles(pid), spec, stack)
    # Explicit backend generation changes the project tree. Refresh project memory
    # in the same request so the stored file inventory does not immediately drift.
    if result.get("generated"):
        spec_memory.refresh(s, spec, "agent")
        project_store.save(s)
    return result

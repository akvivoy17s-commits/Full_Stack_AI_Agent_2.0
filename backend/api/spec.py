"""App spec + project memory API. Everything here is rule based (no LLM calls)."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend import spec as spec_engine
from backend.api.stack import _state
from backend.memory import project_store
from backend.spec import memory as spec_memory
from backend.stack import resolver
from backend.stack.schemas import Mode
from backend.storage import db

router = APIRouter()


class PreviewReq(BaseModel):
    brief: str = Field(min_length=1, max_length=2000)
    mode: Mode = "automatic"
    prefs: dict[str, str | None] = Field(default_factory=dict)
    overrides: dict = Field(default_factory=dict)


class OverridesReq(BaseModel):
    overrides: dict = Field(default_factory=dict)      # replaces all earlier edits; {} clears them


class DecisionReq(BaseModel):
    topic: str = Field(min_length=1, max_length=40)
    decision: str = Field(min_length=1, max_length=160)
    reason: str = Field(default="", max_length=200)


def _idle(pid: str) -> None:
    if db.active_task(pid):
        raise HTTPException(409, "project has a running task; cancel it first")


@router.post("/spec/preview")
def preview(body: PreviewReq):
    """Stateless: stack resolution + app spec for a brief, before any project exists (used by the creation flow)."""
    try:
        res = resolver.resolve(body.mode, body.prefs, body.brief, with_options=False)
    except ValueError as e:
        raise HTTPException(400, str(e))
    if not res["ok"]:
        return {"ok": False, "resolution": res, "spec": None}
    try:
        spec = spec_engine.build(body.brief, res["stack"], body.overrides)
    except ValueError as e:
        raise HTTPException(422, str(e))
    return {"ok": True, "resolution": res, "spec": spec}


@router.get("/projects/{pid}/spec")
def get_spec(pid: str):
    s = _state(pid)
    spec, changed = spec_engine.ensure(s)
    if changed:
        spec_memory.refresh(s, spec)
        project_store.save(s)
    return spec


@router.put("/projects/{pid}/spec")
def put_spec(pid: str, body: OverridesReq):
    s = _state(pid)
    _idle(pid)
    try:
        spec, _ = spec_engine.ensure(s, overrides=body.overrides, force=True)
    except ValueError as e:
        raise HTTPException(422, str(e))
    spec_memory.refresh(s, spec, "user")
    project_store.save(s)
    db.touch_project(pid)
    return spec


@router.get("/projects/{pid}/memory")
def get_memory(pid: str):
    s = _state(pid)
    if not spec_memory.load(pid):
        spec, _ = spec_engine.ensure(s)
        spec_memory.refresh(s, spec)
        project_store.save(s)
    return {"memory": spec_memory.load(pid), "check": spec_memory.check(s)}


@router.post("/projects/{pid}/memory/sync")
def sync_memory(pid: str):
    """Re-derive memory from the real repository (use when `check` reports drift). Decision history is kept."""
    s = _state(pid)
    _idle(pid)
    spec, _ = spec_engine.ensure(s)
    mem = spec_memory.refresh(s, spec)
    project_store.save(s)
    return {"memory": mem, "check": spec_memory.check(s)}


@router.post("/projects/{pid}/decisions")
def add_decision(pid: str, body: DecisionReq):
    s = _state(pid)
    mem = spec_memory.load(pid)
    if not mem:
        spec, _ = spec_engine.ensure(s)
        mem = spec_memory.refresh(s, spec)
    recorded = spec_memory.decide(mem, body.topic.strip(), body.decision.strip(), body.reason.strip(), "user")
    spec_memory._save(pid, mem)
    return {"recorded": recorded, "decisions": mem["decisions"]}

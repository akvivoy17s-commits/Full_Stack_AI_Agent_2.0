"""Technology selection API: catalog, live resolve/validate for the UI, and per-project stack persistence."""
import re

from fastapi import APIRouter, HTTPException

from backend.memory import project_store
from backend.stack import catalog, resolver
from backend import spec as spec_engine
from backend.spec import memory as spec_memory
from backend.stack.schemas import ApplyReq, ResolveReq
from backend.storage import db

router = APIRouter()
CORE = ("frontend", "frontend_lang")


def _state(pid: str):
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", pid) or not db.get_project(pid):
        raise HTTPException(404, "project not found")
    s = project_store.load(pid)
    if not s:
        raise HTTPException(404, "project not found")
    return s


@router.get("/stack/catalog")
def get_catalog():
    return catalog.public()


@router.post("/stack/resolve")
def resolve(body: ResolveReq):
    """Stateless: what would be selected (and why) for these preferences. Used live by the configuration UI."""
    existing = resolver.existing_from(_state(body.project_id)) if body.project_id else None
    try:
        return resolver.resolve(body.mode, body.prefs, body.brief, existing, with_options=body.options)
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.get("/projects/{pid}/stack")
def get_project_stack(pid: str):
    s = _state(pid)
    cfg = s.stack_config or {}
    if not cfg.get("stack"):
        raise HTTPException(404, "this project has no stack configuration yet")
    return {**cfg, **resolver.readiness(cfg["stack"]), "summary": resolver.summary(cfg["stack"])}


@router.put("/projects/{pid}/stack")
def put_project_stack(pid: str, body: ApplyReq):
    s = _state(pid)
    if db.active_task(pid):
        raise HTTPException(409, "project has a running task; cancel it first")
    try:
        res = resolver.resolve(body.mode, body.prefs, s.brief, resolver.existing_from(s))
    except ValueError as e:
        raise HTTPException(400, str(e))
    if not res["ok"]:
        raise HTTPException(422, {"errors": res["errors"], "warnings": res["warnings"]})
    old = (s.stack_config or {}).get("stack") or {}
    changes_frontend = any(old.get(f) != res["stack"].get(f) for f in CORE) and bool(old)
    if changes_frontend and s.sections_done and not body.confirm:
        raise HTTPException(409, "Changing the frontend after code was generated means regenerating it: resend with confirm=true")
    s.stack_config = resolver.config_of(res)
    legacy = res["derived"]["legacy_stack"]
    if legacy:
        s.stack = legacy
    regenerate = changes_frontend and bool(s.sections_done)
    if regenerate:
        s.plan, s.sections_done, s.phase = {}, [], "init"
    # Keep spec and project memory in sync with the saved stack in the same request. ensure(force=True)
    # preserves valid user spec overrides from the previous spec file while re-deriving contracts.
    spec, _ = spec_engine.ensure(s, force=True)
    spec_memory.refresh(s, spec, "user")
    project_store.save(s)
    db.touch_project(pid)
    return {**res, "requires_regenerate": regenerate, "spec": {"hash": spec.get("hash"), "kind": spec.get("kind")},
            "memory_consistent": spec_memory.check(s)["consistent"]}

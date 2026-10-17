import logging
import os
import re
import shutil
import stat
import uuid
from pathlib import Path
from typing import Literal
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from backend import config
from backend.agent.state import AgentState
from backend.api import system, tasks as tasks_api, stack as stack_api, spec as spec_api, backend_gen as backend_api, repo as repo_api, autopilot as autopilot_api, debug as debug_api
from backend import stack as stack_engine
from backend import spec as spec_engine
from backend.spec import memory as spec_memory
from backend.memory import project_store, history
from backend.storage import db
from backend.tools.project_files import ProjectFiles, is_secret
from backend.tools.validators import validate_file
from backend.tools.redact import redact
from backend import security



@asynccontextmanager
async def lifespan(_app):
    db.init()
    db.recover_interrupted()                       # tasks left running by a crash/restart
    for pid in project_store.list_projects():      # register projects created before SQLite existed
        st = project_store.load(pid)
        if st and not db.get_project(pid):
            db.upsert_project(pid, st.brief)
    yield


app = FastAPI(title="Frontend AI Engineer", version=config.VERSION, lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=config.CORS_ORIGINS,   # local dev origins only (see .env.example)
                   allow_methods=["*"], allow_headers=["*"])
app.middleware("http")(security.guard)
app.include_router(system.router)
app.include_router(tasks_api.router)
app.include_router(stack_api.router)
app.include_router(spec_api.router)
app.include_router(backend_api.router)
app.include_router(repo_api.router)
app.include_router(autopilot_api.router)
app.include_router(debug_api.router)


class NewProject(BaseModel):
    brief: str = Field(min_length=5, max_length=2000)
    framework: Literal["html", "react"] = "html"           # react = React + Vite + TypeScript output
    mode: Literal["automatic", "manual", "hybrid"] | None = None   # set -> technology selection engine (see /stack/catalog)
    prefs: dict[str, str | None] = Field(default_factory=dict)
    overrides: dict = Field(default_factory=dict)          # user edits to pages/features/entities from the creation wizard


def _idle(pid: str) -> None:
    if db.active_task(pid):
        raise HTTPException(409, "project has a running task; cancel it first")


@app.exception_handler(Exception)
async def _unhandled(_req, exc):
    logging.getLogger("backend").error("unhandled: %s", redact(repr(exc)))
    return JSONResponse({"detail": "internal error"}, status_code=500)           # never leak paths/tracebacks to clients


def _get(pid: str) -> AgentState:
    try:
        s = project_store.load(pid)
    except ValueError:
        s = None
    if not s:
        raise HTTPException(404, "project not found")
    return s


@app.post("/projects")
def create_project(body: NewProject):
    try:
        spec_engine.validate_overrides(body.overrides)         # reject bad edits before anything is created
    except ValueError as e:
        raise HTTPException(422, str(e))
    pid = re.sub(r"[^a-z0-9]+", "-", body.brief.lower())[:20].strip("-") + "-" + uuid.uuid4().hex[:6]
    res, legacy = stack_engine.for_new_project(body.mode, body.prefs, body.brief, body.framework)
    if body.mode and not res["ok"]:
        raise HTTPException(422, {"errors": res["errors"], "warnings": res["warnings"]})
    s = AgentState(project_id=pid, brief=body.brief, stack=legacy, stack_config=stack_engine.config_of(res))
    try:
        spec, _ = spec_engine.ensure(s, overrides=body.overrides or None)   # zero tokens: app spec + project memory exist from the first moment
    except ValueError as e:                              # e.g. an edit references an entity that was removed
        shutil.rmtree(ProjectFiles(pid).root, ignore_errors=True)
        raise HTTPException(422, str(e))
    spec_memory.refresh(s, spec, "user" if body.mode == "manual" or body.overrides else "agent")
    project_store.save(s)
    db.upsert_project(pid, body.brief)
    history.add(pid, "user", body.brief)
    extra = {"stack": res["stack"], "summary": res.get("summary"), "warnings": res["warnings"],
             "blocking": res.get("blocking", []), "pending": res.get("pending", []),
             "spec": {"kind": spec["kind"], "pages": [p["title"] for p in spec["pages"]], "features": spec["features"],
                      "entities": [e["name"] for e in spec["data"]["entities"]], "routes": len(spec["api"]["routes"]),
                      "gaps": spec["gaps"], "open_questions": spec["open_questions"]}} if body.mode else {}
    return {"project_id": pid, **extra}


@app.get("/projects")
def projects():
    return db.list_projects()


def _rm(path):
    """rmtree that also removes read-only files (node_modules on Windows)."""
    def onerr(func, p, _exc):
        try:
            os.chmod(p, stat.S_IWRITE)
            func(p)
        except OSError:
            pass
    shutil.rmtree(path, onerror=onerr, ignore_errors=False)


@app.delete("/projects/{pid}")
def delete_project(pid: str, confirm: bool = False):
    """Permanently delete a project: files, history, checkpoints, DB rows."""
    if not confirm:
        raise HTTPException(400, "confirm=true required")
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", pid):
        raise HTTPException(400, "invalid project id")
    root = (config.GENERATED_DIR / pid).resolve()
    if not db.get_project(pid) and not root.exists():
        raise HTTPException(404, "project not found")
    if db.active_task(pid):
        raise HTTPException(409, "project has a running task; cancel it first")
    for cp in db.delete_project(pid):
        try:
            Path(cp).unlink(missing_ok=True)
        except OSError:
            pass
    for d in (config.CHECKPOINT_DIR / pid, config.EXPORT_DIR / pid, root):
        if d.exists() and d.resolve().parent in (config.GENERATED_DIR.resolve(), config.CHECKPOINT_DIR.resolve(), config.EXPORT_DIR.resolve()):
            _rm(d)
    db.audit("delete_project", pid, "deleted")
    return {"deleted": pid}


@app.get("/projects/{pid}")
def project(pid: str):
    return _get(pid).to_dict()


@app.get("/projects/{pid}/files")
def files(pid: str):
    _get(pid)
    return ProjectFiles(pid).tree()


@app.get("/projects/{pid}/file")
def file(pid: str, path: str):
    _get(pid)
    if security.is_agent_path(path):
        raise HTTPException(404, "file not found")                  # agent internals are not served through the file API
    try:
        pf = ProjectFiles(pid)
        if pf._safe(path).stat().st_size > config.MAX_READ_BYTES:
            raise HTTPException(413, "file too large")
        text = pf.read(path)
    except (ValueError, OSError):
        raise HTTPException(404, "file not found")
    return {"path": path, "content": text, "issues": validate_file(path, text)}


@app.post("/projects/{pid}/generate")
def generate(pid: str, force: bool = False):
    _get(pid)
    _idle(pid)
    from backend.agent import orchestrator
    try:
        return orchestrator.run(pid, force)
    except (RuntimeError, ValueError) as e:
        raise HTTPException(500, redact(str(e)))


# ---------------- previews, screenshots ----------------
from fastapi.responses import FileResponse  # noqa: E402

EDITABLE = {"html", "css", "js", "json", "md", "svg", "txt"}


class SaveFile(BaseModel):
    path: str = Field(min_length=1, max_length=300)
    content: str = Field(max_length=config.MAX_FILE_BYTES)


class EditReq(BaseModel):
    section: str = Field(min_length=1, max_length=20)
    instruction: str = Field(min_length=3, max_length=500)


@app.put("/projects/{pid}/file")
def save_file(pid: str, body: SaveFile):
    _get(pid)
    _idle(pid)
    if security.is_agent_path(body.path) or body.path.rsplit(".", 1)[-1].lower() not in EDITABLE:
        raise HTTPException(400, "path not editable")
    try:
        ProjectFiles(pid).write(body.path, body.content)
    except ValueError as e:
        raise HTTPException(400, redact(str(e)))
    return {"issues": validate_file(body.path, body.content)}


@app.post("/projects/{pid}/verify")
def verify(pid: str, repair: bool = True):
    _get(pid)
    _idle(pid)
    from backend.agent import orchestrator
    try:
        return orchestrator.verify(pid, do_repair=repair)
    except (RuntimeError, ValueError) as e:
        raise HTTPException(500, redact(str(e)))


@app.post("/projects/{pid}/edit")
def edit(pid: str, body: EditReq):
    _get(pid)
    _idle(pid)
    from backend.agent import orchestrator
    try:
        return orchestrator.edit(pid, body.section, body.instruction)
    except (RuntimeError, ValueError) as e:
        raise HTTPException(500, redact(str(e)))


@app.get("/projects/{pid}/shots")
def shots(pid: str):
    _get(pid)
    from backend.tools import screenshots
    return screenshots.list_shots(ProjectFiles(pid))


@app.get("/projects/{pid}/shot/{name}")
def shot(pid: str, name: str):
    _get(pid)
    if not re.fullmatch(r"[a-z0-9_-]+\.png", name):
        raise HTTPException(404)
    p = ProjectFiles(pid).root / ".agent" / "shots" / name
    if not p.is_file():
        raise HTTPException(404)
    return FileResponse(p)


@app.get("/preview/{pid}/{path:path}")
def preview(pid: str, path: str = ""):
    s = _get(pid)
    pf = ProjectFiles(pid)
    react = s.plan.get("stack", s.stack) == "react"
    base = (pf.root / "dist") if react else pf.root          # React projects are previewed from the real production build
    try:
        pf._safe(path or "index.html")                         # same traversal rules as every other file access
        p = (base / (path or "index.html")).resolve()
        if p.is_dir():
            p = p / "index.html"
        if p != base.resolve() and base.resolve() not in p.parents:
            raise ValueError("outside")
        rel = p.relative_to(pf.root).parts
    except ValueError:
        raise HTTPException(404)
    if ".agent" in rel or is_secret(p.name) or not p.is_file():
        raise HTTPException(404, "not built yet: run Verify" if react else "not found")
    return FileResponse(p)

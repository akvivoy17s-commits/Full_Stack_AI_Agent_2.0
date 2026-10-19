from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Literal

from backend.api.tasks import _project
from backend.memory import task_memory
from backend.repo import mapper
from backend.storage import db

router = APIRouter()


class MemoryIn(BaseModel):
    kind: Literal["note", "decision", "next"] = "note"          # failures are recorded by the agent itself, not by hand
    text: str = Field(min_length=2, max_length=300)


@router.get("/projects/{pid}/repo")
def repo_map(pid: str, refresh: bool = False, full: bool = False):
    _project(pid)
    m = mapper.get(pid, refresh)
    return {**mapper.summary(m), "stale": False, **({"files": m["files"]} if full else {})}


@router.post("/projects/{pid}/repo/refresh")
def repo_refresh(pid: str, force: bool = False):
    _project(pid)
    return mapper.summary(mapper.build(pid, force))


@router.get("/projects/{pid}/repo/search")
def repo_search(pid: str, q: str, limit: int = 10):
    _project(pid)
    return mapper.search(pid, q[:100], limit)


@router.get("/projects/{pid}/repo/file")
def repo_file(pid: str, path: str):
    _project(pid)
    o = mapper.outline(pid, path)
    if not o:
        raise HTTPException(404, "file not in repo map")
    return o


@router.get("/projects/{pid}/memory/tasks")
def memory_list(pid: str, kind: str = "", status: str = "", limit: int = 30):
    _project(pid)
    return db.list_memory(pid, kind if kind in db.MEM_KINDS else "", status if status in ("open", "done") else "", max(1, min(limit, 100)))


@router.post("/projects/{pid}/memory/tasks", status_code=201)
def memory_add(pid: str, body: MemoryIn):
    _project(pid)
    return {"id": task_memory.add(pid, body.kind, body.text)}


@router.post("/projects/{pid}/memory/tasks/{mid}/close")
def memory_close(pid: str, mid: int):
    _project(pid)
    if not db.close_memory(pid, mid):
        raise HTTPException(404, "open memory item not found")
    return {"closed": mid}


@router.get("/projects/{pid}/resume")
def resume(pid: str):
    _project(pid)
    return task_memory.resume(pid)


@router.get("/projects/{pid}/context")
def context(pid: str, budget: int = 1500):
    _project(pid)
    return {"context": task_memory.context(pid, max(200, min(budget, 6000)))}

# Project-aware analysis and Git inspection, used by the IDE before/after edits.
from backend.tools import git as git_tools, project_scanner, language_analyzer
from backend.tools.project_files import ProjectFiles


class AnalysisRequest(BaseModel):
    deep: bool = False  # opt-in: may invoke existing local compiler/build/test scripts; never installs dependencies


class BranchRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    confirm: bool = False


class CommitRequest(BaseModel):
    message: str = Field(min_length=1, max_length=200)
    paths: list[str] = Field(min_length=1, max_length=30)
    confirm: bool = False


@router.get("/projects/{pid}/scan")
def project_scan(pid: str):
    """Return a bounded project map: technology hints, entry points, routes and manifests."""
    _project(pid)
    return project_scanner.scan(ProjectFiles(pid))


@router.post("/projects/{pid}/analyze")
def project_language_analysis(pid: str, body: AnalysisRequest):
    """Analyze language syntax, conservative logic/redundancy hints, and installed toolchain coverage."""
    _project(pid)
    if body.deep and db.active_task(pid):
        raise HTTPException(409, "project has a running task; cancel it before running compiler/build checks")
    try:
        return language_analyzer.analyze_project(ProjectFiles(pid), deep=body.deep)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from None


@router.get("/projects/{pid}/git")
def git_status(pid: str):
    _project(pid)
    return git_tools.status(pid)


@router.get("/projects/{pid}/git/diff")
def git_diff(pid: str, path: str | None = None):
    _project(pid)
    try:
        return git_tools.diff(pid, path)
    except ValueError as e:
        raise HTTPException(400, str(e)) from None


@router.get("/projects/{pid}/git/log")
def git_log(pid: str, limit: int = 10):
    _project(pid)
    return git_tools.log(pid, max(1, min(limit, 30)))


@router.post("/projects/{pid}/git/branch")
def git_create_branch(pid: str, body: BranchRequest):
    _project(pid)
    if db.active_task(pid):
        raise HTTPException(409, "project has a running task; cancel it first")
    try:
        result = git_tools.create_branch(pid, body.name.strip(), body.confirm)
        db.audit("git_branch", pid, result["branch"])
        return result
    except ValueError as e:
        raise HTTPException(400, str(e)) from None


@router.post("/projects/{pid}/git/commit")
def git_commit(pid: str, body: CommitRequest):
    _project(pid)
    if db.active_task(pid):
        raise HTTPException(409, "project has a running task; cancel it first")
    try:
        result = git_tools.commit(pid, body.message, body.paths, body.confirm)
        db.audit("git_commit", pid, f"{result['commit']} {result['message'][:100]}")
        return result
    except ValueError as e:
        raise HTTPException(400, str(e)) from None

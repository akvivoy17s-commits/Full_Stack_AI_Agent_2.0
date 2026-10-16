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

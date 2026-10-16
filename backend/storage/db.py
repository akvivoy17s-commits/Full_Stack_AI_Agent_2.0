"""SQLite storage: projects, tasks, task events (audit log), checkpoints, test summaries, settings."""
import json
import sqlite3
import time
from contextlib import contextmanager

from backend import config
from backend.tools.redact import redact

SCHEMA = """
CREATE TABLE IF NOT EXISTS projects(id TEXT PRIMARY KEY, name TEXT, brief TEXT, created_at REAL, updated_at REAL, settings TEXT DEFAULT '{}');
CREATE TABLE IF NOT EXISTS tasks(id TEXT PRIMARY KEY, project_id TEXT, kind TEXT, status TEXT, params TEXT DEFAULT '{}',
  spec TEXT DEFAULT '{}', result TEXT, error TEXT, checkpoint_id TEXT, tokens_in INTEGER DEFAULT 0, tokens_out INTEGER DEFAULT 0,
  created_at REAL, started_at REAL, finished_at REAL);
CREATE INDEX IF NOT EXISTS ix_tasks_project ON tasks(project_id, created_at);
CREATE TABLE IF NOT EXISTS task_events(id INTEGER PRIMARY KEY AUTOINCREMENT, task_id TEXT, ts REAL, level TEXT, stage TEXT, msg TEXT);
CREATE INDEX IF NOT EXISTS ix_events_task ON task_events(task_id, id);
CREATE TABLE IF NOT EXISTS checkpoints(id TEXT PRIMARY KEY, project_id TEXT, label TEXT, task_id TEXT, path TEXT, size INTEGER, created_at REAL);
CREATE TABLE IF NOT EXISTS test_summaries(id INTEGER PRIMARY KEY AUTOINCREMENT, project_id TEXT, task_id TEXT, summary TEXT, created_at REAL);
CREATE TABLE IF NOT EXISTS repair_attempts(id INTEGER PRIMARY KEY AUTOINCREMENT, project_id TEXT, task_id TEXT, attempt INTEGER, sid TEXT,
  issue TEXT, sig TEXT, method TEXT, outcome TEXT, created_at REAL);
CREATE INDEX IF NOT EXISTS ix_repairs_project ON repair_attempts(project_id, id);
CREATE TABLE IF NOT EXISTS task_steps(task_id TEXT, seq INTEGER, key TEXT, title TEXT, status TEXT DEFAULT 'pending', detail TEXT DEFAULT '',
  started_at REAL, finished_at REAL, PRIMARY KEY(task_id, key));
CREATE TABLE IF NOT EXISTS task_memory(id INTEGER PRIMARY KEY AUTOINCREMENT, project_id TEXT, task_id TEXT, kind TEXT, text TEXT,
  status TEXT DEFAULT 'open', created_at REAL);
CREATE INDEX IF NOT EXISTS ix_tmem_project ON task_memory(project_id, id);
CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY AUTOINCREMENT, ts REAL, action TEXT, project_id TEXT, detail TEXT);
"""
TERMINAL = ("succeeded", "completed_with_issues", "failed", "cancelled")


@contextmanager
def conn():
    c = sqlite3.connect(config.DB_PATH, timeout=10)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA journal_mode=WAL")
    try:
        yield c
        c.commit()
    finally:
        c.close()


def init() -> None:
    with conn() as c:
        c.executescript(SCHEMA)


def _d(row):
    return dict(row) if row else None


# ---- projects
def upsert_project(pid: str, brief: str = "", name: str = "") -> None:
    now = time.time()
    with conn() as c:
        c.execute("INSERT INTO projects(id,name,brief,created_at,updated_at) VALUES(?,?,?,?,?) "
                  "ON CONFLICT(id) DO UPDATE SET updated_at=excluded.updated_at",
                  (pid, name or brief[:40] or pid, brief, now, now))


def touch_project(pid: str) -> None:
    with conn() as c:
        c.execute("UPDATE projects SET updated_at=? WHERE id=?", (time.time(), pid))


def list_projects() -> list[dict]:
    with conn() as c:
        return [dict(r) for r in c.execute("SELECT id,name,brief,created_at,updated_at FROM projects ORDER BY updated_at DESC")]


def get_project(pid: str):
    with conn() as c:
        return _d(c.execute("SELECT * FROM projects WHERE id=?", (pid,)).fetchone())


def delete_project(pid: str) -> list[str]:
    """Remove every DB row of a project. Returns checkpoint file paths so the caller can delete them."""
    with conn() as c:
        paths = [r["path"] for r in c.execute("SELECT path FROM checkpoints WHERE project_id=?", (pid,))]
        c.execute("DELETE FROM task_events WHERE task_id IN (SELECT id FROM tasks WHERE project_id=?)", (pid,))
        for t in ("tasks", "checkpoints", "test_summaries", "repair_attempts", "task_memory"):
            c.execute(f"DELETE FROM {t} WHERE project_id=?", (pid,))
        c.execute("DELETE FROM projects WHERE id=?", (pid,))
    return paths


# ---- tasks
def create_task(tid: str, pid: str, kind: str, params: dict) -> dict:
    with conn() as c:
        c.execute("INSERT INTO tasks(id,project_id,kind,status,params,created_at) VALUES(?,?,?,?,?,?)",
                  (tid, pid, kind, "queued", json.dumps(params), time.time()))
    return get_task(tid)


def update_task(tid: str, **f) -> None:
    for k in ("result", "spec", "params"):
        if k in f and not isinstance(f[k], str):
            f[k] = json.dumps(f[k])
    if "error" in f and f["error"]:
        f["error"] = redact(f["error"])[:2000]
    with conn() as c:
        c.execute(f"UPDATE tasks SET {','.join(k + '=?' for k in f)} WHERE id=?", (*f.values(), tid))


def get_task(tid: str):
    with conn() as c:
        r = _d(c.execute("SELECT * FROM tasks WHERE id=?", (tid,)).fetchone())
    if r:
        for k in ("params", "spec", "result"):
            r[k] = json.loads(r[k]) if r.get(k) else None
    return r


def list_tasks(pid: str, limit: int = 30) -> list[dict]:
    with conn() as c:
        rows = c.execute("SELECT id,kind,status,error,checkpoint_id,tokens_in,tokens_out,created_at,started_at,finished_at "
                         "FROM tasks WHERE project_id=? ORDER BY created_at DESC LIMIT ?", (pid, limit)).fetchall()
    return [dict(r) for r in rows]


def active_task(pid: str):
    with conn() as c:
        return _d(c.execute("SELECT id,kind,status FROM tasks WHERE project_id=? AND status IN ('queued','running') LIMIT 1", (pid,)).fetchone())


def recover_interrupted() -> int:
    with conn() as c:
        cur = c.execute("UPDATE tasks SET status='failed', error='interrupted by server restart', finished_at=? "
                        "WHERE status IN ('queued','running')", (time.time(),))
        return cur.rowcount


def add_event(tid: str, stage: str, msg: str, level: str = "info") -> None:
    with conn() as c:
        c.execute("INSERT INTO task_events(task_id,ts,level,stage,msg) VALUES(?,?,?,?,?)",
                  (tid, time.time(), level, stage, redact(msg)[:1000]))


def events_after(tid: str, after: int = 0, limit: int = 200) -> list[dict]:
    with conn() as c:
        return [dict(r) for r in c.execute("SELECT id,ts,level,stage,msg FROM task_events WHERE task_id=? AND id>? ORDER BY id LIMIT ?",
                                           (tid, after, limit))]


# ---- task steps (progress tracking)
def set_steps(tid: str, steps: list[tuple[str, str]]) -> None:
    with conn() as c:
        c.execute("DELETE FROM task_steps WHERE task_id=?", (tid,))
        c.executemany("INSERT INTO task_steps(task_id,seq,key,title) VALUES(?,?,?,?)", [(tid, i, k, t) for i, (k, t) in enumerate(steps)])


def update_step(tid: str, key: str, status: str, detail: str = "") -> None:
    now = time.time()
    with conn() as c:
        if status == "running":
            c.execute("UPDATE task_steps SET status=?, detail=?, started_at=? WHERE task_id=? AND key=?", (status, redact(detail)[:300], now, tid, key))
        else:
            c.execute("UPDATE task_steps SET status=?, detail=?, finished_at=?, started_at=COALESCE(started_at,?) WHERE task_id=? AND key=?",
                      (status, redact(detail)[:300], now, now, tid, key))


def list_steps(tid: str) -> list[dict]:
    with conn() as c:
        return [dict(r) for r in c.execute("SELECT key,title,status,detail,started_at,finished_at FROM task_steps WHERE task_id=? ORDER BY seq", (tid,))]


# ---- checkpoints / summaries / audit
def add_checkpoint(cid, pid, label, task_id, path, size) -> None:
    with conn() as c:
        c.execute("INSERT INTO checkpoints VALUES(?,?,?,?,?,?,?)", (cid, pid, label[:80], task_id, str(path), size, time.time()))


def list_checkpoints(pid: str) -> list[dict]:
    with conn() as c:
        return [dict(r) for r in c.execute("SELECT id,label,task_id,size,created_at FROM checkpoints WHERE project_id=? ORDER BY created_at DESC", (pid,))]


def get_checkpoint(pid: str, cid: str):
    with conn() as c:
        return _d(c.execute("SELECT * FROM checkpoints WHERE id=? AND project_id=?", (cid, pid)).fetchone())


def delete_checkpoint(cid: str) -> None:
    with conn() as c:
        c.execute("DELETE FROM checkpoints WHERE id=?", (cid,))


def add_summary(pid: str, task_id: str, summary: dict) -> None:
    with conn() as c:
        c.execute("INSERT INTO test_summaries(project_id,task_id,summary,created_at) VALUES(?,?,?,?)",
                  (pid, task_id, redact(json.dumps(summary))[:8000], time.time()))


def list_summaries(pid: str, limit: int = 10) -> list[dict]:
    with conn() as c:
        rows = c.execute("SELECT task_id,summary,created_at FROM test_summaries WHERE project_id=? ORDER BY id DESC LIMIT ?", (pid, limit)).fetchall()
    return [{"task_id": r["task_id"], "created_at": r["created_at"], "summary": json.loads(r["summary"])} for r in rows]


def add_repair_attempt(pid: str, task_id: str, attempt: int, sid: str, issue: str, sig: str, method: str, outcome: str) -> None:
    """outcome: fixed | still_failing | error. One row per (section, issue) per repair loop."""
    with conn() as c:
        c.execute("INSERT INTO repair_attempts(project_id,task_id,attempt,sid,issue,sig,method,outcome,created_at) VALUES(?,?,?,?,?,?,?,?,?)",
                  (pid, task_id, attempt, sid, redact(issue)[:300], sig, method, outcome, time.time()))


def list_repair_attempts(pid: str, limit: int = 60) -> list[dict]:
    with conn() as c:
        rows = c.execute("SELECT task_id,attempt,sid,issue,method,outcome,created_at FROM repair_attempts WHERE project_id=? ORDER BY id DESC LIMIT ?",
                         (pid, limit)).fetchall()
    return [dict(r) for r in rows]


# ---- persistent task memory (kinds: note | decision | failure | next; status: open | done)
MEM_KINDS = ("note", "decision", "failure", "next")
MEM_CAP = 200


def add_memory(pid: str, task_id: str, kind: str, text: str) -> int | None:
    """Store one memory row. Skips an exact duplicate of the latest open row of the same kind. Returns the row id."""
    text = redact(text).strip()[:300]
    if kind not in MEM_KINDS or not text:
        return None
    with conn() as c:
        last = c.execute("SELECT id,text FROM task_memory WHERE project_id=? AND kind=? AND status='open' ORDER BY id DESC LIMIT 1", (pid, kind)).fetchone()
        if last and last["text"] == text:
            return None
        cur = c.execute("INSERT INTO task_memory(project_id,task_id,kind,text,created_at) VALUES(?,?,?,?,?)", (pid, task_id or "", kind, text, time.time()))
        c.execute("DELETE FROM task_memory WHERE project_id=? AND id NOT IN (SELECT id FROM task_memory WHERE project_id=? ORDER BY id DESC LIMIT ?)",
                  (pid, pid, MEM_CAP))
        return cur.lastrowid


def list_memory(pid: str, kind: str = "", status: str = "", limit: int = 30) -> list[dict]:
    q, a = "SELECT id,task_id,kind,text,status,created_at FROM task_memory WHERE project_id=?", [pid]
    for col, v in (("kind", kind), ("status", status)):
        if v:
            q, a = q + f" AND {col}=?", a + [v]
    with conn() as c:
        return [dict(r) for r in c.execute(q + " ORDER BY id DESC LIMIT ?", (*a, limit))]


def close_memory(pid: str, mid: int | None = None, prefix: str = "") -> int:
    """Mark open rows done: one by id, or every open `next` row starting with prefix. Returns rows changed."""
    with conn() as c:
        if mid is not None:
            return c.execute("UPDATE task_memory SET status='done' WHERE project_id=? AND id=? AND status='open'", (pid, mid)).rowcount
        return c.execute("UPDATE task_memory SET status='done' WHERE project_id=? AND kind='next' AND status='open' AND text LIKE ?",
                         (pid, prefix.replace("%", "") + "%")).rowcount


def audit(action: str, pid: str = "", detail: str = "") -> None:
    with conn() as c:
        c.execute("INSERT INTO audit(ts,action,project_id,detail) VALUES(?,?,?,?)", (time.time(), action, pid, redact(detail)[:500]))


# ---- settings
def get_settings() -> dict:
    with conn() as c:
        saved = {r["key"]: json.loads(r["value"]) for r in c.execute("SELECT key,value FROM settings")}
    return {**config.DEFAULT_SETTINGS, **{k: v for k, v in saved.items() if k in config.DEFAULT_SETTINGS}}


def save_settings(values: dict) -> None:
    with conn() as c:
        for k, v in values.items():
            c.execute("INSERT INTO settings VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (k, json.dumps(v)))


init()

"""Phase 4: requirement analysis, step tracking/progress, honest verdicts, and the tracked generate pipeline."""
import pytest

from backend.agent import context, progress, requirements
from backend.spec import compose as B
from backend.stack import resolve
from backend.storage import db

db.init()


def _spec(brief, backend=True):
    st = resolve("automatic", {}, brief)["stack"]
    if not backend:
        st = {**st, "backend": "none", "database": "none", "auth": "none"}
    return B.build(brief, st)


# ---------------------------------------------------------------- requirement analysis
def test_requirements_cover_pages_features_data_and_api():
    a = requirements.analyze(_spec("online store with login, razorpay payments and image uploads"))
    kinds = {r["kind"] for r in a["requirements"]}
    assert {"functional", "page", "data", "api", "security"} <= kinds
    assert a["counts"]["covered"] + a["counts"]["planned"] + a["counts"]["gap"] == len(a["requirements"])
    assert all(r["status"] in ("covered", "planned", "gap") for r in a["requirements"])


def test_gap_when_brief_needs_backend_but_stack_has_none():
    a = requirements.analyze(_spec("online store with login and database", backend=False))
    assert a["gaps"] and a["counts"]["gap"] >= 1


def test_contradictory_brief_is_blocking():
    st = {"frontend": "html", "frontend_lang": "js", "backend": "none"}
    a = requirements.analyze(B.build("store with login and checkout but no backend", st))
    assert a["blocking"] and a["blocking"][0]["id"] == "backend-conflict"


def test_planned_status_is_never_reported_as_covered():
    spec = _spec("personal portfolio website")
    spec["plan"] = [{"id": "pages", "status": "planned:5", "title": "p", "area": "frontend"}]
    a = requirements.analyze(spec)
    ui = [r for r in a["requirements"] if r["kind"] in ("functional", "page")]
    assert ui and all(r["status"] == "planned" for r in ui)


# ---------------------------------------------------------------- tracker + percent
def _tracker_in_task(kind="generate"):
    tid = "t4-" + kind
    ctx = context.TaskContext(tid, lambda stage, msg, lvl="info": db.add_event(tid, stage, msg, lvl))
    context.bind(ctx)
    return tid, progress.Tracker(kind)


def teardown_function(_):
    context.bind(None)


def test_tracker_persists_steps_and_percent():
    tid, tr = _tracker_in_task()
    assert tr.percent() == 0 and len(db.list_steps(tid)) == 6
    with tr.step("analyze") as o:
        o["detail"] = "ok"
    tr.skip("plan", "exists")
    rows = {s["key"]: s for s in db.list_steps(tid)}
    assert rows["analyze"]["status"] == "done" and rows["plan"]["status"] == "skipped"
    assert tr.percent() == round(100 * 2 / 6)
    snap = progress.snapshot(tid)
    assert snap["percent"] == tr.percent() and snap["current"] is None
    assert any(e["stage"] == "step" for e in db.events_after(tid))


def test_failed_step_is_recorded_and_exception_propagates():
    tid, tr = _tracker_in_task("verify")
    with pytest.raises(RuntimeError):
        with tr.step("verify"):
            raise RuntimeError("boom")
    assert db.list_steps(tid)[0]["status"] == "failed"
    assert progress.verdict(tr.steps, [])["verdict"] == "FAIL"


def test_cancel_during_a_step_marks_it_cancelled():
    tid, tr = _tracker_in_task("test")
    with pytest.raises(context.Cancelled):
        with tr.step("verify"):
            context.current().cancel.set()
            context.check()
    assert db.list_steps(tid)[0]["status"] == "cancelled"
    assert progress.verdict(tr.steps, [])["verdict"] == "FAIL"


def test_tracker_works_without_a_task():
    context.bind(None)
    tr = progress.Tracker("edit")
    with tr.step("edit"):
        pass
    assert tr.steps[0]["status"] == "done" and tr.percent() == 50


# ---------------------------------------------------------------- verdict (evidence based)
def _steps(*statuses):
    return [{"key": f"s{i}", "status": s, "detail": ""} for i, s in enumerate(statuses)]


def test_verdicts():
    assert progress.verdict(_steps("done", "skipped", "done"), [])["verdict"] == "PASS"
    assert progress.verdict(_steps("done", "done"), ["x"])["verdict"] == "PARTIAL"
    assert progress.verdict(_steps("done", "pending"), [])["verdict"] == "PARTIAL"
    assert progress.verdict(_steps("done"), [], {"counts": {"planned": 2, "gap": 0}})["verdict"] == "PARTIAL"
    assert progress.verdict(_steps("done"), [], {"blocking": [{"question": "q?"}]})["verdict"] == "BLOCKED"
    assert progress.verdict(_steps("done", "failed"), [])["verdict"] == "FAIL"
    assert progress.verdict(_steps("done"), [], None, "backend not generated")["verdict"] == "PARTIAL"


# ---------------------------------------------------------------- full pipeline (mock LLM, needs fastapi/pydantic installed)
def test_generate_task_reports_steps_and_verdict():
    from backend.agent import tasks
    from backend.agent.state import AgentState
    from backend.memory import project_store
    import time
    project_store.save(AgentState("t4-pipe", "fitness app landing page"))
    db.upsert_project("t4-pipe", "fitness app landing page")
    t = tasks.submit("t4-pipe", "generate", {"force": True})
    for _ in range(300):
        cur = db.get_task(t["id"])
        if cur["status"] in db.TERMINAL:
            break
        time.sleep(0.2)
    assert cur["status"] in ("succeeded", "completed_with_issues"), cur["error"]
    res = cur["result"]
    keys = [s["key"] for s in res["steps"]]
    assert keys == ["analyze", "plan", "design", "backend", "code", "verify"]
    assert all(s["status"] != "pending" for s in res["steps"]) and res["percent"] == 100
    assert res["outcome"]["verdict"] in ("PASS", "PARTIAL")
    assert [s["key"] for s in db.list_steps(t["id"])] == keys


def test_progress_and_requirements_endpoints():
    from fastapi.testclient import TestClient
    from backend.main import app
    c = TestClient(app)
    tid = db.list_tasks("t4-pipe")[0]["id"]
    j = c.get(f"/tasks/{tid}/progress").json()
    assert j["percent"] == 100 and len(j["steps"]) == 6
    assert c.get("/projects/t4-pipe/requirements").json()["requirements"]
    assert c.get("/tasks/nope/progress").status_code == 404

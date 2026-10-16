"""A stored spec whose plan statuses are older than the current generators is refreshed instead of reused."""
import json

from backend.agent.state import AgentState
from backend.memory import project_store
from backend.spec import compose
from backend.storage import db
from backend.tools.project_files import ProjectFiles
from gen_helpers import stack_for


def test_stale_plan_in_stored_spec_is_rebuilt():
    pid = "plan-refresh-1"
    st = stack_for("sqlite", "analytics dashboard", backend="express")
    state = AgentState(pid, "analytics dashboard")
    state.stack_config = {"stack": st}
    project_store.save(state)
    db.upsert_project(pid, "analytics dashboard")
    spec, changed = compose.ensure(state)
    assert changed and {s["id"]: s["status"] for s in spec["plan"]}["tests"] == "ready"
    stale = json.loads(json.dumps(spec))
    for s in stale["plan"]:
        if s["id"] in ("tests", "wiring"):
            s["status"] = "planned:7"
    ProjectFiles(pid).write(".agent/spec.json", json.dumps(stale))
    spec2, changed2 = compose.ensure(state)
    assert changed2 and all(s["status"] == "ready" for s in spec2["plan"] if s["id"] in ("tests", "wiring"))
    _, changed3 = compose.ensure(state)
    assert changed3 is False                                       # stable once refreshed

"""Phase 1: how the selected stack is stored on a project and enforced before generation (no FastAPI needed)."""
import pytest

from backend import stack as stack_engine
from backend.agent import context, orchestrator
from backend.agent.state import AgentState


def _state(stack, sources=None):
    return AgentState(project_id="p1", brief="x", stack_config={"mode": "hybrid", "stack": stack, "sources": sources or {}})


def test_legacy_request_stays_frontend_only():
    for fw, lang in (("html", "js"), ("react", "ts")):
        res, legacy = stack_engine.for_new_project(None, None, "anything", fw)
        s = res["stack"]
        assert res["ok"] and legacy == fw
        assert (s["frontend"], s["frontend_lang"], s["backend"], s["database"]) == (fw, lang, "none", "none")
        assert not res["blocking"]


def test_new_flow_stores_stack_sources_and_reasons():
    res, _ = stack_engine.for_new_project("hybrid", {"backend": "express"}, "SaaS dashboard with login", "html")
    cfg = stack_engine.config_of(res)
    assert cfg["mode"] == "hybrid" and cfg["stack"]["backend"] == "express" and cfg["sources"]["backend"] == "user"
    assert cfg["reasons"]["database"]


def test_old_state_files_without_stack_config_still_load():
    old = {"project_id": "p", "brief": "b", "phase": "done", "plan": {}, "design": {}, "files": {}, "errors": [], "repair_count": 0,
           "motion": {}, "sections_done": [], "usage": {"in": 0, "out": 0}, "stack": "html", "layout": "landing"}
    assert AgentState.from_dict(old).stack_config == {}
    orchestrator._stack_gate(AgentState.from_dict(old))          # legacy projects are never gated


def test_existing_from_drops_automatic_picks():
    st = _state({"frontend": "react", "frontend_lang": "ts", "backend": "express", "testing": "vitest"},
                {"frontend": "user", "frontend_lang": "auto", "backend": "brief", "testing": "default"})
    assert stack_engine.existing_from(st) == {"frontend": "react", "backend": "express"}


def test_gate_refuses_a_frontend_without_generator():
    st = _state({"frontend": "angular", "frontend_lang": "ts", "backend": "none", "database": "none"})
    with pytest.raises(ValueError, match="Angular"):
        orchestrator._stack_gate(st)


def _gate_events(stack):
    events = []
    ctx = context.TaskContext("t1", lambda stage, msg, lvl="info": events.append((stage, msg, lvl)))
    context.bind(ctx)
    try:
        orchestrator._stack_gate(_state(stack))
    finally:
        context.bind(None)
    return events


def test_gate_warns_about_unbuilt_parts_but_allows_the_frontend():
    events = _gate_events({"frontend": "react", "frontend_lang": "ts", "backend": "nestjs", "database": "postgresql",
                           "auth": "jwt", "ai": "llm-api", "cache": "redis", "storage": "local", "testing": "vitest", "deploy": "local"})
    text = " ".join(m for _, m, _ in events)
    assert all(lvl == "warn" for _, _, lvl in events) and "Vitest" in text and "Redis" not in text


def test_gate_is_silent_for_a_stack_the_backend_generator_covers():
    events = _gate_events({"frontend": "react", "frontend_lang": "ts", "backend": "express", "backend_lang": "js", "database": "postgresql",
                           "auth": "jwt", "ai": "none", "cache": "none", "storage": "none", "testing": "none", "deploy": "local"})
    assert events == []

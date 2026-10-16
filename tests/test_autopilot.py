"""Regression tests for prompt-only project creation and deterministic app-shell generation."""
import pytest

from backend.agent import planner
from backend.agent.state import AgentState
from backend.api.autopilot import AutoBuildRequest, resolve_prompt
from backend.engines import app_engine
from backend.stack import config_of
from backend.spec import ensure as ensure_spec
from backend.tools.project_files import ProjectFiles


def test_autobuild_selects_react_for_common_crud_apps():
    for prompt in (
        "Build a todo app with task status, due dates, search and persistence",
        "Create a notes app with tags, pinning and search",
        "Build a CRM management dashboard for customers and deals",
    ):
        result, _legacy, _assumptions, app_shell = resolve_prompt(prompt)
        assert result["ok"], result.get("errors")
        assert app_shell
        stack = result["stack"]
        assert stack["frontend"] == "react"
        assert stack["frontend_lang"] == "ts"


def test_marketing_site_does_not_get_misclassified_as_crud_app():
    result, legacy, _assumptions, app_shell = resolve_prompt(
        "Create a company landing page for a coffee shop"
    )
    assert result["ok"], result.get("errors")
    assert legacy == "html"
    assert not app_shell
    assert planner.layout_for("Create a company landing page for a coffee shop") == "landing"


def test_planner_chooses_app_layout_for_management_and_notes():
    assert planner.layout_for("Create an admin management system", "management") == "app"
    assert planner.layout_for("Analytics dashboard for sales", "dashboard") == "dashboard"
    assert planner.layout_for("Create a notes app with tags", "generic") == "app"
    assert planner.layout_for("Create a personal portfolio", "portfolio") == "portfolio"


def test_generated_todo_shell_has_real_crud_and_no_unfilled_template():
    prompt = "Build a todo app with title, description, status and search"
    resolved, legacy, _assumptions, app_shell = resolve_prompt(prompt)
    assert resolved["ok"] and app_shell
    pid = "autopilot-test-todo"
    pf = ProjectFiles(pid)
    try:
        state = AgentState(project_id=pid, brief=prompt, stack=legacy,
                           stack_config=config_of(resolved))
        state.stack_config["autopilot"] = {"prompt_only": True, "app_shell": True, "assumptions": []}
        spec, _ = ensure_spec(state)
        state.plan = {"layout": "app", "brand": "Task Space", "sections": ["app"]}
        report = app_engine.generate(pf, state)
        source = pf.read("src/App.tsx")
        assert report["entities"] >= 1
        assert "function submitForm" in source
        assert "function removeRow" in source
        assert "function startEdit(row: Row)" in source
        assert "__PAYLOAD__" not in source
        assert "localStorage" in source or report["api_enabled"]
        assert "dataMode" in source
    finally:
        import shutil
        shutil.rmtree(pf.root, ignore_errors=True)


def test_calculator_prompt_uses_safe_deterministic_generator():
    prompt = "Create a responsive calculator app"
    resolved, legacy, _assumptions, app_shell = resolve_prompt(prompt)
    assert resolved["ok"] and app_shell
    pid = "autopilot-test-calculator"
    pf = ProjectFiles(pid)
    try:
        state = AgentState(project_id=pid, brief=prompt, stack=legacy,
                           stack_config=config_of(resolved))
        state.stack_config["autopilot"] = {"prompt_only": True, "app_shell": True, "assumptions": []}
        ensure_spec(state)
        state.plan = {"layout": "app", "brand": "Calculator", "sections": ["app"]}
        report = app_engine.generate(pf, state)
        source = pf.read("src/App.tsx")
        assert report["tool"] == "calculator"
        assert "function calculate" in source
        assert "eval(" not in source
        assert "divide by zero" in source.lower()
        assert "__TITLE__" not in source
    finally:
        import shutil
        shutil.rmtree(pf.root, ignore_errors=True)


def test_autobuild_prompt_is_trimmed_and_control_characters_are_rejected():
    assert AutoBuildRequest(prompt="  Create a notes app  ").prompt == "Create a notes app"
    with pytest.raises(ValueError):
        AutoBuildRequest(prompt="Create a notes app\x00")

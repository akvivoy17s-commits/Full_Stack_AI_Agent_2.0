"""Phase 5: planner and Autopilot share one intent classifier; app layout uses a smaller blueprint budget."""
import pytest
from backend.agent import intent, planner

@pytest.mark.parametrize("brief,kind,layout", [
    ("Build todos app", "generic", "app"), ("task management tool", "local", "app"),
    ("investment portfolio tracker", "generic", "app"), ("Kanban board", "generic", "app"),
    ("Create a personal portfolio", "management", "portfolio"), ("my portfolio website", None, "portfolio"),
    ("Design style: Premium SaaS. a dashboard widget", None, "landing"),
    ("Create a company landing page for a coffee shop", None, "landing"),
    ("Analytics dashboard for sales", "dashboard", "dashboard"),
])
def test_layout_for_agrees_with_intent(brief, kind, layout):
    assert planner.layout_for(brief, kind) == layout

def test_autopilot_reuses_shared_regexes():
    from backend.api import autopilot
    assert autopilot._APP_PROMPT is intent.APP_PROMPT and autopilot._MARKETING_PROMPT is intent.MARKETING_PROMPT

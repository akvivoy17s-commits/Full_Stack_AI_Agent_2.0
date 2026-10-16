"""Phase 2: prompt classifier edge cases (regex-only, no heavy deps)."""
import pytest
from backend.api import autopilot as ap

def _is_app(p):
    return bool(ap._APP_PROMPT.search(p)) and not ap._MARKETING_PROMPT.search(p) and not ap._SPECIALIST_PROMPT.search(p)

APPS = ["Build todos app", "investment portfolio tracker", "task management tool", "booking app for salons",
        "appointment scheduler", "invoice generator", "Kanban board", "habit tracker", "library management system"]
NOT_APPS = ["landing page with dashboard preview", "ecommerce admin panel with inventory", "personal website with notes app",
            "my portfolio website", "Portfolio for a photographer", "coffee shop website", "chatbot for support"]

@pytest.mark.parametrize("p", APPS)
def test_app_prompts(p): assert _is_app(p)

@pytest.mark.parametrize("p", NOT_APPS)
def test_non_app_prompts(p): assert not _is_app(p)

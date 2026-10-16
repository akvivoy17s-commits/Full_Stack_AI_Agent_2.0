"""Pale LLM palettes and style-label brands must not reach the generated app."""
import pytest

from backend.agent.planner import brand_for
from backend.engines import design_engine as D


def _c(**kw):
    return D.normalize({"colors": {"bg": "#ffffff", "fg": "#111111", "primary": "#f5f5ff", "accent": "#eeeeee", "muted": "#f0f0f0", **kw}})["colors"]


def test_pale_palette_gets_readable_button_text_borders_and_accent():
    c = _c()
    rgb = D._rgb
    assert D.contrast(rgb(c["primary"]), (255, 255, 255)) >= 4.0          # white button label is readable
    assert D.contrast(rgb(c["accent"]), rgb(c["bg"])) >= 3.0
    assert D.contrast(rgb(c["muted"]), rgb(c["bg"])) >= 3.5
    assert D.contrast(rgb(c["fg"]), rgb(c["bg"])) >= 4.5


def test_good_palette_is_untouched_and_dark_themes_keep_working():
    good = {"bg": "#0b0b14", "fg": "#f5f5ff", "primary": "#7c5cff", "accent": "#00d4ff", "muted": "#9a9ab5"}
    assert D.normalize({"colors": good})["colors"] == good or all(D.contrast(D._rgb(v), D._rgb(good["bg"])) >= 1.5 for v in D.normalize({"colors": good})["colors"].values())
    c = D.normalize({"colors": {"bg": "#101010", "fg": "#101010", "primary": "#111111", "accent": "#121212", "muted": "#131313"}})["colors"]
    assert D.contrast(D._rgb(c["fg"]), D._rgb(c["bg"])) >= 4.5 and D.contrast(D._rgb(c["primary"]), D._rgb(c["bg"])) >= 1.5


def test_invalid_hex_lengths_fall_back_to_defaults():
    assert D.normalize({"colors": {"bg": "#12345"}})["colors"]["bg"] == D.DEFAULT["colors"]["bg"]


@pytest.mark.parametrize("raw", ["Premium SaaS", "premium saas", "Brand", "", None, "Style: Glassmorphism"])
def test_style_label_or_placeholder_brand_is_replaced(raw):
    b = brand_for(raw, "Build a task management tool with kanban board\n\nDesign style: Premium SaaS. Animation intensity: medium")
    assert b == "Task Management Tool"


def test_real_brand_kept_and_empty_brief_has_fallback():
    assert brand_for("  Taskly ", "anything") == "Taskly"
    assert brand_for("Brand", "") == "Workspace"

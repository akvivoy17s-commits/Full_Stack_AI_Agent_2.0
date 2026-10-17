from pathlib import Path

from backend.engines import animation_engine

ROOT = Path(__file__).resolve().parents[1]


def test_3d_detection_is_explicit_and_does_not_enable_for_ordinary_apps():
    assert animation_engine.wants_3d("Build a cinematic 3D portfolio with Three.js")
    assert animation_engine.wants_3d("Create an interactive WebGL product experience")
    assert not animation_engine.wants_3d("Build a clean todo app with a responsive dashboard")
    assert not animation_engine.wants_3d("Create a premium SaaS landing page with smooth animations")


def test_three_runtime_supports_react_mounts_and_performance_safeguards():
    js = (ROOT / "templates/animation/three-hero.js").read_text(encoding="utf-8")
    css = (ROOT / "templates/animation/animations.css").read_text(encoding="utf-8")
    assert "new MutationObserver" in js
    assert "IntersectionObserver" in js
    assert "prefers-reduced-motion" in js
    assert "Math.min(width < 600 ? 260 : 1200" in js
    assert "renderer.dispose()" in js
    assert "data-three-hero" in css
    assert "three-hero-fallback" in css


def test_section_prompt_has_opt_in_3d_rules():
    from backend.agent import prompts
    assert "data-three-hero" in prompts.SECTION
    assert "Do not add script tags" in prompts.SECTION
    assert "data-three-hero" in prompts.HINTS["hero"]


def test_static_install_copies_the_runtime_referenced_by_layout_templates():
    class ProjectFiles:
        def __init__(self):
            self.files = {}

        def write(self, path, content):
            self.files[path] = content

    pf = ProjectFiles()
    animation_engine.install(pf)
    assert "js/three-hero.js" in pf.files
    assert "js/motion.js" in pf.files
    assert "css/animations.css" in pf.files


def test_react_shell_loads_three_runtime_only_when_requested():
    from types import SimpleNamespace
    from backend.engines import react_engine

    normal = SimpleNamespace(brief="Build a todo app", plan={"layout": "landing"}, design={"colors": {"bg": "#111111"}})
    three_d = SimpleNamespace(brief="Build a 3D portfolio", plan={"layout": "portfolio"}, design={"colors": {"bg": "#111111"}})
    assert "/js/three-hero.js" not in react_engine._index_html(normal, "Todo", "")
    assert "/js/three-hero.js" in react_engine._index_html(three_d, "Portfolio", "")

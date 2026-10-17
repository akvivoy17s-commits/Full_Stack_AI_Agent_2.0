"""Regression checks for opt-in 3D generation and shared runtime integration."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_html_scaffold_runtime_is_installed_and_opt_in():
    engine = (ROOT / "backend/engines/animation_engine.py").read_text(encoding="utf-8")
    runtime = (ROOT / "templates/animation/three-hero.js").read_text(encoding="utf-8")
    assert 'pf.write("js/three-hero.js", _template("three-hero.js"))' in engine
    assert "data-three-hero" in runtime
    assert "if (!hosts.length)" not in runtime  # exported initializer is reusable by React after mount
    assert "import(THREE_URL)" in runtime


def test_three_runtime_has_modes_and_quality_safeguards():
    runtime = (ROOT / "templates/animation/three-hero.js").read_text(encoding="utf-8")
    for mode in ('orb', 'product', 'abstract', 'space'):
        assert mode in runtime
    for feature in (
        "prefers-reduced-motion", "ResizeObserver", "IntersectionObserver",
        "webglcontextlost", "renderer.dispose()", "geometry.dispose()",
        "setPixelRatio", "toneMapping", "three-hero-fallback",
    ):
        assert feature in runtime


def test_react_mount_initializes_and_cleans_up_three_runtime():
    motion = (ROOT / "templates/react/src/lib/MotionEffects.tsx").read_text(encoding="utf-8")
    react_engine = (ROOT / "backend/engines/react_engine.py").read_text(encoding="utf-8")
    assert "import('./three-hero.js')" in motion
    assert "runtime.initThreeHero()" in motion
    assert "cleanupThree()" in motion and "cleanupMotion()" in motion
    assert 'pf.write("src/lib/three-hero.js", runtime)' in react_engine


def test_prompt_requires_dedicated_3d_container_and_realistic_honesty():
    prompts = (ROOT / "backend/agent/prompts.py").read_text(encoding="utf-8")
    assert "data-three-hero" in prompts
    assert "data-three-mode" in prompts
    assert "do not claim photorealistic model fidelity" in prompts
    assert "never attach the 3D hook to a heading" in prompts

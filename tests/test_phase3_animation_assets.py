from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def test_motion_assets_include_required_hooks_and_accessibility_fallbacks():
    css = (ROOT / "templates/animation/animations.css").read_text(encoding="utf-8")
    js = (ROOT / "templates/animation/motion.js").read_text(encoding="utf-8")
    for hook in ("data-float", "data-tilt", "data-parallax", "data-mouse-parallax", "data-three-hero", "data-reveal"):
        assert hook in css or hook in js
    assert "prefers-reduced-motion" in css and "prefers-reduced-motion" in js
    assert "IntersectionObserver" in js


def test_static_templates_load_optional_three_scene():
    for name in ("landing_page", "portfolio"):
        html = (ROOT / f"templates/{name}/index.html").read_text(encoding="utf-8")
        assert 'src="js/three-hero.js"' in html
        assert 'data-3d="three-hero"' in html


def test_react_template_has_motion_and_optional_3d_support():
    package = (ROOT / "templates/react/package.json").read_text(encoding="utf-8")
    motion = (ROOT / "templates/react/src/lib/animations.tsx").read_text(encoding="utf-8")
    hero = (ROOT / "templates/react/src/lib/Hero3D.tsx").read_text(encoding="utf-8")
    entry = (ROOT / "templates/react/src/main.tsx").read_text(encoding="utf-8")
    assert '"framer-motion"' in package and '"@react-three/fiber"' in package
    assert "whileInView" in motion and "useReducedMotion" in motion
    assert "<Canvas" in hero and "<MotionEffects />" in entry

"""Local animation engine: pre-built CSS/vanilla-JS motion is copied, the LLM only picks presets and timing.

Public API (used by planner, code_engine, react_engine): normalize(), css_vars(), install().
Everything the LLM returns is whitelisted, so it cannot inject CSS.
"""
import re
from pathlib import Path

from backend.config import TEMPLATES_DIR

NUM = r"-?(?:\d+(?:\.\d*)?|\.\d+)"
EASING = re.compile(
    rf"^(?:ease|ease-in|ease-out|ease-in-out|linear|cubic-bezier\(\s*{NUM}\s*,\s*{NUM}\s*,\s*{NUM}\s*,\s*{NUM}\s*\))$"
)
PRESETS = {
    "hero": ("fade-up", "fade-in", "scale-in", "slide-in", "none"),
    "scroll": ("reveal", "reveal-left", "reveal-scale", "fade-up", "none"),
    "hover": ("lift", "glow", "scale", "underline", "none"),
}
DEFAULT = {"hero": "fade-up", "scroll": "reveal", "hover": "lift", "lib": "css",
           "duration_ms": [250, 700], "easing": "cubic-bezier(.22,1,.36,1)"}
MIN_MS, MAX_MS = 100, 2000
HERO_FROM = {"fade-up": "translate:0 24px", "fade-in": "", "scale-in": "scale:.94", "slide-in": "translate:-32px 0"}
HOVER_CSS = {
    "lift": ".card:hover{transform:translateY(-6px);box-shadow:0 20px 40px -14px color-mix(in srgb,var(--primary) 45%,transparent)}",
    "glow": ".card:hover{box-shadow:0 0 0 1px color-mix(in srgb,var(--primary) 55%,transparent),0 12px 40px -8px color-mix(in srgb,var(--primary) 55%,transparent)}",
    "scale": ".card:hover{transform:scale(1.03)}",
    "underline": "a:not(.btn):not(.brand){background:linear-gradient(currentColor,currentColor) 0 100%/0 1px no-repeat;"
                 "transition:background-size var(--dur-min) var(--ease)}"
                 "a:not(.btn):not(.brand):hover{background-size:100% 1px}",
}


def _preset(value, allowed, fallback) -> str:
    if not isinstance(value, str):
        return fallback
    v = re.sub(r"[\s_]+", "-", value.strip().lower())[:40]
    return v if v in allowed else fallback


def _durations(value) -> list:
    try:
        if not isinstance(value, (list, tuple)) or len(value) != 2 or any(isinstance(x, bool) for x in value):
            raise ValueError
        lo, hi = (max(MIN_MS, min(int(float(x)), MAX_MS)) for x in value)
        return [min(lo, hi), max(lo, hi)]
    except (TypeError, ValueError, OverflowError):
        return list(DEFAULT["duration_ms"])


def _easing(value) -> str:
    e = value.strip().lower() if isinstance(value, str) else ""
    if not EASING.fullmatch(e):
        return DEFAULT["easing"]
    if e.startswith("cubic-bezier"):
        x1, y1, x2, y2 = (float(n) for n in re.findall(NUM, e))
        if not (0 <= x1 <= 1 and 0 <= x2 <= 1 and -1 <= y1 <= 2 and -1 <= y2 <= 2):  # x must stay in [0,1]; mild overshoot ok
            return DEFAULT["easing"]
    return e


def normalize(m) -> dict:
    """Validate LLM motion output; unknown or unsafe values fall back to defaults. lib is always css."""
    m = m if isinstance(m, dict) else {}
    out = {k: _preset(m.get(k), allowed, DEFAULT[k]) for k, allowed in PRESETS.items()}
    out.update(lib="css", duration_ms=_durations(m.get("duration_ms")), easing=_easing(m.get("easing")))
    return out


def css_vars(m) -> str:
    """Timing tokens + the chosen hero/scroll/hover presets, all behind reduced-motion guards."""
    m = normalize(m)
    lo, hi = m["duration_ms"]
    mid = (lo + hi) // 2
    css = (f":root{{--dur-min:{lo}ms;--dur-mid:{mid}ms;--dur-max:{hi}ms;--ease:{m['easing']};}}\n")
    if m["hero"] in HERO_FROM:
        css += "@media (prefers-reduced-motion:no-preference){\n"
        fr = HERO_FROM[m["hero"]]  # individual translate/scale props: no clash with card hover transforms
        css += f"@keyframes agent-hero{{from{{opacity:0;{fr}}}to{{opacity:1;{fr.split(':')[0] + ':none' if fr else ''}}}}}\n"
        for i in range(1, 7):  # stagger first six hero children
            css += f":where(#hero,[data-hero]) .wrap>:nth-child({i}){{animation:agent-hero var(--dur-max) var(--ease) {(i - 1) * 90}ms backwards}}\n"
        css += "}\n"
    if m["scroll"] == "none":
        css += ".reveal,.reveal-left,.reveal-scale,[data-reveal]{opacity:1!important;transform:none!important;transition:none!important}\n"
    if m["hover"] in HOVER_CSS:
        css += f"@media (hover:hover) and (prefers-reduced-motion:no-preference){{{HOVER_CSS[m['hover']]}}}\n"
        if m["hover"] != "underline":
            css += ".card{transition:transform var(--dur-min) var(--ease),box-shadow var(--dur-min) var(--ease)}\n"
    return css


def _template(name: str) -> str:
    p = Path(TEMPLATES_DIR) / "animation" / name
    if not p.is_file():
        raise FileNotFoundError(f"Missing animation template: {name}")
    text = p.read_text(encoding="utf-8")
    if not text.strip():
        raise ValueError(f"Empty animation template: {name}")
    return text



def wants_3d(brief) -> bool:
    """Return True only when the request explicitly asks for a 3D/WebGL experience.

    This deterministic, conservative check keeps ordinary projects lightweight while
    preserving the public API used by code_engine, react_engine, and quality_engine.
    """
    if not isinstance(brief, str):
        return False
    text = re.sub(r"\s+", " ", brief.lower())
    explicit = (
        r"\b3d\b", r"three\.js", r"threejs", r"webgl", r"react three fiber",
        r"three-dimensional", r"3-dimensional", r"interactive 3d", r"3d animation",
        r"3d website", r"3d portfolio", r"3d hero", r"immersive 3d",
    )
    return any(re.search(pattern, text) for pattern in explicit)

def install(pf) -> None:
    """Install reusable motion assets and the opt-in 3D runtime.

    The 3D module is intentionally shipped with HTML projects because their
    scaffold already references it. It performs no network import unless a
    generated section explicitly opts in with a data-three-hero hook.
    """
    pf.write("css/animations.css", _template("animations.css"))
    pf.write("js/motion.js", _template("motion.js"))
    pf.write("js/three-hero.js", _template("three-hero.js"))

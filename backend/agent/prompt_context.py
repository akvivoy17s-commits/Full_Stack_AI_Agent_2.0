"""Prompt compilation helpers used across planning, generation and repair.

The original user brief remains the source of truth. This module makes a bounded,
requirement-oriented excerpt for smaller-context local models so important details
near the end of a long prompt are not silently discarded.
"""
from __future__ import annotations

import re
from typing import Any

MAX_USER_PROMPT = 6000
_IMPORTANT = re.compile(
    r"\b(must|must-have|required|requirements?|include|including|features?|pages?|sections?|"
    r"responsive|mobile|desktop|tablet|style|visual|design|colour|color|palette|font|typography|"
    r"animation|animated|3d|three\.js|dark mode|light mode|accessibility|seo|form|validation|"
    r"search|filter|sort|pagination|dashboard|admin|login|sign[ -]?up|auth(?:entication|orization)?|"
    r"database|mysql|postgres(?:ql)?|sqlite|mongodb|firebase|api|integration|payment|checkout|"
    r"upload|email|notification|security|performance|loading|empty state|error state|"
    r"do not|don't|avoid|never|exactly|preserve|use this|use only|without|not use)\b",
    re.I,
)


def _segments(text: str) -> list[tuple[int, str, int]]:
    """Return ordered prompt fragments with relevance scores."""
    out: list[tuple[int, str, int]] = []
    for line_no, raw_line in enumerate(text.splitlines() or [text]):
        line = re.sub(r"^\s*(?:[-*•]+|\d+[.)])\s*", "", raw_line).strip()
        if not line:
            continue
        # Split long lines into sentences and semicolon-delimited requirements.
        pieces = re.split(r"(?<=[.!?])\s+|\s*[;\n]\s*", line)
        expanded: list[str] = []
        for piece in pieces:
            piece = re.sub(r"\s+", " ", piece).strip(" \t-•")
            if len(piece) > 420:
                # Long instruction lists often use commas; keep chunks in order.
                expanded.extend(x.strip() for x in re.split(r",\s+(?=[A-Z0-9])", piece) if x.strip())
            elif piece:
                expanded.append(piece)
        for piece_no, piece in enumerate(expanded):
            score = 1
            if _IMPORTANT.search(piece):
                score += 5
            if re.search(r"\b(must|must-have|required|do not|don't|never|exactly|preserve|avoid)\b", piece, re.I):
                score += 4
            if len(piece) <= 240:
                score += 1
            if line_no == 0 and piece_no == 0:
                score += 2
            if re.search(r"#[0-9a-f]{3,8}\b|\b(?:React|Next\.js|Vue|Angular|Svelte|FastAPI|Express|Django|Flask|MySQL|PostgreSQL|MongoDB|Firebase)\b", piece, re.I):
                score += 2
            out.append((len(out), piece, score))
    return out


def compact_requirements(prompt: str, max_chars: int = 1900) -> str:
    """Make a bounded excerpt across the *whole* brief, keeping requirements and constraints.

    Short prompts are returned intact. Long prompts are selected by relevance, then restored
    to source order, which helps keep both the user's intent and late-listed requirements.
    """
    raw = str(prompt or "").strip()[:MAX_USER_PROMPT]
    if len(raw) <= max_chars:
        return raw
    fragments = _segments(raw)
    if not fragments:
        return raw[:max_chars]

    # Always consider both ends so a closing constraint is not lost to early prose.
    forced = {fragments[0][0], fragments[-1][0]}
    ranked = sorted(fragments, key=lambda item: (item[0] in forced, item[2], -item[0]), reverse=True)
    selected: dict[int, str] = {}
    used = 0
    for index, piece, _score in ranked:
        candidate = piece if len(piece) <= 360 else piece[:357].rstrip() + "..."
        cost = len(candidate) + (2 if selected else 0)
        if used + cost > max_chars:
            continue
        selected[index] = candidate
        used += cost
    if not selected:
        return raw[:max_chars]
    result = "\n".join(selected[i] for i in sorted(selected))
    return result[:max_chars]


def _short_list(value: Any, limit: int = 8, item_chars: int = 100) -> list[str]:
    if not isinstance(value, list):
        return []
    out = []
    for item in value[:limit]:
        if isinstance(item, str):
            text = re.sub(r"\s+", " ", item).strip()
        elif isinstance(item, dict):
            title = item.get("name") or item.get("title") or item.get("label") or ""
            detail = item.get("description") or item.get("purpose") or ""
            text = f"{title}: {detail}".strip(": ")
        else:
            continue
        if text:
            out.append(text[:item_chars])
    return out


def section_user_context(state: Any, section_id: str, hint: str = "") -> str:
    """Build targeted generation context from the full brief, blueprint, and selected design."""
    plan = state.plan if isinstance(getattr(state, "plan", None), dict) else {}
    design = state.design if isinstance(getattr(state, "design", None), dict) else {}
    colors = design.get("colors") if isinstance(design.get("colors"), dict) else {}
    fonts = design.get("fonts") if isinstance(design.get("fonts"), dict) else {}
    profile = compact_requirements(getattr(state, "brief", ""), 1750)
    lines = [
        "USER REQUEST — requirements selected across the complete original prompt; treat as source of truth:",
        profile,
        f"PROJECT: {str(plan.get('brand') or 'Website')[:60]} | layout={str(plan.get('layout') or getattr(state, 'layout', 'landing'))} | stack={str(plan.get('stack') or getattr(state, 'stack', 'html'))}",
        "SELECTED TECHNOLOGY CONFIG (preserve explicit user choices): " + str(getattr(state, "stack_config", {}) or {})[:650],
        "STRICT FRAGMENT CONTRACT: output only valid HTML fragment + CSS, not React JSX/TSX; no imports, hooks, function calls, PascalCase component tags, .map expressions, or brace-wrapped JS variables. Use standard lowercase HTML/SVG elements and literal content. Do not combine sections or reference components, variables, or data arrays that are not included in this section context.",
    ]
    if section_id.lower().replace("-", "_") == "kpis":
        lines.append("KPI-ONLY SCOPE: render metric cards only. Do not emit HeroBanner, ProductCardList, CategoryList, featuredProducts, categories or JSX component syntax. If metrics are not provided, show an em dash and an honest no-live-data note.")
    features = _short_list(plan.get("features"), 7, 105)
    components = _short_list(plan.get("components"), 8, 70)
    if features:
        lines.append("PLANNED USER FEATURES: " + "; ".join(features))
    if components:
        lines.append("REUSABLE UI COMPONENTS: " + "; ".join(components))
    pages = plan.get("page_blueprint")
    if isinstance(pages, list):
        page_bits = []
        for page in pages[:5]:
            if not isinstance(page, dict):
                continue
            title = str(page.get("name") or page.get("title") or "Page")[:40]
            sections = _short_list(page.get("sections"), 5, 30)
            page_bits.append(title + (" (" + ", ".join(sections) + ")" if sections else ""))
        if page_bits:
            lines.append("PAGE BLUEPRINT: " + "; ".join(page_bits))
    if colors or fonts:
        lines.append("DESIGN TOKENS: " + "; ".join(f"{k}={v}" for k, v in colors.items())
                     + ("; " if colors and fonts else "")
                     + "; ".join(f"font_{k}={v}" for k, v in fonts.items())
                     + (f"; style={design.get('style')}" if design.get("style") else ""))
    motion = getattr(state, "motion", None)
    if isinstance(motion, dict) and motion:
        motion_bits = [f"{k}={v}" for k, v in motion.items() if k in ("hero", "scroll", "hover", "loading", "lib") and v]
        if motion_bits:
            lines.append("MOTION: " + "; ".join(motion_bits))
    lines.extend([
        f"CURRENT SECTION: {section_id}",
        f"SECTION PURPOSE: {hint or 'Implement the requested section with project-consistent detail.'}",
        "IMPLEMENTATION RULES: reflect the user's product and audience, not a generic template; preserve named content, colors, pages and features; use realistic copy relevant to the domain; every visible action must work or clearly link to a real destination; no lorem ipsum, dead buttons or invented real-world claims; accessible semantic markup, keyboard focus and responsive mobile layout; CSS must be scoped to this section and consistent with the design tokens.",
        "ALREADY GENERATED: " + ", ".join(getattr(state, "sections_done", []) or []),
    ])
    return "\n".join(lines)[:3300]

"""Deterministic checks for common generated-site defects that builds alone cannot catch.

These checks are intentionally conservative: they flag missing local assets, obvious sample filler,
and forms that have no submission path. They do not claim that static analysis proves visual correctness.
"""
from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import urlsplit


ATTR_REF = re.compile(
    r"""<(?:script|img|source|video|audio|iframe|input)\b[^>]*?\b(?:src|poster)\s*=\s*(['"])(.*?)\1""",
    re.IGNORECASE | re.DOTALL,
)
LINK_REF = re.compile(
    r"""<link\b[^>]*?\bhref\s*=\s*(['"])(.*?)\1""", re.IGNORECASE | re.DOTALL
)
CSS_URL = re.compile(r"""url\(\s*(['"]?)(.*?)\1\s*\)""", re.IGNORECASE)
CSS_BAD_VAR_MATH = re.compile(r"var\(\s*--[\w-]+\s*\)\s*\*\s*(?:\d+(?:\.\d+)?|\.\d+)", re.I)
INLINE_STYLE = re.compile(r"""\bstyle\s*=\s*(['"])(.*?)\1""", re.I | re.S)
ANCHOR = re.compile(r"<a\b([^>]*)>(.*?)</a\s*>", re.I | re.S)
TARGET_BLANK = re.compile(r"""\btarget\s*=\s*(['"])_blank\1""", re.I)
REL = re.compile(r"""\brel\s*=\s*(['"])(.*?)\1""", re.I | re.S)
MOUNT_ATTR = re.compile(r"""\bdata-three-hero\b|\bdata-3d\s*=\s*(['"])three-hero\1""", re.I)
BAD_MOUNT_TAG = re.compile(r"""<(h[1-6]|p|span|a|button|strong|em|label)\b[^>]*?(?:data-three-hero|data-3d\s*=\s*(['"])three-hero\2)""", re.I | re.S)
INTERNAL_HREF = re.compile(r"""\bhref\s*=\s*(['"])#([A-Za-z][\w:.-]*)\1""", re.I)
PLACEHOLDER_ENDPOINT = re.compile(r"(?:formspree\.io/(?:your-email|your-email-address|your-form-id|your-email-here|replace-me)|(?:example\.com|your-email|your-form-id|replace-me))", re.I)
FORM = re.compile(r"<form\b([^>]*)>(.*?)</form\s*>", re.IGNORECASE | re.DOTALL)
ACTION = re.compile(r"""\baction\s*=\s*(['"])(.*?)\1""", re.IGNORECASE | re.DOTALL)
PLACEHOLDERS = (
    (re.compile(r"\bproject\s*[1-9]\b", re.I), "generic project placeholder"),
    (re.compile(r"\bdeveloper portfolio\b", re.I), "generic portfolio headline left unchanged"),
    (re.compile(r"\btech\s*[1-9]\b", re.I), "generic technology placeholder"),
    (re.compile(r"\boutcome of project\s*[1-9]\b", re.I), "generic project outcome placeholder"),
    (re.compile(r"\b(?:path/to/|your-email|your-form-id|yourname|your-name)\b", re.I), "unresolved asset or contact placeholder"),
    (re.compile(r"\bfeature\s*[1-9]\b", re.I), "generic feature placeholder"),
    (re.compile(r"\blorem ipsum\b", re.I), "lorem ipsum placeholder text"),
    (re.compile(r"\bexample@example\.com\b", re.I), "example email left in generated content"),
    (re.compile(r"\+123[\s-]*456[\s-]*7890\b", re.I), "sample phone number left in generated content"),
    (re.compile(r"linkedin\.com/in/developer\b", re.I), "sample social profile left in generated content"),
    (re.compile(r"\b(?:john doe|jane doe|your name|your company)\b", re.I), "generic identity placeholder"),
)


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except (OSError, ValueError):
        return ""


def _safe_local(value: str) -> str | None:
    value = value.strip()
    if not value or value.startswith(("#", "data:", "blob:", "mailto:", "tel:", "javascript:")):
        return None
    parsed = urlsplit(value)
    if parsed.scheme or parsed.netloc:
        return None
    path = parsed.path
    if not path:
        return None
    return path


def _sid_at(source: Path, pos: int, index_html: str, state) -> str | None:
    """Map a character position in generated HTML back to its section marker."""
    if source.name != "index.html":
        return None
    start = index_html.rfind("<!--SECTION:", 0, pos + 1)
    if start < 0:
        return None
    end = index_html.find("-->", start)
    if end < 0:
        return None
    marker = index_html[start:end + 3]
    match = re.search(r"<!--\s*SECTION:([a-zA-Z0-9_-]+)\s*-->", marker, re.I)
    if not match:
        return None
    sid = match.group(1)
    close = index_html.find(f"<!--/SECTION:{sid}-->", end + 3)
    if close >= 0 and pos < close:
        return sid
    return None


def _section_for_source(source: Path, index_html: str, state, pos: int | None = None) -> str | None:
    if source.name in ("index.html", "index.htm") and pos is not None:
        return _sid_at(source, pos, index_html, state)
    normalized = source.as_posix()
    for planned in state.plan.get("sections", []):
        component = "".join(part.capitalize() for part in re.split(r"[^a-z0-9]+", planned.lower()) if part)
        if normalized.endswith(f"/src/sections/{component}.tsx") or normalized.endswith(f"/src/sections/{component}.jsx"):
            return planned
    return None


def _section_from_css(text: str, state, pos: int | None = None) -> str | None:
    # Resolve the CSS rule containing the defect, not simply the first section in the file.
    prefix = text[:pos] if pos is not None else text
    rule_start = max(prefix.rfind("}"), prefix.rfind("{"))
    selector_start = prefix.rfind("}", 0, rule_start) + 1
    selector_chunk = prefix[selector_start:rule_start if rule_start >= 0 else len(prefix)]
    candidates = re.findall(r"#([a-z][\w-]*)", selector_chunk, re.I)
    planned = state.plan.get("sections", [])
    for sid in reversed(candidates):
        if sid in planned:
            return sid
    for match in re.finditer(r"#([a-z][\w-]*)", prefix, re.I):
        sid = match.group(1)
        if sid in planned:
            return sid
    return None


def _inside_calc(text: str, pos: int) -> bool:
    # A variable multiplication is valid only if an enclosing calc( has not closed before it.
    calc_pos = text.lower().rfind("calc(", 0, pos)
    close_pos = text.rfind(")", 0, pos)
    return calc_pos > close_pos


def inspect(pf, state) -> list[dict]:
    """Return deduplicated {sid, msg} issues for common missing-asset and fake-UI defects."""
    issues: list[dict] = []
    seen: set[tuple[str | None, str]] = set()

    def add(sid, msg):
        key = (sid, msg)
        if key not in seen:
            seen.add(key)
            issues.append({"sid": sid, "msg": msg})

    root: Path = pf.root
    index_html = _read(root / "index.html")
    files = [root / name for name in pf.tree() if isinstance(name, str)]
    html_files = [p for p in files if p.suffix.lower() in (".html", ".htm")]
    css_files = [p for p in files if p.suffix.lower() == ".css"]
    code_files = [p for p in files if p.suffix.lower() in (".js", ".mjs", ".cjs", ".jsx", ".ts", ".tsx")]

    # Local asset references must point to files that actually exist in the generated project.
    for source in html_files:
        text = _read(source)
        refs = [(m.group(2), m.start()) for m in ATTR_REF.finditer(text)]
        refs += [(m.group(2), m.start()) for m in LINK_REF.finditer(text)]
        for raw, pos in refs:
            local = _safe_local(raw)
            if local is None:
                continue
            target = ((root / local.lstrip("/")) if local.startswith("/") else (source.parent / local)).resolve()
            try:
                target.relative_to(root.resolve())
            except ValueError:
                add(_sid_for_text(text[max(0, pos - 500):pos + 500], index_html, state),
                    f"unsafe local asset path referenced in {source.relative_to(root)}")
                continue
            if not target.is_file() and local.startswith("/") and (root / "public" / local.lstrip("/")).is_file():
                target = root / "public" / local.lstrip("/")
            if not target.is_file():
                snippet = text[max(0, pos - 400):pos + 500]
                sid = _sid_at(source, pos, index_html, state)
                if sid is None and "three-hero.js" in local:
                    sid = "hero" if "hero" in state.plan.get("sections", []) else None
                add(sid, f"missing local asset referenced by {source.relative_to(root)}: {local}")

        # CSS URLs inside inline style attributes are not covered by the stylesheet scan above.
        for style_match in INLINE_STYLE.finditer(text):
            for url_match in CSS_URL.finditer(style_match.group(2)):
                raw = url_match.group(2).strip()
                local = _safe_local(raw)
                if local is None:
                    continue
                target = ((root / local.lstrip("/")) if local.startswith("/") else (source.parent / local)).resolve()
                try:
                    target.relative_to(root.resolve())
                except ValueError:
                    add(_sid_at(source, style_match.start(), index_html, state),
                        f"unsafe inline CSS asset path in {source.relative_to(root)}")
                    continue
                if not target.is_file() and local.startswith("/") and (root / "public" / local.lstrip("/")).is_file():
                    target = root / "public" / local.lstrip("/")
                if not target.is_file():
                    add(_sid_at(source, style_match.start(), index_html, state),
                        f"missing local CSS asset referenced by {source.relative_to(root)}: {local}")

    for source in css_files:
        text = _read(source)
        for m in CSS_URL.finditer(text):
            local = _safe_local(m.group(2))
            if local is None:
                continue
            target = ((root / local.lstrip("/")) if local.startswith("/") else (source.parent / local)).resolve()
            try:
                target.relative_to(root.resolve())
            except ValueError:
                add(None, f"unsafe local CSS asset path in {source.relative_to(root)}")
                continue
            if not target.is_file():
                add(None, f"missing local CSS asset referenced by {source.relative_to(root)}: {local}")

        # Bare CSS variable multiplication is invalid; report it per affected section so each can be repaired.
        for bad_math in CSS_BAD_VAR_MATH.finditer(text):
            if _inside_calc(text, bad_math.start()):
                continue
            sid = _section_from_css(text, state, bad_math.start())
            add(sid, f"invalid CSS arithmetic in {source.relative_to(root)} for section {sid or 'unknown'}: wrap variable multiplication in calc()")

    # CSS embedded in <style> tags needs the same arithmetic validation.
    for source in html_files:
        text = _read(source)
        for style_block in re.finditer(r"<style\b[^>]*>(.*?)</style\s*>", text, re.I | re.S):
            css_text = style_block.group(1)
            for bad_math in CSS_BAD_VAR_MATH.finditer(css_text):
                if _inside_calc(css_text, bad_math.start()):
                    continue
                add(_sid_at(source, style_block.start(), index_html, state),
                    "invalid CSS arithmetic in inline stylesheet: wrap variable multiplication in calc()")

    # Generic demo data is not acceptable as finished content unless the user explicitly asked for it.
    brief = str(getattr(state, "brief", "") or "")
    allow_sample = bool(re.search(r"\b(sample|placeholder|demo data|example content)\b", brief, re.I))
    if not allow_sample:
        content_files = html_files + [p for p in files if p.suffix.lower() in (".tsx", ".jsx", ".vue", ".svelte")]
        for source in content_files:
            text = _read(source)
            for pattern, message in PLACEHOLDERS:
                for match in pattern.finditer(text):
                    sid = _sid_at(source, match.start(), index_html, state)
                    if sid is None:
                        # Map generated React section source paths back to their planned section ID.
                        for planned in state.plan.get("sections", []):
                            component = "".join(part.capitalize() for part in re.split(r"[^a-z0-9]+", planned.lower()) if part)
                            if source.as_posix().endswith(f"/src/sections/{component}.tsx"):
                                sid = planned
                                break
                    add(sid, message)

    # A form with no endpoint and no submit handler is a dead control, not a working contact form.
    all_code = "\n".join(_read(p) for p in code_files)
    has_submit_handler = bool(re.search(
        r"""(?:addEventListener\s*\(\s*['"]submit|onSubmit\s*=|onsubmit\s*=|handleSubmit|submitForm)""",
        all_code, re.I
    ))
    for source in html_files:
        text = _read(source)
        for m in FORM.finditer(text):
            attrs = m.group(1)
            action_match = ACTION.search(attrs)
            action = action_match.group(2).strip() if action_match else ""
            sid = _sid_at(source, m.start(), index_html, state)
            if action and PLACEHOLDER_ENDPOINT.search(action):
                add(sid, "form action contains a placeholder endpoint; configure a real endpoint or remove the fake submission UI")
                continue
            if action and action != "#":
                continue
            if has_submit_handler or re.search(r"\bdata-form-handler\b", attrs, re.I):
                continue
            add(sid, "form has no real submission endpoint or submit handler")

    # External tabs must not expose the opener to the destination page.
    for source in html_files:
        text = _read(source)
        for m in ANCHOR.finditer(text):
            attrs = m.group(1)
            if not TARGET_BLANK.search(attrs):
                continue
            rel_match = REL.search(attrs)
            rel_tokens = set((rel_match.group(2).lower().split() if rel_match else []))
            if not ({"noopener", "noreferrer"} & rel_tokens):
                add(_sid_at(source, m.start(), index_html, state),
                    "external link opens a new tab without rel=noopener or rel=noreferrer")

    # Local fragment links should resolve to an actual element ID.
    for source in html_files:
        text = _read(source)
        ids = set(re.findall(r"\bid\s*=\s*([\'\"])(.*?)\1", text, re.I))
        id_values = {value for _, value in ids}
        for m in INTERNAL_HREF.finditer(text):
            if m.group(2) not in id_values:
                add(_sid_at(source, m.start(), index_html, state),
                    f"internal link points to missing section or element id: #{m.group(2)}")

    # A requested 3D hero must have a real runtime/component and mount point, not just decorative copy.
    from backend.engines import animation_engine
    if animation_engine.wants_3d(brief):
        if state.plan.get("stack") == "react":
            hero_name = "".join(part.capitalize() for part in re.split(r"[^a-z0-9]+", "hero") if part)
            hero_source = root / "src" / "sections" / f"{hero_name}.tsx"
            runtime = root / "public" / "js" / "three-hero.js"
            if not runtime.is_file():
                add("hero" if "hero" in state.plan.get("sections", []) else None,
                    "3D was requested but public/js/three-hero.js runtime is missing")
            hero_text = _read(hero_source)
            if BAD_MOUNT_TAG.search(hero_text):
                add("hero" if "hero" in state.plan.get("sections", []) else None,
                    "3D mount point is attached to a heading/inline element; move it to a sized hero wrapper and keep text/CTAs outside the canvas")
            if not re.search(r"""\bdata-three-hero\b|data-3d\s*=\s*['"]three-hero['"]""", hero_text, re.I):
                add("hero" if "hero" in state.plan.get("sections", []) else None,
                    "3D was requested but the React hero has no Three.js mount point")
        else:
            runtime = root / "js" / "three-hero.js"
            if not runtime.is_file():
                add("hero" if "hero" in state.plan.get("sections", []) else None,
                    "3D was requested but js/three-hero.js runtime is missing")
            live_markup = re.sub(r"<!--.*?-->", "", index_html, flags=re.S)
            bad_mount = BAD_MOUNT_TAG.search(live_markup)
            if bad_mount:
                add("hero" if "hero" in state.plan.get("sections", []) else None,
                    "3D mount point is attached to a heading/inline element; move it to a sized hero wrapper and keep text/CTAs outside the canvas")
            if not re.search(r"""\bdata-three-hero\b|data-3d\s*=\s*['"]three-hero['"]""", live_markup, re.I):
                add("hero" if "hero" in state.plan.get("sections", []) else None,
                    "3D was requested but the hero has no Three.js mount point")

    return issues

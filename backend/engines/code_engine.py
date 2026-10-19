"""Template scaffold (local) + one LLM call per section (resumable). Output = section html/css only."""
import re
from html import escape
from backend import config
from backend.config import TEMPLATES_DIR
from backend.agent import prompts, llm, schemas, context, prompt_context
from backend.engines import design_engine, animation_engine
from backend.memory import project_store

SCRIPT = re.compile(r"<script\b.*?</script\s*>", re.I | re.S)
HANDLER = re.compile(r"""\son\w+\s*=\s*("[^"]*"|'[^']*')""", re.I)
RM = "@media (prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}\n"


def clean_html(h: str) -> str:
    return HANDLER.sub("", SCRIPT.sub("", h))


def clean_css(c: str) -> str:
    return re.sub(r"@import[^;]*;", "", c, flags=re.I).replace("javascript:", "")


def _tpl(rel: str) -> str:
    return (TEMPLATES_DIR / rel).read_text(encoding="utf-8")


def _label(sid: str) -> str:
    return sid.replace("-", " ").title()


LAYOUT_DIR = {"landing": "landing_page", "dashboard": "dashboard", "portfolio": "portfolio", "authentication": "authentication"}


def base_css(layout: str) -> str:
    """Shared utility classes + optional layout-specific CSS (templates/<layout>/layout.css)."""
    css = _tpl("landing_page/base.css")
    extra = TEMPLATES_DIR / LAYOUT_DIR.get(layout, "landing_page") / "layout.css"
    return css + ("\n" + extra.read_text(encoding="utf-8") if extra.is_file() else "")


def nav_footer(layout: str, brand: str, secs: list[str]) -> tuple[str, str]:
    brand = escape(brand or "Brand")
    if layout == "authentication":
        return "", ""
    if layout == "dashboard":
        links = "".join(f'<li><a href="#{s}">{escape(_label(s))}</a></li>' for s in secs)
        return (f'<aside class="side" aria-label="Sidebar"><a class="brand" href="#{secs[0]}">{brand}</a><nav><ul>{links}</ul></nav></aside>', "")
    skip = ("hero", "cta") if layout == "landing" else ("hero",)
    links = "".join(f'<li><a href="#{s}">{escape(_label(s))}</a></li>' for s in secs if s not in skip)
    last = secs[-1] if layout == "portfolio" else "cta"
    label = "Contact" if layout == "portfolio" else "Get started"
    cta = f'<a class="btn btn-primary" href="#{last}">{label}</a>' if last in secs else ""
    nav = (f'<header class="nav"><div class="wrap"><a class="brand" href="#{secs[0]}">{brand}</a>'
           f'<nav><ul>{links}</ul></nav>{cta}</div></header>')
    return nav, f'<footer><div class="wrap">&copy; {brand}. All rights reserved.</div></footer>'


def scaffold(pf, state) -> None:
    layout = state.plan.get("layout", "landing")
    if state.plan.get("stack") == "react":
        from backend.engines import react_engine
        return react_engine.scaffold(pf, state)
    pf.write("css/tokens.css", design_engine.render_tokens(state.design) + animation_engine.css_vars(state.motion))
    pf.write("css/base.css", base_css(layout))
    animation_engine.install(pf)
    secs = state.plan["sections"]
    nav, footer = nav_footer(layout, state.plan.get("brand") or "Brand", secs)
    markers = "\n".join(f"<!--SECTION:{s}--><!--/SECTION:{s}-->" for s in secs)
    html = (_tpl(f"{LAYOUT_DIR.get(layout, 'landing_page')}/index.html").replace("{{TITLE}}", escape(state.plan.get("brand") or "Brand"))
            .replace("{{FONTS}}", design_engine.fonts_link(state.design))
            .replace("{{NAV}}", nav).replace("{{SECTIONS}}", markers).replace("{{FOOTER}}", footer))
    pf.write("index.html", html)
    pf.write("css/sections.css", RM)


_ID_RE = re.compile(r"""(\sid\s*=\s*)(?:"([^"]*)"|'([^']*)'|([^\s>]+))""", re.I)


def _id_value(match) -> str:
    return next((v for v in match.groups()[1:] if v is not None), "").strip()


def _has_id(html: str, value: str) -> bool:
    return any(_id_value(m) == value for m in _ID_RE.finditer(html))


def dedupe_ids(html: str, reserved_ids: set[str] | None = None, current_sid: str | None = None,
               seen_global: set[str] | None = None) -> str:
    """Strip duplicate/foreign section IDs deterministically, including unquoted HTML attributes.

    Section anchor IDs are reserved globally. A section keeps its own root ID once; nested copies and IDs
    that collide with another planned section are removed before browser-based accessibility checks run.
    """
    reserved = reserved_ids or set()
    seen = seen_global if seen_global is not None else set()
    local: set[str] = set()

    def fix(m):
        value = _id_value(m)
        if not value:
            return m.group(0)
        if value in reserved and value != current_sid:
            return ""
        if value == current_sid:
            if value in local:
                return ""
            local.add(value)
            seen.add(value)
            return m.group(0)
        if value in local or value in seen:
            return ""
        local.add(value)
        seen.add(value)
        return m.group(0)

    return _ID_RE.sub(fix, html)


def normalize_existing_ids(pf, state) -> int:
    """Zero-token, idempotent accessibility repair for duplicate IDs across generated sections.

    This runs before expensive browser/LLM repairs. It only changes duplicate/foreign id attributes in
    the generated section source; it does not change business logic or disable any check.
    """
    sections = list(state.plan.get("sections", []))
    if not sections:
        return 0
    originals = {sid: get_section(pf, sid, state) for sid in sections if sid in state.sections_done}
    reserved = set(sections)
    seen_global: set[str] = set()
    cleaned: dict[str, tuple[str, str]] = {}
    changed = 0
    for sid in sections:
        if sid not in originals:
            continue
        html, css = originals[sid]
        new_html = dedupe_ids(html, reserved, sid, seen_global)
        # Keep each section's root anchor registered for all following sections.
        seen_global.add(sid)
        cleaned[sid] = (new_html, css)
        if new_html != html:
            changed += 1
    # Write after reading every source, since writing an HTML section changes the shared index document.
    for sid, (html, css) in cleaned.items():
        old_html = originals[sid][0]
        if html != old_html:
            _insert(pf, state, sid, html, css)
    return changed


def _insert(pf, state, sid: str, html: str, css: str) -> None:
    html = clean_html(html)
    html = dedupe_ids(html, set(state.plan.get("sections", [])), sid)
    if state.plan.get("stack") == "react":
        from backend.engines import react_engine
        return react_engine.insert(pf, state, sid, html, css)
    if not _has_id(html, sid):
        html = f'<div id="{sid}">{html}</div>'
    pat = re.compile(rf"(<!--SECTION:{re.escape(sid)}-->).*?(<!--/SECTION:{re.escape(sid)}-->)", re.S)
    t = pf.read("index.html")
    if not pat.search(t):
        raise ValueError("section marker missing in index.html")
    pf.write("index.html", dedupe_ids(pat.sub(lambda m: m.group(1) + "\n" + html + "\n" + m.group(2), t)))
    pf.write(f".agent/parts/{sid}.css", clean_css(css))
    parts = []
    for s in state.plan["sections"]:
        try:
            parts.append(pf.read(f".agent/parts/{s}.css"))
        except FileNotFoundError:
            pass
    pf.write("css/sections.css", "\n".join(parts) + "\n" + RM)


def generate_sections(pf, state, force: bool = False) -> dict:
    total = {"in": 0, "out": 0}
    secs = state.plan["sections"]
    for n, sid in enumerate(secs, 1):
        context.check()
        if sid in state.sections_done and not force:
            continue                                   # resume: never regenerate finished sections
        context.progress("code", f"Generating section '{sid}' ({n}/{len(secs)})")
        try:
            user = prompt_context.section_user_context(
                state, sid, prompts.HINTS.get(sid, "rich, detailed section"))
            data, u = llm.call_json("section", prompts.SECTION, user, None, config.SECTION_MAX_TOKENS, schema=schemas.SectionOut)
            total["in"] += u["in"]
            total["out"] += u["out"]
            _insert(pf, state, sid, data["html"], data.get("css", ""))
            if sid not in state.sections_done:
                state.sections_done.append(sid)
        except llm.OllamaError as e:
            if e.code in ("offline", "model_missing"):  # no point trying the remaining sections
                project_store.save(state)
                raise
            state.errors.append(f"{sid}: {e}")
            context.progress("code", f"Section '{sid}' failed: {e}", "error")
        except Exception as e:  # noqa: BLE001
            state.errors.append(f"{sid}: {e}")
            context.progress("code", f"Section '{sid}' failed: {e}", "error")
        project_store.save(state)                      # progress is saved after every section
    return total


def get_section(pf, sid: str, state=None):
    """Return (html, css) of one section, so repairs only ever see a small window."""
    if state is not None and state.plan.get("stack") == "react":
        from backend.engines import react_engine
        return react_engine.get_section(pf, sid)
    t = pf.read("index.html")
    m = re.search(rf"<!--SECTION:{re.escape(sid)}-->(.*?)<!--/SECTION:{re.escape(sid)}-->", t, re.S)
    html = m.group(1).strip() if m else ""
    try:
        css = pf.read(f".agent/parts/{sid}.css")
    except FileNotFoundError:
        css = ""
    return html, css


insert = _insert

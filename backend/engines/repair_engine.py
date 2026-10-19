"""Token-cheap repair: one cheap patch call per broken section (only that section is sent).
If patches don't apply cleanly, fall back to regenerating that single section."""
from backend import config
from backend.agent import prompts, llm, schemas
from backend.engines import code_engine
from backend.tools import language_analyzer, debugger

MAX_SECTIONS_PER_LOOP = 3
ZERO = {"in": 0, "out": 0}


def _apply(text: str, patches: list, kind: str):
    for p in patches:
        if p.get("t") != kind:
            continue
        old = p.get("old")
        if not isinstance(old, str) or not old or text.count(old) != 1:
            return None
        text = text.replace(old, str(p.get("new", "")))
    return text



def _section_source_errors(html: str, css: str) -> list[str]:
    """Reject malformed canonical section sources before writing any generated output.

    The language analyzer's HTML balance rules support common optional end tags and its CSS
    scanner ignores strings/comments. These checks are intentionally conservative: a failed
    preflight leaves the previously working canonical source untouched.
    """
    errors: list[str] = []
    _lang, html_issues = language_analyzer._simple_syntax("section.html", html)
    _lang, css_issues = language_analyzer._simple_syntax("section.css", css)
    errors.extend(str(i.get("message", "HTML syntax issue")) for i in html_issues if i.get("severity") == "error")
    errors.extend(str(i.get("message", "CSS syntax issue")) for i in css_issues if i.get("severity") == "error")
    return errors[:12]

def _patch(pf, state, sid: str, notes: str, model: str):
    html, css = code_engine.get_section(pf, sid, state)
    if not html:
        return False, dict(ZERO)
    root_hint = debugger.root_cause_summary([{"file": f".agent/parts/{sid}.html", "msg": notes}])
    user = (
        f"SECTION: {sid}\nTASK/DIAGNOSTICS:\n{notes}\n"
        f"DETERMINISTIC HINTS:\n{root_hint.get('root_cause_hints', [])}\n"
        "CONTRACT: HTML must be valid HTML, not JSX/TSX. Do not emit component names, imports, hooks, "
        "brace-based variables, `.map()` expressions, or event handlers. Do not invent unavailable data.\n"
        f"HTML:\n{html}\nCSS:\n{css}"
    )
    data, u = llm.call_json("repair", prompts.REPAIR_PATCH, user, model, 1200)
    patches = data.get("patches") or []
    if not isinstance(patches, list) or not patches:
        return False, u
    if any(not isinstance(p, dict) or p.get("t") not in {"html", "css"} for p in patches):
        return False, u
    new_html, new_css = _apply(html, patches, "html"), _apply(css, patches, "css")
    if new_html is None or new_css is None:
        return False, u
    if new_html == html and new_css == css:
        # A syntactically valid but unchanged response must not trigger full-section
        # regeneration. The verification loop sees unchanged canonical fingerprints and
        # records one no-progress attempt, preventing repeated LLM calls for the same error.
        from backend.agent import context
        context.progress("repair", f"Rejected no-op patch for '{sid}'; preserving source and stopping retry churn", "warn")
        return True, u
    errors = _section_source_errors(new_html, new_css)
    if errors:
        context.progress("repair", f"Rejected malformed patch for '{sid}': {'; '.join(errors[:3])}", "warn")
        return False, u
    # HTML is the editable contract; any JSX-only component/interpolation is normalized by
    # react_engine.insert before derived TSX is written. The next build decides acceptance.
    code_engine.insert(pf, state, sid, new_html, new_css)
    return True, u


def _regen(pf, state, sid: str, notes: str) -> dict:
    user = (f"{state.compact(900)}\nSECTION: {sid}\nHINT: {prompts.HINTS.get(sid, 'rich, detailed section')}\nFIX:\n{notes}")
    data, u = llm.call_json("section", prompts.SECTION, user, None, config.SECTION_MAX_TOKENS, schema=schemas.SectionOut)
    html, css = data["html"], data.get("css", "")
    errors = _section_source_errors(html, css)
    if errors:
        # Never overwrite canonical source with an output that already fails deterministic
        # markup/delimiter checks. The caller records this as an unsuccessful repair.
        raise ValueError("regenerated section failed source preflight: " + "; ".join(errors[:4]))
    code_engine.insert(pf, state, sid, html, css)
    if sid not in state.sections_done:
        state.sections_done.append(sid)
    return u


def _run(pf, state, sid: str, notes: str, model: str, regen: bool = False):
    """Returns (usage, method). A rejected patch falls back to regenerating only that section."""
    total = dict(ZERO)
    if not regen:
        ok, u = _patch(pf, state, sid, notes, model)
        total["in"] += u["in"]; total["out"] += u["out"]
        if ok:
            return total, "patch"
    u = _regen(pf, state, sid, notes)
    total["in"] += u["in"]; total["out"] += u["out"]
    return total, "regen"


def fix(pf, state, issues: list[dict], regen_sids: set | None = None) -> dict:
    """Repairs at most MAX_SECTIONS_PER_LOOP sections. Returns usage plus 'log': [{sid, method, msgs}] of what was attempted."""
    by: dict[str, list[str]] = {}
    for i in issues:
        if i.get("sid"):
            by.setdefault(i["sid"], []).append(i["msg"])
    total = dict(ZERO)
    total["log"] = []
    for sid, msgs in list(by.items())[:MAX_SECTIONS_PER_LOOP]:
        try:
            u, method = _run(pf, state, sid, "\n".join(f"- {m}" for m in msgs[:4]), None, sid in (regen_sids or ()))
            total["in"] += u["in"]; total["out"] += u["out"]
            total["log"].append({"sid": sid, "method": method, "msgs": msgs})
        except Exception:  # noqa: BLE001  (issue stays in the final report)
            total["log"].append({"sid": sid, "method": "error", "msgs": msgs})
    return total


def edit(pf, state, sid: str, instruction: str) -> dict:
    if sid not in state.plan.get("sections", []):
        raise ValueError("unknown section")
    return _run(pf, state, sid, f"- EDIT REQUEST: {instruction[:500]}", None)[0]

"""Token-cheap repair: one cheap patch call per broken section (only that section is sent).
If patches don't apply cleanly, fall back to regenerating that single section."""
from backend import config
from backend.agent import prompts, llm, schemas
from backend.engines import code_engine

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


def _patch(pf, state, sid: str, notes: str, model: str):
    html, css = code_engine.get_section(pf, sid, state)
    if not html:
        return False, dict(ZERO)
    data, u = llm.call_json("repair", prompts.REPAIR_PATCH,
                            f"SECTION: {sid}\nTASK:\n{notes}\nHTML:\n{html}\nCSS:\n{css}", model, 1200)
    patches = data.get("patches") or []
    new_html, new_css = _apply(html, patches, "html"), _apply(css, patches, "css")
    if not patches or new_html is None or new_css is None:
        return False, u
    code_engine.insert(pf, state, sid, new_html, new_css)
    return True, u


def _regen(pf, state, sid: str, notes: str) -> dict:
    user = (f"{state.compact(900)}\nSECTION: {sid}\nHINT: {prompts.HINTS.get(sid, 'rich, detailed section')}\nFIX:\n{notes}")
    data, u = llm.call_json("section", prompts.SECTION, user, None, config.SECTION_MAX_TOKENS, schema=schemas.SectionOut)
    code_engine.insert(pf, state, sid, data["html"], data.get("css", ""))
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

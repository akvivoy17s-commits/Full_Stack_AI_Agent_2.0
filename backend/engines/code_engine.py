"""Template scaffold (local) + one LLM call per section (resumable). Output = section html/css only."""
import re
from datetime import datetime
from html import escape
from backend import config
from backend.config import TEMPLATES_DIR
from backend.agent import prompts, llm, schemas, context
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


LAYOUT_DIR = {"landing": "landing_page", "dashboard": "dashboard", "portfolio": "portfolio"}


NAV_JS = """(() => {
  'use strict';
  const nav = document.querySelector('.nav');
  const menu = nav && nav.querySelector('nav');
  const wrap = nav && nav.querySelector('.wrap');
  if (!nav || !menu || !wrap) return;
  if (!menu.id) menu.id = 'site-nav';

  // Progressive enhancement: without JS the nav stays a scrollable row (see base.css).
  const btn = document.createElement('button');
  btn.type = 'button';
  btn.className = 'nav-toggle';
  btn.setAttribute('aria-expanded', 'false');
  btn.setAttribute('aria-controls', menu.id);
  btn.setAttribute('aria-label', 'Open menu');
  btn.innerHTML = '<span aria-hidden="true"></span>';
  wrap.appendChild(btn);

  const mq = window.matchMedia('(max-width: 800px)');
  const set = (open, refocus) => {
    nav.classList.toggle('open', open);
    btn.setAttribute('aria-expanded', String(open));
    btn.setAttribute('aria-label', open ? 'Close menu' : 'Open menu');
    if (!open && refocus) btn.focus();
  };
  btn.addEventListener('click', () => set(!nav.classList.contains('open')));
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && nav.classList.contains('open')) set(false, true);
  });
  menu.addEventListener('click', (e) => { if (e.target.closest('a')) set(false); });
  document.addEventListener('click', (e) => {
    if (nav.classList.contains('open') && !nav.contains(e.target)) set(false);
  });
  const onChange = () => { if (!mq.matches) set(false); };
  if (mq.addEventListener) mq.addEventListener('change', onChange);

  // Scroll-spy: mark the link of the section in view with aria-current.
  const links = [...nav.querySelectorAll('a[href^="#"]:not(.brand):not(.btn)')];
  const targets = new Map();
  links.forEach((a) => {
    const el = document.getElementById(a.getAttribute('href').slice(1));
    if (!el || !el.closest('main')) return;
    if (!targets.has(el)) targets.set(el, []);
    targets.get(el).push(a);
  });
  if ('IntersectionObserver' in window && targets.size) {
    const io = new IntersectionObserver((entries) => entries.forEach((en) => {
      if (!en.isIntersecting) return;
      links.forEach((a) => a.removeAttribute('aria-current'));
      (targets.get(en.target) || []).forEach((a) => a.setAttribute('aria-current', 'true'));
    }), { rootMargin: '-45% 0px -50% 0px' });
    targets.forEach((_, el) => io.observe(el));
  }
})();
"""

# Small additions that belong to code_engine's own markup (footer links, CTA inside the mobile menu).
EXTRA_CSS = """
.footer-nav ul{display:flex;flex-wrap:wrap;justify-content:center;gap:8px 24px;list-style:none;margin:0 0 1.2em;padding:0}
.footer-nav li+li{margin-top:0}
.footer-nav a{display:inline-block;padding:.45em 0;color:var(--fg);text-decoration:none}
.footer-nav a:hover{text-decoration:underline;text-underline-offset:.2em}
.footer-note{margin:0 auto;font-size:.88rem}
.nav .nav-cta-mobile{display:none}
@media(max-width:800px){.nav:has(.nav-toggle) .nav-cta-mobile{display:block;padding-top:16px}.nav .nav-cta-mobile .btn{width:100%}}
"""

NAV_MAX = 6


def base_css(layout: str) -> str:
    """Shared utility classes + optional layout-specific CSS (templates/<layout>/layout.css)."""
    css = _tpl("landing_page/base.css") + EXTRA_CSS
    extra = TEMPLATES_DIR / LAYOUT_DIR.get(layout, "landing_page") / "layout.css"
    return css + ("\n" + extra.read_text(encoding="utf-8") if extra.is_file() else "")


def nav_footer(layout: str, brand: str, secs: list[str]) -> tuple[str, str]:
    """Semantic, JS-free markup. The mobile menu button is added by js/nav.js (HTML stack)."""
    brand = escape(brand or "Brand")
    first = secs[0] if secs else "main"
    if layout == "dashboard":
        links = "".join(f'<li><a href="#{s}">{escape(_label(s))}</a></li>' for s in secs)
        return (f'<aside class="side" aria-label="Sidebar"><a class="brand" href="#{first}">{brand}</a>'
                f'<nav aria-label="Dashboard sections"><ul>{links}</ul></nav></aside>', "")
    skip = ("hero", "cta") if layout == "landing" else ("hero",)
    items = [s for s in secs if s not in skip][:NAV_MAX]
    links = "".join(f'<li><a href="#{s}">{escape(_label(s))}</a></li>' for s in items)
    last = secs[-1] if layout == "portfolio" else "cta"
    label = "Contact" if layout == "portfolio" else "Get started"
    cta = f'<a class="btn btn-primary" href="#{last}">{label}</a>' if last in secs else ""
    cta_mobile = f'<li class="nav-cta-mobile"><a class="btn btn-primary" href="#{last}">{label}</a></li>' if cta else ""
    nav = (f'<header class="nav"><div class="wrap"><a class="brand" href="#{first}">{brand}</a>'
           f'<nav id="site-nav" aria-label="Primary"><ul>{links}{cta_mobile}</ul></nav>{cta}</div></header>')
    flinks = "".join(f'<li><a href="#{s}">{escape(_label(s))}</a></li>' for s in items)
    fnav = f'<nav class="footer-nav" aria-label="Footer"><ul>{flinks}</ul></nav>' if items else ""
    footer = (f'<footer><div class="wrap">{fnav}'
              f'<p class="footer-note">&copy; {datetime.now().year} {brand}. All rights reserved.</p></div></footer>')
    return nav, footer


def _enhance_shell(html: str, state) -> str:
    """Page-level a11y/SEO: main landmark target, nav script, meta description, theme colour."""
    html = html.replace("<main>", '<main id="main" tabindex="-1">', 1)
    html = html.replace('<script src="js/motion.js" defer></script>',
                        '<script src="js/motion.js" defer></script>\n<script src="js/nav.js" defer></script>', 1)
    desc = str(state.plan.get("tagline") or state.plan.get("description") or "").strip()
    meta = f'<meta name="description" content="{escape(desc[:160], quote=True)}">\n' if desc else ""
    meta += f'<meta name="theme-color" content="{escape(str(((state.design or {}).get("colors") or {}).get("bg") or "#0b0b14"), quote=True)}">\n'
    html = html.replace("<title>", meta + "<title>", 1)
    if animation_engine.wants_3d(getattr(state, "brief", "")) and state.plan.get("stack") != "react":
        script = '<script type="module" src="js/three-hero.js"></script>'
        if script not in html:
            html = html.replace("</body>", script + "\n</body>", 1)
    return html


def scaffold(pf, state) -> None:
    layout = state.plan.get("layout", "landing")
    if state.plan.get("stack") == "react":
        from backend.engines import react_engine
        return react_engine.scaffold(pf, state)
    pf.write("css/tokens.css", design_engine.render_tokens(state.design) + animation_engine.css_vars(state.motion))
    pf.write("css/base.css", base_css(layout))
    animation_engine.install(pf)
    pf.write("js/nav.js", NAV_JS)
    secs = state.plan["sections"]
    nav, footer = nav_footer(layout, state.plan.get("brand") or "Brand", secs)
    nav = '<a class="skip-link" href="#main">Skip to main content</a>\n' + nav
    markers = "\n".join(f"<!--SECTION:{s}--><!--/SECTION:{s}-->" for s in secs)
    html = (_tpl(f"{LAYOUT_DIR.get(layout, 'landing_page')}/index.html").replace("{{TITLE}}", escape(state.plan.get("brand") or "Brand"))
            .replace("{{FONTS}}", design_engine.fonts_link(state.design))
            .replace("{{NAV}}", nav).replace("{{SECTIONS}}", markers).replace("{{FOOTER}}", footer))
    html = _enhance_shell(html, state)
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
    # Three.js section scripts are stripped from model output. Mount the existing local runtime
    # deterministically only when the brief explicitly requests 3D.
    if sid == "hero" and animation_engine.wants_3d(getattr(state, "brief", "")):
        if not re.search(r"""\bdata-three-hero\b|data-3d\s*=\s*['"]three-hero['"]""", html, re.I):
            m = re.search(r"<([a-z][a-z0-9-]*)\b([^>]*)>", html, re.I)
            if m:
                tag, attrs = m.group(1), m.group(2)
                html = html[:m.start()] + f"<{tag}{attrs} data-three-hero>" + html[m.end():]
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
            hint = prompts.HINTS.get(sid, 'rich, detailed section')
            if sid == "hero" and animation_engine.wants_3d(state.brief):
                primary = ((state.design or {}).get("colors") or {}).get("primary", "#7c5cff")
                hint += (f" 3D IS REQUIRED BY THE USER: add data-three-hero and "
                         f'data-three-color="{primary}" to the visual wrapper. Keep all hero text and buttons '
                         "as real accessible DOM elements; the canvas is decorative. Include CSS fallback styling.")
            user = (f"{state.compact(900)}\nSECTION: {sid}\nHINT: {hint}"
                    f"\nDONE: {','.join(state.sections_done)}")
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

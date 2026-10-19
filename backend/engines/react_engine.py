"""React + Vite + TypeScript output. Same section pipeline as HTML mode: the model returns section html/css, the engine keeps those
as the source of truth in .agent/parts/ and derives src/sections/<Name>.tsx (+ .css) deterministically. Build is verified for real
(npm install -> tsc --noEmit && vite build) and the built `dist/` is what the browser tests and the live preview use."""
import json
import re
import shutil
from html import escape

from backend.agent import context
from backend.engines import animation_engine, design_engine, html2jsx
from backend.engines import code_engine as ce
from backend.tools import terminal, debugger

PKG = {
    "name": "generated-site", "private": True, "version": "0.1.0", "type": "module",
    "scripts": {"dev": "vite", "build": "tsc --noEmit && vite build", "typecheck": "tsc --noEmit", "preview": "vite preview"},
    "dependencies": {"react": "^18.3.1", "react-dom": "^18.3.1"},
    "devDependencies": {"@types/react": "^18.3.3", "@types/react-dom": "^18.3.0", "@vitejs/plugin-react": "^4.3.1",
                        "typescript": "^5.5.4", "vite": "^5.4.0"},
}
STATIC = ["vite.config.ts", "tsconfig.json", "src/main.tsx", "src/lib/motion.ts", "src/lib/MotionEffects.tsx", "src/lib/three-hero.d.ts", "src/vite-env.d.ts"]
THREE_RUNTIME = "src/lib/three-hero.js"


def pascal(sid: str) -> str:
    n = "".join(w.capitalize() for w in re.split(r"[^a-z0-9]+", sid.lower()) if w) or "Section"
    return n if n[0].isalpha() else "S" + n


def _component(name: str, body: str, css_file: str | None) -> str:
    imp = f"import './{css_file}'\n\n" if css_file else ""
    return f"{imp}export default function {name}() {{\n  return (\n    <>\n      {body}\n    </>\n  )\n}}\n"


def ensure_three_runtime(pf) -> bool:
    """Restore the checked-in runtime required by MotionEffects' static dynamic-import.

    A promise .catch() only handles runtime loading failures; Vite still resolves a
    literal import at build time. Therefore every React scaffold must contain this
    file, even when no section opts into 3D (the runtime loads Three.js only for hosts
    with the opt-in data attribute).
    """
    changed = False
    try:
        existing = pf.read(THREE_RUNTIME)
    except (OSError, ValueError, FileNotFoundError, UnicodeError):
        existing = ""
    if not existing.strip():
        runtime = animation_engine._template("three-hero.js")
        if "export function initThreeHero" not in runtime or "three-hero-fallback" not in runtime:
            raise RuntimeError("canonical Three.js runtime failed its integrity check")
        pf.write("src/lib/three-hero.js", runtime)
        changed = True

    declaration_rel = "src/lib/three-hero.d.ts"
    try:
        declaration = pf.read(declaration_rel)
    except (OSError, ValueError, FileNotFoundError, UnicodeError):
        declaration = ""
    if not declaration.strip():
        pf.write(declaration_rel, ce._tpl("react/src/lib/three-hero.d.ts"))
        changed = True
    return changed


def restore_static(pf) -> list[str]:
    """Zero-token repair: restore missing repository-owned React scaffold files."""
    restored = []
    for rel in STATIC:
        if not (pf.root / rel).is_file():
            pf.write(rel, ce._tpl(f"react/{rel}"))
            restored.append(rel)
    if ensure_three_runtime(pf):
        restored.append(THREE_RUNTIME)
    return restored


def scaffold(pf, state) -> None:
    for rel in STATIC:
        pf.write(rel, ce._tpl(f"react/{rel}"))
    runtime = animation_engine._template("three-hero.js")
    if "export function initThreeHero" not in runtime or "three-hero-fallback" not in runtime:
        raise RuntimeError("canonical Three.js runtime failed its integrity check")
    pf.write("src/lib/three-hero.js", runtime)
    # The quality gate checks a public runtime for explicitly requested 3D projects;
    # MotionEffects imports the source copy above for all React projects.
    if animation_engine.wants_3d(getattr(state, "brief", "")):
        pf.write("public/js/three-hero.js", runtime)
    pf.write("package.json", json.dumps(PKG, indent=2) + "\n")
    pf.write(".gitignore", "node_modules\ndist\n")
    pf.write("src/styles/tokens.css", design_engine.render_tokens(state.design) + animation_engine.css_vars(state.motion))
    pf.write("src/styles/base.css", ce.base_css(state.plan.get("layout", "landing")))
    pf.write("src/styles/animations.css", ce._tpl("animation/animations.css"))
    pf.write("src/styles/reduced.css", ce.RM)
    brand = state.plan.get("brand") or "Brand"
    nav, footer = ce.nav_footer(state.plan.get("layout", "landing"), brand, state.plan["sections"])
    pf.write("src/components/Nav.tsx", _component("Nav", html2jsx.convert(nav), None))
    pf.write("src/components/Footer.tsx", _component("Footer", html2jsx.convert(footer), None))
    fonts = design_engine.fonts_link(state.design)
    pf.write("index.html", ce._tpl("react/index.html").replace("{{TITLE}}", escape(brand)).replace("{{FONTS}}", fonts))
    _write_app(pf, state)


def _present(pf, state) -> list[str]:
    return [s for s in state.plan["sections"] if (pf.root / "src" / "sections" / f"{pascal(s)}.tsx").is_file()]


def _write_app(pf, state) -> None:
    if state.plan.get("layout") == "app":
        from backend.engines import app_engine
        app_engine.generate(pf, state)
        return
    secs = _present(pf, state)
    layout = state.plan.get("layout", "landing")
    imports = "".join(f"import {pascal(s)} from './sections/{pascal(s)}'\n" for s in secs)
    if layout == "authentication":
        shell_open = '<div className="auth-layout">\n      <main>'
        shell_close = "</main>\n    </div>"
        navigation_imports = ""
    elif layout == "dashboard":
        shell_open = '<div className="shell">\n      <Nav />\n      <div className="dash-main">\n        <main>'
        shell_close = "</main>\n      </div>\n    </div>"
        navigation_imports = "import Nav from './components/Nav'\nimport Footer from './components/Footer'\n"
    else:
        shell_open, shell_close = ("<Nav />\n      <main>", "</main>\n      <Footer />")
        navigation_imports = "import Nav from './components/Nav'\nimport Footer from './components/Footer'\n"
    body = "\n          ".join(f"<{pascal(s)} />" for s in secs)
    app = (f"import './styles/tokens.css'\nimport './styles/base.css'\nimport './styles/animations.css'\n"
           f"{navigation_imports}{imports}"
           f"import './styles/reduced.css'\n\nexport default function App() {{\n  return (\n    <>\n      "
           f"{shell_open}\n          {body}\n        {shell_close}\n    </>\n  )\n}}\n")
    pf.write("src/App.tsx", app)


# Any executable JSX interpolation violates the HTML-fragment contract. Do not maintain
# a short deny-list of variable names: local models invent different identifiers every run.
_JSX_EXPRESSION = re.compile(
    # Bare interpolations have no internal spaces (`{items}`); expressions may include
    # spaces only when an operator/member/call follows the identifier. Avoid treating
    # ordinary prose such as `{ text }` as executable JSX.
    r"\{(?:[A-Za-z_$][A-Za-z0-9_$]*|true|false|null|undefined)"
    r"(?:\s*(?:\.|\?\.|\[|\(|===|!==|==|!=|&&|\|\||\?\?|\+|-|\*|/|%|<|>|=).{0,140})?\}",
    re.S,
)
_JSX_FRAGMENT = re.compile(r"<\s*/?\s*>")

# Compatibility fallbacks: older copies of backend.engines.html2jsx expose only
# convert(), while newer copies also export HTML_TAGS and SVG_ELEMENTS.  The
# validation path must tolerate either version instead of failing verification.
_HTML_TAGS_FALLBACK = set((
    "a abbr address area article aside audio b base bdi bdo blockquote body br button canvas "
    "caption cite code col colgroup data datalist dd del details dfn dialog div dl dt em embed "
    "fieldset figcaption figure footer form h1 h2 h3 h4 h5 h6 head header hgroup hr html i iframe "
    "img input ins kbd label legend li link main map mark menu meta meter nav noscript object ol "
    "optgroup option output p picture pre progress q rp rt ruby s samp script search section select "
    "slot small source span strong style sub summary sup table tbody td template textarea tfoot th "
    "thead time title tr track u ul var video wbr svg math"
).split())
_SVG_TAGS_FALLBACK = set((
    "svg g defs symbol use path rect circle ellipse line polyline polygon text tspan title desc "
    "metadata clippath mask pattern marker lineargradient radialgradient stop filter feblend "
    "fecolormatrix fecomponenttransfer fecomposite feconvolvematrix fediffuselighting "
    "fedisplacementmap fedistantlight fedropshadow feflood fefunca fefuncb fefuncg fefuncr "
    "fegaussianblur feimage femerge femergenode femorphology feoffset fepointlight "
    "fespecularlighting fespotlight fetile feturbulence foreignobject textpath animatemotion "
    "animatetransform animate set view"
).split())


def _known_markup_tags() -> set[str]:
    """Return recognized HTML/SVG tags across old and new html2jsx module versions."""
    known = set(_HTML_TAGS_FALLBACK) | set(_SVG_TAGS_FALLBACK)
    html_tags = getattr(html2jsx, "HTML_TAGS", ())
    svg_tags = getattr(html2jsx, "SVG_ELEMENTS", ())
    # Some legacy implementations expose an SVG name map instead of SVG_ELEMENTS.
    svg_name_map = getattr(html2jsx, "SVG_TAGS", {})
    if isinstance(html_tags, dict):
        html_tags = (*html_tags.keys(), *html_tags.values())
    if isinstance(svg_tags, dict):
        svg_tags = (*svg_tags.keys(), *svg_tags.values())
    if isinstance(svg_name_map, dict):
        svg_tags = (*tuple(svg_tags), *svg_name_map.keys(), *svg_name_map.values())
    for tag in (*tuple(html_tags or ()), *tuple(svg_tags or ())):
        if isinstance(tag, str):
            known.add(tag.lower())
    return known


def _looks_like_raw_jsx(markup: str) -> bool:
    """Reject React/JSX constructs and unknown intrinsic tags before they reach TypeScript.

    The model contract is an HTML fragment, not JSX. This check intentionally uses broad
    structural rules instead of a brittle list of known hallucinated component names.
    """
    source = str(markup or "")
    if _JSX_FRAGMENT.search(source):
        return True
    # Inline style braces are ordinary CSS and must not be mistaken for JavaScript expressions.
    source = re.sub(r"<style\b[^>]*>.*?</style\s*>", "", source, flags=re.I | re.S)
    source = re.sub(r"<!--.*?-->", "", source, flags=re.S)
    if _JSX_EXPRESSION.search(source):
        return True
    tag_text = " ".join(re.findall(r"<[^>]+>", source))
    if re.search(r"=>|\.map\s*\(", tag_text):
        return True
    # Unknown non-hyphenated tags are neither HTML nor valid custom elements, and
    # PascalCase unknown tags are React components the generator has not imported.
    known = _known_markup_tags()
    for tag in re.findall(r"<\s*/?\s*([A-Za-z][A-Za-z0-9:_-]*)\b", source):
        low = tag.lower()
        if low not in known and "-" not in low and ":" not in low:
            return True
        if tag[:1].isupper() and low not in known:
            return True
    return False


def _safe_section_fallback(sid: str, state) -> tuple[str, str]:
    """Token-free, build-safe HTML for a section when the model returns React-only JSX.

    This fallback is intentionally used only when output violates the HTML-fragment contract, never
    just because prose or styling is imperfect. No fabricated business figures are shown.
    """
    key = sid.lower().replace("-", "_")
    if key == "kpis":
        html = (
            '<section class="safe-kpis" aria-labelledby="kpis-heading">'
            '<header class="safe-section-heading"><p class="safe-eyebrow">Store overview</p>'
            '<h2 id="kpis-heading">Key performance indicators</h2>'
            '<p>Live metrics will appear here when store data is connected.</p></header>'
            '<div class="safe-kpi-grid">'
            '<article class="safe-kpi-card"><span>Total sales</span><strong>—</strong><small>Awaiting live data</small></article>'
            '<article class="safe-kpi-card"><span>Orders</span><strong>—</strong><small>Awaiting live data</small></article>'
            '<article class="safe-kpi-card"><span>Products</span><strong>—</strong><small>Awaiting live data</small></article>'
            '<article class="safe-kpi-card"><span>Customers</span><strong>—</strong><small>Awaiting live data</small></article>'
            '</div></section>'
        )
        css = (
            '.safe-kpis{display:grid;gap:1.25rem}.safe-section-heading{display:grid;gap:.45rem}'
            '.safe-section-heading h2{margin:0;font-size:clamp(1.35rem,2vw,1.8rem)}'
            '.safe-section-heading p{margin:0;color:var(--muted,#7a8494)}'
            '.safe-eyebrow{font-size:.78rem;font-weight:700;letter-spacing:.12em;text-transform:uppercase}'
            '.safe-kpi-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:1rem}'
            '.safe-kpi-card{display:grid;gap:.55rem;padding:1.15rem;border:1px solid var(--border,rgba(128,128,128,.22));'
            'border-radius:var(--radius,14px);background:var(--surface,rgba(128,128,128,.06));min-width:0}'
            '.safe-kpi-card span,.safe-kpi-card small{color:var(--muted,#7a8494)}.safe-kpi-card strong{font-size:1.8rem}'
            '@media(max-width:900px){.safe-kpi-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}'
            '@media(max-width:520px){.safe-kpi-grid{grid-template-columns:1fr}}'
        )
        return html, css

    title = ce._label(sid)
    html = (f'<section class="safe-section" aria-labelledby="safe-{escape(sid)}-heading">'
            f'<p class="safe-eyebrow">Workspace</p><h2 id="safe-{escape(sid)}-heading">{escape(title)}</h2>'
            '<p>Content for this section can be added once its requirements are confirmed.</p></section>')
    css = ('.safe-section{display:grid;gap:.75rem}.safe-section h2{margin:0}'
           '.safe-section p{color:var(--muted,#7a8494)}.safe-eyebrow{font-size:.78rem;font-weight:700;letter-spacing:.12em;text-transform:uppercase}')
    return html, css


def _normalize_firebase_auth_form_tags(markup: str, sid: str) -> str:
    """Convert hallucinated FirebaseAuthForm tags into native forms before HTML->JSX.

    Section prompts return HTML, not imported React components. Leaving this invented
    tag as ``<firebaseauthform>`` creates TS2339, while preserving a capitalized
    ``<FirebaseAuthForm>`` in some direct JSX paths creates TS2304. The generated
    FirebaseAuthBridge already wires native forms using ``data-firebase-auth``.
    """
    mode = {"login": "login", "register": "register", "forgot_password": "forgot_password",
            "reset_password": "reset_password"}.get(sid)
    if not mode:
        return markup

    pattern = re.compile(r"<\s*(/?)\s*firebaseauthform\b([^>]*)>", re.I)

    def replace(match):
        if match.group(1):
            return "</form>"
        attrs = match.group(2) or ""
        self_closing = bool(re.search(r"/\s*$", attrs))
        attrs = re.sub(r"/\s*$", "", attrs)
        if not re.search(r"\bdata-firebase-auth\s*=", attrs, re.I):
            attrs += f' data-firebase-auth="{mode}"'
        opening = f"<form{attrs}>"
        return opening + "</form>" if self_closing else opening

    return pattern.sub(replace, markup)


def _normalize_firebase_auth_form_jsx(jsx: str, sid: str) -> str:
    """Last line of defense for auth component tags that survive a generation path."""
    mode = {"login": "login", "register": "register", "forgot_password": "forgot_password",
            "reset_password": "reset_password"}.get(sid)
    if not mode:
        return jsx
    pattern = re.compile(r"<\s*(/?)\s*firebaseauthform\b([^>]*)>", re.I)

    def replace(match):
        if match.group(1):
            return "</form>"
        attrs = match.group(2) or ""
        self_closing = bool(re.search(r"/\s*$", attrs))
        attrs = re.sub(r"/\s*$", "", attrs)
        if not re.search(r"\bdata-firebase-auth\s*=", attrs, re.I):
            attrs += f' data-firebase-auth="{mode}"'
        opening = f"<form{attrs}>"
        return opening + "</form>" if self_closing else opening

    return pattern.sub(replace, jsx)


def _wire_firebase_auth_form(html: str, sid: str) -> str:
    """Tag generated auth forms so the runtime Firebase bridge can wire their submit events."""
    mode = {"login": "login", "register": "register", "forgot_password": "forgot_password", "reset_password": "reset_password"}.get(sid)
    if not mode or not re.search(r"<form\b", html, re.I):
        return html

    def tag_form(match):
        opening = match.group(0)
        if "data-firebase-auth" not in opening.lower():
            opening = opening[:-1] + f' data-firebase-auth="{mode}">'
        return opening

    html = re.sub(r"<form\b[^>]*>", tag_form, html, count=1, flags=re.I)
    input_pattern = re.compile(r"<input\b[^>]*>", re.I)
    input_tags = input_pattern.findall(html)
    seen_email = False
    seen_password = False

    def attr(tag: str, name: str) -> str:
        match = re.search(r"\b" + re.escape(name) + r"\s*=\s*(['\"])(.*?)\1", tag, re.I)
        return match.group(2).lower() if match else ""

    def hints(tag: str) -> str:
        return " ".join(attr(tag, key) for key in ("name", "placeholder", "aria-label", "autocomplete", "type"))

    # Prefer an explicitly identified email field. A registration form often puts
    # full-name first, so blindly tagging the first text input as email is incorrect.
    has_explicit_email = any(
        attr(tag, "type") == "email" or "email" in hints(tag)
        for tag in input_tags
    )

    def tag_input(match):
        nonlocal seen_email, seen_password
        tag = match.group(0)
        hint = hints(tag)
        typ = attr(tag, "type")
        name = attr(tag, "name")
        is_password = typ == "password" or "password" in hint
        is_email = typ == "email" or "email" in hint
        looks_like_name = any(word in hint for word in ("fullname", "full name", "display name", "username", "first name", "last name"))
        if is_password and not seen_password:
            seen_password = True
            if not name:
                tag = tag[:-1] + ' name="password">'
            if not typ:
                tag = re.sub(r"<input\b", '<input type="password"', tag, count=1, flags=re.I)
        elif (is_email or (not has_explicit_email and not seen_email and not looks_like_name
                           and typ not in ("hidden", "submit", "button", "checkbox", "radio", "password")
                           and name not in ("name", "fullname", "full_name", "username"))) and not seen_email:
            seen_email = True
            if not name:
                tag = tag[:-1] + ' name="email">'
            if not typ:
                tag = re.sub(r"<input\b", '<input type="email"', tag, count=1, flags=re.I)
        elif looks_like_name and not name:
            tag = tag[:-1] + ' name="fullName">'
        return tag

    html = input_pattern.sub(tag_input, html)
    if "data-firebase-auth-status" not in html.lower():
        html = re.sub(r"</form\s*>", '<p data-firebase-auth-status aria-live="polite"></p></form>', html, count=1, flags=re.I)
    return html


def _prepare_section_source(sid: str, html: str, css: str, state) -> tuple[str, str, bool]:
    """Normalize model-produced HTML/CSS before either saving or compiling it.

    Generated sections are HTML fragments, never arbitrary React modules. Any executable
    JSX expression or unknown component tag is replaced with a safe section scaffold before
    it can become TypeScript source.
    """
    html, css = ce.clean_html(html), ce.clean_css(css)
    stack = ((getattr(state, "stack_config", None) or {}).get("stack") or {})
    firebase_auth = (stack.get("backend") or "none") == "none" and (stack.get("auth") or "none") == "firebase-auth"
    if firebase_auth:
        html = _normalize_firebase_auth_form_tags(html, sid)
        html = _wire_firebase_auth_form(html, sid)
    rejected = _looks_like_raw_jsx(html)
    if rejected:
        html, css = _safe_section_fallback(sid, state)
    if not ce._has_id(html, sid):
        html = f'<div id="{escape(sid, quote=True)}">{html}</div>'
    return html, css, rejected


def _render_section_component(sid: str, html: str, css: str, state) -> tuple[str, str]:
    """Return deterministic CSS/TSX derived only from the canonical HTML/CSS fragment."""
    name = pascal(sid)
    stack = ((getattr(state, "stack_config", None) or {}).get("stack") or {})
    firebase_auth = (stack.get("backend") or "none") == "none" and (stack.get("auth") or "none") == "firebase-auth"
    jsx = html2jsx.convert(html)
    if firebase_auth:
        jsx = _normalize_firebase_auth_form_jsx(jsx, sid)
    return css, _component(name, jsx, f"{sid}.css")


def insert(pf, state, sid: str, html: str, css: str) -> None:
    html, css, rejected = _prepare_section_source(sid, html, css, state)
    if rejected:
        context.progress(
            "code",
            f"Rejected React-only component/variable syntax in '{sid}'; inserted a valid HTML scaffold without another model call",
            "warn",
        )
    pf.write(f".agent/parts/{sid}.html", html)
    pf.write(f".agent/parts/{sid}.css", css)
    css_text, tsx_text = _render_section_component(sid, html, css, state)
    pf.write(f"src/sections/{sid}.css", css_text)
    pf.write(f"src/sections/{pascal(sid)}.tsx", tsx_text)
    _write_app(pf, state)


def reconcile_derived_outputs(pf, state) -> list[str]:
    """Rebuild generated React outputs from canonical section HTML/CSS before every build.

    `.agent/parts/*.html` and `.agent/parts/*.css` are authoritative. Section TSX is derived
    output: it must never retain a bad edit from a repair attempt such as undeclared JSX
    components (`HeroBanner`, `ProductCardList`) or free variables (`featuredProducts`).
    Reconciliation is idempotent, updates only generator-owned section outputs, and sanitizes
    malformed canonical HTML using the same safe fallback as normal generation.
    """
    if not (state.plan or {}).get("sections") or state.plan.get("layout") == "app":
        return []
    changed: list[str] = []
    for sid in state.plan.get("sections", []):
        try:
            html, css = get_section(pf, sid)
        except (OSError, ValueError, FileNotFoundError):
            continue
        if not html.strip():
            continue
        prepared_html, prepared_css, rejected = _prepare_section_source(sid, html, css, state)
        if rejected:
            context.progress("verify", f"Rejected invalid JSX-like source in canonical section '{sid}' and restored a safe HTML scaffold", "warn")
        # Persist sanitization so the next edit/repair starts from the corrected canonical source.
        if prepared_html != html:
            pf.write(f".agent/parts/{sid}.html", prepared_html)
        if prepared_css != css:
            pf.write(f".agent/parts/{sid}.css", prepared_css)
        css_text, tsx_text = _render_section_component(sid, prepared_html, prepared_css, state)
        expected = {
            f"src/sections/{sid}.css": css_text,
            f"src/sections/{pascal(sid)}.tsx": tsx_text,
        }
        for rel, content in expected.items():
            try:
                current = pf.read(rel)
            except (OSError, ValueError, FileNotFoundError):
                current = None
            if current != content:
                pf.write(rel, content)
                changed.append(rel)
    if changed:
        # App imports are derived from the currently present generated sections too.
        _write_app(pf, state)
        context.progress("verify", "Rebuilt derived React files from canonical section sources: " + ", ".join(changed[:8]), "warn")
    return changed

def get_section(pf, sid: str):
    def rd(ext):
        try:
            return pf.read(f".agent/parts/{sid}.{ext}")
        except FileNotFoundError:
            return ""
    return rd("html").strip(), rd("css")


# ---------------------------------------------------------------------------------------------- build verification
SEC_FILE = re.compile(r"src/sections/([A-Za-z0-9]+)\.(?:tsx|css)")


def sid_from_output(text: str, state) -> str | None:
    m = SEC_FILE.search(text)
    if not m:
        return None
    for s in state.plan.get("sections", []):
        if pascal(s) == m.group(1):
            return s
    return None


_DIAGNOSTIC_MARKER = re.compile(
    r"error\s+TS\d+|error during build|\bERROR:|\bnpm ERR!|unexpected token|"
    r"transform failed|failed to resolve|could not resolve|cannot find module|"
    r"failed to parse|syntaxerror|typeerror|referenceerror|rolluperror|\[vite:", re.I)


def diagnostic_blocks(output: str, max_blocks: int = 6, max_chars: int = 2200) -> list[str]:
    """Extract compiler-error neighborhoods instead of returning just stack-frame lines."""
    lines = (output or "").splitlines()
    if not lines:
        return ["Build command failed without diagnostic output."]
    marker_indexes = [i for i, line in enumerate(lines) if _DIAGNOSTIC_MARKER.search(line)]
    if not marker_indexes:
        return ["\n".join(lines[-10:])[-max_chars:]]

    # Specific syntax/type messages are ranked before generic wrappers like "error during build".
    def priority(i: int) -> tuple[int, int]:
        line = lines[i]
        score = 0
        if re.search(r"error\s+TS\d+|\bERROR:|unexpected token|transform failed|could not resolve|cannot find module|failed to parse|syntaxerror", line, re.I):
            score += 10
        if re.search(r"(?:src[/\\].+\.(?:tsx?|jsx?|css|json)|\.(?:tsx?|jsx?|css|json):\d+:\d+|\(\d+,\d+\))", line, re.I):
            score += 8
        if re.search(r"^\s*at\s+", line):
            score -= 4
        return (-score, i)

    selected = []
    for i in sorted(marker_indexes, key=priority):
        lo, hi = max(0, i - 2), min(len(lines), i + 5)
        # Merge overlapping neighborhoods so the primary error and source location remain together.
        merged = False
        for j, (a, b) in enumerate(selected):
            if lo <= b and hi >= a:
                selected[j] = (min(a, lo), max(b, hi))
                merged = True
                break
        if not merged:
            selected.append((lo, hi))
        selected.sort()
        rendered = ["\n".join(lines[a:b]) for a, b in selected]
        if len(rendered) >= max_blocks or sum(map(len, rendered)) >= max_chars:
            break

    rendered = ["\n".join(lines[a:b]).strip() for a, b in selected]
    out, remaining = [], max_chars
    for block in rendered:
        if not block or remaining <= 0:
            continue
        block = block[:min(remaining, 900)]
        out.append(block)
        remaining -= len(block) + 2
        if len(out) >= max_blocks:
            break
    return out or ["\n".join(lines[-10:])[-max_chars:]]


def repair_known_scaffold_import(pf, output: str) -> bool:
    """Repair one known LLM self-repair regression without another model call.

    MotionEffects.tsx is agent-owned scaffold. If a previous repair adds an invalid
    ``../three-hero`` import, TypeScript reports TS2307. Restore this tiny component
    from the canonical template rather than repeatedly asking a small model to patch
    the same missing module. Other files and imports are deliberately untouched.
    """
    text_out = (output or "").replace("\\", "/")
    if "src/lib/MotionEffects.tsx" not in text_out:
        return False
    if not re.search(r"TS2307|Cannot find module", output or "", re.I):
        return False
    if not re.search(r"Cannot find module\s+['\"]\.\./three-hero['\"]", output or "", re.I):
        return False
    rel = "src/lib/MotionEffects.tsx"
    try:
        current = pf.read(rel)
        if "../three-hero" not in current and "..\\three-hero" not in current:
            return False
        canonical = ce._tpl("react/src/lib/MotionEffects.tsx")
        if not canonical or current == canonical:
            return False
        pf.write(rel, canonical)
    except (OSError, ValueError, FileNotFoundError):
        return False
    context.progress(
        "repair",
        "Restored src/lib/MotionEffects.tsx from the canonical scaffold after an unresolved ../three-hero import",
        "warn",
    )
    return True


def restore_generated_sections_from_diagnostics(pf, state, output: str) -> list[str]:
    """Rebuild failed derived TSX sections from canonical .agent/parts HTML/CSS.

    `src/sections/*.tsx` is generated output, not the source of truth. LLM file-level
    repair of these files can introduce undeclared identifiers or invalid JSX even when
    the original fragment was valid. Restore only sections explicitly named by compiler
    diagnostics, and never overwrite unrelated/user files.
    """
    if not re.search(r"error\s+TS\d+|error during build|transform failed|failed to parse", output or "", re.I):
        return []
    if not (state.plan or {}).get("sections"):
        return []
    rels = set(re.findall(r"""(?:^|[\s"'(:])((?:src[/\\])sections[/\\][A-Za-z0-9]+\.tsx)""", output or "", re.I))
    if not rels:
        return []
    found = {rel.replace("\\", "/").lower() for rel in rels}
    restored: list[str] = []
    for sid in state.plan.get("sections", []):
        rel = f"src/sections/{pascal(sid)}.tsx"
        if rel.lower() not in found:
            continue
        html, css = get_section(pf, sid)
        if not html.strip():
            continue
        try:
            before = pf.read(rel)
        except (OSError, ValueError, FileNotFoundError):
            before = ""
        # `insert` validates the HTML-fragment contract, falling back to a deterministic
        # safe scaffold if a previous repair accidentally put raw JSX into the source part.
        insert(pf, state, sid, html, css)
        try:
            after = pf.read(rel)
        except (OSError, ValueError, FileNotFoundError):
            after = ""
        if after and after != before:
            restored.append(rel)
    return restored


def build(pf, state) -> dict:
    """Real build. Preserve useful diagnostics so failed generated files can be repaired."""
    checks, issues = [], []

    def chk(name, status, detail=""):
        checks.append({"name": name, "viewport": "build", "status": status, "detail": detail})

    if not shutil.which("node") or not shutil.which("npm"):
        msg = "node/npm not found: React build, type check and browser tests could not run (install Node.js 18+)"
        for n in ("npm install", "type check", "production build"):
            chk(n, "skipped", msg)
        return {"issues": [{"sid": None, "msg": msg}], "checks": checks, "note": msg, "built": False}
    # Existing generated projects may predate the runtime being written by the React
    # scaffold. Repair this known missing module deterministically before TypeScript/Vite
    # runs, so the model never wastes a repair round on an agent-owned asset.
    runtime_restored = ensure_three_runtime(pf)
    if runtime_restored:
        context.progress("build", "Restored missing agent-owned src/lib/three-hero.js from the canonical runtime", "warn")

    # Never compile stale or LLM-patched derived TSX. Reconstruct section components
    # from canonical HTML/CSS before invoking TypeScript or Vite.
    try:
        reconciled = reconcile_derived_outputs(pf, state)
    except Exception as exc:  # diagnostics must still be reported if reconciliation fails
        reconciled = []
        context.progress("verify", f"Derived-file reconciliation failed ({type(exc).__name__}); continuing with compiler diagnostics", "warn")
    cwd = str(pf.root)
    if not (pf.root / "node_modules" / "vite").is_dir():
        context.progress("build", "npm install (first run can take a few minutes)")
        r = terminal.run(["npm", "install", "--no-audit", "--no-fund", "--prefer-offline"], cwd, timeout=900, max_out=1500)
        if r["code"] != 0:
            detail = "\n\n".join(diagnostic_blocks(r["out"], max_blocks=3, max_chars=1200))
            msg = f"npm install failed (code {r['code']}):\n{detail}"
            chk("npm install", "failed", msg[:400])
            for n in ("type check", "production build"):
                chk(n, "skipped", "npm install failed")
            return {"issues": [{"sid": None, "msg": msg}], "checks": checks, "note": "npm install failed", "built": False}
    chk("npm install", "passed")
    context.progress("build", "tsc --noEmit && vite build")
    r = terminal.run(["npm", "run", "build"], cwd, timeout=300, max_out=12000)
    out = r["out"]
    auto_repairs: list[str] = [THREE_RUNTIME] if runtime_restored else []
    if r["code"] != 0 and repair_known_scaffold_import(pf, out):
        auto_repairs.append("src/lib/MotionEffects.tsx")
        context.check()
        context.progress("build", "Retrying TypeScript/Vite build after deterministic scaffold repair")
        r = terminal.run(["npm", "run", "build"], cwd, timeout=300, max_out=12000)
        out = r["out"]
    if r["code"] != 0:
        restored = restore_generated_sections_from_diagnostics(pf, state, out)
        if restored:
            auto_repairs.extend(restored)
            context.check()
            context.progress("build", "Regenerated derived section TSX from canonical HTML/CSS source: " + ", ".join(restored), "warn")
            r = terminal.run(["npm", "run", "build"], cwd, timeout=300, max_out=12000)
            out = r["out"]
    deterministic_repair = bool(auto_repairs)
    if r["code"] == 0:
        detail = "passed after deterministic source-of-truth repair" if deterministic_repair else ""
        chk("type check", "passed", detail)
        chk("production build", "passed", detail)
        if not auto_repairs and not reconciled:
            note = "ok"
        elif not auto_repairs and reconciled:
            note = "ok (derived React output reconciled)"
        elif auto_repairs == ["src/lib/MotionEffects.tsx"]:
            note = "ok (scaffold import repaired)"
        else:
            note = "ok (generated files restored)"
        return {"issues": [], "checks": checks, "note": note,
                "built": True, "auto_repairs": auto_repairs}

    blocks = diagnostic_blocks(out, max_blocks=6, max_chars=5000)
    parsed = debugger.prioritize_diagnostics(debugger.parse_diagnostics(out, root=pf.root), root=pf.root)
    ts = bool(re.search(r"error\s+TS\d+", out, re.I))
    vite_started = bool(re.search(r"vite v\d|transforming \(|building for production|error during build|\[vite:", out, re.I))
    type_status = "failed" if ts or not vite_started else "passed"
    type_detail = "TypeScript/compiler diagnostics found" if ts else ("passed before Vite build failed" if vite_started else "build command failed before type-check completion")
    chk("type check", type_status, type_detail)
    chk("production build", "skipped" if type_status == "failed" else "failed",
        "not executed: type check failed" if type_status == "failed" else (blocks[0][:400] if blocks else "Vite production build failed"))
    if parsed:
        # Emit individual file/line-aware root diagnostics rather than broad stack-trace wrappers.
        for diagnostic in parsed[:16]:
            rel = diagnostic.get("file") or ""
            line = diagnostic.get("line")
            code = f" {diagnostic['code']}" if diagnostic.get("code") else ""
            issue_text = (f"build diagnostic [{diagnostic['category']}]: "
                          f"{rel}{(':'+str(line)) if line else ''}:{code} {diagnostic['message']}").strip()
            issues.append({"sid": sid_from_output(rel + "\n" + issue_text, state),
                           "file": rel or None, "line": line, "category": diagnostic.get("category"),
                           "tool": diagnostic.get("tool"), "msg": issue_text[:1600]})
    else:
        for block in blocks:
            issue_text = f"build diagnostic:\n{block}"
            issues.append({"sid": sid_from_output(issue_text, state), "msg": issue_text[:1600]})
    cause_report = debugger.root_cause_summary(issues, root=pf.root)
    for hint in cause_report.get("root_cause_hints", [])[:3]:
        context.progress("debugger", hint, "warn")
    if deterministic_repair:
        issues = [{**item, "msg": ("Deterministic repair was attempted; " + item["msg"])[:1600]}
                  for item in issues]
    return {"issues": issues or [{"sid": None, "msg": f"build failed (exit {r['code']}):\n{out[-1200:]}"}],
            "checks": checks, "note": "build failed after deterministic repair" if deterministic_repair else "build failed",
            "built": False, "auto_repairs": auto_repairs, "diagnostics": parsed[:40], "root_cause": cause_report}
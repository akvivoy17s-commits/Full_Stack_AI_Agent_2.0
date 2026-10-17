"""React + Vite + TypeScript output. Same section pipeline as HTML mode: the model returns section html/css, the engine keeps those
as the source of truth in .agent/parts/ and derives src/sections/<Name>.tsx (+ .css) deterministically. Build is verified for real
(npm install -> tsc --noEmit && vite build) and the built `dist/` is what the browser tests and the live preview use.

Shell quality (zero LLM tokens, all deterministic):
  * Nav.tsx      real React nav: mobile menu toggle, Escape / outside-click / link-click close, scroll-spy (aria-current)
  * App.tsx      skip link, <main id="main" tabIndex={-1}> landmark, every section wrapped in an error boundary
  * index.html   viewport-fit=cover, meta description, theme-color, noscript message
  * SectionBoundary.tsx  one broken generated section can never blank the whole page
"""
import json
import re
import shutil
from html import escape

from backend.agent import context
from backend.engines import animation_engine, design_engine, html2jsx
from backend.engines import code_engine as ce
from backend.tools import terminal

PKG = {
    "name": "generated-site", "private": True, "version": "0.1.0", "type": "module",
    "engines": {"node": ">=18"},
    "scripts": {"dev": "vite", "build": "tsc --noEmit && vite build", "typecheck": "tsc --noEmit", "preview": "vite preview"},
    "dependencies": {"react": "^18.3.1", "react-dom": "^18.3.1"},
    "devDependencies": {"@types/react": "^18.3.3", "@types/react-dom": "^18.3.0", "@vitejs/plugin-react": "^4.3.1",
                        "typescript": "^5.5.4", "vite": "^5.4.0"},
}
STATIC = ["vite.config.ts", "tsconfig.json", "src/main.tsx", "src/lib/motion.ts", "src/lib/MotionEffects.tsx", "src/vite-env.d.ts"]

# --------------------------------------------------------------------------------------------- shell building blocks
SECTION_BOUNDARY_TSX = """import { Component, type ErrorInfo, type ReactNode } from 'react'

type Props = { id: string; children: ReactNode }
type State = { failed: boolean }

/** Keeps one broken generated section from blanking the whole page (renders nothing extra when healthy). */
export default class SectionBoundary extends Component<Props, State> {
  state: State = { failed: false }

  static getDerivedStateFromError(): State {
    return { failed: true }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error(`[section:${this.props.id}]`, error, info.componentStack)
  }

  render() {
    if (!this.state.failed) return this.props.children
    return (
      <section id={this.props.id} className="sec section-fallback">
        <div className="wrap">
          <p role="status">This section could not be displayed.</p>
        </div>
      </section>
    )
  }
}
"""

SHELL_CSS = """/* React shell helpers: landmark focus, stacking, section fallback */
#root{isolation:isolate}
main:focus,main:focus-visible{outline:none}
.section-fallback{text-align:center}
"""

NAV_TSX = """import { useEffect, useRef, useState } from 'react'

const BRAND: string = __BRAND__
const FIRST: string = __FIRST__
const LINKS: { id: string; label: string }[] = __LINKS__
const CTA: { id: string; label: string } | null = __CTA__

export default function Nav() {
  const root = useRef<HTMLElement>(null)
  const toggle = useRef<HTMLButtonElement>(null)
  const [open, setOpen] = useState(false)
  const [active, setActive] = useState('')

  // `.open` is toggled on the existing <header>: motion.ts toggles `.scrolled` on the same node, so className must stay constant.
  useEffect(() => {
    root.current?.classList.toggle('open', open)
  }, [open])

  // Escape closes (and returns focus to the button); a click outside the header closes.
  useEffect(() => {
    if (!open) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setOpen(false)
        toggle.current?.focus()
      }
    }
    const onDoc = (e: MouseEvent) => {
      if (root.current && !root.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('keydown', onKey)
    document.addEventListener('click', onDoc)
    return () => {
      document.removeEventListener('keydown', onKey)
      document.removeEventListener('click', onDoc)
    }
  }, [open])

  // Leaving the mobile breakpoint always resets the menu.
  useEffect(() => {
    const mq = window.matchMedia('(max-width: 800px)')
    const onChange = () => {
      if (!mq.matches) setOpen(false)
    }
    mq.addEventListener('change', onChange)
    return () => mq.removeEventListener('change', onChange)
  }, [])

  // Scroll-spy: mark the link of the section in view with aria-current.
  useEffect(() => {
    if (!('IntersectionObserver' in window)) return
    const targets = LINKS.map((l) => document.getElementById(l.id)).filter((el): el is HTMLElement => !!el && !!el.closest('main'))
    if (!targets.length) return
    const io = new IntersectionObserver(
      (entries) => entries.forEach((en) => { if (en.isIntersecting) setActive(en.target.id) }),
      { rootMargin: '-45% 0px -50% 0px' },
    )
    targets.forEach((el) => io.observe(el))
    return () => io.disconnect()
  }, [])

  return (
    <header className="nav" ref={root}>
      <div className="wrap">
        <a className="brand" href={`#${FIRST}`}>{BRAND}</a>
        <nav id="site-nav" aria-label="Primary" onClick={(e) => { if ((e.target as HTMLElement).closest('a')) setOpen(false) }}>
          <ul>
            {LINKS.map((l) => (
              <li key={l.id}>
                <a href={`#${l.id}`} aria-current={active === l.id ? 'true' : undefined}>{l.label}</a>
              </li>
            ))}
            {CTA && (
              <li className="nav-cta-mobile">
                <a className="btn btn-primary" href={`#${CTA.id}`}>{CTA.label}</a>
              </li>
            )}
          </ul>
        </nav>
        {CTA && <a className="btn btn-primary" href={`#${CTA.id}`}>{CTA.label}</a>}
        <button
          ref={toggle}
          type="button"
          className="nav-toggle"
          aria-expanded={open}
          aria-controls="site-nav"
          aria-label={open ? 'Close menu' : 'Open menu'}
          onClick={() => setOpen((v) => !v)}
        >
          <span aria-hidden="true" />
        </button>
      </div>
    </header>
  )
}
"""

NOSCRIPT = '<div id="root"><noscript>This site needs JavaScript enabled to display its content.</noscript></div>'


def pascal(sid: str) -> str:
    n = "".join(w.capitalize() for w in re.split(r"[^a-z0-9]+", sid.lower()) if w) or "Section"
    return n if n[0].isalpha() else "S" + n


def _component(name: str, body: str, css_file: str | None) -> str:
    imp = f"import './{css_file}'\n\n" if css_file else ""
    return f"{imp}export default function {name}() {{\n  return (\n    <>\n      {body}\n    </>\n  )\n}}\n"


def _nav_tsx(layout: str, brand: str, secs: list[str]) -> str:
    """Interactive Nav component for landing/portfolio. Same link rules as code_engine.nav_footer (HTML stack parity)."""
    skip = ("hero", "cta") if layout == "landing" else ("hero",)
    items = [s for s in secs if s not in skip][:ce.NAV_MAX]
    last = secs[-1] if layout == "portfolio" and secs else "cta"
    cta = {"id": last, "label": "Contact" if layout == "portfolio" else "Get started"} if last in secs else None
    links = [{"id": s, "label": ce._label(s)} for s in items]
    dump = lambda v: json.dumps(v, ensure_ascii=False)  # noqa: E731  (JSON is valid TS literal syntax)
    return (NAV_TSX.replace("__BRAND__", dump(brand)).replace("__FIRST__", dump(secs[0] if secs else "main"))
            .replace("__LINKS__", dump(links)).replace("__CTA__", dump(cta)))


def restore_static(pf) -> list[str]:
    """Zero-token repair: rewrite any missing scaffold file (vite/tsconfig/main.tsx/lib/*) from the templates.
    State-free shell helpers (SectionBoundary, shell.css) are restored too, but are not part of the returned STATIC list."""
    restored = []
    for rel in STATIC:
        if not (pf.root / rel).is_file():
            pf.write(rel, ce._tpl(f"react/{rel}"))
            restored.append(rel)
    for rel, text in (("src/components/SectionBoundary.tsx", SECTION_BOUNDARY_TSX), ("src/styles/shell.css", SHELL_CSS)):
        if not (pf.root / rel).is_file():
            pf.write(rel, text)
    runtime_path = "src/lib/three-hero.js"
    if not (pf.root / runtime_path).is_file():
        runtime = animation_engine._template("three-hero.js").replace(
            "if (typeof document !== 'undefined') initThreeHero();", ""
        )
        pf.write(runtime_path, runtime)
        restored.append(runtime_path)
    return restored


def _index_html(state, brand: str, fonts: str) -> str:
    html = ce._tpl("react/index.html").replace("{{TITLE}}", escape(brand)).replace("{{FONTS}}", fonts)
    html = html.replace("width=device-width,initial-scale=1", "width=device-width,initial-scale=1,viewport-fit=cover", 1)
    html = ce._enhance_shell(html, state)                      # meta description + theme-color (same as HTML stack)
    return html.replace('<div id="root"></div>', NOSCRIPT, 1)


def scaffold(pf, state) -> None:
    layout = state.plan.get("layout", "landing")
    for rel in STATIC:
        pf.write(rel, ce._tpl(f"react/{rel}"))
    runtime = animation_engine._template("three-hero.js").replace(
        "if (typeof document !== 'undefined') initThreeHero();", ""
    )
    pf.write("src/lib/three-hero.js", runtime)
    pf.write("package.json", json.dumps(PKG, indent=2) + "\n")
    pf.write(".gitignore", "node_modules\ndist\n")
    pf.write("src/styles/tokens.css", design_engine.render_tokens(state.design) + animation_engine.css_vars(state.motion))
    pf.write("src/styles/base.css", ce.base_css(layout))
    pf.write("src/styles/animations.css", ce._tpl("animation/animations.css"))
    pf.write("src/styles/shell.css", SHELL_CSS)
    pf.write("src/styles/reduced.css", ce.RM)
    pf.write("src/components/SectionBoundary.tsx", SECTION_BOUNDARY_TSX)
    brand = state.plan.get("brand") or "Brand"
    secs = state.plan["sections"]
    nav, footer = ce.nav_footer(layout, brand, secs)
    pf.write("src/components/Nav.tsx", _component("Nav", html2jsx.convert(nav), None) if layout == "dashboard"
             else _nav_tsx(layout, brand, secs))
    pf.write("src/components/Footer.tsx", _component("Footer", html2jsx.convert(footer), None))
    pf.write("index.html", _index_html(state, brand, design_engine.fonts_link(state.design)))
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
    main_open = '<main id="main" tabIndex={-1}>'
    shell_open, shell_close = ((f'<div className="shell">\n      <Nav />\n      <div className="dash-main">\n        {main_open}', "</main>\n      </div>\n    </div>")
                               if layout == "dashboard" else (f"<Nav />\n      {main_open}", "</main>\n      <Footer />"))
    body = "\n          ".join(f'<SectionBoundary id="{s}"><{pascal(s)} /></SectionBoundary>' for s in secs)
    app = (f"import './styles/tokens.css'\nimport './styles/base.css'\nimport './styles/animations.css'\nimport './styles/shell.css'\n"
           f"import Nav from './components/Nav'\nimport Footer from './components/Footer'\n"
           f"import SectionBoundary from './components/SectionBoundary'\n{imports}"
           f"import './styles/reduced.css'\n\nexport default function App() {{\n  return (\n    <>\n"
           f"      <a className=\"skip-link\" href=\"#main\">Skip to main content</a>\n      "
           f"{shell_open}\n          {body}\n        {shell_close}\n    </>\n  )\n}}\n")
    restore_static(pf)                                         # keeps SectionBoundary/shell.css present for the imports above
    pf.write("src/App.tsx", app)


def insert(pf, state, sid: str, html: str, css: str) -> None:
    html, css = ce.clean_html(html), ce.clean_css(css)
    if not ce._has_id(html, sid):
        html = f'<div id="{sid}">{html}</div>'
    pf.write(f".agent/parts/{sid}.html", html)
    pf.write(f".agent/parts/{sid}.css", css)
    name = pascal(sid)
    pf.write(f"src/sections/{sid}.css", css)
    pf.write(f"src/sections/{name}.tsx", _component(name, html2jsx.convert(html), f"{sid}.css"))
    _write_app(pf, state)


def get_section(pf, sid: str):
    def rd(ext):
        try:
            return pf.read(f".agent/parts/{sid}.{ext}")
        except FileNotFoundError:
            return ""
    return rd("html").strip(), rd("css")


# ---------------------------------------------------------------------------------------------- build verification
SEC_FILE = re.compile(r"src/sections/([A-Za-z0-9_\-]+)\.(?:tsx|css)")
ERR_LINE = re.compile(r"error|Error|✘|ERROR|Could not resolve|Unexpected|Transform failed")


def sid_from_output(text: str, state) -> str | None:
    """Map a build error line to the section that caused it (works for Hero.tsx and hero-section.css alike)."""
    m = SEC_FILE.search(text)
    if not m:
        return None
    for s in state.plan.get("sections", []):
        if m.group(1) in (pascal(s), s):
            return s
    return None


def build(pf, state) -> dict:
    """Real build. Returns {issues, checks, note}. Missing tools => 'skipped' + an issue (never a fake pass)."""
    checks, issues = [], []

    def chk(name, status, detail=""):
        checks.append({"name": name, "viewport": "build", "status": status, "detail": detail})

    if not shutil.which("node") or not shutil.which("npm"):
        msg = "node/npm not found: React build, type check and browser tests could not run (install Node.js 18+)"
        for n in ("npm install", "type check", "production build"):
            chk(n, "skipped", msg)
        return {"issues": [{"sid": None, "msg": msg}], "checks": checks, "note": msg, "built": False}
    cwd = str(pf.root)
    if not (pf.root / "node_modules" / "vite").is_dir():
        context.progress("build", "npm install (first run can take a few minutes)")
        r = terminal.run(["npm", "install", "--no-audit", "--no-fund", "--prefer-offline"], cwd, timeout=900, max_out=1500)
        if r["code"] != 0:
            msg = f"npm install failed (code {r['code']}): {r['out'][-300:]}"
            chk("npm install", "failed", msg[:200])
            for n in ("type check", "production build"):
                chk(n, "skipped", "npm install failed")
            return {"issues": [{"sid": None, "msg": msg}], "checks": checks, "note": "npm install failed", "built": False}
    chk("npm install", "passed")
    context.progress("build", "tsc --noEmit && vite build")
    r = terminal.run(["npm", "run", "build"], cwd, timeout=300, max_out=6000)
    out = r["out"]
    if r["code"] == 0:
        chk("type check", "passed")
        if (pf.root / "dist" / "index.html").is_file():
            chk("production build", "passed")
            return {"issues": [], "checks": checks, "note": "ok", "built": True}
        chk("production build", "failed", "build exited 0 but dist/index.html is missing")
        return {"issues": [{"sid": None, "msg": "build: dist/index.html missing after a successful build"}], "checks": checks,
                "note": "build produced no output", "built": False}
    errs = [ln.strip() for ln in out.splitlines() if ERR_LINE.search(ln)][:8] or [out[-300:]]
    ts = any("error TS" in ln for ln in errs)
    chk("type check", "failed" if ts else "passed", errs[0][:200] if ts else "")
    chk("production build", "skipped" if ts else "failed", "not executed: type check failed" if ts else errs[0][:200])
    for ln in errs[:6]:
        issues.append({"sid": sid_from_output(ln, state), "msg": f"build: {ln[:220]}"})
    return {"issues": issues, "checks": checks, "note": "build failed", "built": False}

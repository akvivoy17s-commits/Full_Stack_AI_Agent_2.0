"""Playwright inspection against a LOCAL DEV SERVER (http://127.0.0.1:<port>), 3 viewports + a reduced-motion pass.
Checks: page load, console/page errors, failed local requests, horizontal overflow, scroll reveals, broken images,
navigation links, button/disclosure interactions, accessibility audit, reduced-motion behaviour. Captures screenshots.
Every check ends up as passed / failed / skipped in `report` -- a check that did not execute is never reported as passed."""
from backend.agent import context
from backend.tools import a11y, screenshots
from backend.tools.devserver import StaticServer

VIEWPORTS = [("desktop", 1280, 800), ("tablet", 768, 1024), ("mobile", 375, 740)]
CHECKS = ["page loads", "console errors", "failed requests", "horizontal overflow", "scroll reveals", "broken images",
          "navigation links", "interactions", "accessibility"]
SID = "(e) => { const s = e.closest('main > [id]'); return s ? s.id : ''; }"
JS_OVERFLOW = """() => { const w = innerWidth, out = new Set();
  if (document.documentElement.scrollWidth <= w + 1) return [];
  document.querySelectorAll('body *').forEach(el => {
    if (el.closest('.marquee')) return;
    const r = el.getBoundingClientRect();
    if (r.width > 0 && r.right > w + 2) { const s = el.closest('main > [id]'); out.add(s ? s.id : ''); } });
  return [...out]; }"""
JS_HIDDEN = """() => [...document.querySelectorAll('.reveal,.reveal-left,.reveal-scale')]
  .filter(e => !e.classList.contains('in')).map(e => { const s = e.closest('main > [id]'); return s ? s.id : ''; })"""
JS_IMGS = """() => [...document.images].filter(i => i.complete && i.naturalWidth === 0 && i.src && !i.src.startsWith('data:'))
  .map(i => { const s = i.closest('main > [id]'); return s ? s.id : ''; })"""
JS_ANIM = "() => document.getAnimations().filter(a => a.constructor.name === 'CSSAnimation' && a.playState === 'running').length"
JS_VISIBLE_TARGET = "id => { const e = document.getElementById(id); if (!e) return false; const r = e.getBoundingClientRect(); return r.top < innerHeight && r.bottom > 0; }"


def available() -> bool:
    try:
        import playwright.sync_api  # noqa: F401
        return True
    except ImportError:
        return False


def _empty(note: str) -> dict:
    checks = [{"name": c, "viewport": v, "status": "skipped", "detail": note} for v, _, _ in VIEWPORTS for c in CHECKS]
    return {"issues": [], "note": note, "images": {}, "report": {"url": None, "checks": checks, "a11y": [], "notes": [note]}}


def inspect(pf, shots: bool = True, serve_dir=None, want_images: bool = False) -> dict:
    if not available():
        return _empty("playwright not installed (pip install playwright && python -m playwright install chromium): browser checks skipped")
    from playwright.sync_api import sync_playwright
    root = serve_dir or pf.root
    if not (root / "index.html").is_file():
        return _empty(f"{root.name}/index.html not found: nothing to open (build first): browser checks skipped")
    issues, seen, checks, a11y_found, notes, images = [], set(), [], [], [], {}

    def add(sid, msg):
        if (sid, msg) not in seen:
            seen.add((sid, msg))
            issues.append({"sid": sid or None, "msg": msg})

    def rec(name, vp, msgs, detail=""):
        checks.append({"name": name, "viewport": vp, "status": "failed" if msgs else "passed",
                       "detail": "; ".join(msgs[:3]) if msgs else detail})

    try:
        with StaticServer(root) as srv, sync_playwright() as p:
            try:
                b = p.chromium.launch()
            except Exception as e:  # noqa: BLE001
                return _empty(f"Chromium could not start ({str(e).splitlines()[0][:100]}). Run: python -m playwright install chromium")
            try:
                for name, w, h in VIEWPORTS:
                    context.check()
                    _run_viewport(b, srv.url, name, w, h, pf, shots, want_images, add, rec, a11y_found, notes, images)
                context.check()
                _reduced_motion(b, srv.url, add, rec)
            finally:
                b.close()
            report_url = srv.url
    except Exception as e:  # noqa: BLE001  (Cancelled is BaseException and passes through; finally blocks close everything)
        notes.append(f"browser check aborted: {str(e).splitlines()[0][:150]}")
        report_url = None
    done = {(c["name"], c["viewport"]) for c in checks}
    why = notes[-1] if notes else "not executed"
    for vp, _, _ in VIEWPORTS:
        for c in CHECKS:
            if (c, vp) not in done:
                checks.append({"name": c, "viewport": vp, "status": "skipped", "detail": why})
    if ("reduced motion", "desktop") not in done:
        checks.append({"name": "reduced motion", "viewport": "desktop", "status": "skipped", "detail": why})
    if shots:
        screenshots.prune(pf)
    return {"issues": issues, "note": "ok" if not notes else notes[-1], "images": images,
            "report": {"url": report_url and "local dev server (127.0.0.1)", "checks": checks, "a11y": a11y_found, "notes": notes}}


def _run_viewport(b, url, name, w, h, pf, shots, want_images, add, rec, a11y_found, notes, images):
    page = b.new_page(viewport={"width": w, "height": h})
    cons, net = [], []
    try:
        page.on("pageerror", lambda e: cons.append(f"js error: {str(e)[:140]}"))
        page.on("console", lambda m: m.type == "error" and not m.text.startswith("Failed to load resource") and cons.append(f"console: {m.text[:140]}"))
        page.on("requestfailed", lambda r: r.url.startswith(url) and net.append(f"failed: {r.url[len(url):][:80]}"))
        page.on("response", lambda r: r.url.startswith(url) and r.status >= 400 and not r.url.endswith("favicon.ico")
                and net.append(f"HTTP {r.status}: {r.url[len(url):][:80]}"))
        resp = page.goto(url, wait_until="load", timeout=20000)
        ok = bool(resp and resp.ok)
        rec("page loads", name, [] if ok else [f"HTTP {resp.status if resp else '??'}"])
        if not ok:
            add(None, f"[{name}] page did not load")
            return
        total = page.evaluate("document.documentElement.scrollHeight")
        for y in range(0, total, 400):                          # trigger scroll reveals
            page.evaluate(f"scrollTo(0,{y})")
            page.wait_for_timeout(90)
        page.wait_for_timeout(800)
        for sid in page.evaluate(JS_OVERFLOW):
            add(sid, f"[{name}] horizontal overflow")
        rec("horizontal overflow", name, [f"section '{s}'" for s in page.evaluate(JS_OVERFLOW)])
        hidden = sorted(set(page.evaluate(JS_HIDDEN)))
        for sid in hidden:
            add(sid, f"[{name}] reveal elements never became visible")
        rec("scroll reveals", name, [f"section '{s}'" for s in hidden])
        imgs = sorted(set(page.evaluate(JS_IMGS)))
        for sid in imgs:
            add(sid, f"[{name}] broken image")
        rec("broken images", name, [f"section '{s}'" for s in imgs])
        _interact(page, url, name, add, rec)
        found = a11y.audit(page)
        for f in found:
            add(f["sid"], f"[a11y:{f['rule']}] {f['msg']}")
            if not any(x["msg"] == f["msg"] and x["sid"] == f["sid"] for x in a11y_found):
                a11y_found.append(f)
        rec("accessibility", name, [f["msg"] for f in found], "subset of WCAG rules, see report.a11y")
        page.evaluate("scrollTo(0,0)")
        if want_images:
            images[name] = page.screenshot(type="jpeg", quality=55)       # viewport only: small, cheap for a vision model
        if shots:
            screenshots.take(page, pf, name)
    except Exception as e:  # noqa: BLE001
        notes.append(f"[{name}] check error: {str(e).splitlines()[0][:120]}")
    finally:
        for m in dict.fromkeys(cons):
            add(None, f"[{name}] {m}")
        for m in dict.fromkeys(net):
            add(None, f"[{name}] {m}")
        rec("console errors", name, list(dict.fromkeys(cons)))
        rec("failed requests", name, list(dict.fromkeys(net)))
        page.close()


def _interact(page, url, name, add, rec):
    nav, tested, btns, details = [], 0, 0, 0
    links = page.locator('a[href^="#"]')
    for i in range(min(links.count(), 14)):
        a = links.nth(i)
        href = a.get_attribute("href") or ""
        sid = a.evaluate(SID)
        if href in ("#", ""):
            nav.append(f"placeholder link href=\"{href}\"")
            add(sid, f"[{name}] placeholder link href=\"{href}\" goes nowhere")
            continue
        if not page.evaluate("id => !!document.getElementById(id)", href[1:]):
            nav.append(f"{href} has no target")
            add(sid, f"[{name}] link {href} points to a missing id")
            continue
        if tested >= 4 or not a.is_visible():
            continue
        try:
            page.evaluate("scrollTo(0,0)")
            a.click(timeout=2000)
            page.wait_for_timeout(750)
            tested += 1
            if not page.evaluate(JS_VISIBLE_TARGET, href[1:]):
                nav.append(f"{href} did not scroll into view")
                add(sid, f"[{name}] link {href} did not scroll its target into view")
        except Exception:  # noqa: BLE001  (e.g. covered by another element): reported as detail, not as a defect
            nav.append(f"{href} not clickable (not counted as defect)")
    rec("navigation links", name, [m for m in nav if "not counted" not in m], f"{tested} link(s) clicked")
    for i in range(min(page.locator("button:visible").count(), 5)):
        bt = page.locator("button:visible").nth(i)
        if bt.evaluate("e => !!e.closest('form') || e.type === 'submit'"):
            continue
        try:
            bt.click(timeout=1500)
            btns += 1
            if not page.url.startswith(url):
                page.goto(url)
        except Exception:  # noqa: BLE001
            pass
    for i in range(min(page.locator("summary:visible").count(), 2)):
        s = page.locator("summary:visible").nth(i)
        try:
            before = s.evaluate("e => e.parentElement.open")
            s.click(timeout=1500)
            if s.evaluate("e => e.parentElement.open") == before:
                add(s.evaluate(SID), f"[{name}] <details> does not toggle")
            details += 1
        except Exception:  # noqa: BLE001
            pass
    forms = page.locator("form").count()
    rec("interactions", name, [], f"{btns} button(s), {details} disclosure(s) exercised; {forms} form(s) found, not submitted")


def _reduced_motion(b, url, add, rec):
    ctx = b.new_context(viewport={"width": 1280, "height": 800}, reduced_motion="reduce")
    page = ctx.new_page()
    msgs = []
    try:
        page.goto(url, wait_until="load", timeout=20000)
        page.wait_for_timeout(400)
        hid = sorted(set(page.evaluate(JS_HIDDEN)))
        for sid in hid:
            msgs.append(f"section '{sid}' stays hidden")
            add(sid, "[reduced-motion] reveal elements stay hidden")
        n = page.evaluate(JS_ANIM)
        if n:
            msgs.append(f"{n} CSS animation(s) still running")
            add(None, f"[reduced-motion] {n} CSS animation(s) still running with prefers-reduced-motion")
    finally:
        ctx.close()
    rec("reduced motion", "desktop", msgs, "reveals visible, animations stopped")

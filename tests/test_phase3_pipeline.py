"""Phase 3: command allowlist, HTML->JSX, layouts, React/Vite output, repair tracking, vision honesty, browser report honesty.
Browser tests use a FAKE Playwright (they verify orchestration/reporting code, NOT real Chromium behaviour).
Set RUN_REACT_BUILD=1 to also run a real `npm install` + `vite build` test."""
import os
import shutil
import types

import pytest

os.environ["MOCK_LLM"] = "1"
os.environ["USE_BROWSER"] = "0"
from fastapi.testclient import TestClient

from backend.agent import llm, orchestrator
from backend.agent.state import AgentState
from backend.engines import html2jsx, react_engine
from backend.main import app
from backend.memory import project_store
from backend.storage import db
from backend.tools import a11y, browser, terminal, vision
from backend.tools.devserver import StaticServer
from backend.tools.project_files import ProjectFiles

client = TestClient(app)
db.init()


def _setup(pid, brief="landing page for a fitness app", stack="html"):
    project_store.save(AgentState(pid, brief, stack=stack))
    db.upsert_project(pid, brief)
    orchestrator.run(pid, force=True)
    return ProjectFiles(pid)


# ---------------------------------------------------------------- command allowlist
@pytest.mark.parametrize("cmd", [["rm", "-rf", "/"], ["npm", "exec", "x"], ["npm", "install", "left-pad"], ["npm", "run", "evil"],
                                 ["npx", "rimraf", "."], ["node", "-e", "1"], ["node", "--check", "../x.js"], ["python", "-c", "1"], []])
def test_terminal_rejects_everything_off_allowlist(cmd):
    with pytest.raises(ValueError):
        terminal.run(cmd, ".")


def test_terminal_allows_only_exact_shapes():
    assert terminal.allowed(["npm", "install", "--no-audit", "--no-fund"]) and terminal.allowed(["npm", "run", "build"])
    assert terminal.allowed(["npx", "tsc", "--noEmit"]) and terminal.allowed(["node", "--check", "js/motion.js"])


# ---------------------------------------------------------------- HTML -> JSX
def test_html2jsx_attributes_svg_style_text():
    j = html2jsx.convert('<div class="a" style="--d:2;margin-top:8px" tabindex="0"><svg viewBox="0 0 2 2" stroke-width="2"><linearGradient id="g"/></svg>'
                         '<label for="x">A &amp; {b}</label><input value="v" required><br><img src="a.png" alt=""></div>')
    assert 'className="a"' in j and "as React.CSSProperties" in j and '"marginTop": "8px"' in j and "tabIndex={0}" in j
    assert "viewBox" in j and 'strokeWidth="2"' in j and "<linearGradient" in j and 'htmlFor="x"' in j
    assert "{'{'}" in j and "{'}'}" in j and "defaultValue" in j and "<br />" in j and "<img" in j and "/>" in j


def test_html2jsx_normalizes_already_camelcased_react_attributes():
    # HTMLParser lowercases attribute names, including className/htmlFor emitted by an LLM.
    j = html2jsx.convert('<main className="register"><h1 className="title">Create account</h1>'
                         '<label htmlFor="email">Email</label><input id="email" /></main>')
    assert 'className="register"' in j
    assert 'className="title"' in j
    assert 'htmlFor="email"' in j
    assert 'classname=' not in j and 'htmlfor=' not in j


def test_html2jsx_closes_unbalanced_markup_and_drops_comments_handlers():
    j = html2jsx.convert('<div><!-- c --><p onclick="x()">hi</div>')
    assert j == "<div><p>hi</p></div>"


# ---------------------------------------------------------------- layouts / templates
def test_layout_detection_and_sections():
    from backend.agent import planner
    assert planner.layout_for("x\n\nDesign style: Analytics dashboard. Animation intensity: balanced.") == "dashboard"
    assert planner.layout_for("Design style: Interactive portfolio. Animation") == "portfolio"
    assert planner.layout_for("Design style: Premium SaaS. a dashboard widget") == "landing"
    assert planner._ids(["hero", "kpis", "nope"], "dashboard") == ["overview", "kpis", "charts", "table"]      # invalid -> fallback


@pytest.mark.parametrize("brief,marker", [("Design style: Analytics dashboard. sales stats", 'class="shell"'),
                                          ("Design style: Interactive portfolio. my work", "<header")])
def test_html_layouts_scaffold(brief, marker):
    pf = _setup("t-lay-" + marker[:3].strip('<"= ') + str(len(brief)), brief)
    assert marker in pf.read("index.html")
    assert pf.read("css/base.css").count(".sr-only") >= 1 and "focus-visible" in pf.read("css/base.css")


# ---------------------------------------------------------------- React + Vite output
def test_react_scaffold_and_section_files(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda _n: None)               # no node/npm here: scaffold + honest report only
    pf = _setup("t-react-a", stack="react")
    names = set(pf.tree())
    assert {"package.json", "vite.config.ts", "tsconfig.json", "src/main.tsx", "src/App.tsx", "src/lib/motion.ts", "src/sections/Hero.tsx"} <= names
    assert "export default function Hero" in pf.read("src/sections/Hero.tsx") and "<Hero />" in pf.read("src/App.tsx")
    r = orchestrator.verify("t-react-a", do_repair=False, with_browser=False)
    statuses = {c["name"]: c["status"] for c in r["report"]["checks"]}
    assert statuses["production build"] == "skipped" and r["phase"] == "verify"        # never "done" without a real build
    assert any("node/npm not found" in i for i in r["issues"])


def test_react_edit_and_get_section_roundtrip(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda _n: None)
    pf = _setup("t-react-b", stack="react")
    html, css = react_engine.get_section(pf, "hero")
    assert 'id="hero"' in html and css
    react_engine.insert(pf, project_store.load("t-react-b"), "hero", html.replace("Hero", "Hello"), css)
    assert "Hello" in pf.read("src/sections/Hero.tsx")


def test_react_build_error_maps_to_section():
    st = AgentState("x", "b")
    st.plan = {"sections": ["hero", "features"]}
    assert react_engine.sid_from_output("src/sections/Features.tsx(6,127): error TS1005", st) == "features"
    assert react_engine.sid_from_output("vite.config.ts: error", st) is None


@pytest.mark.skipif(os.getenv("RUN_REACT_BUILD") != "1" or not shutil.which("npm"), reason="slow: needs npm + network (RUN_REACT_BUILD=1)")
def test_react_real_build():
    pf = _setup("t-react-real", stack="react")
    r = orchestrator.verify("t-react-real", do_repair=False, with_browser=False)
    assert r["issues"] == [] and (pf.root / "dist" / "index.html").is_file()


def test_framework_in_api_and_preview_of_unbuilt_react():
    pid = client.post("/projects", json={"brief": "react site please", "framework": "react"}).json()["project_id"]
    assert project_store.load(pid).stack == "react"
    assert client.post("/projects", json={"brief": "react site please", "framework": "vue"}).status_code == 422
    assert client.get(f"/preview/{pid}/index.html").status_code == 404                  # not built yet
    assert client.get(f"/preview/{pid}/../x").status_code in (404, 422)


# ---------------------------------------------------------------- repair tracking
def test_same_issue_is_never_repaired_more_than_twice():
    pf = _setup("t-rep-a")
    broken = '<section id="hero" class="sec"><div><h2>x</h2></section>'
    pf.write("index.html", pf.read("index.html").replace('<h2 class="reveal">Hero</h2>', "<div><h2>x</h2>"))
    orig, calls = llm.call_json, []

    def fake(kind, system, user, model=None, max_tokens=None, **kw):
        calls.append(kind)
        if kind == "repair":                                    # patch applies cleanly but does not fix anything
            return {"patches": [{"t": "html", "old": "<h2>x</h2>", "new": "<h2>x</h2>"}]}, {"in": 1, "out": 1}
        if kind == "section":                                   # regeneration is broken too
            return {"html": broken, "css": "#hero{padding:1px}"}, {"in": 1, "out": 1}
        return orig(kind, system, user, model, max_tokens, **kw)
    llm.call_json = fake
    try:
        client.put("/settings", json={"max_repair_loops": 3})
        r = orchestrator.verify("t-rep-a")
    finally:
        llm.call_json = orig
    log = [e for e in r["repair_log"] if e["sid"] == "hero"]
    assert list(dict.fromkeys(e["method"] for e in log)) == ["patch"]
    assert log and log[-1]["outcome"] == "no_progress_same_source"
    assert calls.count("repair") == 1 and r["issues"]  # Stop after one proven no-op instead of repeating it.
    assert {x["attempt"] for x in db.list_repair_attempts("t-rep-a") if x["sid"] == "hero"} == {1}
    assert client.get("/projects/t-rep-a/repairs").json()[0]["outcome"] == "no_progress_same_source"


def test_successful_repair_is_recorded_as_fixed():
    pf = _setup("t-rep-b")
    pf.write("index.html", pf.read("index.html").replace('<h2 class="reveal">Hero</h2>', "<div><h2 class=\"reveal\">Hero</h2>"))
    orig = llm.call_json

    def fake(kind, system, user, model=None, max_tokens=None, **kw):
        if kind == "repair":
            return {"patches": [{"t": "html", "old": '<div><h2 class="reveal">Hero</h2>', "new": '<h2 class="reveal">Hero</h2>'}]}, {"in": 1, "out": 1}
        return orig(kind, system, user, model, max_tokens, **kw)
    llm.call_json = fake
    try:
        r = orchestrator.verify("t-rep-b")
    finally:
        llm.call_json = orig
    assert r["issues"] == [] and {e["outcome"] for e in r["repair_log"]} == {"fixed"} and r["phase"] == "done"


# ---------------------------------------------------------------- vision is optional and honest
def test_vision_skipped_without_model_and_text_model_never_gets_images():
    db.save_settings({"vision_model": ""})
    v = vision.analyze({"desktop": b"x"}, ["hero"])
    assert v["status"] == "skipped" and "no vision model" in v["note"]


def test_vision_findings_are_warnings_not_issues():
    db.save_settings({"vision_model": "llava:7b"})
    seen = {}
    orig = llm.call_json

    def fake(kind, system, user, model=None, max_tokens=None, **kw):
        if kind == "vision":
            seen["model"], seen["images"] = model, kw.get("images")
            return {"issues": [{"sid": "hero", "msg": "headline overlaps image"}, {"sid": "bogus", "msg": "x"}]}, {"in": 1, "out": 1}
        return orig(kind, system, user, model, max_tokens, **kw)
    llm.call_json = fake
    try:
        v = vision.analyze({"desktop": b"\xff\xd8"}, ["hero", "cta"])
    finally:
        llm.call_json = orig
        db.save_settings({"vision_model": ""})
    assert seen["model"] == "llava:7b" and seen["images"] and v["status"] == "ok"
    assert v["findings"][0]["sid"] == "hero" and v["findings"][1]["sid"] == ""            # unknown section ids are dropped


# ---------------------------------------------------------------- browser: honest reports (fake Playwright)
class _Loc:
    def __init__(self, sel): self.sel = sel
    def count(self): return 2 if self.sel.startswith("a[href") else 0
    def nth(self, i): return self
    def get_attribute(self, _n): return "#hero" if self.sel.startswith("a[href") else None
    def evaluate(self, *_a): return "hero"
    def is_visible(self): return True
    def click(self, **_k): pass


class _Page:
    url = "http://127.0.0.1/"
    def on(self, *_a): pass
    def goto(self, *_a, **_k): return types.SimpleNamespace(ok=True, status=200)
    def evaluate(self, js, arg=None):
        if js == a11y.A11Y_JS:
            return [{"rule": "img-alt", "sid": "hero", "msg": "image without alt text"}]
        if "scrollHeight" in js:
            return 800
        if "getElementById" in js:
            return True
        if "CSSAnimation" in js:
            return 0
        return None if js.startswith("scrollTo") else []
    def wait_for_timeout(self, *_a): pass
    def locator(self, sel): return _Loc(sel)
    def screenshot(self, path=None, **_k):
        if path:
            open(path, "wb").write(b"png")
        return b"jpg"
    def close(self): pass


class _Browser:
    def new_page(self, **_k): return _Page()
    def new_context(self, **_k): return types.SimpleNamespace(new_page=lambda: _Page(), close=lambda: None)
    def close(self): pass


def _fake_pw(monkeypatch, launch_error=None):
    def launch():
        if launch_error:
            raise RuntimeError(launch_error)
        return _Browser()
    pw = types.SimpleNamespace(chromium=types.SimpleNamespace(launch=launch))

    class CM:
        def __enter__(self): return pw
        def __exit__(self, *a): return None
    monkeypatch.setattr("playwright.sync_api.sync_playwright", lambda: CM())


def test_browser_report_marks_every_check_and_a11y_issue(monkeypatch):
    _fake_pw(monkeypatch)
    pf = _setup("t-br-a")
    r = browser.inspect(pf, want_images=True)
    names = {(c["name"], c["viewport"]) for c in r["report"]["checks"]}
    assert {(n, v) for n in browser.CHECKS for v in ("desktop", "tablet", "mobile")} <= names and ("reduced motion", "desktop") in names
    assert {c["status"] for c in r["report"]["checks"] if c["name"] == "accessibility"} == {"failed"}
    assert any(i["sid"] == "hero" and "[a11y:img-alt]" in i["msg"] for i in r["issues"]) and r["images"].keys() == {"desktop", "tablet", "mobile"}
    assert len([s for s in pf.tree() if s.endswith(".png")]) == 0 and len(list((pf.root / ".agent" / "shots").glob("*.png"))) == 3


def test_browser_never_reports_pass_when_chromium_cannot_start(monkeypatch):
    _fake_pw(monkeypatch, launch_error="Executable doesn't exist at /x\nrun playwright install")
    r = browser.inspect(_setup("t-br-b"))
    assert r["issues"] == [] and "playwright install chromium" in r["note"]
    assert r["report"]["checks"] and all(c["status"] == "skipped" for c in r["report"]["checks"])


def test_dev_server_serves_dir_but_never_agent_state(tmp_path):
    import httpx
    (tmp_path / "index.html").write_text("hi")
    (tmp_path / ".agent").mkdir()
    (tmp_path / ".agent" / "state.json").write_text("secret")
    with StaticServer(tmp_path) as s:
        assert httpx.get(s.url).text == "hi" and httpx.get(s.url + ".agent/state.json").status_code == 404
    with pytest.raises(Exception):
        httpx.get(s.url, timeout=1)                                                         # server really stopped


def test_test_task_kind_runs_checks_without_repairs():
    pid = client.post("/projects", json={"brief": "landing for tests"}).json()["project_id"]
    import time
    def wait(tid):
        for _ in range(200):
            t = client.get(f"/tasks/{tid}").json()
            if t["status"] in db.TERMINAL:
                return t
            time.sleep(0.1)
    wait(client.post(f"/projects/{pid}/tasks", json={"kind": "generate"}).json()["id"])
    t = wait(client.post(f"/projects/{pid}/tasks", json={"kind": "test"}).json()["id"])
    assert t["status"] in ("succeeded", "completed_with_issues") and t["result"]["repairs"] == 0
    rep = client.get(f"/projects/{pid}/report").json()
    assert {"checks", "a11y", "vision", "repairs", "counts"} <= rep.keys()
    assert client.get("/projects/nope/report").status_code == 404

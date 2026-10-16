import os
import shutil
os.environ["MOCK_LLM"] = "1"
os.environ["USE_BROWSER"] = "0"
from backend.agent import llm, orchestrator
from backend.agent.state import AgentState
from backend.memory import project_store
from backend.tools import browser, terminal
from backend.tools.project_files import ProjectFiles

BROKEN = '<div><h2 class="reveal">Hero</h2>'
GOOD = '<h2 class="reveal">Hero</h2>'


def _setup(pid):
    project_store.save(AgentState(pid, "fitness app landing page"))
    orchestrator.run(pid, force=True)
    return ProjectFiles(pid)


def _with_fake(fake, fn):
    orig = llm.call_json
    llm.call_json = fake
    try:
        return fn()
    finally:
        llm.call_json = orig


def test_repair_patch():
    pf = _setup("t-p3a")
    pf.write("index.html", pf.read("index.html").replace(GOOD, BROKEN))
    assert orchestrator.verify("t-p3a", do_repair=False)["issues"]
    orig = llm.call_json

    def fake(kind, system, user, model=None, max_tokens=None, **kw):
        if kind == "repair":
            return {"patches": [{"t": "html", "old": BROKEN, "new": GOOD}]}, {"in": 10, "out": 5}
        return orig(kind, system, user, model, max_tokens, **kw)
    r = _with_fake(fake, lambda: orchestrator.verify("t-p3a"))
    assert r["issues"] == [] and r["repairs"] == 1 and r["phase"] == "done" and r["usage"]["in"] >= 10


def test_repair_fallback_regen():
    pf = _setup("t-p3b")
    pf.write("index.html", pf.read("index.html").replace(GOOD, BROKEN))
    orig = llm.call_json

    def fake(kind, system, user, model=None, max_tokens=None, **kw):
        if kind == "repair":
            return {"patches": [{"t": "html", "old": "does-not-exist", "new": ""}]}, {"in": 0, "out": 0}
        return orig(kind, system, user, model, max_tokens, **kw)
    r = _with_fake(fake, lambda: orchestrator.verify("t-p3b"))
    assert r["issues"] == [] and r["repairs"] == 1


def test_edit_section():
    _setup("t-p3c")
    orig = llm.call_json

    def fake(kind, system, user, model=None, max_tokens=None, **kw):
        if kind == "repair":
            return {"patches": [{"t": "html", "old": GOOD, "new": '<h2 class="reveal">Hero!!</h2>'}]}, {"in": 7, "out": 3}
        return orig(kind, system, user, model, max_tokens, **kw)
    r = _with_fake(fake, lambda: orchestrator.edit("t-p3c", "hero", "make title louder"))
    assert "Hero!!" in ProjectFiles("t-p3c").read("index.html") and r["issues"] == []


def test_js_syntax_and_tools():
    pf = _setup("t-p3d")
    pf.write("js/broken.js", "function(){")
    if shutil.which("node"):
        assert any("broken.js" in i for i in orchestrator.verify("t-p3d", do_repair=False)["issues"])
    try:
        terminal.run(["rm", "-rf", "/"], ".")
        assert False
    except ValueError:
        pass
    res = browser.inspect(pf, shots=False)           # works with or without playwright
    assert isinstance(res["issues"], list) and "note" in res


def teardown_module(_m=None):
    for s in "abcd":
        shutil.rmtree(ProjectFiles.__init__.__globals__["GENERATED_DIR"] / f"t-p3{s}", ignore_errors=True)

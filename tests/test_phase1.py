from backend.tools.project_files import ProjectFiles
from backend.tools.validators import validate_file
from backend.agent.state import AgentState
from backend.memory import project_store, history


def test_files_and_ops():
    pf = ProjectFiles("t-phase1")
    pf.write("index.html", "<html><head><meta name=\"viewport\"></head><body><p>a</p></body></html>")
    errs = pf.apply_ops([{"op": "patch", "path": "index.html", "old": "<p>a</p>", "new": "<p>b</p>"},
                         {"op": "patch", "path": "index.html", "old": "nope", "new": "x"}])
    assert len(errs) == 1 and "<p>b</p>" in pf.read("index.html")
    try:
        pf.write("../evil.txt", "x"); assert False
    except ValueError:
        pass


def test_validators():
    assert validate_file("a.css", "a{transition:1s}")
    assert not validate_file("a.css", "a{transition:1s} @media (prefers-reduced-motion){a{transition:none}}")
    assert validate_file("a.html", "<div><p></div>")


def test_state_history():
    s = AgentState("t-phase1", "landing page for a fitness app")
    project_store.save(s)
    assert project_store.load("t-phase1").brief.startswith("landing")
    for i in range(20):
        history.add("t-phase1", "u", f"msg {i}")
    assert len(history.context("t-phase1")) <= 3000

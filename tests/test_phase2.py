import os
os.environ["MOCK_LLM"] = "1"
os.environ["USE_BROWSER"] = "0"
from backend.agent.state import AgentState
from backend.agent import orchestrator
from backend.memory import project_store
from backend.tools.project_files import ProjectFiles


def test_pipeline_mock():
    pid = "t-phase2"
    project_store.save(AgentState(pid, "landing page for a fitness tracking app"))
    r = orchestrator.run(pid, force=True)
    pf = ProjectFiles(pid)
    html = pf.read("index.html")
    assert r["sections_done"] == ["hero", "features", "showcase", "pricing", "cta"]
    assert r["issues"] == [], r["issues"]
    assert "<script>alert" not in html and "onclick" not in html      # sanitized
    assert 'id="hero"' in html and "Mock content" in html
    assert "#pricing{padding:96px 0}" in pf.read("css/sections.css")
    assert "--primary:#7c5cff" in pf.read("css/tokens.css")
    assert project_store.load(pid).phase == "done"
    # resume: second run makes no new section work
    r2 = orchestrator.run(pid)
    assert r2["sections_done"] == r["sections_done"]

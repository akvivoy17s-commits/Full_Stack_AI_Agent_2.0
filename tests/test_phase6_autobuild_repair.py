"""Phase 6: repair window keeps long generated error lines; missing scaffold files are restored with zero tokens."""
import uuid
from backend.agent import selfrepair as sr
from backend.engines import react_engine
from backend.tools.project_files import ProjectFiles


def test_window_always_contains_error_line_with_long_lines():
    long = "x" * 1500
    text = "\n".join([long] * 10 + ["ERRORLINE foo(bar)"] + [long] * 10)
    w = sr._window(text, 11)
    assert "ERRORLINE foo(bar)" in w and len(w) <= 2400


def test_window_short_file_is_30_lines_around_error():
    w = sr._window("\n".join(f"l{i}" for i in range(100)), 50)
    assert "l50" in w and "l35" in w and "l63" in w and "l64" not in w


def test_restore_static_rewrites_only_missing_files():
    pf = ProjectFiles("p6r-" + uuid.uuid4().hex[:6])
    pf.write("package.json", "{}")
    assert len(react_engine.restore_static(pf)) == len(react_engine.STATIC)
    pf.write("src/lib/MotionEffects.tsx", "// custom")
    assert react_engine.restore_static(pf) == [] and pf.read("src/lib/MotionEffects.tsx") == "// custom"


def test_rollback_does_not_recheck_project():
    pf = ProjectFiles("p6r-" + uuid.uuid4().hex[:6])
    pf.write("a.py", "x = 1\n")
    calls = []

    def check(p):                                   # any edit makes things worse: 2 issues instead of 1
        calls.append(1)
        return [sr._issue("a.py", "e1"), sr._issue("a.py", "e2")] if p.read("a.py") != "x = 1\n" else [sr._issue("a.py", "e1")]
    r = sr.repair_files(pf, call=lambda u: ({"patches": [{"old": "x = 1", "new": "x = 2"}]}, {"in": 5, "out": 5}), check=check,
                        issues=[sr._issue("a.py", "e1")], max_rounds=1)
    assert pf.read("a.py") == "x = 1\n" and any(e["outcome"] == "rolled_back" for e in r["log"])
    assert len(calls) == 1                           # one check after the patch, none after the rollback

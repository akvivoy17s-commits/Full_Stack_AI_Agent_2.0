import json
import uuid

from backend.agent import selfrepair as sr
from backend.tools.project_files import ProjectFiles

OK = {"in": 10, "out": 10}


def _pf():
    return ProjectFiles("p6-" + uuid.uuid4().hex[:8])


def _fix(old, new):
    return lambda user: ({"patches": [{"old": old, "new": new}]}, OK)


def test_fixes_python_syntax_error():
    pf = _pf()
    pf.write("app/main.py", "def f(:\n    return 1\n")
    r = sr.repair_files(pf, call=_fix("def f(:", "def f():"))
    assert r["status"] == "PASS" and r["fixed"] == 1 and sr.static_issues(pf) == []


def test_fixes_invalid_json():
    pf = _pf()
    pf.write("cfg.json", '{"a": 1,}')
    r = sr.repair_files(pf, call=_fix('{"a": 1,}', '{"a": 1}'))
    assert r["status"] == "PASS" and json.loads(pf.read("cfg.json")) == {"a": 1}


def test_protected_files_never_edited():
    pf = _pf()
    pf.write("tests/test_x.py", "def t(:\n")
    pf.write(".env.example", "x")
    calls = []
    r = sr.repair_files(pf, call=lambda u: calls.append(u) or ({"patches": []}, OK))
    assert calls == [] and r["status"] == "BLOCKED" and r["blocked"]
    assert pf.read("tests/test_x.py") == "def t(:\n"


def test_suppression_patch_rejected():
    pf = _pf()
    pf.write("a.py", "x = (\n")
    r = sr.repair_files(pf, call=_fix("x = (\n", "x = 1  # noqa\n"))
    assert r["status"] == "FAIL" and pf.read("a.py") == "x = (\n"


def test_bounded_attempts_same_issue():
    pf = _pf()
    pf.write("a.py", "x = (\n")
    n = []
    r = sr.repair_files(pf, call=lambda u: n.append(1) or ({"patches": [{"old": "nope", "new": "x"}]}, OK), max_rounds=10)
    assert len(n) <= sr.MAX_TRIES and r["status"] == "FAIL"


def test_worse_patch_rolled_back():
    pf = _pf()
    pf.write("a.py", "x = (\n")
    pf.write("b.json", "{}")
    r = sr.repair_files(pf, call=_fix("{}", "{,"), issues=[sr._issue("a.py", "SyntaxError", 1), sr._issue("b.json", "bad", 1)],
                        check=lambda p: sr.static_issues(p) + ([] if p.read("b.json") == "{}" else [sr._issue("c.py", "x")]))
    assert pf.read("b.json") == "{}" and any(e["outcome"] == "rolled_back" for e in r["log"])


def test_token_budget_stops():
    pf = _pf()
    pf.write("a.py", "x = (\n")
    r = sr.repair_files(pf, call=lambda u: ({"patches": [{"old": "x = (", "new": "x = (1"}]}, {"in": 9000, "out": 9000}), token_budget=100)
    assert r["attempts"] == 1 and r["stop"] and r["status"] == "FAIL"


def test_ambiguous_patch_rejected():
    pf = _pf()
    pf.write("a.py", "y = 1\ny = 1\nx = (\n")
    r = sr.repair_files(pf, call=_fix("y = 1", "y = 2"))
    assert r["status"] == "FAIL" and pf.read("a.py").count("y = 1") == 2


def test_clean_project_is_pass_without_llm_calls():
    pf = _pf()
    pf.write("a.py", "x = 1\n")
    r = sr.repair_files(pf, call=lambda u: 1 / 0)
    assert r["status"] == "PASS" and r["attempts"] == 0


def test_fixes_js_syntax_error_via_node():
    import shutil
    if not shutil.which("node"):
        return
    pf = _pf()
    pf.write("src/a.js", "function f( { return 1 }\n")
    r = sr.repair_files(pf, call=_fix("function f( {", "function f() {"))
    assert r["status"] == "PASS"

from types import SimpleNamespace

import pytest

from backend.agent import selfrepair
from backend.engines import react_engine, repair_engine
from backend.tools import debugger
from backend.tools.project_files import ProjectFiles
import backend.tools.project_files as project_files


@pytest.fixture
def pf(tmp_path, monkeypatch):
    monkeypatch.setattr(project_files, "GENERATED_DIR", tmp_path)
    return ProjectFiles("debugger-test")


def _check_from_file(pf):
    text = pf.read("src/broken.py")
    if "BAD" in text:
        return [{"file": "src/broken.py", "msg": "src/broken.py: invalid token BAD"}]
    if "EVIL" in text:
        return [{"file": "src/broken.py", "msg": "src/broken.py: new compiler error EVIL"}]
    return []


def _patch(_user):
    return {"patches": [{"old": "BAD", "new": "fixed()"}]}, {"in": 1, "out": 1}


def test_file_repair_accepts_patch_only_when_diagnostics_disappear(pf, monkeypatch):
    pf.write("src/broken.py", "BAD\n")
    monkeypatch.setattr(selfrepair.db, "add_repair_attempt", lambda *args, **kwargs: None)
    result = selfrepair.repair_files(pf, issues=_check_from_file(pf), check=_check_from_file, call=_patch, max_rounds=1)
    assert pf.read("src/broken.py") == "fixed()\n"
    assert result["fixed"] >= 1
    assert result["status"] == "PASS"


def test_file_repair_rolls_back_patch_that_replaces_one_error_with_another(pf, monkeypatch):
    pf.write("src/broken.py", "BAD\n")
    def bad_patch(_user):
        return {"patches": [{"old": "BAD", "new": "EVIL"}]}, {"in": 1, "out": 1}
    monkeypatch.setattr(selfrepair.db, "add_repair_attempt", lambda *args, **kwargs: None)
    result = selfrepair.repair_files(pf, issues=_check_from_file(pf), check=_check_from_file, call=bad_patch, max_rounds=1)
    assert pf.read("src/broken.py") == "BAD\n"
    assert result["status"] == "FAIL"
    assert result["log"][0]["outcome"] == "rolled_back"
    assert result["log"][0]["reason"] == "regression"


def test_file_repair_rolls_back_patch_when_diagnostics_do_not_improve(pf, monkeypatch):
    pf.write("src/broken.py", "BAD\n")
    never_fixed = lambda _pf: [{"file": "src/broken.py", "msg": "same persistent diagnostic"}]
    monkeypatch.setattr(selfrepair.db, "add_repair_attempt", lambda *args, **kwargs: None)
    result = selfrepair.repair_files(pf, issues=never_fixed(pf), check=never_fixed, call=_patch, max_rounds=1)
    assert pf.read("src/broken.py") == "BAD\n"
    assert result["log"][0]["outcome"] == "rolled_back"
    assert result["log"][0]["reason"] == "no_progress"


def test_section_repair_preflight_rejects_unbalanced_html_and_css():
    issues = repair_engine._section_source_errors("<section><div></section>", ".card { color: red;")
    assert issues
    assert any("div" in issue or "delimiter" in issue for issue in issues)


def test_reconcile_rebuilds_bad_generated_kpis_from_canonical_source(pf):
    state = SimpleNamespace(
        plan={"sections": ["kpis"], "layout": "dashboard", "brand": "Example Store"},
        stack_config={"stack": {"frontend": "react", "backend": "express"}},
        design={}, motion={},
    )
    pf.write(".agent/parts/kpis.html", (
        '<section><HeroBanner /><ProductCardList items={featuredProducts} />'
        '<CategoryList items={categories} /><productcardlist /></section>'
    ))
    pf.write(".agent/parts/kpis.css", ".kpis { display: grid; }")
    changed = react_engine.reconcile_derived_outputs(pf, state)
    generated = pf.read("src/sections/Kpis.tsx")
    canonical = pf.read(".agent/parts/kpis.html")
    assert changed
    assert "HeroBanner" not in generated
    assert "ProductCardList" not in generated
    assert "featuredProducts" not in generated
    assert "CategoryList" not in generated
    assert "productcardlist" not in generated
    assert "safe-kpi-grid" in canonical


def test_patch_guard_rejects_suppression_markers():
    ok, reason = debugger.validate_patch_text("before", "// @ts-ignore\nafter")
    assert not ok
    assert reason == "patch_attempts_to_suppress_checks"

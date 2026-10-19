from backend.agent import selfrepair
from backend.tools.project_files import ProjectFiles


def test_new_test_failure_rolls_back_a_diagnostic_improving_patch():
    import uuid

    pf = ProjectFiles("reverify-" + uuid.uuid4().hex[:8])
    pf.write("src/app.py", "value = 1\n")
    verifier_calls = {"count": 0}

    def verifier(_pf):
        verifier_calls["count"] += 1
        if verifier_calls["count"] == 1:
            return set(), True
        return {"backend Python tests"}, True

    def check(project):
        return [] if project.read("src/app.py") == "value = 2\n" else [selfrepair._issue("src/app.py", "syntax diagnostic", 1)]

    result = selfrepair.repair_files(
        pf,
        issues=[selfrepair._issue("src/app.py", "syntax diagnostic", 1)],
        check=check,
        call=lambda _prompt: ({"patches": [{"old": "value = 1", "new": "value = 2"}]}, {"in": 2, "out": 2}),
        max_rounds=1,
        reverify=verifier,
    )

    assert pf.read("src/app.py") == "value = 1\n"
    assert any(row.get("outcome") == "rolled_back" for row in result["log"])
    assert verifier_calls["count"] >= 2


def test_preexisting_test_failure_does_not_mask_a_real_diagnostic_fix():
    import uuid

    pf = ProjectFiles("reverify-" + uuid.uuid4().hex[:8])
    pf.write("src/app.py", "value = 1\n")

    def check(project):
        return [] if project.read("src/app.py") == "value = 2\n" else [selfrepair._issue("src/app.py", "syntax diagnostic", 1)]

    result = selfrepair.repair_files(
        pf,
        issues=[selfrepair._issue("src/app.py", "syntax diagnostic", 1)],
        check=check,
        call=lambda _prompt: ({"patches": [{"old": "value = 1", "new": "value = 2"}]}, {"in": 2, "out": 2}),
        max_rounds=1,
        reverify=lambda _pf: ({"backend Python tests"}, True),
    )

    assert pf.read("src/app.py") == "value = 2\n"
    assert result["fixed"] == 1


def test_section_retry_budget_stops_repeating_the_same_issue():
    from backend.agent import orchestrator

    issue = {"sid": "hero", "msg": "same unresolved TypeScript error"}
    signature = orchestrator._sig(issue)
    assert orchestrator._section_fixable(issue, {signature: 0})
    assert not orchestrator._section_fixable(issue, {signature: orchestrator.MAX_TRIES_PER_ISSUE})


def test_section_repair_gate_requires_a_strict_diagnostic_reduction():
    from backend.agent import orchestrator

    before = [{"sid": None, "file": "src/App.tsx", "msg": "TS2304 Cannot find name 'Hero'"}]
    assert orchestrator._repair_improved(before, [], set(), set(), True)[0]
    assert not orchestrator._repair_improved(before, before, set(), set(), True)[0]
    assert not orchestrator._repair_improved(before, [], set(), {"new test failure"}, True)[0]
    assert not orchestrator._repair_improved(before, [], set(), set(), False)[0]

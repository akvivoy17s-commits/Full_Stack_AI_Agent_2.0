"""Phase 3: tiered fallback keeps the requested backend; named-tech mismatches are reported."""
from backend.api.autopilot import resolve_prompt


def test_django_mongodb_keeps_django_with_sqlite():
    res, _leg, asm, _app = resolve_prompt("Library management system with Django and MongoDB")
    st = res["stack"]
    assert st["backend"] == "django" and st["database"] == "sqlite"
    assert any(a.startswith("Requested") for a in asm)


def test_unsupported_named_tech_is_reported():
    for prompt, name in (("inventory system in Go with Gin", "go"), ("expense tracker using Angular", "angular"),
                         ("Kanban board with Vue", "vue"), ("Build a blog in Laravel", "laravel")):
        res, _l, asm, _a = resolve_prompt(prompt)
        assert res["ok"]
        assert any(a.startswith(f"You named {name}") for a in asm), asm


def test_supported_choice_has_no_mismatch_note():
    _res, _l, asm, _a = resolve_prompt("Build a Spring Boot HR system with MySQL")
    assert not any(a.startswith("You named") for a in asm)


def test_unimplemented_features_are_reported_not_ignored():
    _r, _l, asm, _a = resolve_prompt("booking app for salons with payments")
    assert any(a.startswith("Payments were mentioned") for a in asm)
    _r, _l, asm, _a = resolve_prompt("task manager with real-time updates")
    assert any(a.startswith("Real-time updates") for a in asm)
    _r, _l, asm, _a = resolve_prompt("Build a todo app")
    assert not any(a.startswith(("Payments", "Real-time", "Login")) for a in asm)

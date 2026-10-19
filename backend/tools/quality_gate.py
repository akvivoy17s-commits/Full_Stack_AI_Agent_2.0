"""Truthful, project-wide multi-language verification gate.

Static analysis can detect definite parser/compiler failures, but it cannot prove all
business logic correct. This module combines analyzer results with checks already run by
the React/app verification pipeline and explicitly reports missing toolchain/test evidence.
It never installs packages or runs commands itself; commands are handled by the bounded
language_analyzer only when deep verification is explicitly requested.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from backend.tools import language_analyzer


_COMPILER_WORDS = ("compiler", "type checker", "typecheck", "parser", "syntax")
_TEST_WORDS = ("test", "pytest", "unit", "integration", "end-to-end", "e2e")


def _status(check: dict) -> str:
    return str(check.get("status", "skipped")).lower()


def _is_passed(checks: list[dict], *needles: str) -> bool:
    for check in checks:
        if _status(check) != "passed":
            continue
        name = str(check.get("name", "")).lower()
        if all(needle.lower() in name for needle in needles):
            return True
    return False


def _language_covered(language: str, checks: list[dict]) -> bool:
    """Use only evidence that actually validates the detected language.

    In particular, a Vite/bundler build is not automatically treated as a TypeScript
    typecheck unless a separate typecheck passed or the command detail explicitly says
    TypeScript was checked. This prevents optimistic false-green results.
    """
    lang = language.lower()
    if "typescript" in lang or "tsx" in lang:
        if (_is_passed(checks, "type check") or _is_passed(checks, "typecheck")
                or _is_passed(checks, "typescript typecheck") or _is_passed(checks, "npm", "typecheck")):
            return True
        for check in checks:
            if _status(check) != "passed":
                continue
            name = str(check.get("name", "")).lower()
            detail = str(check.get("detail", "")).lower()
            if ("build" in name or "build" in detail) and any(token in detail for token in ("tsc --noemit", "typescript typecheck", "typescript compiler")):
                return True
        return False
    if "javascript / jsx" in lang or lang == "jsx":
        return (_is_passed(checks, "javascript syntax") or _is_passed(checks, "npm", "build")
                or _is_passed(checks, "production build"))
    if "javascript" in lang:
        return (_is_passed(checks, "javascript syntax") or _is_passed(checks, "production build")
                or _is_passed(checks, "npm", "build"))
    if "vue" in lang or "svelte" in lang:
        return _is_passed(checks, "npm", "build") or _is_passed(checks, "production build")
    # Native deep-check reports normally use the same language label.
    for check in checks:
        if _status(check) != "passed":
            continue
        label = str(check.get("language", "")).lower()
        if lang == label or lang in [x.strip() for x in label.split(",")]:
            return True
    return False


def _compiler_gaps(analysis: dict, evidence: list[dict]) -> list[dict]:
    gaps = []
    seen: set[str] = set()
    for check in analysis.get("checks", []):
        if _status(check) != "skipped":
            continue
        name = str(check.get("name", ""))
        lname = str(check.get("language", "")).strip()
        lower = name.lower()
        # These entries explicitly mean a detected language did not receive a compiler
        # or parser check. Generic build/test-script skips are handled separately.
        if not any(word in lower for word in _COMPILER_WORDS):
            continue
        if not lname or lname.lower() == "multiple" or _language_covered(lname, evidence):
            continue
        key = lname.lower()
        if key in seen:
            continue
        seen.add(key)
        gaps.append({
            "language": lname,
            "check": name,
            "detail": str(check.get("detail", "No suitable local compiler/parser was available."))[:350],
        })
    if analysis.get("truncated"):
        gaps.append({"language": "Project scan", "check": "Scan limit", "detail": "The configured source-file scan limit was reached."})
    for note in analysis.get("notes", []):
        if "could not be read" in str(note).lower():
            gaps.append({"language": "Project files", "check": "Unreadable source", "detail": str(note)[:350]})
    return gaps[:30]


def _test_evidence(checks: list[dict]) -> dict[str, Any]:
    test_checks = [
        {"name": str(c.get("name", "")), "status": _status(c), "detail": str(c.get("detail", ""))[:220]}
        for c in checks
        if any(word in str(c.get("name", "")).lower() for word in _TEST_WORDS)
        and "coverage gaps" not in str(c.get("name", "")).lower()
    ]
    passed = [c for c in test_checks if c["status"] == "passed"]
    failed = [c for c in test_checks if c["status"] == "failed"]
    skipped = [c for c in test_checks if c["status"] == "skipped"]
    if failed:
        status = "failed"
    elif passed and skipped:
        status = "partial"
    elif passed:
        status = "passed"
    else:
        status = "not_run"
    return {
        "status": status,
        "passed": passed[:10], "failed": failed[:10], "skipped": skipped[:10],
        "note": "Passing tests provide evidence only for tested behavior; they do not prove all logic correct."
        if passed else "No successful test-run evidence was found. Business logic is not proven by syntax/type checks alone.",
    }


def run_quality_gate(
    pf,
    *,
    deep: bool = False,
    existing_checks: list[dict] | None = None,
    require_logic_tests: bool = False,
) -> dict[str, Any]:
    """Run static checks, optionally available local toolchains, and report certainty gaps.

    ``existing_checks`` may contain build/type-check results produced by the frontend
    engine. These are reused as evidence so a successful TypeScript build is not falsely
    reported as an unverified TypeScript toolchain merely because the generic scanner
    does not parse TSX itself.
    """
    analysis = language_analyzer.analyze_project(pf, deep=deep, include_redundancy=True)
    evidence = list(analysis.get("checks", [])) + list(existing_checks or [])
    errors = [i for i in analysis.get("issues", []) if i.get("severity") == "error"]
    failed_checks = [c for c in analysis.get("checks", []) if _status(c) == "failed"]
    # Existing compiler/build errors are supplied by the app/section verification engine.
    external_failures = [c for c in (existing_checks or []) if _status(c) == "failed"]
    coverage_gaps = _compiler_gaps(analysis, evidence)
    if not analysis.get("files_scanned", 0):
        coverage_gaps.append({
            "language": "Project", "check": "No source files detected",
            "detail": "No recognized source/configuration files were scanned; correctness cannot be assessed.",
        })
    tests = _test_evidence(evidence)
    logic_hints = analysis.get("redundancy", [])[:30]
    actionable_logic_hints = [
        item for item in logic_hints
        if item.get("category") == "logic" and item.get("severity") == "warning"
    ]
    if tests["status"] == "failed":
        logic_status = "tests_failed"
    elif actionable_logic_hints:
        logic_status = "needs_review"
    elif tests["status"] == "passed":
        logic_status = "verified_by_tests"
    elif tests["status"] == "partial":
        logic_status = "test_coverage_partial"
    else:
        logic_status = "not_proven"

    # A report cannot claim a complete syntax pass while any detected language was not
    # actually parsed/compiled. Build/test failure remains a hard failure; absent
    # toolchains remain partial and must never silently turn green.
    if errors or failed_checks or external_failures:
        status = "failed"
    elif coverage_gaps:
        status = "partial"
    else:
        status = "passed"

    if ((require_logic_tests and tests["status"] != "passed")
            or tests["status"] == "partial" or actionable_logic_hints) and status == "passed":
        # Business logic needs test evidence. Heuristic logic red flags require review,
        # even if a test suite passed; tests cover only the paths they actually exercise.
        status = "partial"

    syntax_failure_words = ("syntax", "parser", "compiler", "type check", "typecheck", "build")
    syntax_failed_checks = [
        check for check in [*analysis.get("checks", []), *(existing_checks or [])]
        if _status(check) == "failed"
        and any(word in str(check.get("name", "")).lower() for word in syntax_failure_words)
    ]
    if errors or syntax_failed_checks:
        syntax_status = "failed"
    elif coverage_gaps:
        syntax_status = "partial"
    else:
        syntax_status = "passed"

    by_language = analysis.get("languages", [])
    return {
        "status": status,
        "deep": bool(deep),
        "syntax_status": syntax_status,
        "logical_status": logic_status,
        "logic_tests_required": bool(require_logic_tests),
        "files_scanned": analysis.get("files_scanned", 0),
        "languages_detected": [x.get("name") for x in by_language],
        "language_counts": by_language,
        "error_count": len(errors),
        "failed_check_count": len(failed_checks) + len(external_failures),
        "coverage_gaps": coverage_gaps,
        "test_evidence": tests,
        "logic_hints": logic_hints,
        "actionable_logic_hints": actionable_logic_hints[:20],
        "issues": errors[:50],
        "checks": analysis.get("checks", [])[:80],
        "notes": [
            *analysis.get("notes", []),
            "A parser/build pass verifies only the checks that ran; it cannot prove all runtime or business logic correct.",
            "A skipped compiler/parser is unverified, never counted as a pass.",
        ],
        "scope": analysis.get("scope", "Multi-language static verification."),
    }

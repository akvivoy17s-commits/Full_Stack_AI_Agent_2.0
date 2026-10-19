"""Regression tests for truthful cross-language quality gating."""
import uuid

import pytest

from backend.tools import language_analyzer, quality_gate, terminal
from backend.tools.project_files import ProjectFiles


@pytest.fixture
def pf(tmp_path, monkeypatch):
    monkeypatch.setattr("backend.tools.project_files.GENERATED_DIR", tmp_path)
    return ProjectFiles("quality-gate-" + uuid.uuid4().hex[:8])


def test_definite_python_syntax_error_fails_quality_gate(pf, monkeypatch):
    pf.write("src/broken.py", "def invalid(:\n    return 1\n")
    monkeypatch.setattr(language_analyzer.shutil, "which", lambda _name: None)

    report = quality_gate.run_quality_gate(pf)

    assert report["status"] == "failed"
    assert report["syntax_status"] == "failed"
    assert report["error_count"] >= 1
    assert any(i["file"] == "src/broken.py" for i in report["issues"])


def test_missing_rust_toolchain_is_unverified_not_passed(pf, monkeypatch):
    pf.write("src/main.rs", 'fn main() { println!("ok"); }\n')
    monkeypatch.setattr(language_analyzer.shutil, "which", lambda _name: None)

    report = quality_gate.run_quality_gate(pf)

    assert report["status"] == "partial"
    assert any(g["language"] == "Rust" for g in report["coverage_gaps"])


def test_successful_react_build_is_evidence_for_typescript_coverage(pf, monkeypatch):
    pf.write("src/App.tsx", "export default function App() { return <main>OK</main>; }\n")
    monkeypatch.setattr(language_analyzer.shutil, "which", lambda _name: None)
    evidence = [
        {"name": "type check", "status": "passed", "detail": "tsc completed"},
        {"name": "production build", "status": "passed", "detail": "Vite build completed"},
    ]

    report = quality_gate.run_quality_gate(pf, existing_checks=evidence)

    assert report["status"] == "passed"
    assert not any(g["language"] == "TypeScript / TSX" for g in report["coverage_gaps"])


def test_interactive_logic_without_test_evidence_is_not_declared_verified(pf, monkeypatch):
    pf.write("src/main.py", "def calculate(value):\n    return value * 2\n")
    monkeypatch.setattr(language_analyzer.shutil, "which", lambda _name: None)

    report = quality_gate.run_quality_gate(pf, require_logic_tests=True)

    assert report["status"] == "partial"
    assert report["logical_status"] == "not_proven"
    assert report["test_evidence"]["status"] == "not_run"


def test_parser_tool_allowlist_matches_configured_language_adapters():
    assert terminal.allowed(["php", "-l", "src/main.php"])
    assert terminal.allowed(["ruby", "-c", "src/main.rb"])
    assert terminal.allowed(["bash", "-n", "scripts/check.sh"])
    assert terminal.allowed(["swiftc", "-typecheck", "Sources/main.swift"])
    assert terminal.allowed(["gcc", "-fsyntax-only", "src/main.c"])
    assert terminal.allowed(["g++", "-fsyntax-only", "src/main.cpp"])
    assert terminal.allowed(["cargo", "check", "--offline", "--locked"])
    assert terminal.allowed(["tsc", "--noEmit", "--pretty", "false"])
    assert terminal.allowed(["dart", "analyze"])
    assert not terminal.allowed(["php", "-r", "system('whoami');"])
    assert not terminal.allowed(["cargo", "run"])
    assert not terminal.allowed(["tsc", "--noEmit", "&&", "whoami"])


def test_build_without_explicit_typecheck_does_not_cover_typescript(pf, monkeypatch):
    pf.write("src/App.tsx", "export default function App() { return <main>OK</main>; }\n")
    monkeypatch.setattr(language_analyzer.shutil, "which", lambda _name: None)
    report = quality_gate.run_quality_gate(
        pf, existing_checks=[{"name": "production build", "status": "passed", "detail": "Vite build completed"}]
    )
    assert report["status"] == "partial"
    assert report["syntax_status"] == "partial"
    assert any(g["language"] == "TypeScript / TSX" for g in report["coverage_gaps"])


def test_passing_and_skipped_test_suites_report_partial_evidence(pf, monkeypatch):
    pf.write("src/main.py", "def double(value):\n    return value * 2\n")
    monkeypatch.setattr(language_analyzer.shutil, "which", lambda _name: None)
    report = quality_gate.run_quality_gate(pf, existing_checks=[
        {"name": "unit tests", "status": "passed", "detail": "3 passed"},
        {"name": "integration tests", "status": "skipped", "detail": "database service unavailable"},
    ], require_logic_tests=True)
    assert report["test_evidence"]["status"] == "partial"
    assert report["logical_status"] == "test_coverage_partial"
    assert report["status"] == "partial"


def test_empty_project_is_not_reported_as_correct(pf, monkeypatch):
    monkeypatch.setattr(language_analyzer.shutil, "which", lambda _name: None)
    report = quality_gate.run_quality_gate(pf)
    assert report["status"] == "partial"
    assert report["syntax_status"] == "partial"
    assert any(g["check"] == "No source files detected" for g in report["coverage_gaps"])


def test_likely_logic_red_flag_prevents_green_status_even_if_syntax_is_valid(pf, monkeypatch):
    pf.write("src/logic.js", "function valid(value) { return value === value; }\n")
    monkeypatch.setattr(language_analyzer.shutil, "which", lambda _name: None)
    report = quality_gate.run_quality_gate(pf)
    assert report["syntax_status"] in {"passed", "partial"}
    assert report["logical_status"] == "needs_review"
    assert report["status"] == "partial"
    assert report["actionable_logic_hints"]

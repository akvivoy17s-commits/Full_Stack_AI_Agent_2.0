"""Coverage for language-aware syntax and conservative redundancy analysis."""
import json
import uuid
from pathlib import Path

import pytest

from backend.tools import language_analyzer, terminal
from backend.tools.project_files import ProjectFiles


@pytest.fixture
def pf(tmp_path, monkeypatch):
    monkeypatch.setattr("backend.tools.project_files.GENERATED_DIR", tmp_path)
    return ProjectFiles("langs-" + uuid.uuid4().hex[:8])


def test_detects_python_json_html_and_css_syntax_errors(pf, monkeypatch):
    pf.write("src/broken.py", "def nope(:\n  pass\n")
    pf.write("config.json", '{"broken": true,,}')
    pf.write("index.html", "<section><form></section>")
    pf.write("styles.css", ".card { color: red;\n")
    monkeypatch.setattr(language_analyzer.shutil, "which", lambda _name: None)

    report = language_analyzer.analyze_project(pf)
    error_files = {x["file"] for x in report["issues"] if x["severity"] == "error"}

    assert report["status"] == "failed"
    assert {"src/broken.py", "config.json", "index.html", "styles.css"} <= error_files


def test_reports_python_logic_and_redundancy_without_making_it_a_syntax_failure(pf, monkeypatch):
    pf.write("src/logic.py", """import os

def choose(value):
    if value == value:
        return True
        print('unreachable')
    return False

def choose(value):
    return value
""")
    monkeypatch.setattr(language_analyzer.shutil, "which", lambda _name: None)

    report = language_analyzer.analyze_project(pf)
    hints = report["redundancy"]

    assert any("unused import 'os'" in x["message"] for x in hints)
    assert any("compares 'value' with itself" in x["message"] for x in hints)
    assert any("unreachable statement" in x["message"] for x in hints)
    assert any("duplicate definition 'choose'" in x["message"] for x in hints)
    assert report["status"] == "passed"  # advisory logic findings don't act as syntax/build failures


def test_detects_language_groups_and_does_not_claim_unavailable_compilers_pass(pf, monkeypatch):
    pf.write("src/main.rs", "fn main() { println!(\"hi\"); }\n")
    pf.write("src/App.tsx", "export default function App() { return <div /> }\n")
    pf.write("src/main.go", "package main\nfunc main() {}\n")
    monkeypatch.setattr(language_analyzer.shutil, "which", lambda _name: None)

    report = language_analyzer.analyze_project(pf)
    by_name = {x["name"]: x for x in report["languages"]}

    assert by_name["Rust"]["files"] == 1
    assert by_name["TypeScript / TSX"]["files"] == 1
    assert by_name["Go"]["files"] == 1
    assert by_name["Rust"]["skipped"] >= 1
    assert any(c["status"] == "skipped" for c in report["checks"])


def test_jsonc_trailing_comma_is_accepted_but_invalid_json_is_not(pf, monkeypatch):
    pf.write("tsconfig.json", '{\n  // TypeScript config permits JSONC syntax\n  "compilerOptions": {"strict": true,},\n}\n')
    pf.write("package.json", '{ invalid }')
    monkeypatch.setattr(language_analyzer.shutil, "which", lambda _name: None)

    report = language_analyzer.analyze_project(pf)
    errors = [x for x in report["issues"] if x["severity"] == "error"]
    assert len(errors) == 1
    assert errors[0]["file"] == "package.json"


def test_deep_mode_never_installs_missing_dependencies(pf, monkeypatch):
    pf.write("package.json", json.dumps({"name": "sample", "scripts": {"build": "vite build"}}))
    pf.write("src/main.ts", "const count: number = 1;\n")
    calls = []
    monkeypatch.setattr(language_analyzer.shutil, "which", lambda _name: None)
    monkeypatch.setattr(terminal, "run", lambda *a, **k: calls.append(a) or {"code": 0, "out": ""})

    report = language_analyzer.analyze_project(pf, deep=True)

    assert not calls
    assert any("Dependencies are not installed" in c["detail"] for c in report["checks"])


def test_terminal_parser_allowlist_is_exact_and_rejects_shell_chaining():
    assert terminal.allowed(["php", "-l", "src/index.php"])
    assert terminal.allowed(["ruby", "-c", "src/main.rb"])
    assert terminal.allowed(["gcc", "-fsyntax-only", "src/main.c"])
    assert terminal.allowed(["cargo", "check", "--offline", "--locked"])
    assert terminal.allowed(["tsc", "--noEmit", "--pretty", "false"])
    assert not terminal.allowed(["php", "-l", "src/index.php; whoami"])
    assert not terminal.allowed(["ruby", "-e", "puts 1"])
    assert not terminal.allowed(["cargo", "run"])
    assert not terminal.allowed(["tsc", "--noEmit", "&&", "whoami"])


def test_reports_obvious_javascript_logic_redundancy(pf, monkeypatch):
    pf.write("src/logic.js", "function visible(value) {\n  if (value === value) return value && value;\n  return false;\n}\n")
    monkeypatch.setattr(language_analyzer.shutil, "which", lambda _name: None)

    report = language_analyzer.analyze_project(pf)
    hints = report["redundancy"]
    assert any("compares 'value' with itself" in x["message"] for x in hints)
    assert any("repeated operand 'value'" in x["message"] for x in hints)


def test_analyzer_includes_go_and_dotnet_build_manifests(pf, monkeypatch):
    pf.write("go.mod", "module sample\n\ngo 1.22\n")
    pf.write("app/App.csproj", "<Project Sdk=\"Microsoft.NET.Sdk\"><PropertyGroup><TargetFramework>net8.0</TargetFramework></PropertyGroup></Project>")
    files, truncated = language_analyzer._files(pf)
    assert "go.mod" in files
    assert "app/App.csproj" in files


def test_jsonc_line_comments_preserve_line_structure(pf, monkeypatch):
    pf.write("tsconfig.json", '{\n  // comment should preserve subsequent line numbers\n  "compilerOptions": {"strict": true,},\n}\n')
    pf.write("package.json", '{ "name": "ok" }')
    monkeypatch.setattr(language_analyzer.shutil, "which", lambda _name: None)
    report = language_analyzer.analyze_project(pf)
    assert not [x for x in report["issues"] if x["severity"] == "error"]

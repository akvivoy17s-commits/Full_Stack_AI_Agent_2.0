from backend.tools import debugger


def test_parses_multiple_typescript_errors_into_file_line_diagnostics():
    output = (
        "src/sections/Kpis.tsx(6,50): error TS2304: Cannot find name 'HeroBanner'.\n"
        "src/sections/Kpis.tsx(6,125): error TS2304: Cannot find name 'ProductCardList'.\n"
        "src/sections/Kpis.tsx(6,331): error TS2339: Property 'productcardlist' does not exist on type 'JSX.IntrinsicElements'.\n"
    )
    parsed = debugger.parse_diagnostics(output)
    assert len(parsed) == 3
    assert all(item["file"] == "src/sections/Kpis.tsx" for item in parsed)
    assert [item["line"] for item in parsed] == [6, 6, 6]
    assert parsed[0]["category"] == "undefined_symbol"
    assert parsed[2]["category"] == "invalid_jsx_tag"


def test_detects_root_cause_hint_for_jsx_contract_violations():
    issues = [{"file": "src/sections/Kpis.tsx", "msg": (
        "src/sections/Kpis.tsx(6,50): error TS2304: Cannot find name 'HeroBanner'.\n"
        "src/sections/Kpis.tsx(6,331): error TS2339: Property 'productcardlist' does not exist on type 'JSX.IntrinsicElements'."
    )}]
    result = debugger.root_cause_summary(issues)
    assert result["issue_count"] == 1
    assert any("HTML contract" in hint or "JSX/HTML contract" in hint for hint in result["root_cause_hints"])


def test_repair_acceptance_requires_strict_diagnostic_reduction():
    before = [{"file": "src/a.tsx", "msg": "src/a.tsx(2,4): error TS2304: Cannot find name 'Thing'."}]
    after = []
    assert debugger.compare_diagnostics(before, after)["status"] == "improved"
    assert debugger.compare_diagnostics(before, before)["status"] == "unchanged"
    other = [{"file": "src/a.tsx", "msg": "src/a.tsx(2,4): error TS2339: Property 'Thing' does not exist on type 'X'."}]
    assert debugger.compare_diagnostics(before, other)["status"] == "regressed"


def test_repair_context_does_not_read_environment_secrets(tmp_path, monkeypatch):
    from backend.tools.project_files import ProjectFiles
    import backend.tools.project_files as project_files

    monkeypatch.setattr(project_files, "GENERATED_DIR", tmp_path)
    pf = ProjectFiles("context-test")
    pf.write("src/app.tsx", "import { Missing } from './missing';\nexport const App = () => <Missing />;\n")
    pf.write("package.json", '{"scripts":{"build":"tsc --noEmit && vite build"},"dependencies":{"react":"*"}}')
    # ProjectFiles deliberately blocks .env reads. The context builder should only inspect
    # an allowlisted set of manifests and source snippets.
    output = debugger.repair_context(pf, "src/app.tsx", [{"file": "src/app.tsx", "msg": "Cannot find module './missing'"}], pf.read("src/app.tsx"))
    assert "package.json" in output
    assert "scripts" in output
    assert "PRIVATE_API_KEY" not in output

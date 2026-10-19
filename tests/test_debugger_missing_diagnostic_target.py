import uuid

from backend.agent import selfrepair as sr
from backend.tools import debugger
from backend.tools.project_files import ProjectFiles


def _pf():
    return ProjectFiles("dbg-target-" + uuid.uuid4().hex[:10])


def test_ts_diagnostic_same_line_as_build_command_uses_actual_source_file():
    output = ("> tsc --noEmit && vite build src/lib/MotionEffects.tsx(13,12): "
              "error TS2307: Cannot find module '../three-hero' or its corresponding type declarations.")
    rows = debugger.parse_diagnostics(output, root="C:/Users/Ajmal Khan/Desktop/project")
    assert rows
    assert rows[0]["file"] == "src/lib/MotionEffects.tsx"
    assert rows[0]["category"] == "missing_dependency_or_import"


def test_windows_absolute_path_with_spaces_is_normalized_relative_to_project_root():
    output = ("C:/Users/Ajmal Khan/Desktop/ai agent/generated_projects/p/src/lib/MotionEffects.tsx"
              "(13,12): error TS2307: Cannot find module '../three-hero'.")
    rows = debugger.parse_diagnostics(output, root="C:/Users/Ajmal Khan/Desktop/ai agent/generated_projects/p")
    assert rows and rows[0]["file"] == "src/lib/MotionEffects.tsx"


def test_missing_module_target_is_mapped_to_existing_diagnostic_source():
    pf = _pf()
    pf.write("src/lib/MotionEffects.tsx", "import { effect } from '../three-hero';\nexport default effect;\n")
    msg = ("build diagnostic: > tsc --noEmit && vite build "
           "src/lib/MotionEffects.tsx(1,24): error TS2307: Cannot find module '../three-hero'.")
    issue = {"file": "three-hero.js", "line": 1, "msg": "three-hero.js: " + msg}
    assert sr._resolve_repair_target(pf, issue) == "src/lib/MotionEffects.tsx"


def test_missing_unmappable_target_is_blocked_without_llm_call():
    pf = _pf()
    issue = {"file": "missing/three-hero.js", "msg": "missing generated asset missing/three-hero.js"}
    calls = []
    result = sr.repair_files(
        pf,
        issues=[issue],
        check=lambda _pf: [issue],
        call=lambda user: calls.append(user) or ({"patches": []}, {"in": 0, "out": 0}),
    )
    assert calls == []
    assert result["status"] == "BLOCKED"
    assert result["attempts"] == 0
    assert any(row["outcome"] == "target_missing" for row in result["log"])
    assert any("repair skipped" in row["msg"].lower() for row in result["remaining"])


def test_existing_explicit_target_still_resolves_normally():
    pf = _pf()
    pf.write("src/broken.js", "function x() {}\n")
    assert sr._resolve_repair_target(pf, {"file": "src/broken.js", "msg": "syntax error"}) == "src/broken.js"

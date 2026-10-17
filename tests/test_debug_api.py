from pydantic import ValidationError
import pytest

from backend.api import debug


def test_debug_request_accepts_error_up_to_15000_characters():
    request = debug.DebugRequest(error_text="E" * 15000)
    assert len(request.error_text) == 15000


def test_debug_request_rejects_error_over_15000_characters():
    with pytest.raises(ValidationError):
        debug.DebugRequest(error_text="E" * 15001)


def test_debugger_never_patches_tests_secrets_or_lockfiles():
    assert debug._eligible("src/App.tsx")
    assert debug._eligible("backend/main.py")
    assert not debug._eligible("tests/test_main.py")
    assert not debug._eligible("src/App.test.tsx")
    assert not debug._eligible("package-lock.json")
    assert not debug._eligible(".env")
    assert not debug._eligible("node_modules/pkg/index.js")


def test_project_chunks_include_all_readable_files_and_split_long_files():
    class FakeProjectFiles:
        def tree(self):
            return ["src/App.tsx", "src/helper.ts", "tests/test_app.py", ".env", "package-lock.json"]

        def read(self, path):
            return {
                "src/App.tsx": "A" * 4000,
                "src/helper.ts": "helper source",
                "tests/test_app.py": "assert True",
                ".env": "API_KEY=secret",
                "package-lock.json": "{\"lockfileVersion\": 3}",
            }[path]

    included, chunks = debug._project_chunks(FakeProjectFiles(), "src/App.tsx error")
    assert included == ["src/App.tsx", "src/helper.ts", "tests/test_app.py"]
    assert [c["offset"] for c in chunks if c["file"] == "src/App.tsx"] == ["0", "3500"]
    assert all(c["file"] != ".env" for c in chunks)


def test_batches_keep_every_chunk():
    chunks = [{"file": f"src/{i}.tsx", "offset": "0", "content": "x" * 3500} for i in range(12)]
    batches = debug._batches(chunks)
    assert len(batches) > 1
    assert sum(len(batch) for batch in batches) == len(chunks)


def test_debug_endpoint_scans_the_selected_project_across_all_batches(monkeypatch):
    files = {f"src/File{i}.tsx": f"FILE_MARKER_{i} " + ("x" * 3400) for i in range(8)}

    class FakeProjectFiles:
        def __init__(self, project_id):
            assert project_id == "currently-open-project"

        def tree(self):
            return list(files)

        def read(self, path, max_chars=None):
            value = files[path]
            return value[:max_chars] if max_chars else value

    prompts = []
    monkeypatch.setattr(debug, "_project", lambda pid: None)
    monkeypatch.setattr(debug, "ProjectFiles", FakeProjectFiles)
    monkeypatch.setattr(debug.llm, "call_json", lambda *args: (prompts.append(args[2]) or {"summary": "scanned", "diagnostics": [], "patches": [], "verification": []}, {"in": 1, "out": 1}))

    result = debug.debug_project("currently-open-project", debug.DebugRequest(error_text="TypeError: sample runtime error", apply_fixes=False))
    assert result["files_scanned"] == len(files)
    assert len(prompts) > 1
    combined = "\n".join(prompts)
    for marker in range(len(files)):
        assert f"FILE_MARKER_{marker}" in combined
    assert "CURRENT WORKSPACE PROJECT ID: currently-open-project" in combined

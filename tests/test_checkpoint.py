import pytest

from backend.tools import checkpoint


def test_checkpoint_restores_changes_and_removes_new_source_files(tmp_path):
    root = tmp_path / "project"
    root.mkdir()
    existing = root / "src" / "App.tsx"
    existing.parent.mkdir()
    existing.write_text("export const before = true;\n", encoding="utf-8")

    snap = checkpoint.capture(root, ["src/App.tsx", "src/Generated.tsx"])
    existing.write_text("broken source", encoding="utf-8")
    (root / "src" / "Generated.tsx").write_text("new invalid file", encoding="utf-8")

    restored = checkpoint.restore(root, snap)
    assert existing.read_text(encoding="utf-8") == "export const before = true;\n"
    assert not (root / "src" / "Generated.tsx").exists()
    assert set(restored) == {"src/App.tsx", "src/Generated.tsx"}


def test_checkpoint_rejects_path_traversal(tmp_path):
    root = tmp_path / "project"
    root.mkdir()
    with pytest.raises(ValueError, match="relative|traversal|escapes"):
        checkpoint.capture(root, ["../outside.py"])


def test_checkpoint_rejects_secret_paths(tmp_path):
    root = tmp_path / "project"
    root.mkdir()
    with pytest.raises(ValueError, match="secret"):
        checkpoint.capture(root, [".env"])

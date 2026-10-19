"""Regression tests for generated-project path and atomic-write safety."""
import os
import uuid

import pytest

from backend.tools.project_files import ProjectFiles


def test_project_root_symlink_is_rejected(tmp_path, monkeypatch):
    monkeypatch.setattr("backend.tools.project_files.GENERATED_DIR", tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    try:
        (tmp_path / "project-link").symlink_to(outside, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("directory symlinks are unavailable")

    with pytest.raises(ValueError, match="symlink"):
        ProjectFiles("project-link")


def test_predictable_tmp_symlink_cannot_redirect_file_write(tmp_path, monkeypatch):
    monkeypatch.setattr("backend.tools.project_files.GENERATED_DIR", tmp_path / "generated")
    pf = ProjectFiles("write-safe-" + uuid.uuid4().hex[:8])
    pf.write("victim.txt", "before")
    outside = tmp_path / "outside-secret.txt"
    outside.write_text("keep this secret", encoding="utf-8")
    try:
        (pf.root / "victim.txt.tmp").symlink_to(outside)
    except (OSError, NotImplementedError):
        pytest.skip("file symlinks are unavailable")

    pf.write("victim.txt", "after")

    assert outside.read_text(encoding="utf-8") == "keep this secret"
    assert pf.read("victim.txt") == "after"


def test_installed_and_build_output_dirs_are_ignored_and_protected(tmp_path, monkeypatch):
    monkeypatch.setattr("backend.tools.project_files.GENERATED_DIR", tmp_path / "generated")
    pf = ProjectFiles("ignore-safe-" + uuid.uuid4().hex[:8])
    for rel in ("NODE_MODULES/evil.js", ".VENV/bin/python", "dist/index.html", "target/classes/App.class"):
        with pytest.raises(ValueError, match="protected directory"):
            pf.write(rel, "do not overwrite")
    (pf.root / ".venv").mkdir()
    (pf.root / ".venv" / "python.exe").write_text("fake", encoding="utf-8")
    (pf.root / "dist").mkdir()
    (pf.root / "dist" / "index.html").write_text("build output", encoding="utf-8")
    assert ".venv/python.exe" not in pf.tree()
    assert "dist/index.html" not in pf.tree()

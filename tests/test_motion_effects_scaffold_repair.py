from pathlib import Path
from types import SimpleNamespace

from backend.engines import react_engine


class MemoryProjectFiles:
    def __init__(self, root: Path, files: dict[str, str]):
        self.root = root
        self.files = dict(files)

    def read(self, rel: str) -> str:
        if rel not in self.files:
            raise FileNotFoundError(rel)
        return self.files[rel]

    def write(self, rel: str, content: str) -> None:
        self.files[rel] = content
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def _broken_component() -> str:
    return '''import { useEffect } from 'react'
import Hero from '../three-hero'
import { initMotion } from './motion'
export default function MotionEffects() {
  useEffect(() => initMotion(), [])
  return <Hero />
}
'''


def _ts2307_output(path: str = 'src/lib/MotionEffects.tsx') -> str:
    return f"{path}(13,12): error TS2307: Cannot find module '../three-hero' or its corresponding type declarations."


def test_known_missing_three_hero_import_restores_canonical_scaffold(tmp_path):
    pf = MemoryProjectFiles(tmp_path, {"src/lib/MotionEffects.tsx": _broken_component()})

    changed = react_engine.repair_known_scaffold_import(pf, _ts2307_output())

    assert changed is True
    assert pf.read("src/lib/MotionEffects.tsx") == react_engine.ce._tpl("react/src/lib/MotionEffects.tsx")
    assert "../three-hero" not in pf.read("src/lib/MotionEffects.tsx")


def test_known_repair_does_not_touch_other_files_or_diagnostics(tmp_path):
    broken = _broken_component()
    pf = MemoryProjectFiles(tmp_path, {"src/lib/MotionEffects.tsx": broken})

    assert not react_engine.repair_known_scaffold_import(
        pf, "src/sections/Overview.tsx(3,2): error TS2307: Cannot find module '../three-hero'."
    )
    assert pf.read("src/lib/MotionEffects.tsx") == broken


def test_build_retries_once_after_deterministic_scaffold_repair(tmp_path, monkeypatch):
    root = tmp_path
    (root / "node_modules" / "vite").mkdir(parents=True)
    pf = MemoryProjectFiles(root, {"src/lib/MotionEffects.tsx": _broken_component()})
    calls = []

    monkeypatch.setattr(react_engine.shutil, "which", lambda name: f"/fake/{name}")

    def fake_run(command, cwd, **kwargs):
        calls.append(command)
        if len(calls) == 1:
            return {"code": 2, "out": _ts2307_output()}
        return {"code": 0, "out": "tsc passed\nvite build passed"}

    monkeypatch.setattr(react_engine.terminal, "run", fake_run)

    result = react_engine.build(pf, SimpleNamespace())

    assert result["built"] is True
    assert result["issues"] == []
    assert result["auto_repairs"] == ["src/lib/three-hero.js", "src/lib/MotionEffects.tsx"]
    assert result["note"] == "ok (generated files restored)"
    assert len(calls) == 2
    assert pf.read("src/lib/MotionEffects.tsx") == react_engine.ce._tpl("react/src/lib/MotionEffects.tsx")

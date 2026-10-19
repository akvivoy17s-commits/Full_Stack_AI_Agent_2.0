from pathlib import Path

from backend.agent import selfrepair


class MemoryProjectFiles:
    def __init__(self, root: Path, files: dict[str, str]):
        self.root = root
        self.files = dict(files)
        for rel, text in files.items():
            path = root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")

    def read(self, rel: str, max_chars=None) -> str:
        if rel in self.files:
            text = self.files[rel]
        else:
            text = (self.root / rel).read_text(encoding="utf-8")
        return text[:max_chars] if max_chars else text

    def write(self, rel: str, content: str) -> str:
        path = (self.root / rel).resolve()
        if self.root.resolve() not in path.parents:
            raise ValueError("path escapes root")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        self.files[rel] = content
        return "hash"

    def tree(self) -> list[str]:
        return sorted(p.relative_to(self.root).as_posix() for p in self.root.rglob("*") if p.is_file())

    def _safe(self, rel: str) -> Path:
        path = (self.root / rel).resolve()
        if self.root.resolve() not in path.parents:
            raise ValueError("unsafe path")
        return path


def test_missing_three_hero_maps_to_canonical_react_scaffold_and_rechecks(tmp_path):
    issue = {"file": "three-hero.js", "msg": "three-hero.js: unresolved local module"}
    broken = "import Hero from '../three-hero';\nexport default function MotionEffects() { return <Hero /> }\n"
    pf = MemoryProjectFiles(tmp_path, {"src/lib/MotionEffects.tsx": broken})

    def check(project):
        source = project.read("src/lib/MotionEffects.tsx")
        return [issue] if "../three-hero" in source else []

    result = selfrepair.repair_files(
        pf, issues=[issue], check=check,
        call=lambda _user: (_ for _ in ()).throw(AssertionError("LLM should not be called for known scaffold recovery")),
    )

    assert result["status"] == "PASS"
    assert result["attempts"] == 0
    assert "../three-hero" not in pf.read("src/lib/MotionEffects.tsx")
    assert "initMotion" in pf.read("src/lib/MotionEffects.tsx")
    assert any(row["outcome"] == "deterministic_recovery" for row in result["log"])


def test_missing_html_three_hero_asset_restored_only_when_referenced(tmp_path):
    issue = {"file": "three-hero.js", "msg": "missing generated asset three-hero.js"}
    pf = MemoryProjectFiles(tmp_path, {"index.html": '<html><body><main data-three-hero></main><script type="module" src="js/three-hero.js"></script></body></html>'})

    def check(project):
        return [issue] if not (project.root / "js/three-hero.js").is_file() else []

    result = selfrepair.repair_files(
        pf, issues=[issue], check=check,
        call=lambda _user: (_ for _ in ()).throw(AssertionError("LLM should not be called for a known checked-in asset")),
    )

    asset = tmp_path / "js/three-hero.js"
    assert result["status"] == "PASS"
    assert asset.is_file()
    text = asset.read_text(encoding="utf-8")
    assert "querySelectorAll" in text and "three-hero-fallback" in text


def test_does_not_restore_html_animation_asset_when_no_entry_references_it(tmp_path):
    issue = {"file": "three-hero.js", "msg": "missing generated asset three-hero.js"}
    pf = MemoryProjectFiles(tmp_path, {"index.html": "<html><body><h1>No 3D hero script here</h1></body></html>"})
    changed = selfrepair._restore_known_missing_module_assets(pf, [issue])
    assert changed == []
    assert not (tmp_path / "js/three-hero.js").exists()


def test_unrelated_missing_module_is_not_fabricated(tmp_path):
    issue = {"file": "missing/future-widget.js", "msg": "missing module future-widget.js"}
    pf = MemoryProjectFiles(tmp_path, {"index.html": "<html><body></body></html>"})
    changed = selfrepair._restore_known_missing_module_assets(pf, [issue])
    assert changed == []
    assert not (tmp_path / "missing/future-widget.js").exists()


def test_canonical_react_motion_import_restores_missing_runtime_without_llm(tmp_path):
    from backend.engines import code_engine

    issue = {"file": "three-hero.js", "msg": "Cannot resolve ./three-hero.js from src/lib/MotionEffects.tsx"}
    pf = MemoryProjectFiles(tmp_path, {
        "src/lib/MotionEffects.tsx": code_engine._tpl("react/src/lib/MotionEffects.tsx"),
    })

    def check(project):
        return [issue] if not (project.root / "src/lib/three-hero.js").is_file() else []

    result = selfrepair.repair_files(
        pf, issues=[issue], check=check,
        call=lambda _user: (_ for _ in ()).throw(AssertionError("known scaffold asset must not consume an LLM repair")),
    )

    assert result["status"] == "PASS"
    assert result["attempts"] == 0
    assert (tmp_path / "src/lib/three-hero.js").is_file()
    assert (tmp_path / "src/lib/three-hero.d.ts").is_file()
    assert any(row["outcome"] == "deterministic_recovery" for row in result["log"])

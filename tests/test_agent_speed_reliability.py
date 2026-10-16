from types import SimpleNamespace
import uuid

from backend.engines import code_engine
from backend.tools.project_files import ProjectFiles
from backend.tools.validators import validate_html


def test_dedupe_ids_handles_quoted_unquoted_and_reserved_section_ids():
    html = '<section id=hero><h2 id="hero">Heading</h2><input id="hero-email"><input id=hero-email></section>'
    cleaned = code_engine.dedupe_ids(html, {"hero", "features"}, "hero")
    assert cleaned.count("id=hero") == 1
    assert cleaned.count('id="hero-email"') == 1
    assert validate_html(cleaned) == []


def test_normalize_existing_ids_repairs_duplicate_ids_without_llm():
    pf = ProjectFiles("test-ids-" + uuid.uuid4().hex[:8])
    pf.write("index.html", '''<!doctype html><html lang="en"><head><title>IDs</title></head><body><main>
<!--SECTION:hero--><section id=hero><h1 id="hero">Heading</h1><input id="shared"></section><!--/SECTION:hero-->
<!--SECTION:features--><section id="features"><p id="hero">Feature</p><input id="shared"></section><!--/SECTION:features-->
</main></body></html>''')
    pf.write("css/sections.css", "")
    state = SimpleNamespace(plan={"sections": ["hero", "features"], "stack": "html"}, sections_done=["hero", "features"])
    changed = code_engine.normalize_existing_ids(pf, state)
    assert changed == 2
    whole = pf.read("index.html")
    for sid in ("hero", "features"):
        assert whole.count(f'id="{sid}"') + whole.count(f"id={sid}") == 1
    assert whole.count('id="shared"') == 1
    assert code_engine.normalize_existing_ids(pf, state) == 0


def test_generation_profiles_bound_output_without_skipping_validation():
    from backend.agent.llm import effective_output_budget

    assert effective_output_budget("section", 1800, "fast") == 1500
    assert effective_output_budget("section", 1800, "balanced") == 1800
    assert effective_output_budget("section", 2500, "quality") == 2500
    assert effective_output_budget("repair", 1200, "fast") == 650
    assert effective_output_budget("unbounded-kind", 777, "quality") == 777


def test_settings_schema_accepts_only_supported_generation_profiles():
    import pytest
    from pydantic import ValidationError
    from backend.agent.schemas import SettingsUpdate

    for profile in ("fast", "balanced", "quality"):
        assert SettingsUpdate(generation_profile=profile).generation_profile == profile
    with pytest.raises(ValidationError):
        SettingsUpdate(generation_profile="turbo")

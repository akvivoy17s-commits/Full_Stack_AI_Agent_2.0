from pathlib import Path

from backend.knowledge import guide_retriever as kr


def test_all_user_supplied_guides_are_bundled():
    # Eight previously bundled guides plus eight newly supplied full-stack guides.
    assert len(kr.GUIDES) == 17
    assert all((kr.GUIDE_DIR / filename).is_file() for filename in kr.GUIDES)
    assert len(kr._chunks()) > 1000


def test_new_full_stack_guides_have_source_content():
    expected = {
        "fullstack_web_development_complete_concepts_tools_functions_guide.md",
        "nestjs_backend_complete_syntax_functions_guide.md",
        "python_for_ai_complete_syntax_functions_guide.md",
        "react_js_typescript_full_stack_complete_guide.md",
        "rust_backend_complete_syntax_functions_guide.md",
        "springboot_java_full_stack_complete_guide.md",
        "sql_complete_full_stack_syntax_functions_guide.md",
        "tailwind_css_complete_syntax_utilities_guide.md",
        "ecommerce_shopping_reference_guide.md",
    }
    assert expected.issubset(kr.GUIDES)
    assert all((kr.GUIDE_DIR / name).stat().st_size > 10_000 for name in expected)


def test_mongodb_prompt_retrieves_mongodb_syntax_and_aggregation_guide():
    result = kr.retrieve_knowledge(
        "repair",
        "Fix MongoDB aggregation pipeline and updateOne query in backend code",
        file_path="backend/repositories/products.js",
        max_chars=1800,
    )
    assert "MongoDB" in result
    assert "mongodb_complete_syntax_functions_full_stack_guide.md" in result
    assert len(result) <= 1800


def test_django_and_fastapi_docs_are_detected_for_backend_tasks():
    django = kr.retrieve_knowledge("repair", "Django ORM QuerySet migration error", file_path="app/models.py")
    fastapi = kr.retrieve_knowledge("repair", "FastAPI Pydantic response model validation error", file_path="app/main.py")
    assert "django_complete_syntax_functions_full_stack_guide.md" in django
    assert "flask_fastapi_complete_syntax_functions_guide.md" in fastapi


def test_dockerfile_uses_docker_guide():
    result = kr.retrieve_knowledge("repair", "Fix Docker build stage", file_path="Dockerfile", max_chars=1800)
    assert "docker_complete_syntax_commands_full_stack_guide.md" in result


def test_section_prompts_get_web_baseline_guides():
    result = kr.retrieve_knowledge("section", "Build a responsive HTML/CSS hero with JavaScript interactions", max_chars=1900)
    assert "html_complete_full_stack_guide.md" in result
    assert "css_complete_3d_4d_animations_full_stack_guide.md" in result
    assert "javascript_full_stack_complete_guide.md" in result
    assert len(result) <= 1900


def test_context_enrichment_does_not_exceed_reference_budget_by_much():
    original = "Create a responsive page using HTML CSS and JavaScript."
    result = kr.enrich_user_context("section", original, max_chars=800)
    assert result.startswith(original)
    assert "REFERENCE KNOWLEDGE" in result
    assert len(result) <= len(original) + 800


def test_unknown_task_with_no_guide_signal_does_not_inject_random_docs():
    # SQLite is a real database signal and should retrieve SQL guidance; use an unrelated
    # non-technology request here to test that the retriever does not inject random guides.
    result = kr.retrieve_knowledge("some unrelated task", "rotate a local archive at midnight")
    assert result == ""


def test_typescript_file_gets_language_fundamentals_without_angular_api_injection():
    result = kr.retrieve_knowledge("repair", "TS2307 module not found", file_path="src/lib/MotionEffects.tsx", max_chars=1900)
    assert "javascript_full_stack_complete_guide.md" in result
    assert "angular_typescript_full_stack_complete_guide.md" in result
    # When Angular is not selected, Angular-only concepts are filtered out.
    assert "Angular CLI Commands" not in result


def test_explicit_backend_stack_is_not_crowded_out_by_default_frontend_guides():
    result = kr.retrieve_knowledge("blueprint", "Django API with MongoDB and Docker Compose deployment", max_chars=1900)
    assert "django_complete_syntax_functions_full_stack_guide.md" in result
    assert "mongodb_complete_syntax_functions_full_stack_guide.md" in result or "docker_complete_syntax_commands_full_stack_guide.md" in result


def test_llm_json_generation_attaches_relevant_guides_when_not_in_mock_mode(monkeypatch):
    import json
    import pytest
    # A files-only patch staging area may not include the host project's config.py;
    # in the actual project this integration test runs normally.
    pytest.importorskip("backend.config")
    from backend.agent import llm

    observed = []
    monkeypatch.setattr(llm.config, "MOCK_LLM", False)
    monkeypatch.setattr(llm.db, "get_settings", lambda: {
        "provider": "ollama", "fallback_provider": "", "max_retries": 0,
        "generation_profile": "fast",
    })
    monkeypatch.setattr(llm.P, "provider_settings", lambda settings, provider: {"model": "unit-test-model"})

    def fake_chat(system, user, model, max_tokens, settings, images=None):
        observed.append(user)
        return json.dumps({"html": "<section><h1>Test</h1></section>", "css": "section { display: block; }"}), {"in": 1, "out": 1}

    monkeypatch.setattr(llm, "_chat", fake_chat)
    result, _usage = llm.call_json("section", "system", "Build a semantic HTML section with responsive CSS and JavaScript interaction.", max_tokens=10)
    assert result["html"].startswith("<section")
    assert observed and "REFERENCE KNOWLEDGE" in observed[0]
    assert "html_complete_full_stack_guide.md" in observed[0]
    assert "css_complete_3d_4d_animations_full_stack_guide.md" in observed[0]


import pytest


@pytest.mark.parametrize(("query", "path", "expected"), [
    ("Create a NestJS backend with controllers, providers, DTOs and guards", "", "nestjs_backend_complete_syntax_functions_guide.md"),
    ("Build a Python RAG agent using embeddings and PyTorch", "backend/agent/model.py", "python_for_ai_complete_syntax_functions_guide.md"),
    ("Fix React TypeScript component hooks and TSX build errors", "src/components/Panel.tsx", "react_js_typescript_full_stack_complete_guide.md"),
    ("Fix Rust Axum Tokio SQLx compile errors", "src/main.rs", "rust_backend_complete_syntax_functions_guide.md"),
    ("Fix Spring Boot Java REST controller and JPA repository", "src/main/java/App.java", "springboot_java_full_stack_complete_guide.md"),
    ("Correct PostgreSQL migration, joins and foreign-key constraint", "db/migrations/001.sql", "sql_complete_full_stack_syntax_functions_guide.md"),
    ("Tailwind CSS v4 @theme utility not generated", "src/index.css", "tailwind_css_complete_syntax_utilities_guide.md"),
    ("Create a full-stack web app with API, database, auth and deployment", "", "fullstack_web_development_complete_concepts_tools_functions_guide.md"),
])
def test_new_guide_retrieval_routes_to_relevant_document(query, path, expected):
    result = kr.retrieve_knowledge("repair" if path else "blueprint", query, file_path=path, max_chars=2200)
    assert expected in result
    assert len(result) <= 2200


def test_react_guide_does_not_match_angular_reactive_forms_by_substring_only():
    selected = kr._detected_guides("Angular reactive forms validation", "repair", "src/app/form.ts")
    assert "angular_typescript_full_stack_complete_guide.md" in selected
    assert "react_js_typescript_full_stack_complete_guide.md" not in selected


def test_backend_python_edit_retrieves_language_guide_not_frontend_only_guides():
    result = kr.retrieve_knowledge("edit", "Fix Python typing and async bug", file_path="backend/service.py", max_chars=2000)
    assert "python_for_ai_complete_syntax_functions_guide.md" in result
    assert "html_complete_full_stack_guide.md" not in result


def test_ui_section_can_retrieve_react_and_tailwind_guides_without_backend_noise():
    result = kr.retrieve_knowledge("section", "Build a React TypeScript dashboard using Tailwind CSS v4", max_chars=2200)
    assert "react_js_typescript_full_stack_complete_guide.md" in result
    assert "tailwind_css_complete_syntax_utilities_guide.md" in result
    assert "nestjs_backend_complete_syntax_functions_guide.md" not in result


def test_ecommerce_reference_guide_is_retrieved_for_ui_and_full_stack_tasks():
    query = (
        "Build a React ecommerce shopping website with product catalog, category filters, "
        "cart persistence, wishlist, checkout, address book, orders, Firebase and admin product management"
    )
    result = kr.retrieve_knowledge("blueprint", query, max_chars=2800)
    assert "ecommerce_shopping_reference_guide.md" in result
    assert "server must" in result.lower() or "checkout" in result.lower()
    ui = kr.retrieve_knowledge("section", query, max_chars=2500)
    assert "ecommerce_shopping_reference_guide.md" in ui
    assert len(result) <= 2800 and len(ui) <= 2500

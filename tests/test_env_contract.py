"""Environment-contract regression tests for generated full-stack projects."""
from __future__ import annotations

import shutil
import subprocess

import pytest

from backend.gen import stage
from backend.gen.env_contract import public_env_example
from backend.spec import compose
from backend.spec.env_contract import detect
from backend.stack.resolver import resolve
from backend.tools.project_files import ProjectFiles


def _stack(brief: str, backend: str = "express", database: str = "postgresql") -> dict:
    result = resolve(
        "manual",
        {
            "frontend": "react",
            "frontend_lang": "ts",
            "backend": backend,
            "backend_lang": "js" if backend == "express" else "ts",
            "database": database,
            "auth": "jwt",
        },
        brief,
    )
    assert result["ok"], result.get("errors")
    return result["stack"]


def test_named_and_generic_api_keys_get_server_only_env_names():
    assert detect("Build a chatbot using OpenAI API")[0]["name"] == "OPENAI_API_KEY"
    acme = detect("Build inventory sync that integrates with Acme API")
    assert len(acme) == 1
    assert acme[0]["name"] == "ACME_API_KEY"
    assert acme[0]["scope"] == "server" and acme[0]["secret"] is True
    unknown = detect("Add support for an external API")
    assert {entry["name"] for entry in unknown} == {"EXTERNAL_API_BASE_URL", "EXTERNAL_API_KEY"}


def test_public_frontend_example_never_contains_server_keys():
    spec = {
        "env": [
            {"name": "VITE_SUPABASE_ANON_KEY", "scope": "public", "secret": False,
             "placeholder": "your-public-value", "purpose": "Public key"},
            {"name": "SUPABASE_SERVICE_ROLE_KEY", "scope": "server", "secret": True,
             "placeholder": "your-secret-value", "purpose": "Private service key", "integration": "supabase"},
            {"name": "ACME_API_KEY", "scope": "server", "secret": True,
             "placeholder": "your-acme-api-key", "purpose": "Private Acme key", "integration": "acme"},
        ]
    }
    example = public_env_example(spec)
    assert "VITE_SUPABASE_ANON_KEY" in example
    assert "SUPABASE_SERVICE_ROLE_KEY" not in example
    assert "ACME_API_KEY" not in example


def test_express_generation_wires_detected_key_through_env_and_runtime_config(tmp_path):
    brief = "Build an inventory dashboard that integrates with Acme API to sync stock. Use PostgreSQL database."
    stack = _stack(brief)
    spec = compose.build(brief, stack)
    pf = ProjectFiles("env-contract-express-test")
    result = stage.run(pf, spec, stack)

    assert result["generated"] is True
    backend_env = pf.read("backend/.env.example")
    assert "DATABASE_URL=postgresql://" in backend_env
    assert "ACME_API_KEY=your-acme-api-key" in backend_env
    assert "ACME_API_KEY" in pf.read("backend/src/lib/external-env.js")
    config = pf.read("backend/src/config.js")
    assert '"ACME_API_KEY"' in config and "externalApis:" in config
    assert "ACME_API_KEY" not in pf.read(".env.example")  # private key never reaches Vite env
    ignore = pf.read("backend/.gitignore")
    assert ".env" in ignore and ".env.*" in ignore and "!.env.example" in ignore
    assert "backend/.env" in pf.read("backend/ENVIRONMENT.md")

    node = shutil.which("node")
    if node:
        config_path = pf.root / "backend/src/config.js"
        helper_path = pf.root / "backend/src/lib/external-env.js"
        for path in (config_path, helper_path):
            check = subprocess.run([node, "--check", str(path)], capture_output=True, text=True, timeout=20)
            assert check.returncode == 0, check.stderr


def test_generic_api_key_mentions_are_detected_even_without_vendor_name():
    entries = detect("The website should read an API key for Contoso and use the key only on the server.")
    assert any(entry["name"] == "CONTOSO_API_KEY" and entry["secret"] for entry in entries)


@pytest.mark.parametrize(
    ("backend", "language", "expected_path", "expected_marker"),
    [
        ("nestjs", "ts", "backend/src/config.ts", "externalApis:"),
        ("fastapi", "py", "backend/app/external_env.py", "ALLOWED_EXTERNAL_ENV"),
        ("flask", "py", "backend/app/external_env.py", "ALLOWED_EXTERNAL_ENV"),
        ("django", "py", "backend/app/external_env.py", "ALLOWED_EXTERNAL_ENV"),
        ("spring", "java", "backend/src/main/java/app/integrations/ExternalApiEnvironment.java", "CONTOSO_API_KEY"),
    ],
)
def test_runtime_env_adapter_is_generated_for_supported_backend_stacks(
    backend, language, expected_path, expected_marker
):
    brief = "Build a customer portal that uses Contoso API for customer records. Use PostgreSQL database."
    result = resolve(
        "manual",
        {
            "frontend": "react",
            "frontend_lang": "ts",
            "backend": backend,
            "backend_lang": language,
            "database": "postgresql",
            "auth": "jwt",
        },
        brief,
    )
    assert result["ok"], result.get("errors")
    spec = compose.build(brief, result["stack"])
    pf = ProjectFiles(f"env-contract-{backend}-test")
    generated = stage.run(pf, spec, result["stack"])

    assert generated["generated"] is True
    assert "CONTOSO_API_KEY=your-contoso-api-key" in pf.read("backend/.env.example")
    assert expected_path in pf.tree()
    assert expected_marker in pf.read(expected_path)
    assert "CONTOSO_API_KEY" not in pf.read(".env.example")
    assert "!.env.example" in pf.read("backend/.gitignore")

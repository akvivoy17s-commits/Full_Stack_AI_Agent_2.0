import os

import pytest

from backend.agent import providers as P


def test_registry_has_all_requested_providers_and_fixed_key_allowlist():
    assert {"ollama", "openai", "gemini", "openrouter", "groq", "deepseek", "anthropic"} <= set(P.PROVIDER_REGISTRY)
    assert P.PROVIDER_REGISTRY["anthropic"]["adapter"] == "anthropic_messages"
    assert P.PROVIDER_REGISTRY["gemini"]["adapter"] == "openai_compatible"
    for meta in P.PROVIDER_REGISTRY.values():
        key_name = meta["key_env_var"]
        assert key_name is None or key_name in P.KEY_ENV_VARS


def test_api_key_is_scoped_to_selected_provider(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "openai-test-key")
    monkeypatch.setenv("GEMINI_API_KEY", "gemini-test-key")
    assert P.api_key("openai") == "openai-test-key"
    assert P.api_key("gemini") == "gemini-test-key"
    assert P.api_key("deepseek") is None
    assert P.api_key("ollama") is None


def test_legacy_llm_key_only_applies_to_openai_provider(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("LLM_API_KEY", "legacy-test-key")
    assert P.api_key("openai") == "legacy-test-key"
    assert P.api_key("gemini") is None


def test_remote_http_with_key_is_rejected():
    with pytest.raises(P.ProviderError) as err:
        P.check_destination("http://example.com/v1", "my-secret", "gemini")
    assert err.value.code == "insecure"


def test_remote_host_without_key_is_rejected():
    with pytest.raises(P.ProviderError) as err:
        P.check_destination("https://example.com/v1", None, "deepseek")
    assert err.value.code == "no_key"
    assert "DEEPSEEK_API_KEY" in str(err.value)


def test_local_ollama_can_use_http_without_key():
    P.check_destination("http://localhost:11434", None, "ollama")


def test_openai_body_uses_selected_base_url_for_protocol_options():
    body = P.openai_body("system", "write JSON", "custom-model", 120, {}, base_url="https://api.openai.com/v1")
    assert body["model"] == "custom-model"
    assert body["max_completion_tokens"] == 120
    assert body["response_format"] == {"type": "json_object"}
    compatible = P.openai_body("system", "write JSON", "m", 120, {}, base_url="https://api.groq.com/openai/v1")
    assert compatible["max_tokens"] == 120


def test_anthropic_native_request_body_and_sse_parsing():
    body = P.anthropic_body("rules", "return JSON", "claude-sonnet-4-6", 900, ["YmFzZTY0"])
    assert body["system"] == "rules"
    assert body["messages"][0]["content"][1]["source"]["data"] == "YmFzZTY0"
    assert "response_format" not in body
    text, usage, done = P.parse_anthropic_event("content_block_delta", '{"type":"content_block_delta","delta":{"type":"text_delta","text":"{\\\"ok\\\":true}"}}')
    assert text == '{"ok":true}'
    assert usage is None and not done
    _, usage, done = P.parse_anthropic_event("message_start", '{"type":"message_start","message":{"usage":{"input_tokens":9}}}')
    assert usage == (9, 0) and not done
    _, usage, done = P.parse_anthropic_event("message_delta", '{"type":"message_delta","usage":{"output_tokens":4}}')
    assert usage == (0, 4) and not done
    _, usage, done = P.parse_anthropic_event("message_stop", '{"type":"message_stop"}')
    assert usage is None and done


def test_provider_resolution_uses_per_provider_model_and_url():
    settings = {
        "provider": "gemini",
        "gemini_model": "gemini-custom",
        "gemini_base_url": "https://generativelanguage.googleapis.com/v1beta/openai",
    }
    resolved = P.provider_settings(settings)
    assert resolved["id"] == "gemini"
    assert resolved["model"] == "gemini-custom"
    assert resolved["base_url"].endswith("/openai")


def test_unknown_provider_fails_closed():
    with pytest.raises(ValueError):
        P.get_provider("malicious-provider")


def test_settings_endpoint_never_persists_or_returns_submitted_api_key(monkeypatch, tmp_path):
    from backend import config
    from backend.agent.schemas import SettingsUpdate
    from backend.api import system

    # Isolate credentials in a temporary .env file rather than touching a developer's config.
    secret_env = tmp_path / ".env"
    monkeypatch.setattr(P, "_dotenv_path", lambda: secret_env)
    state = dict(config.DEFAULT_SETTINGS)
    saved = {}

    monkeypatch.setattr(system.db, "get_settings", lambda: dict(state))
    def save_settings(values):
        saved.update(values)
        state.update(values)
    monkeypatch.setattr(system.db, "save_settings", save_settings)
    monkeypatch.setattr(system.db, "audit", lambda *args, **kwargs: None)

    response = system.put_settings(SettingsUpdate(
        provider="gemini",
        model="gemini-test-model",
        base_url="https://generativelanguage.googleapis.com/v1beta/openai",
        api_key="gemini-secret-test-value",
    ))
    assert response["provider"] == "gemini"
    assert response["model"] == "gemini-test-model"
    assert response["api_key_set"] is True
    assert "api_key" not in response
    assert "gemini-secret-test-value" not in repr(response)
    assert "api_key" not in saved
    assert "gemini-secret-test-value" not in repr(saved)
    assert "GEMINI_API_KEY" in secret_env.read_text(encoding="utf-8")
    assert "gemini-secret-test-value" in secret_env.read_text(encoding="utf-8")


def test_call_json_uses_configured_fallback_after_primary_goes_offline(monkeypatch):
    from backend import config
    from backend.agent import llm

    settings = dict(config.DEFAULT_SETTINGS)
    settings.update({"provider": "openai", "fallback_provider": "ollama", "max_retries": 0})
    monkeypatch.setattr(config, "MOCK_LLM", False)
    monkeypatch.setattr(llm.db, "get_settings", lambda: dict(settings))
    monkeypatch.setattr(llm.context, "check", lambda: None)
    monkeypatch.setattr(llm.context, "progress", lambda *args, **kwargs: None)
    seen = []

    def fake_chat(system, user, model, max_tokens, selected_settings, images=None):
        active = selected_settings["provider"]
        seen.append(active)
        if active == "openai":
            raise P.ProviderError("offline", "test provider offline")
        return '{"issues": []}', {"in": 3, "out": 2}

    monkeypatch.setattr(llm, "_chat", fake_chat)
    data, usage = llm.call_json("vision", "system", "user")
    assert data == {"issues": []}
    assert usage == {"in": 3, "out": 2}
    assert seen == ["openai", "ollama"]

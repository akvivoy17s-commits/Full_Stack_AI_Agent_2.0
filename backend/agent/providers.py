"""LLM provider registry, credential handling and protocol helpers.

API keys are accepted only for environment-variable names defined in KEY_ENV_VARS.
The Settings API may write a key to the private project .env file, but never to
SQLite, logs, generated projects, or API responses.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from urllib.parse import urlparse

# Provider metadata is deliberately code-defined: callers cannot select an arbitrary
# environment-variable name through the settings API.
PROVIDER_REGISTRY: dict[str, dict[str, str | None]] = {
    "ollama": {
        "name": "Ollama",
        "adapter": "ollama",
        "base_url_env": "OLLAMA_BASE_URL",
        "model_env": "OLLAMA_MODEL",
        "key_env_var": None,
        "default_base_url": "http://localhost:11434",
        "default_model": "qwen2.5-coder:7b",
    },
    "openai": {
        "name": "OpenAI / OpenAI-compatible",
        "adapter": "openai_compatible",
        "base_url_env": "OPENAI_BASE_URL",
        "model_env": "OPENAI_MODEL",
        "key_env_var": "OPENAI_API_KEY",
        "default_base_url": "https://api.openai.com/v1",
        "default_model": "gpt-4o-mini",
    },
    "gemini": {
        "name": "Google Gemini",
        "adapter": "openai_compatible",
        "base_url_env": "GEMINI_BASE_URL",
        "model_env": "GEMINI_MODEL",
        "key_env_var": "GEMINI_API_KEY",
        "default_base_url": "https://generativelanguage.googleapis.com/v1beta/openai",
        "default_model": "gemini-3.8-flash",
    },
    "openrouter": {
        "name": "OpenRouter",
        "adapter": "openai_compatible",
        "base_url_env": "OPENROUTER_BASE_URL",
        "model_env": "OPENROUTER_MODEL",
        "key_env_var": "OPENROUTER_API_KEY",
        "default_base_url": "https://openrouter.ai/api/v1",
        "default_model": "openai/gpt-oss-120b",
    },
    "groq": {
        "name": "Groq",
        "adapter": "openai_compatible",
        "base_url_env": "GROQ_BASE_URL",
        "model_env": "GROQ_MODEL",
        "key_env_var": "GROQ_API_KEY",
        "default_base_url": "https://api.groq.com/openai/v1",
        "default_model": "openai/gpt-oss-120b",
    },
    "deepseek": {
        "name": "DeepSeek",
        "adapter": "openai_compatible",
        "base_url_env": "DEEPSEEK_BASE_URL",
        "model_env": "DEEPSEEK_MODEL",
        "key_env_var": "DEEPSEEK_API_KEY",
        "default_base_url": "https://api.deepseek.com",
        "default_model": "deepseek-flash",
    },
    "anthropic": {
        "name": "Anthropic Claude",
        "adapter": "anthropic_messages",
        "base_url_env": "ANTHROPIC_BASE_URL",
        "model_env": "ANTHROPIC_MODEL",
        "key_env_var": "ANTHROPIC_API_KEY",
        "default_base_url": "https://api.anthropic.com/v1",
        "default_model": "claude-sonnet-4-6",
    },
}

# Fixed allowlist. Never build this from request data or allow a request to name an env var.
KEY_ENV_VARS = (
    "LLM_API_KEY",  # compatibility with the previous OpenAI-compatible configuration
    "OPENAI_API_KEY",
    "GEMINI_API_KEY",
    "OPENROUTER_API_KEY",
    "GROQ_API_KEY",
    "DEEPSEEK_API_KEY",
    "ANTHROPIC_API_KEY",
)
PROVIDERS = tuple(PROVIDER_REGISTRY)
RETRYABLE = {"timeout", "rate_limit", "server"}  # auth/model_missing/offline/bad_response fail fast
BACKOFF_BASE, BACKOFF_CAP, HINT_CAP = 1.0, 8.0, 30.0


class ProviderError(RuntimeError):
    """code: offline | model_missing | timeout | bad_response | http | auth | rate_limit | server | no_key | insecure"""

    def __init__(self, code: str, msg: str, retry_after: float | None = None):
        super().__init__(msg)
        self.code = code
        self.retry_after = retry_after


def get_provider(provider: str) -> dict[str, str | None]:
    """Get registry metadata or fail closed for unknown provider names."""
    try:
        return PROVIDER_REGISTRY[provider]
    except (KeyError, TypeError):
        raise ValueError(f"Unsupported LLM provider: {provider}") from None


def provider_settings(settings: dict, provider: str | None = None) -> dict[str, str | None]:
    """Resolve the selected provider's effective URL/model without changing stored settings."""
    provider = provider or str(settings.get("provider", "ollama"))
    meta = get_provider(provider)
    legacy = "openai" if provider == "openai" else provider
    base_url = settings.get(f"{legacy}_base_url") or os.getenv(str(meta["base_url_env"]), "") or meta["default_base_url"]
    model = settings.get(f"{legacy}_model") or os.getenv(str(meta["model_env"]), "") or meta["default_model"]
    return {"id": provider, **meta, "base_url": str(base_url), "model": str(model)}


def api_key(provider: str | None = None) -> str | None:
    """Return only the selected provider's allowlisted key, never an arbitrary env value."""
    provider = provider or os.getenv("LLM_PROVIDER", "ollama")
    meta = PROVIDER_REGISTRY.get(provider)
    key_name = meta.get("key_env_var") if meta else None
    if not key_name:
        return None
    value = os.environ.get(str(key_name), "").strip()
    if value:
        return value
    # Backward compatibility for the old single-key OpenAI-compatible mode only.
    if provider == "openai":
        legacy = os.environ.get("LLM_API_KEY", "").strip()
        return legacy or None
    return None


def api_key_set(provider: str | None = None) -> bool:
    return bool(api_key(provider))


def _dotenv_path() -> Path:
    return Path(__file__).resolve().parents[2] / ".env"


def set_api_key(provider: str, value: str) -> None:
    """Store a key server-side in the ignored .env file and current process environment."""
    meta = get_provider(provider)
    key_name = meta.get("key_env_var")
    if not key_name or str(key_name) not in KEY_ENV_VARS:
        raise ValueError(f"{provider} does not accept an API key")
    value = value.strip()
    if not value:
        raise ValueError("API key cannot be empty")
    if "\n" in value or "\r" in value:
        raise ValueError("API key must be a single line")
    try:
        from dotenv import set_key
        env_path = _dotenv_path()
        env_path.touch(exist_ok=True)
        set_key(str(env_path), str(key_name), value, quote_mode="always")
        try:
            os.chmod(env_path, 0o600)
        except OSError:
            pass  # Windows ACLs govern file access; chmod is best effort there.
    except ImportError:
        # python-dotenv is a project dependency. Fail rather than silently keeping
        # a key only in volatile process memory if it is unexpectedly missing.
        raise RuntimeError("python-dotenv is required to save provider API keys") from None
    os.environ[str(key_name)] = value


def clear_api_key(provider: str) -> None:
    """Remove a provider key from the current process and ignored .env file."""
    meta = get_provider(provider)
    key_name = meta.get("key_env_var")
    if not key_name or str(key_name) not in KEY_ENV_VARS:
        raise ValueError(f"{provider} does not accept an API key")
    names = [str(key_name)]
    if provider == "openai":
        names.append("LLM_API_KEY")
    try:
        from dotenv import unset_key
        env_path = _dotenv_path()
        for name in names:
            if env_path.exists():
                unset_key(str(env_path), name)
            os.environ.pop(name, None)
    except ImportError:
        raise RuntimeError("python-dotenv is required to remove provider API keys") from None


def is_local(url: str) -> bool:
    h = (urlparse(url).hostname or "").lower()
    return h in ("localhost", "127.0.0.1", "::1") or h.endswith(".localhost")


def check_destination(url: str, key: str | None, provider: str = "openai") -> None:
    """Never send a key over plain HTTP to a remote host; remote hosts require a key."""
    meta = PROVIDER_REGISTRY.get(provider, PROVIDER_REGISTRY["openai"])
    key_name = str(meta.get("key_env_var") or "LLM_API_KEY")
    if key and urlparse(url).scheme != "https" and not is_local(url):
        raise ProviderError("insecure", "Refusing to send the API key over plain http to a remote host. Use an https:// URL.")
    if not key and not is_local(url):
        raise ProviderError("no_key", f"No API key found. Set {key_name} in the backend environment or Settings.")


def auth_headers(key: str | None) -> dict:
    return {"Authorization": f"Bearer {key}"} if key else {}


def anthropic_headers(key: str | None) -> dict:
    headers = {"anthropic-version": "2023-06-01", "content-type": "application/json"}
    if key:
        headers["x-api-key"] = key
    return headers


def parse_retry_after(v) -> float | None:
    try:
        return max(0.0, float(v))
    except (TypeError, ValueError):
        return None


def classify_http(status: int, text: str, retry_after: float | None = None) -> ProviderError:
    t = (text or "")[:200]
    if status in (401, 403):
        return ProviderError("auth", f"API key rejected (HTTP {status}). Check the selected provider key in backend Settings/environment.")
    if status == 404:
        return ProviderError("model_missing", f"Model or endpoint not found (HTTP 404): {t}")
    if status == 408:
        return ProviderError("timeout", "Provider timed out (HTTP 408)", retry_after)
    if status == 429:
        return ProviderError("rate_limit", f"Rate limited (HTTP 429): {t}", retry_after)
    if status >= 500:
        return ProviderError("server", f"Provider error (HTTP {status}): {t}", retry_after)
    return ProviderError("http", f"Provider returned HTTP {status}: {t}")


def openai_body(system: str, user: str, model: str, max_tokens: int, s: dict,
                images: list[str] | None = None, base_url: str | None = None) -> dict:
    content = user if not images else [{"type": "text", "text": user}] + [
        {"type": "image_url", "image_url": {"url": "data:image/png;base64," + i}} for i in images]
    base = base_url or s.get("openai_base_url", "https://api.openai.com/v1")
    official = (urlparse(base).hostname or "") == "api.openai.com"
    body = {"model": model, "stream": True, "stream_options": {"include_usage": True},
            "response_format": {"type": "json_object"},
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": content}]}
    body["max_completion_tokens" if official else "max_tokens"] = max_tokens
    if not official:  # some official models reject non-default temperature
        body["temperature"] = 0.2
    return body


def anthropic_body(system: str, user: str, model: str, max_tokens: int,
                   images: list[str] | None = None) -> dict:
    content: str | list[dict] = user
    if images:
        content = [{"type": "text", "text": user}] + [
            {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": image}}
            for image in images
        ]
    # Claude's Messages API has no OpenAI-style response_format; the shared parser
    # validates JSON and the common repair prompt retries invalid model output.
    return {"model": model, "max_tokens": max_tokens, "stream": True,
            "system": system, "messages": [{"role": "user", "content": content}]}


def parse_sse(line):
    """-> None (ignore) | (text, (in, out) | None, done: bool)."""
    if not line or not line.startswith("data:"):
        return None
    p = line[5:].strip()
    if p == "[DONE]":
        return "", None, True
    try:
        d = json.loads(p)
    except ValueError:
        return None
    if not isinstance(d, dict):
        return None
    if d.get("error"):
        e = d["error"]
        raise ProviderError("http", str(e.get("message") if isinstance(e, dict) else e)[:200])
    text = "".join(((c.get("delta") or {}).get("content") or "") for c in d.get("choices") or [] if isinstance(c, dict))
    u = d.get("usage")
    usage = (int(u.get("prompt_tokens") or 0), int(u.get("completion_tokens") or 0)) if isinstance(u, dict) else None
    return text, usage, False


def parse_anthropic_event(event: str, payload: str):
    """Parse one Anthropic Messages SSE event into (text, usage, done)."""
    if not payload or payload == "[DONE]":
        return "", None, payload == "[DONE]"
    try:
        data = json.loads(payload)
    except ValueError:
        return "", None, False
    if not isinstance(data, dict):
        return "", None, False
    if event == "error" or data.get("type") == "error":
        err = data.get("error") or {}
        message = err.get("message", "Anthropic returned an error") if isinstance(err, dict) else str(err)
        raise ProviderError("http", str(message)[:200])
    if event == "message_start":
        usage = data.get("message", {}).get("usage", {})
        return "", (int(usage.get("input_tokens") or 0), 0), False
    if event == "content_block_delta":
        delta = data.get("delta") or {}
        return (str(delta.get("text") or "") if delta.get("type") == "text_delta" else ""), None, False
    if event == "message_delta":
        usage = data.get("usage") or {}
        return "", (0, int(usage.get("output_tokens") or 0)), False
    if event == "message_stop":
        return "", None, True
    return "", None, False


def backoff(n: int, hint: float | None = None) -> float:
    """Delay before retry #n (1-based): server hint (capped) or exponential, always bounded."""
    if hint is not None:
        return min(hint, HINT_CAP)
    return min(BACKOFF_CAP, BACKOFF_BASE * 2 ** (n - 1))


def with_retries(fn, attempts: int = 3, *, sleep=time.sleep, check=None, on_retry=None):
    """Run fn(); retry only transient ProviderErrors, at most `attempts` calls total."""
    attempts = max(1, attempts)
    for n in range(1, attempts + 1):
        if check:
            check()
        try:
            return fn()
        except ProviderError as e:
            if e.code not in RETRYABLE or n >= attempts:
                raise
            delay = backoff(n, e.retry_after)
            if on_retry:
                on_retry(n, attempts, e, delay)
            left = delay
            while left > 0:
                step = min(0.25, left)
                sleep(step)
                left -= step
                if check:
                    check()

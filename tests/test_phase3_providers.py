"""Upgrade phase 3: provider system (Ollama + OpenAI-compatible), bounded retries, env-only keys."""
import json

import httpx
import pytest

from backend import config
from backend.agent import llm, providers as P

OPENAI = dict(config.DEFAULT_SETTINGS, provider="openai", openai_base_url="https://api.example.com/v1", openai_model="m1", max_retries=2)


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr(llm.db, "get_settings", lambda: dict(OPENAI))
    monkeypatch.setattr(llm.config, "MOCK_LLM", False)       # conftest turns the mock on globally; these tests exercise the real provider path


# ---- keys + destination safety
def test_key_from_env_only(monkeypatch):
    assert P.api_key("openai") is None
    monkeypatch.setenv("LLM_API_KEY", " legacy ")
    assert P.api_key("openai") == "legacy"             # legacy single-key mode still works for openai
    monkeypatch.setenv("OPENAI_API_KEY", " sk-abc ")
    assert P.api_key("openai") == "sk-abc"             # the provider's own allowlisted variable wins
    assert P.api_key("ollama") is None                 # providers without a key variable never read the environment


def test_key_never_a_setting_or_in_status(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "sk-secret-value-123456")
    from backend.agent.schemas import SettingsUpdate
    assert SettingsUpdate.model_fields["api_key"].repr is False        # write-only: accepted on PUT, never echoed back
    assert "key" not in "".join(config.DEFAULT_SETTINGS)               # never persisted in the SQLite settings
    monkeypatch.setattr(httpx, "get", lambda *a, **k: type("R", (), {"status_code": 200, "raise_for_status": lambda s: None,
                                                                   "json": lambda s: {"data": [{"id": "m1"}]}})())
    st = llm.status()
    assert st["api_key_set"] is True and "sk-secret" not in json.dumps(st)


def test_destination_rules():
    with pytest.raises(P.ProviderError) as e:
        P.check_destination("https://api.example.com/v1", None)
    assert e.value.code == "no_key"
    with pytest.raises(P.ProviderError) as e:
        P.check_destination("http://api.example.com/v1", "k")
    assert e.value.code == "insecure"
    P.check_destination("http://localhost:1234/v1", None)      # local servers need no key
    P.check_destination("https://api.example.com/v1", "k")


# ---- classification + retry
@pytest.mark.parametrize("status,code", [(401, "auth"), (403, "auth"), (404, "model_missing"), (429, "rate_limit"), (503, "server"), (400, "http")])
def test_classify(status, code):
    assert P.classify_http(status, "x").code == code


def test_retry_only_transient_and_bounded():
    calls, sleeps = [], []

    def flaky():
        calls.append(1)
        raise P.ProviderError("rate_limit", "429")
    with pytest.raises(P.ProviderError):
        P.with_retries(flaky, 3, sleep=sleeps.append)
    assert len(calls) == 3 and round(sum(sleeps), 2) == 3.0       # 1s + 2s backoff

    calls.clear()

    def auth():
        calls.append(1)
        raise P.ProviderError("auth", "bad key")
    with pytest.raises(P.ProviderError):
        P.with_retries(auth, 3, sleep=lambda s: None)
    assert len(calls) == 1                                          # never retried


def test_retry_after_hint_capped_and_recovers():
    seq = iter([P.ProviderError("server", "x", retry_after=999), "ok"])

    def fn():
        v = next(seq)
        if isinstance(v, Exception):
            raise v
        return v
    sleeps = []
    assert P.with_retries(fn, 3, sleep=sleeps.append) == "ok"
    assert round(sum(sleeps), 1) == P.HINT_CAP


def test_cancel_during_backoff():
    class Stop(Exception):
        pass

    def check():
        raise Stop
    with pytest.raises(Stop):
        P.with_retries(lambda: 1, 3, check=check)


# ---- request body + SSE
def test_openai_body_variants():
    b = P.openai_body("sys", "usr", "m", 100, dict(OPENAI, openai_base_url="https://api.openai.com/v1"), ["QUJD"])
    assert b["max_completion_tokens"] == 100 and "temperature" not in b and b["response_format"] == {"type": "json_object"}
    assert b["messages"][1]["content"][1]["image_url"]["url"].startswith("data:image/png;base64,")
    b2 = P.openai_body("s", "u", "m", 50, OPENAI)
    assert b2["max_tokens"] == 50 and b2["temperature"] == 0.2 and b2["messages"][1]["content"] == "u"


def test_parse_sse():
    assert P.parse_sse("") is None and P.parse_sse(": keepalive") is None and P.parse_sse("data: not-json") is None
    assert P.parse_sse('data: {"choices":[{"delta":{"content":"hi"}}]}') == ("hi", None, False)
    assert P.parse_sse('data: {"choices":[],"usage":{"prompt_tokens":3,"completion_tokens":4}}') == ("", (3, 4), False)
    assert P.parse_sse("data: [DONE]")[2] is True
    with pytest.raises(P.ProviderError):
        P.parse_sse('data: {"error":{"message":"boom"}}')


# ---- llm integration (mocked transport)
class FakeStream:
    def __init__(self, status=200, lines=(), headers=None, text=""):
        self.status_code, self._lines, self.headers, self.text = status, lines, headers or {}, text

    def __enter__(self): return self
    def __exit__(self, *a): return False
    def read(self): pass
    def iter_lines(self): return iter(self._lines)


def _sse(*chunks):
    return [f"data: {json.dumps({'choices': [{'delta': {'content': c}}]})}" for c in chunks] + [
        'data: {"choices":[],"usage":{"prompt_tokens":5,"completion_tokens":7}}', "data: [DONE]"]


def test_openai_stream_end_to_end(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "k")
    seen = {}

    def stream(method, url, json=None, headers=None, timeout=None):
        seen.update(url=url, headers=headers, body=json)
        return FakeStream(lines=_sse('{"a":', ' 1}'))
    monkeypatch.setattr(httpx, "stream", stream)
    data, usage = llm.call_json("t", "sys", "usr")
    assert data == {"a": 1} and usage == {"in": 5, "out": 7}
    assert seen["url"].endswith("/chat/completions") and seen["headers"]["Authorization"] == "Bearer k" and seen["body"]["model"] == "m1"


def test_call_json_retries_429_then_succeeds(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "k")
    monkeypatch.setattr(P.time, "sleep", lambda s: None)
    replies = iter([FakeStream(429, headers={"retry-after": "1"}, text="slow down"), FakeStream(lines=_sse('{"ok": true}'))])
    monkeypatch.setattr(httpx, "stream", lambda *a, **k: next(replies))
    assert llm.call_json("t", "s", "u")[0] == {"ok": True}


def test_auth_error_not_retried_and_key_redacted(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "sk-supersecretkey-0123456789")
    n = []
    monkeypatch.setattr(httpx, "stream", lambda *a, **k: (n.append(1), FakeStream(401, text="bad sk-supersecretkey-0123456789"))[1])
    with pytest.raises(llm.OllamaError) as e:
        llm.call_json("t", "s", "u")
    assert e.value.code == "auth" and len(n) == 1 and "supersecret" not in str(e.value)


def test_missing_key_fails_fast_without_network(monkeypatch):
    monkeypatch.setattr(httpx, "stream", lambda *a, **k: pytest.fail("must not call network"))
    with pytest.raises(llm.OllamaError) as e:
        llm.call_json("t", "s", "u")
    assert e.value.code == "no_key"


def test_ollama_provider_still_dispatches(monkeypatch):
    monkeypatch.setattr(llm.db, "get_settings", lambda: dict(config.DEFAULT_SETTINGS, provider="ollama"))
    seen = []
    monkeypatch.setattr(llm, "_chat_ollama", lambda *a, **k: (seen.append(a[2]) or '{"x": 1}', {"in": 1, "out": 1}))
    assert llm.call_json("t", "s", "u")[0] == {"x": 1} and seen == [config.DEFAULT_SETTINGS["ollama_model"]]

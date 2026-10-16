"""Registry-routed LLM client for Ollama, OpenAI-compatible services, and native Anthropic Messages API.
Streams are cancellable; JSON is validated; transient errors use bounded retries and an optional configured
fallback provider. API keys remain server-side and are never stored in SQLite or returned by the API."""
import json
import re
import time

import httpx
from pydantic import BaseModel, ValidationError

from backend import config
from backend.agent import context
from backend.agent import providers as P
from backend.storage import db
from backend.tools.redact import redact

OllamaError = P.ProviderError   # historic name kept: callers catch llm.OllamaError (covers every provider)


OUTPUT_TOKEN_BUDGETS = {
    "fast": {"blueprint": 900, "section": 1500, "repair": 650, "vision": 400},
    "balanced": {"blueprint": 1200, "section": 1900, "repair": 900, "vision": 400},
    "quality": {"blueprint": 1200, "section": 2500, "repair": 1200, "vision": 500},
}


def effective_output_budget(kind: str, requested: int | None, profile: str = "fast") -> int:
    """Bound completions for CPU-friendly profiles without changing validation or skipping checks."""
    base = requested or config.MAX_OUT_TOKENS
    cap = OUTPUT_TOKEN_BUDGETS.get(profile, OUTPUT_TOKEN_BUDGETS["fast"]).get(kind)
    return min(base, cap) if cap else base


def parse_json(text: str) -> dict:
    t = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()
    i, j = t.find("{"), t.rfind("}")
    if i < 0 or j < 0:
        raise ValueError("no JSON in reply")
    return json.loads(t[i:j + 1])


def _has_model(name: str, models: list[str]) -> bool:
    base = name if ":" in name else name + ":latest"
    return name in models or base in models


def status(base_url: str | None = None, model: str | None = None, provider: str | None = None) -> dict:
    """Check the selected registered provider without ever returning credentials."""
    s = db.get_settings()
    pid = provider or s.get("provider", "ollama")
    try:
        resolved = P.provider_settings(s, pid)
    except ValueError as e:
        return {"provider": pid, "reachable": False, "model_available": False,
                "models": [], "api_key_set": False, "error": str(e)}
    url = (base_url or resolved["base_url"] or "").rstrip("/")
    selected_model = model or resolved["model"]
    adapter = resolved["adapter"]
    if adapter == "ollama":
        out = _status_ollama(s, url, str(selected_model))
        return {"provider": pid, "adapter": adapter, "api_key_set": False, **out}
    if adapter == "anthropic_messages":
        return _status_anthropic(s, pid, url, str(selected_model))
    return _status_compatible(s, pid, url, str(selected_model))


def _status_compatible(s: dict, provider: str, url: str, model: str) -> dict:
    key, vision = P.api_key(provider), s.get("vision_model", "")
    out = {"provider": provider, "adapter": "openai_compatible", "reachable": False,
           "base_url": url, "model": model, "model_available": False,
           "vision_model": vision, "vision_available": False, "models": [], "error": None,
           "api_key_set": bool(key), "model_check": "unverified"}
    try:
        P.check_destination(url, key, provider)
        r = httpx.get(url + "/models", headers=P.auth_headers(key), timeout=5.0)
        if r.status_code in (401, 403):
            out["reachable"] = True
            raise P.classify_http(r.status_code, "")
        if r.status_code == 404:  # some compatible servers do not expose a model-list route
            out.update(reachable=True, model_available=True, vision_available=bool(vision))
            return out
        r.raise_for_status()
        payload = r.json()
        out["models"] = [m.get("id", "") for m in payload.get("data", []) if isinstance(m, dict)]
        out.update(reachable=True, model_check="listed", model_available=model in out["models"],
                   vision_available=bool(vision) and vision in out["models"])
        if not out["model_available"]:
            out["error"] = f"Model '{model}' is not available at {url}. Choose a model listed by this provider."
    except P.ProviderError as e:
        out["error"] = redact(e)
    except httpx.HTTPStatusError as e:
        out["error"] = f"Provider returned HTTP {e.response.status_code} at {url}"
    except (httpx.HTTPError, ValueError) as e:
        out["error"] = f"Provider is not reachable at {url} ({type(e).__name__})"
    return out


def _status_anthropic(s: dict, provider: str, url: str, model: str) -> dict:
    key = P.api_key(provider)
    out = {"provider": provider, "adapter": "anthropic_messages", "reachable": False,
           "base_url": url, "model": model, "model_available": False,
           "vision_model": "", "vision_available": False, "models": [], "error": None,
           "api_key_set": bool(key), "model_check": "unverified"}
    try:
        P.check_destination(url, key, provider)
        r = httpx.get(url + "/models", headers=P.anthropic_headers(key), timeout=5.0)
        if r.status_code in (401, 403):
            out["reachable"] = True
            raise P.classify_http(r.status_code, "")
        if r.status_code == 404:
            out.update(reachable=True, model_available=True)
            return out
        r.raise_for_status()
        payload = r.json()
        out["models"] = [m.get("id", "") for m in payload.get("data", []) if isinstance(m, dict)]
        out.update(reachable=True, model_check="listed", model_available=model in out["models"])
        if not out["model_available"]:
            out["error"] = f"Model '{model}' is not available at {url}. Choose a model listed by Anthropic."
    except P.ProviderError as e:
        out["error"] = redact(e)
    except httpx.HTTPStatusError as e:
        out["error"] = f"Provider returned HTTP {e.response.status_code} at {url}"
    except (httpx.HTTPError, ValueError) as e:
        out["error"] = f"Provider is not reachable at {url} ({type(e).__name__})"
    return out


def _status_ollama(s: dict, base_url: str, model: str) -> dict:
    url = base_url.rstrip("/")
    vision = s.get("vision_model", "")
    out = {"reachable": False, "base_url": url, "model": model, "model_available": False,
           "vision_model": vision, "vision_available": False, "models": [], "error": None,
           "model_check": "listed"}
    try:
        r = httpx.get(url + "/api/tags", timeout=3.0)
        r.raise_for_status()
        out["models"] = [m.get("name", "") for m in r.json().get("models", [])]
        out["reachable"] = True
        out["model_available"] = _has_model(model, out["models"])
        out["vision_available"] = bool(vision) and _has_model(vision, out["models"])
        if not out["model_available"]:
            out["error"] = f"Model '{model}' is not installed. Run: ollama pull {model}"
    except httpx.HTTPError as e:
        out["error"] = f"Ollama is not reachable at {url} ({type(e).__name__}). Start it with: ollama serve"
    return out

def _chat_ollama(system: str, user: str, model: str, max_tokens: int, s: dict, images: list[str] | None = None) -> tuple[str, dict]:
    url = s["ollama_base_url"].rstrip("/") + "/api/chat"
    body = {"model": model, "stream": True, "format": "json", "keep_alive": s.get("ollama_keep_alive", "30m"),
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user, **({"images": images} if images else {})}],
            "options": {"num_predict": max_tokens, "num_ctx": s["num_ctx"], "temperature": 0.2}}
    deadline = time.monotonic() + s["timeout_s"]
    parts, usage = [], {"in": 0, "out": 0}
    try:
        with httpx.stream("POST", url, json=body, timeout=httpx.Timeout(connect=5, read=60, write=30, pool=5)) as r:
            if r.status_code == 404:
                raise OllamaError("model_missing", f"Model '{model}' not found. Run: ollama pull {model}")
            if r.status_code != 200:
                r.read()
                raise P.classify_http(r.status_code, r.text[:200], P.parse_retry_after(r.headers.get("retry-after")))
            for line in r.iter_lines():
                context.check()                                    # cancel between chunks
                if time.monotonic() > deadline:
                    raise OllamaError("timeout", f"Generation exceeded {s['timeout_s']}s")
                if not line:
                    continue
                d = json.loads(line)
                if d.get("error"):
                    raise OllamaError("http", str(d["error"])[:200])
                parts.append(d.get("message", {}).get("content", ""))
                if d.get("done"):
                    usage = {"in": d.get("prompt_eval_count", 0), "out": d.get("eval_count", 0)}
    except httpx.ConnectError:
        raise OllamaError("offline", f"Ollama is not reachable at {s['ollama_base_url']}. Start it with: ollama serve")
    except httpx.TimeoutException:
        raise OllamaError("timeout", "Ollama stopped responding (model may still be loading or the machine is overloaded)")
    except httpx.TransportError as e:
        raise OllamaError("server", f"Connection to Ollama dropped ({type(e).__name__})")
    return "".join(parts), usage


def _chat_openai(system: str, user: str, model: str, max_tokens: int, s: dict,
                 images: list[str] | None = None, *, provider: str = "openai",
                 base_url: str | None = None) -> tuple[str, dict]:
    """OpenAI Chat Completions protocol; works with OpenAI and compatible providers."""
    resolved = P.provider_settings(s, provider)
    base, key = (base_url or resolved["base_url"] or "").rstrip("/"), P.api_key(provider)
    P.check_destination(base, key, provider)
    body = P.openai_body(system, user, model, max_tokens, s, images, base_url=base)
    deadline = time.monotonic() + s["timeout_s"]
    parts, usage = [], {"in": 0, "out": 0}
    try:
        with httpx.stream("POST", base + "/chat/completions", json=body, headers=P.auth_headers(key),
                          timeout=httpx.Timeout(connect=5, read=60, write=30, pool=5)) as r:
            if r.status_code != 200:
                r.read()
                raise P.classify_http(r.status_code, redact(r.text), P.parse_retry_after(r.headers.get("retry-after")))
            for line in r.iter_lines():
                context.check()
                if time.monotonic() > deadline:
                    raise OllamaError("timeout", f"Generation exceeded {s['timeout_s']}s")
                ev = P.parse_sse(line)
                if not ev:
                    continue
                text, u, done = ev
                if text:
                    parts.append(text)
                if u:
                    usage = {"in": u[0], "out": u[1]}
                if done:
                    break
    except OllamaError as e:
        raise OllamaError(e.code, redact(e), e.retry_after) from None
    except httpx.ConnectError:
        raise OllamaError("offline", f"Provider '{provider}' is not reachable at {base}")
    except httpx.TimeoutException:
        raise OllamaError("timeout", "Provider stopped responding")
    except httpx.TransportError as e:
        raise OllamaError("server", f"Connection to provider dropped ({type(e).__name__})")
    return "".join(parts), usage


def _chat_anthropic(system: str, user: str, model: str, max_tokens: int, s: dict,
                    images: list[str] | None = None, *, base_url: str | None = None) -> tuple[str, dict]:
    """Native Anthropic Messages API adapter (SSE event stream, not OpenAI-compatible)."""
    provider = "anthropic"
    resolved = P.provider_settings(s, provider)
    base, key = (base_url or resolved["base_url"] or "").rstrip("/"), P.api_key(provider)
    P.check_destination(base, key, provider)
    body = P.anthropic_body(system, user, model, max_tokens, images)
    deadline = time.monotonic() + s["timeout_s"]
    parts, usage = [], {"in": 0, "out": 0}
    current_event = ""
    try:
        with httpx.stream("POST", base + "/messages", json=body, headers=P.anthropic_headers(key),
                          timeout=httpx.Timeout(connect=5, read=60, write=30, pool=5)) as r:
            if r.status_code != 200:
                r.read()
                raise P.classify_http(r.status_code, redact(r.text), P.parse_retry_after(r.headers.get("retry-after")))
            for line in r.iter_lines():
                context.check()
                if time.monotonic() > deadline:
                    raise OllamaError("timeout", f"Generation exceeded {s['timeout_s']}s")
                if not line:
                    current_event = ""
                    continue
                if line.startswith("event:"):
                    current_event = line[6:].strip()
                    continue
                if not line.startswith("data:"):
                    continue
                text, u, done = P.parse_anthropic_event(current_event, line[5:].strip())
                if text:
                    parts.append(text)
                if u:
                    usage["in"] = max(usage["in"], u[0])
                    usage["out"] = max(usage["out"], u[1])
                if done:
                    break
    except OllamaError as e:
        raise OllamaError(e.code, redact(e), e.retry_after) from None
    except httpx.ConnectError:
        raise OllamaError("offline", f"Anthropic endpoint is not reachable at {base}")
    except httpx.TimeoutException:
        raise OllamaError("timeout", "Anthropic stopped responding")
    except httpx.TransportError as e:
        raise OllamaError("server", f"Connection to Anthropic dropped ({type(e).__name__})")
    return "".join(parts), usage


def _chat(system: str, user: str, model: str, max_tokens: int, s: dict,
          images: list[str] | None = None) -> tuple[str, dict]:
    pid = str(s.get("provider", "ollama"))
    resolved = P.provider_settings(s, pid)
    adapter = resolved["adapter"]
    if adapter == "ollama":
        local_settings = {**s, "ollama_base_url": resolved["base_url"]}
        return _chat_ollama(system, user, model, max_tokens, local_settings, images) if images else _chat_ollama(system, user, model, max_tokens, local_settings)
    if adapter == "anthropic_messages":
        return _chat_anthropic(system, user, model, max_tokens, s, images, base_url=resolved["base_url"])
    return _chat_openai(system, user, model, max_tokens, s, images, provider=pid, base_url=resolved["base_url"])

def call_json(kind: str, system: str, user: str, model: str | None = None, max_tokens: int | None = None,
              schema: type[BaseModel] | None = None, images: list[str] | None = None):
    """Returns (data: dict, usage: {'in','out'}). Transient transport errors are retried (bounded); one retry on invalid JSON / schema mismatch."""
    context.check()
    if config.MOCK_LLM:
        data = _mock(kind, user)
        return (schema.model_validate(data).model_dump() if schema else data), {"in": 0, "out": 0}
    s = db.get_settings()
    max_tokens = effective_output_budget(kind, max_tokens, s.get("generation_profile", "fast"))
    primary_provider = str(s.get("provider", "ollama"))
    model = model or P.provider_settings(s, primary_provider)["model"]
    fallback_provider = str(s.get("fallback_provider", "") or "")
    if fallback_provider not in P.PROVIDER_REGISTRY or fallback_provider == primary_provider:
        fallback_provider = ""
    attempts = 1 + int(s.get("max_retries", 2))
    usage, msg = {"in": 0, "out": 0}, user

    def note(n, total, e, delay):
        context.progress("llm", f"{kind}: {e.code}, retry {n}/{total - 1} in {delay:.0f}s", "warn")

    for attempt in range(2):
        context.progress("llm", f"{kind}: asking {model}" + (" (retry)" if attempt else ""))
        token_budget = max_tokens or config.MAX_OUT_TOKENS
        started = time.monotonic()

        def generate(selected_settings, selected_model):
            args = (system, msg, selected_model, token_budget, selected_settings)
            return P.with_retries(lambda: _chat(*args, images) if images else _chat(*args), attempts,
                                  check=context.check, on_retry=note)

        try:
            text, u = generate(s, model)
            active_model = model
        except P.ProviderError as primary_error:
            fallback_codes = P.RETRYABLE | {"offline", "model_missing", "no_key"}
            if not fallback_provider or primary_error.code not in fallback_codes:
                raise
            fallback_settings = {**s, "provider": fallback_provider}
            fallback_model = P.provider_settings(fallback_settings, fallback_provider)["model"]
            context.progress("llm", f"{primary_provider} unavailable ({primary_error.code}); trying configured fallback {fallback_provider}", "warn")
            try:
                text, u = generate(fallback_settings, fallback_model)
                active_model = fallback_model
            except P.ProviderError as fallback_error:
                raise OllamaError(fallback_error.code,
                                  f"Primary provider '{primary_provider}' failed ({primary_error.code}); configured fallback '{fallback_provider}' also failed: {redact(fallback_error)}",
                                  fallback_error.retry_after) from None

        elapsed = max(0.001, time.monotonic() - started)
        usage["in"] += u["in"]
        usage["out"] += u["out"]
        context.progress("llm", f"{kind}: {u['out']} output tokens in {elapsed:.1f}s ({u['out'] / elapsed:.1f} tok/s) via {active_model}")
        try:
            data = parse_json(text)
            if schema:
                data = schema.model_validate(data).model_dump()
            return data, usage
        except (ValueError, ValidationError) as e:
            msg = user + f"\nYour last reply was invalid ({str(e)[:120]}). Return ONLY valid JSON matching the format."
    raise OllamaError("bad_response", f"{kind}: model did not return valid JSON")


def _mock(kind: str, user: str) -> dict:
    if kind == "blueprint":
        return {"brand": "Mockly", "stack": "html", "sections": ["hero", "features", "showcase", "pricing", "cta"],
                "pages": ["index"], "notes": "mock",
                "design": {"colors": {"bg": "#0b0b14", "fg": "#f5f5ff", "primary": "#7c5cff",
                                      "accent": "#00d4ff", "muted": "#9a9ab5"},
                           "fonts": {"head": "Poppins", "body": "Inter"}, "radius": 16, "spacing": 8,
                           "style": "dark glass neon"},
                "motion": {"hero": "fade-up", "scroll": "reveal", "hover": "lift", "lib": "css",
                           "duration_ms": [250, 700], "easing": "cubic-bezier(.22,1,.36,1)"}}
    if kind == "section":
        sid = re.search(r"SECTION: ([a-z0-9-]+)", user).group(1)
        return {"html": f'<section id="{sid}" class="sec"><div class="wrap"><h2 class="reveal">{sid.title()}</h2>'
                        f'<p class="reveal" data-delay="1">Mock content</p>'
                        f'<script>alert(1)</script><a onclick="x()" class="btn">Go</a></div></section>',
                "css": f"#{sid}{{padding:96px 0}}"}
    if kind == "vision":
        return {"issues": []}
    if kind == "repair":
        return {"patches": []}              # forces the regenerate fallback in mock mode
    raise ValueError(kind)

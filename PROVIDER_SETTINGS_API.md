# Multi-provider LLM settings (Phase 1 backend contract)

Phase 1 now routes model calls through `backend/agent/providers.py`. The registry defines each provider's display name, adapter, default base URL/model, and the one allowed environment-variable name used for its API key.

Supported provider IDs:

| ID | Adapter | Key environment variable |
|---|---|---|
| `ollama` | Ollama `/api/chat` | Not required |
| `openai` | OpenAI-compatible Chat Completions | `OPENAI_API_KEY` (legacy `LLM_API_KEY` is still accepted for this provider) |
| `gemini` | OpenAI-compatible Chat Completions | `GEMINI_API_KEY` |
| `openrouter` | OpenAI-compatible Chat Completions | `OPENROUTER_API_KEY` |
| `groq` | OpenAI-compatible Chat Completions | `GROQ_API_KEY` |
| `deepseek` | OpenAI-compatible Chat Completions | `DEEPSEEK_API_KEY` |
| `anthropic` | Native Anthropic Messages API | `ANTHROPIC_API_KEY` |

## Settings and model-list endpoints

`GET /providers` returns the provider catalog, the selected provider, each provider's model/base URL, and a boolean `api_key_set`; it never returns a key. `GET /providers/{provider}/models` attempts to query the provider's model-list endpoint and returns model IDs. If that provider or endpoint is not reachable, the route returns HTTP 503 with an error detail.

`GET /settings` includes the current `provider`, active `model`, active `base_url`, selected adapter, per-provider model/base-URL settings, the provider catalog and `api_key_set`. It never returns `api_key`.

`PUT /settings` accepts the active `provider`, `model`, `base_url`, optional `api_key`, and optional `clear_api_key`. Example body:

```json
{
  "provider": "gemini",
  "model": "gemini-3.8-flash",
  "base_url": "https://generativelanguage.googleapis.com/v1beta/openai",
  "api_key": "paste-key-here"
}
```

The sample value above is a placeholder, not a real credential. A submitted key is written only to the ignored server-side `.env` file and the running backend process environment; it is excluded from SQLite settings, audit details, logs, and API responses. `clear_api_key: true` removes the key for the selected provider. Only environment variable names in `KEY_ENV_VARS` can be targeted; clients cannot choose arbitrary environment variable names. Remote providers require HTTPS and an API key, and sending a key to a remote plain-HTTP endpoint is blocked.

## Provider fallback

`LLM_FALLBACK_PROVIDER` may be set to another supported provider ID, for example `ollama`. Leave it empty to disable fallback. When enabled, the agent retries transient failures against the primary provider, then attempts the explicitly configured fallback for transient/offline/model-missing/no-key failures. Fallback does not occur for authentication rejection, invalid endpoint security, or bad JSON; those errors remain visible rather than being hidden.

## Frontend integration (Phase 3)

The Settings dialog can populate its provider dropdown from `GET /providers`, model choices from `GET /providers/{provider}/models`, and edit model/base URL/key through `PUT /settings`. Send the key only when the user submits the form; do not put it in browser local storage or display it again after save. Use `api_key_set` to show whether a key is configured. Keep existing destination-check UX by calling `POST /ollama/check` with `{ "provider": "...", "base_url": "...", "model": "..." }` before saving if desired.

# Upgrade progress (8 phases, approval gate after each)

| # | Phase | Status |
|---|-------|--------|
| 1 | Audit + file-tool/endpoint security hardening | DONE (merged) |
| 2 | Command runner: allowlisted python/pytest/lint/go/etc. checks | DONE (merged) |
| 3 | Provider registry: Ollama, OpenAI-compatible cloud providers + native Anthropic; retries/fallback | DONE (merged) |
| 4 | Planner: requirement analysis, task execution, progress tracking | DONE (merged) |
| 5 | Repo understanding + persistent task memory (token-cheap) | DONE (merged) |
| 6 | Bounded self-repair loop (fingerprinting, no repeat attempts) | DONE (merged) |
| 7 | Frontend integration + end-to-end generator checks | DONE (merged) |
| 8 | Final verification + PASS/PARTIAL/BLOCKED/FAIL report | DONE (see PHASE8_REPORT.md) |

## Phase 1 findings / changes
- Baseline before changes: 234 passed, 7 skipped.
- FIXED: GET /projects/{pid}/file could read `.agent/*` internal state and any secret file; /preview could serve `.env`/keys from the project root.
- FIXED: ProjectFiles now refuses secret files (.env*, keys, .npmrc...; `.env.example` allowed), writes into node_modules/.git, and reads over MAX_FILE_BYTES.
- FIXED: tree() walked all of node_modules before filtering; now prunes ignored dirs, hides secrets, capped at 2000 entries.
- Added tests/test_phase1_hardening.py.
- Noted for later phases: terminal allowlist is JS/TS only (no python/pytest/lint checks) -> Phase 2; LLM client is Ollama-only with one JSON retry -> Phase 3.

## Phase 2 changes
- terminal.py allowlist extended with exact shapes: python (-m py_compile / compileall / pytest / ruff check), npm run lint|test, npm test, go build|vet|test ./..., mvn -q -B compile|test, dotnet build|test.
- Argument validation: no traversal, absolute paths, option injection; pytest only accepts `-p no:cacheprovider` (blocks `-p <plugin>` code loading).
- Child env scrubbed of key/token/secret/password/auth variables; output passed through redact().
- New `detect_checks(root)` -> list of checks that apply to a project (used by Phase 6 self-repair).
- Not verified here: go / mvn / dotnet / ruff execution (tools not installed in this environment) — only allowlist logic tested for those.
- Tests: 280 passed, 7 skipped (new: tests/test_phase2_runner.py, 31 tests incl. real py_compile + pytest runs).

---

# Upgrade progress (8 phases, approval gate after each)

| # | Phase | Status |
|---|-------|--------|
| 1 | Audit + file-tool/endpoint security hardening | DONE (merged) |
| 2 | Command runner: allowlisted python/pytest/lint/go/etc. checks | DONE (merged) |
| 3 | Provider registry: Ollama, OpenAI-compatible cloud providers + native Anthropic; retries/fallback | DONE (merged) |
| 4 | Planner: requirement analysis, task execution, progress tracking | DONE (merged) |
| 5 | Repo understanding + persistent task memory (token-cheap) | DONE (merged) |
| 6 | Bounded self-repair loop (fingerprinting, no repeat attempts) | DONE (merged) |
| 7 | Frontend integration + end-to-end generator checks | DONE (merged) |
| 8 | Final verification + PASS/PARTIAL/BLOCKED/FAIL report | DONE (see PHASE8_REPORT.md) |

## Phase 1 findings / changes
- Baseline before changes: 234 passed, 7 skipped.
- FIXED: GET /projects/{pid}/file could read `.agent/*` internal state and any secret file; /preview could serve `.env`/keys from the project root.
- FIXED: ProjectFiles now refuses secret files (.env*, keys, .npmrc...; `.env.example` allowed), writes into node_modules/.git, and reads over MAX_FILE_BYTES.
- FIXED: tree() walked all of node_modules before filtering; now prunes ignored dirs, hides secrets, capped at 2000 entries.
- Added tests/test_phase1_hardening.py.
- Noted for later phases: terminal allowlist is JS/TS only (no python/pytest/lint checks) -> Phase 2; LLM client is Ollama-only with one JSON retry -> Phase 3.

## Phase 2 changes
- terminal.py allowlist extended with exact shapes: python (-m py_compile / compileall / pytest / ruff check), npm run lint|test, npm test, go build|vet|test ./..., mvn -q -B compile|test, dotnet build|test.
- Argument validation: no traversal, absolute paths, option injection; pytest only accepts `-p no:cacheprovider` (blocks `-p <plugin>` code loading).
- Child env scrubbed of key/token/secret/password/auth variables; output passed through redact().
- New `detect_checks(root)` -> list of checks that apply to a project (used by Phase 6 self-repair).
- Not verified here: go / mvn / dotnet / ruff execution (tools not installed in this environment) — only allowlist logic tested for those.
- Tests: 280 passed, 7 skipped (new: tests/test_phase2_runner.py, 31 tests incl. real py_compile + pytest runs).

## Phase 3 changes
- Expanded `backend/agent/providers.py` into a fixed registry for Ollama, OpenAI-compatible OpenAI/Gemini/OpenRouter/Groq/DeepSeek, and native Anthropic Messages API. Each entry contains a name, adapter, default base URL/model, and allowlisted key environment variable.
- `backend/agent/llm.py` routes through the registry, keeps streaming/cancellation, JSON validation, bounded retry/backoff, and adds optional configured provider fallback. `llm.OllamaError` remains a compatibility alias for `ProviderError`.
- `backend/config.py` and `.env.example` include provider-specific `*_BASE_URL`, `*_MODEL`, and `*_API_KEY` settings plus optional `LLM_FALLBACK_PROVIDER`.
- `/providers`, `/providers/{provider}/models`, `/settings`, and `/ollama/check` expose provider/model data without returning any API-key value. `PUT /settings` accepts a write-only key; it saves to the ignored server-side `.env` and process environment, never SQLite or the response.
- Key safety is retained: fixed `KEY_ENV_VARS` allowlist, remote API keys are rejected for plain-HTTP endpoints, remote hosts require a key, request URLs are validated, and errors are redacted.
- Tests: `tests/test_provider_registry.py` covers key scoping, URL safety, registry entries, native Anthropic SSE parsing, settings key handling, and configured fallback.
- Current focused verification: `python -m compileall -q backend tests` and `python -m pytest -q` — 12 tests passed. API smoke check returned HTTP 200 for `/health`, `/providers`, and `/settings`. No live provider generation was performed.

## V2 Phase 7 (generated project quality)
DONE pending review: see PHASE7_NOTES.md (Dockerfile, compose, CI, frontend API client; catalog gap fix).

## Provider registry expansion (2026-10)

The provider integration was expanded after the original Phase 3 merge. See `PROVIDER_SETTINGS_API.md` for the contract consumed by the Phase 3 Settings UI. This phase1 archive includes the backend API and the contract document; it does not include or modify `frontend/src/workspace/SettingsDialog.tsx` or `frontend/src/services/api.ts`.

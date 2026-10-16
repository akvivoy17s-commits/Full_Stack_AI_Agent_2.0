# Merge report — phases 1-8 in one tree

Base for the 3-way merge: `fullstack_ai_agent_complete` (the common ancestor all phase zips were cut from). Starting tree: phase 8 (carries the phase 7 frontend). Phases 1-6 were then merged on top.

## Why a merge was needed
The phase 7/8 zips were built from `complete`, not from phases 1-6, so they did not contain: phase 1 `security.py` + hardening, phase 2 runner, phase 3 `providers.py`, phase 4 `progress.py`/`requirements.py`, phase 5 `repo/` + `task_memory.py` + `api/repo.py`, phase 6 `selfrepair.py`. `PHASE8_REPORT.md` flagged these as PARTIAL for that reason.

## Conflicts resolved by hand
| File | Resolution |
|---|---|
| `backend/main.py` | `/file` endpoint: phase 1 `is_agent_path` + 413 size cap, `(ValueError, OSError)` handling |
| `backend/tools/project_files.py` | `tree()`: phase 2 pruned `os.walk` + phase 1 symlink skip + secret filtering, capped at `MAX_TREE` |
| `backend/agent/schemas.py` | `OllamaCheck`: phase 1 `validate_base_url` validator + phase 3 `provider` field |
| `backend/agent/tasks.py` | phase 4 progress/verdict + phase 5 task memory / repo map |
| `backend/storage/db.py` | both `task_steps` (phase 4) and `task_memory` (phase 5) tables |
| `backend/agent/orchestrator.py` | imports: `progress`, `requirements` (phase 4) + `selfrepair` (phase 6) |
| docs | `PHASES.md`, `IMPLEMENTATION_REPORT.md`, `PHASE_PROGRESS.md` unified |

## Bugs fixed
1. Phases 4/5/6 code missing from the phase 7/8 tree (above).
2. `tests/test_phase3_providers.py`: `conftest.py` forces `MOCK_LLM=1`, so 5 provider tests hit the mock and raised `ValueError` instead of exercising the provider path. The autouse fixture now sets `llm.config.MOCK_LLM = False`.
3. `verify_phase8.py`: allowlist probes used shapes the runner correctly rejects (`compileall x`, bare `ruff`), so Phase 2 showed PARTIAL. Probes now use the real allowed shapes.
4. Stale status tables (phases shown as pending/next) updated; `data/` and `generated_projects/*` runtime output removed from the tree.

## Verification
Run in an environment with no PyPI/npm access, so the full suite could not be run here.
- Done: `compileall`; internal-import, undefined-name and module-attribute checks on every Python file (0 problems); 29 TS/TSX files parse; `api.ts` passes `tsc --strict` and every `api.*` call in components exists; `verify_phase8.py` Phases 1-6 PASS.
- Done: fastapi-free tests run with a minimal pytest shim (phases 1-6 units: security, runner, providers, progress/requirements, self-repair, stack) — all passed after fix #2, except a test that spawns real pytest and one that needs `fastapi.testclient`.
- NOT run: the FastAPI/TestClient tests, `npm ci` / `tsc` / `eslint` / `vite build`, live Ollama.

Please run locally: `pip install -r backend/requirements.txt && pytest -q`, then `cd frontend && npm ci && npm run typecheck && npm run lint && npm run build`, then `python verify_phase8.py .`.

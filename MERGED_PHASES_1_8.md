# Merged build: phase 1 base + deltas 2-8 (Autopilot) - working-condition pass

## Merge
Base = fullstack_ai_agent_phase1.zip. Deltas applied in order 2 -> 8 (every delta file was already cumulative
for its own file, so the last copy wins: api/autopilot.py = phase 8, test_autopilot_resolver.py = phase 8, ...).
No file conflicts, no file lost. Old per-phase notes (PHASE1..8_AUTOPILOT*.md) are kept.

## Verified on a real toolchain (this time nothing is stubbed)
| Check | Result |
|---|---|
| `python -m pytest -q` | 534 passed, 32 skipped, 0 failed (base alone: 13 failed) |
| `python verify_autopilot.py` | 8/8 PASS (was 5 PASS + 3 BLOCKED in phase 8) |
| `cd frontend && npm install && npm run build` (tsc --noEmit + vite) | OK |
| `npm run lint` | OK (was 1 error) |
| Live run: backend (mock LLM) -> POST /autobuild "task management tool with kanban board" -> task | succeeded, verdict PASS |
| `npm install && npm run build` inside that generated project | OK |

Skipped tests (32) need tools that are not in this environment (JDK/Maven, Docker, real browser, ...).

## Fixes made in this pass
Code
- backend/agent/tasks.py: race - the task was marked succeeded/failed BEFORE the repo map + task memory were written,
  so a poller (or the next task) could see a finished task without its memory (test failed ~2 of 8 runs). Memory is now written first.
- backend/agent/planner.py: layout_for ignored kind="portfolio" (a portfolio project with a short brief became "landing").
- frontend/src/workspace/CreateWizard.tsx: eslint no-unused-expressions error (ternary used as a statement).

Tests that were stale against the current code (the code is right, the assertion was old)
- Spring Boot is "ready" since v2 phase 5 (test_backend_gen_django/flask/nest, test_stack_api, test_spec_engine, test_spec_project).
- Nest + Redis cache is generated since v2 phase 6 (test_backend_gen_nest).
- Django settings now have optional upload/live-cache parts (test_backend_gen_django security defaults).
- Django + MongoDB is refused by the stack rules, so it is no longer a valid generation combo (test_v2_phase7_project).
- Provider keys are per-provider allowlisted env vars and writable via PUT /settings (write-only) (test_phase3_providers).
- management kind -> "app" shell on purpose since Autopilot phase 5 (test_spec_project).

## Run it
    pip install -r backend/requirements.txt
    python -m pytest -q
    python verify_autopilot.py
    cd frontend && npm install && npm run build
    uvicorn backend.main:app --port 8000     # + cd frontend && npm run dev

## Known limits (not verifiable here)
- Live runs against a real model (Ollama / OpenAI-compatible) - only the mock LLM was used.
- Playwright browser checks need `playwright install chromium`.
- Docker / Maven / .NET / Go toolchains were not run.

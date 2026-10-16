# Phase 8 - Final verification (Autopilot work, phases 1-8)

**Verdict: PARTIAL** - everything verifiable in this sandbox passed; pytest, npm build and live generation could not run here.

## Run on your machine
    python verify_autopilot.py                      # 8 checks, no pytest needed; writes autopilot_evidence.json
    python -m pytest -q                             # full suite
    cd frontend && npm install && npm run build

## Evidence (sandbox, python verify_autopilot.py)
| # | Check | Result |
|---|-------|--------|
| 1 | compileall backend + tests | PASS |
| 2 | intent classifier, 16 prompts | PASS |
| 3 | stack resolver, tiered fallback, named-tech + feature notes | BLOCKED here (fastapi missing); logic verified earlier by running resolve_prompt standalone against the real stack engine (11 + 8 prompts) |
| 4 | planner.layout_for vs intent | BLOCKED here (httpx/pydantic missing); verified by executing the function standalone, old-vs-new diff over 24 prompts x 7 kinds |
| 5 | app_engine entities + generated App.tsx (3 variants) tsc strict | PASS (React types stubbed) |
| 6 | selfrepair window/rollback + restore_static | BLOCKED in the script here (httpx); window, rollback (1 check call) and restore_static verified standalone; existing 10 selfrepair tests pass standalone |
| 7 | generated client.ts, 23 stack combos, tsc --strict | PASS |
| 8 | no real secrets outside tests | PASS |
Expected on a machine with deps installed: checks 3, 4, 6 turn PASS.

## What changed per phase
1. Cleanup: 26 __pycache__ dirs removed; secret scan = fake test fixtures only.
2. Classifier: todos/booking/scheduler/invoice/kanban/management; "investment portfolio" is an app.
3. Resolver: tiered fallback (keep backend -> Express+SQLite -> frontend only); named-tech mismatch notes (Go, Angular, Vue, Laravel...).
4. App shell: domain default entities (CRM, booking, inventory, invoice); reported TS errors do not reproduce in this tree.
5. Planner: shared backend/agent/intent.py; layout_for agrees with Autopilot; app blueprint max_tokens 1200 -> 700.
6. Self-repair: error-line-safe window, no re-check after rollback, zero-token restore_static.
7. UI: "Autopilot decisions" card from persisted assumptions.
8. NEW here: feature notes for things the app shell does not build (payments, real-time, login without auth) - "booking app with payments" no longer silently drops payments. verify_autopilot.py + this report.

## Known limits (not fixed)
- Payments/real-time are reported, not generated in prompt-only app shells.
- tests/test_spec_project.py:176 expects layout "dashboard" for kind=management and "portfolio" for ("my work", kind=portfolio); the original code already returned app/landing, so those assertions look stale. Send the pytest output if they fail.
- Real @types/react, vite build, browser run, live LLM generation, Docker, Maven: never run in this sandbox.
- No generator can guarantee zero bugs for every prompt; check the assumptions card before relying on a build.

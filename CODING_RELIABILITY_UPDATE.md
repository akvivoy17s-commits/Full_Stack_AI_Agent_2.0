# Coding Reliability Patch

## Purpose

This patch strengthens the React + TypeScript generated-section pipeline against the recurring failure where a model/repair writes React-only components or undeclared expressions (`HeroBanner`, `ProductCardList`, `featuredProducts`, `CategoryList`, `categories`) into an HTML-fragment section, leaving `src/sections/Kpis.tsx` invalid.

## Changed files

- `backend/engines/react_engine.py`
  - Centralizes deterministic section-source normalization and rendering.
  - Reconciles generated `src/sections/*.tsx` and section CSS from canonical `.agent/parts/*.html`/`.css` before every build.
  - Persists a safe fallback if canonical HTML contains unsupported JSX/component expressions.
  - Keeps generated App imports synchronized after derived section files are repaired.
- `backend/agent/orchestrator.py`
  - Fingerprints each section's editable source before a repair attempt.
  - Stops a repeated model repair when the identical diagnostic remains and the canonical source did not change.
- `tests/test_generated_tsx_source_guard.py`
  - Adds regression tests for corrupt derived TSX, invalid canonical JSX-like HTML, idempotent reconciliation, and pre-build reconciliation.

## Validation

- Focused generator/build-repair suite: **37 passed**.
- Python compilation of modified backend modules: passed.
- Broad suite sample: 143 passed, 12 skipped, then stopped at 5 failures. Those failures included the environment's Django import/dependency conflict (`django.db` unavailable) and an existing Acme environment-variable contract assertion. Therefore the full suite is not reported as passing.
- This patch does not guarantee zero possible coding defects. It adds deterministic safeguards and regression tests so this class of invalid generated TSX is repaired before TypeScript runs, and it avoids repeatedly paying for an identical failed repair.

## Apply

Copy the three paths in the ZIP to the same relative paths under the `fullstack_ai_agent` project root, overwriting those files. Restart the FastAPI backend and run the generated project's Verify/Repair check again. Keep a backup before overwriting.

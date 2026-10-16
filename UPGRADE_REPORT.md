# Full Stack AI Agent — Upgrade Report

## What changed

### Generation speed and diagnostics
- Added **Fast / Balanced / Quality** generation profiles, configurable in the existing Settings dialog and via `GENERATION_PROFILE`.
- Applied profile-aware output-token caps for blueprint, section, repair, and vision calls. Fast is the default for CPU-only/local-model machines; verification and security checks remain enabled in every profile.
- Added Ollama `keep_alive` configuration (`OLLAMA_KEEP_ALIVE=30m` by default) so the model can remain loaded between pipeline calls.
- Added measured LLM output-token, elapsed-time, and tokens/second progress events to help identify which stages are slow.
- Reduced generated section output targets to avoid overly large responses from smaller local coding models.

### Duplicate IDs and repair behavior
- Strengthened HTML ID detection to handle quoted and unquoted `id` attributes.
- Added deterministic, idempotent duplicate/conflicting ID normalization before expensive verification, with no LLM call.
- Applied ID cleanup at insertion time and added duplicate-ID static validation.
- Kept repair fallback behavior for cases where a targeted patch cannot be applied; duplicate IDs are handled earlier so the model does not need to spend repair calls on this common issue.

### Ecommerce backend correctness
- Added a transactional `/api/checkout` generator for the **Express + SQLite/PostgreSQL/MySQL** combination when authentication and the required ecommerce entities are present.
- Checkout reads prices and stock from the database, validates quantities, checks/decrements stock inside a transaction, stores order ownership, and does not trust client-submitted totals.
- Added generated API tests for authentication, server-side prices, stock handling, ownership and transaction rollback.
- Added `OrderItem.user_id` to the ecommerce spec to resolve the owner-scope warning.
- Checkout is reported as unsupported for combinations where this implementation is not available; it is not falsely marked as generated for other backend generators or MongoDB.

### Additional reliability fixes
- Fixed the project requirements endpoint to load the actual current project specification.
- Allowed IPv6 loopback `localhost` model URLs while continuing to reject link-local, unspecified, metadata and invalid URL targets.
- Added tests for profile caps, accepted profile values, duplicate-ID normalization, checkout support conditions and owner scoping.
- Updated the memory-map test fixture to model an existing local `.env` file without weakening the product's protected-file write rules.

## Validation performed

- `python -m compileall -q backend tests` — passed.
- Focused regression suite across agent speed/reliability, backend generators, repair, providers, specifications, security, cancellation and frontend/backend route contracts — **67 passed**.
- Node syntax checks for generated Express JavaScript ran through the targeted generator tests.

## Remaining verification limits

- The complete 369-test suite did not finish within the available execution window; a run excluding the optional generated-backend e2e module reached the long-running stack-engine fuzz test at 97% before timing out. Therefore, this report does **not** claim the entire suite passed.
- Generated Python-backend end-to-end tests need the generated project's runtime dependencies (including `bcrypt`) installed; that dependency was not available in the current verification environment.
- Installing npm dependencies for a generated checkout project timed out in this environment, so the newly generated checkout route was syntax-checked and generator-tested, but not exercised against a live SQLite/PostgreSQL/MySQL database here.
- This upgrade does not implement every external integration in the original prompt. Payments/webhooks, uploads, WebSocket live updates and other features not supported by the selected generator remain explicitly reported as gaps rather than fake implementations.

## Recommended settings for a 16 GB CPU-only laptop

- `GENERATION_PROFILE=fast`
- `OLLAMA_NUM_CTX=4096`
- `OLLAMA_KEEP_ALIVE=30m`
- `MAX_CONCURRENCY=1`

Use **Settings → Generation profile → Balanced** if a generated section becomes too short. Use **Quality** when detail is more important than generation time.

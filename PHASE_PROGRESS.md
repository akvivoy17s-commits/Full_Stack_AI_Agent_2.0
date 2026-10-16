# Upgrade progress (resume file)

| # | Phase | Status |
|---|-------|--------|
| 1 | Audit + file/endpoint security hardening | DONE (merged) — see PHASES.md |
| 2 | Command runner (python/pytest/lint/go, allowlisted) | DONE (merged) — see PHASES.md |
| 3 | Provider registry (Ollama, OpenAI-compatible providers + native Anthropic, retries/fallback) | DONE (merged) — see PHASES.md |
| 4 | Planner / requirement analysis / task execution / progress | DONE (merged) — see PHASES.md |
| 5 | Repo understanding + persistent task memory | DONE (merged) — see PHASES.md |
| 6 | Bounded self-repair loop | DONE (merged) — see PHASES.md |
| 7 | Frontend integration + e2e generator checks | DONE (merged) — see PHASES.md |
| 8 | Final verification + PASS/PARTIAL/BLOCKED/FAIL report | DONE (merged) — see PHASES.md |

## Phase 1 - audit findings (evidence-based)
Baseline: 234 passed / 7 skipped. After: 259 passed / 7 skipped (25 new in tests/test_security_phase1.py).

Fixed
1. HIGH  Preview iframe ran generated JS same-origin with the API (sandbox had allow-same-origin) -> could call any API route. Now opaque origin (iframe + CSP sandbox header) and `nosniff`.
2. HIGH  No CSRF/Origin check on POST/PUT/DELETE (simple cross-site POSTs, sandboxed pages `Origin: null`). Now rejected unless Origin is in CORS_ORIGINS.
3. MED   `.agent` protection was case-sensitive (`.Agent/` bypass on Windows/macOS) -> case-insensitive via security.is_agent_path; `.agent/*` no longer readable through the file API.
4. MED   SSRF: /settings and /ollama/check accepted any URL (metadata IP, credentials). Now validated (no link-local/unspecified/metadata, no userinfo); LAN/loopback Ollama still allowed.
5. MED   Symlinks inside a project were followed into export/checkpoint zips -> skipped; restore no longer rmtree()s a symlink.
6. MED   Legacy endpoints (generate/verify/edit/save file) ignored the running-task lock -> 409 like the task API.
7. LOW   Windows alternate data streams (`a.txt:x`) in paths -> rejected.
8. LOW   Unbounded file save body / unbounded file read -> max_length + MAX_READ_BYTES (413).
9. LOW   Raw exception text returned to clients -> redacted; unhandled errors return a generic 500 (details only in redacted log).
10. NEW  Host-header allowlist (DNS rebinding), optional API_TOKEN, security headers.

Known, NOT fixed in phase 1 (carried forward)
- `npm install/ci` runs lifecycle scripts of model-written package.json (code-exec risk) -> Phase 2 (command runner). 
- `node --check` accepts absolute .js paths (syntax check only) -> Phase 2.
- Frontend does not send API_TOKEN yet (token is off by default) -> Phase 7.
- Preview pages can no longer use localStorage/cookies (opaque origin) - intentional trade-off.
- Python test deps (pytest) are not in requirements.txt (requirements-dev) -> Phase 2.

---

# Upgrade v2 (generator roadmap) - Phase 6: Integrations

6A (this zip): Express only. Cache (Redis or in-memory fallback; per-caller GET cache, write invalidation, `X-Cache`), uploads (raw body, magic-byte type check, random names, local storage), Stripe payments (`/api/payments/intent` amount from stored order; `/api/payments/webhook` raw-body HMAC + amount check, idempotent), WebSocket `/ws` (origin check, auth message, metadata-only `change` events). Enabled by the app spec/stack (`cache=redis`, `storage=local`, payment/upload/ws routes); otherwise no files or dependencies are added.
Verified here: generation of 6 backends x 4 DBs, `node --check` of all generated JS, Stripe signature + cache logic executed in node with stubbed packages, new Python tests (7). NOT verified here (no network): `npm install`, running the Express app with real redis/ws/Stripe, existing repo pytest suite (pytest unavailable).
Not done (6B, next): same integrations for FastAPI/Flask/NestJS/Django/Spring, S3 storage, Razorpay/PayPal, Firebase (Auth token exchange / Firestore).

6B (this zip): FastAPI + Flask. Shared core `app/cache.py`, `app/uploads_core.py`, `app/live_core.py`; FastAPI `live.py` (cache middleware + WebSocket `/ws`) and `routes/uploads.py`; Flask `live.py` (cache hooks) and `routes/uploads.py`. Same behaviour/limits as Express (per-caller cache, write invalidation, magic-byte uploads, 100 kB cap kept on normal routes, `/ws` origin + auth message).
Deliberately NOT generated for Python: payments (needs the server-side transactional checkout, which only Express has) and Flask WebSocket (no built-in support).
Verified: Flask runtime over HTTP (cache MISS/HIT/invalidate, uploads, 415/400/401/404/413 cases) with in-memory DB; all generated .py compile for 8 combos; 46-combo generation smoke. NOT verified: FastAPI at runtime (fastapi not installed here), real Redis.
Next: 6C NestJS + Django, 6D Spring, 6E S3 / Razorpay / PayPal / Firebase / Python+Nest checkout->payments.

6C (this zip): NestJS + Django. Nest: `src/integrations/{cache,events,live,uploads,ws}.ts` (Express-level middleware/router, mounted before the JSON parser for uploads; `ws` attached to the HTTP server in main.ts). Django: `LiveMiddleware` (cache + invalidation, listed after ApiMiddleware), `uploads_views.py`, shared Python core; the 100 kB cap is kept on every route except `/api/uploads`. Django has no WebSocket (needs ASGI + Channels). Payments are not generated for Nest/Django (no server-side checkout there yet).
Also fixed a 6A/6B bug: an app with WebSocket but no cache shipped `live` code that imports the cache module without shipping it (Express, FastAPI); the cache module is now included whenever WebSocket is on. Regression test added.
Verified: 46-combo generation smoke, all new tests (11) pass, generated Nest TS parses (no syntax errors). NOT verified: Nest compile/run (no npm packages here), Django runtime (Django not installed), real Redis/ws/Stripe, Express and FastAPI at runtime.
Next: 6D Spring, 6E S3 / Razorpay / PayPal / Firebase / checkout+payments for Python and Nest.

6D (this zip): Spring Boot. `app/integrations/`: `Cache` (Redis via Jedis when `REDIS_URL` is reachable, else in-memory; retry after 30 s), `Events`, `LiveFilter` (per-caller GET cache with `X-Cache`, token re-checked before a HIT, write invalidation + `{entity, op}` events), `UploadController` + `UploadKinds` (raw body, magic-byte type, random names, `UPLOAD_MAX_BYTES`, `/api/uploads` exempt from the 100 kB cap), `WsConfig` + `WsHandler` + `WsTokens` (`/ws`, origin check from `CORS_ORIGINS`, auth message within 5 s, 2 kB message cap, `WS_MAX_CLIENTS`, 30 s ping). Files, `jedis` and `spring-boot-starter-websocket` are added only when the spec needs them; plain apps get nothing. Tests: `CacheTest`, `UploadKindsTest` (generated), 3 new Python tests.
Verified here: generation for 3 DBs x 3 briefs; `UploadKinds` and `Events` compiled and executed with javac (PNG ok, script/empty rejected, event delivered); syntax-only javac of all integration files shows no errors other than missing Spring/Jedis jars. NOT verified (no Maven, no network): full `mvn test`/compile with Spring + Jedis, running the app, real Redis, WebSocket handshake, pytest suite (pytest unavailable; new tests run by hand with a stub).
Not done: Spring payments (no server-side checkout outside Express).
Next: 6E S3 / Razorpay / PayPal / Firebase / checkout+payments for Python, Nest, Spring.

6E (this zip): Razorpay + PayPal payments for Express (the provider comes from the spec's env vars; Stripe unchanged). New `routes/payments_razorpay.js`, `routes/payments_paypal.js` (copied over `routes/payments.js` by the generator, so the app wiring is the same) and shared `lib/pay.js` (own pending order only, amount from the stored order, idempotent mark-paid on exact minor-unit match). Razorpay: order created via REST (paise), webhook HMAC-SHA256 over the raw body (`payment.captured`, currency + amount checked). PayPal: Orders v2, webhook verified by PayPal's verify-webhook-signature (`PAYPAL_WEBHOOK_ID`), server-side idempotent capture on `CHECKOUT.ORDER.APPROVED` only for an order we created with the same amount, mark-paid on `PAYMENT.CAPTURE.COMPLETED`. `m["paymentProvider"]`, per-provider currency env (`RAZORPAY_CURRENCY`, `PAYPAL_CURRENCY`), `PAYPAL_WEBHOOK_ID` / `PAYPAL_ENV` env, README and OpenAPI text follow the provider.
Also fixed: the 6D change made the old "Spring has no integrations" test stale; it now asserts Spring has cache/uploads/WebSocket and no payments.
Verified: generation + `node --check` for stripe/razorpay/paypal; the real generated route code run in node with stubbed express/fetch/db (bad/missing signature -> 400, wrong amount/currency ignored, replay harmless, order never resurrected, PayPal capture only for a matching pending order, intent amount read from the stored order). All phase 6 tests pass except the Flask HTTP test (Flask not installed here). 7 other failures in older test files fail identically on the untouched 6C zip (missing flask/django/pytest here), so they are environmental.
NOT verified: real Razorpay/PayPal sandbox calls (no network), `npm install` + running the Express app.
Moved to later parts (NOT done): S3 storage, Firebase (Auth token exchange / Firestore), and checkout + payments for Python/Nest/Spring.
Next: 6F S3 storage (Express first), 6G Firebase, 6H checkout+payments for Python/Nest/Spring.

6F (this zip): S3-compatible storage for Express (`storage=s3`; AWS S3, MinIO, R2, Spaces). `lib/s3.js` signs with AWS Signature V4 using fetch (no SDK; virtual-hosted style for amazonaws.com endpoints, path style otherwise); `routes/uploads_s3.js` is copied over `routes/uploads.js`, so the app wiring is unchanged. The bucket stays PRIVATE: same sign-in rule, magic-byte type check, random names and size cap as local uploads, downloads proxied through the API with nosniff + sandbox CSP. Placeholder credentials -> 503 `storage_unavailable` with no request made; unreachable/rejecting storage -> 502. `m["storage"]` added; README/.env follow the storage kind (`S3_*` replaces `UPLOAD_DIR`).
Verified: the signer reproduces the AWS documentation SigV4 example signature exactly; generated routes run in node against a fake bucket (upload -> PUT with correct URL/auth header, secret never sent, bad type rejected before any request, download round-trips bytes, bad names 404 without touching the bucket). Phase 6 tests pass except the Flask HTTP test (Flask not installed here).
NOT verified: a real bucket (no network), presigned URLs (not generated by design), `npm install` + running the app.
S3 is Express only; Python/Nest/Spring/Django with `storage=s3` still report "file uploads" as not generated.
Next: 6G Firebase (Auth token exchange / Firestore), 6H checkout+payments for Python/Nest/Spring, S3 for the other backends.

6H.3 (this zip): NestJS checkout + payments. `POST /api/checkout` (`src/checkout/*`): one transaction via the new optional `Db.tx()` (TypeORM: row locks `FOR UPDATE` except SQLite, conditional `stock - n WHERE stock >= n`, any throw rolls back); prices/stock read server-side, same validation and error codes as Express/FastAPI. Payments (`src/integrations/pay.ts` + `payments.ts`; Razorpay/PayPal variants are copied over `payments.ts` by `nest.py`): webhook mounted BEFORE the JSON parser (raw-body signature), intent route after it, own pending order only, amount from the stored order, idempotent mark-paid via conditional `Db.updateWhere()` on exact minor-unit match. Generated `notify.ts` (cache invalidation + WS events for writes outside CRUD) and `pay-mount.ts` (no-op when the app has no payments). Gate in `model.py`: checkout/payments now allow `nestjs`; MongoDB still reports checkout as not generated. Generated test `test/checkout.e2e-spec.ts` (needs `npm install`).
Also fixed (pre-existing, found by the import check): `bootstrap.ts`, `main.ts`, `health.controller.ts` imported optional integration files with a literal path, so `nest build` could not compile apps without uploads/cache/ws; they are now loaded by name.
Verified here: 25 NestJS projects (sqlite/postgresql/mysql/mssql/mongodb x stripe/razorpay/paypal/plain) generated, every relative import resolves and every .ts parses; real checkout + payment code transpiled and run in node with a fake transactional db (totals from DB, client total ignored, rollback leaves stock/orders untouched, bad/oversized/non-integer items 400, Stripe + Razorpay signature vectors, markPaid exact-amount/replay/cancelled-order cases, payableOrder own-order only). tests/test_v2_phase6h3_nest_checkout.py: 12 pass. Existing suites: no new failures (3 failures exist identically on the untouched 6H.2 zip: spring status, node validation harness, OpenAPI equality since 6H.1).
NOT verified (no npm/network): `nest build`/`jest` with real Nest + TypeORM, real provider calls, real PostgreSQL/MySQL/SQL Server locking.
Next: 6H.4 Django checkout + payments, 6H.5 Spring, 6H.6 S3 + Firebase Storage.

6H.4 (this zip): Django checkout + payments. `POST /api/checkout` (`app/checkout_core.py` + `checkout_views.py`): one `transaction.atomic()`, `select_for_update()` row locks (ignored by SQLite), conditional `UPDATE ... WHERE stock >= n` via `F()`, prices/stock read server-side, same validation and error codes as the other backends. Payments (`pay_shared.py`, `payments_core.py`, `payments_views.py`; Razorpay/PayPal variants copied over `payments_core.py` by `django_gen.py`): webhook verified over the exact raw `request.body`, intent only for the caller's own pending order, amount from the stored order, idempotent `mark_paid` on exact minor-unit match. `templates/django/app/{checkout_core,pay_shared}.py` override the SQLAlchemy versions in `templates/python` (later root wins). Gate in `model.py`: checkout/payments now allow `django`; MongoDB is not a Django option.
Also fixed (pre-existing since 6H.1): Django projects shipped the SQLAlchemy `checkout_core.py` / `pay_shared.py` / `payments_*.py` even when the app had no checkout (dead files importing sqlalchemy); `django_gen._skip` now drops them unless needed.
Verified here: 4 DBs (sqlite/postgresql/mysql/mssql) x 3 providers generated, every .py compiles, no sqlalchemy in the Django files; real checkout + payment code run against an in-memory fake Django ORM (totals from DB, rollback leaves stock/orders untouched, bad items 400, own-order only, exact-amount idempotent mark-paid). tests/test_v2_phase6h4_django_checkout.py: 3 pass; stale 6 integrations assertion updated.
NOT verified (Django/pytest not installed, no network): real Django ORM / `manage.py check`, real PostgreSQL/MySQL row locking, real provider calls.
Next: 6H.5 Spring checkout + payments, 6H.6 S3 + Firebase Storage.

6H.5 (this zip): Spring checkout + payments. `app/checkout/` (`CheckoutController`, `CheckoutService`, `Money`, `Notify`): `POST /api/checkout` in one `TransactionTemplate` transaction, `SELECT ... FOR UPDATE` (PostgreSQL/MySQL) or `WITH (UPDLOCK, ROWLOCK)` (SQL Server), prices/stock read server-side, conditional `UPDATE ... WHERE stock >= ?`, any exception rolls back; same validation and error codes as the other backends. `app/payments/` (`PaymentsController`, `PayProvider`, `PayShared`, `PayCrypto`, and only the app's provider: `StripePay` / `RazorpayPay` / `PaypalPay`): webhook takes the raw `byte[]` body, signature checked in constant time over those exact bytes (Stripe 5-minute window, Razorpay HMAC; PayPal verifies via its API), intent only for the caller's own pending order, amount from the stored order, idempotent `markPaid` on exact minor-unit match; HTTPS via `java.net.http` (10 s), Jackson only for parsing. `Notify` invalidates the cache and emits `{entity, op}` for writes outside CRUD (a no-op class is generated when the app has neither cache nor WebSocket). Placeholders `your-...` and `<set>` count as "not configured" (503). Generated unit test `CheckoutMathTest` (cents, cart validation, signatures). Gate in `model.py`: checkout/payments now allow `spring`; MongoDB still reports checkout as not generated.
Verified here: 24 Spring projects (sqlite/postgresql/mysql/mssql x stripe/razorpay/paypal x with/without cache) generated and every .java parses (0 syntax errors); all new classes type-checked with javac against minimal Spring/Jackson stubs (including all 3 providers + controllers); `Money` + `PayCrypto` compiled and run for real (cents, cart rules, Stripe + Razorpay signature vectors); CheckoutService + PayShared run against a fake transactional JDBC (totals from DB, row lock requested, rollback leaves stock/orders untouched, inactive/missing/out-of-stock products rejected, anon 401, own-order only, exact-amount idempotent mark-paid, cache + event notified). tests/test_v2_phase6h5_spring_checkout.py: 3 pass; 3 stale 6-integrations assertions updated.
NOT verified (no Maven, no Spring/Jackson jars, no network): `mvn test`/compile with real Spring, running the app, real PostgreSQL/MySQL/SQL Server locking, real provider calls, the generated JUnit `CheckoutMathTest` itself (JUnit jar missing; same assertions were run by hand).
Next: 6H.6 S3 + Firebase Storage for non-Express backends (the last open item of phase 6).

6H.6 (merged): S3-compatible + Firebase Storage uploads for FastAPI, Flask, Django, NestJS, Spring. Phase 6 (6A-6H.6) is merged into this one tree and re-verified; see PHASE6_MERGED.md.

Next: Phase 7 frontend integration + end-to-end generator checks.

## Provider registry update (2026-10)

Expanded provider support and server-side settings are documented in `PROVIDER_SETTINGS_API.md`. This phase1 archive includes provider registry and backend endpoints, but not the separate Phase 3 frontend files. Focused tests: 12 passed; no live API/model call was used in the verification.

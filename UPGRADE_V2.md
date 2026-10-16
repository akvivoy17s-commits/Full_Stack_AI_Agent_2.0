# Upgrade V2 (8 phases, approval gate after each)

| # | Phase | Status |
|---|-------|--------|
| 1 | Creation UI foundation (guided wizard, layout, states) | DONE (approved) |
| 2 | Creation UI advanced (pages/features/entity editor, live spec preview, presets) | DONE (approved) |
| 3 | Database layer (relations, indexes, migrations, seed, SQL Server) | DONE (approved) |
| 4 | Backend core consistency across 5 generators | DONE - awaiting approval |
| 5 | Missing backends (Spring finish, Go, ASP.NET, Laravel) | IN PROGRESS: 5.1 approved, 5.2 Spring security/seed/register done - awaiting approval |
| 6 | Integrations (Redis, uploads, payments, WebSocket, Firebase) | DONE (merged): 6A-6F, 6G Firebase, 6H.1-6H.6 checkout + payments + S3/Firebase Storage for every backend - see PHASE6_MERGED.md |
| 7 | Generated project quality (Docker, CI, tests, API client) | pending |
| 8 | Final verification matrix + report | pending |

## Phase 1 changes
- Guided wizard (CreateWizard.tsx, briefing.ts), full-column layout, sentence-case labels.

## Phase 2 changes
- Wizard is now Describe -> Technology -> Data & pages -> Review.
- New `SpecEditor.tsx`: live preview via existing `POST /spec/preview` (350 ms debounce, stale responses ignored). Edit pages (title, address, sign-in), features, entities (add, remove, fields with type/ref/enum/required/unique). Invalid input is explained inline and never sent; `Reset edits` restores the generated model. `User` is read-only.
- New `presets.ts`: save/load/delete up to 10 presets (brief, style, motion, stack, edits) in localStorage; no secrets stored.
- Backend: `POST /projects` accepts `overrides` (validated before anything is created; a bad edit returns 422 and leaves no project folder). Editing an existing entity's fields now keeps its read/write access rules (before, an edit silently reset them to user/owner).
- Tests added: `tests/test_v2_phase2.py` (3 cases).

## Verification (honest)
- Ran here: the spec logic directly in Python (access rules kept: Product stays public/admin; dropping Product is rejected because OrderItem refers to it; bad entity name rejected). `py_compile` on changed Python files. `tsc` strict check of the whole workspace graph against stub React types: no errors besides stub artifacts.
- NOT run: pytest suite (pytest/fastapi not installed here, no network), `npm ci && npm run build`, lint, browser. Run: `pytest tests/test_v2_phase2.py tests/test_spec_engine.py tests/test_spec_project.py` and `cd frontend && npm ci && npm run build`.

## Phase 3 changes
- Shared model rules (`gen/model.py`): per-field `index` (ref/enum/bool/searchable; never text/url), per-reference `onDelete` (CASCADE internal, RESTRICT required, SET NULL optional), deterministic `seed` plan.
- SQL Server (`mssql`) generated for Express (knex+tedious), NestJS (TypeORM+mssql), FastAPI/Flask (SQLAlchemy+pymssql), Django (mssql-django, needs an ODBC driver). SQL Server uses NO ACTION instead of SET NULL (multiple cascade paths are rejected); optional unique columns get filtered unique indexes.
- Migrations: FastAPI/Flask now ship Alembic (`alembic.ini`, `migrations/`, frozen `0001_initial.py`); `migrate()` applies it. Express (knex), NestJS (TypeORM) and Django already had migrations and now use the shared index/FK rules.
- Seed: `python -m scripts.seed_sample` / `npm run seed:sample` (all generators except Spring). Idempotent, links to the seeded admin, refuses in production unless `ALLOW_SAMPLE_DATA=true`.
- MongoDB: lookup indexes from the same `index` rule (Express, NestJS, FastAPI/Flask).
- Spring: schema.json/Java `Field` carry `index`/`onDelete`; its DB layer is Phase 5.
- Tests: `tests/test_v2_phase3.py` (4 cases: shared rules, Alembic-vs-models drift check, seed idempotency + FK check on SQLite, SQL Server SQL via `alembic --sql`). Three older tests that said mssql was "planned" were updated.

## Verification (honest)
- Ran: full pytest (see result below); generated Express/NestJS/FastAPI/Flask/Django projects on SQLite with seed run twice and FK check; Express project's own tests (9/9); `tsc` on NestJS sqlite and mssql projects; knex and Alembic SQL Server SQL generated offline.
- NOT run: a real SQL Server, a real MongoDB (seed/indexes there are untested), NestJS Jest suite, Django `makemigrations --check`, `test_phase7_e2e.py`.

## Phase 4 changes
- `?sort=<field>` / `?sort=-<field>` on every list endpoint in all 5 generators (Express, NestJS, FastAPI, Flask, Django), SQL and MongoDB. Allowed: `id` or any non-text, non-sensitive field. Default stays `-id`; `id` is always the tie-breaker so pages are stable. Anything else (unknown field, text, sensitive, repeated param) is a 400 `validation_failed`.
- One OpenAPI 3.0.3 document (`gen/openapi.py`) built from the shared model and written to `backend/openapi.json` by every generator; served at `GET /api/openapi.json` (+ `/api/docs` reference page) by all five. It lists every generated route, request/response schemas (secrets excluded), access level, query params (page, limit, q, sort, filters), bearer auth and the standard error body.
- Already consistent before this phase and left unchanged (checked, not rewritten): validation (unknown fields rejected, typed), pagination `{data,page,limit,total}` (max 100), exact filters, error body `{error:{code,message,details?}}`, single-use rotating refresh tokens, server-side RBAC (public/user/owner/admin, other users' records 404).
- NOT added (needs a schema change, so deliberately left out): refresh-token reuse detection (revoking every session when an already-used token comes back).
- Tests: `tests/test_v2_phase4.py` (6 cases).

## Phase 4 verification (honest)
- Ran: the 6 new tests (via a local pytest stand-in, pytest is not installed here): OpenAPI byte-identical across FastAPI/Flask/Django/NestJS and valid (all `$ref` resolve, every manifest route documented, `sort` on every list, no `password_hash`) for SQLite and MongoDB; Python parse + ordering through `service.list_records`; Express `parseList` run under Node; Flask over HTTP (sort asc/desc, 400 body, `/api/openapi.json`, `/api/docs`). `py_compile` on all Python templates, `node --check` on all Express templates.
- NOT run: pytest suite, real SQL/MongoDB ORDER BY (SQLAlchemy/knex/TypeORM/Django ORM/Mongoose sort code is untested here), FastAPI/Django/NestJS/Express servers (no deps, no network), `tsc` on NestJS. Run: `pytest tests/test_v2_phase4.py tests/test_backend_gen_*.py`.

## Phase 5 plan (one part at a time, approval after each)
5.1 Spring data layer (approved) | 5.2 Spring JWT + seed + register (this delivery) | 5.3 Go | 5.4 ASP.NET | 5.5 Laravel

## Phase 5.1 changes (Spring Boot data layer)
- SQL: Spring JDBC `SqlRepo` (all values bound, names checked) for SQLite/PostgreSQL/MySQL/SQL Server; pool from `DATABASE_URL` (`DbConfig`); Flyway script `db/migration/V1__initial.sql` generated per dialect from the shared model (FKs with onDelete, indexes, SQL Server filtered unique indexes). MongoDB: `MongoRepo` (indexes from the same rule).
- `EntityService` + `CrudController`: CRUD for every entity at `/api/{path}`, access rules public/user/owner/admin (others' records 404), ref checks, `created_at`/`updated_at`, `?sort=` (same rules/message as the other 5 generators), unique/FK violation -> 409.
- `GET /api/openapi.json` + `/api/docs` (shared OpenAPI document, `src/main/resources/openapi.json`).
- Callers are anonymous until 5.2 (`AnonymousAuth`), so non-public routes answer 401. Spring is still NOT registered in `stage.GENERATORS`.
- Only the files a stack needs are emitted (SQL / Mongo / no database).
- Tests: `tests/test_v2_phase5_spring.py` (13 cases); generated `SqlRepoTest` (SQLite round trip) and a DB-free `ApiSmokeTest`.

## Phase 5.1 verification (honest)
- Ran: 13 new tests + the 10 old Spring tests (stand-in runner, no pytest here). The generated SQLite script was executed in real SQLite (FK check, indexes). Real `java` run of `CoreCheck` incl. new sort rules. `javac` syntax check of generated Java for sqlite/mongodb/none (only missing-library errors allowed).
- NOT run: Maven/Spring (no network), so `SqlRepo`, `MongoRepo`, `DbConfig`, `CrudController`, the JUnit tests are compiled only for syntax; no PostgreSQL/MySQL/SQL Server/MongoDB server; Flyway SQLite support not confirmed. Run `mvn test` in a generated backend.
- Known: ORM label in the catalog still says JPA; part 5.2 changes it to Spring JDBC when registering. MySQL unique index on a `url` field would exceed the key length.

## Phase 5.2 changes (Spring Boot sign-in, seed, registration)
- `core/Jwt.java`: HS256 with the JDK only (HMAC-SHA256, constant-time compare, requires `exp`, rejects `alg:none`/other algs, signature checked before the body is read). `web/JwtAuth.java` reads the Bearer token: no header = anonymous, bad token = 401 `invalid_token` (ignored on public routes). `web/AuthSettings.java` stops start-up on a weak `JWT_SECRET` (<32 chars / placeholder).
- `web/AuthController.java`: `POST /api/auth/register|login|refresh|logout`, `GET /api/auth/me`, same contract as the other 5 backends: BCrypt (`spring-security-crypto` only; no Spring Security filter chain, access rules stay in `EntityService`), role never client-set, timing-equalised unknown email, single-use rotating refresh tokens (delete-then-check), logout one or all sessions. Existing rate limits already cover `/api/auth/*`.
- Seed: `--seed=admin` (ADMIN_EMAIL / ADMIN_PASSWORD) and `--seed=sample` (idempotent, refused in production unless `ALLOW_SAMPLE_DATA=true`), run without a web server, then the process exits. `schema.json` now carries the shared `seed` plan.
- Registered: `stage.GENERATORS["spring"]`; catalog now lists Spring (java; sqlite/postgresql/mysql/mssql/mongodb; auth none|jwt) and the ORM label is "Spring JDBC + Flyway" (was "Spring Data JPA").
- No-sign-in stacks get `AnonymousAuth` instead and no auth/seed-admin files.
- Tests: `tests/test_v2_phase5_spring.py` now 24 cases; generated `JwtTest` and `AuthFlowTest` (real SQLite through MockMvc); real `java` run of Jwt checks in `CoreCheck`. Old tests that said Spring was "planned" now use Go.

## Phase 5.2 verification (honest)
- Ran: 24 + 10 Spring tests (stand-in runner), Jwt sign/verify/tamper/expiry/alg-none under a real `java` run, `javac` syntax check of generated Java, stack-engine tests (30).
- NOT run: Maven/Spring (no network), so `AuthController`, `JwtAuth`, `SeedRunner`, `AuthFlowTest`, `JwtTest` (JUnit) are syntax-checked only; no real PostgreSQL/MySQL/SQL Server/MongoDB. `--seed=` startup path (non-web context) untested. In `test_backend_gen.py` 2 tests (regeneration idempotency, Node validation) also fail on the untouched phase 1-4 zip in this sandbox (not caused by this phase).

## Phase 6G changes (Firebase, Express)
- `POST /api/auth/firebase {idToken}` (stack auth = firebase-auth, Express + database): Admin SDK `verifyIdToken(token, checkRevoked=true)`; only verified-email tokens; same email = same local account, else a new user with the default role (never from the token, unusable random password hash). Returns the normal token pair. Rate limited, bad token = generic 401, SDK missing = 503.
- Firebase Storage uploads (stack storage = firebase-storage): same file-type/size checks as S3 uploads, private bucket, served only through `/api/uploads`.
- `lib/firebase.js` (lazy Admin init; key from `FIREBASE_SERVICE_ACCOUNT_PATH` or Google default credentials), config validation (`FIREBASE_PROJECT_ID`, `FIREBASE_STORAGE_BUCKET`), `.env.example`, `.gitignore` (`secrets/`), OpenAPI, manifest, README. Shipped only when needed; `firebase-admin` dependency only then.
- Tests: `tests/test_v2_phase6_firebase.py` (5 cases incl. Node run of `lib/firebase.js` against a stub SDK).

## Phase 6G verification (honest)
- Ran: new 5 tests + phase6 integrations (21/21) + stack engine (30/30) + spring (4/4) via a pytest stand-in; `node --check` on generated JS. phase4 / backend_gen / spec_engine fail the same tests before and after this change (stand-in/env limits).
- NOT run: real Firebase project, `npm install`, the sign-in route end to end (no express/bcryptjs here), Firestore/RTDB as database.
- Still open: checkout + payments for Python/Nest/Spring (6H), S3 + Firebase Storage for non-Express backends.

## Phase 6H plan (one part at a time)
6H.1 FastAPI + Flask checkout + Stripe (this delivery) | 6H.2 Razorpay/PayPal for Python | 6H.3 NestJS | 6H.4 Django | 6H.5 Spring | 6H.6 S3 + Firebase Storage for non-Express

## Phase 6H.1 changes (FastAPI + Flask, SQL databases)
- `POST /api/checkout {items:[{productId, quantity}]}`: one transaction; prices/stock read server-side (row lock off SQLite), conditional stock decrement (no overselling), `pending` order + items, same limits/errors as Express (1-50 lines, qty 1-99, 400/409 codes). Money in integer cents, half-up.
- Stripe (stdlib `urllib`, no SDK): `POST /api/payments/intent {orderId}` (own pending order, amount from the stored order, idempotency key) and `POST /api/payments/webhook` (HMAC over raw bytes, 300 s tolerance, constant-time compare; idempotent, amount must match). Cache invalidated after paid.
- Shared logic in `app/checkout_core.py` + `app/payments_core.py`; thin routes per framework; shipped only when the app has a store + Stripe. `schema.SCHEMA["checkout"]`, `.env.example` (`STRIPE_CURRENCY`), OpenAPI, manifest, README.
- Model: `checkout` now also for fastapi/flask (SQL only); `payments` for them only with Stripe (Razorpay/PayPal stay "not generated" until 6H.2). MongoDB: still honestly "not generated".
- Not pushed over WebSocket yet: a webhook-driven `paid` change (Express emits it).
- Updated 3 old assertions that said "checkout/payments not generated" for FastAPI/Flask.

## Phase 6H.1 verification (honest)
- Ran: new 3 tests (generation for both frameworks, `compile()` of every generated .py, real HMAC signature checks incl. stale/tampered/wrong secret, item parsing, cents rounding with SQLAlchemy stubbed), phase6 integrations 21/21, firebase 5/5, spring 5/5. Other failing tests (stand-in/env) are the same set before and after.
- NOT run: a real database transaction (`create_order`, stock race, row lock), Stripe call, FastAPI/Flask over HTTP (no SQLAlchemy/FastAPI here, no network). Run: `pytest tests/test_v2_phase6h1_python_checkout.py` then a generated backend's own tests.

## Phase 6H.2 changes (Razorpay + PayPal, FastAPI + Flask)
- `app/pay_shared.py` (new, shared by all providers): `payable_order` (own pending order, amount from the stored order, min 50 minor units), idempotent `mark_paid` (pending + amount must match, cache invalidated), bounded `request_json` (10 s, stdlib), standard 502/503 errors. Stripe moved onto it (behaviour unchanged); `handle_webhook(db, raw, headers)` now takes lower-case headers for every provider.
- Razorpay: order in paise via REST, `X-Razorpay-Signature` HMAC-SHA256 over raw bytes (constant time), `payment.captured` + currency check; returns `razorpayOrderId` + public `keyId`.
- PayPal Orders v2: OAuth token cached (thread-safe), `custom_id` = our order id, PayPal verifies the webhook signature (`PAYPAL_WEBHOOK_ID`), `CHECKOUT.ORDER.APPROVED` captures server-side only when the stored order is pending and amount+currency match (idempotent `PayPal-Request-Id`), `PAYMENT.CAPTURE.COMPLETED` marks paid. `PAYPAL_ENV=live` for production.
- Generator copies the chosen provider over `app/payments_core.py`; config, `.env.example` (`*_CURRENCY`), README, OpenAPI follow the provider. Model: `payments` for fastapi/flask with any of the 3 providers.
- Updated 1 old assertion ("payments Express-only" now excludes FastAPI).

## Phase 6H.2 verification (honest)
- Ran: new 3 tests (all provider x framework generation + `compile()`, Razorpay HMAC valid/tampered/upper-case/empty secret, webhook currency + bad-signature + placeholder-secret paths, PayPal capture rules: matching order captured once, wrong amount/currency/not-pending ignored, unverified event rejected, capture-completed marks paid) with SQLAlchemy stubbed; 6H.1 3/3, phase6 21/21, firebase 5/5, spring 5/5. Other failing tests = same set as the original zip.
- NOT run: real Razorpay/PayPal/Stripe calls, real DB, FastAPI/Flask over HTTP.

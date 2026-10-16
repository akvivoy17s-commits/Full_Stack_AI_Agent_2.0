# Phase 6 merged (6A-6F + 6G + 6H.1-6H.6) - FINAL

Base: the 6H.5 snapshot plus 6H.6. Every zip (6A-6F, 6G, 6H.1-6H.5) was a full snapshot and each step only added to the previous one; a file-by-file chain comparison found nothing missing and nothing reverted.

Checked (script, on the 6F tree):
- No file from 6A-6E is missing in 6F, and no change from an earlier zip was lost or reverted (all file contents compared).
- `tests/test_v2_phase6_integrations.py`: 21/21 pass (Express cache/uploads/Stripe/WS, Razorpay, PayPal, S3 signing, Python/Nest/Django/Spring cache+uploads+WS).
- Generated 145 projects (express, fastapi, flask, nestjs, django, spring x sqlite/postgresql/mysql/mongodb/none x store/plain briefs x cache/storage/payment variants): every generated JS passes `node --check`, every generated Python file compiles, every relative import of a shipped integration file resolves, and every integration flag in `model.py` has its file shipped.

Integration map (where each one is generated; checked on 348 generated projects)
| Integration | Express | FastAPI | Flask | NestJS | Django | Spring |
|---|---|---|---|---|---|---|
| Cache (Redis / in-memory) | yes | yes | yes | yes | yes | yes |
| Uploads: local disk | yes | yes | yes | yes | yes | yes |
| Uploads: S3-compatible / Firebase Storage | yes | yes | yes | yes | yes | yes |
| WebSocket `/ws` | yes | yes | no | yes | no | yes |
| Checkout + Stripe / Razorpay / PayPal | yes | yes | yes | yes | yes | yes |
| Firebase sign-in (ID token exchange) | yes | no | no | no | no | no |

Rules that hold everywhere: checkout + payments need a SQL database and sign-in (MongoDB / no database report them as "not generated"); WebSocket needs no database; a feature is only generated when the spec asks for it and only the chosen provider/store file is shipped.

How the parts connect (all in `backend/gen/`)
- `model.py` is the single gate: it reads the spec + stack and sets `integrations` (cache, uploads, payments, ws), `checkout`, `paymentProvider`, `storage`, `firebaseAuth`. Every generator reads only these flags.
- Each generator (`express.py`, `fastapi_gen.py`, `flask_gen.py`, `nest.py`, `django_gen.py`, `spring_gen.py`) skips template files the flags do not need and copies the provider/store variant over the base file (payments_razorpay/paypal over payments core, uploads_remote + storage_s3/firebase over uploads).
- `.env.example`, `requirements.txt` / `package.json` / `pom.xml`, README and `openapi.json` come from the same flags, so a project never lists a variable, dependency or route it does not ship.
- Optional modules are imported lazily behind the same flags (for example Express `require('../lib/firebase')` only when Firebase sign-in is on), so a plain app has no dead imports.

Checked (script on the final tree)
- File-by-file chain comparison 6F -> 6G -> 6H.1 -> ... -> 6H.5: 0 missing, 0 reverted.
- 348 projects (6 backends x sqlite/postgresql/mysql/mongodb/none x store-with-Stripe / Razorpay / PayPal and plain briefs x s3 / firebase-storage / local): every Python file compiles; every .ts has no syntax diagnostics; every .js passes `node --check`; every top-level relative import / require resolves to a shipped file; each enabled integration ships its main file. Only shared-file cases remain by design: WebSocket without cache still ships the cache module it imports, and `live` ships with cache.
- Spring: 0 Java syntax errors on a parse of the generated files; S3 signature identical across Express, Python, NestJS and Spring (see `tests/test_v2_phase6h6_storage.py`).
- Tests of every 6x step re-run: same results as before the merge (failures that remain are sandbox limits: pytest, Flask, Django, Maven not installed).

Not run here (no network): `npm install`, Maven, real Redis / S3 / Firebase / Stripe / Razorpay / PayPal, FastAPI / Django / Nest runtime, full pytest.
Phase 6 is complete. Next: Phase 7 (frontend integration + end-to-end generator checks).

## 6H.6 - S3-compatible + Firebase Storage for every backend
Uploads (`POST /api/uploads`, `GET /api/uploads/{name}`) now go to a PRIVATE bucket for FastAPI, Flask, Django, NestJS and Spring too (Express had both since 6A/6G). Chosen by the stack's `storage` value (`s3` | `firebase-storage` | `local`).
- Same rules as local uploads: sign-in rule, type from magic bytes, random names, size cap, files served only through the API; bad names never reach the bucket.
- S3: SigV4 with no SDK (urllib / fetch / java.net.http); AWS endpoints use virtual-hosted style, MinIO/R2/Spaces path style. Firebase: Admin SDK (`firebase-admin` is added to requirements / package.json / pom.xml only when used).
- Files: Python `app/storage_remote.py` + `app/uploads_core.py` (remote version); NestJS `integrations/storage.ts` + `uploads.ts`; Spring `ObjectStore` + `S3Store` | `FirebaseStore` + `UploadController`. Local storage output is unchanged.
- Tests: `tests/test_v2_phase6h6_storage.py` (per-backend files/env/deps, Python S3 round trip against a fake server, Firebase store with a stub SDK, and one signature computed by Express, Python, NestJS and Spring that must be identical). `test_s3_only_where_it_is_generated` became `test_s3_is_generated_for_every_backend_since_6h6`.
- Checked here: 87 generated projects (6 backends x 5 databases x s3/firebase/local) - every Python file compiles, every .ts has no syntax diagnostics, every .js passes `node --check`; Spring: 0 Java syntax errors on a parse of all 56 files. No other test changed result vs the 6H.5 baseline.
- Not run here (no network, no Maven, no Firebase/S3 account): `npm install`, `mvn`, real S3/MinIO/Firebase, FastAPI/Django/Nest runtime, full pytest (pytest not installed in this sandbox).
- Step 6H is complete after this (6H.1-6H.6). Next: Phase 7 (frontend integration + end-to-end generator checks).

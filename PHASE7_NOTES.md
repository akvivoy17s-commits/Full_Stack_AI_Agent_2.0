# Phase 7 - generated project quality (frontend integration + end-to-end generator checks)

New: `backend/gen/project.py` (called by `stage.run`, deterministic, zero tokens). Per generated project:
- `backend/Dockerfile` + `.dockerignore` (Express, NestJS, FastAPI, Flask, Django, Spring; non-root user, HEALTHCHECK for Node/Python).
- `docker-compose.yml` + `docker.env.example`: api + db (PostgreSQL / MySQL / MongoDB; SQLite = volume; SQL Server = bring your own) + redis when cache is on + uploads volume for local storage. Run: `cp docker.env.example docker.env && docker compose --env-file docker.env up --build`. Provider keys stay in `backend/.env`.
- `.github/workflows/ci.yml`: backend test (+ build for Nest) + `docker build`; web-app build job (skipped when no root package.json).
- `src/api/client.ts|js` (React / Vue / Svelte only): typed client from the same entities as the backend: auth with refresh-once on 401, list/get/create/update/remove per resource, checkout, payment intent, `watch()` for `/ws`. Base URL = `VITE_API_URL`.

Bug fixed (blocked Phase 6 end to end): `catalog.GENERATORS` still said cache/storage = none only, so `stage.run` refused Redis / local / S3 / Firebase storage ("planned"); Express firebase-auth was refused too. Table now matches what `model.py` generates. `test_gate_warns_about_unbuilt_parts...` adjusted (Redis no longer a gap).

Checked here: 116 stack combinations (6 backends x 5 DBs x 2 briefs x cache on/off): compose + CI parse as YAML, every TS client passes `tsc --strict`, JS client passes `node --check`; `stage.run` through the real ProjectFiles writes all new files and a second run rewrites nothing. New tests: `tests/test_v2_phase7_project.py`.
Not run here: docker build / compose up, GitHub Actions, pytest (not installed), npm install, mvn.

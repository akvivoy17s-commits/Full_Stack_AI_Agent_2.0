# Phase 8 (V2) - final verification
Run: `python verify_v2_phase8.py` -> `PHASE8_V2_REPORT.md` + `phase8_v2_evidence.json` (zero tokens, real checks only).

Matrix: 9 backends x 6 DBs (sqlite/postgresql/mysql/mongodb/mssql/none) x 2 briefs x cache on/off = 216 combos.
Per combo: selectable? generator ready? generate backend + Phase 7 extras; py ast, node --check, ts syntax, yaml/json parse, secret scan, Java brace check, `not_generated`/warnings.

Status meaning: PASS = generated + static checks clean | PARTIAL = generated, some part listed in not_generated | PLANNED = generator not built | BLOCKED = needs a tool this sandbox lacks | N/A = not selectable (e.g. Django + MongoDB).

Result: PASS 118, PARTIAL 22, PLANNED 72 (Go, ASP.NET, Laravel), FAIL 0, N/A 4.
PARTIAL = store brief on mongodb/none -> `checkout` not generated (needs SQL tables).

BLOCKED here (run on your machine): pytest suite, npm ci + tsc type-check + build, mvn/javac, go/dotnet/php, docker build/compose up, GitHub Actions, live DB/Redis/Stripe/Firebase/Ollama.
Commands: `pip install -r backend/requirements.txt pytest httpx && pytest -q`, then `cd generated_projects/<x> && docker compose up --build`.

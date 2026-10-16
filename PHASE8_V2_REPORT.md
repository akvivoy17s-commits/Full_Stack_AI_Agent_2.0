# Phase 8 (V2) - generation matrix

Static checks only (py ast, node --check, ts syntax, yaml/json parse, secret scan, route/not_generated report).

| backend | sqlite | postgresql | mysql | mongodb | mssql | none |
|---|---|---|---|---|---|---|
| express | PASS | PASS | PASS | PARTIAL | PASS | PARTIAL |
| nestjs | PASS | PASS | PASS | PARTIAL | PASS | PARTIAL |
| fastapi | PASS | PASS | PASS | PARTIAL | PASS | PARTIAL |
| flask | PASS | PASS | PASS | PARTIAL | PASS | PARTIAL |
| django | PASS | PASS | PASS | N/A | PASS | PARTIAL |
| spring | PASS | PASS | PASS | PARTIAL | PASS | PARTIAL |
| go | PLANNED | PLANNED | PLANNED | PLANNED | PLANNED | PLANNED |
| aspnet | PLANNED | PLANNED | PLANNED | PLANNED | PLANNED | PLANNED |
| laravel | PLANNED | PLANNED | PLANNED | PLANNED | PLANNED | PLANNED |

Totals: PASS=118, PARTIAL=22, BLOCKED=0, PLANNED=72, FAIL=0, N/A=4

## Not PASS (first 40)

- `express|mongodb|store|nocache` **PARTIAL** - 30 files ok; not_generated=['checkout']
- `express|mongodb|store|redis` **PARTIAL** - 33 files ok; not_generated=['checkout']
- `express|none|store|nocache` **PARTIAL** - 22 files ok; not_generated=['checkout']
- `express|none|store|redis` **PARTIAL** - 22 files ok; not_generated=['checkout']
- `nestjs|mongodb|store|nocache` **PARTIAL** - 45 files ok; not_generated=['checkout']
- `nestjs|mongodb|store|redis` **PARTIAL** - 48 files ok; not_generated=['checkout']
- `nestjs|none|store|nocache` **PARTIAL** - 31 files ok; not_generated=['checkout']
- `nestjs|none|store|redis` **PARTIAL** - 31 files ok; not_generated=['checkout']
- `fastapi|mongodb|store|nocache` **PARTIAL** - 37 files ok; not_generated=['checkout']
- `fastapi|mongodb|store|redis` **PARTIAL** - 40 files ok; not_generated=['checkout']
- `fastapi|none|store|nocache` **PARTIAL** - 25 files ok; not_generated=['checkout']
- `fastapi|none|store|redis` **PARTIAL** - 25 files ok; not_generated=['checkout']
- `flask|mongodb|store|nocache` **PARTIAL** - 37 files ok; not_generated=['checkout']
- `flask|mongodb|store|redis` **PARTIAL** - 40 files ok; not_generated=['checkout']
- `flask|none|store|nocache` **PARTIAL** - 25 files ok; not_generated=['checkout']
- `flask|none|store|redis` **PARTIAL** - 25 files ok; not_generated=['checkout']
- `django|none|store|nocache` **PARTIAL** - 30 files ok; not_generated=['checkout']
- `django|none|store|redis` **PARTIAL** - 30 files ok; not_generated=['checkout']
- `spring|mongodb|store|nocache` **PARTIAL** - 45 files ok; not_generated=['checkout']
- `spring|mongodb|store|redis` **PARTIAL** - 49 files ok; not_generated=['checkout']
- `spring|none|store|nocache` **PARTIAL** - 35 files ok; not_generated=['checkout']
- `spring|none|store|redis` **PARTIAL** - 35 files ok; not_generated=['checkout']
- `go|sqlite|college|nocache` **PLANNED** - gaps: Go (net/http) generator is planned (phase 4).
- `go|sqlite|college|redis` **PLANNED** - gaps: Go (net/http) generator is planned (phase 4).
- `go|sqlite|store|nocache` **PLANNED** - gaps: Go (net/http) generator is planned (phase 4).
- `go|sqlite|store|redis` **PLANNED** - gaps: Go (net/http) generator is planned (phase 4).
- `go|postgresql|college|nocache` **PLANNED** - gaps: Go (net/http) generator is planned (phase 4).
- `go|postgresql|college|redis` **PLANNED** - gaps: Go (net/http) generator is planned (phase 4).
- `go|postgresql|store|nocache` **PLANNED** - gaps: Go (net/http) generator is planned (phase 4).
- `go|postgresql|store|redis` **PLANNED** - gaps: Go (net/http) generator is planned (phase 4).
- `go|mysql|college|nocache` **PLANNED** - gaps: Go (net/http) generator is planned (phase 4).
- `go|mysql|college|redis` **PLANNED** - gaps: Go (net/http) generator is planned (phase 4).
- `go|mysql|store|nocache` **PLANNED** - gaps: Go (net/http) generator is planned (phase 4).
- `go|mysql|store|redis` **PLANNED** - gaps: Go (net/http) generator is planned (phase 4).
- `go|mongodb|college|nocache` **PLANNED** - gaps: Go (net/http) generator is planned (phase 4).
- `go|mongodb|college|redis` **PLANNED** - gaps: Go (net/http) generator is planned (phase 4).
- `go|mongodb|store|nocache` **PLANNED** - gaps: Go (net/http) generator is planned (phase 4).
- `go|mongodb|store|redis` **PLANNED** - gaps: Go (net/http) generator is planned (phase 4).
- `go|mssql|college|nocache` **PLANNED** - gaps: Go (net/http) generator is planned (phase 4).
- `go|mssql|college|redis` **PLANNED** - gaps: Go (net/http) generator is planned (phase 4).

## BLOCKED here (needs your machine)

- tsc type-check w/ deps, npm ci/build: tsc found, deps not installed -> BLOCKED
- pytest suite: pytest missing -> BLOCKED
- javac/mvn (Spring compile): no javac, mvn missing -> BLOCKED
- go / dotnet / php toolchains: missing -> BLOCKED
- docker build/compose up, GitHub Actions, live DB/Redis/Stripe/Firebase: BLOCKED

# Phase 3 - Stack resolver + fallback correctness
- Fallback is now tiered: (1) keep requested backend, switch DB to SQLite/auth none; (2) Express+SQLite; (3) frontend only. Each tier accepted only if ok, not blocking, coverage ready.
  Before: any unsupported combo jumped straight to Express. Now "Django + MongoDB" -> Django + SQLite.
- Assumptions now name requested vs chosen stack.
- New _named_tech_notes(): reports when an explicitly named tech (Go, Angular, Vue, Svelte, Next, ASP.NET, Laravel...) was not selected. Previously silent (Go -> Express with no message).
- tests/test_autopilot_resolver.py (3 tests).
- Verified: 11 probe prompts resolve ok; mismatch notes correct on 8 prompts (resolver run standalone with real stack engine). pytest/fastapi not installed, so suite NOT run.

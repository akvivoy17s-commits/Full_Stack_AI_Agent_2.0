# Phase 2 - Prompt classifier hardening
- backend/api/autopilot.py: _APP_PROMPT now matches todos, task management/list, booking(s), appointment(s), scheduler, invoice, kanban, "<x> management", expense, notes, plural trackers.
- _MARKETING_PROMPT: "portfolio" is marketing only as "portfolio website/site/page" or a bare leading "portfolio"; "investment/stock/crypto portfolio tracker" is now an app.
- Specialist (ecommerce/chat) precedence unchanged.
- tests/test_autopilot_classifier.py: 16 parametrized cases.
- Verified: all 22 probe prompts classify as expected (regex run standalone), py_compile OK. pytest/fastapi not installed here, so suite NOT run.

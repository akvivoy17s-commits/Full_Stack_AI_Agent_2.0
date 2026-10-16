# Phase 5 - Planner + task pipeline integration
- Problem: planner.layout_for had its own regexes, disagreeing with Autopilot (e.g. "task management tool", "booking app", "Kanban board" -> landing; "investment portfolio tracker" -> portfolio). Only /autobuild was protected by the app_shell flag; wizard and re-plan paths were not.
- NEW backend/agent/intent.py: single source of truth (APP/MARKETING/SPECIALIST regexes + is_app_prompt). autopilot.py imports them (old names kept as aliases, Phase 2 tests unaffected); planner.layout_for uses them. Removed planner.APP_INTENT.
- Guards kept: kind=management/cms -> app; dashboard/analytics -> dashboard; bare "dashboard widget" on a landing brief stays landing (allow_dashboard=False); "personal/my/online/designer... portfolio" stays marketing.
- Token cut: blueprint LLM call max_tokens 1200 -> 700 when layout=app (app shell is deterministic; only brand/design/motion needed).
- Diffed old vs new layout_for over 24 prompts x 7 kinds: only intended changes (more prompts -> app). 
- tests/test_phase5_integration.py. NOT run (pytest/pydantic/httpx absent here); layout rules + classifier lists verified by standalone execution.
- Note: tests/test_spec_project.py:176 expects layout "dashboard" for kind=management and "portfolio" for kind=portfolio("my work"); old code already returned app/landing there, so those assertions look stale - if pytest flags them, send me the output.

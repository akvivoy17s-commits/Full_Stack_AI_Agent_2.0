# Phase 4 - Planner, requirement analysis, task execution, progress tracking
Overlay: unzip over the project root (same paths). 0 extra LLM tokens (all rule based).

New: backend/agent/requirements.py (covered/planned/gap + blocking questions), backend/agent/progress.py (step tracker, percent, PASS/PARTIAL/BLOCKED/FAIL verdict), tests/test_phase4.py
Changed: backend/agent/orchestrator.py (run/edit tracked step by step), backend/agent/tasks.py (steps+percent+outcome in result), backend/api/tasks.py (GET /tasks/{id}/progress, GET /projects/{id}/requirements), backend/storage/db.py (task_steps table, auto-created)

Run: python -m pytest tests/test_phase4.py -q

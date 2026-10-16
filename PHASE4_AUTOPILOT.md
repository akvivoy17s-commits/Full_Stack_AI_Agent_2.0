# Phase 4 - App-shell generator (TS build errors)
- Reported errors re-checked in THIS tree: (a) generated client.ts: 23 stack combos (6 backends x sqlite/pg+redis/mongo/none) pass `tsc --strict`, 0 failures; (b) src/lib/MotionEffects.tsx + motion.ts exist in templates/react and are in react_engine.STATIC; (c) html2jsx turns bare tokens (lift, md:grid-cols-3) into className, boolean attrs -> defaultChecked etc. => no repro, already fixed upstream.
- app_engine.py App.tsx generated for 5 prompts (API on/off, JWT) type-checks with tsc strict (stubbed React types, noImplicitAny off because stub): 0 errors.
- NEW: domain-aware default entities (_domain_entities): CRM -> Customer+Deal, booking -> Booking, inventory -> Item, invoice -> Invoice. Before, these prompts fell back to a generic "Task" entity when the spec had none.
- tests/test_app_engine_domains.py (7 cases).
- NOT verified: real @types/react (no node_modules/network), vite build, pytest.

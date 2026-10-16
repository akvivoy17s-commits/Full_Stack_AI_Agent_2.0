# Phase 7 - Autopilot UX
- Gap: /autobuild returns assumptions (stack downgrades, named-tech mismatches from Phase 3) but the UI never showed them, so the user could not see what Autopilot decided.
- PromptPanel.tsx: new "Autopilot decisions (N)" card for prompt-only projects, read from project.stack_config.autopilot.assumptions (persisted by the backend, so it survives reloads and re-opening the project). Shows a "no assumptions needed" line when empty, plus a reminder to review before relying on the result.
- services/api.ts: AutopilotInfo type + ProjectState.stack_config.autopilot (2 small edits: new interface before ProjectState, `; autopilot?: AutopilotInfo` added to stack_config).
- Verified: PromptPanel.tsx + api.ts type-check clean with tsc strict (React/lucide types stubbed: node_modules not installable here). NOT run: npm run build, browser check.

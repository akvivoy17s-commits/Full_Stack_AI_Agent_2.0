# Full-Stack AI Agent — Expanded Language and Tool Knowledge

## Purpose

This incremental patch expands the existing local guide-retrieval system with the eight Markdown guides supplied in `fullstack_web_development_complete_concepts_tools_functions_guide.zip`. It does not replace the existing agent or rewrite unrelated project files.

## New reference guides

- `fullstack_web_development_complete_concepts_tools_functions_guide.md` — full-stack architecture, frontend/backend/database integration, tools, testing, security, and deployment.
- `nestjs_backend_complete_syntax_functions_guide.md` — NestJS + TypeScript backend patterns.
- `python_for_ai_complete_syntax_functions_guide.md` — Python fundamentals and AI/ML/LLM/RAG patterns.
- `react_js_typescript_full_stack_complete_guide.md` — React, JSX/TSX, TypeScript components, hooks, APIs, tests, and production patterns.
- `rust_backend_complete_syntax_functions_guide.md` — Rust, ownership/types, Axum, Tokio, SQLx, backend APIs, and tests.
- `springboot_java_full_stack_complete_guide.md` — Java + Spring Boot, REST, data access, security, testing, deployment.
- `sql_complete_full_stack_syntax_functions_guide.md` — SQL syntax, schemas, queries, dialect differences, performance, and safety.
- `tailwind_css_complete_syntax_utilities_guide.md` — Tailwind utility syntax, variants, responsive styles, React integration, and v3/v4 differences.

## Agent behavior changes

- Guide routing now recognizes these frameworks, languages, file extensions, configuration filenames, and common database/tool terms.
- TypeScript/TSX file paths can retrieve React/TypeScript references; `.py`, `.rs`, `.java`, `.sql`, and related project files select matching references.
- Single-word aliases are matched at word boundaries to avoid false positives such as matching `React` merely because a prompt contains “reactive forms.”
- The retrieval budget remains bounded; the agent receives only selected excerpts rather than the whole knowledge library for every model call.
- Prompts explicitly instruct the model to prefer manifests, installed versions, nearby code, compiler/parser diagnostics, and tests over examples in guides; avoid invented imports/APIs and incompatible major versions; preserve unrelated changes; and report verification honestly.
- Existing source guides are still expected to be present from the prior knowledge-base update. This patch contains only the eight new guides and the updated retrieval/test files.

## Verification

- Python compile check for `backend/knowledge/guide_retriever.py`: passed.
- Guide retrieval test suite: 21 passed, 1 skipped.
- The single skipped integration test needs the host project's `backend.config` module, which is not part of this changed-files-only patch staging area. Run the suite again in the actual full repository.

## Important limitation

This is retrieval-augmented guidance, not model fine-tuning. It helps the model consult relevant concepts when a task is planned, generated, or repaired, but it cannot guarantee zero coding mistakes or literal coverage of every current and future API. The agent must continue to validate actual project code with its compiler/typechecker, linter, build, tests, and browser checks where available.

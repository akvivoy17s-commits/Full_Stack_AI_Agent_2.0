# Bundled Language and Tool Guide Knowledge Update

## What this patch changes

This patch adds a local, dependency-free retrieval layer over the eight Markdown guides supplied by the user:

- MongoDB full-stack guide
- Angular + TypeScript guide
- CSS, responsive design, 2D/3D and time-based animation guide
- Django + Python guide
- Docker and Docker Compose guide
- Flask + FastAPI + Python web guide
- HTML and semantic web structure guide
- JavaScript, Node.js, Express and browser APIs guide

The complete documents are stored under `backend/knowledge/guides/`. `backend/knowledge/guide_retriever.py` splits them by headings and bounded chunks, matches user requests / selected stack / affected file paths, and appends only short relevant excerpts to real model requests for blueprint planning, frontend section generation, and source-code repair. This protects the small local model's context window from the cost of loading every guide on every call.

The planner and section context now include the selected technology configuration so guide retrieval can prefer the stack actually being used. The model instructions clarify that the guides are references, not guarantees: actual repository manifests, installed versions, neighboring code, compiler diagnostics, and tests take precedence. When TypeScript concepts are retrieved from the Angular guide for a non-Angular project, Angular-specific APIs are excluded.

## Scope and limitations

This is a retrieval-backed reference library, not a fine-tuning or model-training operation. It gives the agent access to the supplied concepts at generation and repair time; it cannot guarantee zero coding mistakes or 100% knowledge across all language versions. Not every guide is included in every model request—only relevant excerpts are, within a bounded character budget. The existing generator/toolchain still determines which languages and frameworks can be scaffolded directly, and native compilers, linters, tests, and build checks remain the verification authority.

## Validation

- `python -m compileall -q backend`: passed.
- `pytest -q tests/test_guide_retriever.py`: 10 passed, including tests for all eight bundled guide files, focused retrieval, bounded excerpts, and actual LLM request enrichment.
- A broader selected regression run against the assembled pre-existing patch set is not completely green because unrelated existing tests have baseline mismatches (including mocked blueprint schema, terminal allowlist, and authentication scaffold assertions). Those are outside this knowledge-retrieval patch and are not represented as passing.

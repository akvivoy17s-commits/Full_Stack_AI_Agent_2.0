# Full-Stack AI Developer Agent

A local-first AI website developer that keeps the existing **React + TypeScript + Vite** UI and **FastAPI + Ollama** agent, with a rules-based technology selector, project specification/memory, and deterministic backend generators. The technology selector uses no LLM tokens. Ollama is used for the visual website-generation/editing workflow.

> **Honest scope:** this is a working, partially multi-stack agent—not yet a universal generator for every technology in the catalog. The catalog includes both implemented and planned choices. Unsupported choices remain visible but are labelled as planned or blocked; the agent must not claim they were generated.

## Prompt-only Autopilot

Use the **Autopilot Builder** in the workspace to describe the website or web app once and start generation without stepping through the technology, data, and review wizard. The backend resolves a stack from the generators implemented in this repository, records its assumptions, creates the project, and queues the generation task. For common data-management prompts (for example, to-do lists, notes, trackers, CRM and admin workspaces), the generator creates an interactive React + TypeScript workspace with search, forms, create/edit/delete flows and loading, error, and empty states. It uses the generated API only when that backend/database combination is supported; otherwise it clearly uses browser-local storage. Calculator prompts use a small deterministic generator and a safe expression parser. The normal generation/verification/repair pipeline remains enabled.

**Important limit:** no software generator can promise zero bugs or perfect behavior for every possible prompt. Autopilot minimizes follow-up questions and performs automated checks, but complex requirements, third-party integrations, real API keys/OAuth/payment credentials, cloud infrastructure, and production deployment still require the appropriate configuration and final review. The selected stack, assumptions, and verification report should be checked before production use.

## Current generation support

| Area | Available now | Important limit |
|---|---|---|
| Frontend | HTML + CSS + JavaScript; React + TypeScript + Vite | Angular, Next.js, Vue/Nuxt, Svelte/SvelteKit, SolidJS are catalogued but their project generators are not implemented. |
| Backend | Express (JavaScript), NestJS (TypeScript), FastAPI, Flask, Django | ASP.NET Core, Laravel, Go, and full Spring Boot are not registered generators. Spring Boot Part A is incomplete groundwork only. |
| Database | SQLite, PostgreSQL, MySQL and MongoDB for supported Express/NestJS/FastAPI/Flask combinations; SQLite/PostgreSQL/MySQL for Django | SQL Server, Firestore and Realtime Database are not generated integrations yet. Compatibility is checked per framework/ORM. |
| Authentication | No auth or generated JWT access/refresh flow for supported backends | External OAuth/Firebase Auth integration is not generated yet. Supply secure environment values for JWT secrets. |
| Cache / storage / Python AI | Options are shown in the catalog | Redis, production object storage, and the separate Python AI-service generator are planned, not wired into current backend generators. |
| Testing | Agent’s own static/build/browser/a11y verification and generated backend test scaffolding where provided | Optional frontend test-runner selections such as Vitest are catalogued but not scaffolded for new frontend projects yet. |

## Features

- Existing frontend workspace, project sidebar, code/file view, preview/report panels, Ollama status and settings are retained.
- Technology configuration UI supports **Automatic**, **Manual**, and **Hybrid** modes. It shows compatible options, reasons, warnings, generation gaps, and the resolved stack before project creation.
- Technology preferences are saved in browser local storage. Project stack, selection reasons, application spec, and project memory are stored with the project; secrets are not stored in the project memory.
- Automatic stack selection is bounded by the generators actually present in this repository. Manual selections are not silently replaced: incompatible/planned options are reported.
- Project spec describes pages, features, entities, API contracts, environment-variable names, security/test needs, assumptions, and gaps. Stack changes refresh the spec and project memory together.
- Backend generation is deterministic and reports generated files, retained user-edited files, commands, and unsupported requirements. It does not use fake production API responses to hide gaps.
- Existing checkpoints, project file safety validation, task progress/events, error reporting, and verify/repair workflow are retained.
- Local Ollama integration defaults to `qwen2.5-coder:7b`; a vision model is optional.

## Requirements

- Python 3.11 or newer (Python 3.11 is the recommended baseline for this repository).
- Node.js 18+ and npm (needed for the frontend and generated React projects).
- Ollama installed locally with a coding model pulled.
- Chromium installed through Playwright if real browser tests/screenshots are required; browser checks can be skipped when unavailable.

## Run on Windows (PowerShell)

From the extracted project directory:

```powershell
# 1. Create and activate a Python environment
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r backend\requirements.txt

# 2. Create local configuration (keep .env private)
Copy-Item .env.example .env

# 3. Install browser runtime when using browser verification
python -m playwright install chromium

# 4. Start Ollama in a separate terminal
ollama pull qwen2.5-coder:7b
ollama serve

# 5. Start the API from the project root
uvicorn backend.main:app --reload
```

In another PowerShell terminal:

```powershell
cd frontend
npm ci
npm run dev
```

Open `http://localhost:5173`. API documentation is available at `http://localhost:8000/docs`.

### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
cp .env.example .env
python -m playwright install chromium
ollama pull qwen2.5-coder:7b
uvicorn backend.main:app --reload
```

In a second terminal run `cd frontend && npm ci && npm run dev`.

## Environment configuration

The committed `.env.example` contains placeholder/default configuration only. Adjust as needed:

- `LLM_PROVIDER` — active provider: `ollama`, `openai`, `gemini`, `openrouter`, `groq`, `deepseek`, or `anthropic`.
- `LLM_FALLBACK_PROVIDER` — optional explicit fallback provider; blank disables automatic provider fallback.
- Provider configuration uses one `*_BASE_URL`, `*_MODEL`, and `*_API_KEY` trio per provider. Ollama needs no API key. Gemini, OpenRouter, Groq and DeepSeek use the OpenAI-compatible Chat Completions adapter; Anthropic Claude uses its native Messages API adapter.
- `OLLAMA_BASE_URL` and `OLLAMA_MODEL` default to `http://localhost:11434` and `qwen2.5-coder:7b`.
- `OLLAMA_VISION_MODEL` — optional vision-capable local Ollama model; leave empty to disable.
- `OLLAMA_TIMEOUT_S`, `OLLAMA_NUM_CTX`, `OLLAMA_KEEP_ALIVE`, `MAX_CONCURRENCY`, and `MAX_REPAIR_LOOPS` — runtime/resource controls. `OLLAMA_KEEP_ALIVE=30m` avoids repeatedly unloading the model between pipeline stages.
- Provider keys can be entered from backend Settings; the server writes keys to the ignored local `.env` file and process environment, never SQLite or API responses. Use HTTPS for all remote provider endpoints.
- `GENERATION_PROFILE` — `fast` (default, shorter outputs for CPU-only computers), `balanced`, or `quality`; selectable from **Settings → Generation profile**. The profiles cap LLM output tokens but keep verification/security checks enabled.
- `SECTION_MAX_TOKENS` — maximum requested token budget for each section before the selected generation profile cap is applied.
- `DATA_DIR`, `GENERATED_DIR` — optional location overrides for runtime/project data.
- `CORS_ORIGINS` — allowed browser origins, default local Vite addresses.

Do not commit `.env`, real API keys, database passwords, local databases, checkpoint archives, generated projects, `.venv`, or `node_modules`.

## Useful commands

```powershell
# Frontend
cd frontend
npm run lint
npm run typecheck
npm run build

# Backend tests (from project root; keep the agent offline during unit tests)
$env:MOCK_LLM = "1"
$env:USE_BROWSER = "0"
python -m pytest -q

# Reset test-only runtime data to an isolated location before running all tests
$env:DATA_DIR = "$env:TEMP\fullstack-agent-test-data"
$env:GENERATED_DIR = "$env:TEMP\fullstack-agent-test-generated"
python -m pytest -q
```

The `MOCK_LLM=1` mode is strictly for automated tests and is not real model output. `USE_BROWSER=0` skips live browser checks in the backend test process. To test with the actual model/browser, unset those variables and use the normal UI workflow.

## API overview

- `GET /health`, `GET /ollama/status`, and `POST /ollama/check`
- `GET /providers` and `GET /providers/{provider}/models` for provider discovery and model lists
- `GET /settings` and `PUT /settings` (provider/model/base URL are editable; API keys are write-only and never returned)
- `GET /stack/catalog`, `POST /stack/resolve`
- `POST /projects` (legacy HTML/React flow, or stack mode + preferences)
- `GET /projects/{id}/stack`, `PUT /projects/{id}/stack`
- `GET /projects/{id}/spec`, `PUT /projects/{id}/spec`, `GET /projects/{id}/memory`
- `GET|POST /projects/{id}/backend` to inspect/generate the selected backend explicitly
- `POST /projects/{id}/tasks` and `GET /tasks/{id}`, `/tasks/{id}/events`, `/tasks/{id}/stream`
- Project files, preview, report, checkpoints, export, repair history and settings endpoints

## Repository map

```text
backend/
  agent/       orchestration, context, task manager, prompts, project state
  api/         FastAPI routes for system, tasks, stack, spec and backend generation
  engines/     HTML/React generation, design, animation and repair engines
  gen/         deterministic backend generators and generator templates
  memory/      project metadata/history and specification memory
  spec/        requirements-to-application-spec composer/templates
  stack/       technology catalog, analyzer, compatibility rules and resolver
  storage/     SQLite metadata and checkpoint support
  tools/       terminal/browser/project-file/validation/security helpers
frontend/src/
  workspace/   project workspace, prompt panel, technology configuration, code and activity panels
  services/    frontend API client
  landing/     landing page components
tests/         technology, spec, generator, API and pipeline regression tests
templates/     HTML page layouts and shared animation/design templates
generated_projects/  generated user projects (runtime output; not source templates)
```

## Verification status and limitations

The Python test suite is designed to run without an Ollama server by setting `MOCK_LLM=1` and without Chromium by setting `USE_BROWSER=0`. Tests validate orchestration and deterministic generators, but passing generator tests are not equivalent to running every generated framework, database driver, or external service against a production environment.

The frontend dependencies must be installed before TypeScript type-checking, linting or production builds can be validated. In offline environments `npm ci` may fail if the npm cache does not contain the locked packages. A blocked package download is an environment limitation, not evidence that the frontend build passed.

This software is a development agent, not a hosted production service. Before exposing it to a network, review authentication/access control and process isolation for the environment in which it will run. Use non-production credentials during development and back up generated project data before making destructive changes.

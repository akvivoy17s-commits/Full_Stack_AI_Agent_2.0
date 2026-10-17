"""Single-prompt project creation: infer a checked-in stack, save the project and queue generation."""
from __future__ import annotations

import re
import shutil
import uuid
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator

from backend.agent.state import AgentState
from backend.agent import tasks
from backend.memory import history, project_store
from backend.storage import db
from backend.tools.project_files import ProjectFiles
from backend import stack as stack_engine, spec as spec_engine
from backend.spec import memory as spec_memory
from backend.gen import stage as backend_generation

router = APIRouter()

from backend.agent.intent import APP_PROMPT as _APP_PROMPT, MARKETING_PROMPT as _MARKETING_PROMPT, SPECIALIST_PROMPT as _SPECIALIST_PROMPT, is_app_prompt


class AutoBuildRequest(BaseModel):
    prompt: str = Field(min_length=5, max_length=15000)

    @field_validator("prompt")
    @classmethod
    def validate_prompt(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 5:
            raise ValueError("Describe the website or app in at least 5 characters.")
        if any(ord(char) < 32 and char not in "\n\r\t" for char in value):
            raise ValueError("The prompt contains unsupported control characters.")
        return value


_NAMED_TECH = (
    ("frontend", "angular", r"\bangular\b"), ("frontend", "vue", r"\bvue(\.?js)?\b|\bnuxt\b"),
    ("frontend", "svelte", r"\bsvelte(kit)?\b"), ("frontend", "next", r"\bnext\.?js\b"),
    ("backend", "go", r"\bgolang\b|\bgin\b|\bgo (backend|api|server)\b|\bin go\b|\bwith go\b"),
    ("backend", "aspnet", r"\basp\.?net\b|\.net core\b|\bc#"), ("backend", "laravel", r"\blaravel\b|\bphp\b"),
    ("backend", "django", r"\bdjango\b"), ("backend", "flask", r"\bflask\b"), ("backend", "fastapi", r"\bfast-?api\b"),
    ("backend", "nestjs", r"\bnest(js)?\b"), ("backend", "spring", r"\bspring( boot)?\b"), ("backend", "express", r"\bexpress(js)?\b"),
)


def _named_tech_notes(prompt: str, stack: dict) -> list[str]:
    """Tell the user when a technology they named explicitly was not the one selected."""
    notes = []
    for field, value, pattern in _NAMED_TECH:
        if re.search(pattern, prompt, re.I) and stack.get(field) != value:
            notes.append(f"You named {value}, but the selected {field} is {stack.get(field) or 'none'} because {value} is not available for this combination in this release.")
    return notes[:3]


_FEATURE_NOTES = (
    (r"\b(stripe|razorpay|paypal|payments?|subscriptions?)\b", None,
     "Payments were mentioned: Autopilot app shells do not configure payment providers (real keys and a reviewed checkout flow are required), so none is wired."),
    (r"\b(real-?time|websockets?|push notifications?|e-?mail notifications?|sms)\b", None,
     "Real-time updates or notifications were mentioned: they are not generated in the prompt-only app shell."),
    (r"\b(log-?in|sign[- ]?in|user accounts?|authentication|roles?)\b", "auth",
     "Login or accounts were mentioned, but the selected stack has no authentication, so the generated app has no sign-in."),
)


def _feature_notes(prompt: str, stack: dict, is_app: bool) -> list[str]:
    """Say what the app shell does NOT implement, instead of silently ignoring it."""
    if not is_app:
        return []
    out = []
    for pattern, needs, note in _FEATURE_NOTES:
        if re.search(pattern, prompt, re.I) and (needs is None or stack.get(needs) in (None, "", "none")):
            out.append(note)
    return out


def resolve_prompt(prompt: str) -> tuple[dict, str, list[str], bool]:
    """Resolve a prompt to a generator-backed stack, without asking the user follow-up questions."""
    is_app = is_app_prompt(prompt)
    assumptions: list[str] = []
    if is_app:
        prefs = {"frontend": "react", "frontend_lang": "ts"}
        res = stack_engine.resolve("hybrid", prefs, prompt)
        assumptions.append("Interactive app detected: React + TypeScript selected for the supported app-shell generator.")
    else:
        res = stack_engine.resolve("automatic", {}, prompt)
    stack = res.get("stack") or {}
    front_supported = stack.get("frontend") == "html" or (stack.get("frontend") == "react" and stack.get("frontend_lang") == "ts")
    api_coverage = backend_generation.coverage(stack)
    needs_fallback = (not res.get("ok") or not front_supported or bool(res.get("blocking")))
    if stack.get("backend") not in (None, "", "none") and not api_coverage.get("ready"):
        needs_fallback = True
    if needs_fallback:
        requested = {k: stack.get(k) for k in ("frontend", "backend", "database")}
        wants_api = bool((res.get("requirements") or {}).get("needs", {}).get("backend")) or stack.get("backend") not in (None, "", "none")
        base = {"frontend": "react", "frontend_lang": "ts"}
        tiers: list[tuple[dict, str]] = []
        if wants_api and stack.get("backend") not in (None, "", "none", "express"):
            keep = dict(base, backend=stack["backend"], database="sqlite", auth="none")
            if stack.get("backend_lang"):
                keep["backend_lang"] = stack["backend_lang"]
            tiers.append((keep, "kept the requested backend and switched the database to SQLite"))
        if wants_api:
            tiers.append((dict(base, backend="express", backend_lang="js", database="sqlite", auth="none"), "switched to Express + SQLite"))
        tiers.append((dict(base, backend="none", database="none", auth="none"), "reduced to the React + TypeScript frontend only"))
        chosen = None
        for prefs, note in tiers:
            cand = stack_engine.resolve("hybrid", prefs, prompt)
            cstack = cand.get("stack") or {}
            if cand.get("ok") and not cand.get("blocking") and (cstack.get("backend") in (None, "", "none") or backend_generation.coverage(cstack).get("ready")):
                chosen = (cand, note)
                break
        if chosen is None:
            raise_stack = stack_engine.resolve("hybrid", dict(base, backend="none", database="none", auth="none"), prompt)
            chosen = (raise_stack, "reduced to the React + TypeScript frontend only")
        res, note = chosen
        got = res.get("stack") or {}
        want = ", ".join(f"{k}={v}" for k, v in requested.items() if v not in (None, "", "none")) or "the inferred stack"
        assumptions.append(f"Requested ({want}) is not fully generated in this release; {note} (now {got.get('frontend')}/{got.get('backend') or 'none'}/{got.get('database') or 'none'}).")
        stack = got
    assumptions.extend(n for n in _named_tech_notes(prompt, stack) if not any(n[:20] in a for a in assumptions))
    assumptions.extend(n for n in _feature_notes(prompt, stack, is_app) if n not in assumptions)
    if is_app:
        assumptions.append("Data fields and core screens are inferred from the prompt; you can refine the generated source afterwards.")
    if stack.get("backend") not in (None, "", "none") and not backend_generation.coverage(stack).get("ready"):
        assumptions.append("This backend is not covered by the current generator; API behavior will be reported as unavailable rather than simulated.")
    return res, stack_engine.legacy_stack(stack) or "react", assumptions, is_app


@router.post("/autobuild", status_code=202)
def autobuild(body: AutoBuildRequest):
    prompt = body.prompt.strip()
    res, legacy, assumptions, is_app = resolve_prompt(prompt)
    if not res.get("ok"):
        details = "; ".join(str(e.get("msg", "stack resolution failed")) for e in res.get("errors", []))
        raise HTTPException(422, details or "Could not choose a supported technology stack for this prompt.")
    pid = re.sub(r"[^a-z0-9]+", "-", prompt.lower())[:24].strip("-") + "-" + uuid.uuid4().hex[:6]
    state = AgentState(project_id=pid, brief=prompt, stack=legacy, stack_config=stack_engine.config_of(res))
    state.stack_config["autopilot"] = {"prompt_only": True, "app_shell": is_app, "assumptions": assumptions}
    try:
        spec, _ = spec_engine.ensure(state)
        spec_memory.refresh(state, spec, "agent")
        project_store.save(state)
        db.upsert_project(pid, prompt)
        history.add(pid, "user", prompt)
        task = tasks.submit(pid, "generate", {})
    except Exception as exc:
        shutil.rmtree(ProjectFiles(pid).root, ignore_errors=True)
        db.delete_project(pid)
        raise HTTPException(500, "Could not queue the autonomous build. Check the backend logs and model connection.") from exc
    return {
        "project_id": pid,
        "task_id": task.get("id"),
        "stack": res.get("stack", {}),
        "summary": res.get("summary", ""),
        "assumptions": assumptions,
        "autopilot": True,
    }

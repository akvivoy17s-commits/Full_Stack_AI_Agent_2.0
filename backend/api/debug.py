"""Project-aware debugging endpoint: collect evidence, propose minimal patches, and verify actual results."""
from __future__ import annotations

import json
import re
from pathlib import PurePosixPath

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.agent import llm
from backend.api.tasks import _project
from backend.storage import checkpoints, db
from backend.tools import project_scanner
from backend.tools.project_files import ProjectFiles, is_secret
from backend.tools.redact import redact

router = APIRouter()
EDITABLE = {".html", ".htm", ".css", ".scss", ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx", ".json", ".py", ".vue", ".svelte", ".go", ".rs", ".java", ".kt", ".php", ".rb", ".sql", ".yml", ".yaml", ".toml", ".xml", ".md"}
PROTECTED = re.compile(r"(^|/)(tests?|__tests__|\.agent|node_modules|\.git|dist|build|target|\.venv|venv)/|(^|/)(package-lock\.json|pnpm-lock\.yaml|yarn\.lock|poetry\.lock|\.env[^/]*)$", re.I)
SUPPRESS = re.compile(r"eslint-disable|@ts-ignore|@ts-nocheck|noqa|type:\s*ignore|pytest\.mark\.skip|\.skip\(", re.I)


class DebugRequest(BaseModel):
    error_text: str = Field(min_length=3, max_length=12000)
    apply_fixes: bool = True


def _diagnostic_text(error: str, path: str, rel: str) -> bool:
    base = PurePosixPath(rel).name.lower()
    p = path.replace("\\", "/").strip().lower()
    return rel.lower() in p or base in p or base in error.lower()


def _pick_context(pf: ProjectFiles, error: str, files: list[str]) -> list[dict]:
    error_l = error.lower()
    scored: list[tuple[int, str]] = []
    path_hints = re.findall(r"(?:[A-Za-z]:)?[\w./\\-]+\.(?:tsx?|jsx?|js|mjs|cjs|py|css|html?|json|vue|svelte|java|go|rs)\b", error)
    # When a concrete source path is present in the error, use that exact project file
    # as the diagnostic context. Falling back to loosely scored files can accidentally
    # authorize an AI patch to an unrelated file that happened to be in the context.
    explicit_matches: list[str] = []
    for hint in path_hints:
        normalized_hint = hint.replace("\\", "/").strip("./").lower()
        normalized_hint = normalized_hint.split(":", 1)[0]
        matches = [f for f in files if f.lower() == normalized_hint or f.lower().endswith("/" + normalized_hint)]
        if not matches:
            basename = PurePosixPath(normalized_hint).name
            basename_matches = [f for f in files if PurePosixPath(f).name.lower() == basename]
            if len(basename_matches) == 1:
                matches = basename_matches
        explicit_matches.extend(matches)
    explicit_matches = list(dict.fromkeys(
        f for f in explicit_matches
        if not PROTECTED.search(f) and not is_secret(f) and PurePosixPath(f).suffix.lower() in EDITABLE
    ))
    if explicit_matches:
        ordered = explicit_matches[:8]
    else:
        ordered = []
    for rel in files:
        if PROTECTED.search(rel) or is_secret(rel):
            continue
        ext = PurePosixPath(rel).suffix.lower()
        if ext not in EDITABLE:
            continue
        lower = rel.lower()
        score = 0
        if any(_diagnostic_text(error, hint, rel) for hint in path_hints): score += 15
        parts = set(PurePosixPath(rel).parts)
        score += 4 if "src" in parts else 0
        score += 2 if PurePosixPath(rel).name.lower() in {"app.tsx", "app.jsx", "main.tsx", "main.ts", "main.py", "app.py", "server.js", "package.json", "tsconfig.json", "vite.config.ts", "vite.config.js"} else 0
        stem = PurePosixPath(rel).stem.lower()
        for token in re.findall(r"[a-z][a-z0-9_]{2,}", error_l):
            if token in stem or token in lower: score += 2
        if ext in (".tsx", ".jsx", ".ts", ".js", ".py"): score += 1
        if score:
            scored.append((score, rel))
    if not ordered:
        if not scored:
            scored = [(0, f) for f in files if not PROTECTED.search(f) and PurePosixPath(f).suffix.lower() in EDITABLE][:6]
        ordered = [f for _, f in sorted(scored, key=lambda x: (-x[0], len(x[1]), x[1]))[:8]]
    context_files = []
    budget = 11500
    for rel in ordered:
        try:
            source = pf.read(rel)
        except (OSError, ValueError, UnicodeError):
            continue
        if not source: continue
        remaining = budget - sum(len(x["content"]) for x in context_files)
        if remaining <= 0: break
        clip = min(2200, remaining)
        context_files.append({"path": rel, "content": source[:clip]})
    return context_files


def _parse_diagnostics(value, allowed_paths: set[str]) -> list[dict]:
    result = []
    if not isinstance(value, list): return result
    for row in value[:25]:
        if not isinstance(row, dict): continue
        file = str(row.get("file") or "")[:300].replace("\\", "/")
        if file and file not in allowed_paths: file = ""
        line = row.get("line")
        if not isinstance(line, int) or line < 1: line = None
        sev = str(row.get("severity", "warning")).lower()
        if sev not in ("error", "warning", "info"): sev = "warning"
        message = redact(str(row.get("message") or ""))[:500]
        if message: result.append({"severity": sev, "file": file, "line": line, "message": message})
    return result


def _safe_patches(value, pf: ProjectFiles, allowed_paths: set[str]) -> list[dict]:
    result = []
    if not isinstance(value, list): return result
    for row in value[:3]:
        if not isinstance(row, dict): continue
        rel = str(row.get("file") or "").replace("\\", "/").strip()
        old, new = row.get("old"), row.get("new")
        reason = redact(str(row.get("reason") or ""))[:250]
        if not rel or rel not in allowed_paths or not isinstance(old, str) or not isinstance(new, str): continue
        if rel.startswith("/") or ".." in rel.split("/") or ":" in rel or PROTECTED.search(rel) or is_secret(rel): continue
        if PurePosixPath(rel).suffix.lower() not in EDITABLE or not (0 < len(old) <= 500) or len(new) > 3000 or old == new or SUPPRESS.search(new): continue
        try:
            if pf.read(rel).count(old) != 1: continue
        except (OSError, ValueError, UnicodeError):
            continue
        result.append({"file": rel, "old": old, "new": new, "reason": reason})
    return result


@router.post("/projects/{pid}/debug")
def debug_project(pid: str, body: DebugRequest):
    _project(pid)
    if db.active_task(pid):
        raise HTTPException(409, "project has a running task; cancel it first")
    pf = ProjectFiles(pid)
    error_text = redact(body.error_text.strip())[:12000]
    file_names = pf.tree()
    scan = project_scanner.scan(pf)
    relevant = _pick_context(pf, error_text, file_names)
    allowed_paths = {f["path"] for f in relevant}
    system = (
        "You are a cautious senior full-stack debugger. Diagnose only from the supplied error and source context. "
        "Return ONLY JSON with keys summary, diagnostics, patches. diagnostics is a list of {severity, file, line, message}; severity must be error, warning, or info. "
        "patches is a list of at most 3 {file, old, new, reason}. Each old string must be exact and unique in the supplied file. "
        "Make the smallest targeted fix. Do not suppress lint/type/test errors, remove tests, introduce placeholders, change unrelated files, "
        "or claim a fix is verified. If evidence is insufficient, return diagnostics and no patch. Do not output credentials."
    )
    user = json.dumps({"reported_error": error_text, "project_summary": {
        "frameworks": scan.get("frameworks", []), "languages": scan.get("languages", []),
        "entry_points": scan.get("entry_points", [])[:12], "routes": scan.get("routes", [])[:20],
    }, "source_files": relevant}, ensure_ascii=False)
    try:
        result, usage = llm.call_json("repair", system, user, None, 900)
    except Exception as exc:  # model/provider problems should not appear as an application traceback
        message = redact(str(exc))[:500] or type(exc).__name__
        return {"summary": "Debug analysis could not contact or parse a model response.",
                "diagnostics": [{"severity": "error", "file": "", "line": None, "message": message}],
                "applied": [], "rejected": [], "files_scanned": len(file_names), "files_in_context": [f["path"] for f in relevant],
                "verification": ["Skipped: diagnosis did not produce a usable model response."],
                "usage": {"in": 0, "out": 0}, "apply_fixes": body.apply_fixes}
    if not isinstance(result, dict): result = {}
    summary = redact(str(result.get("summary") or "Analysis finished; review diagnostics before relying on the result."))[:1200]
    diagnostics = _parse_diagnostics(result.get("diagnostics"), allowed_paths)
    if not diagnostics and not result.get("patches"):
        diagnostics = [{"severity": "info", "file": "", "line": None,
                       "message": "No structured root-cause finding was returned. Check the error text and relevant source files."}]
    proposed = _safe_patches(result.get("patches"), pf, allowed_paths)
    applied, rejected, verification = [], [], []
    if body.apply_fixes and proposed:
        if db.active_task(pid):
            raise HTTPException(409, "project has a running task; cancel it first")
        cp = checkpoints.create(pid, "checkpoint before AI debug repair")
        try:
            from backend.agent import selfrepair
            baseline_issues = selfrepair.static_issues(pf)
        except Exception:
            baseline_issues = []
        before_text: dict[str, str] = {}
        for patch in proposed:
            try:
                before_text.setdefault(patch["file"], pf.read(patch["file"]))
                ok = pf.patch(patch["file"], patch["old"], patch["new"])
            except (OSError, ValueError) as exc:
                ok = False
                rejected.append(f"{patch['file']}: {redact(str(exc))[:200]}")
            if not ok:
                if not any(patch["file"] in r for r in rejected):
                    rejected.append(f"{patch['file']}: source changed or patch was no longer unique")
                continue
            applied.append({"file": patch["file"], "reason": patch["reason"] or "Targeted repair"})
        if applied:
            try:
                remaining = selfrepair.static_issues(pf)
                changed_paths = {p["file"] for p in applied}
                baseline_changed = [i for i in baseline_issues if i.get("file") in changed_paths]
                remain_here = [i for i in remaining if i.get("file") in changed_paths]
                if len(remain_here) > len(baseline_changed):
                    for rel, original in before_text.items():
                        pf.write(rel, original)
                    rejected.extend(f"{rel}: rolled back because static errors increased after the patch" for rel in before_text)
                    applied.clear()
                    verification.append("Patch rolled back because static syntax errors increased in the changed files.")
                elif remain_here:
                    verification.append(f"Static source checks still report {len(remain_here)} issue(s) in changed files: " + "; ".join(i["msg"][:140] for i in remain_here[:3]))
                else:
                    verification.append("Static syntax checks passed for changed files, where supported.")
                verification.append("A checkpoint was saved before changes: " + cp["id"])
                verification.append("Browser/build/regression tests were not run automatically by this diagnostic action. Use Verify & repair or Run browser tests for broader verification.")
            except Exception as exc:
                verification.append("Changes were applied, but static verification could not complete: " + redact(str(exc))[:200])
    elif proposed and not body.apply_fixes:
        rejected = [f"{p['file']}: patch proposed but not applied (apply_fixes=false)" for p in proposed]
        verification.append("No files were changed. Review the diagnosis and run the fix action to apply selected edits.")
    else:
        verification.append("No patch was applied. The model did not provide a safe, unique patch; this is not proof the error is fixed.")
    db.audit("debug_project", pid, f"scanned={len(file_names)} context={len(relevant)} applied={len(applied)}")
    return {"summary": summary, "diagnostics": diagnostics, "applied": applied, "rejected": rejected,
            "files_scanned": len(file_names), "files_in_context": [f["path"] for f in relevant],
            "verification": verification, "usage": usage if isinstance(usage, dict) else {"in": 0, "out": 0},
            "apply_fixes": body.apply_fixes}

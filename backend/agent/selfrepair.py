"""Phase 6: bounded self-repair for project FILES (JS / Python / JSON syntax errors; extra checks can be plugged in).

Token-cheap: one small LLM call per broken file, only a ~30 line window is sent, answer = unique-match patches.
Bounded: max rounds, max tries per issue, token budget, stops when nothing changes, rolls back a round that made things worse.
Safe: tests, secrets, lockfiles and .agent/ are never edited; patches that add check-suppression markers are rejected.
"""
import hashlib
import json
import re
from pathlib import Path, PurePosixPath
from urllib.parse import urlsplit

from backend.agent import context
from backend.storage import db
from backend.tools import terminal, language_analyzer, debugger

MAX_ROUNDS, MAX_TRIES, TOKEN_BUDGET = 3, 2, 12000
MAX_FILES_PER_ROUND, MAX_MSGS_PER_FILE = 3, 4
EDITABLE = (".js", ".mjs", ".cjs", ".py", ".pyw", ".pyi", ".json", ".jsonc", ".ts", ".tsx", ".jsx", ".css", ".scss", ".sass", ".html", ".htm", ".vue", ".svelte", ".java", ".kt", ".kts", ".go", ".rs", ".php", ".rb", ".cs", ".sql", ".dart", ".swift", ".c", ".h", ".cc", ".cpp", ".cxx", ".hh", ".hpp", ".hxx", ".sh", ".bash", ".ps1", ".psm1", ".xml", ".yaml", ".yml", ".toml")

PROTECTED = re.compile(
    r"(^|/)(tests?|__tests__|\.agent|node_modules|\.git)/|(^|/)(conftest\.py|package-lock\.json|\.env[^/]*)$|"
    r"(\.test\.|\.spec\.|_test\.py$|(^|/)test_[^/]*\.py$)|"
    # React section components and the HTML-mode entry document are generator-owned outputs.
    # Repair their section source via the section engine, never via generic file patching.
    r"(^|/)src/sections/[^/]+\.tsx$|(^|/)index\.html$", re.I)
SUPPRESS = re.compile(r"eslint-disable|@ts-ignore|@ts-nocheck|noqa|type:\s*ignore|pragma:\s*no cover|\.skip\(|pytest\.mark\.skip|--no-verify", re.I)

SYSTEM = ('You are a compiler-evidence-first senior debugger. Return ONLY JSON {"patches":[{"old":"exact unique source text, <=300 chars","new":"replacement"}]}. '
          'At most 3 minimal patches. Fix the earliest/root diagnostic first; inspect imports, declarations, types, project manifests and call sites. '
          'Never invent an import, module, component, identifier, dependency or API. Never convert HTML fragments into JSX expressions. '
          'Never add lint/type/test suppression, any casts, broad exception swallowing, fake fallback behavior or disabled checks to hide an error. '
          'If evidence is insufficient, return an empty patches array. Patch acceptance depends on rerunning checks, not your explanation.')


def _sig(file: str, msg: str) -> str:
    return hashlib.md5(f"{file}|{msg}".encode()).hexdigest()[:10]


def _issue(file: str, msg: str, line: int | None = None) -> dict:
    return {"sid": None, "file": file, "line": line, "msg": f"{file}: {msg}"[:240]}


# ------------------------------------------------------------------ checks (in-process or allowlisted node; no shell)
def static_issues(pf) -> list[dict]:
    """Return only actionable syntax/compiler errors for the bounded repair loop.

    Logic/redundancy findings are exposed separately by the language analysis API;
    heuristic warnings must never trigger automatic code edits by themselves.
    """
    try:
        report = language_analyzer.analyze_project(pf, deep=False, include_redundancy=False)
    except Exception as exc:  # a reporting failure must not crash the entire task
        context.progress("verify", f"Multi-language static analysis could not complete: {type(exc).__name__}", "warn")
        return []
    out = []
    for row in report.get("issues", []):
        if row.get("severity") != "error":
            continue
        if row.get("category") in {"logic", "redundancy", "coverage"}:
            continue
        rel = row.get("file")
        msg = str(row.get("message") or "syntax/compile error")[:220]
        if not rel or not isinstance(rel, str):
            continue
        line = row.get("line") if isinstance(row.get("line"), int) and row.get("line") > 0 else None
        out.append(_issue(rel, f"{row.get('tool', 'analyzer')}: {msg}", line))
    return out


# ------------------------------------------------------------------ patching
def _window(text: str, line: int | None, budget: int = 1800) -> str:
    """~30 lines around the error, but always containing the error line even when generated lines are very long."""
    if not line:
        return text[:budget]
    lines = text.splitlines()
    if not lines:
        return ""
    idx = min(max(line - 1, 0), len(lines) - 1)
    target = lines[idx][: budget * 2 // 3]
    lo = hi = idx
    size = len(target)
    while size < budget and (lo > max(0, idx - 15) or hi < min(len(lines) - 1, idx + 14)):
        if lo > max(0, idx - 15) and size + len(lines[lo - 1]) + 1 <= budget:
            lo -= 1
            size += len(lines[lo]) + 1
        elif hi < min(len(lines) - 1, idx + 14) and size + len(lines[hi + 1]) + 1 <= budget:
            hi += 1
            size += len(lines[hi]) + 1
        else:
            break
    return "\n".join(lines[lo:idx] + [target] + lines[idx + 1: hi + 1])


def _valid_patch(p) -> bool:
    if not isinstance(p, dict) or not isinstance(p.get("old"), str) or not isinstance(p.get("new"), str):
        return False
    return 0 < len(p["old"]) <= 300 and len(p["new"]) <= 1500 and p["old"] != p["new"] and not SUPPRESS.search(p["new"])


def _apply(text: str, patches: list) -> str | None:
    """All-or-nothing: every patch must be valid and match exactly once."""
    if not patches or len(patches) > 3 or not all(_valid_patch(p) for p in patches):
        return None
    for p in patches:
        if text.count(p["old"]) != 1:
            return None
        text = text.replace(p["old"], p["new"])
    return text


def _default_call(user: str):
    from backend.agent import llm          # lazy: keeps this module importable/testable without the model stack
    return llm.call_json("repair", SYSTEM, user, None, 900)


def _existing_project_file(pf, rel: str) -> str | None:
    """Return a safe canonical relative path only when the target is an existing file."""
    if not isinstance(rel, str) or not rel.strip():
        return None
    value = rel.strip().strip("\"'`").replace("\\", "/")
    while value.startswith("./"):
        value = value[2:]
    if value.startswith("/") or re.match(r"^[A-Za-z]:", value) or "\x00" in value or ".." in value.split("/"):
        return None
    try:
        root = Path(pf.root).resolve()
        # ProjectFiles._safe applies the same traversal/symlink guard as reads/writes.
        candidate = pf._safe(value) if hasattr(pf, "_safe") else (root / value).resolve()
        candidate = Path(candidate).resolve()
        if candidate == root or root not in candidate.parents or not candidate.is_file():
            return None
        return candidate.relative_to(root).as_posix()
    except (OSError, ValueError, RuntimeError):
        return None


def _resolve_repair_target(pf, issue: dict) -> str | None:
    """Map a diagnostic to the existing source file that produced it.

    Build output can mention a missing imported asset before the actual TypeScript source
    location. Never try to read/patch that missing import target. Prefer parsed compiler
    locations, then other explicit source locations in the diagnostic, and only then an
    explicit issue.file that actually exists in the project.
    """
    raw = str(issue.get("msg") or issue.get("message") or issue.get("detail") or "")
    root = getattr(pf, "root", None)
    try:
        parsed = debugger.parse_diagnostics(raw, root=root, limit=20)
    except Exception:
        parsed = []
    for row in parsed:
        candidate = _existing_project_file(pf, str(row.get("file") or ""))
        if candidate and candidate.lower().endswith(EDITABLE):
            return candidate

    # Some bundlers state `Could not resolve "../x" from "src/path/File.tsx"` without
    # line/column data, so there is no compiler-location record to parse.
    ext_group = r"(?:" + "|".join(re.escape(x.lstrip(".")) for x in EDITABLE) + r")"
    source_paths = re.findall(
        rf"(?i)((?:src|app|client|server|lib|pages|components|routes|js|css)/[A-Za-z0-9_@.+/\-]+?\.{ext_group})",
        raw,
    )
    for path in reversed(source_paths):
        candidate = _existing_project_file(pf, path)
        if candidate and candidate.lower().endswith(EDITABLE):
            return candidate

    explicit = _existing_project_file(pf, str(issue.get("file") or ""))
    if explicit and explicit.lower().endswith(EDITABLE):
        return explicit

    # Last safe fallback: if an error names a missing module, locate a unique existing
    # source file that imports/references that exact module stem. Do not choose HTML or
    # generator-protected outputs as arbitrary patch targets.
    missing = str(issue.get("file") or "")
    stem = PurePosixPath(missing.replace("\\", "/")).stem
    if stem and re.fullmatch(r"[A-Za-z0-9_.-]+", stem):
        escaped_stem = re.escape(stem)
        needle = re.compile(
            r"""(?i)(?:from\s*['\"][^'\"]*STEM|import\s*['\"][^'\"]*STEM|require\s*\(\s*['\"][^'\"]*STEM|src\s*=\s*['\"][^'\"]*STEM)""".replace("STEM", escaped_stem)
        )
        candidates: list[str] = []
        try:
            tree = pf.tree()
        except Exception:
            tree = []
        for rel in tree[:2000]:
            normalized = str(rel).replace("\\", "/")
            if PROTECTED.search(normalized) or not normalized.lower().endswith(EDITABLE):
                continue
            try:
                source = pf.read(normalized, max_chars=200_000)
            except (OSError, ValueError, UnicodeError):
                continue
            if needle.search(source):
                candidates.append(normalized)
        # Only repair a reference automatically when it points to one unambiguous source.
        if len(candidates) == 1:
            return _existing_project_file(pf, candidates[0])
    return None


def _module_file_exists(root: Path, source_file: str, specifier: str) -> bool:
    """Resolve a relative JS/TS import without importing or executing project code."""
    specifier = (specifier or "").strip()
    if not specifier.startswith("."):
        return True  # Package imports need package-manifest/dependency analysis instead.
    base = (root / PurePosixPath(source_file).parent / specifier).resolve()
    if base == root or root not in base.parents:
        return True  # Refuse to repair an import that escapes the project root.
    for suffix in ("", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".json", ".vue", ".svelte"):
        if Path(str(base) + suffix).is_file():
            return True
    return any((base / name).is_file() for name in
               ("index.ts", "index.tsx", "index.js", "index.jsx", "index.mjs", "index.cjs"))


def _restore_known_missing_module_assets(pf, issues: list[dict]) -> list[tuple[str, str]]:
    """Recover known three-hero regressions using canonical, repository-owned sources.

    A verifier may report ``three-hero.js`` as the missing target rather than the file
    that referenced it. Do not send the missing path to the LLM. Instead, repair the
    known React scaffold only when its import target is absent, or restore the matching
    checked-in animation asset only when local HTML explicitly references it.
    """
    combined = "\n".join(
        str(item.get("file") or "") + " " + str(item.get("msg") or item.get("message") or item.get("detail") or "")
        for item in issues
    )
    if not re.search(r"three[-_]hero(?:\.js)?", combined, re.I):
        return []

    root = Path(pf.root).resolve()
    recovered: list[tuple[str, str]] = []

    # React + Vite: a bad LLM patch can inject an invalid parent-level import,
    # while the canonical component itself imports a runtime that older scaffolds
    # accidentally failed to generate. Repair both deterministically from checked-in
    # sources rather than spending repeated model calls on an agent-owned file.
    motion_rel = "src/lib/MotionEffects.tsx"
    try:
        motion = pf.read(motion_rel)
    except (OSError, ValueError, FileNotFoundError):
        motion = ""
    import_pattern = re.compile(
        r"(?:from\s*|import\s*(?:\(\s*)?)['\"](?P<specifier>\.{1,2}/[^'\"]*three[-_]hero(?:\.[A-Za-z0-9]+)?)['\"]",
        re.I,
    )
    imports = [m.group("specifier") for m in import_pattern.finditer(motion)]
    if motion and imports and not all(_module_file_exists(root, motion_rel, spec) for spec in imports):
        try:
            from backend.engines import code_engine as ce
            canonical = ce._tpl("react/src/lib/MotionEffects.tsx")
            if (canonical and "../three-hero" not in canonical and "..\\three-hero" not in canonical
                    and "export default function MotionEffects" in canonical and canonical != motion):
                pf.write(motion_rel, canonical)
                motion = canonical
                recovered.append((motion_rel, "restored canonical React MotionEffects scaffold for unresolved local import"))
                context.progress("repair", "Restored canonical src/lib/MotionEffects.tsx after an invalid local import", "warn")
        except (ImportError, OSError, ValueError, FileNotFoundError, AttributeError):
            pass

        # The canonical MotionEffects file intentionally imports ./three-hero.js.
        # If that exact module is missing, restore the known runtime and its type contract.
        imports = [m.group("specifier") for m in import_pattern.finditer(motion)]
        if any(spec.replace("\\", "/") == "./three-hero.js" for spec in imports):
            if not _module_file_exists(root, motion_rel, "./three-hero.js"):
                try:
                    from backend.engines.react_engine import ensure_three_runtime
                    if ensure_three_runtime(pf):
                        recovered.append(("src/lib/three-hero.js", "restored missing React Three.js runtime and type contract from canonical templates"))
                        context.progress("repair", "Restored the missing React three-hero runtime from the canonical template", "warn")
                except (ImportError, OSError, ValueError, FileNotFoundError, AttributeError, RuntimeError):
                    pass

    # HTML mode: when an existing local entry actually references the missing animation
    # script, restore that asset from the checked-in template at the exact relative path.
    try:
        listed = list(pf.tree())
    except Exception:
        listed = []
    html_paths = sorted(set(["index.html"] + [str(x).replace("\\", "/") for x in listed
                                              if str(x).lower().endswith((".html", ".htm"))]))
    for html_rel in html_paths[:200]:
        try:
            html = pf.read(html_rel, max_chars=200_000)
        except (OSError, ValueError, UnicodeError, FileNotFoundError):
            continue
        pattern = re.compile(r"<script\b[^>]*\bsrc\s*=\s*(['\"])([^'\"]*three[-_]hero\.js(?:\?[^'\"]*)?)\1[^>]*>", re.I)
        for match in pattern.finditer(html):
            src = urlsplit(match.group(2)).path
            if not src or src.startswith(("/", "\\")) or re.match(r"^[A-Za-z]:", src):
                continue
            target = (root / PurePosixPath(html_rel).parent / PurePosixPath(src)).resolve()
            if target == root or root not in target.parents or target.is_file():
                continue
            rel = target.relative_to(root).as_posix()
            try:
                from backend.engines import code_engine as ce
                source = ce._tpl("animation/three-hero.js")
                if (not source or "export function initThreeHero" not in source
                        or "querySelectorAll" not in source or "three-hero-fallback" not in source):
                    continue
                pf.write(rel, source)
                recovered.append((rel, f"restored referenced animation asset from canonical template used by {html_rel}"))
                context.progress("repair", f"Restored missing local animation asset {rel} from canonical template", "warn")
            except (ImportError, OSError, ValueError, FileNotFoundError, AttributeError):
                continue
    return recovered


def _prepare_repair_targets(pf, issues: list[dict], log: list[dict] | None = None) -> list[dict]:
    prepared = []
    for original in issues:
        item = dict(original)
        reported = str(item.get("file") or "")
        target = _resolve_repair_target(pf, item)
        if target:
            item["file"] = target
            prepared.append(item)
            if reported and reported.replace("\\", "/") != target:
                context.progress("debugger", f"Mapped diagnostic target '{reported}' to existing source '{target}'", "warn")
            continue
        item["file"] = ""  # blank path means blocked; never give it to pf.read/write or the LLM
        reason = f"repair skipped: reported target '{reported or '(unknown)'}' is missing or unmappable; no existing source file was found"
        item["msg"] = (str(item.get("msg") or reason) + f" [{reason}]")[:500]
        if log is not None:
            log.append({"round": 0, "file": reported, "issue": str(item.get("msg") or "")[:120],
                        "outcome": "target_missing", "reason": reason})
        context.progress("repair", reason, "warn")
        prepared.append(item)
    return prepared


# ------------------------------------------------------------------ the loop
def repair_files(pf, issues: list[dict] | None = None, check=None, call=None, max_rounds: int = MAX_ROUNDS,
                 max_tries: int = MAX_TRIES, token_budget: int = TOKEN_BUDGET, reverify=None) -> dict:
    """Returns {status: PASS|PARTIAL|FAIL|BLOCKED, remaining, blocked, fixed, rounds, attempts, usage, stop, log}."""
    check, call = check or static_issues, call or _default_call
    raw_issues = list(check(pf) if issues is None else issues)
    pid, tid = pf.root.name, (context.current().task_id if context.current() else "")
    tries: dict[str, int] = {}
    log, fixed, used, stop, attempts, seen = [], 0, 0, "", 0, set()

    # Missing-module reports can point at a nonexistent target, which must never be
    # patched directly. First attempt known deterministic recovery, then re-run the
    # checks so stale diagnostics cannot be reported as fixed.
    recovered = _restore_known_missing_module_assets(pf, raw_issues)
    if recovered:
        log.extend({"round": 0, "file": rel, "issue": "missing three-hero module/asset",
                    "outcome": "deterministic_recovery", "reason": why} for rel, why in recovered)
        refreshed = list(check(pf))
        if not refreshed:
            context.progress("verify", f"Deterministic missing-module recovery cleared the issue(s): {len(recovered)} file(s) restored")
            return {"status": "PASS", "remaining": [], "blocked": [], "fixed": max(len(raw_issues), 1),
                    "rounds": 0, "attempts": 0, "usage_tokens": 0,
                    "stop": "deterministic missing-module recovery verified", "log": log[-30:]}
        raw_issues = refreshed

    issues = _prepare_repair_targets(pf, raw_issues, log)

    def verification_state():
        if reverify is None:
            return None
        try:
            value = reverify(pf)
            if (isinstance(value, tuple) and len(value) == 2
                    and isinstance(value[0], (set, frozenset, list, tuple))):
                return set(str(x) for x in value[0]), bool(value[1])
            return set(str(x) for x in (value or [])), True
        except Exception as exc:  # verification failures must not look like successful checks
            context.progress("verify", f"Repair re-verification failed: {type(exc).__name__}", "warn")
            return {"__verification_unavailable__"}, False

    baseline_verification = verification_state()

    def rec(i, rnd, outcome, reason: str | None = None):
        row = {"round": rnd, "file": i["file"], "issue": i["msg"][:120], "outcome": outcome}
        if reason:
            row["reason"] = reason
        log.append(row)
        db.add_repair_attempt(pid, tid, rnd, i["file"], i["msg"], _sig(i["file"], i["msg"]), "file_patch", outcome)

    def split(items):
        fix, blk, spent = [], [], []
        for i in items:
            f = i.get("file")
            if not f or PROTECTED.search(f) or not f.endswith(EDITABLE):
                blk.append(i)
            elif tries.get(_sig(f, i["msg"]), 0) >= max_tries:
                spent.append(i)
            else:
                fix.append(i)
        return fix, blk, spent

    rounds = 0
    for rnd in range(1, max_rounds + 1):
        context.check()
        fix, blk, spent = split(issues)
        key = frozenset(_sig(i.get("file") or "", i["msg"]) for i in issues)
        if not fix:
            stop = "nothing repairable left" if issues else ""
            break
        if key in seen:
            stop = "no progress (same failures as an earlier round)"
            break
        if used >= token_budget:
            stop = f"token budget reached ({token_budget})"
            break
        seen.add(key)
        rounds = rnd
        by: dict[str, list[dict]] = {}
        for i in fix:
            by.setdefault(i["file"], []).append(i)
        backups, touched = {}, []
        for f, group in list(by.items())[:MAX_FILES_PER_ROUND]:
            for i in group:
                tries[_sig(f, i["msg"])] = tries.get(_sig(f, i["msg"]), 0) + 1
            attempts += 1
            try:
                text = pf.read(f)
                msgs = "\n".join(f"- {i['msg']}" for i in group[:MAX_MSGS_PER_FILE])
                evidence = debugger.repair_context(pf, f, group[:MAX_MSGS_PER_FILE], text, root=pf.root)
                user_context = (
                    f"{evidence}\nREPAIR CONTRACT:\n{msgs}\n"
                    "Choose the smallest root-cause fix. Do not touch unrelated files or make speculative rewrites. "
                    "The verifier will reject changes unless observed diagnostics strictly decrease without new diagnostics.\n"
                    f"EXACT PATCH WINDOW:\n{_window(text, group[0].get('line'))}"
                )
                data, u = call(user_context)
                used += u["in"] + u["out"]
                new = _apply(text, data.get("patches") or [])
                if new is not None:
                    valid, reason = debugger.validate_patch_text(text, new)
                    if not valid:
                        new = None
                        context.progress("repair", f"{f}: rejected unsafe patch ({reason})", "warn")
            except Exception as e:  # noqa: BLE001  (a failed repair attempt must never crash the task)
                for i in group:
                    rec(i, rnd, "error")
                context.progress("repair", f"{f}: repair call failed ({str(e)[:60]})", "warn")
                continue
            if new is None:
                for i in group:
                    rec(i, rnd, "patch_rejected")
                continue
            backups[f] = text
            pf.write(f, new)
            touched.append((f, group))
            context.progress("repair", f"Patched {f} (round {rnd}/{max_rounds})")
        after = _prepare_repair_targets(pf, list(check(pf)), log)
        # Re-run declared build/test checks immediately after this repair round. The
        # verifier is allowlisted and never installs dependencies. New failures reject
        # the round even when the source diagnostic count happened to decrease.
        current_verification = verification_state()
        new_check_failure = False
        if current_verification is not None:
            if not current_verification[1]:
                new_check_failure = True
            elif baseline_verification is not None:
                new_check_failure = bool(current_verification[0] - baseline_verification[0])
        delta = debugger.compare_diagnostics(issues, after, root=pf.root)
        # A patch is accepted only if diagnostics strictly shrink and re-verification
        # did not introduce a newly failing declared build/test check.
        if delta["status"] != "improved" or new_check_failure:
            if new_check_failure:
                delta["status"] = "regression"
            for f, text in backups.items():
                pf.write(f, text)
            reason = ("verification_regression" if new_check_failure else
                      ("no_progress" if delta["status"] == "unchanged" else "regression"))
            for f, group in touched:
                for i in group:
                    # Keep the established outcome token for existing dashboards while
                    # attaching a structured reason for the stronger debugger report.
                    rec(i, rnd, "rolled_back", reason=reason)
            context.progress(
                "repair",
                f"Rejected repair round ({delta['status']}): {delta['before_count']} diagnostic(s) before, "
                f"{delta['after_count']} after; restored original files",
                "warn",
            )
            after = list(issues)  # restored bytes mean the prior evidence is the authoritative state
            stop = stop or ("repair produced no diagnostic improvement" if delta["status"] == "unchanged" else "repair introduced or changed diagnostics; rolled back")
        else:
            baseline_verification = current_verification
            now = {_sig(i.get("file") or "", i["msg"]) for i in after}
            for f, group in touched:
                for i in group:
                    ok = _sig(f, i["msg"]) not in now
                    fixed += int(ok)
                    rec(i, rnd, "fixed" if ok else "still_failing")
        issues = after
    else:
        stop = stop or ("max rounds reached" if issues else "")
    if not issues:
        status = "PASS"
    else:
        fix, blk, spent = split(issues)
        status = "PARTIAL" if fixed else ("BLOCKED" if blk and not fix and not spent and not attempts else "FAIL")
        if spent and not stop:
            stop = f"issue(s) tried {max_tries}x without success"
    fix, blk, spent = split(issues)
    return {"status": status, "remaining": issues, "blocked": [i["msg"] for i in blk], "fixed": fixed, "rounds": rounds,
            "attempts": attempts, "usage_tokens": used, "stop": stop, "log": log[-30:]}

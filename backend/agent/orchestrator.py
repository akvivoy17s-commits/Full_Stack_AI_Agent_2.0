import hashlib
import json

from backend import config
from backend.agent import planner, context, progress, requirements, selfrepair
from backend.storage import db
from backend.engines import code_engine, react_engine, repair_engine
from backend.memory import project_store, history
from backend.tools import browser, screenshots, vision
from backend.tools.project_files import ProjectFiles
from backend.tools import checkpoint as checkpoint_tools
from backend.tools.validators import validate_html, validate_css
from backend import stack as stack_engine
from backend import spec as spec_engine
from backend.spec import memory as spec_memory
from backend.gen import stage as backend_stage


def _add(state, u: dict) -> None:
    state.usage["in"] += u["in"]
    state.usage["out"] += u["out"]


MAX_TRIES_PER_ISSUE = 2        # one targeted patch, then one source-of-truth section regeneration


def _sig(i: dict) -> str:
    return hashlib.md5(f"{i.get('sid')}|{i['msg']}".encode()).hexdigest()[:10]


def _task_id() -> str:
    c = context.current()
    return c.task_id if c else ""


def _section_fixable(issue: dict, tries: dict | None = None) -> bool:
    """Only send canonical section issues to the section repair engine.

    A raw `file` issue belongs to file-level repair. React section compile errors are
    represented with `generated_file` instead: the TSX file is derived and must be
    repaired by modifying its canonical HTML/CSS source, never by patching generated TSX.
    """
    if not issue.get("sid") or issue.get("file"):
        return False
    return (tries or {}).get(_sig(issue), 0) < MAX_TRIES_PER_ISSUE


def _section_source_fingerprint(pf, state, sid: str) -> str:
    """Stable fingerprint for the actual editable source of one generated section."""
    try:
        html, css = code_engine.get_section(pf, sid, state)
    except Exception:  # a missing source has a stable empty fingerprint
        html, css = "", ""
    return hashlib.sha256((str(html) + "\0" + str(css)).encode("utf-8", errors="replace")).hexdigest()


def _section_checkpoint_paths(state, sids) -> list[str]:
    """Files the canonical section engine is allowed to update during a section repair."""
    paths = {"index.html", "css/sections.css", "src/App.tsx"}
    for sid in sids:
        sid = str(sid)
        paths.update({f".agent/parts/{sid}.html", f".agent/parts/{sid}.css"})
        paths.update({f"src/sections/{sid}.css", f"src/sections/{react_engine.pascal(sid)}.tsx"})
    return sorted(paths)


def _issue_keys(items: list[dict]) -> set[tuple[str, str, str]]:
    """Stable exact diagnostic identities used to decide whether a repair improved evidence."""
    import re
    rows = set()
    for item in items:
        file_name = str(item.get("file") or "").replace("\\", "/")
        message = re.sub(r"\s+", " ", str(item.get("msg") or item.get("message") or "")).strip()
        rows.add((str(item.get("sid") or ""), file_name, message))
    return rows


def _deep_failed_check_names(pf, enabled: bool) -> tuple[set[str], bool]:
    """Return names of failed declared checks; false means verification itself was unavailable."""
    if not enabled:
        return set(), True
    try:
        from backend.tools.project_verifier import verify_backend
        result = verify_backend(pf, deep=True)
        checks = result.get("checks", [])
        if not isinstance(checks, list):
            return {"__verification_unavailable__"}, False
        return {str(c.get("name") or "unnamed check") for c in checks
                if isinstance(c, dict) and c.get("status") == "failed"}, True
    except Exception as exc:  # never convert an unavailable verifier into a green pass
        context.progress("verify", f"Post-repair build/test verification could not complete: {type(exc).__name__}", "warn")
        return {"__verification_unavailable__"}, False


def _repair_improved(before: list[dict], after: list[dict], before_failed: set[str],
                     after_failed: set[str], verifier_ok: bool) -> tuple[bool, str]:
    before_keys, after_keys = _issue_keys(before), _issue_keys(after)
    if not verifier_ok:
        return False, "post-repair verifier was unavailable"
    new_failed_checks = after_failed - before_failed
    if new_failed_checks:
        return False, "new failing check(s): " + ", ".join(sorted(new_failed_checks)[:4])
    if after_keys < before_keys:
        return True, "diagnostics reduced and no new checks failed"
    return False, "diagnostics did not strictly decrease"


def collect_issues(pf, state, with_browser: bool, want_images: bool = False):
    """All checks are local/free. Issues with a 'sid' are auto-repairable.
    Returns (issues, note, extra) where extra = {report: {checks, a11y, notes}, images}."""
    issues, checks = [], []
    if state.plan.get("layout") == "app":
        app_path = pf.root / "src" / "App.tsx"
        app_text = ""
        try:
            app_text = pf.read("src/App.tsx")
        except (OSError, ValueError):
            pass
        app_ok = bool(app_text.strip()) and "export default function App" in app_text and "__PAYLOAD__" not in app_text
        if not app_ok:
            issues.append({"sid": "app", "msg": "application entry point is missing or incomplete"})
        checks.append({"name": "application entry point", "viewport": "static", "status": "passed" if app_ok else "failed", "detail": "src/App.tsx" if app_ok else "src/App.tsx missing or incomplete"})
        # Schema-driven app files are checked by TypeScript/Vite rather than the marketing-section validator.
    else:
        for sid in state.plan.get("sections", []):
            if sid not in state.sections_done:
                issues.append({"sid": sid, "msg": "section not generated"})
                continue
            html, css = code_engine.get_section(pf, sid, state)
            if not html.strip():
                issues.append({"sid": sid, "msg": "section empty"})
                continue
            issues += [{"sid": sid, "msg": e} for e in validate_html(html)]
            issues += [{"sid": sid, "msg": e} for e in validate_css(css) if "reduced-motion" not in e]
        checks.append({"name": "section markup + CSS", "viewport": "static", "status": "failed" if issues else "passed", "detail": f"{len(issues)} issue(s)"})
    issues += selfrepair.static_issues(pf)                 # file syntax checks (JS via node, Python/JSON in-process)
    extra = {"report": {"checks": checks, "a11y": [], "notes": []}, "images": {}}
    serve_dir, note = pf.root, "skipped"
    if state.plan.get("stack") == "react":
        restored = react_engine.restore_static(pf) if (pf.root / "package.json").is_file() else []
        if restored:
            context.progress("repair", f"Restored missing scaffold file(s): {', '.join(restored)}")
        b = react_engine.build(pf, state)
        for build_issue in b["issues"]:
            msg = str(build_issue.get("msg", ""))
            file_match = __import__("re").search(r"\b((?:src[/\\])?[\w./\\-]+\.(?:tsx?|jsx?|css))", msg)
            if file_match:
                rel = file_match.group(1).replace("\\", "/")
                line_match = __import__("re").search(r"\((\d+),\d+\)", msg) or __import__("re").search(r":(\d+):\d+", msg)
                build_issue["line"] = int(line_match.group(1)) if line_match else None
                if rel.lower().startswith("src/sections/") and rel.lower().endswith(".tsx") and build_issue.get("sid"):
                    # TSX section files are derived from .agent/parts/<sid>.html/.css.
                    # Mark the real diagnostic location for reporting, but route repair to
                    # the canonical section source rather than letting selfrepair corrupt TSX.
                    build_issue["generated_file"] = rel
                else:
                    build_issue["file"] = rel
        issues += b["issues"]
        checks += b["checks"]
        note = b["note"]
        if b["built"]:
            serve_dir = pf.root / "dist"
        else:
            with_browser = False                            # nothing built -> nothing to open (reported, not hidden)
            extra["report"]["notes"].append("browser checks skipped: the project did not build")
    if with_browser:
        b = browser.inspect(pf, serve_dir=serve_dir, want_images=want_images)
        issues += b["issues"]
        note = b["note"]
        checks += b["report"]["checks"]
        extra["report"]["a11y"] = b["report"]["a11y"]
        extra["report"]["notes"] += b["report"]["notes"]
        extra["images"] = b["images"]
    return issues, note, extra


def _spec_stage(state) -> dict:
    """Build/refresh the app spec and project memory (rule based, 0 tokens) and say what this build does NOT cover."""
    spec, changed = spec_engine.ensure(state)
    if changed or not spec_memory.load(state.project_id):
        spec_memory.refresh(state, spec)
    project_store.save(state)
    d = spec["data"]
    context.progress("spec", f"{spec['kind']}: {len(spec['pages'])} page(s), {len(d['entities'])} entities, {len(spec['api']['routes'])} route(s)"
                             + ("" if changed else " (spec unchanged)"))
    for g in spec["gaps"]:
        context.progress("spec", g, "warn")
    for q in spec["open_questions"]:
        context.progress("spec", f"Open question: {q['question']}", "warn")
    return requirements.analyze(spec)


def _backend_stage(state, pf) -> tuple[str, str]:
    """Generate the selected backend (rule based, 0 tokens). Unsupported parts are reported, never faked.
    Returns (step status, detail): skipped | issues | done."""
    cfg = (state.stack_config or {}).get("stack")
    if not cfg or (cfg.get("backend") or "none") == "none":
        return "skipped", "no backend selected"
    spec, _ = spec_engine.ensure(state)
    r = backend_stage.run(pf, spec, cfg)
    if not r["generated"]:
        for g in r["gaps"]:
            context.progress("backend", f"Not generated yet: {g}", "warn")
        return "issues", ("not generated: " + (r["gaps"][0] if r["gaps"] else "unsupported backend"))[:200]
    context.progress("backend", f"{r['generator']} + {r['database'] or 'no database'}: {r['routes']} route(s), {len(r['written'])} file(s) written")
    for k in r["kept"]:
        context.progress("backend", f"Kept your edited file: {k}", "warn")
    for n in r["not_generated"]:
        context.progress("backend", f"Not generated yet: {n}", "warn")
    for w in r["warnings"]:
        context.progress("backend", w, "warn")
    detail = f"{r['generator']}: {r['routes']} route(s), {len(r['written'])} file(s)"
    return ("issues", detail + f"; not generated: {', '.join(r['not_generated'])[:100]}") if r["not_generated"] else ("done", detail)


def _spec_report(state) -> dict:
    """Compact spec + memory-consistency block for the verification report."""
    spec, _ = spec_engine.ensure(state)
    spec_memory.refresh(state, spec)
    chk = spec_memory.check(state)
    return {"kind": spec["kind"], "pages": len(spec["pages"]), "entities": len(spec["data"]["entities"]), "routes": len(spec["api"]["routes"]),
            "not_generated_yet": [s["title"] for s in spec["plan"] if s["status"] not in ("ready", "done")], "gaps": spec["gaps"],
            "open_questions": [q["question"] for q in spec["open_questions"]], "memory_consistent": chk["consistent"], "memory_drift": chk["drift"]}


def _vision_enabled() -> bool:
    return bool((db.get_settings().get("vision_model") or "").strip())


def verify(pid: str, do_repair: bool = True, with_browser: bool | None = None, deep: bool = False) -> dict:
    with_browser = config.USE_BROWSER if with_browser is None else with_browser
    state = project_store.load(pid)
    if not state:
        raise ValueError("project not found")
    pf = ProjectFiles(pid)
    normalized = code_engine.normalize_existing_ids(pf, state)
    if normalized:
        context.progress("verify", f"Normalized duplicate or conflicting IDs in {normalized} section(s) without an LLM call")
    issues, note, extra = [], "skipped", {}
    rollback_failure_note = None
    configured_loops = min(db.get_settings()["max_repair_loops"], 5)
    max_loops = configured_loops
    if do_repair and max_loops == 0:
        context.progress("repair", "Section repair loops are disabled (Settings > Repair loops = 0). Set this to 2-3 to let the agent regenerate broken sections.", "warn")
    tries: dict[str, int] = {}                   # issue signature -> repair attempts this cycle
    attempts_by_sid: dict[str, int] = {}          # bounds section attempts even if diagnostics mutate
    pending: list[dict] = []                     # repairs whose outcome is judged by the next check pass
    stalled_signatures: set[str] = set()          # same error + unchanged canonical source: never call the model again
    repair_log: list[dict] = []
    vision_on = with_browser and _vision_enabled()
    for attempt in range(max_loops + 1):
        context.check()
        context.progress("verify", f"Running checks (pass {attempt + 1})")
        issues, note, extra = collect_issues(pf, state, with_browser, vision_on)
        now = {_sig(i) for i in issues}
        for rp in pending:                       # record what the previous repair actually achieved
            still_failing = rp["sig"] in now
            source_unchanged = bool(rp.get("source_fingerprint")) and (
                _section_source_fingerprint(pf, state, str(rp["sid"])) == rp["source_fingerprint"]
            )
            if rp["method"] == "error":
                outcome = "error"
            elif still_failing and source_unchanged:
                outcome = "no_progress_same_source"
                stalled_signatures.add(rp["sig"])
                context.progress(
                    "repair",
                    f"Stopped retrying '{rp['sid']}': the same diagnostic remains and its canonical source did not change",
                    "warn",
                )
            else:
                outcome = "still_failing" if still_failing else "fixed"
            row = {"attempt": rp["attempt"], "sid": rp["sid"], "issue": rp["msg"][:160], "method": rp["method"], "outcome": outcome}
            repair_log.append(row)
            db.add_repair_attempt(pid, _task_id(), rp["attempt"], rp["sid"], rp["msg"], rp["sig"], rp["method"], outcome)
        pending = []
        fixable = [i for i in issues if _section_fixable(i, tries)
                   and _sig(i) not in stalled_signatures
                   and attempts_by_sid.get(str(i.get("sid")), 0) < MAX_TRIES_PER_ISSUE]
        for i in issues:
            sid_key = str(i.get("sid") or "")
            if sid_key and (tries.get(_sig(i), 0) >= MAX_TRIES_PER_ISSUE
                            or attempts_by_sid.get(sid_key, 0) >= MAX_TRIES_PER_ISSUE):
                context.progress("repair", f"Not retrying '{sid_key}': {i['msg'][:60]} (section repair budget exhausted)", "warn")
        if not do_repair or not fixable or attempt == max_loops:
            break
        context.progress("repair", f"Repair attempt {attempt + 1}/{max_loops}: {len(fixable)} issue(s)")
        regen = {i["sid"] for i in fixable if attempts_by_sid.get(str(i.get("sid")), 0) >= 1}  # patch failed -> one regeneration
        # A stable baseline is captured after the current build/static pass. Each repair
        # round is checkpointed and immediately re-verified; failed changes are rolled back.
        baseline_issues = collect_issues(pf, state, False, False)[0]
        baseline_failed, baseline_verifier_ok = _deep_failed_check_names(pf, deep)
        source_before = {
            str(i["sid"]): _section_source_fingerprint(pf, state, str(i["sid"]))
            for i in fixable if i.get("sid")
        }
        sids_to_checkpoint = {str(i["sid"]) for i in fixable if i.get("sid")}
        sections_done_before = list(state.sections_done)
        try:
            checkpoint = checkpoint_tools.capture(pf.root, _section_checkpoint_paths(state, sids_to_checkpoint))
        except Exception as exc:  # if safe rollback cannot be guaranteed, do not make the change
            checkpoint = None
            context.progress("repair", f"Skipped repair because a safe checkpoint could not be created: {str(exc)[:140]}", "warn")
            res = {"in": 0, "out": 0, "log": [
                {"sid": sid, "method": "error", "msgs": ["safe checkpoint unavailable"]}
                for sid in sids_to_checkpoint
            ]}
        else:
            res = repair_engine.fix(pf, state, fixable, regen)
        _add(state, res)
        after_repair_issues = collect_issues(pf, state, False, False)[0]  # fresh React/Vite build
        after_failed, after_verifier_ok = _deep_failed_check_names(pf, deep)  # declared build + tests, when enabled
        verifier_ok = baseline_verifier_ok and after_verifier_ok
        improved, repair_reason = _repair_improved(
            baseline_issues, after_repair_issues, baseline_failed, after_failed, verifier_ok
        )
        if not improved:
            if checkpoint is not None:
                try:
                    checkpoint_tools.restore(pf.root, checkpoint)
                    state.sections_done = sections_done_before
                    context.progress("repair", f"Rejected section repair and restored checkpoint: {repair_reason}", "warn")
                    # Re-run verification on restored code; only then may the next pass proceed.
                    collect_issues(pf, state, False, False)
                    _deep_failed_check_names(pf, deep)
                except Exception as exc:
                    rollback_failure_note = f"Checkpoint rollback failed: {type(exc).__name__}: {str(exc)[:180]}"
                    context.progress("repair", rollback_failure_note, "error")
            else:
                state.sections_done = sections_done_before
        else:
            context.progress("verify", "Post-repair build/static checks passed their regression gate; no new test/check failures detected")
        done = {e["sid"]: e["method"] for e in res.get("log", [])} or {i["sid"]: "patch" for i in fixable}
        counted_sections: set[str] = set()
        for i in fixable:
            if i["sid"] in done:
                tries[_sig(i)] = tries.get(_sig(i), 0) + 1
                sid_key = str(i.get("sid"))
                # Several compiler/markup diagnostics can belong to one section. Count one
                # repair operation per section per pass, not one per diagnostic message.
                if sid_key not in counted_sections:
                    attempts_by_sid[sid_key] = attempts_by_sid.get(sid_key, 0) + 1
                    counted_sections.add(sid_key)
                pending.append({"attempt": attempt + 1, "sid": i["sid"], "msg": i["msg"], "sig": _sig(i),
                                "method": done[i["sid"]],
                                "source_fingerprint": source_before.get(str(i["sid"]))})
        state.repair_count += 1
        project_store.save(state)
    report = extra.get("report", {"checks": [], "a11y": [], "notes": []})
    def _file_repair_check(_pf):
        # Build/import/type errors are refreshed after every file-repair round.
        rows = [i for i in collect_issues(_pf, state, False, False)[0]
                if i.get("file") and not selfrepair.PROTECTED.search(str(i.get("file")))]
        return rows

    file_fixable = [i for i in issues if i.get("file") and not selfrepair.PROTECTED.search(str(i.get("file")))]
    if do_repair and file_fixable:                           # Phase 6: bounded file-level self-repair
        sr = selfrepair.repair_files(
            pf,
            file_fixable,
            check=_file_repair_check,
            reverify=(lambda _pf: _deep_failed_check_names(_pf, deep)) if deep else None,
        )
        issues = [i for i in issues if not i.get("file") or selfrepair.PROTECTED.search(str(i.get("file")))] + sr["remaining"]
        state.usage["out"] += sr["usage_tokens"]
        report["selfrepair"] = {k: sr[k] for k in ("status", "fixed", "rounds", "attempts", "stop", "blocked", "log")}
        state.repair_count += bool(sr["attempts"])
    if deep:
        # This pass is read-only: it may execute only the project's declared allowlisted
        # checks when dependencies are already installed; it never installs dependencies.
        from backend.tools.project_verifier import verify_backend
        deep_result = verify_backend(pf, deep=True)
        report["deep_project_verification"] = {
            "status": deep_result.get("status", "unknown"),
            "note": deep_result.get("note", ""),
            "issues": deep_result.get("issues", []),
        }
        report["checks"].extend(deep_result.get("checks", []))
        for item in deep_result.get("blocking_issues", []):
            issues.append({"sid": None, "msg": "deep verification: " + str(item.get("message", "check failed"))[:500]})

    # Final project-wide language audit. The normal pass parses supported syntax and
    # reuses build evidence collected above. Deep mode additionally invokes only the
    # analyzer's fixed/allowlisted local toolchain checks; it never installs packages.
    from backend.tools.quality_gate import run_quality_gate
    selected_stack = (state.stack_config or {}).get("stack") or {}
    require_logic_tests = (
        state.plan.get("layout") in {"app", "dashboard"}
        or selected_stack.get("backend") not in (None, "", "none")
        or len((state.plan.get("features") or [])) >= 4
    )
    quality = run_quality_gate(
        pf,
        deep=deep,
        existing_checks=report.get("checks", []),
        require_logic_tests=require_logic_tests,
    )
    report["quality_gate"] = quality
    report.setdefault("notes", []).extend(quality.get("notes", [])[:8])
    # Static parser/compiler failures discovered by the audit must never be omitted from
    # the task result. Avoid duplicate diagnostics already returned by the repair loop.
    for diagnostic in quality.get("issues", []):
        if diagnostic.get("severity") != "error":
            continue
        rel = str(diagnostic.get("file") or "").replace("\\", "/")
        message = str(diagnostic.get("message") or "language verification failed")[:450]
        pretty = (f"{rel}: " if rel else "") + f"quality gate ({diagnostic.get('tool', 'analyzer')}): {message}"
        duplicate = any(
            (rel and str(existing.get("file") or "").replace("\\", "/") == rel
             and (message in str(existing.get("msg", "")) or str(existing.get("msg", "")) in pretty))
            or (not rel and message in str(existing.get("msg", "")))
            for existing in issues
        )
        if not duplicate:
            issues.append({"sid": None, "file": rel or None, "line": diagnostic.get("line"), "msg": pretty})

    if quality.get("status") == "partial":
        gaps = quality.get("coverage_gaps", [])
        gap_text = ", ".join(dict.fromkeys(str(g.get("language", "unknown")) for g in gaps))
        if gap_text:
            context.progress("verify", "Verification is partial; no suitable local compiler/parser evidence for: " + gap_text[:220], "warn")
        if require_logic_tests and quality.get("logical_status") in {"not_proven", "test_coverage_partial"}:
            context.progress("verify", "Build/syntax checks are not a proof of business logic; test evidence is missing or incomplete.", "warn")
        if quality.get("logical_status") == "needs_review":
            context.progress("verify", f"Potential logic red flags need review ({len(quality.get('actionable_logic_hints', []))} finding(s)); checks do not prove the code is correct.", "warn")

    if rollback_failure_note:
        issues.append({"sid": None, "file": None, "msg": rollback_failure_note})

    report["vision"] = vision.analyze(extra.get("images", {}), state.plan.get("sections", [])) if vision_on else \
        {"status": "skipped", "note": "no vision model configured (optional)" if not _vision_enabled() else "browser checks did not run", "findings": []}
    report["repairs"] = repair_log
    report["spec"] = _spec_report(state)
    report["backend"] = backend_stage.status(pf)
    counts = {s: sum(1 for c in report["checks"] if c["status"] == s) for s in ("passed", "failed", "skipped")}
    report["counts"] = counts
    state.errors = [(f"{i['sid']}: " if i["sid"] else "") + i["msg"] for i in issues]
    state.files = {p: pf.hash(p) for p in pf.tree()}
    state.phase = "done" if not issues and quality.get("status") == "passed" else "verify"
    project_store.save(state)
    try:
        pf.write(".agent/report.json", json.dumps(report, indent=1)[:190000])
    except ValueError:
        pass
    total = len(state.plan.get("sections", []))
    context.progress("verify", f"{len(issues)} issue(s) remaining after {state.repair_count} repair loop(s); checks: "
                               f"{counts['passed']} passed, {counts['failed']} failed, {counts['skipped']} skipped; "
                               f"multi-language gate: {quality.get('status', 'unknown').upper()}")
    for f in report["vision"]["findings"]:
        context.progress("vision", f"[{f['viewport']}] {f['msg']}", "warn")
    db.touch_project(pid)
    history.add(pid, "agent", f"{len(state.sections_done)}/{total} sections, {len(issues)} issues, {state.repair_count} repair loops")
    return {"project_id": pid, "phase": state.phase, "sections_done": state.sections_done,
            "sections_total": total, "files": list(state.files), "issues": state.errors,
            "repairs": state.repair_count, "browser": note, "shots": screenshots.list_shots(pf),
            "usage": state.usage, "open": f"generated_projects/{pid}/index.html", "stack": state.plan.get("stack", "html"),
            "report": report, "verification_status": quality.get("status", "unknown"),
            "quality_gate": quality,
            "warnings": [f"[{f['viewport']}] {f['msg']}" for f in report["vision"]["findings"]],
            "repair_log": repair_log[-30:]}


def _stack_gate(state) -> None:
    """Never silently swap the user's technology: refuse what has no generator yet, and list what is not generated yet."""
    cfg = (state.stack_config or {}).get("stack")
    if not cfg:
        return
    r = stack_engine.readiness(cfg)
    if r["blocking"]:
        raise ValueError(" ".join(r["blocking"]) + " Choose HTML/CSS/JS or React + TypeScript for now, or wait for the phase that adds it.")
    for p in r["pending"]:
        context.progress("stack", f"Not generated yet in this build: {p}. Only the frontend is produced.", "warn")


def run(pid: str, force: bool = False, tr: "progress.Tracker | None" = None) -> dict:
    """analyze -> plan -> design -> backend -> code -> verify (auto-repair loop), every step tracked."""
    state = project_store.load(pid)
    if not state:
        raise ValueError("project not found")
    tr = tr or progress.Tracker("generate")
    pf = ProjectFiles(pid)
    with tr.step("analyze") as o:
        _stack_gate(state)
        analysis = _spec_stage(state)
        c = analysis["counts"]
        o["detail"] = f"{c['covered']} covered, {c['planned']} planned, {c['gap']} gap"
        o["status"] = "issues" if (c["planned"] or c["gap"] or analysis["blocking"]) else "done"
    with tr.step("backend") as o:
        o["status"], o["detail"] = _backend_stage(state, pf)
    backend_note = o["detail"] if o["status"] == "issues" else ""
    state.errors = []
    if force:
        state.plan, state.sections_done = {}, []
    if state.plan:
        tr.skip("plan", "plan already exists")
    else:
        with tr.step("plan"):
            state.phase = "plan"
            context.progress("plan", "Planning structure, design tokens and motion")
            _add(state, planner.blueprint(state))
            project_store.save(state)
    if force or "index.html" not in pf.tree():
        with tr.step("design"):
            state.phase = "design"
            context.progress("design", "Scaffolding design system and animation library")
            code_engine.scaffold(pf, state)
            state.sections_done = []
            project_store.save(state)
    else:
        tr.skip("design", "scaffold already exists")
    with tr.step("code") as o:
        state.phase = "code"
        if state.plan.get("layout") == "app":
            from backend.engines import app_engine
            if force or not (pf.root / "src" / "App.tsx").is_file():
                app_engine.generate(pf, state)
            state.sections_done = ["app"]
            project_store.save(state)
            o["detail"] = "schema-driven application shell and CRUD flows generated"
        else:
            _add(state, code_engine.generate_sections(pf, state))
            project_store.save(state)
            o["detail"] = f"{len(state.sections_done)}/{len(state.plan.get('sections', []))} sections"
    with tr.step("verify") as o:
        # Autopilot generation uses the deep read-only verification pass by default.
        # It runs only pre-approved local compiler/build/test commands with existing
        # dependencies; it never installs packages. Missing toolchains/tests stay partial.
        res = verify(pid, deep=True)
        o["status"] = "done" if res.get("verification_status") == "passed" and not res["issues"] else "issues"
        o["detail"] = (f"{len(res['issues'])} issue(s), {res['repairs']} repair loop(s); "
                       f"quality gate {res.get('verification_status', 'unknown')}")
    return {**res, "analysis": analysis, "backend_note": backend_note}


def edit(pid: str, section: str, instruction: str, tr: "progress.Tracker | None" = None) -> dict:
    """Natural-language edit of ONE section via small patches, then quick static verify."""
    state = project_store.load(pid)
    if not state:
        raise ValueError("project not found")
    tr = tr or progress.Tracker("edit")
    pf = ProjectFiles(pid)
    with tr.step("edit"):
        _add(state, repair_engine.edit(pf, state, section, instruction))
        project_store.save(state)
        history.add(pid, "user", f"edit {section}: {instruction}")
    with tr.step("verify") as o:
        res = verify(pid, do_repair=False, with_browser=False)
        o["status"] = "done" if res.get("verification_status") == "passed" and not res["issues"] else "issues"
        o["detail"] = f"{len(res['issues'])} issue(s); quality gate {res.get('verification_status', 'unknown')}"
    return res

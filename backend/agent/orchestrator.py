import hashlib
import json

from backend import config
from backend.agent import planner, context, progress, requirements, selfrepair
from backend.storage import db
from backend.engines import code_engine, react_engine, repair_engine, quality_engine
from backend.memory import project_store, history
from backend.tools import browser, screenshots, vision
from backend.tools.project_files import ProjectFiles
from backend.tools.validators import validate_html, validate_css
from backend import stack as stack_engine
from backend import spec as spec_engine
from backend.spec import memory as spec_memory
from backend.gen import stage as backend_stage


def _add(state, u: dict) -> None:
    state.usage["in"] += u["in"]
    state.usage["out"] += u["out"]


MAX_TRIES_PER_ISSUE = 2        # the same issue is never repaired more than twice (patch, then full-section regen)


def _sig(i: dict) -> str:
    return hashlib.md5(f"{i.get('sid')}|{i['msg']}".encode()).hexdigest()[:10]


def _task_id() -> str:
    c = context.current()
    return c.task_id if c else ""


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
    issues += quality_engine.inspect(pf, state)          # missing assets, fake placeholders and dead forms
    extra = {"report": {"checks": checks, "a11y": [], "notes": []}, "images": {}}
    serve_dir, note = pf.root, "skipped"
    if state.plan.get("stack") == "react":
        restored = react_engine.restore_static(pf) if (pf.root / "package.json").is_file() else []
        if restored:
            context.progress("repair", f"Restored missing scaffold file(s): {', '.join(restored)}")
        b = react_engine.build(pf, state)
        for build_issue in b["issues"]:
            msg = str(build_issue.get("msg", ""))
            file_match = __import__("re").search(r"\b((?:src/)[\w./-]+\.(?:tsx?|jsx?|css))", msg)
            if file_match:
                build_issue["file"] = file_match.group(1)
                line_match = __import__("re").search(r"\((\d+),\d+\)", msg) or __import__("re").search(r":(\d+):\d+", msg)
                build_issue["line"] = int(line_match.group(1)) if line_match else None
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


def verify(pid: str, do_repair: bool = True, with_browser: bool | None = None) -> dict:
    with_browser = config.USE_BROWSER if with_browser is None else with_browser
    state = project_store.load(pid)
    if not state:
        raise ValueError("project not found")
    pf = ProjectFiles(pid)
    normalized = code_engine.normalize_existing_ids(pf, state)
    if normalized:
        context.progress("verify", f"Normalized duplicate or conflicting IDs in {normalized} section(s) without an LLM call")
    issues, note, extra = [], "skipped", {}
    max_loops = min(db.get_settings()["max_repair_loops"], 5)
    tries: dict[str, int] = {}                   # issue signature -> repair attempts this cycle
    pending: list[dict] = []                     # repairs whose outcome is judged by the next check pass
    repair_log: list[dict] = []
    vision_on = with_browser and _vision_enabled()
    for attempt in range(max_loops + 1):
        context.check()
        context.progress("verify", f"Running checks (pass {attempt + 1})")
        issues, note, extra = collect_issues(pf, state, with_browser, vision_on)
        now = {_sig(i) for i in issues}
        for rp in pending:                       # record what the previous repair actually achieved
            outcome = "error" if rp["method"] == "error" else ("still_failing" if rp["sig"] in now else "fixed")
            row = {"attempt": rp["attempt"], "sid": rp["sid"], "issue": rp["msg"][:160], "method": rp["method"], "outcome": outcome}
            repair_log.append(row)
            db.add_repair_attempt(pid, _task_id(), rp["attempt"], rp["sid"], rp["msg"], rp["sig"], rp["method"], outcome)
        pending = []
        fixable = [i for i in issues if i["sid"] and tries.get(_sig(i), 0) < MAX_TRIES_PER_ISSUE]
        for i in issues:
            if i["sid"] and tries.get(_sig(i), 0) >= MAX_TRIES_PER_ISSUE:
                context.progress("repair", f"Not retrying '{i['sid']}': {i['msg'][:60]} (already tried {MAX_TRIES_PER_ISSUE}x)", "warn")
        if not do_repair or not fixable or attempt == max_loops:
            break
        context.progress("repair", f"Repair attempt {attempt + 1}/{max_loops}: {len(fixable)} issue(s)")
        regen = {i["sid"] for i in fixable if tries.get(_sig(i), 0) >= 1}      # a patch already failed -> regenerate that section
        res = repair_engine.fix(pf, state, fixable, regen)
        _add(state, res)
        done = {e["sid"]: e["method"] for e in res.get("log", [])} or {i["sid"]: "patch" for i in fixable}
        for i in fixable:
            if i["sid"] in done:
                tries[_sig(i)] = tries.get(_sig(i), 0) + 1
                pending.append({"attempt": attempt + 1, "sid": i["sid"], "msg": i["msg"], "sig": _sig(i), "method": done[i["sid"]]})
        state.repair_count += 1
        project_store.save(state)
    report = extra.get("report", {"checks": [], "a11y": [], "notes": []})
    if do_repair and any(i.get("file") for i in issues):     # Phase 6: bounded file-level self-repair
        sr = selfrepair.repair_files(
            pf,
            [i for i in issues if i.get("file")],
            check=lambda _pf: [i for i in collect_issues(_pf, state, False, False)[0] if i.get("file")],
        )
        issues = [i for i in issues if not i.get("file")] + sr["remaining"]
        state.usage["out"] += sr["usage_tokens"]
        report["selfrepair"] = {k: sr[k] for k in ("status", "fixed", "rounds", "attempts", "stop", "blocked", "log")}
        state.repair_count += bool(sr["attempts"])
    report["vision"] = vision.analyze(extra.get("images", {}), state.plan.get("sections", [])) if vision_on else \
        {"status": "skipped", "note": "no vision model configured (optional)" if not _vision_enabled() else "browser checks did not run", "findings": []}
    report["repairs"] = repair_log
    report["spec"] = _spec_report(state)
    report["backend"] = backend_stage.status(pf)
    counts = {s: sum(1 for c in report["checks"] if c["status"] == s) for s in ("passed", "failed", "skipped")}
    report["counts"] = counts
    state.errors = [(f"{i['sid']}: " if i["sid"] else "") + i["msg"] for i in issues]
    state.files = {p: pf.hash(p) for p in pf.tree()}
    state.phase = "done" if not issues else "verify"
    project_store.save(state)
    try:
        pf.write(".agent/report.json", json.dumps(report, indent=1)[:190000])
    except ValueError:
        pass
    total = len(state.plan.get("sections", []))
    context.progress("verify", f"{len(issues)} issue(s) remaining after {state.repair_count} repair loop(s); checks: "
                               f"{counts['passed']} passed, {counts['failed']} failed, {counts['skipped']} skipped")
    for f in report["vision"]["findings"]:
        context.progress("vision", f"[{f['viewport']}] {f['msg']}", "warn")
    db.touch_project(pid)
    history.add(pid, "agent", f"{len(state.sections_done)}/{total} sections, {len(issues)} issues, {state.repair_count} repair loops")
    return {"project_id": pid, "phase": state.phase, "sections_done": state.sections_done,
            "sections_total": total, "files": list(state.files), "issues": state.errors,
            "repairs": state.repair_count, "browser": note, "shots": screenshots.list_shots(pf),
            "usage": state.usage, "open": f"generated_projects/{pid}/index.html", "stack": state.plan.get("stack", "html"),
            "report": report, "warnings": [f"[{f['viewport']}] {f['msg']}" for f in report["vision"]["findings"]],
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
        res = verify(pid)
        o["status"] = "issues" if res["issues"] else "done"
        o["detail"] = f"{len(res['issues'])} issue(s), {res['repairs']} repair loop(s)"
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
        o["status"] = "issues" if res["issues"] else "done"
        o["detail"] = f"{len(res['issues'])} issue(s)"
    return res

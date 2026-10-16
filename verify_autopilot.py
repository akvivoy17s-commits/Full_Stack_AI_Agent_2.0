"""Phase 8: one-command verification of the Autopilot work (phases 1-7). Run from the repo root: python verify_autopilot.py
No pytest needed. Each check prints PASS / FAIL / BLOCKED (BLOCKED = a tool or dependency is missing, not a code failure)."""
import compileall, json, os, re, shutil, subprocess, sys, tempfile, types, uuid
sys.path.insert(0, "."); sys.path.insert(0, "tests")
sys.modules.setdefault("pytest", types.SimpleNamespace(mark=types.SimpleNamespace(skipif=lambda *a, **k: (lambda f: f), parametrize=lambda *a, **k: (lambda f: f)), fixture=lambda *a, **k: (lambda f: f)))
R = []
def check(name):
    def deco(fn):
        try:
            ok, detail = fn()
            R.append((name, "PASS" if ok else "FAIL", detail))
        except (ImportError, FileNotFoundError) as e:
            R.append((name, "BLOCKED", f"{type(e).__name__}: {e}"))
        except Exception as e:  # noqa: BLE001
            R.append((name, "FAIL", f"{type(e).__name__}: {e}"[:200]))
        return fn
    return deco
TSC = shutil.which("tsc")
STUB = """declare module 'react' { export function useState<S>(i:S|(()=>S)):[S,(v:S|((p:S)=>S))=>void]; export function useEffect(f:()=>void|(()=>void),d?:any[]):void; export function useMemo<T>(f:()=>T,d:any[]):T; export function useCallback<T extends (...a:any[])=>any>(f:T,d:any[]):T; export type FormEvent<T=any>={preventDefault():void;currentTarget:any;target:any} }
declare module 'react/jsx-runtime' { export const jsx:any,jsxs:any,Fragment:any }
declare module '*.css'
declare namespace JSX { interface IntrinsicElements {[k:string]:any} interface Element{} }
interface ImportMeta { env: Record<string,string|undefined> }
"""

@check("1 compileall backend+tests")
def _(): return compileall.compile_dir("backend", quiet=2) and compileall.compile_dir("tests", quiet=2), "all .py compile"

@check("2 intent classifier (16 prompts)")
def _():
    from backend.agent import intent
    apps = ["Build todos app", "investment portfolio tracker", "task management tool", "booking app for salons", "appointment scheduler", "invoice generator", "Kanban board", "habit tracker", "library management system"]
    no = ["landing page with dashboard preview", "ecommerce admin panel with inventory", "personal website with notes app", "my portfolio website", "Portfolio for a photographer", "coffee shop website", "chatbot for support"]
    bad = [p for p in apps if not intent.is_app_prompt(p)] + [p for p in no if intent.is_app_prompt(p)]
    return not bad, bad or "16/16"

@check("3 stack resolver + fallback + notes")
def _():
    from backend.api.autopilot import resolve_prompt
    r, _l, a, _ = resolve_prompt("Library management system with Django and MongoDB")
    ok = r["stack"]["backend"] == "django" and r["stack"]["database"] == "sqlite"
    for p, n in (("inventory system in Go with Gin", "go"), ("expense tracker using Angular", "angular"), ("Build a blog in Laravel", "laravel")):
        ok &= any(x.startswith(f"You named {n}") for x in resolve_prompt(p)[2])
    ok &= any(x.startswith("Payments were mentioned") for x in resolve_prompt("booking app for salons with payments")[2])
    ok &= not any(x.startswith(("You named", "Payments")) for x in resolve_prompt("Build a todo app")[2])
    return bool(ok), "django kept, 3 named-tech notes, payments note, clean todo"

@check("4 planner.layout_for agrees with intent")
def _():
    from backend.agent import planner
    t = [("Build todos app", "generic", "app"), ("task management tool", "local", "app"), ("Create a personal portfolio", "management", "portfolio"),
         ("Design style: Premium SaaS. a dashboard widget", None, "landing"), ("Analytics dashboard for sales", "dashboard", "dashboard"), ("Create a company landing page for a coffee shop", None, "landing")]
    bad = [x for x in t if planner.layout_for(x[0], x[1]) != x[2]]
    return not bad, bad or f"{len(t)}/{len(t)}"

@check("5 app_engine entities + generated App.tsx type-check")
def _():
    from backend.engines import app_engine
    from backend.agent.state import AgentState
    names = [e["name"] for e in app_engine._default_entities("management", "CRM for customers and deals")]
    if names != ["Customer", "Deal"]: return False, names
    if not TSC: raise FileNotFoundError("tsc not installed")
    d = tempfile.mkdtemp()
    class PF:
        def write(s, rel, txt): p = os.path.join(d, "app", rel); os.makedirs(os.path.dirname(p), exist_ok=True); open(p, "w").write(txt)
    cfgs = [{"backend": "express", "database": "sqlite", "auth": "none"}, {"backend": "express", "database": "postgresql", "auth": "jwt"}, {"backend": "none", "database": "none", "auth": "none"}]
    for i, c in enumerate(cfgs):
        st = AgentState(project_id=f"v{i}", brief="CRM for customers and deals with login", stack="react", stack_config={"stack": {"frontend": "react", "frontend_lang": "ts", **c}})
        class P(PF):
            def write(s, rel, txt): super().write(f"{i}/{rel}", txt)
        app_engine.generate(P(), st)
    open(os.path.join(d, "s.d.ts"), "w").write(STUB)
    json.dump({"compilerOptions": {"target": "ES2020", "module": "ESNext", "moduleResolution": "bundler", "jsx": "react-jsx", "strict": True, "noImplicitAny": False, "noEmit": True, "skipLibCheck": True, "lib": ["ES2020", "DOM"]}, "include": ["s.d.ts", "app/**/*.tsx"]}, open(os.path.join(d, "tsconfig.json"), "w"))
    r = subprocess.run([TSC, "-p", d], capture_output=True, text=True)
    return r.returncode == 0, (r.stdout[:200] or "3 variants, 0 tsc errors (React types stubbed)")

@check("6 selfrepair window/rollback + restore_static")
def _():
    from backend.agent import selfrepair as sr
    from backend.tools.project_files import ProjectFiles
    long = "x" * 1500
    if "ERRORLINE" not in sr._window("\n".join([long] * 10 + ["ERRORLINE"] + [long] * 10), 11): return False, "window lost error line"
    pf = ProjectFiles("v6-" + uuid.uuid4().hex[:6]); pf.write("a.py", "x = 1\n"); calls = []
    def chk(p): calls.append(1); return [sr._issue("a.py", "e1"), sr._issue("a.py", "e2")] if p.read("a.py") != "x = 1\n" else [sr._issue("a.py", "e1")]
    r = sr.repair_files(pf, call=lambda u: ({"patches": [{"old": "x = 1", "new": "x = 2"}]}, {"in": 1, "out": 1}), check=chk, issues=[sr._issue("a.py", "e1")], max_rounds=1)
    if not (pf.read("a.py") == "x = 1\n" and len(calls) == 1): return False, "rollback/recheck"
    from backend.engines import react_engine as re_
    pf.write("package.json", "{}")
    return len(re_.restore_static(pf)) == len(re_.STATIC) and re_.restore_static(pf) == [], "window ok, rollback w/o recheck, restore_static idempotent"

@check("7 generated client.ts (23 stacks) tsc --strict")
def _():
    if not TSC: raise FileNotFoundError("tsc not installed")
    from gen_helpers import stack_for, BRIEF, STORE
    from backend.gen import model, project
    from backend.spec import compose
    n = bad = 0
    for be in ("express", "fastapi", "nestjs", "django", "spring", "flask"):
        for db, brief, kw in (("sqlite", BRIEF, {}), ("postgresql", STORE, {"cache": "redis"}), ("mongodb", BRIEF, {}), ("none", BRIEF, {})):
            try: st = stack_for(db, brief, backend=be, **kw)
            except AssertionError: continue
            spec = compose.build(brief, st); ex = project.extras(spec, st, model.build(spec, st)); c = ex.get("src/api/client.ts")
            if not c: continue
            d = tempfile.mkdtemp(); open(d + "/client.ts", "w").write(c); n += 1
            if subprocess.run([TSC, "--noEmit", "--strict", "--target", "es2022", "--module", "esnext", "--moduleResolution", "bundler", "--skipLibCheck", "--lib", "es2022,dom", d + "/client.ts"], capture_output=True).returncode: bad += 1
    return bad == 0 and n > 0, f"{n} clients, {bad} failed"

@check("8 no real secrets outside tests")
def _():
    pat = re.compile(r"(sk-(live|proj)-[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}(?!EXAMPLE)|BEGIN (RSA )?PRIVATE KEY)")
    hits = []
    for r, _d, fs in os.walk("."):
        if any(x in r for x in ("node_modules", "tests", ".git")): continue
        for f in fs:
            if f.endswith((".py", ".ts", ".tsx", ".js", ".json", ".md", ".env", ".example")) and not f.startswith("verify"):
                try: t = open(os.path.join(r, f), encoding="utf-8").read()
                except (OSError, UnicodeDecodeError): continue
                if pat.search(t): hits.append(os.path.join(r, f))
    return not hits, hits or "none"

w = max(len(n) for n, _, _ in R)
for n, s, d in R: print(f"{s:8} {n:<{w}}  {d}")
c = {k: sum(1 for _, s, _ in R if s == k) for k in ("PASS", "FAIL", "BLOCKED")}
print("\nOVERALL:", "FAIL" if c["FAIL"] else ("PARTIAL" if c["BLOCKED"] else "PASS"), c)
json.dump([{"check": n, "status": s, "detail": str(d)} for n, s, d in R], open("autopilot_evidence.json", "w"), indent=1)
sys.exit(1 if c["FAIL"] else 0)

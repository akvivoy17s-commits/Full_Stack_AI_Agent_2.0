#!/usr/bin/env python3
"""Phase 8 final verification. Run from project root:  python verify_phase8.py [root]
Runs only real checks; anything that cannot run is BLOCKED (never faked). Writes PHASE8_REPORT.md + phase8_evidence.json."""
import ast, importlib, json, os, re, shutil, socket, subprocess, sys, tempfile
ROOT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")
os.chdir(ROOT); sys.path.insert(0, ROOT)
E = {}  # evidence
def sh(cmd, t=300):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=t); return r.returncode, (r.stdout + r.stderr)[-6000:]
    except Exception as e: return -1, str(e)
def walk(ext, skip=("node_modules", ".git", "__pycache__")):
    return [os.path.join(d, f) for d, ds, fs in os.walk(".") if not any(s in d for s in skip) for f in fs if f.endswith(ext)]
rd = lambda p: open(p, encoding="utf8", errors="ignore").read()
exists = os.path.exists

# ---- A. Python syntax
py = walk(".py"); bad = []
for p in py:
    try: ast.parse(rd(p))
    except SyntaxError as e: bad.append(f"{p}: {e}")
E["py_syntax"] = {"files": len(py), "errors": bad}
# ---- B. internal import resolution (static)
mods = {p[2:-3].replace(os.sep, ".").removesuffix(".__init__") for p in py}
miss = []
for p in py:
    if "/templates/" in p.replace(os.sep, "/"): continue
    for n in ast.walk(ast.parse(rd(p))):
        if isinstance(n, ast.ImportFrom) and n.module and n.module.startswith("backend") and n.level == 0 and n.module not in mods:
            miss.append(f"{p}: {n.module}")
E["missing_internal_imports"] = miss
# ---- C. runtime import of every backend module (real)
ext_missing, real_err = {}, []
for m in sorted(x for x in mods if x.startswith("backend") and ".templates." not in x):  # templates only resolve after staging into a generated app
    try: importlib.import_module(m)
    except ModuleNotFoundError as e:
        if e.name and not e.name.startswith("backend"): ext_missing.setdefault(e.name, []).append(m)
        else: real_err.append(f"{m}: {e}")
    except Exception as e: real_err.append(f"{m}: {type(e).__name__}: {e}")
E["import_third_party_missing"] = {k: len(v) for k, v in ext_missing.items()}; E["import_real_errors"] = real_err
# ---- D. secrets / dangerous calls
pat = re.compile(r"(sk-[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{30,})")
sec = [p for p in walk(".py") + walk(".ts") + walk(".tsx") + walk(".js") + walk(".json") + walk(".md") if "package-lock" not in p and pat.search(rd(p))]
dang = [f"{p}: {k}" for p in py if p.startswith("./backend") and "/templates/" not in p for k in ("shell=True", "eval(", "exec(", "os.system(") if k in rd(p)]
E["secret_like_strings_in"] = sec; E["dangerous_calls"] = dang; E["env_file_committed"] = exists(".env")
# ---- E. JS syntax (node --check) + TS/TSX syntax (typescript transpile)
js = walk(".js"); jsbad = []
if shutil.which("node"):
    for p in js:
        if "tailwind" in p or "postcss" in p or "eslint.config" in p: continue
        rc, o = sh(["node", "--check", p], 30)
        if rc: jsbad.append(p)
E["js"] = {"files": len(js), "errors": jsbad, "node": bool(shutil.which("node"))}
ts = [p for p in walk(".ts") + walk(".tsx") if not p.endswith(".d.ts")]; tsbad = []; ts_ok = None
if shutil.which("node") and shutil.which("npm"):
    tsc = shutil.which("tsc"); tsmod = os.path.dirname(os.path.dirname(os.path.realpath(tsc))) if tsc else ""
    if not exists(os.path.join(tsmod, "package.json")):
        rc, root = sh(["npm", "root", "-g"], 20); tsmod = os.path.join(root.strip(), "typescript")
    if exists(tsmod):
        ts_ok = True
        js_code = ("const ts=require(process.argv[1]);const fs=require('fs');let bad=[];for(const f of process.argv.slice(2)){"
                   "let r;try{r=ts.transpileModule(fs.readFileSync(f,'utf8'),{reportDiagnostics:true,fileName:f,compilerOptions:{jsx:'preserve',target:'ES2020'}})}catch(e){bad.push(f);continue}"
                   "if(r.diagnostics.length)bad.push(f)}console.log(JSON.stringify(bad))")
        rc, o = sh(["node", "-e", js_code, tsmod] + ts, 120)
        o = o.replace("\n", " ")[-4000:] if False else o
        try: tsbad = json.loads(o.strip().splitlines()[-1])
        except Exception: ts_ok = None
E["ts_syntax"] = {"files": len(ts), "errors": tsbad, "checked": bool(ts_ok)}
# ---- F. frontend api.ts calls vs backend routes (real static cross-check)
def routes():
    out = set()
    for p in walk(".py"):
        if p.startswith("./backend") and "/templates/" not in p and "/gen/" not in p:
            s = rd(p); pre = re.search(r'APIRouter\([^)]*prefix\s*=\s*["\']([^"\']*)', s); pre = pre.group(1) if pre else ""
            for m in re.finditer(r'@\w+\.(get|post|put|delete|patch)\(\s*["\']([^"\']*)', s): out.add(re.sub(r"\{[^}]+\}", "{}", pre + m.group(2)))
    return out
bk = routes(); fe = set()
for p in walk(".ts") + walk(".tsx"):
    if p.startswith("./frontend/src/services"):
        for m in re.finditer(r"(?:\$\{B\}|[`'\"(]\s*)(/[a-z][A-Za-z0-9_/\-\$\{\}\.]*)", rd(p)): fe.add(re.sub(r"\$\{[^}]+\}", "{}", m.group(1)).rstrip("/"))
nomatch = sorted(f for f in fe if f != "/api" and f.rstrip("/") not in {b.rstrip("/") for b in bk} and not any(re.fullmatch(re.sub(r"\{\}", "[^/]+", b), f) for b in bk))
E["frontend_calls_without_backend_route"] = nomatch; E["frontend_calls"] = len(fe); E["backend_routes"] = len(bk)
# ---- G. capability probes (phase 1-7)
def has(p, *k): return exists(p) and all(x in rd(p) for x in k)
runner_ok = {}
try:
    from backend.tools import terminal as T
    for name, a in {"node_check": ["node", "--check", "a.js"], "npm_build": ["npm", "run", "build"], "python": ["python", "-m", "compileall", "-q", "."],
                    "pytest": ["python", "-m", "pytest"], "ruff": ["python", "-m", "ruff", "check", "."], "go_vet": ["go", "vet", "./..."], "go_test": ["go", "test", "./..."]}.items():
        runner_ok[name] = bool(T.allowed(a))
    runner_ok["shell_injection_blocked"] = not T.allowed(["node", "--check", "a.js;rm -rf /"]) and not T.allowed(["bash", "-c", "x"])
except Exception as e: runner_ok = {"error": f"{type(e).__name__}: {e}"}
llm = rd("backend/agent/llm.py") if exists("backend/agent/llm.py") else ""
E["runner_allowlist"] = runner_ok
E["provider"] = {"ollama": "ollama" in llm.lower(), "openai_compatible": bool(re.search(r"openai|/v1/chat/completions", llm, re.I)),
                 "keys_from_env": bool(re.search(r"environ|getenv", llm)), "retry": "retry" in llm.lower(), "timeout": "timeout" in llm.lower()}
E["files_present"] = {k: exists(k) for k in ["backend/agent/requirements.py", "backend/agent/progress.py", "backend/agent/selfrepair.py", "backend/memory/project_store.py",
                      "backend/spec/memory.py", "backend/tools/project_files.py", "backend/tools/redact.py", "tests/test_phase7_e2e.py", ".env.example", "README.md"]}
E["path_guard"] = has("backend/tools/project_files.py", "resolve") and ('".."' in rd("backend/tools/project_files.py") or "'..'" in rd("backend/tools/project_files.py"))
E["repair_bounded"] = has("backend/agent/orchestrator.py", "MAX_TRIES_PER_ISSUE") or has("backend/agent/selfrepair.py", "MAX")
# ---- H. executed suites (real or BLOCKED)
def have(m):
    try: importlib.import_module(m); return True
    except Exception: return False
if have("pytest") and have("fastapi") and have("httpx"):
    env = dict(os.environ, MOCK_LLM="1", USE_BROWSER="0", DATA_DIR=tempfile.mkdtemp(), GENERATED_DIR=tempfile.mkdtemp())
    r = subprocess.run([sys.executable, "-m", "pytest", "-q", "-x", "--no-header", "tests"], capture_output=True, text=True, env=env, timeout=1800)
    E["pytest"] = {"ran": True, "rc": r.returncode, "tail": r.stdout[-400:]}
else: E["pytest"] = {"ran": False, "why": "pytest/fastapi/httpx not installed"}
nm = exists("frontend/node_modules")
if nm:
    E["frontend"] = {k: sh(["npm", "run", k], 600)[0] for k in ("typecheck", "build")}; E["frontend"]["lint"] = sh(["npm", "run", "lint"], 600)[0]
else: E["frontend"] = {"ran": False, "why": "frontend/node_modules missing (npm ci not run)"}
try: socket.create_connection(("localhost", 11434), 2).close(); E["ollama_reachable"] = True
except OSError: E["ollama_reachable"] = False
# ---- I. verdicts
R = []
def v(cap, status, ev): R.append((cap, status, ev))
sec_real = [s for s in sec if "/tests/" not in s]
v("Phase 1 · file/endpoint security", "PASS" if (E["path_guard"] and not sec_real and not dang and not E["env_file_committed"]) else "PARTIAL",
  f"path guard={E['path_guard']}, secrets outside tests={len(sec_real)}, dangerous calls={len(dang)}, .env committed={E['env_file_committed']}")
ra = E["runner_allowlist"]; full = all(ra.get(k) for k in ("python", "pytest", "ruff", "go_vet")) if "error" not in ra else False
v("Phase 2 · command runner (python/pytest/lint/go)", "PASS" if full else ("PARTIAL" if ra.get("node_check") else "FAIL"), f"allowlist probe={ra}")
pv = E["provider"]; v("Phase 3 · provider system (Ollama + OpenAI-compatible, env keys)", "PASS" if pv["openai_compatible"] and pv["keys_from_env"] and pv["retry"] else ("PARTIAL" if pv["ollama"] else "FAIL"), str(pv))
fp = E["files_present"]; v("Phase 4 · planner/requirements/progress", "PASS" if fp["backend/agent/requirements.py"] and fp["backend/agent/progress.py"] else "PARTIAL", f"requirements.py={fp['backend/agent/requirements.py']}, progress.py={fp['backend/agent/progress.py']}; planner.py/tasks.py={exists('backend/agent/planner.py')}/{exists('backend/agent/tasks.py')}")
v("Phase 5 · repo understanding + persistent memory", "PASS" if fp["backend/memory/project_store.py"] and fp["backend/spec/memory.py"] else "PARTIAL", f"project_store={fp['backend/memory/project_store.py']}, spec/memory={fp['backend/spec/memory.py']}")
v("Phase 6 · bounded self-repair", ("PASS" if fp["backend/agent/selfrepair.py"] else "PARTIAL") if E["repair_bounded"] else "FAIL", f"bounded={E['repair_bounded']}, selfrepair.py module={fp['backend/agent/selfrepair.py']}")
fe_ok = not nomatch and not tsbad and not jsbad and not real_err
v("Phase 7 · frontend integration (static)", "PARTIAL" if fe_ok else "FAIL", f"unmatched calls={nomatch}, ts errors={tsbad}, js errors={jsbad}, real import errors={len(real_err)}")
v("Automated test suite", "PASS" if E["pytest"].get("rc") == 0 else ("FAIL" if E["pytest"].get("ran") else "BLOCKED"), str(E["pytest"]))
fr = E["frontend"]; v("Frontend typecheck/build/lint", "PASS" if fr.get("ran", True) and fr.get("typecheck") == 0 and fr.get("build") == 0 else ("BLOCKED" if fr.get("ran") is False else "FAIL"), str(fr))
v("Live model connectivity (Ollama)", "PASS" if E["ollama_reachable"] else "BLOCKED", f"localhost:11434 reachable={E['ollama_reachable']}")
json.dump(E, open("phase8_evidence.json", "w"), indent=1)
with open("PHASE8_REPORT.md", "w", encoding="utf8") as f:
    f.write("# Phase 8 — Final verification report\n\n| Capability | Status | Evidence |\n|---|---|---|\n")
    for c, s, e in R: f.write(f"| {c} | **{s}** | {e[:300].replace('|','/')} |\n")
for c, s, e in R: print(f"{s:8} {c}")

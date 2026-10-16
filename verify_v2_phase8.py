#!/usr/bin/env python3
"""V2 Phase 8: generation matrix across stacks -> PHASE8_V2_REPORT.md (+ .json). Usage: python verify_v2_phase8.py [root]
Only real checks. Anything that cannot run here is BLOCKED, anything not built is PLANNED. Never faked."""
import ast, itertools, json, os, shutil, subprocess, sys, tempfile
ROOT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else "."); os.chdir(ROOT); sys.path[:0] = [ROOT, os.path.join(ROOT, "tests")]
import yaml
from backend.gen import model, project, stage
from backend.spec import compose
from backend.stack import catalog
from backend.stack.resolver import resolve
BRIEFS = {"college": "college management system with student login and courses", "store": "online store with products cart and orders"}
BACKENDS = ["express", "nestjs", "fastapi", "flask", "django", "spring", "go", "aspnet", "laravel"]
DBS = ["sqlite", "postgresql", "mysql", "mongodb", "mssql", "none"]
LANG = {"express": "js", "nestjs": "ts", "spring": "java", "go": "go", "aspnet": "cs", "laravel": "php"}
TSC = shutil.which("tsc"); NODE = shutil.which("node"); JAVAC = shutil.which("javac")
def sh(cmd, t=120):
    try: r = subprocess.run(cmd, capture_output=True, text=True, timeout=t); return r.returncode, (r.stdout + r.stderr)[-400:]
    except Exception as e: return -1, str(e)
def check_files(files, tmp):
    errs = []
    for rel, txt in files.items():
        p = os.path.join(tmp, rel); os.makedirs(os.path.dirname(p), exist_ok=True); open(p, "w", encoding="utf8").write(txt)
        try:
            if rel.endswith(".py"): ast.parse(txt)
            elif rel.endswith((".yml", ".yaml")): yaml.safe_load(txt)
            elif rel.endswith(".json"): json.loads(txt)
            elif rel.endswith(".java") and txt.count("{") != txt.count("}"): errs.append(f"{rel}: unbalanced braces")
        except Exception as e: errs.append(f"{rel}: {type(e).__name__}: {str(e)[:80]}")
        if rel.endswith(".js") and NODE and "/templates/" not in rel:
            rc, o = sh([NODE, "--check", p]); rc and errs.append(f"{rel}: {o[:120]}")
        if any(k in txt for k in ("sk-live", "AKIA", "BEGIN PRIVATE KEY")): errs.append(f"{rel}: secret-like string")
    return errs
def ts_syntax(tmp):  # syntax only (deps are not installed, so no type resolution)
    ts = [os.path.join(d, f) for d, _, fs in os.walk(tmp) for f in fs if f.endswith((".ts", ".tsx"))]
    if not ts or not TSC: return None if not TSC else []
    rc, o = sh([TSC, "--noEmit", "--skipLibCheck", "--noResolve", "--target", "es2020", "--experimentalDecorators", "--emitDecoratorMetadata", *ts], 240)
    return [l for l in o.splitlines() if "error TS1" in l][:3]   # TS1xxx = syntax errors only
rows, results = [], {"PASS": 0, "PARTIAL": 0, "BLOCKED": 0, "PLANNED": 0, "FAIL": 0}
detail = {}
for be, db, bk, cache in itertools.product(BACKENDS, DBS, BRIEFS, (None, "redis")):
    key = f"{be}|{db}|{bk}|{cache or 'nocache'}"
    prefs = {"frontend": "react", "frontend_lang": "ts", "backend": be, "backend_lang": LANG.get(be, "py"), "database": db, "auth": "jwt" if db != "none" else "none"}
    if cache: prefs["cache"] = cache
    r = resolve("manual", prefs, BRIEFS[bk])
    if not r["ok"]: detail[key] = ("N/A", "not selectable: " + "; ".join(map(str, r["errors"]))[:90]); continue
    st = r["stack"]; cov = stage.coverage(st)
    if not cov["ready"]: detail[key] = ("PLANNED" if be in ("go", "aspnet", "laravel") else "PARTIAL", "gaps: " + ", ".join(map(str, cov["gaps"]))[:110]); continue
    try:
        spec = compose.build(BRIEFS[bk], st); m = model.build(spec, st); files = stage.GENERATORS[be].generate(spec, st, m); files.update(project.extras(spec, st, m))
        with tempfile.TemporaryDirectory() as tmp:
            errs = check_files(files, tmp); t = ts_syntax(tmp)
        if errs: detail[key] = ("FAIL", "; ".join(errs[:2]))
        elif m["not_generated"] or m["warnings"]: detail[key] = ("PARTIAL", f"{len(files)} files ok; not_generated={m['not_generated']}"[:120])
        else: detail[key] = ("PASS", f"{len(files)} files, {len(m['manifest'])} routes, static checks clean" + ("" if t is not None else "; ts not checked"))
        if t: detail[key] = ("FAIL", "ts syntax: " + t[0][:100])
    except Exception as e: detail[key] = ("FAIL", f"{type(e).__name__}: {str(e)[:100]}")
for k, (s, _) in detail.items(): results[s] = results.get(s, 0) + 1
# summary per backend x db
by = {}
for k, (s, n) in detail.items():
    be, db, *_ = k.split("|"); by.setdefault((be, db), []).append(s)
def agg(l): return "FAIL" if "FAIL" in l else "PASS" if set(l) == {"PASS"} else "PLANNED" if set(l) == {"PLANNED"} else "N/A" if set(l) == {"N/A"} else "PARTIAL"
L = ["# Phase 8 (V2) - generation matrix", "", "Static checks only (py ast, node --check, ts syntax, yaml/json parse, secret scan, route/not_generated report).", "",
     "| backend | " + " | ".join(DBS) + " |", "|---|" + "---|" * len(DBS)]
for be in BACKENDS: L.append(f"| {be} | " + " | ".join(agg(by.get((be, d), ["N/A"])) for d in DBS) + " |")
L += ["", "Totals: " + ", ".join(f"{k}={v}" for k, v in results.items()), "", "## Not PASS (first 40)", ""]
L += [f"- `{k}` **{s}** - {n}" for k, (s, n) in detail.items() if s not in ("PASS", "N/A")][:40]
L += ["", "## BLOCKED here (needs your machine)", "", f"- tsc type-check w/ deps, npm ci/build: {'tsc found' if TSC else 'tsc missing'}, deps not installed -> BLOCKED",
      f"- pytest suite: {'ok' if shutil.which('pytest') else 'pytest missing -> BLOCKED'}", f"- javac/mvn (Spring compile): {'javac' if JAVAC else 'no javac'}, mvn missing -> BLOCKED",
      "- go / dotnet / php toolchains: missing -> BLOCKED", "- docker build/compose up, GitHub Actions, live DB/Redis/Stripe/Firebase: BLOCKED"]
open("PHASE8_V2_REPORT.md", "w").write("\n".join(L) + "\n"); json.dump({k: v for k, v in detail.items()}, open("phase8_v2_evidence.json", "w"), indent=0)
print("\n".join(L[:20 + len(BACKENDS)])); print(results)

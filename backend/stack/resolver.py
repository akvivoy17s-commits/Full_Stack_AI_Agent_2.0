"""Technology selection engine: Automatic / Manual / Hybrid. Rules only, so it costs zero LLM tokens.

Precedence for every field:  user choice  >  existing project  >  explicit mention in the brief  >  automatic pick.
Automatic picks are always constrained by what is already fixed, and the final stack goes through rules.validate().
A user-selected technology is never silently replaced: an incompatibility is returned as an error instead."""
from backend.stack import catalog as C, rules
from backend.stack.analyze import analyze

MODES = ("automatic", "manual", "hybrid")
MANUAL_REQUIRED = ("frontend", "backend", "database")
PYTHON_BACKENDS = ("fastapi", "flask", "django")
GEN_FIELDS = ("frontend", "backend", "database", "auth", "cache", "storage", "ai", "testing", "deploy")


def label(field: str, value: str) -> str:
    return C.TABLES.get(field, {}).get(value, {}).get("label", value)


def clean_prefs(prefs) -> dict:
    out = {}
    for k, v in (prefs or {}).items():
        if k not in C.FIELDS:
            raise ValueError(f"unknown option '{k}'")
        v = None if v is None else str(v).strip().lower()
        if v in (None, "", "auto"):
            continue
        out[k] = v
    return out


def legacy_stack(stack: dict) -> str | None:
    """Maps to the generator that exists today: 'html' or 'react' (React + Vite + TypeScript). None = no generator yet."""
    fe, lang = stack.get("frontend"), stack.get("frontend_lang")
    if fe == "html":
        return "html"
    return "react" if fe == "react" and lang == "ts" else None


def readiness(stack: dict) -> dict:
    gen = {f: C.status(f, stack.get(f) or "none", stack) for f in GEN_FIELDS}
    blocking = [] if gen["frontend"] == C.READY else [
        f"{label('frontend', stack.get('frontend'))} + {label('frontend_lang', stack.get('frontend_lang'))} generator is not available yet ({gen['frontend']})."]
    pending = [f"{f}: {label(f, stack[f])} ({s})" for f, s in gen.items()
               if f != "frontend" and s != C.READY and stack.get(f) not in (None, "", "none")]
    return {"generator": gen, "blocking": blocking, "pending": pending}


# ------------------------------------------------------------------ need helpers (explicit choices beat the brief)
def _needs_backend(req: dict, s: dict) -> bool:
    if s.get("backend"):
        return s["backend"] != "none"
    if C.db_group(s.get("database")) in ("sql", "mongodb") or s.get("auth") in ("jwt", "session", "oauth2"):
        return True
    if s.get("cache") in ("redis", "memory") or s.get("storage") in ("local", "s3") or s.get("ai") not in (None, "", "none"):
        return True
    return req["needs"]["backend"]


def _needs_db(req: dict, s: dict) -> bool:
    if s.get("database"):
        return s["database"] != "none"
    return s.get("auth") in ("jwt", "session") or req["needs"]["db"]


# ------------------------------------------------------------------ pickers: each returns (value, short reason)
def _frontend_ok(c: str, s: dict) -> bool:
    spec = C.FRONTEND[c]
    return not ((s.get("frontend_lang") and s["frontend_lang"] not in spec["langs"])
                or (s.get("testing") and s["testing"] not in C.TESTING_FOR[c])
                or (s.get("deploy") == "static" and spec["kind"] == "ssr"))


def _frontend(req: dict, s: dict):
    pick, why = _frontend_pick(req, s)
    if _frontend_ok(pick, s):
        return pick, why
    for c in ("react", "vue", "next", "svelte", "angular", "html", "solid", "nuxt", "sveltekit"):
        if _frontend_ok(c, s):
            return c, f"{why}; switched to {label('frontend', c)} to honour your other selections"
    return pick, why


def _frontend_pick(req: dict, s: dict):
    n, kind, cx = req["needs"], req["kind"], req["complexity"]
    be = s.get("backend")
    if n["firebase"] and not n["enterprise"] and kind not in ("ecommerce", "cms"):
        return "react", "Firebase covers data and auth, so a client-rendered React app is enough"
    if kind in ("portfolio", "landing", "site", "generic", "local") and cx == "simple":
        return "html", "Simple informational site: no framework or build step needed"
    if kind in ("ecommerce", "cms") or (n["seo"] and cx != "simple" and kind not in ("dashboard", "chat", "chatbot", "management")):
        return "react", "This build can generate React + TypeScript; Next.js SSR is a future option, so keep SEO content server-independent"
    if kind == "management" or n["enterprise"] or (be in ("spring", "aspnet") and cx != "simple"):
        return "react", "Use the available React + TypeScript generator; Angular's enterprise tooling is catalogued but not scaffolded yet"
    return "react", "Interactive application UI: React with TypeScript is a solid default"


def _backend_ok(c: str, s: dict) -> bool:
    spec = C.BACKEND[c]
    # Automatic decisions are bounded by checked-in generators, not just catalog labels.
    # Explicitly selected planned technologies remain selectable and are reported as pending.
    g = C.GENERATORS.get(c)
    if not g:
        return False
    lang = s.get("backend_lang")
    if lang and lang not in g["langs"]:
        return False
    db = s.get("database") or "none"
    if db != "none" and db not in g["db"]:
        return False
    grp = C.db_group(db)
    if grp and grp not in C.ORMS[c]:
        return False
    orm = s.get("orm")
    wanted = g["orm"].get(grp or "")
    if orm and orm not in ("none", wanted) and db != "none":
        return False
    for field in ("auth", "cache", "storage", "ai"):
        selected = s.get(field) or "none"
        if selected not in g[field]:
            return False
    if s.get("ai") == "python-inprocess" and spec["runtime"] != "python":
        return False
    return True


def _backend(req: dict, s: dict):
    n, kind, cx, fe = req["needs"], req["kind"], req["complexity"], s.get("frontend")
    if not _needs_backend(req, s):
        return "none", "No server-side requirement: the browser (or Firebase) covers everything"
    c: list[tuple[str, str]] = []
    if s.get("ai") == "python-inprocess":
        c.append(("fastapi", "Python backend required to host the AI module in-process"))
    elif n["ai"] == "ml":
        c.append(("fastapi", "ML/vision/NLP work belongs in Python; FastAPI gives typed async endpoints"))
    if kind == "chatbot":
        c.append(("fastapi", "AI chatbot: FastAPI handles streaming and LLM clients well"))
    if kind == "cms":
        c.append(("django", "A CMS needs admin, auth, ORM and migrations out of the box"))
    if (kind == "management" or n["enterprise"]) and cx == "complex":
        c.append(("nestjs", "Enterprise-style modules and dependency injection are available in the generated NestJS backend"))
    if n["microsoft"] and cx != "simple":
        c.append(("aspnet", "Microsoft/Azure environment mentioned"))
    if fe == "angular":
        c.append(("nestjs", "NestJS mirrors Angular's modules and dependency injection"))
    if kind == "ecommerce" and cx == "complex":
        c.append(("nestjs", "Complex commerce domain benefits from NestJS modules and DI"))
    if n["realtime"]:
        c.append(("express", "WebSockets (Socket.IO) are straightforward on Node"))
    c.append(("express", "Simple, flexible REST API with the least moving parts"))
    for cand, why in c:
        if _backend_ok(cand, s):
            return cand, why
    for cand in C.BACKEND:                               # nothing preferred fits the fixed choices: first backend that does
        if cand != "none" and _backend_ok(cand, s):
            return cand, "The only backend compatible with your other selections"
    return c[-1][0], "No backend fits all selections (see errors)"


def _database(req: dict, s: dict):
    n, cx, be = req["needs"], req["complexity"], s["backend"]
    if be == "none":
        if n["firebase"]:
            return ("firebase-rtdb" if n["rtdb"] else "firestore"), "Firebase requested and there is no backend, so a browser-safe BaaS is used"
        return "none", "No backend selected, so nothing is persisted (choose Firebase to store data without a server)"
    if not _needs_db(req, s):
        return "none", "No persistent data required"
    c: list[tuple[str, str]] = []
    if n["firebase"]:
        c.append(("firestore", "Firebase requested"))
    if n["documents"]:
        c.append(("mongodb", "Flexible, nested documents fit MongoDB"))
    if be == "laravel" or n["mysql_hosting"]:
        c.append(("mysql", "MySQL is the standard choice for Laravel and shared hosting"))
    if be == "aspnet" and n["microsoft"]:
        c.append(("mssql", "SQL Server fits the Microsoft/Azure environment"))
    if n["local"] or cx == "simple":
        c.append(("sqlite", "Zero-setup file database fits a small or local app"))
    c += [("postgresql", "Relational data with transactions, constraints and complex queries"),
          ("mysql", "Relational database with wide hosting support"), ("sqlite", "Zero-setup file database")]
    orm = s.get("orm")
    for cand, why in c:
        grp = C.db_group(cand)
        if grp in C.ORMS[be] and (not orm or orm == "none" or orm in C.ORMS[be][grp]):
            return cand, why
    return "none", "No database fits the selected backend"


def _fill(stack: dict, src: dict, why: dict, req: dict, smart: bool, notes: list) -> None:
    n, cx = req["needs"], req["complexity"]

    def put(f, v, reason):
        stack[f], src[f], why[f] = v, ("auto" if smart else "default"), reason

    if "frontend" not in stack:
        put("frontend", *_frontend(req, stack))
    fe = stack["frontend"]
    if "frontend_lang" not in stack:
        langs = C.FRONTEND[fe]["langs"]
        put("frontend_lang", "ts" if "ts" in langs else "js", "TypeScript catches errors early" if "ts" in langs else "This framework choice has no build step")
    if "backend" not in stack:
        put("backend", *_backend(req, stack))
    be = stack["backend"]
    if "backend_lang" not in stack:
        langs = C.BACKEND[be]["langs"] if be != "none" else [""]
        # Pick a language the checked-in generator can actually emit. Express TypeScript is
        # catalogued as a future option; selecting it automatically would silently produce
        # only a frontend until that generator lands. Explicit user/brief choices still win.
        generated_langs = {"express": "js", "nestjs": "ts", "fastapi": "py", "flask": "py", "django": "py"}
        lang = generated_langs.get(be, langs[0] if langs else "")
        if lang not in langs and langs:
            lang = langs[0]
        put("backend_lang", lang, "Compatible with the available backend generator" if be in generated_langs else "Fixed by the selected framework")
    if "database" not in stack:
        put("database", *_database(req, stack))
    db = stack["database"]
    grp = C.db_group(db)
    if "orm" not in stack:
        pool = C.ORMS.get(be, {}).get(grp or "", [])
        put("orm", pool[0] if pool else "none", "Default data layer for this backend and database" if pool else "No database layer needed")
    if "auth" not in stack:
        if not (n["auth"] and smart):
            put("auth", "none", "No sign-in required")
        elif db == "none" and be != "none" and grp != "firebase":
            put("auth", "none", "Sign-in was requested but no database is selected to store users")
            notes.append({"fields": ["auth", "database"], "field": "auth", "msg": "The brief asks for sign-in, but no database is selected, so authentication was skipped."})
        elif grp == "firebase" or be == "none":
            put("auth", "firebase-auth", "Firebase Authentication needs no extra user store")
        elif be in ("django", "laravel"):
            put("auth", "session", "Framework-native session authentication")
        else:
            put("auth", "jwt", "Stateless tokens suit an API consumed by a separate frontend")
    if "cache" not in stack:
        use = smart and be != "none" and (n["cache"] or (n["realtime"] and cx == "complex"))
        put("cache", "redis" if use else "none", "Caching or realtime scale was requested" if use else "Not justified: no cache added")
    if "storage" not in stack:
        if smart and n["uploads"]:
            v = "firebase-storage" if (be == "none" or grp == "firebase") else ("s3" if n["s3"] else "local")
            put("storage", v, "File uploads requested")
        else:
            put("storage", "none", "No file uploads")
    if "ai" not in stack:
        if smart and n["ai"] != "none" and be == "none":
            put("ai", "none", "AI features need a backend, and none is selected")
            notes.append({"fields": ["ai", "backend"], "field": "ai", "msg": "The brief asks for AI features, but no backend is selected to run them safely."})
        elif smart and n["ai"] == "ml":
            put("ai", "python-inprocess" if be in PYTHON_BACKENDS else "python-service",
                "ML code runs inside the Python backend" if be in PYTHON_BACKENDS else "ML needs Python: isolated service next to the primary backend")
        elif smart and n["ai"] == "llm":
            put("ai", "llm-api", "A hosted LLM called from the backend is enough: no separate AI service needed")
        else:
            put("ai", "none", "No AI features")
    if "testing" not in stack:
        # The agent performs its own available checks, but it does not currently scaffold every
        # frontend unit-test runner into generated projects. Do not select a planned tool by default.
        put("testing", "none", "No extra frontend test runner requested; the agent still runs available verification")
    if "deploy" not in stack:
        if not smart:
            put("deploy", "local", "Local only")
        elif n["firebase"] and be == "none":
            put("deploy", "firebase-hosting", "Matches the Firebase project")
        elif be == "none" and C.FRONTEND[fe]["kind"] != "ssr":
            put("deploy", "static", "Frontend only: any static host works")
        else:
            # Local run instructions are available. Docker files are not emitted in this build,
            # so deployment remains an explicit choice instead of a default unsupported promise.
            put("deploy", "local", "Local development; deployment target not requested")


def _derived(stack: dict) -> dict:
    be = stack.get("backend") or "none"
    runtimes = {C.FRONTEND[stack["frontend"]]["runtime"], C.BACKEND[be]["runtime"]} - {"none"}
    if stack.get("ai") in ("python-service", "python-inprocess"):
        runtimes.add("python")
    return {"runtimes": [C.RUNTIME_NAME[r] for r in sorted(runtimes)], "backend_tests": C.BACKEND_TESTS[be],
            "legacy_stack": legacy_stack(stack), "full_stack": be != "none" or C.db_group(stack.get("database")) == "firebase"}


def _summary(stack: dict) -> str:
    fe = f"{label('frontend', stack['frontend'])}{'' if stack['frontend'] == 'html' else ' (' + label('frontend_lang', stack['frontend_lang']) + ')'}"
    parts = [fe]
    be = stack.get("backend") or "none"
    if be != "none":
        parts.append(label("backend", be) + (f" ({label('backend_lang', stack['backend_lang'])})" if be == "express" else ""))
    for f in ("database", "auth", "cache", "storage", "ai"):
        if stack.get(f) not in (None, "", "none"):
            parts.append(label(f, stack[f]))
    return " · ".join(parts)


def resolve(mode: str = "automatic", prefs: dict | None = None, brief: str = "", existing: dict | None = None,
            with_options: bool = False) -> dict:
    if mode not in MODES:
        raise ValueError(f"mode must be one of {MODES}")
    req = analyze(brief)
    warnings, errors = [], []
    user = clean_prefs(prefs)
    if mode == "automatic" and user:
        warnings.append({"fields": [], "field": None, "msg": "Automatic mode ignores manual selections; use Hybrid to keep them."})
        user = {}
    fixed, src = {}, {}
    for f, v in user.items():
        fixed[f], src[f] = v, "user"
    for f, v in clean_prefs(existing).items():
        if f not in fixed:
            fixed[f], src[f] = v, "existing"
    for f, v in req["mentions"].items():
        if f not in fixed:
            fixed[f], src[f] = v, "brief"
        elif fixed[f] != v and src[f] != "brief":
            warnings.append({"fields": [f], "field": f, "msg": f"The brief mentions {label(f, v)} but {label(f, fixed[f])} ({src[f]}) is kept."})
    stack, why = dict(fixed), {}

    for f, v in fixed.items():                                          # unknown ids: report, do not guess
        if v not in C.TABLES[f]:
            errors.append({"fields": [f], "field": f, "msg": f"Unknown {f.replace('_', ' ')} '{v}'."})
    if not errors and mode == "manual":
        for f in MANUAL_REQUIRED:
            if f not in stack:
                errors.append({"fields": [f], "field": f, "msg": f"Manual mode needs a {f} choice (use 'none' if it is not required)."})
    if errors:
        return _result(mode, stack, src, why, req, errors, warnings, False)

    notes: list = []
    _fill(stack, src, why, req, mode != "manual", notes)
    e, w = rules.validate(stack)
    return _result(mode, stack, src, why, req, errors + e, warnings + notes + w, with_options)


def _result(mode, stack, src, why, req, errors, warnings, with_options) -> dict:
    out = {"mode": mode, "ok": not errors, "stack": stack, "sources": src, "reasons": why, "errors": errors, "warnings": warnings,
           "requirements": {k: req[k] for k in ("kind", "complexity", "signals")}}
    if not errors:
        out["summary"] = _summary(stack)
        out["derived"] = _derived(stack)
        out.update(readiness(stack))
        if with_options:
            out["options"] = rules.options(stack)
    return out


summary = _summary


# ------------------------------------------------------------------ project persistence helpers
def for_new_project(mode: str | None, prefs: dict | None, brief: str, framework: str = "html") -> tuple[dict, str]:
    """(resolution, legacy generator id) for POST /projects. Without a mode the request is the old frontend-only flow."""
    if mode:
        res = resolve(mode, prefs, brief)
        return res, ((res.get("derived") or {}).get("legacy_stack") or framework)
    res = resolve("manual", {"frontend": framework, "frontend_lang": "js" if framework == "html" else "ts",
                             "backend": "none", "database": "none"}, "")
    return res, framework

def config_of(result: dict) -> dict:
    """What gets stored on the project (state.stack_config): the stack plus where each choice came from. No secrets."""
    return {"mode": result["mode"], "stack": result["stack"], "sources": result["sources"], "reasons": result["reasons"]}


def existing_from(state) -> dict | None:
    """The project's current stack for 'extend, do not migrate'. Only choices that came from the user, the brief or an
    earlier 'existing' stack are carried over; automatic/default picks are re-derived so a changed core choice cannot
    leave a stale ORM or test runner behind."""
    cfg = getattr(state, "stack_config", None) or {}
    keep = {f: v for f, v in (cfg.get("stack") or {}).items() if (cfg.get("sources") or {}).get(f) in ("user", "brief", "existing")}
    return keep or None

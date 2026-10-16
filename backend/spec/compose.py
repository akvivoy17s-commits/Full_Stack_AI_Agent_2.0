"""Build the application spec from (brief, resolved stack, user overrides). Zero LLM tokens, deterministic.

The spec is the contract later phases consume: backend generators read `entities` + `api`, the API client reads `api`,
the verifier checks the generated code against it. It describes what the *selected stack* will contain; brief needs the
stack does not cover are reported honestly under `gaps` instead of being faked.
"""
import hashlib
import json
import re

from backend.stack import catalog as C
from backend.stack.analyze import analyze, split_style
from backend.spec import templates as T

SPEC_VERSION = 1
TYPES = {"string", "text", "int", "float", "bool", "datetime", "email", "url"}
_FIELD = re.compile(r"^([a-z][a-z0-9_]{0,30}):(string|text|int|float|bool|datetime|email|url|ref\([A-Z][A-Za-z0-9]{1,30}\)|enum\([a-z0-9_|]{1,80}\))(!?)(@?)$")
_NAME = re.compile(r"^[A-Z][A-Za-z0-9]{1,30}$")
_SLUG = re.compile(r"^[a-z][a-z0-9-]{0,30}$")
NO_CRUD = {"User", "OrderItem"}
PUBLIC_PREFIX = {"react": "VITE_", "vue": "VITE_", "svelte": "VITE_", "solid": "VITE_", "next": "NEXT_PUBLIC_", "nuxt": "NUXT_PUBLIC_", "sveltekit": "PUBLIC_"}
DB_URL = {"sqlite": "sqlite:///./app.db", "postgresql": "postgresql://user:password@localhost:5432/appdb",
          "mysql": "mysql://user:password@localhost:3306/appdb", "mssql": "mssql://user:password@localhost:1433/appdb"}
PROVIDERS = {"razorpay": r"razorpay", "paypal": r"paypal", "stripe": r"stripe"}


# ------------------------------------------------------------------ fields / entities
def parse_field(tok: str) -> dict:
    m = _FIELD.match(tok.strip())
    if not m:
        raise ValueError(f"invalid field '{tok}' (expected name:type[!][@])")
    name, typ, req, uniq = m.groups()
    f = {"name": name, "type": typ, "required": bool(req), "unique": bool(uniq)}
    if typ.startswith("ref("):
        f["type"], f["ref"] = "ref", typ[4:-1]
    elif typ.startswith("enum("):
        f["type"], f["values"] = "enum", typ[5:-1].split("|")
    return f


def plural(n: str) -> str:
    p = re.sub(r"(?<!^)(?=[A-Z])", "-", n).lower()
    if re.search(r"[^aeiou]y$", p):
        return p[:-1] + "ies"
    return p + ("es" if re.search(r"(s|x|ch|sh)$", p) else "s")


def _entity(name: str, tokens: list[str], read: str, write: str, roles: list[str]) -> dict:
    fields = [parse_field(t.replace("{roles}", "|".join(roles))) for t in tokens]
    return {"name": name, "path": plural(name), "fields": fields, "read": read, "write": write,
            "sensitive": [f["name"] for f in fields if f["name"] in ("password_hash",)],
            "searchable": [f["name"] for f in fields if f["type"] in ("string", "text") and f["name"] not in ("password_hash",)][:3],
            "relations": [{"field": f["name"], "to": f["ref"]} for f in fields if f["type"] == "ref"]}


def integrity(entities: list[dict]) -> list[str]:
    names, probs = {e["name"] for e in entities}, []
    for e in entities:
        seen = set()
        for f in e["fields"]:
            if f["name"] in seen:
                probs.append(f"{e['name']}.{f['name']} is defined twice")
            seen.add(f["name"])
            if f.get("ref") and f["ref"] not in names:
                probs.append(f"{e['name']}.{f['name']} references unknown entity {f['ref']}")
    return probs


def _variant(brief: str) -> tuple[str, dict]:
    for pat, label, ents in T.MANAGEMENT_VARIANTS:
        if re.search(pat, brief, re.I):
            return label, ents
    return "generic", T.ENTITIES["management"]


def _entities(kind: str, text: str, auth: bool, needs: dict, contact: bool, roles: list[str]) -> tuple[list[dict], str]:
    src, variant = dict(T.ENTITIES.get(kind, {})), ""
    if kind == "management":
        variant, src = _variant(text)
        src = dict(src)
    for need in ("payments", "uploads"):
        if needs.get(need):
            src.update(T.NEED_ENTITIES[need])
    if contact:
        src.update(T.NEED_ENTITIES["contact"])
    elif needs.get("email") and kind == "landing":
        src.update(T.NEED_ENTITIES["newsletter"])
    out = []
    if auth:
        out.append(_entity("User", *T.USER, roles))
    for name, (toks, rd, wr) in src.items():
        if not auth:                                           # no accounts -> no owner links, everything public
            toks = [t for t in toks if "ref(User)" not in t]
            rd, wr = "public", "public"
        out.append(_entity(name, toks, rd, wr, roles))
    return out, variant


def _apply_entity_overrides(ents: list[dict], ov: dict, roles: list[str]) -> list[dict]:
    drop = set(ov.get("drop_entities", []))
    before = {e["name"]: e for e in ents}
    ents = [e for e in ents if e["name"] not in drop]
    for name, toks in (ov.get("entities") or {}).items():
        prev = before.get(name)          # editing fields of an existing entity keeps its access rules
        new = _entity(name, toks, prev["read"] if prev else "user", prev["write"] if prev else "owner", roles)
        ents = [e for e in ents if e["name"] != name] + [new]
    return ents


# ------------------------------------------------------------------ api
def _plain(a: str) -> str:
    return "user" if a == "owner" else a


def _api(ents: list[dict], needs: dict, kind: str, stack: dict, auth: bool, contact: bool) -> list[dict]:
    out = [{"method": "GET", "path": "/api/health", "entity": None, "access": "public", "summary": "Service health check"}]
    if auth:
        a = stack.get("auth")
        if a in ("jwt", "session"):
            out += [{"method": "POST", "path": "/api/auth/register", "entity": "User", "access": "public", "summary": "Create an account"},
                    {"method": "POST", "path": "/api/auth/login", "entity": "User", "access": "public", "summary": "Sign in"},
                    {"method": "POST", "path": "/api/auth/logout", "entity": None, "access": "user", "summary": "Sign out"}]
            if a == "jwt":
                out.append({"method": "POST", "path": "/api/auth/refresh", "entity": None, "access": "public", "summary": "Exchange a refresh token"})
        out.append({"method": "GET", "path": "/api/auth/me", "entity": "User", "access": "user", "summary": "Current user"})
    for e in ents:
        if e["name"] in NO_CRUD and e["name"] != "User":
            continue
        base = f"/api/{e['path']}"
        if e["name"] == "User":
            out += [{"method": "GET", "path": base, "entity": "User", "access": "admin", "summary": "List users", "paginated": True}]
            continue
        n, q = e["name"], e["searchable"]
        out += [{"method": "GET", "path": base, "entity": n, "access": _plain(e["read"]), "summary": f"List {e['path']}", "paginated": True, "query": q},
                {"method": "GET", "path": base + "/{id}", "entity": n, "access": _plain(e["read"]), "summary": f"Get one {n}"},
                {"method": "POST", "path": base, "entity": n, "access": _plain(e["write"]), "summary": f"Create {n}"},
                {"method": "PUT", "path": base + "/{id}", "entity": n, "access": e["write"], "summary": f"Update {n}"},
                {"method": "DELETE", "path": base + "/{id}", "entity": n, "access": e["write"], "summary": f"Delete {n}"}]
    if kind == "ecommerce":
        out.append({"method": "POST", "path": "/api/checkout", "entity": "Order", "access": "user", "summary": "Create an order from the cart"})
    if needs.get("payments"):
        out += [{"method": "POST", "path": "/api/payments/intent", "entity": "Payment", "access": "user", "summary": "Start a payment"},
                {"method": "POST", "path": "/api/payments/webhook", "entity": "Payment", "access": "public", "summary": "Provider webhook (signature verified)"}]
    if needs.get("uploads"):
        out.append({"method": "POST", "path": "/api/uploads", "entity": "FileAsset", "access": "user" if auth else "public", "summary": "Upload a file (type + size limited)"})
    if needs.get("realtime"):
        out.append({"method": "WS", "path": "/ws", "entity": None, "access": "user" if auth else "public", "summary": "Live updates"})
    if needs.get("ai") in ("llm", "ml") and stack.get("ai") not in (None, "none"):
        out.append({"method": "POST", "path": "/api/ai/chat" if needs["ai"] == "llm" else "/api/ai/predict", "entity": None,
                    "access": "user" if auth else "public", "summary": "AI request (server-side key, timeout, structured errors)"})
    for r in out:
        if r["entity"] and r["entity"] in ("Enquiry", "Subscriber") and r["method"] == "POST":
            r["rate_limited"] = True
    return out


# ------------------------------------------------------------------ env / security / tests / plan
def _env(stack: dict, needs: dict, text: str, backend_on: bool) -> list[dict]:
    out = []

    def add(name, purpose, placeholder, scope="server", secret=None):
        sec = bool(re.search(r"KEY|SECRET|PASSWORD|TOKEN", name)) if secret is None else secret
        out.append({"name": name, "scope": scope, "secret": sec, "placeholder": placeholder, "purpose": purpose})
    fe = stack.get("frontend")
    pre = PUBLIC_PREFIX.get(fe, "")
    if backend_on:
        add("PORT", "HTTP port", "8000")
        add("CORS_ORIGINS", "Allowed browser origins (comma separated)", "http://localhost:5173")
        if pre or fe in ("html", "angular"):
            add(f"{pre}API_URL" if pre else "API_BASE_URL", "Backend base URL used by the frontend API client", "http://localhost:8000", "public", False)
    db = stack.get("database") or "none"
    if db in DB_URL:
        add("DATABASE_URL", "Database connection string", DB_URL[db], secret=db != "sqlite")
    elif db == "mongodb":
        add("MONGODB_URI", "MongoDB connection string", "mongodb://localhost:27017/appdb", secret=True)
    elif db in ("firestore", "firebase-rtdb"):
        add("FIREBASE_PROJECT_ID", "Firebase project id", "your-project-id", secret=False)
        if backend_on:
            add("FIREBASE_SERVICE_ACCOUNT_PATH", "Path to the service-account JSON (never commit it)", "./secrets/service-account.json", secret=True)
        if not backend_on or stack.get("auth") == "firebase-auth":
            for k in ("API_KEY", "AUTH_DOMAIN", "APP_ID"):
                add(f"{pre}FIREBASE_{k}", "Firebase web config (public by design; protect data with security rules)", "your-value", "public", False)
    a = stack.get("auth")
    if a == "jwt":
        add("JWT_SECRET", "Signing key for access tokens (long random string)", "<generate-a-long-random-string>")
        add("JWT_ACCESS_TTL_MIN", "Access token lifetime in minutes", "15", secret=False)
        add("JWT_REFRESH_TTL_DAYS", "Refresh token lifetime in days", "7", secret=False)
    elif a == "session":
        add("SESSION_SECRET", "Session cookie signing key", "<generate-a-long-random-string>")
    elif a == "oauth2":
        add("OAUTH_CLIENT_ID", "OAuth client id", "your-client-id", secret=False)
        add("OAUTH_CLIENT_SECRET", "OAuth client secret", "your-client-secret")
    if stack.get("cache") == "redis":
        add("REDIS_URL", "Redis connection string", "redis://localhost:6379/0", secret=True)
    st = stack.get("storage")
    if st == "local":
        add("UPLOAD_DIR", "Directory for uploaded files (development)", "./uploads", secret=False)
    elif st == "s3":
        for k, v in (("S3_ENDPOINT", "https://s3.amazonaws.com"), ("S3_BUCKET", "your-bucket"), ("S3_REGION", "us-east-1"),
                     ("S3_ACCESS_KEY_ID", "your-access-key-id"), ("S3_SECRET_ACCESS_KEY", "your-secret-access-key")):
            add(k, "S3-compatible storage setting", v, secret=k in ("S3_ACCESS_KEY_ID", "S3_SECRET_ACCESS_KEY"))
    ai = stack.get("ai")
    if ai == "llm-api" or (ai == "python-inprocess" and needs.get("ai") == "llm"):
        add("LLM_PROVIDER", "LLM provider id", "openai", secret=False)
        add("LLM_API_KEY", "LLM API key (server side only)", "your-api-key")
        add("LLM_MODEL", "Model name", "your-model-name", secret=False)
    if ai == "python-service":
        add("AI_SERVICE_URL", "Internal URL of the Python AI service", "http://localhost:8100", secret=False)
        add("AI_SERVICE_TOKEN", "Shared secret between the backend and the AI service", "<generate-a-long-random-string>")
    if needs.get("payments"):
        p = provider(text)
        if p == "razorpay":
            add("RAZORPAY_KEY_ID", "Razorpay key id", "your-key-id", secret=True)
            add("RAZORPAY_KEY_SECRET", "Razorpay key secret", "your-key-secret")
            add("RAZORPAY_WEBHOOK_SECRET", "Razorpay webhook secret", "your-webhook-secret")
        elif p == "paypal":
            add("PAYPAL_CLIENT_ID", "PayPal client id", "your-client-id", secret=True)
            add("PAYPAL_CLIENT_SECRET", "PayPal client secret", "your-client-secret")
            add("PAYPAL_WEBHOOK_ID", "PayPal webhook id (the signature check needs it)", "your-webhook-id", secret=False)
            add("PAYPAL_ENV", "PayPal environment: sandbox or live", "sandbox", secret=False)
        else:
            add("STRIPE_SECRET_KEY", "Stripe secret key", "your-secret-key")
            add("STRIPE_WEBHOOK_SECRET", "Stripe webhook signing secret", "your-webhook-secret")
            add(f"{pre}STRIPE_PUBLISHABLE_KEY", "Stripe publishable key (public by design)", "your-publishable-key", "public", False)
    if needs.get("email"):
        for k, v in (("SMTP_HOST", "smtp.example.com"), ("SMTP_PORT", "587"), ("SMTP_USER", "your-smtp-user"),
                     ("SMTP_PASSWORD", "your-smtp-password"), ("MAIL_FROM", "no-reply@example.com")):
            add(k, "Outgoing email setting", v, secret=k == "SMTP_PASSWORD")
    return out


def provider(text: str) -> str:
    for p, pat in PROVIDERS.items():
        if re.search(pat, text, re.I):
            return p
    return "stripe"


def _security(stack: dict, needs: dict, auth: bool, backend_on: bool, kind: str, contact: bool) -> list[str]:
    s = []
    if backend_on:
        s += ["Validate every request body and query on the server", "Restrictive CORS (explicit origins only)", "Safe error responses (no stack traces)",
              "Request timeouts and structured logging without secrets"]
    if auth:
        s += ["Enforce authorization on the backend for every protected route (never rely on the frontend)",
              "Hash passwords with a slow adaptive hash; never return password hashes"]
        if stack.get("auth") == "jwt":
            s.append("Short-lived access tokens with refresh rotation")
    if backend_on and (auth or contact):
        s.append("Rate limit sign-in and public form endpoints")
    if needs.get("payments"):
        s.append("Verify payment webhook signatures; never trust client-reported amounts")
    if needs.get("uploads"):
        s.append("Limit upload size and allowed types; never serve uploads as executable content")
    if needs.get("ai") != "none":
        s.append("Keep AI/LLM keys on the server only; cap prompt size and request time")
    if (stack.get("database") or "").startswith("firebase") or stack.get("database") == "firestore":
        s.append("Write Firebase security rules; the browser SDK is not a trust boundary")
    if backend_on:
        s.append("Parameterised queries / ORM only (no string-built queries)")
    s.append("Secrets only in environment variables; .env.example holds placeholders only")
    return s


def _tests(stack: dict, features: list[str], auth: bool, backend_on: bool, db_on: bool) -> dict:
    fe_t = stack.get("testing") or "none"
    t = {"frontend": fe_t if fe_t != "none" else "static checks + browser verification (built in)", "backend": C.BACKEND_TESTS.get(stack.get("backend") or "none", ""),
         "must_cover": ["Form validation and error states"]}
    if backend_on:
        t["must_cover"] += ["Every API route: success, validation error, unauthorised", "Frontend/backend contract (paths, methods, schemas)"]
    if auth:
        t["must_cover"] += ["Sign-in / sign-up", "Role-based access (user cannot reach admin routes)"]
    if db_on:
        t["must_cover"] += ["Database create / read / update / delete and constraints"]
    t["must_cover"] += [f"Critical flow: {f}" for f in features[:3]]
    return t


def _plan(stack: dict, pages: list[dict], ents: list[dict], api: list[dict], auth: bool, backend_on: bool, db_on: bool, needs: dict) -> list[dict]:
    st = lambda f: C.status(f, stack.get(f) or "none", stack)    # noqa: E731
    worst = lambda *fs: next((s for s in (st(f) for f in fs) if s != C.READY), C.READY)    # noqa: E731
    steps = [("spec", "spec", "Requirements, stack and architecture decisions", "done"),
             ("design", "frontend", "Design system and motion tokens", st("frontend")),
             ("pages", "frontend", f"Frontend: {len(pages)} page(s)", st("frontend"))]
    if db_on:
        steps.append(("data", "database", f"Data model: {len(ents)} entit{'y' if len(ents) == 1 else 'ies'}, migrations, indexes", worst("database", "orm")))
    if backend_on:
        steps.append(("api", "backend", f"Backend: {len(api)} route(s) with validation and error handling", st("backend")))
    if auth:
        steps.append(("auth", "backend", "Authentication and backend-enforced authorization", worst("auth", "backend")))
    ints = [f for f in ("ai", "cache", "storage") if (stack.get(f) or "none") != "none"]
    if ints or needs.get("payments") or needs.get("email"):
        steps.append(("integrations", "backend", "External services and optional infrastructure", worst(*ints) if ints else st("backend")))
    if backend_on:
        steps.append(("wiring", "frontend", "Generated API client and frontend/backend wiring", worst("frontend", "backend")))    # client.ts is generated (v2 phase 7)
    steps += [("tests", "tests", "Automated tests for the selected stack", st("backend") if backend_on else C.READY),    # every ready backend generator writes its own test suite
              ("verify", "tests", "Run checks, repair, report verified results", C.READY)]
    return [{"id": i, "area": a, "title": t, "status": s} for i, a, t, s in steps]


# ------------------------------------------------------------------ overrides
def validate_overrides(ov) -> dict:
    """Shape and size checks for user edits to the spec. Raises ValueError with a readable reason."""
    if not isinstance(ov, dict):
        raise ValueError("overrides must be an object")
    bad = set(ov) - {"pages", "features", "entities", "drop_entities"}
    if bad:
        raise ValueError(f"unknown override key(s): {', '.join(sorted(bad))}")
    out = {}
    if "pages" in ov:
        p = ov["pages"]
        if not isinstance(p, list) or not 1 <= len(p) <= 20:
            raise ValueError("pages must be a list of 1-20 items")
        seen, pages = set(), []
        for x in p:
            slug = str((x or {}).get("slug", "")) if isinstance(x, dict) else ""
            title = str(x.get("title", "")).strip()[:60] if isinstance(x, dict) else ""
            if not _SLUG.match(slug) or not title or slug in seen:
                raise ValueError(f"invalid or duplicate page '{slug}' (slug: lowercase letters, digits, dashes)")
            seen.add(slug)
            pages.append({"slug": slug, "title": title, "auth": bool(x.get("auth"))})
        out["pages"] = pages
    if "features" in ov:
        f = ov["features"]
        if not isinstance(f, list) or len(f) > 30 or not all(isinstance(i, str) and 2 <= len(i.strip()) <= 120 for i in f):
            raise ValueError("features must be a list of up to 30 strings (2-120 chars)")
        out["features"] = [i.strip() for i in f]
    if "entities" in ov:
        e = ov["entities"]
        if not isinstance(e, dict) or len(e) > 20:
            raise ValueError("entities must be an object with up to 20 entities")
        out["entities"] = {}
        for name, toks in e.items():
            if not _NAME.match(name) or not isinstance(toks, list) or not 1 <= len(toks) <= 25:
                raise ValueError(f"invalid entity '{name}' (PascalCase name, 1-25 field tokens)")
            for t in toks:
                parse_field(str(t))
            out["entities"][name] = [str(t) for t in toks]
    if "drop_entities" in ov:
        d = ov["drop_entities"]
        if not isinstance(d, list) or not all(isinstance(n, str) and _NAME.match(n) for n in d):
            raise ValueError("drop_entities must be a list of entity names")
        out["drop_entities"] = d
    return out


# ------------------------------------------------------------------ main
def _inputs_hash(brief: str, stack: dict, ov: dict) -> str:
    raw = json.dumps([SPEC_VERSION, brief, stack, ov], sort_keys=True)
    return hashlib.md5(raw.encode()).hexdigest()[:12]


def build(brief: str, stack: dict, overrides: dict | None = None) -> dict:
    ov = validate_overrides(overrides or {})
    text, style = split_style(brief)
    req = analyze(brief)
    kind, needs = req["kind"], req["needs"]
    backend_on = (stack.get("backend") or "none") != "none"
    db_on = (stack.get("database") or "none") != "none"
    auth = (stack.get("auth") or "none") != "none"
    roles = T.ROLES.get(kind, ["user", "admin"])
    contact = kind in ("portfolio", "site") and backend_on
    ents, variant = ([], "")
    if db_on or backend_on:
        ents, variant = _entities(kind, text, auth, needs, contact, roles)
        ents = _apply_entity_overrides(ents, ov, roles)
        probs = integrity(ents)
        if probs:
            raise ValueError("; ".join(probs[:4]))
    api = _api(ents, needs, kind, stack, auth, contact) if backend_on else []

    pages = [{"slug": s, "title": t, "auth": bool(a)} for s, t, a in T.PAGES.get(kind, T.PAGES["generic"])]
    if auth and stack.get("auth") in ("jwt", "session", "firebase-auth", "oauth2"):
        pages += [{"slug": s, "title": t, "auth": False} for s, t, _ in T.LOGIN_PAGES]
    if not auth:
        pages = [{**p, "auth": False} for p in pages]
    pages = ov.get("pages", pages)

    features = list(T.FEATURES.get(kind, T.FEATURES["generic"]))
    if kind in ("portfolio", "site") and not backend_on:
        features = [f for f in features if "form" not in f.lower()] + ["Contact through a mailto link (no backend selected)"]
    extra = {"auth": "Sign-in, sign-up and role-based access", "realtime": "Live updates over WebSocket", "uploads": "File uploads",
             "email": "Transactional email", "payments": f"Online payments ({provider(text)})"}
    for k, label in extra.items():
        if needs.get(k) and (k != "auth" or auth) and (backend_on or k == "auth") and label not in features:
            features.append(label)
    if needs["ai"] != "none" and (stack.get("ai") or "none") != "none":
        features.append("AI assistant" if needs["ai"] == "llm" else "Machine-learning feature")
    features = ov.get("features", features)

    gaps, assumptions, questions = [], [], []
    if not backend_on and not db_on:
        miss = [k for k in ("auth", "db", "payments", "email", "uploads", "realtime") if needs.get(k)] + (["ai"] if needs["ai"] != "none" else [])
        if miss:
            gaps.append(f"The brief implies {', '.join(miss)} but the selected stack has no backend or database; those parts will not be functional.")
    if needs["ai"] != "none" and (stack.get("ai") or "none") == "none":
        gaps.append("The brief mentions an AI feature but no AI integration mode is selected.")
    if needs.get("payments") and backend_on:
        if not any(re.search(p, text, re.I) for p in PROVIDERS.values()):
            assumptions.append(f"Payment provider not specified explicitly; {provider(text).title()} assumed (name another provider in the brief to change it).")
    if kind == "management" and variant == "generic":
        assumptions.append("Domain not specified; a generic Department/Record data model is used. Edit the entities to match your domain.")
    assumptions.append("Text and imagery are placeholders derived from the brief; replace them with real content.")
    if kind == "generic" and len(text.split()) < 8:
        questions.append({"id": "purpose", "question": "What is the website for and who is it for?", "why": "The brief is too short to choose pages and features reliably."})
    neg_backend = re.search(r"(?:no|without|skip)\s+(?:a\s+|any\s+)?(?:backend|server)|front-?end only", text, re.I)
    if neg_backend and re.search(r"log ?in|sign ?up|database|payments?|checkout", text, re.I):
        questions.append({"id": "backend-conflict", "question": "The brief asks for 'no backend' but also login/data/payments. Should a backend be added, or should those features be dropped?",
                          "why": "Accounts, stored data and payments cannot work safely without a server (or a managed service such as Firebase)."})

    purpose = f"{T.KIND_LABEL.get(kind, 'Website')}: " + re.sub(r"\s+", " ", text).strip()[:160]
    spec = {"version": SPEC_VERSION, "kind": kind, "complexity": req["complexity"], "purpose": purpose,
            "target_users": T.USERS.get(kind, T.USERS["generic"]), "style": style, "variant": variant,
            "stack": {k: stack.get(k) for k in C.FIELDS if stack.get(k)}, "pages": pages, "features": features,
            "roles": roles if auth else [], "auth": {"enabled": auth, "method": stack.get("auth") or "none"},
            "data": {"enabled": db_on, "database": stack.get("database") or "none", "access": "backend" if backend_on else ("security-rules" if db_on else "none"),
                     "entities": ents},
            "api": {"base": "/api" if backend_on else "", "routes": api},
            "integrations": [k for k in ("payments", "email", "uploads", "realtime") if needs.get(k) and backend_on] + ([f"ai:{stack['ai']}"] if (stack.get("ai") or "none") != "none" else [])
                            + ([f"cache:{stack['cache']}"] if (stack.get("cache") or "none") != "none" else []) + ([f"storage:{stack['storage']}"] if (stack.get("storage") or "none") != "none" else []),
            "env": _env(stack, needs, text, backend_on), "security": _security(stack, needs, auth, backend_on, kind, contact),
            "testing": _tests(stack, features, auth, backend_on, db_on), "deployment": stack.get("deploy") or "local",
            "plan": _plan(stack, pages, ents, api, auth, backend_on, db_on, needs),
            "assumptions": assumptions, "gaps": gaps, "open_questions": questions, "overrides": ov}
    spec["api"]["digest"] = hashlib.md5(json.dumps(api, sort_keys=True).encode()).hexdigest()[:10]
    spec["hash"] = _inputs_hash(brief, stack, ov)
    return spec


def digest(spec: dict, max_chars: int = 320) -> str:
    """One short line for LLM context (instead of the whole spec)."""
    ents = [e["name"] for e in spec["data"]["entities"]]
    parts = [f"kind={spec['kind']}", "pages=" + ",".join(p["title"] for p in spec["pages"][:8]), "features=" + "; ".join(spec["features"][:5])]
    if ents:
        parts.append("entities=" + ",".join(ents[:8]))
    return " | ".join(parts)[:max_chars]


# ------------------------------------------------------------------ state integration
def stack_of(state) -> dict:
    """The stack to build the spec for: the resolved stack, or the legacy html/react choice for older projects."""
    cfg = (getattr(state, "stack_config", None) or {}).get("stack")
    if cfg:
        return dict(cfg)
    react = state.stack == "react"
    return {"frontend": "react" if react else "html", "frontend_lang": "ts" if react else "js", "backend": "none", "database": "none",
            "auth": "none", "cache": "none", "storage": "none", "ai": "none", "testing": "none", "deploy": "local"}


def ensure(state, overrides: dict | None = None, force: bool = False) -> tuple[dict, bool]:
    """Return (spec, changed). Rebuilds only when brief, stack or overrides changed (hash); persists .agent/spec.json."""
    from backend.tools.project_files import ProjectFiles
    pf = ProjectFiles(state.project_id)
    old = None
    try:
        old = json.loads(pf.read(".agent/spec.json"))
    except (OSError, ValueError):
        pass
    ov = overrides if overrides is not None else ((old or {}).get("overrides") or {})
    fell_back = False
    try:
        spec = build(state.brief, stack_of(state), ov)
    except ValueError:
        if overrides is not None:
            raise
        spec, fell_back = build(state.brief, stack_of(state), {}), True     # stale/invalid stored overrides never block generation
    stale_plan = bool(old) and old.get("plan") != spec.get("plan")      # generator statuses changed since the spec was stored (hash covers inputs only)
    if old and old.get("hash") == spec["hash"] and not force and not fell_back and not stale_plan:
        state.spec_digest = digest(old)
        return old, False
    pf.write(".agent/spec.json", json.dumps(spec, indent=1))
    state.spec_digest = digest(spec)
    return spec, True


def load(pid: str) -> dict | None:
    from backend.tools.project_files import ProjectFiles
    try:
        return json.loads(ProjectFiles(pid).read(".agent/spec.json"))
    except (OSError, ValueError):
        return None

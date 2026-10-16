"""Spec -> framework-neutral backend model. Shared by every generator (Express now, FastAPI/Flask next)."""
import re

NOT_GENERATED = {"/api/payments/intent": "payments", "/api/payments/webhook": "payments",
                 "/api/uploads": "file uploads", "/ws": "WebSocket live updates"}
AUTH_FIELDS = {"email", "name", "password_hash", "role", "created_at"}
SQL = {"sqlite", "postgresql", "mysql", "mssql"}
SEED_ROWS = 3


def _ops(routes: list[dict], entity: str, path: str) -> list[str]:
    base, ops = f"/api/{path}", []
    for r in routes:
        if r.get("entity") != entity:
            continue
        key = (r["method"], r["path"])
        ops += [o for o, k in (("list", ("GET", base)), ("get", ("GET", base + "/{id}")), ("create", ("POST", base)),
                               ("update", ("PUT", base + "/{id}")), ("delete", ("DELETE", base + "/{id}"))) if key == k]
    return ops


def build(spec: dict, stack: dict) -> dict:
    data, api, auth = spec["data"], spec["api"], spec["auth"]
    db = stack.get("database") if data.get("enabled") else None
    db = None if db in (None, "", "none") else db
    routes = api["routes"]
    roles = spec.get("roles") or ["admin", "user"]
    ents, warns = [], []
    if db:
        for e in data["entities"]:
            fields = [dict(f) for f in e["fields"]]
            owner = next((f["name"] for f in fields if f["type"] == "ref" and f["ref"] == "User"), None)
            is_user = e["name"] == "User"
            if is_user and auth.get("enabled"):
                extra = [f["name"] for f in fields if f["name"] not in AUTH_FIELDS and f["required"]]
                if extra:
                    warns.append(f"User has extra required field(s) {extra}; sign-up only collects email, name and password, so they are made optional.")
                    for f in fields:
                        if f["name"] in extra:
                            f["required"] = False
            read, write = e["read"], e["write"]
            if "owner" in (read, write) and not owner and not is_user:
                warns.append(f"{e['name']} is owner-scoped but has no reference to User; access falls back to 'user'.")
                read, write = ("user" if read == "owner" else read), ("user" if write == "owner" else write)
            ents.append({"name": e["name"], "table": e["path"].replace("-", "_"), "path": e["path"], "fields": fields, "read": read, "write": write,
                         "searchable": e.get("searchable", []), "sensitive": e.get("sensitive", []), "ownerField": owner if not is_user else None,
                         "isUser": is_user, "internal": False, "ops": _ops(routes, e["name"], e["path"])})
        if auth.get("enabled") and ("POST", "/api/auth/refresh") in {(r["method"], r["path"]) for r in routes}:
            ents.append({"name": "RefreshToken", "table": "refresh_tokens", "path": "refresh-tokens", "internal": True, "isUser": False, "ops": [],
                         "read": "admin", "write": "admin", "searchable": [], "sensitive": [], "ownerField": None,
                         "fields": [{"name": "user_id", "type": "ref", "ref": "User", "required": True, "unique": False},
                                    {"name": "token_hash", "type": "string", "required": True, "unique": True},
                                    {"name": "expires_at", "type": "datetime", "required": True, "unique": False}]})
    ents = _sorted(ents)
    if db == "mssql":     # SQL Server rejects SET NULL where several paths could reach a table ("cycles or multiple cascade paths"): use NO ACTION, a parent delete is then a 409
        for e in ents:
            for f in e["fields"]:
                if f.get("onDelete") == "SET NULL":
                    f["onDelete"] = "NO ACTION"
    paths = {(r["method"], r["path"]) for r in routes}
    skipped = sorted({NOT_GENERATED[r["path"]] for r in routes if r["path"] in NOT_GENERATED})
    raw_names = {e["name"] for e in data.get("entities", [])}
    checkout_requested = ("POST", "/api/checkout") in paths
    checkout = bool(checkout_requested and stack.get("backend") in ("express", "fastapi", "flask", "nestjs", "django", "spring") and db in SQL and auth.get("enabled") and
                    {"User", "Product", "Order", "OrderItem"}.issubset(raw_names))
    if checkout_requested and not checkout:
        skipped.append("checkout")
    be = stack.get("backend")
    express = be == "express"
    pyweb = be in ("fastapi", "flask", "django", "nestjs", "spring")
    has = lambda p: any(r["path"] == p for r in routes)
    order = next((e for e in data["entities"] if e["name"] == "Order"), None) if db in SQL else None
    order_ok = bool(order and {"user_id", "status", "total"} <= {f["name"] for f in order["fields"]})
    env_names = {v["name"] for v in spec.get("env", [])}
    pprov = "razorpay" if "RAZORPAY_KEY_ID" in env_names else "paypal" if "PAYPAL_CLIENT_ID" in env_names else "stripe" if "STRIPE_SECRET_KEY" in env_names else ""
    integ = {"cache": bool((express or pyweb) and db and stack.get("cache") == "redis"),
             "uploads": bool((express or pyweb) and has("/api/uploads") and (stack.get("storage") == "local" or ((express or pyweb) and stack.get("storage") in ("s3", "firebase-storage")))),
             "payments": bool((express or be in ("fastapi", "flask", "nestjs", "django", "spring")) and checkout and order_ok and has("/api/payments/intent") and bool(pprov)),
             "ws": bool((express or be in ("fastapi", "nestjs", "spring")) and has("/ws"))}
    gen_paths = {"/api/payments/intent": integ["payments"], "/api/payments/webhook": integ["payments"], "/api/uploads": integ["uploads"], "/ws": integ["ws"]}
    done = {"payments": integ["payments"], "file uploads": integ["uploads"], "WebSocket live updates": integ["ws"]}
    skipped = [s for s in skipped if not done.get(s)]
    if any(r.get("method") == "POST" and r["path"].startswith("/api/ai") for r in routes):
        skipped.append("AI endpoint")
    admin = "admin" if "admin" in roles else roles[0]
    others = [r for r in roles if r != admin]
    default = "user" if "user" in others else others[0] if others else "user"      # sign-up must never produce the administrator role
    if not others:
        warns.append(f"The spec has only the '{admin}' role; sign-up creates role 'user' instead.")
    if admin != "admin":
        warns.append(f"No 'admin' role in the spec; '{admin}' is treated as the administrator role.")
    fb_auth = bool(express and db and auth.get("enabled") and stack.get("auth") == "firebase-auth")
    out = {"db": db, "sql": db in SQL, "seed": seed_plan(ents, bool(auth.get("enabled") and db)) if db else [], "checkout": checkout, "integrations": integ, "paymentProvider": pprov if integ["payments"] else "", "storage": stack.get("storage") if integ["uploads"] else "", "adminRole": admin, "auth": bool(auth.get("enabled") and db), "roles": roles,
            "defaultRole": default, "entities": ents, "refresh": ("POST", "/api/auth/refresh") in paths,
            "rateLimited": sorted(r["path"] for r in routes if r.get("rate_limited")), "warnings": warns, "not_generated": skipped,
            "manifest": sorted(f"{r['method']} {r['path']}" for r in routes if (r["path"] not in NOT_GENERATED or gen_paths.get(r["path"])) and r["method"] != "WS"
                               and not r["path"].startswith("/api/ai")
                               and not (r["path"] == "/api/checkout" and not checkout))}
    out["firebaseAuth"] = fb_auth
    if fb_auth:
        out["manifest"] = sorted(out["manifest"] + ["POST /api/auth/firebase"])
    return out


def _sorted(ents: list[dict]) -> list[dict]:
    """Parents first (migrations need it). A reference cycle is allowed: the back-edge simply gets no FK constraint."""
    by, out, seen = {e["name"]: e for e in ents}, [], set()

    def visit(e):
        if e["name"] in seen:
            return
        seen.add(e["name"])
        for f in e["fields"]:
            if f["type"] == "ref" and f["ref"] in by and f["ref"] != e["name"]:
                visit(by[f["ref"]])
        out.append(e)
    for e in ents:
        visit(e)
    pos = {e["name"]: i for i, e in enumerate(out)}
    for e in out:
        for f in e["fields"]:
            if f["type"] == "ref":
                f["fk"] = f["ref"] in pos and pos[f["ref"]] < pos[e["name"]] or f["ref"] == e["name"]
                f["onDelete"] = "CASCADE" if e["internal"] else "RESTRICT" if f["required"] else "SET NULL"
            # one rule for every generator: index the columns that are looked up or filtered by (unique columns already have an index)
            f["index"] = bool(not f["unique"] and f["type"] not in ("text", "url") and (f["type"] in ("ref", "enum", "bool") or f["name"] in e["searchable"]))
    return out


_WORDS = ["alpha", "bravo", "charlie", "delta", "echo"]


def _sample(e: dict, f: dict, i: int):
    """Deterministic, obviously-fake value for one field (row i, 0-based). Never random, so tests and re-runs agree."""
    t, n = f["type"], f["name"]
    if t == "enum":
        vals = f.get("values") or f.get("enum") or [""]
        return vals[i % len(vals)]
    if t == "email":
        return f"{e['table']}{i + 1}@example.com"
    if t == "url":
        return f"https://example.com/{e['path']}/{i + 1}"
    if t == "int":
        return i + 1
    if t == "float":
        return round(9.99 + i * 10, 2)
    if t == "bool":
        return i % 2 == 0
    if t == "datetime":
        return f"2026-01-{i + 1:02d}T09:00:00Z"
    word = _WORDS[i % len(_WORDS)]
    return f"{word} {n.replace('_', ' ')} {i + 1}" if t == "string" else f"Sample {e['name']} {i + 1}: {word} text for {n.replace('_', ' ')}."


def seed_plan(ents: list[dict], auth: bool) -> list[dict]:
    """Sample rows per entity, parents first. A reference is {"$ref": [Entity, rowIndex]} so each runtime resolves it to the id it just created.
    Entities that must point at User are skipped unless sign-in exists (the seed script links them to the first admin)."""
    names, out = {e["name"] for e in ents if not e["internal"] and not e["isUser"]}, []
    for e in ents:
        if e["internal"] or e["isUser"]:
            continue
        rows, skip = [], False
        for i in range(SEED_ROWS):
            row = {}
            for f in e["fields"]:
                if f["type"] == "ref":
                    if f["ref"] == "User":
                        if auth:
                            row[f["name"]] = {"$ref": ["User", 0]}
                        elif f["required"]:
                            skip = True
                    elif f["ref"] in names and f["ref"] != e["name"]:
                        row[f["name"]] = {"$ref": [f["ref"], i % SEED_ROWS]}
                    elif f["required"]:
                        skip = True
                elif f["required"] or f["unique"] or i == 0:
                    row[f["name"]] = _sample(e, f, i)
            rows.append(row)
        if not skip:
            out.append({"entity": e["name"], "rows": rows})
        else:
            names.discard(e["name"])
    return out


def env_lines(spec: dict, model: dict, extra: dict[str, str], cmds: dict | None = None, more: dict | None = None) -> list[str]:
    """.env.example lines for the SERVER only (public values belong to the frontend). Placeholders, never real secrets."""
    cmds = {"seed": "npm run seed:admin", "migrate": "npm run migrate", **(cmds or {})}
    out, seen = [], set()
    for v in spec["env"]:
        if v["scope"] != "server" or v["name"] in seen:
            continue
        if v["name"] in ("DATABASE_URL",) and not model["db"]:
            continue
        seen.add(v["name"])
        out.append(f"# {v['purpose']}" + (" (SECRET)" if v["secret"] else ""))
        out.append(f"{v['name']}={extra.get(v['name'], v['placeholder'])}")
    for k, (d, ph) in {"ADMIN_EMAIL": ("First admin account (used only by `"+cmds["seed"]+"`)", "admin@example.com"),
                       "ADMIN_PASSWORD": ("First admin password, 8-72 chars (used only by `"+cmds["seed"]+"`)", "<choose-a-strong-password>"),
                       "AUTO_MIGRATE": ("Run migrations on start (true for development; run `" + cmds["migrate"] + "` yourself in production)", "true"),
                       "TRUST_PROXY": ("Set to 1 when behind a reverse proxy so rate limiting sees real client IPs", "0"),
                       **(more or {})}.items():
        if k in seen or (k.startswith("ADMIN") and not model["auth"]) or (k == "AUTO_MIGRATE" and not model["sql"]):
            continue
        out += [f"# {d}", f"{k}={ph}"]
    return out


def slug(name: str) -> str:
    return re.sub(r"[^a-z0-9-]", "-", name.lower()).strip("-") or "app"


PAY_CUR = {"stripe": ("STRIPE_CURRENCY", "usd"), "razorpay": ("RAZORPAY_CURRENCY", "inr"), "paypal": ("PAYPAL_CURRENCY", "usd")}
PAY_README = {
    "stripe": "Payments (Stripe): `POST /api/payments/intent {orderId}` returns a `clientSecret` (amount read from the stored order); `POST /api/payments/webhook` verifies the signature and marks a matching pending order `paid`. Point your Stripe webhook at it for `payment_intent.succeeded`.",
    "razorpay": "Payments (Razorpay): `POST /api/payments/intent {orderId}` creates a Razorpay order (amount in paise from the stored order) and returns `razorpayOrderId` + the public `keyId` for the checkout widget; `POST /api/payments/webhook` verifies `X-Razorpay-Signature` over the raw body and marks a matching pending order `paid`. Subscribe your Razorpay webhook to `payment.captured`.",
    "paypal": "Payments (PayPal): `POST /api/payments/intent {orderId}` creates a PayPal order (amount from the stored order) and returns `approveUrl` for the buyer; `POST /api/payments/webhook` has PayPal verify the signature (`PAYPAL_WEBHOOK_ID`), captures an approved order on the server (`CHECKOUT.ORDER.APPROVED`) and marks a matching pending order `paid` (`PAYMENT.CAPTURE.COMPLETED`). Use `PAYPAL_ENV=live` in production."}


FB_STORAGE_ENV = {"FIREBASE_PROJECT_ID": ("Firebase project id", "your-project-id"),
                  "FIREBASE_SERVICE_ACCOUNT_PATH": ("Path to the service-account JSON (SECRET, never commit it; empty = Google application default credentials)", "./secrets/service-account.json"),
                  "FIREBASE_STORAGE_BUCKET": ("Firebase Storage bucket name for uploads, e.g. your-project-id.appspot.com", "your-project-id.appspot.com")}
UPLOAD_README = {"local": "Files are stored in `UPLOAD_DIR` (use a persistent volume in production).",
                 "s3": "Files go to a PRIVATE S3-compatible bucket (`S3_*`; AWS, MinIO, R2, Spaces) signed with SigV4 and are served only through the API. For AWS use the regional endpoint, e.g. `https://s3.eu-west-1.amazonaws.com`; the bucket needs no public access and no CORS.",
                 "firebase-storage": "Files go to a private Firebase Storage bucket (`FIREBASE_STORAGE_BUCKET`) through the Admin SDK and are served only through the API. Keep the bucket's security rules closed to clients."}


def integ_env(m: dict) -> dict:
    """Extra .env.example entries for the enabled integrations (name -> (description, placeholder))."""
    I = m["integrations"]
    return {**({"CACHE_TTL_SECONDS": ("Seconds a cached read stays valid (any write invalidates all cached reads)", "30")} if I["cache"] else {}),
            **({"UPLOAD_MAX_BYTES": ("Maximum upload size in bytes", "5242880")} if I["uploads"] else {}),
            **(FB_STORAGE_ENV if I["uploads"] and m.get("storage") == "firebase-storage" else {}),
            **({PAY_CUR[m.get("paymentProvider") or "stripe"][0]: ("Three-letter ISO currency for payments", PAY_CUR[m.get("paymentProvider") or "stripe"][1])} if I["payments"] else {}),
            **({"WS_MAX_CLIENTS": ("Maximum simultaneous WebSocket clients", "500")} if I["ws"] else {})}


def integ_readme(m: dict) -> str:
    """README section for the enabled integrations ('' when none)."""
    I = m["integrations"]
    rows = (("checkout", "Checkout: `POST /api/checkout {items:[{productId, quantity}]}` creates a pending order in one transaction; prices and stock are read from the database (never from the client), stock is decremented with a conditional update so concurrent orders cannot oversell."),
            ("payments", PAY_README[m.get("paymentProvider") or "stripe"]),
            ("cache", "Cache: GET reads of CRUD resources are cached per caller (`X-Cache: HIT|MISS`, `CACHE_TTL_SECONDS`); any successful write invalidates all cached reads. Redis when `REDIS_URL` is reachable, otherwise in-memory."),
            ("uploads", "Uploads: `POST /api/uploads` with the raw file as the body (PNG/JPEG/GIF/WebP/PDF, type checked from file bytes, `UPLOAD_MAX_BYTES`); `GET /api/uploads/{name}`. " + UPLOAD_README[m.get("storage") or "local"]),
            ("ws", "WebSocket `/ws`: send `{\"type\":\"auth\",\"token\":\"<access token>\"}` first; the server then pushes `{type:\"change\", entity, op}` after writes. Refetch over the REST API."))
    body = "".join(f"- {t}\n" for k, t in rows if (m.get("checkout") if k == "checkout" else I[k]))
    return "## Integrations\n" + body + "\n" if body else ""

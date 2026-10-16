"""Express (Node.js, JavaScript) generator. Static JS comes from templates/express; only data-driven files are built here."""
import json
from pathlib import Path

from backend.gen import model as M
from backend.gen import openapi

TPL = Path(__file__).parent / "templates" / "express"
DRIVER = {"sqlite": {"better-sqlite3": "^11.3.0"}, "postgresql": {"pg": "^8.12.0"}, "mysql": {"mysql2": "^3.11.0"}, "mssql": {"tedious": "^18.6.1"}}
COMMON = {"express": "^4.19.2", "cors": "^2.8.5", "helmet": "^7.1.0", "express-rate-limit": "^7.4.0", "dotenv": "^16.4.5"}


def _col(f: dict, db: str, table_of: dict, internal: bool) -> str:
    n, t = json.dumps(f["name"]), f["type"]
    if t == "ref":
        c = f"t.integer({n}).unsigned()"
    elif t in ("string", "enum"):
        c = f"t.string({n}, {64 if t == 'enum' else 255})"
    elif t == "email":
        c = f"t.string({n}, 255)"
    elif t == "url":
        c = f"t.string({n}, 2048)"
    elif t == "text":
        c = f"t.text({n}, 'mediumtext')"
    elif t == "int":
        c = f"t.integer({n})"
    elif t == "float":
        c = f"t.double({n})"
    elif t == "bool":
        c = f"t.boolean({n})"
    else:  # datetime
        c = f"t.timestamp({n}, {{ useTz: true }})" if db == "postgresql" else f"t.datetime({n})"
    c += ".notNullable()" if f["required"] else ".nullable()"
    if f["unique"]:                      # knex adds `WHERE col IS NOT NULL` on SQL Server, so optional unique columns may hold several NULLs there too
        c += ".unique()"
    if t == "ref" and f.get("fk"):
        c += f".references('id').inTable({json.dumps(table_of[f['ref']])}).onDelete({json.dumps(f['onDelete'])})"
    if f.get("index"):
        c += ".index()"
    return f"    {c};"


def migration(m: dict) -> str:
    table_of = {e["name"]: e["table"] for e in m["entities"]}
    ups = []
    for e in m["entities"]:
        cols = "\n".join(_col(f, m["db"], table_of, e["internal"]) for f in e["fields"])
        ups.append(f"  await knex.schema.createTable({json.dumps(e['table'])}, (t) => {{\n    t.increments('id');\n{cols}\n  }});")
    downs = [f"  await knex.schema.dropTableIfExists({json.dumps(e['table'])});" for e in reversed(m["entities"])]
    return ("// Generated from the app spec. Do not edit by hand; regenerate instead.\n"
            "exports.up = async (knex) => {\n" + "\n".join(ups) + "\n};\n\nexports.down = async (knex) => {\n" + "\n".join(downs) + "\n};\n")


def schema_js(m: dict) -> str:
    ents = {e["name"]: e for e in m["entities"]}
    body = {"db": m["db"], "seed": m["seed"], "auth": m["auth"], "refresh": m["auth"] and m["refresh"], "checkout": bool(m.get("checkout")), "integrations": m["integrations"], "firebaseAuth": bool(m.get("firebaseAuth")), "storage": m.get("storage") or "", "roles": m["roles"], "adminRole": m["adminRole"],
            "defaultRole": m["defaultRole"], "entities": ents}
    return "// Generated from the app spec (entities, fields, access rules). Single source of truth for validation, routes and migrations.\n" \
           "module.exports = " + json.dumps(body, indent=2) + ";\n"


def _fb(m: dict) -> bool:
    """Firebase Admin SDK is needed for Firebase Storage uploads and/or Firebase ID-token sign-in."""
    return bool(m.get("firebaseAuth") or (m["integrations"]["uploads"] and m.get("storage") == "firebase-storage"))


def package_json(m: dict, name: str) -> str:
    deps = dict(COMMON)
    if m["db"]:
        deps["jsonwebtoken"] = "^9.0.2"  # middleware/auth.js is loaded by every CRUD route, also in apps without sign-in
    if m["auth"]:
        deps["bcryptjs"] = "^2.4.3"
    if m["sql"]:
        deps.update({"knex": "^3.1.0", **DRIVER[m["db"]]})
    elif m["db"] == "mongodb":
        deps["mongoose"] = "^8.6.0"
    if m["integrations"]["cache"]:
        deps["redis"] = "^4.7.0"
    if m["integrations"]["ws"]:
        deps["ws"] = "^8.18.0"
    if _fb(m):
        deps["firebase-admin"] = "^12.6.0"
    scripts = {"start": "node src/server.js", "dev": "node --watch src/server.js", "test": "node --test"}
    if m["db"]:
        scripts["migrate"] = "node scripts/migrate.js"
    if m["db"]:
        scripts["seed:sample"] = "node scripts/seed-sample.js"
    if m["auth"]:
        scripts["seed:admin"] = "node scripts/seed-admin.js"
    pkg = {"name": f"{name}-api", "version": "1.0.0", "private": True, "description": "Generated Express API", "main": "src/server.js",
           "engines": {"node": ">=18.18"}, "scripts": scripts, "dependencies": dict(sorted(deps.items()))}
    return json.dumps(pkg, indent=2) + "\n"


UPLOAD_LOCAL = "Uploads: `POST /api/uploads` with the raw file as the body (PNG/JPEG/GIF/WebP/PDF, type checked from file bytes, `UPLOAD_MAX_BYTES`); `GET /api/uploads/{name}`. Files are stored in `UPLOAD_DIR` (use a persistent volume in production)."
UPLOAD_FB = ("Uploads: `POST /api/uploads` with the raw file as the body (PNG/JPEG/GIF/WebP/PDF, type checked from file bytes, `UPLOAD_MAX_BYTES`); `GET /api/uploads/{name}`. "
             "Files go to a private Firebase Storage bucket (`FIREBASE_STORAGE_BUCKET`) through the Admin SDK and are served only through the API. Keep the bucket's security rules closed to clients.")
FB_AUTH = ("Firebase sign-in: `POST /api/auth/firebase {idToken}` verifies a Firebase ID token with the Admin SDK (signature, expiry, project). Only tokens with a verified email are accepted; "
           "a matching local user is signed in (same email = same account), otherwise one is created with the default role. The role never comes from the token. Returns the same token pair as `/api/auth/login`.")
UPLOAD_S3 = ("Uploads: `POST /api/uploads` with the raw file as the body (PNG/JPEG/GIF/WebP/PDF, type checked from file bytes, `UPLOAD_MAX_BYTES`); `GET /api/uploads/{name}`. "
             "Files go to a PRIVATE S3-compatible bucket (`S3_*`; AWS, MinIO, R2, Spaces) signed with SigV4 and are served only through the API. "
             "For AWS use the regional endpoint, e.g. `https://s3.eu-west-1.amazonaws.com`; the bucket needs no public access and no CORS.")


def readme(m: dict, spec: dict) -> str:
    db = {"sqlite": "SQLite (file)", "postgresql": "PostgreSQL", "mysql": "MySQL", "mssql": "SQL Server", "mongodb": "MongoDB", None: "none"}[m["db"]]
    steps = ["cd backend", "npm install", "cp .env.example .env   # then edit the values"]
    if m["auth"]:
        steps.append("npm run seed:admin   # creates the first admin from ADMIN_EMAIL / ADMIN_PASSWORD")
    if m["sql"]:
        steps.append("npm run migrate      # optional in development when AUTO_MIGRATE=true")
    steps += ["npm run dev", "npm test"]
    routes = "\n".join(f"- `{r}`" for r in m["manifest"])
    notes = "\n".join(f"- {n}" for n in m["warnings"] + [f"Not generated yet: {x}." for x in m["not_generated"]]) or "- none"
    auth = ("- Sign-up always creates role `%s`; admins come from `npm run seed:admin`.\n- Access token (HS256, short lived) + single-use rotating refresh token (stored hashed).\n"
            "- Responses: `{user, accessToken, refreshToken, tokenType, expiresIn}`." % m["defaultRole"]) if m["auth"] else "- No authentication in this app."
    I = m["integrations"]
    integ = "".join(f"- {t}\n" for k, t in (
        ("cache", "Cache: GET reads of CRUD resources are cached per caller (`X-Cache: HIT|MISS`, `CACHE_TTL_SECONDS`); any successful write invalidates all cached reads. Redis when `REDIS_URL` is reachable, otherwise in-memory."),
        ("fbauth", FB_AUTH),
        ("uploads", UPLOAD_FB if m.get("storage") == "firebase-storage" else UPLOAD_S3 if m.get("storage") == "s3" else UPLOAD_LOCAL),
        ("payments", M.PAY_README[m.get("paymentProvider") or "stripe"]),
        ("ws", "WebSocket `/ws`: send `{\"type\":\"auth\",\"token\":\"<access token>\"}` first; the server then pushes `{type:\"change\", entity, op}` after writes. Refetch over the REST API."))
        if (m.get("firebaseAuth") if k == "fbauth" else I[k]))
    if integ:
        integ = "## Integrations\n" + integ + "\n"
    return f"""# {spec['purpose'][:80]} - API

Express + {db}. Generated from the app spec; routes, validation and tests follow `src/schema.js`.

## Run
```bash
{chr(10).join(steps)}
```
Health check: `GET /api/health`.{"  Tests for PostgreSQL / MySQL / MongoDB need `TEST_DATABASE_URL` pointing at a disposable database." if m["db"] and m["db"] != "sqlite" else ""}

## Routes
{routes}

Lists accept `?page`, `?limit` (max 100), `?q` and exact filters on reference / enum / boolean fields, and return `{{data, page, limit, total}}`.
Errors are always `{{error: {{code, message, details?}}}}`.

## Security
{auth}
- Authorization is enforced on the server for every route (public / user / owner / admin). Other users' records return 404.
- Helmet, explicit CORS origins (`CORS_ORIGINS`), 100 kB body limit, rate limits on auth and public forms, request timeout, no stack traces in responses.
- Unknown fields are rejected; every value is type-checked; queries are parameterised.
- Secrets live in `.env` only (never commit it). Put the API behind HTTPS in production and set `TRUST_PROXY` correctly.

{integ}## Notes
{notes}
"""


def _skip(rel: str, m: dict) -> bool:
    """Which static template files this app does not need (no database -> no db layer, CRUD, validation, migrations)."""
    if rel in ("src/db/mongo.js",):
        return m["db"] != "mongodb"
    if rel == "src/db/sql.js":
        return not m["sql"]
    if rel == "src/db/index.js" or rel.startswith(("src/routes/crud", "src/lib/validate", "scripts/migrate")):
        return not m["db"]
    if rel == "scripts/seed-sample.js":
        return not m["db"]
    if rel in ("src/routes/auth.js", "scripts/seed-admin.js"):
        return not m["auth"]
    I = m["integrations"]
    if rel in ("src/lib/cache.js",):
        return not (I["cache"] or I["ws"])        # middleware/live.js imports it
    if rel in ("src/middleware/live.js", "src/lib/events.js"):
        return not (I["cache"] or I["ws"] or I["payments"])
    if rel == "src/routes/uploads.js":
        return not I["uploads"]
    prov = m.get("paymentProvider") or "stripe"
    if rel == "src/routes/uploads_s3.js":
        return True                                          # copied over uploads.js by generate() for storage=s3
    if rel == "src/lib/s3.js":
        return not (I["uploads"] and m.get("storage") == "s3")
    if rel == "src/lib/firebase.js":
        return not _fb(m)
    if rel == "src/routes/payments.js":
        return not I["payments"]
    if rel in ("src/routes/payments_razorpay.js", "src/routes/payments_paypal.js"):
        return True                                          # copied over payments.js by generate() when that provider is chosen
    if rel == "src/lib/pay.js":
        return not (I["payments"] and prov != "stripe")
    if rel == "src/ws.js":
        return not I["ws"]
    if rel == "src/routes/checkout.js":
        return not m.get("checkout", False)
    return False


def generate(spec: dict, stack: dict, m: dict) -> dict[str, str]:
    files = {}
    for p in sorted(TPL.rglob("*.js")):
        rel = p.relative_to(TPL).as_posix()
        if _skip(rel, m):
            continue
        files[f"backend/{rel}"] = p.read_text(encoding="utf-8")
    prov = m.get("paymentProvider") or "stripe"
    if m["integrations"]["payments"] and prov != "stripe":
        files["backend/src/routes/payments.js"] = (TPL / "src" / "routes" / f"payments_{prov}.js").read_text(encoding="utf-8")
    if m["integrations"]["uploads"] and m.get("storage") == "s3":
        files["backend/src/routes/uploads.js"] = (TPL / "src" / "routes" / "uploads_s3.js").read_text(encoding="utf-8")
    if m["integrations"]["uploads"] and m.get("storage") == "firebase-storage":
        src = (TPL / "src" / "routes" / "uploads_s3.js").read_text(encoding="utf-8")      # same checks as S3 uploads; only the store differs
        files["backend/src/routes/uploads.js"] = (src.replace("const s3 = require('../lib/s3');", "const store = require('../lib/firebase').storage;")
                                                  .replace("s3.put(", "store.put(").replace("s3.get(", "store.get(").replace("private S3 bucket", "private Firebase Storage bucket"))
    files["backend/src/schema.js"] = schema_js(m)
    files["backend/openapi.json"] = openapi.dumps(m, spec)
    if m["sql"]:
        files["backend/migrations/001_init.js"] = migration(m)
    files["backend/package.json"] = package_json(m, M.slug(spec.get("purpose", "app").split(".")[0])[:40])
    I = m["integrations"]
    more = {**({"CACHE_TTL_SECONDS": ("Seconds a cached read stays valid (any write invalidates all cached reads)", "30")} if I["cache"] else {}),
            **({"FIREBASE_PROJECT_ID": ("Firebase project id", "your-project-id"),
                "FIREBASE_SERVICE_ACCOUNT_PATH": ("Path to the service-account JSON (SECRET, never commit it; empty = Google application default credentials)", "./secrets/service-account.json")} if _fb(m) else {}),
            **({"FIREBASE_STORAGE_BUCKET": ("Firebase Storage bucket name for uploads, e.g. your-project-id.appspot.com", "your-project-id.appspot.com")} if I["uploads"] and m.get("storage") == "firebase-storage" else {}),
            **({"UPLOAD_MAX_BYTES": ("Maximum upload size in bytes", "5242880")} if I["uploads"] else {}),
            **({M.PAY_CUR[prov][0]: ("Three-letter ISO currency for payments", M.PAY_CUR[prov][1])} if I["payments"] else {}),
            **({"WS_MAX_CLIENTS": ("Maximum simultaneous WebSocket clients", "500")} if I["ws"] else {})}
    env = M.env_lines(spec, m, {}, more=more)
    files["backend/.env.example"] = "\n".join(env) + "\n"
    files["backend/.gitignore"] = "node_modules\n.env\n*.db\n*.db-journal\n" + ("secrets/\n*service-account*.json\n" if _fb(m) else "")
    files["backend/README.md"] = readme(m, spec)
    files["backend/.agent-manifest.json"] = json.dumps({"generator": "express", "db": m["db"], "routes": m["manifest"]}, indent=1) + "\n"
    return files


def commands(m: dict) -> dict:
    steps = ["cd backend", "npm install", "cp .env.example .env"] + (["npm run seed:admin"] if m["auth"] else []) + ["npm run dev"]
    return {"run": " && ".join(steps), "test": "cd backend && npm test"}

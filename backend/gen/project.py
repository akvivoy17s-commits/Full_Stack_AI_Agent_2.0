"""Phase 7: project-level extras next to the backend (zero LLM tokens, deterministic).

Dockerfile + .dockerignore (per backend), docker-compose.yml + .env.example (db / redis / uploads volume),
GitHub Actions CI, and a typed frontend API client built from the same model the backend was generated from.
Everything is derived from the model flags, so nothing is listed that the backend does not ship.
"""
import json

from backend.gen import model as M
from backend.gen import spring_gen

NODE, PY = "node:20-bookworm-slim", "python:3.12-slim"
VITE = ("react", "vue", "svelte")
DB_SVC = {"postgresql": ("postgres:16-alpine", "postgresql://app:${DB_PASSWORD:?set DB_PASSWORD}@db:5432/app", 5432),
          "mysql": ("mysql:8.4", "mysql://app:${DB_PASSWORD:?set DB_PASSWORD}@db:3306/app", 3306),
          "mongodb": ("mongo:7", "mongodb://db:27017/app", 27017)}
DB_ENV = {"postgresql": {"POSTGRES_USER": "app", "POSTGRES_PASSWORD": "${DB_PASSWORD:?set DB_PASSWORD}", "POSTGRES_DB": "app"},
          "mysql": {"MYSQL_USER": "app", "MYSQL_PASSWORD": "${DB_PASSWORD:?set DB_PASSWORD}", "MYSQL_ROOT_PASSWORD": "${DB_PASSWORD:?set DB_PASSWORD}", "MYSQL_DATABASE": "app"}}
DB_DATA = {"postgresql": "/var/lib/postgresql/data", "mysql": "/var/lib/mysql", "mongodb": "/data/db"}
DB_HEALTH = {"postgresql": "pg_isready -U app -d app", "mysql": "mysqladmin ping -h 127.0.0.1 -uroot -p$$MYSQL_ROOT_PASSWORD --silent", "mongodb": "mongosh --quiet --eval 'db.runCommand({ping:1})'"}


def _kind(stack: dict) -> str:
    return {"express": "node", "nestjs": "nest", "spring": "java"}.get(stack["backend"], "python")


def dockerfile(stack: dict, m: dict) -> str:
    k = _kind(stack)
    if k == "java":
        j = getattr(spring_gen, "JAVA", "21")
        return (f"FROM maven:3.9-eclipse-temurin-{j} AS build\nWORKDIR /src\nCOPY pom.xml .\nRUN mvn -q -B dependency:go-offline\nCOPY src ./src\nRUN mvn -q -B -DskipTests package && cp target/*.jar /app.jar\n\n"
                f"FROM eclipse-temurin:{j}-jre\nRUN useradd -r -u 10001 app && mkdir /data && chown app /data\nWORKDIR /app\nCOPY --from=build /app.jar app.jar\nENV HOST=0.0.0.0 PORT=8000\nEXPOSE 8000\nUSER app\nCMD [\"java\", \"-jar\", \"app.jar\"]\n")
    hc_node = "CMD node -e \"fetch('http://127.0.0.1:'+(process.env.PORT||8000)+'/api/health').then(r=>process.exit(r.ok?0:1)).catch(()=>process.exit(1))\""
    hc_py = "CMD python -c \"import os,urllib.request as u;u.urlopen('http://127.0.0.1:'+os.environ.get('PORT','8000')+'/api/health',timeout=3)\""
    tail = "ENV HOST=0.0.0.0 PORT=8000 NODE_ENV=production\n" if k != "python" else "ENV HOST=0.0.0.0 PORT=8000 PYTHONUNBUFFERED=1\n"
    if k == "nest":
        return (f"FROM {NODE} AS build\nWORKDIR /app\nCOPY package*.json ./\nRUN npm install\nCOPY . .\nRUN npm run build\n\n"
                f"FROM {NODE}\nWORKDIR /app\nCOPY package*.json ./\nRUN npm install --omit=dev && npm cache clean --force\nCOPY --from=build /app/dist ./dist\n{tail}"
                f"RUN mkdir -p uploads && chown -R node:node /app\nUSER node\nEXPOSE 8000\nHEALTHCHECK --interval=30s --timeout=5s --start-period=20s {hc_node}\nCMD [\"node\", \"dist/main\"]\n")
    if k == "node":
        return (f"FROM {NODE}\nWORKDIR /app\nCOPY package*.json ./\nRUN npm install --omit=dev && npm cache clean --force\nCOPY . .\n{tail}"
                f"RUN mkdir -p uploads data && chown -R node:node /app\nUSER node\nEXPOSE 8000\nHEALTHCHECK --interval=30s --timeout=5s --start-period=20s {hc_node}\nCMD [\"node\", \"src/server.js\"]\n")
    return (f"FROM {PY}\nWORKDIR /app\nCOPY requirements.txt .\nRUN pip install --no-cache-dir -r requirements.txt\nCOPY . .\n{tail}"
            f"RUN useradd -r -u 10001 app && mkdir -p uploads data && chown -R app /app\nUSER app\nEXPOSE 8000\nHEALTHCHECK --interval=30s --timeout=5s --start-period=20s {hc_py}\nCMD [\"python\", \"-m\", \"app\"]\n")


def dockerignore(stack: dict) -> str:
    base = [".env", ".env.*", "!.env.example", "*.db", "uploads", ".git", ".pytest_cache", "__pycache__", ".venv", "tests"]
    return "\n".join(base + {"node": ["node_modules"], "nest": ["node_modules", "dist"], "java": ["target"]}.get(_kind(stack), [])) + "\n"


def _y(v: str) -> str:
    return json.dumps(v)


def compose(spec: dict, stack: dict, m: dict) -> str:
    db, I, k = m["db"], m["integrations"], _kind(stack)
    env = {"PORT": "8000", "HOST": "0.0.0.0", "CORS_ORIGINS": "${CORS_ORIGINS:-http://localhost:5173}"}
    if m["auth"]:
        env["JWT_SECRET"] = "${JWT_SECRET:?set JWT_SECRET (32+ random chars)}"
    if db in DB_SVC:
        env["DATABASE_URL"] = DB_SVC[db][1]
    elif db == "sqlite":
        env["DATABASE_URL"] = "sqlite:////app/data/app.db"
    if m["sql"]:
        env["AUTO_MIGRATE"] = "true"
    if I["cache"]:
        env["REDIS_URL"] = "redis://redis:6379"
    if I["uploads"] and (m.get("storage") or "local") == "local":
        env["UPLOAD_DIR"] = "/app/uploads"
    out = ["# Generated. Start with: cp docker.env.example docker.env && docker compose --env-file docker.env up --build", "services:", "  api:", "    build: ./backend",
           "    ports:", '      - "${API_PORT:-8000}:8000"', "    env_file:", "      - path: ./backend/.env", "        required: false", "    environment:"]
    out += [f"      {n}: {_y(v)}" for n, v in env.items()]
    vols = []
    if db == "sqlite":
        vols.append(("/app/data", "data"))
    if I["uploads"] and (m.get("storage") or "local") == "local":
        vols.append(("/app/uploads", "uploads"))
    if vols:
        out += ["    volumes:"] + [f"      - {n}:{p}" for p, n in vols]
    dep = (["db"] if db in DB_SVC else []) + (["redis"] if I["cache"] else [])
    if dep:
        out += ["    depends_on:"] + [f"      {d}:\n        condition: service_healthy" for d in dep]
    out += ["    restart: unless-stopped"]
    if db in DB_SVC:
        out += ["  db:", f"    image: {DB_SVC[db][0]}"]
        if db in DB_ENV:
            out += ["    environment:"] + [f"      {n}: {_y(v)}" for n, v in DB_ENV[db].items()]
        out += ["    volumes:", f"      - dbdata:{DB_DATA[db]}", "    healthcheck:", f"      test: [\"CMD-SHELL\", {_y(DB_HEALTH[db])}]",
                "      interval: 5s", "      timeout: 5s", "      retries: 20", "    restart: unless-stopped"]
    if I["cache"]:
        out += ["  redis:", "    image: redis:7-alpine", "    healthcheck:", "      test: [\"CMD\", \"redis-cli\", \"ping\"]", "      interval: 5s", "      timeout: 3s", "      retries: 20", "    restart: unless-stopped"]
    names = [n for _, n in vols] + (["dbdata"] if db in DB_SVC else [])
    if names:
        out += ["volumes:"] + [f"  {n}:" for n in names]
    if db == "mssql":
        out.insert(1, "# SQL Server is not started here: set DATABASE_URL in backend/.env to your own SQL Server.")
    return "\n".join(out) + "\n"


def compose_env(m: dict) -> str:
    lines = ["# Used by docker-compose.yml only. Provider keys (Stripe, S3, ...) go in backend/.env (see backend/.env.example)."]
    if m["auth"]:
        lines.append("JWT_SECRET=<generate-a-long-random-string>")
    if m["db"] in ("postgresql", "mysql"):
        lines.append("DB_PASSWORD=<choose-a-db-password>")
    lines += ["CORS_ORIGINS=http://localhost:5173", "API_PORT=8000"]
    return "\n".join(lines) + "\n"


def ci(stack: dict) -> str:
    k = _kind(stack)
    setup = {"node": "      - uses: actions/setup-node@v4\n        with: { node-version: 20 }\n      - run: npm install\n      - run: npm test",
             "nest": "      - uses: actions/setup-node@v4\n        with: { node-version: 20 }\n      - run: npm install\n      - run: npm run build\n      - run: npm test",
             "java": f"      - uses: actions/setup-java@v4\n        with: {{ distribution: temurin, java-version: '{getattr(spring_gen, 'JAVA', '21')}' }}\n      - run: mvn -B -q test",
             "python": "      - uses: actions/setup-python@v5\n        with: { python-version: '3.12' }\n      - run: pip install -r requirements-dev.txt\n      - run: python -m pytest -q"}[k]
    return ("name: CI\non:\n  push: { branches: [main] }\n  pull_request:\n\njobs:\n  backend:\n    runs-on: ubuntu-latest\n    defaults:\n      run:\n        working-directory: backend\n    steps:\n      - uses: actions/checkout@v4\n"
            + setup + "\n      - run: docker build -t api-ci .\n"
            "\n  frontend:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n      - uses: actions/setup-node@v4\n        with: { node-version: 20 }\n"
            "      - name: Build the web app (skipped when there is no package.json at the root)\n        run: |\n          if [ -f package.json ]; then npm install && npm run build --if-present; else echo 'no frontend at root'; fi\n")


def _ts_type(f: dict) -> str:
    return {"int": "number", "float": "number", "bool": "boolean", "ref": "number"}.get(f["type"], "string")


def client(m: dict, ts: bool) -> str:
    ents = [e for e in m["entities"] if not e["internal"] and e["path"] and e["ops"]]
    T = (lambda s: s) if ts else (lambda s: "")
    out = ["// Generated from the app spec. Same contract as the generated backend (" + ", ".join(f"/api/{e['path']}" for e in ents) + ").", "// Set VITE_API_URL to the backend origin.", ""]
    if ts:
        for e in ents:
            fs = "".join(f"  {f['name']}{'' if f['required'] else '?'}: {_ts_type(f)};\n" for f in e["fields"] if not (e["isUser"] and "password" in f["name"]))
            out.append(f"export interface {e['name']} {{\n  id: number;\n{fs}}}\n")
        out += ["export interface Page<T> { data: T[]; page: number; limit: number; total: number }",
                "export interface ListQuery { page?: number; limit?: number; q?: string; sort?: string; [k: string]: string | number | boolean | undefined }", ""]
    api_err = ("export class ApiError extends Error {\n  constructor(public status: number, public code: string, message: string, public details?: unknown) { super(message); }\n}" if ts else
               "export class ApiError extends Error {\n  constructor(status, code, message, details) { super(message); this.status = status; this.code = code; this.details = details; }\n}")
    out += [api_err, "",
            "const env = (import.meta" + (" as any" if ts else "") + ").env || {};", "export const API_URL = String(env.VITE_API_URL || 'http://localhost:8000').replace(/\\/$/, '');", "",
            "let access" + T(": string | null") + " = null;", "let refresh" + T(": string | null") + " = null;",
            "const KEY = 'api.refresh';", "try { refresh = localStorage.getItem(KEY); } catch { /* storage unavailable */ }",
            f"export function setTokens(a{T(': string | null')}, r{T('?: string | null')}) {{\n  access = a; if (r !== undefined) refresh = r;\n  try {{ refresh ? localStorage.setItem(KEY, refresh) : localStorage.removeItem(KEY); }} catch {{ /* ignore */ }}\n}}", ""]
    out += [f"async function raw(path{T(': string')}, method{T(': string')}, body{T('?: unknown')}, token{T(': string | null')} = access){T(': Promise<Response>')} {{\n"
            "  const h" + T(": { [k: string]: string }") + " = {};\n  if (body !== undefined) h['Content-Type'] = 'application/json';\n  if (token) h.Authorization = 'Bearer ' + token;\n"
            "  return fetch(API_URL + path, { method, headers: h, body: body === undefined ? undefined : JSON.stringify(body) });\n}", ""]
    if m["auth"] and m["refresh"]:
        out += [f"let pending{T(': Promise<boolean> | null')} = null;\nasync function renew(){T(': Promise<boolean>')} {{\n  if (!refresh) return false;\n  pending ??= (async () => {{\n    const r = await raw('/api/auth/refresh', 'POST', {{ refreshToken: refresh }}, null);\n"
                "    if (!r.ok) {{ setTokens(null, null); return false; }}\n    const d = await r.json(); setTokens(d.accessToken, d.refreshToken ?? null); return true;\n  }})().finally(() => {{ pending = null; }});\n  return pending;\n}}".replace("{{", "{").replace("}}", "}"), ""]
    renew = "if (r.status === 401 && access && (await renew())) r = await raw(path, method, body);" if m["auth"] and m["refresh"] else ""
    out += [f"async function call{'<T>' if ts else ''}(path{T(': string')}, method = 'GET', body{T('?: unknown')}){T(': Promise<T>')} {{\n  let r = await raw(path, method, body);\n  {renew}\n"
            "  if (r.status === 204) return undefined" + T(" as T") + ";\n  const d = await r.json().catch(() => ({}));\n"
            "  if (!r.ok) throw new ApiError(r.status, d?.error?.code || 'error', d?.error?.message || r.statusText, d?.error?.details);\n  return d" + T(" as T") + ";\n}", ""]
    out.append(f"const qs = (q{T('?: ListQuery')}) => {{\n  const p = new URLSearchParams();\n  for (const [k, v] of Object.entries(q || {{}})) if (v !== undefined && v !== '') p.set(k, String(v));\n  const s = p.toString();\n  return s ? '?' + s : '';\n}};\n")
    body = []
    if m["auth"]:
        tk = "d.accessToken, d.refreshToken ?? null"
        body += [f"  auth: {{\n    async login(email{T(': string')}, password{T(': string')}) {{ const d = await call{'<any>' if ts else ''}('/api/auth/login', 'POST', {{ email, password }}); setTokens({tk}); return d.user; }},\n"
                 f"    async register(data{T(': { [k: string]: unknown }')}) {{ const d = await call{'<any>' if ts else ''}('/api/auth/register', 'POST', data); setTokens({tk}); return d.user; }},\n"
                 f"    me() {{ return call{'<{ user: any }>' if ts else ''}('/api/auth/me').then((d{T(': any')}) => d.user); }},\n"
                 "    async logout() { try { await call('/api/auth/logout', 'POST', { refreshToken: refresh }); } finally { setTokens(null, null); } },\n  },"]
    for e in ents:
        n, p, ops = e["name"], e["path"], e["ops"]
        rows = []
        if "list" in ops:
            rows.append(f"list: (q{T('?: ListQuery')}) => call{f'<Page<{n}>>' if ts else ''}('/api/{p}' + qs(q)),")
        if "get" in ops:
            rows.append(f"get: (id{T(': number')}) => call{f'<{n}>' if ts else ''}(`/api/{p}/${{id}}`),")
        if "create" in ops:
            rows.append(f"create: (data{T(f': Partial<{n}>')}) => call{f'<{n}>' if ts else ''}('/api/{p}', 'POST', data),")
        if "update" in ops:
            rows.append(f"update: (id{T(': number')}, data{T(f': Partial<{n}>')}) => call{f'<{n}>' if ts else ''}(`/api/{p}/${{id}}`, 'PUT', data),")
        if "delete" in ops:
            rows.append(f"remove: (id{T(': number')}) => call{'<void>' if ts else ''}(`/api/{p}/${{id}}`, 'DELETE'),")
        key = p.replace("-", "_")
        body.append(f"  {key}: {{\n" + "\n".join("    " + r for r in rows) + "\n  },")
    if m.get("checkout"):
        body.append(f"  checkout: (items{T(': { productId: number; quantity: number }[]')}) => call{'<any>' if ts else ''}('/api/checkout', 'POST', {{ items }}),")
    if m["integrations"]["payments"]:
        body.append(f"  payIntent: (orderId{T(': number')}) => call{'<any>' if ts else ''}('/api/payments/intent', 'POST', {{ orderId }}),")
    out += ["export const api = {"] + body + ["};", ""]
    if m["integrations"]["ws"]:
        out += [f"/** Live updates: calls onChange({{ entity, op }}) after a write; refetch over REST. Returns a close function. */",
                f"export function watch(onChange{T(': (e: { entity: string; op: string }) => void')}){T(': () => void')} {{\n  const ws = new WebSocket(API_URL.replace(/^http/, 'ws') + '/ws');\n"
                "  ws.onopen = () => access && ws.send(JSON.stringify({ type: 'auth', token: access }));\n  ws.onmessage = (ev) => { try { const d = JSON.parse(ev.data); if (d.type === 'change') onChange(d); } catch { /* ignore */ } };\n  return () => ws.close();\n}", ""]
    return "\n".join(out)


def extras(spec: dict, stack: dict, m: dict) -> dict[str, str]:
    f = {"backend/Dockerfile": dockerfile(stack, m), "backend/.dockerignore": dockerignore(stack), "docker-compose.yml": compose(spec, stack, m),
         "docker.env.example": compose_env(m), ".github/workflows/ci.yml": ci(stack)}
    fe = stack.get("frontend")
    if fe in VITE:
        ts = (stack.get("frontend_lang") or "typescript") != "javascript"
        f["src/api/client." + ("ts" if ts else "js")] = client(m, ts)
    return f

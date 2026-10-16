"""NestJS (Node.js, TypeScript) generator. Static TypeScript lives in templates/nestjs; only data-driven files are built here
(schema.ts, app.module.ts, db/connect.ts, package.json, README). Same spec -> API contract as Express, FastAPI and Flask."""
import json
from pathlib import Path

from backend.gen import model as M
from backend.gen import openapi

TPL = Path(__file__).parent / "templates" / "nestjs"
DRIVER = {"sqlite": {"better-sqlite3": "^11.3.0"}, "postgresql": {"pg": "^8.12.0"}, "mysql": {"mysql2": "^3.11.0"}, "mssql": {"mssql": "^11.0.1"}}
NEST = "^10.4.0"          # Nest 10 runs on Express 4, which the body-size limit and the exception mapping rely on
COMMON = {"@nestjs/common": NEST, "@nestjs/core": NEST, "@nestjs/platform-express": NEST, "express": "^4.19.2", "helmet": "^7.1.0",
          "dotenv": "^16.4.5", "reflect-metadata": "^0.2.2", "rxjs": "^7.8.1"}
DEV = {"@nestjs/cli": NEST, "@nestjs/testing": NEST, "@types/express": "^4.17.21", "@types/jest": "^29.5.12", "@types/node": "^20.14.0",
       "@types/supertest": "^6.0.2", "jest": "^29.7.0", "supertest": "^7.0.0", "ts-jest": "^29.2.0", "ts-node": "^10.9.2", "typescript": "^5.5.0"}
TSCONFIG = {"compilerOptions": {"module": "commonjs", "target": "ES2021", "removeComments": True, "emitDecoratorMetadata": True,
                                "experimentalDecorators": True, "esModuleInterop": True, "sourceMap": True, "outDir": "./dist",
                                "incremental": True, "skipLibCheck": True, "strict": True, "forceConsistentCasingInFileNames": True},
            "include": ["src", "test"]}


def schema_ts(m: dict) -> str:
    body = {"db": m["db"], "seed": m["seed"], "auth": m["auth"], "refresh": m["auth"] and m["refresh"], "roles": m["roles"], "adminRole": m["adminRole"],
            "defaultRole": m["defaultRole"], "entities": {e["name"]: e for e in m["entities"]}, "integrations": m["integrations"], "checkout": bool(m.get("checkout"))}
    return ("// Generated from the app spec (entities, fields, access rules). Single source of truth for validation, routes, migrations and tests.\n"
            "import { Schema } from './common/types';\n\nexport const SCHEMA = " + json.dumps(body, indent=2) + " as unknown as Schema;\n")


def app_module(m: dict) -> str:
    imps = ["import { Module } from '@nestjs/common';", "import { APP_FILTER, APP_GUARD } from '@nestjs/core';",
            "import { AllExceptionsFilter } from './common/exception.filter';", "import { ApiLimit } from './common/rate-limit';",
            "import { HealthController } from './health.controller';"]
    mods = []
    if m["db"]:
        imps += ["import { AccessModule } from './auth/access.module';", "import { CrudModule } from './crud/crud.module';", "import { DbModule } from './db/db.module';"]
        mods += ["DbModule", "AccessModule"]
        if m["auth"]:
            imps.append("import { AuthModule } from './auth/auth.module';")
            mods.append("AuthModule")
        if m.get("checkout"):
            imps.append("import { CheckoutModule } from './checkout/checkout.module';")
            mods.append("CheckoutModule")
        mods.append("CrudModule")
    return ("\n".join(imps) + f"""

@Module({{
  imports: [{', '.join(mods)}],
  controllers: [HealthController],
  providers: [
    {{ provide: APP_GUARD, useClass: ApiLimit }},
    {{ provide: APP_FILTER, useClass: AllExceptionsFilter }},
  ],
}})
export class AppModule {{}}
""")


def connect_ts(m: dict) -> str:
    if not m["db"]:
        return "import { Db } from './db';\n\n// This app has no database.\nexport const connect = async (): Promise<Db | null> => null;\n"
    return f"// Adapter for the database this project was generated for ({m['db']}).\nexport {{ connect }} from './{'mongoose' if m['db'] == 'mongodb' else 'typeorm'}.db';\n"


def package_json(m: dict, name: str) -> str:
    deps, dev = dict(COMMON), dict(DEV)
    if m["db"]:
        deps["@nestjs/jwt"] = "^10.2.0"
    if m["auth"]:
        deps["bcryptjs"] = "^2.4.3"
        dev["@types/bcryptjs"] = "^2.4.6"
    if m["sql"]:
        deps.update({"typeorm": "^0.3.20", **DRIVER[m["db"]]})
    elif m["db"] == "mongodb":
        deps["mongoose"] = "^8.6.0"
    I = m["integrations"]
    if I["cache"]:
        deps["redis"] = "^4.7.0"
    if I["ws"]:
        deps["ws"] = "^8.18.0"
        dev["@types/ws"] = "^8.5.12"
    if I["uploads"] or I["ws"] or I["payments"]:
        deps["jsonwebtoken"] = "^9.0.2"
        dev["@types/jsonwebtoken"] = "^9.0.6"
    if I["uploads"] and m.get("storage") == "firebase-storage":
        deps["firebase-admin"] = "^12.6.0"
    scripts = {"build": "nest build", "start": "node dist/main", "start:dev": "nest start --watch", "test": "jest --runInBand"}
    if m["db"]:
        scripts["migrate"] = "ts-node src/scripts/migrate.ts"
    if m["auth"]:
        scripts["seed:admin"] = "ts-node src/scripts/seed-admin.ts"
    if m["db"]:
        scripts["seed:sample"] = "ts-node src/scripts/seed-sample.ts"
    jest = {"rootDir": ".", "testEnvironment": "node", "setupFiles": ["<rootDir>/test/setup-env.ts"], "testRegex": "test/.*\\.e2e-spec\\.ts$",
            "transform": {"^.+\\.ts$": "ts-jest"}, "moduleFileExtensions": ["js", "json", "ts"], "testTimeout": 30000}
    pkg = {"name": f"{name}-api", "version": "1.0.0", "private": True, "description": "Generated NestJS API", "engines": {"node": ">=18.18"},
           "scripts": scripts, "dependencies": dict(sorted(deps.items())), "devDependencies": dict(sorted(dev.items())), "jest": jest}
    return json.dumps(pkg, indent=2) + "\n"


def readme(m: dict, spec: dict) -> str:
    db = {"sqlite": "SQLite (file)", "postgresql": "PostgreSQL", "mysql": "MySQL", "mssql": "SQL Server", "mongodb": "MongoDB", None: "none"}[m["db"]]
    orm = {"mongodb": "Mongoose", None: ""}.get(m["db"], "TypeORM")
    steps = ["cd backend", "npm install", "cp .env.example .env   # then edit the values"]
    if m["auth"]:
        steps.append("npm run seed:admin   # creates the first admin from ADMIN_EMAIL / ADMIN_PASSWORD")
    if m["sql"]:
        steps.append("npm run migrate      # optional in development when AUTO_MIGRATE=true")
    steps += ["npm run start:dev", "npm test"]
    routes = "\n".join(f"- `{r}`" for r in m["manifest"])
    notes = "\n".join(f"- {n}" for n in m["warnings"] + [f"Not generated yet: {x}." for x in m["not_generated"]]) or "- none"
    auth = (f"- Sign-up always creates role `{m['defaultRole']}`; admins come from `npm run seed:admin`.\n- Access token (HS256, short lived, `@nestjs/jwt`) + single-use rotating refresh token (stored hashed).\n"
            "- Responses: `{user, accessToken, refreshToken, tokenType, expiresIn}`.") if m["auth"] else "- No authentication in this app."
    extra = "  Tests for PostgreSQL / MySQL / MongoDB need `TEST_DATABASE_URL` pointing at a disposable database." if m["db"] and m["db"] != "sqlite" else ""
    return f"""# {spec['purpose'][:80]} - API

NestJS (TypeScript) + {db}{(' via ' + orm) if orm else ''}. Generated from the app spec; routes, validation and tests follow `src/schema.ts`. Node.js 18.18 or newer.

## Run
```bash
{chr(10).join(steps)}
```
Production: `npm run build && npm start` (migrations: `node dist/scripts/migrate.js`). Health check: `GET /api/health`.{extra}

## Layout
`src/crud/` one controller per entity (built from the spec) + `CrudService` (access rules, validation); `src/auth/` guards, JWT, sign-in flow; `src/db/` the data layer behind one `Db` interface; `src/common/` validation, errors, rate limits. Controllers only map HTTP onto services.

## Routes
{routes}

Lists accept `?page`, `?limit` (max 100), `?q` and exact filters on reference / enum / boolean fields, and return `{{data, page, limit, total}}`.
Errors are always `{{error: {{code, message, details?}}}}`.

## Security
{auth}
- Authorization is enforced on the server for every route (public / user / owner / admin). Other users' records return 404.
- Helmet, explicit CORS origins (`CORS_ORIGINS`), 100 kB body limit, rate limits on auth and public forms (in memory, per process), request timeout, no stack traces in responses.
- Unknown fields are rejected; every value is type-checked; queries are parameterised.
- Secrets live in `.env` only (never commit it). Put the API behind HTTPS in production and set `TRUST_PROXY` correctly.

{M.integ_readme(m)}## Notes
{notes}
"""


def notify_ts(m: dict) -> str:
    """Tells the cache and the WebSocket clients about writes made outside the CRUD controllers (checkout, payment webhooks)."""
    I = m["integrations"]
    head = "// Writes that bypass the CRUD controllers (checkout, payment webhooks) announce themselves here.\n"
    if not (I["cache"] or I["ws"]):
        return head + "export async function changed(_entities: string[]): Promise<void> {\n  // no cache and no WebSocket in this app\n}\n"
    imps = ("import * as cache from './cache';\n" if I["cache"] else "") + "import { events } from './events';\n"
    body = ("  await cache.invalidate();\n" if I["cache"] else "") + "  for (const entity of entities) events.emit('change', { entity, op: 'update' });\n"
    return head + imps + "\nexport async function changed(entities: string[]): Promise<void> {\n" + body + "}\n"


def pay_mount_ts(m: dict) -> str:
    """Mounts the payment routers on the Express layer: the webhook BEFORE the JSON parser (raw bytes are signed), the intent route after it."""
    if not m["integrations"]["payments"]:
        return ("// This app has no payments.\nimport type { NestExpressApplication } from '@nestjs/platform-express';\n\n"
                "export const mountWebhook = (_app: NestExpressApplication): void => undefined;\nexport const mountIntent = (_app: NestExpressApplication): void => undefined;\n")
    return """import { Router } from 'express';
import type { NestExpressApplication } from '@nestjs/platform-express';
import { DB, Db } from '../db/db';
import { intent, webhook } from './payments';

const db = (app: NestExpressApplication): Db => app.get<Db>(DB, { strict: false });

export function mountWebhook(app: NestExpressApplication): void {
  const r = Router();
  r.post('/', ...webhook(db(app)));
  app.use('/api/payments/webhook', r);
}

export function mountIntent(app: NestExpressApplication): void {
  app.use('/api/payments', intent(db(app)));
}
"""


def _skip(rel: str, m: dict) -> bool:
    I = m["integrations"]
    if rel in ("src/integrations/payments_razorpay.ts", "src/integrations/payments_paypal.ts"):
        return True                                    # copied over payments.ts by generate() for that provider
    if rel in ("src/integrations/payments.ts", "src/integrations/pay.ts"):
        return not I["payments"]
    if rel.startswith("src/checkout/") or rel == "test/checkout.e2e-spec.ts":
        return not m.get("checkout")
    if rel in ("src/integrations/cache.ts",):
        return not (I["cache"] or I["ws"])
    if rel in ("src/integrations/live.ts", "src/integrations/events.ts"):
        return not (I["cache"] or I["ws"])
    if rel == "src/integrations/uploads.ts":
        return not I["uploads"]
    if rel in ("src/integrations/uploads_remote.ts", "src/integrations/storage-s3.ts", "src/integrations/storage-firebase.ts"):
        return True                                    # copied by generate() for storage=s3 / firebase-storage
    if rel == "src/integrations/ws.ts":
        return not I["ws"]
    if rel == "src/db/typeorm.db.ts" or rel == "src/db/column-types.ts" or rel.startswith("src/migrations/"):
        return not m["sql"]
    if rel == "src/scripts/seed-sample.ts":
        return not m["db"]
    if rel == "src/db/mongoose.db.ts":
        return m["db"] != "mongodb"
    if rel in ("src/auth/auth.service.ts", "src/auth/auth.controller.ts", "src/auth/auth.module.ts", "src/scripts/seed-admin.ts"):
        return not m["auth"]
    if rel.startswith(("src/auth/", "src/crud/", "src/scripts/")) or rel in ("src/db/db.module.ts", "src/common/validate.ts"):
        return not m["db"]
    return False


def generate(spec: dict, stack: dict, m: dict) -> dict[str, str]:
    files = {}
    for p in sorted(TPL.rglob("*.ts")):
        rel = p.relative_to(TPL).as_posix()
        if not _skip(rel, m):
            files[f"backend/{rel}"] = p.read_text(encoding="utf-8")
    files["backend/src/schema.ts"] = schema_ts(m)
    files["backend/src/integrations/pay-mount.ts"] = pay_mount_ts(m)
    if m.get("checkout"):
        files["backend/src/integrations/notify.ts"] = notify_ts(m)
    if m["integrations"]["payments"] and (m.get("paymentProvider") or "stripe") != "stripe":
        files["backend/src/integrations/payments.ts"] = (TPL / "src" / "integrations" / f"payments_{m['paymentProvider']}.ts").read_text(encoding="utf-8")
    if m["integrations"]["uploads"] and m.get("storage") in ("s3", "firebase-storage"):
        IT = TPL / "src" / "integrations"
        files["backend/src/integrations/uploads.ts"] = (IT / "uploads_remote.ts").read_text(encoding="utf-8")
        files["backend/src/integrations/storage.ts"] = (IT / ("storage-s3.ts" if m["storage"] == "s3" else "storage-firebase.ts")).read_text(encoding="utf-8")
    files["backend/openapi.json"] = openapi.dumps(m, spec)
    files["backend/src/app.module.ts"] = app_module(m)
    files["backend/src/db/connect.ts"] = connect_ts(m)
    files["backend/package.json"] = package_json(m, M.slug(spec.get("purpose", "app").split(".")[0])[:40])
    files["backend/tsconfig.json"] = json.dumps(TSCONFIG, indent=2) + "\n"
    files["backend/tsconfig.build.json"] = json.dumps({"extends": "./tsconfig.json", "include": ["src"], "exclude": ["node_modules", "dist", "test"]}, indent=2) + "\n"
    files["backend/nest-cli.json"] = json.dumps({"sourceRoot": "src", "compilerOptions": {"deleteOutDir": True}}, indent=2) + "\n"
    files["backend/.env.example"] = "\n".join(M.env_lines(spec, m, {}, more=M.integ_env(m))) + "\n"
    files["backend/.gitignore"] = "node_modules\ndist\n.env\n*.db\n*.db-journal\n*.tsbuildinfo\n"
    files["backend/README.md"] = readme(m, spec)
    files["backend/.agent-manifest.json"] = json.dumps({"generator": "nestjs", "db": m["db"], "routes": m["manifest"]}, indent=1) + "\n"
    return files


def commands(m: dict) -> dict:
    steps = ["cd backend", "npm install", "cp .env.example .env"] + (["npm run seed:admin"] if m["auth"] else []) + ["npm run start:dev"]
    return {"run": " && ".join(steps), "test": "cd backend && npm test"}

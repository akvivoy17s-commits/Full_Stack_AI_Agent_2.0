"""Technology catalog: the single source of truth for stack selection (pure data, zero LLM tokens).

Every option has a `status`:
  "ready"        a generator for it exists in this build
  "planned:<n>"  selectable and validated, but its generator is delivered in upgrade phase <n>
Nothing marked planned is ever reported as working; the pipeline refuses or lists it as pending.
"""

READY = "ready"


def _o(label: str, desc: str, phase: int = 0, **kw) -> dict:
    return {"label": label, "desc": desc, "phase": phase, **kw}


# ------------------------------------------------------------------ frontend (framework x language)
FRONTEND = {
    "html": _o("HTML + CSS + JavaScript", "No build step. Best for portfolios and simple sites.", 5,
               langs=["js"], ready_langs=["js"], kind="static", seo="good", runtime="none"),
    "react": _o("React", "Component UI with hooks. Great for dashboards and SPAs.", 5,
                langs=["js", "ts"], ready_langs=["ts"], kind="spa", seo="limited", runtime="node"),
    "angular": _o("Angular", "Opinionated TypeScript framework (DI, RxJS, reactive forms). Enterprise apps.", 5,
                  langs=["ts"], ready_langs=[], kind="spa", seo="limited", runtime="node"),
    "next": _o("Next.js", "React with routing and server rendering. Good SEO, e-commerce, content sites.", 5,
               langs=["js", "ts"], ready_langs=[], kind="ssr", seo="good", runtime="node"),
    "vue": _o("Vue", "Approachable component framework with composables.", 5,
              langs=["js", "ts"], ready_langs=[], kind="spa", seo="limited", runtime="node"),
    "nuxt": _o("Nuxt", "Vue with routing and server rendering.", 5,
               langs=["js", "ts"], ready_langs=[], kind="ssr", seo="good", runtime="node"),
    "svelte": _o("Svelte (Vite)", "Compiler-based UI with very small bundles.", 5,
                 langs=["js", "ts"], ready_langs=[], kind="spa", seo="limited", runtime="node"),
    "sveltekit": _o("SvelteKit", "Svelte with routing and server rendering.", 5,
                    langs=["js", "ts"], ready_langs=[], kind="ssr", seo="good", runtime="node"),
    "solid": _o("SolidJS", "Fine-grained reactive UI with a React-like syntax.", 5,
                langs=["js", "ts"], ready_langs=[], kind="spa", seo="limited", runtime="node"),
}
FRONTEND_LANG = {"js": _o("JavaScript", ""), "ts": _o("TypeScript", "")}

# ------------------------------------------------------------------ backend
BACKEND = {
    "none": _o("No backend", "Frontend only, or a BaaS such as Firebase used directly from the browser.", 0,
               langs=[], runtime="none"),
    "express": _o("Node.js + Express", "Minimal, flexible REST APIs.", 3, langs=["js", "ts"], runtime="node"),
    "nestjs": _o("Node.js + NestJS", "Modular TypeScript backend (DI, guards, DTO validation).", 4, langs=["ts"], runtime="node"),
    "fastapi": _o("Python + FastAPI", "Typed async APIs with automatic OpenAPI docs. Strong for AI features.", 3, langs=["py"], runtime="python"),
    "flask": _o("Python + Flask", "Lightweight Python web framework.", 3, langs=["py"], runtime="python"),
    "django": _o("Python + Django", "Batteries included: ORM, admin, auth, migrations.", 4, langs=["py"], runtime="python"),
    "spring": _o("Java + Spring Boot", "Enterprise-grade services on Spring Boot (JDBC, Flyway, JWT).", 4, langs=["java"], runtime="java"),
    "aspnet": _o("C# + ASP.NET Core", "High-performance .NET web APIs.", 4, langs=["cs"], runtime="dotnet"),
    "laravel": _o("PHP + Laravel", "Full-featured PHP framework (Eloquent, queues, auth).", 4, langs=["php"], runtime="php"),
    "go": _o("Go (net/http)", "Small, fast, single-binary services.", 4, langs=["go"], runtime="go"),
}
BACKEND_LANG = {"js": _o("JavaScript", ""), "ts": _o("TypeScript", ""), "py": _o("Python", ""), "java": _o("Java", ""),
                "cs": _o("C#", ""), "php": _o("PHP", ""), "go": _o("Go", "")}

# ------------------------------------------------------------------ database ("group" decides which ORMs apply)
DATABASE = {
    "none": _o("No database", "Nothing persisted.", 0, group=None),
    "sqlite": _o("SQLite", "Zero-setup file database for local and lightweight apps.", 3, group="sql"),
    "postgresql": _o("PostgreSQL", "Robust relational database: relations, transactions, complex queries.", 3, group="sql"),
    "mysql": _o("MySQL", "Popular relational database, wide hosting support.", 3, group="sql"),
    "mssql": _o("Microsoft SQL Server", "Relational database for Microsoft/Azure environments.", 4, group="sql"),
    "mongodb": _o("MongoDB", "Document database for flexible, nested data.", 3, group="mongodb"),
    "firestore": _o("Firebase Firestore", "Managed document database with realtime sync (not relational SQL).", 4, group="firebase"),
    "firebase-rtdb": _o("Firebase Realtime Database", "Managed JSON tree with low-latency sync (not relational SQL).", 4, group="firebase"),
}

# ORMs / data-access layers per backend and database group. The first entry is the default.
ORMS = {
    "express": {"sql": ["knex", "prisma", "sequelize"], "mongodb": ["mongoose", "prisma"], "firebase": ["firebase-admin"]},
    "nestjs": {"sql": ["typeorm", "prisma"], "mongodb": ["mongoose", "typeorm"], "firebase": ["firebase-admin"]},
    "fastapi": {"sql": ["sqlalchemy", "sqlmodel"], "mongodb": ["pymongo", "motor", "beanie"], "firebase": ["firebase-admin"]},
    "flask": {"sql": ["sqlalchemy"], "mongodb": ["pymongo", "mongoengine"], "firebase": ["firebase-admin"]},
    "django": {"sql": ["django-orm"], "firebase": ["firebase-admin"]},          # no first-party MongoDB support
    "spring": {"sql": ["jdbc"], "mongodb": ["spring-data-mongodb"], "firebase": ["firebase-admin"]},
    "aspnet": {"sql": ["efcore"], "mongodb": ["mongodb-driver"], "firebase": ["firebase-admin"]},
    "laravel": {"sql": ["eloquent"], "mongodb": ["laravel-mongodb"], "firebase": ["firebase-admin"]},
    "go": {"sql": ["database-sql", "gorm", "sqlx"], "mongodb": ["mongo-driver"], "firebase": ["firebase-admin"]},
    "none": {"firebase": ["firebase-client"]},                                  # browser talks to Firebase, guarded by security rules
}
ORM = {k: _o(v, "", 3) for k, v in {
    "none": "None", "knex": "Knex.js", "prisma": "Prisma", "sequelize": "Sequelize", "mongoose": "Mongoose", "typeorm": "TypeORM",
    "sqlalchemy": "SQLAlchemy", "sqlmodel": "SQLModel", "motor": "Motor (async PyMongo)", "beanie": "Beanie ODM",
    "pymongo": "PyMongo", "mongoengine": "MongoEngine", "django-orm": "Django ORM", "jdbc": "Spring JDBC + Flyway",
    "spring-data-mongodb": "Spring Data MongoDB", "efcore": "Entity Framework Core", "mongodb-driver": "MongoDB .NET driver",
    "eloquent": "Eloquent", "laravel-mongodb": "Laravel MongoDB (official)", "database-sql": "database/sql",
    "gorm": "GORM", "sqlx": "sqlx", "mongo-driver": "mongo-driver", "firebase-admin": "Firebase Admin SDK",
    "firebase-client": "Firebase client SDK + security rules"}.items()}

# ------------------------------------------------------------------ cross-cutting options
AUTH = {
    "none": _o("No authentication", "", 0),
    "jwt": _o("JWT (access + refresh)", "Stateless tokens verified by the backend.", 3),
    "session": _o("Cookie sessions", "Server-side sessions; best for same-site apps.", 3),
    "oauth2": _o("OAuth 2 / social login", "Sign in with Google, GitHub and similar.", 4),
    "firebase-auth": _o("Firebase Authentication", "Managed sign-in; the backend verifies Firebase ID tokens.", 4),
}
CACHE = {
    "none": _o("No cache", "", 0),
    "redis": _o("Redis", "Shared cache, rate-limit counters, queues.", 4),
    "memory": _o("In-process memory cache", "Framework-level cache, single instance only.", 4),
}
STORAGE = {
    "none": _o("No file storage", "", 0),
    "local": _o("Local disk", "Development and single-server deployments.", 3),
    "s3": _o("S3-compatible object storage", "AWS S3, MinIO, Cloudflare R2 and similar.", 4),
    "firebase-storage": _o("Firebase Storage", "Managed storage with security rules.", 4),
}
AI = {
    "none": _o("No AI features", "", 0),
    "llm-api": _o("LLM API from the backend", "Backend calls a hosted LLM; the key never reaches the browser.", 4),
    "python-inprocess": _o("Python AI module (in the Python backend)", "ML/NLP/vision code inside FastAPI, Flask or Django.", 4),
    "python-service": _o("Separate Python AI service", "Isolated FastAPI service reached over HTTP. For heavy or isolated ML.", 4),
}
TESTING = {k: _o(v, "", 0 if k == "none" else 5) for k, v in {
    "none": "No test framework", "vitest": "Vitest", "jest": "Jest", "karma": "Karma + Jasmine",
    "playwright": "Playwright", "cypress": "Cypress"}.items()}
TESTING_FOR = {   # which frontend test runners make sense for which framework (first = default)
    "html": ["none", "playwright", "cypress"],
    "react": ["vitest", "jest", "playwright", "cypress", "none"],
    "angular": ["karma", "jest", "vitest", "playwright", "cypress", "none"],
    "next": ["jest", "vitest", "playwright", "cypress", "none"],
    "vue": ["vitest", "jest", "playwright", "cypress", "none"],
    "nuxt": ["vitest", "playwright", "cypress", "none"],
    "svelte": ["vitest", "jest", "playwright", "cypress", "none"],
    "sveltekit": ["vitest", "playwright", "cypress", "none"],
    "solid": ["vitest", "jest", "playwright", "none"],
}
BACKEND_TESTS = {"express": "jest + supertest", "nestjs": "jest + supertest", "fastapi": "pytest", "flask": "pytest",
                 "django": "pytest", "spring": "JUnit", "aspnet": "xUnit", "laravel": "PHPUnit", "go": "go test", "none": ""}
DEPLOY = {k: _o(v, "", 0 if k == "local" else 8) for k, v in {
    "local": "Local only", "docker": "Docker / docker-compose", "static": "Static hosting (GitHub Pages, S3...)",
    "vercel": "Vercel", "netlify": "Netlify", "render": "Render", "firebase-hosting": "Firebase Hosting"}.items()}

TABLES = {"frontend": FRONTEND, "frontend_lang": FRONTEND_LANG, "backend": BACKEND, "backend_lang": BACKEND_LANG,
          "database": DATABASE, "orm": ORM, "auth": AUTH, "cache": CACHE, "storage": STORAGE, "ai": AI,
          "testing": TESTING, "deploy": DEPLOY}
FIELDS = tuple(TABLES)
RUNTIME_NAME = {"node": "Node.js 18+", "python": "Python 3.11+", "java": "JDK 17+", "dotnet": ".NET SDK 8+", "php": "PHP 8.2+ + Composer", "go": "Go 1.22+"}


# Backend generators that exist in this build (phase 3: Express, FastAPI, Flask; phase 4: NestJS, Django, more to come). Readiness is per combination, never per label.
GENERATORS = {
    "express": {"langs": ["js"], "db": ["sqlite", "postgresql", "mysql", "mssql", "mongodb"], "orm": {"sql": "knex", "mongodb": "mongoose"},
                "auth": ["none", "jwt", "firebase-auth"], "storage": ["none", "local", "s3", "firebase-storage"], "cache": ["none", "redis"], "ai": ["none"]},
    "nestjs": {"langs": ["ts"], "db": ["sqlite", "postgresql", "mysql", "mssql", "mongodb"], "orm": {"sql": "typeorm", "mongodb": "mongoose"},
               "auth": ["none", "jwt"], "storage": ["none", "local", "s3", "firebase-storage"], "cache": ["none", "redis"], "ai": ["none"]},
    "fastapi": {"langs": ["py"], "db": ["sqlite", "postgresql", "mysql", "mssql", "mongodb"], "orm": {"sql": "sqlalchemy", "mongodb": "pymongo"},
                "auth": ["none", "jwt"], "storage": ["none", "local", "s3", "firebase-storage"], "cache": ["none", "redis"], "ai": ["none"]},
    "flask": {"langs": ["py"], "db": ["sqlite", "postgresql", "mysql", "mssql", "mongodb"], "orm": {"sql": "sqlalchemy", "mongodb": "pymongo"},
              "auth": ["none", "jwt"], "storage": ["none", "local", "s3", "firebase-storage"], "cache": ["none", "redis"], "ai": ["none"]},
    "spring": {"langs": ["java"], "db": ["sqlite", "postgresql", "mysql", "mssql", "mongodb"], "orm": {"sql": "jdbc", "mongodb": "spring-data-mongodb"},
               "auth": ["none", "jwt"], "storage": ["none", "local", "s3", "firebase-storage"], "cache": ["none", "redis"], "ai": ["none"]},
    "django": {"langs": ["py"], "db": ["sqlite", "postgresql", "mysql", "mssql"], "orm": {"sql": "django-orm"},      # MongoDB is rejected by the rules (no first-party support)
               "auth": ["none", "jwt"], "storage": ["none", "local", "s3", "firebase-storage"], "cache": ["none", "redis"], "ai": ["none"]},
}


def generator_gaps(stack: dict) -> list[str]:
    """Why the selected backend combination cannot be generated yet ([] = fully generable). Rule based, zero tokens."""
    b = stack.get("backend") or "none"
    if b == "none":
        return []
    g = GENERATORS.get(b)
    if not g:
        return [f"{BACKEND[b]['label']} generator is planned (phase {BACKEND[b]['phase']})."]
    out = []
    lang = stack.get("backend_lang") or g["langs"][0]
    if lang not in g["langs"]:
        out.append(f"{BACKEND[b]['label']} is generated in {', '.join(g['langs'])} only; {lang} is planned.")
    db = stack.get("database") or "none"
    if db != "none" and db not in g["db"]:
        out.append(f"{DATABASE[db]['label']} with {BACKEND[b]['label']} is planned (phase {DATABASE[db]['phase']}).")
    elif db != "none":
        want = g["orm"].get(db_group(db))
        orm = stack.get("orm") or want
        if orm not in (None, "none", want):
            out.append(f"{ORM[orm]['label']} is not generated yet; this build generates {ORM[want]['label']} for {DATABASE[db]['label']}.")
    for f in ("auth", "cache", "storage", "ai"):
        v = stack.get(f) or "none"
        if v not in g[f]:
            out.append(f"{TABLES[f][v]['label']} is planned (phase {TABLES[f][v]['phase']}).")
    return out


def status(field: str, value: str, stack: dict | None = None) -> str:
    """'ready' or 'planned:<phase>'. Frontends depend on the chosen language (React is ready for TypeScript only);
    backend/database/orm/auth/cache/storage/ai depend on the whole combination once a backend generator exists."""
    if field in ("backend", "database", "orm", "auth", "cache", "storage", "ai") and value not in (None, "", "none"):
        b = (stack or {}).get("backend")
        if stack is not None and b in GENERATORS:
            bad = generator_gaps(stack)
            label = TABLES[field][value]["label"] if value in TABLES[field] else value
            if field == "backend":
                return READY if not any("is generated in" in g or "generator is planned" in g for g in bad) else f"planned:{TABLES[field][value]['phase']}"
            return f"planned:{TABLES[field][value]['phase']}" if any(g.startswith(label) for g in bad) else READY
        if field == "backend" and value in GENERATORS:
            return READY
        if stack is None and field in ("database", "auth") and any(value in g[{"database": "db"}.get(field, field)] for g in GENERATORS.values()):
            return READY
    if value in (None, "", "none") and field != "frontend":
        return READY
    item = TABLES[field].get(value)
    if not item:
        return "unknown"
    if field == "frontend":
        lang = (stack or {}).get("frontend_lang")
        return READY if lang in item["ready_langs"] else f"planned:{item['phase']}"
    return READY if item["phase"] == 0 else f"planned:{item['phase']}"


def db_group(db: str | None) -> str | None:
    return DATABASE.get(db or "none", {}).get("group")


def public() -> dict:
    """JSON for the UI: every option with label, description and status."""
    out = {}
    for field, table in TABLES.items():
        out[field] = [{"id": k, "label": v["label"], "desc": v["desc"], "status": status(field, k) if field != "frontend" else
                       (READY if v["ready_langs"] else f"planned:{v['phase']}"),
                       **({"langs": v["langs"], "ready_langs": v["ready_langs"], "kind": v["kind"]} if field == "frontend" else {}),
                       **({"langs": v["langs"], "runtime": v["runtime"]} if field == "backend" else {})} for k, v in table.items()]
    return {"fields": out, "orms": ORMS, "testing_for": TESTING_FOR, "backend_tests": BACKEND_TESTS}

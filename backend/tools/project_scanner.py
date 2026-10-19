"""Lightweight, secret-safe project analysis for IDE context and debugging.

The scanner never sends the whole repository to the model. It returns metadata,
framework hints, likely entry points, route hints, and manifest summaries.
"""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import PurePosixPath

from backend.tools.project_files import ProjectFiles

MAX_FILES = 2000
MAX_MANIFEST_BYTES = 120_000
MANIFEST_NAMES = {
    "package.json", "pyproject.toml", "requirements.txt", "Pipfile", "poetry.lock",
    "Cargo.toml", "go.mod", "pom.xml", "build.gradle", "build.gradle.kts",
    "Gemfile", "composer.json", "pubspec.yaml", "Dockerfile", "docker-compose.yml",
    "vite.config.ts", "vite.config.js", "next.config.js", "next.config.mjs", "next.config.ts",
    "angular.json", "nuxt.config.ts", "svelte.config.js", "tsconfig.json",
}
EXT_LANG = {
    ".py": "Python", ".pyw": "Python", ".pyi": "Python stubs",
    ".js": "JavaScript", ".mjs": "JavaScript", ".cjs": "JavaScript", ".jsx": "JavaScript/JSX",
    ".ts": "TypeScript", ".tsx": "TypeScript/TSX",
    ".html": "HTML", ".htm": "HTML", ".css": "CSS", ".scss": "SCSS", ".sass": "Sass", ".vue": "Vue SFC", ".svelte": "Svelte",
    ".java": "Java", ".kt": "Kotlin", ".kts": "Kotlin script", ".go": "Go", ".rs": "Rust", ".php": "PHP", ".rb": "Ruby", ".cs": "C#", ".sql": "SQL", ".dart": "Dart", ".swift": "Swift",
    ".c": "C", ".h": "C/C++ header", ".cc": "C++", ".cpp": "C++", ".cxx": "C++", ".hh": "C++ header", ".hpp": "C++ header", ".hxx": "C++ header",
    ".sh": "Shell", ".bash": "Shell", ".ps1": "PowerShell", ".psm1": "PowerShell",
    ".json": "JSON", ".jsonc": "JSONC", ".toml": "TOML", ".yaml": "YAML", ".yml": "YAML", ".xml": "XML", ".xsl": "XML", ".xslt": "XML", ".svg": "SVG/XML",
    ".graphql": "GraphQL", ".gql": "GraphQL", ".proto": "Protocol Buffers", ".ex": "Elixir", ".exs": "Elixir", ".erl": "Erlang", ".hrl": "Erlang", ".clj": "Clojure", ".cljs": "ClojureScript", ".scala": "Scala", ".sc": "Scala", ".r": "R", ".lua": "Lua", ".pl": "Perl", ".pm": "Perl", ".hs": "Haskell", ".lhs": "Haskell",
}
SKIP_PARTS = {"node_modules", ".git", ".venv", "venv", "dist", "build", "target", "__pycache__", ".agent"}


def _read(pf: ProjectFiles, rel: str, limit: int = MAX_MANIFEST_BYTES) -> str:
    try:
        text = pf.read(rel)
        return text[:limit]
    except (OSError, ValueError, UnicodeError):
        return ""


def _manifest_summary(pf: ProjectFiles, files: list[str]) -> dict:
    summaries: dict[str, dict] = {}
    for name in sorted({PurePosixPath(f).name for f in files} & MANIFEST_NAMES):
        path = next((f for f in files if PurePosixPath(f).name == name and f.count("/") <= 1), None)
        if not path:
            path = next((f for f in files if PurePosixPath(f).name == name), None)
        if not path:
            continue
        text = _read(pf, path)
        if not text:
            continue
        row: dict = {"path": path}
        if name == "package.json":
            try:
                data = json.loads(text)
                if isinstance(data, dict):
                    row.update({
                        "name": str(data.get("name", ""))[:100],
                        "scripts": sorted(str(k) for k in (data.get("scripts") or {}).keys())[:40]
                            if isinstance(data.get("scripts"), dict) else [],
                        "dependencies": sorted(set((data.get("dependencies") or {}).keys()) |
                                               set((data.get("devDependencies") or {}).keys()))[:100]
                            if isinstance(data.get("dependencies"), dict) and isinstance(data.get("devDependencies") or {}, dict)
                            else sorted((data.get("dependencies") or {}).keys())[:100]
                            if isinstance(data.get("dependencies"), dict) else [],
                    })
            except (ValueError, TypeError):
                row["invalid_json"] = True
        elif name in ("requirements.txt", "Pipfile"):
            row["dependencies"] = [x.strip().split(";")[0].split("#")[0].strip()[:100]
                                   for x in text.splitlines() if x.strip() and not x.lstrip().startswith(("#", "-"))][:80]
        elif name == "pyproject.toml":
            row["declares"] = [x for x in ("[project]", "[tool.poetry]", "[tool.pytest.ini_options]", "[tool.ruff") if x in text][:10]
        summaries[path] = row
    return summaries


def scan(pf: ProjectFiles) -> dict:
    files = pf.tree()[:MAX_FILES]
    visible_files = [x for x in files if not (set(PurePosixPath(x).parts) & SKIP_PARTS)]
    ext_counts = Counter(PurePosixPath(x).suffix.lower() for x in visible_files)
    languages = Counter(EXT_LANG[e] for e, n in ext_counts.items() if n and e in EXT_LANG)
    manifests = _manifest_summary(pf, visible_files)
    all_deps = {d.lower() for m in manifests.values() for d in m.get("dependencies", [])}
    # `dependencies` in package.json may include versions only in source manifest, not response.
    package_text = "\n".join(_read(pf, p) for p in manifests if PurePosixPath(p).name == "package.json")
    frameworks = []
    for needle, label in (
        ('"react"', "React"), ('"next"', "Next.js"), ('"vue"', "Vue"), ('"@angular/core"', "Angular"),
        ('"svelte"', "Svelte"), ('"express"', "Express"), ('"fastapi"', "FastAPI"),
        ('"django"', "Django"), ('"flask"', "Flask"), ('"@nestjs/core"', "NestJS"),
        ('"firebase"', "Firebase"), ('"prisma/client"', "Prisma"), ('"mongoose"', "Mongoose"),
    ):
        if needle in package_text.lower() or any(needle.strip('"') in d for d in all_deps):
            frameworks.append(label)
    if any(PurePosixPath(x).name == "requirements.txt" for x in visible_files):
        py_text = "\n".join(_read(pf, x, 50_000).lower() for x in visible_files
                              if PurePosixPath(x).name in ("requirements.txt", "pyproject.toml", "Pipfile"))
        for needle, label in (("fastapi", "FastAPI"), ("django", "Django"), ("flask", "Flask"), ("pytest", "pytest")):
            if needle in py_text and label not in frameworks:
                frameworks.append(label)
    managers = []
    for name, label in (("package-lock.json", "npm"), ("pnpm-lock.yaml", "pnpm"), ("yarn.lock", "Yarn"),
                        ("bun.lockb", "Bun"), ("bun.lock", "Bun"), ("poetry.lock", "Poetry"),
                        ("Pipfile.lock", "Pipenv"), ("requirements.txt", "pip"), ("Cargo.lock", "Cargo"),
                        ("go.sum", "Go modules"), ("pnpm-workspace.yaml", "pnpm workspaces")):
        if any(PurePosixPath(x).name == name for x in visible_files):
            managers.append(label)
    if "package.json" in manifests and not any(m in managers for m in ("npm", "pnpm", "Yarn", "Bun")):
        managers.append("npm (inferred from package.json)")

    entry_patterns = (
        "src/main.tsx", "src/main.ts", "src/main.jsx", "src/main.js", "src/App.tsx", "src/App.jsx",
        "app/page.tsx", "app/page.jsx", "pages/index.tsx", "pages/index.jsx", "index.html",
        "main.py", "app.py", "backend/main.py", "manage.py", "src/main/java", "cmd/main.go",
        "Cargo.toml", "pubspec.yaml",
    )
    entry_points = [x for x in visible_files if any(x == pat or (pat.endswith("/") and x.startswith(pat)) for pat in entry_patterns)]
    if not entry_points:
        entry_points = [x for x in visible_files[:40] if PurePosixPath(x).name.lower() in
                        {"main.py", "app.py", "index.html", "main.ts", "main.tsx", "app.ts", "app.tsx", "server.js", "index.js"}]
    routes, endpoints = [], []
    frontend_route = re.compile(r"(?:path\s*=\s*['\"]([^'\"]+)['\"]|path:\s*['\"]([^'\"]+)['\"])")
    api_route = re.compile(r"(?:@?(?:app|router)\.)(get|post|put|patch|delete|api_route)\s*\(\s*['\"]([^'\"]+)['\"]", re.I)
    frontend_source = [x for x in visible_files if x.endswith((".tsx", ".jsx", ".ts", ".js", ".vue", ".svelte"))]
    backend_source = [x for x in visible_files if x.endswith((".py", ".js", ".ts"))]
    for rel in frontend_source[:200]:
        # Only likely route files, with a small bounded scan per file.
        if not any(k in rel.lower() for k in ("route", "router", "page", "app.")) and PurePosixPath(rel).name not in ("App.tsx", "App.jsx", "App.ts", "App.js"):
            continue
        txt = _read(pf, rel, 30_000)
        for m in frontend_route.finditer(txt):
            value = m.group(1) or m.group(2)
            if value and value not in routes:
                routes.append(value)
                if len(routes) >= 80: break
        if PurePosixPath(rel).name in ("page.tsx", "page.jsx") and rel.startswith("app/"):
            slug = "/" + "/".join(PurePosixPath(rel).parts[1:-1])
            if slug not in routes: routes.append(slug or "/")
    for rel in backend_source[:250]:
        txt = _read(pf, rel, 40_000)
        for m in api_route.finditer(txt):
            item = {"method": m.group(1).upper(), "path": m.group(2), "file": rel}
            if item not in endpoints:
                endpoints.append(item)
                if len(endpoints) >= 100: break
        if len(endpoints) >= 100: break
    return {
        "project_id": pf.root.name,
        "root_name": pf.root.name,
        "files_scanned": len(visible_files),
        "truncated": len(files) >= MAX_FILES,
        "languages": [{"name": k, "files": v} for k, v in languages.most_common()],
        "frameworks": sorted(set(frameworks)),
        "package_managers": managers,
        "entry_points": sorted(set(entry_points))[:30],
        "routes": sorted(set(routes))[:80],
        "api_endpoints": endpoints,
        "manifests": manifests,
        "file_extensions": [{"extension": ext or "(no extension)", "files": n} for ext, n in ext_counts.most_common(20)],
        "warnings": (["The file scan reached its configured limit; the summary may be incomplete."] if len(files) >= MAX_FILES else []),
    }

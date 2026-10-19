"""Local, dependency-free retrieval over the user's bundled full-stack language guides.

The complete source guides stay in backend/knowledge/guides. Only the most relevant
small excerpts are added to a model request so small local models don't receive every
page of every guide at once. Actual project manifests, compiler output, and tests take
precedence over an example in a guide.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from functools import lru_cache
from typing import Any, Iterable

GUIDE_DIR = Path(__file__).resolve().parent / "guides"

# Each guide is one of the documents provided by the user. Aliases are intentionally
# explicit; the retriever never pretends a guide exists for an undocumented technology.
GUIDES: dict[str, dict[str, Any]] = {
    "ecommerce_shopping_reference_guide.md": {
        "title": "E-commerce and shopping website engineering playbook (based on supplied reference source)",
        "aliases": (
            "ecommerce", "e-commerce", "online store", "shopping website", "shopping site", "shopping cart",
            "cart", "checkout", "product catalog", "product details", "product listing", "wishlist", "wish list",
            "order tracking", "order history", "order management", "admin products", "admin orders", "inventory",
            "product upload", "payment webhook", "upi", "utr", "firebase shopping", "storefront", "buy now",
            "product reviews", "review eligibility", "shipping address", "address book", "shopping-main",
            "commerce site", "store admin", "shopping reference", "cart persistence", "product stock",
        ),
    },
    "mongodb_complete_syntax_functions_full_stack_guide.md": {
        "title": "MongoDB full-stack guide",
        "aliases": ("mongodb", "mongo db", "mongosh", "mongoose", "bson", "aggregation pipeline", "document database", "nosql"),
    },
    "angular_typescript_full_stack_complete_guide.md": {
        "title": "Angular + TypeScript guide",
        "aliases": ("angular", "typescript", "type script", "rxjs", "signal input", "angular cli", "ng generate", "template-driven", "reactive forms", "angular component", "angular service"),
    },
    "css_complete_3d_4d_animations_full_stack_guide.md": {
        "title": "CSS, responsive design, 2D/3D and time-based animation guide",
        "aliases": ("css", "scss", "sass", "stylesheet", "responsive design", "keyframes", "animation", "3d", "4d", "transform", "grid", "flexbox"),
    },
    "django_complete_syntax_functions_full_stack_guide.md": {
        "title": "Django + Python guide",
        "aliases": ("django", "django orm", "manage.py", "modelform", "queryset", "django rest framework", "python django"),
    },
    "docker_complete_syntax_commands_full_stack_guide.md": {
        "title": "Docker and Docker Compose guide",
        "aliases": ("docker", "dockerfile", "docker compose", "compose.yaml", "container", "containerize", "buildkit", "volume mount"),
    },
    "flask_fastapi_complete_syntax_functions_guide.md": {
        "title": "Flask + FastAPI + Python web guide",
        "aliases": ("fastapi", "flask", "pydantic", "uvicorn", "asgi", "wsgi", "python api", "python backend", "dependency injection"),
    },
    "html_complete_full_stack_guide.md": {
        "title": "HTML and semantic web structure guide",
        "aliases": ("html", "html5", "semantic html", "dom", "form markup", "accessibility", "aria", "html form", "doctype"),
    },
    "javascript_full_stack_complete_guide.md": {
        "title": "JavaScript, Node.js, Express and browser APIs guide",
        "aliases": ("javascript", "node.js", "nodejs", "express", "npm", "promise", "async await", "fetch api", "jsx", "tsx", "vite", "frontend", "backend javascript"),
    },
    "fullstack_web_development_complete_concepts_tools_functions_guide.md": {
        "title": "Full-stack web development concepts and tools guide",
        "aliases": ("full-stack web development", "fullstack web development", "full-stack application", "full stack application", "full stack web", "frontend backend database", "web application architecture", "web development tools", "website", "web app", "end-to-end web", "api architecture", "deployment workflow", "choose a stack", "php", "laravel", "redis", "git workflow", "github actions", "continuous integration", "continuous deployment", "rest api design", "oauth", "csrf", "cors", "nginx", "linux server", "web security", "websocket", "openapi", "graphql", "server-side rendering", "rate limiting"),
    },
    "nestjs_backend_complete_syntax_functions_guide.md": {
        "title": "NestJS + TypeScript backend guide",
        "aliases": ("nestjs", "nest js", "@nestjs", "nest cli", "nestjs cli", "nestjs controller", "nestjs service", "nestjs guard", "nestjs interceptor", "nestjs dto", "typeorm nestjs", "prisma nestjs"),
    },
    "python_for_ai_complete_syntax_functions_guide.md": {
        "title": "Python language and AI engineering guide",
        "aliases": ("python", "python 3", "python for ai", "machine learning", "deep learning", "pytorch", "tensorflow", "scikit-learn", "large language model", "llm", "rag", "retrieval augmented generation", "transformers", "pandas", "numpy", "jupyter", "langchain", "vector database", "embeddings", "ai agent"),
    },
    "react_js_typescript_full_stack_complete_guide.md": {
        "title": "React + TypeScript full-stack guide",
        "aliases": ("react", "react.js", "reactjs", "react typescript", "react hooks", "react dom", "react router", "react component", "react frontend", "useState", "useEffect", "tsx", "jsx"),
    },
    "rust_backend_complete_syntax_functions_guide.md": {
        "title": "Rust + Axum backend guide",
        "aliases": ("rust", "cargo", "axum", "tokio", "sqlx", "actix-web", "actix web", "rust backend", "rust api", "borrow checker", "ownership and borrowing"),
    },
    "springboot_java_full_stack_complete_guide.md": {
        "title": "Java + Spring Boot backend guide",
        "aliases": ("spring boot", "springboot", "spring mvc", "spring security", "spring data jpa", "spring framework", "java backend", "java language", "maven java", "gradle java", "jpa", "hibernate", "restcontroller", "spring starter"),
    },
    "sql_complete_full_stack_syntax_functions_guide.md": {
        "title": "SQL, relational database design and query guide",
        "aliases": ("sql", "postgresql", "postgres", "mysql", "sqlite", "sql server", "t-sql", "oracle sql", "query plan", "database schema", "stored procedure", "sql injection", "database migration", "database index", "relational database", "joins", "sql query"),
    },
    "tailwind_css_complete_syntax_utilities_guide.md": {
        "title": "Tailwind CSS utilities and responsive UI guide",
        "aliases": ("tailwind", "tailwind css", "tailwindcss", "utility-first css", "utility first css", "tailwind v4", "tailwind v3", "@theme", "tailwind variants", "responsive utility classes"),
    },
}


@dataclass(frozen=True)
class Chunk:
    guide: str
    title: str
    heading: str
    text: str
    terms: frozenset[str]

_WORD_RE = re.compile(r"[a-z][a-z0-9_+#.-]{1,}", re.I)
_HEADING_RE = re.compile(r"^(#{1,4})\s+(.+?)\s*$", re.M)


def _tokens(text: str) -> set[str]:
    return {x.lower().strip("._-+") for x in _WORD_RE.findall(text or "") if len(x) > 1}


def _split_long_section(text: str, limit: int = 2200) -> list[str]:
    """Split long guide sections on paragraphs, then lines, retaining all source text."""
    if len(text) <= limit:
        return [text.strip()] if text.strip() else []
    paras = re.split(r"\n\s*\n", text)
    result: list[str] = []
    current = ""
    for para in paras:
        if len(para) > limit:
            if current.strip():
                result.append(current.strip())
                current = ""
            line_group = ""
            for line in para.splitlines():
                if line_group and len(line_group) + len(line) + 1 > limit:
                    result.append(line_group.strip())
                    line_group = ""
                line_group += ("\n" if line_group else "") + line
            if line_group.strip():
                result.append(line_group.strip())
            continue
        if current and len(current) + len(para) + 2 > limit:
            result.append(current.strip())
            current = para
        else:
            current += ("\n\n" if current else "") + para
    if current.strip():
        result.append(current.strip())
    return result


@lru_cache(maxsize=1)
def _chunks() -> tuple[Chunk, ...]:
    chunks: list[Chunk] = []
    for filename, meta in GUIDES.items():
        path = GUIDE_DIR / filename
        if not path.is_file():
            continue
        source = path.read_text(encoding="utf-8", errors="replace")
        headings = list(_HEADING_RE.finditer(source))
        if not headings:
            parts = [(meta["title"], source)]
        else:
            parts = []
            for i, h in enumerate(headings):
                end = headings[i + 1].start() if i + 1 < len(headings) else len(source)
                title = re.sub(r"`", "", h.group(2)).strip()
                body = source[h.end():end].strip()
                if body:
                    parts.append((title, body))
        for heading, body in parts:
            for number, segment in enumerate(_split_long_section(body), 1):
                heading_path = heading if number == 1 else f"{heading} (part {number})"
                chunks.append(Chunk(filename, meta["title"], heading_path, segment, frozenset(_tokens(heading_path + " " + segment))))
    return tuple(chunks)


def _flatten(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return " ".join(f"{k} {_flatten(v)}" for k, v in value.items())
    if isinstance(value, (list, tuple, set)):
        return " ".join(_flatten(x) for x in value)
    return str(value)


def _alias_matches(alias: str, text: str) -> bool:
    """Match single-word technologies on word boundaries (React must not match reactive)."""
    value = alias.lower().strip()
    if re.fullmatch(r"[a-z0-9]+", value):
        return bool(re.search(rf"(?<![a-z0-9]){re.escape(value)}(?![a-z0-9])", text, re.I))
    return value in text


def _detected_guides(text: str, task: str, file_path: str = "") -> list[str]:
    normalized = re.sub(r"[^a-z0-9.+#/_ -]+", " ", (text + " " + file_path).lower())
    selected: list[str] = []
    for filename, meta in GUIDES.items():
        if any(_alias_matches(alias, normalized) for alias in meta["aliases"]):
            selected.append(filename)

    path = file_path.lower().replace("\\", "/")
    basename = Path(path).name
    if basename in {"dockerfile", "containerfile"} or path.endswith((".dockerfile", "compose.yml", "compose.yaml", "docker-compose.yml", "docker-compose.yaml")):
        selected.append("docker_complete_syntax_commands_full_stack_guide.md")
    if path.endswith((".html", ".htm", ".svg")):
        selected.append("html_complete_full_stack_guide.md")
    if path.endswith((".css", ".scss", ".sass")) or any(x in normalized for x in ("style", "layout", "animation", "responsive")):
        selected.append("css_complete_3d_4d_animations_full_stack_guide.md")
    if path.endswith((".js", ".mjs", ".cjs", ".jsx", ".ts", ".tsx")):
        selected.append("javascript_full_stack_complete_guide.md")
    if path.endswith((".jsx", ".tsx")):
        selected.append("react_js_typescript_full_stack_complete_guide.md")
    if path.endswith((".ts", ".tsx")):
        # This guide supplies general TypeScript syntax; Angular-specific sections are filtered below unless selected.
        selected.append("angular_typescript_full_stack_complete_guide.md")
    if path.endswith(".py"):
        selected.append("python_for_ai_complete_syntax_functions_guide.md")
    if path.endswith(".rs") or basename == "cargo.toml":
        selected.append("rust_backend_complete_syntax_functions_guide.md")
    if path.endswith(".java") or basename in {"pom.xml", "build.gradle", "build.gradle.kts"}:
        selected.append("springboot_java_full_stack_complete_guide.md")
    if path.endswith((".sql", ".prisma")) or "/migrations/" in path:
        selected.append("sql_complete_full_stack_syntax_functions_guide.md")
    if basename == "tailwind.config.js" or basename == "tailwind.config.ts" or "tailwind" in path:
        selected.append("tailwind_css_complete_syntax_utilities_guide.md")
    if basename == "nest-cli.json" or "nestjs" in path or "nest-cli" in path:
        selected.append("nestjs_backend_complete_syntax_functions_guide.md")
    if path.endswith((".dockerfile", "compose.yml", "compose.yaml")) or "docker" in path:
        selected.append("docker_complete_syntax_commands_full_stack_guide.md")

    # General front-end context is helpful for section generation, but framework-specific
    # guides are selected first and all excerpts remain bounded to the task budget.
    frontend_defaults = (
        "html_complete_full_stack_guide.md",
        "css_complete_3d_4d_animations_full_stack_guide.md",
        "javascript_full_stack_complete_guide.md",
    )
    if task in {"section", "frontend_repair"}:
        selected.extend(frontend_defaults)
    elif task == "blueprint" and not selected:
        selected.extend(("fullstack_web_development_complete_concepts_tools_functions_guide.md",) + frontend_defaults)

    # A plain Python request uses the Python language/AI guide. Framework-specific
    # requests still retain their matching Django/FastAPI/NestJS/etc. references.
    if re.search(r"\bpython\b", normalized):
        selected.append("python_for_ai_complete_syntax_functions_guide.md")

    selected = list(dict.fromkeys(x for x in selected if x in GUIDES))
    frontend_allowed = {
        "html_complete_full_stack_guide.md",
        "css_complete_3d_4d_animations_full_stack_guide.md",
        "javascript_full_stack_complete_guide.md",
        "angular_typescript_full_stack_complete_guide.md",
        "react_js_typescript_full_stack_complete_guide.md",
        "tailwind_css_complete_syntax_utilities_guide.md",
        "ecommerce_shopping_reference_guide.md",
    }
    # Section generation is always a UI task. For explicit frontend repair/edit tasks,
    # restrict references to frontend material. A generic `edit` against backend file paths
    # is intentionally allowed to retrieve backend/database/language guides.
    path_suffix = Path(path).suffix.lower()
    is_ui_edit = (
        task == "edit"
        and (path_suffix in {".html", ".htm", ".css", ".scss", ".sass", ".jsx", ".tsx"}
             or any(term in normalized for term in ("frontend", "react component", "css style", "tailwind", "jsx", "tsx")))
        and not any(term in normalized for term in ("nestjs", "spring boot", "django", "fastapi", "flask", "rust backend", "sql migration"))
    )
    if task in {"section", "frontend_repair"} or is_ui_edit:
        selected = [filename for filename in selected if filename in frontend_allowed]
    return selected


def retrieve_knowledge(task: str, query: str = "", technologies: Any = None, file_path: str = "", max_chars: int = 2200) -> str:
    """Return bounded, ranked excerpts from the supplied guides; never load every guide at once."""
    budget = max(0, min(int(max_chars or 0), 6000))
    if budget < 180:
        return ""
    task = str(task or "repair").lower()
    text = f"{query or ''}\n{_flatten(technologies)}\n{file_path}"
    selected = _detected_guides(text, task, file_path)
    if not selected:
        return ""

    # Prefer guides with the most explicit technology mentions. At most four source
    # guides are retrieved per request so focused guidance has enough room to be useful.
    normalized = text.lower()
    def guide_priority(filename: str) -> int:
        return sum(1 for alias in GUIDES[filename]["aliases"] if _alias_matches(alias, normalized))
    selected = sorted(selected, key=guide_priority, reverse=True)[:min(4, max(1, budget // 430))]
    selected_set = set(selected)
    qterms = _tokens(text)
    angular_requested = bool(re.search(r"\bangular\b", text, re.I))
    scored: list[tuple[float, Chunk]] = []
    for chunk in _chunks():
        if chunk.guide not in selected_set:
            continue
        if chunk.guide == "angular_typescript_full_stack_complete_guide.md" and not angular_requested:
            # This source combines TypeScript fundamentals with Angular. If Angular is not
            # selected, only include language-level TypeScript sections, never Angular APIs.
            if not re.search(r"typescript essentials|typescript syntax reference|variables and primitive types|arrays and tuples|objects, type aliases|union, intersection|functions and return types|narrowing and type guards|generics|classes, access modifiers|imports and exports|async typescript", chunk.heading, re.I):
                continue
        overlap = len(qterms & chunk.terms)
        heading_overlap = len(qterms & _tokens(chunk.heading))
        score = overlap * 0.35 + heading_overlap * 2.7
        lowered = chunk.heading.lower()
        if task in {"repair", "frontend_repair", "edit", "verification"} and any(
            x in lowered for x in ("common errors", "troubleshooting", "security", "testing", "debugging", "best practices")
        ):
            score += 1.25
        scored.append((score, chunk))
    scored.sort(key=lambda pair: pair[0], reverse=True)
    if not scored:
        return ""

    # Allocate room to one best excerpt per guide, clipping on a line boundary. This
    # prevents a 2 KB guide subsection from crowding out every other selected technology.
    guide_budget = max(140, (budget - 105 * len(selected)) // max(1, len(selected)))
    guide_budget = min(650, guide_budget)
    chosen: list[tuple[Chunk, str]] = []
    seen_guides: set[str] = set()
    used = 0

    def render_header(chunk: Chunk) -> str:
        return f"[{chunk.title} | {chunk.heading} | source: {chunk.guide}]\n"

    def trim(text_to_trim: str, limit: int) -> str:
        if len(text_to_trim) <= limit:
            return text_to_trim.strip()
        candidate = text_to_trim[:limit]
        # Prefer a complete line/paragraph where practical, but keep a meaningful excerpt.
        split_at = max(candidate.rfind("\n"), candidate.rfind(" "))
        if split_at >= int(limit * 0.65):
            candidate = candidate[:split_at]
        return candidate.rstrip()

    for _, chunk in scored:
        if chunk.guide in seen_guides:
            continue
        header = render_header(chunk)
        remaining = budget - used - len(header) - 2
        body_budget = min(guide_budget, remaining)
        if body_budget < 100:
            continue
        excerpt = trim(chunk.text, body_budget)
        if not excerpt:
            continue
        chosen.append((chunk, excerpt))
        used += len(header) + len(excerpt) + 2
        seen_guides.add(chunk.guide)
        if seen_guides >= selected_set or used >= budget:
            break

    # If room remains, add one additional high-relevance topic from an already-selected guide.
    for _, chunk in scored:
        if len(chosen) >= 5 or used >= budget - 140:
            break
        if any(c.guide == chunk.guide and c.heading == chunk.heading for c, _ in chosen):
            continue
        header = render_header(chunk)
        remaining = budget - used - len(header) - 2
        if remaining < 100:
            break
        excerpt = trim(chunk.text, min(remaining, 420))
        if excerpt:
            chosen.append((chunk, excerpt))
            used += len(header) + len(excerpt) + 2

    return "\n\n".join(render_header(chunk) + excerpt for chunk, excerpt in chosen)[:budget]


def enrich_user_context(task: str, user: str, max_chars: int = 1800, file_path: str = "") -> str:
    """Append guide excerpts to a model user message for coding/planning/repair requests."""
    query = str(user or "")
    if not query.strip():
        return query
    header = (
        "\n\nREFERENCE KNOWLEDGE (relevant bundled guide excerpts):\n"
        "Use as references, not blind copy. Project manifests, installed versions, neighboring code, diagnostics, and tests take precedence. Never invent imports/APIs or mix incompatible major versions. Make minimal patches and preserve working behavior. Run actual checks and report passed/failed/skipped honestly; guides are not exhaustive. If Angular is not selected, use only TypeScript fundamentals from its guide.\n"
    )
    # max_chars is the entire added knowledge budget, not just the excerpts.
    excerpt_budget = max(0, min(int(max_chars or 0) - len(header), 5600))
    refs = retrieve_knowledge(task=task, query=query, file_path=file_path, max_chars=excerpt_budget)
    if not refs:
        return query
    return query + header + refs

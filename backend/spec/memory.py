"""Project memory: the decisions, conventions and contracts of ONE project, stored in `.agent/memory.json`.

Not shared between projects, never holds secrets, and `check()` compares it with the real repository so it cannot
silently drift from the code. Zero LLM tokens.
"""
import hashlib
import json
from datetime import datetime, timezone

from backend.stack import catalog as C
from backend.stack import resolver
from backend.spec import compose as B
from backend.tools.project_files import ProjectFiles
from backend.tools.redact import redact

FILE = ".agent/memory.json"
MAX_DECISIONS = 40
NAMING = {"js": "camelCase variables, PascalCase components, kebab-case files", "ts": "camelCase variables, PascalCase types/components",
          "py": "snake_case modules/functions, PascalCase classes", "java": "PascalCase classes, camelCase methods, lowercase packages",
          "cs": "PascalCase for public members", "php": "PSR-12 (PascalCase classes, camelCase methods)", "go": "gofmt, exported names in PascalCase"}
# (install, dev, build, test); None = not applicable. Backend generators (phase 3+) follow these exact commands.
FRONTEND_CMDS = {"html": (None, "npx serve .", None, None), "react": ("npm install", "npm run dev", "npm run build", None),
                 "angular": ("npm install", "npm start", "npm run build", "npm test"), "next": ("npm install", "npm run dev", "npm run build", "npm test"),
                 "vue": ("npm install", "npm run dev", "npm run build", "npm test"), "nuxt": ("npm install", "npm run dev", "npm run build", "npm test"),
                 "svelte": ("npm install", "npm run dev", "npm run build", "npm test"), "sveltekit": ("npm install", "npm run dev", "npm run build", "npm test"),
                 "solid": ("npm install", "npm run dev", "npm run build", "npm test")}
BACKEND_CMDS = {"express": ("npm install", "npm run dev", "npm run build", "npm test"), "nestjs": ("npm install", "npm run start:dev", "npm run build", "npm test"),
                "fastapi": ("pip install -r requirements.txt", "python -m app", None, "python -m pytest"),
                "flask": ("pip install -r requirements.txt", "python -m app", None, "python -m pytest"),
                "django": ("pip install -r requirements.txt", "python -m app", None, "python -m pytest"),
                "spring": (None, "./mvnw spring-boot:run", "./mvnw package", "./mvnw test"), "aspnet": ("dotnet restore", "dotnet run", "dotnet build", "dotnet test"),
                "laravel": ("composer install", "php artisan serve", None, "php artisan test"), "go": ("go mod download", "go run ./cmd/server", "go build ./...", "go test ./...")}
LANG_OF = {"express": "js", "nestjs": "ts", "fastapi": "py", "flask": "py", "django": "py", "spring": "java", "aspnet": "cs", "laravel": "php", "go": "go"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _cmds(table: dict, key: str, status: str) -> dict:
    inst, dev, build, test = table.get(key, (None,) * 4)
    return {"install": inst, "dev": dev, "build": build, "test": test, "verified": status == C.READY}


def load(pid: str) -> dict | None:
    try:
        return json.loads(ProjectFiles(pid).read(FILE))
    except (OSError, ValueError):
        return None


def _save(pid: str, mem: dict) -> None:
    ProjectFiles(pid).write(FILE, json.dumps(mem, indent=1))


def _top(paths: list[str]) -> list[str]:
    return sorted({(p.split("/")[0] + "/") if "/" in p else p for p in paths})


def _files_digest(paths: list[str]) -> str:
    return hashlib.md5("\n".join(sorted(paths)).encode()).hexdigest()[:10]


def decide(mem: dict, topic: str, decision: str, reason: str = "", by: str = "agent") -> bool:
    """Append a decision unless the latest one for this topic is identical. Returns True when something was recorded."""
    log = mem.setdefault("decisions", [])
    last = next((d for d in reversed(log) if d["topic"] == topic), None)
    if last and last["decision"] == decision:
        return False
    log.append({"at": _now(), "topic": topic, "decision": redact(decision)[:160], "reason": redact(reason)[:200], "by": by})
    del log[:-MAX_DECISIONS]
    return True


def refresh(state, spec: dict, by: str = "agent") -> dict:
    """Rebuild memory from the real state + spec (keeps the decision history). Called by the pipeline and the API."""
    pf = ProjectFiles(state.project_id)
    old = load(state.project_id) or {}
    stack = B.stack_of(state)
    cfg = state.stack_config or {}
    src, why = cfg.get("sources", {}), cfg.get("reasons", {})
    mem = {"version": 1, "updated": _now(), "decisions": old.get("decisions", [])}
    for f in C.FIELDS:
        v = stack.get(f)
        if v and (v != "none" or (old.get("stack") or {}).get(f) not in (None, "none", v)):
            decide(mem, f, resolver.label(f, v), why.get(f, ""), "user" if src.get(f) == "user" else by)
    if spec.get("overrides"):
        decide(mem, "spec-overrides", ", ".join(sorted(spec["overrides"])) + " edited by the user", "", "user")
    be = stack.get("backend") or "none"
    be_status = C.status("backend", be, stack)
    tree = pf.tree()
    mem.update({
        "stack": stack, "stack_summary": resolver.summary(stack) if stack.get("frontend") in C.FRONTEND else "", "mode": cfg.get("mode", "legacy"),
        "conventions": {
            "structure": {"actual": _top(tree), "planned": [d for d, on in (("backend/", be != "none"), ("database/", spec["data"]["enabled"] and be != "none"),
                                                                           ("ai-service/", stack.get("ai") == "python-service")) if on and d not in _top(tree)]},
            "naming": {"frontend": NAMING.get(stack.get("frontend_lang") or "js", ""), **({"backend": NAMING[LANG_OF[be]]} if be in LANG_OF else {})},
            "commands": {"frontend": _cmds(FRONTEND_CMDS, stack.get("frontend", "html"), C.status("frontend", stack.get("frontend", "html"), stack)),
                         **({"backend": _cmds(BACKEND_CMDS, be, be_status)} if be in BACKEND_CMDS else {})}},
        "design": {"layout": state.layout, "tokens": {k: str(v)[:40] for k, v in list((state.design or {}).items())[:12]}},
        "api": {"base": spec["api"]["base"], "routes": len(spec["api"]["routes"]), "digest": spec["api"]["digest"]},
        "spec": {"hash": spec["hash"], "kind": spec["kind"], "pages": len(spec["pages"]), "entities": len(spec["data"]["entities"])},
        "testing": spec["testing"], "deployment": spec["deployment"],
        "files": {"count": len(tree), "digest": _files_digest(tree), "paths": tree[:300]},
    })
    _save(state.project_id, mem)
    return mem


def check(state) -> dict:
    """Compare memory with the actual repository. Returns {consistent, drift:[{kind, msg}]}."""
    pf = ProjectFiles(state.project_id)
    mem = load(state.project_id)
    if not mem:
        return {"consistent": False, "drift": [{"kind": "missing", "msg": "No project memory yet."}]}
    drift, stack = [], B.stack_of(state)
    if mem.get("stack") != stack:
        changed = sorted(f for f in set(mem.get("stack") or {}) | set(stack) if (mem.get("stack") or {}).get(f) != stack.get(f))
        drift.append({"kind": "stack", "msg": f"Memory stack differs from the project stack ({', '.join(changed)})."})
    spec = B.load(state.project_id)
    if not spec:
        drift.append({"kind": "spec", "msg": "No app spec stored."})
    else:
        if spec["hash"] != B._inputs_hash(state.brief, stack, spec.get("overrides") or {}):
            drift.append({"kind": "spec", "msg": "The app spec is stale (brief or stack changed since it was built)."})
        if mem.get("spec", {}).get("hash") != spec["hash"]:
            drift.append({"kind": "spec", "msg": "Memory refers to a different spec version."})
    tree = pf.tree()
    listed = set((mem.get("files") or {}).get("paths", []))
    if len(listed) < 300:                                           # path list is capped: only compare when complete
        gone, new = sorted(listed - set(tree)), sorted(set(tree) - listed)
        if gone:
            drift.append({"kind": "files", "msg": f"{len(gone)} file(s) in memory no longer exist (e.g. {gone[0]})."})
        if new:
            drift.append({"kind": "files", "msg": f"{len(new)} new file(s) not in memory (e.g. {new[0]})."})
    marker = {"react": "package.json", "html": "index.html"}.get(stack.get("frontend"))
    if marker and state.sections_done and marker not in tree:
        drift.append({"kind": "frontend", "msg": f"Frontend is {stack['frontend']} but {marker} is missing."})
    return {"consistent": not drift, "drift": drift}

"""Pipeline stage: spec + stack -> backend files in <project>/backend. Zero LLM tokens, deterministic.

User edits are never overwritten: a file is rewritten only if it is new or still identical to what this generator wrote last time.
"""
import hashlib
import json

from backend.gen import django_gen, express, fastapi_gen, flask_gen, model, nest, project, spring_gen, env_contract
from backend.stack import catalog

GENERATORS = {"express": express, "fastapi": fastapi_gen, "flask": flask_gen, "nestjs": nest, "django": django_gen, "spring": spring_gen}
STATE = ".agent/backend.json"


def coverage(stack: dict | None) -> dict:
    """What this build can generate for a stack. `ready` means every selected backend part has a generator."""
    stack = stack or {}
    b = stack.get("backend") or "none"
    if b == "none":
        return {"backend": "none", "ready": False, "gaps": [], "note": "No backend selected."}
    gaps = catalog.generator_gaps(stack)
    return {"backend": b, "ready": not gaps and b in GENERATORS, "gaps": gaps, "note": ""}


def _h(t: str) -> str:
    return hashlib.sha256(t.encode("utf-8")).hexdigest()[:16]


def _load(pf) -> dict:
    try:
        return json.loads(pf.read(STATE))
    except (OSError, ValueError):
        return {}


def run(pf, spec: dict, stack: dict) -> dict:
    """Generate (or refresh) the backend. Returns a summary; never raises for 'not supported yet', it says why instead."""
    cov = coverage(stack)
    if not cov["ready"]:
        return {"generated": False, "gaps": cov["gaps"], "note": cov["note"]}
    gen = GENERATORS[stack["backend"]]
    m = model.build(spec, stack)
    files = gen.generate(spec, stack, m)
    files.update(project.extras(spec, stack, m))
    # Include public frontend configuration separately from private backend secrets.
    try:
        existing_frontend_env = pf.read(".env.example")
    except (OSError, ValueError):
        existing_frontend_env = ""
    try:
        root_gitignore = pf.read(".gitignore")
    except (OSError, ValueError):
        root_gitignore = ""
    if root_gitignore:
        files.setdefault(".gitignore", root_gitignore)
    files.update(env_contract.enrich_files(files, spec, stack, existing_frontend_env))
    prev = _load(pf).get("hashes", {})
    hashes, written, kept = {}, [], []
    for rel, text in files.items():
        new = _h(text)
        try:
            cur = _h(pf.read(rel))
        except (OSError, ValueError):
            cur = None
        if cur is not None and cur != new and prev.get(rel) != cur:
            kept.append(rel)                       # the user changed this file: keep their version
            hashes[rel] = prev.get(rel, new)
            continue
        if cur != new:
            pf.write(rel, text)
            written.append(rel)
        hashes[rel] = new
    pf.write(STATE, json.dumps({"generator": stack["backend"], "db": m["db"], "hashes": hashes, "routes": m["manifest"],
                                "not_generated": m["not_generated"], "warnings": m["warnings"]}, indent=1))
    return {"generated": True, "generator": stack["backend"], "database": m["db"], "files": len(files), "written": written, "kept": kept,
            "routes": len(m["manifest"]), "not_generated": m["not_generated"], "warnings": m["warnings"],
            "commands": gen.commands(m)}


def status(pf) -> dict:
    """Last generation result for the report / API (reads .agent/backend.json)."""
    s = _load(pf)
    if not s:
        return {"generated": False}
    return {"generated": True, "generator": s["generator"], "db": s["db"], "routes": len(s.get("routes", [])), "files": len(s.get("hashes", {})),
            "not_generated": s.get("not_generated", []), "warnings": s.get("warnings", [])}

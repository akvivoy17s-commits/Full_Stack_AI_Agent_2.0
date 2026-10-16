"""Repo understanding: compact, incremental map of ONE generated project, stored in `.agent/repo_map.json`.

Zero LLM tokens. Unchanged files (same hash) are reused, secrets files are never read, output is size-capped.
"""
import ast
import hashlib
import json
import re
import time
from collections import Counter

from backend.tools.project_files import ProjectFiles
from backend.tools.redact import redact

FILE = ".agent/repo_map.json"
MAX_FILES, MAX_PARSE, MAX_SYM = 400, 60_000, 14
LANG = {".py": "py", ".js": "js", ".jsx": "js", ".mjs": "js", ".cjs": "js", ".ts": "ts", ".tsx": "ts", ".java": "java", ".go": "go",
        ".cs": "cs", ".php": "php", ".html": "html", ".css": "css", ".json": "json", ".md": "md", ".sql": "sql", ".yml": "yaml", ".yaml": "yaml"}
CODE = {"py", "js", "ts", "java", "go", "cs", "php"}
SECRET = re.compile(r"(^|/)(\.env(\..*)?|.*\.(pem|key|p12|pfx)|id_rsa.*|credentials.*\.json)$", re.I)
ENTRY = {"main.py", "__main__.py", "server.js", "app.js", "main.ts", "main.tsx", "main.jsx", "index.html", "manage.py", "main.go", "Program.cs"}
RX_SYM = {"js": r"(?:function|class)\s+([A-Za-z_$][\w$]*)|export\s+(?:const|let|var)\s+([A-Za-z_$][\w$]*)",
          "ts": r"(?:function|class|interface|enum)\s+([A-Za-z_$][\w$]*)|export\s+(?:const|let|var|type)\s+([A-Za-z_$][\w$]*)",
          "java": r"(?:class|interface|enum|record)\s+(\w+)", "cs": r"(?:class|interface|enum|record|struct)\s+(\w+)",
          "go": r"func\s+(?:\([^)]*\)\s*)?(\w+)|type\s+(\w+)\s+(?:struct|interface)", "php": r"(?:function|class|interface|trait)\s+(\w+)"}
RX_IMP = {"js": r"""(?:from\s+|require\(\s*|import\s+)['"]([^'"]+)['"]""", "ts": r"""(?:from\s+|require\(\s*|import\s+)['"]([^'"]+)['"]""",
          "java": r"import\s+(?:static\s+)?([\w.]+);", "go": r"""^\s*(?:import\s+)?"([^"]+)"$""", "cs": r"using\s+([\w.]+);", "php": r"use\s+([\w\\]+);"}


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())


def _py(src: str):
    try:
        t = ast.parse(src)
    except (SyntaxError, ValueError):
        return [], []
    sym = [n.name for n in t.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))]
    imp = []
    for n in ast.walk(t):
        if isinstance(n, ast.Import):
            imp += [a.name for a in n.names]
        elif isinstance(n, ast.ImportFrom):
            imp.append("." * n.level + (n.module or ""))
    return sym, imp


def _parse(lang: str, src: str):
    if lang == "py":
        return _py(src)
    sym = [next((g for g in m if g), "") if isinstance(m, tuple) else m for m in re.findall(RX_SYM.get(lang, r"$^"), src)]
    imp = re.findall(RX_IMP.get(lang, r"$^"), src, re.M)
    return [s for s in sym if s], imp


def _entry(path: str, lang: str, src: str) -> bool:
    base = path.rsplit("/", 1)[-1]
    return base in ENTRY or (lang == "java" and "@SpringBootApplication" in src)


def _manifest(pf: ProjectFiles, path: str) -> dict | None:
    base = path.rsplit("/", 1)[-1]
    try:
        t = pf.read(path, 100_000)
    except (OSError, ValueError):
        return None
    if base == "package.json":
        try:
            j = json.loads(t)
        except ValueError:
            return None
        return {"path": path, "kind": "npm", "name": j.get("name", ""), "scripts": list((j.get("scripts") or {}))[:12],
                "deps": sorted({*(j.get("dependencies") or {}), *(j.get("devDependencies") or {})})[:25]}
    if base == "requirements.txt":
        return {"path": path, "kind": "pip", "deps": [re.split(r"[=<>~\[; ]", l.strip())[0] for l in t.splitlines()
                                                         if l.strip() and not l.startswith("#")][:25]}
    if base == "pom.xml":
        return {"path": path, "kind": "maven", "deps": sorted(set(re.findall(r"<artifactId>([^<]+)</artifactId>", t)))[:25]}
    if base == "go.mod":
        return {"path": path, "kind": "go", "deps": re.findall(r"^\s+([\w./-]+)\s+v", t, re.M)[:25]}
    if base == "composer.json":
        try:
            return {"path": path, "kind": "composer", "deps": sorted((json.loads(t).get("require") or {}))[:25]}
        except ValueError:
            return None
    return None


def _resolve(src: str, imp: str, lang: str, tree: set[str]) -> str | None:
    """Map a local import to a project file (None for packages / unknown)."""
    d = src.rsplit("/", 1)[0] if "/" in src else ""
    if lang in ("js", "ts") and imp.startswith("."):
        parts = [p for p in (d + "/" + imp).split("/") if p]
        out = []
        for p in parts:
            if p == "..":
                if out:
                    out.pop()
            elif p != ".":
                out.append(p)
        base = "/".join(out)
        for c in [base] + [base + e for e in (".ts", ".tsx", ".js", ".jsx", ".mjs")] + [base + "/index" + e for e in (".ts", ".tsx", ".js", ".jsx")]:
            if c in tree:
                return c
    if lang == "py" and imp:
        dots = len(imp) - len(imp.lstrip("."))
        mod = imp.lstrip(".").replace(".", "/")
        pre = "/".join(d.split("/")[:max(0, len(d.split("/")) - (dots - 1))]) if dots and d else ""
        for c in ([f"{pre}/{mod}".strip("/")] if dots else []) or [mod]:
            for t in (c + ".py", c + "/__init__.py"):
                if t in tree:
                    return t
                hit = next((x for x in tree if x.endswith("/" + t)), None) if not dots else None
                if hit:
                    return hit
    return None


def load(pid: str) -> dict | None:
    try:
        return json.loads(ProjectFiles(pid).read(FILE))
    except (OSError, ValueError):
        return None


def _digest(pf: ProjectFiles, paths: list[str]) -> str:
    return hashlib.md5("\n".join(f"{p}:{pf.hash(p)}" for p in sorted(paths)).encode()).hexdigest()[:10]


def _paths(pf: ProjectFiles) -> list[str]:
    return [p for p in pf.tree() if not SECRET.search(p)]


def stale(pid: str) -> bool:
    m, pf = load(pid), ProjectFiles(pid)
    return not m or m.get("digest") != _digest(pf, _paths(pf)[:MAX_FILES])


def build(pid: str, force: bool = False) -> dict:
    """(Re)build the map. Only changed/new files are re-parsed unless force=True."""
    pf = ProjectFiles(pid)
    old = {} if force else (load(pid) or {}).get("files", {})
    allp = _paths(pf)
    paths = allp[:MAX_FILES]
    tree, files, manifests, entries = set(paths), {}, [], []
    for p in paths:
        h = pf.hash(p)
        lang = LANG.get("." + p.rsplit(".", 1)[-1].lower() if "." in p.rsplit("/", 1)[-1] else "", "other")
        o = old.get(p)
        if o and o.get("h") == h:
            files[p] = o
        else:
            e = {"h": h, "l": lang, "n": 0, "sym": [], "imp": [], "ent": False}
            if lang in CODE | {"html"}:
                try:
                    src = pf.read(p, MAX_PARSE)
                except (OSError, ValueError):
                    src = ""                                    # unreadable / binary: keep the entry without symbols
                e["n"] = src.count("\n") + 1 if src else 0
                if lang in CODE:
                    sym, imp = _parse(lang, src)
                    e["sym"], e["imp"] = sym[:MAX_SYM], list(dict.fromkeys(imp))[:MAX_SYM]
                e["ent"] = _entry(p, lang, src)
            files[p] = e
        if files[p]["ent"]:
            entries.append(p)
        if p.rsplit("/", 1)[-1] in ("package.json", "requirements.txt", "pom.xml", "go.mod", "composer.json") and p.count("/") <= 3:
            m = _manifest(pf, p)
            if m:
                manifests.append(m)
    deps_in = Counter()
    for p, e in files.items():
        links = sorted({r for i in e["imp"] if (r := _resolve(p, i, e["l"], tree)) and r != p})
        e["use"] = links[:MAX_SYM]
        deps_in.update(links)
    tests = [p for p in paths if re.search(r"(^|/)(tests?|__tests__|spec)/|(\.|_)(test|spec)\.\w+$|(^|/)test_\w+\.py$", p)]
    m = {"version": 1, "updated": _now(), "digest": _digest(pf, paths), "truncated": len(allp) > MAX_FILES, "files": files,
         "manifests": manifests, "entries": entries, "tests": tests[:40],
         "hubs": [[p, n] for p, n in deps_in.most_common(8)],
         "langs": dict(Counter(e["l"] for e in files.values() if e["l"] != "other").most_common()),
         "stats": {"files": len(allp), "lines": sum(e["n"] for e in files.values())}}
    pf.write(FILE, json.dumps(m, separators=(",", ":")))
    return m


def get(pid: str, refresh: bool = False) -> dict:
    """Stored map; rebuilt when missing, stale or refresh=True."""
    return build(pid) if refresh or stale(pid) else load(pid)


def summary(m: dict) -> dict:
    return {k: m[k] for k in ("updated", "digest", "truncated", "manifests", "entries", "tests", "hubs", "langs", "stats")}


def compact(pid: str, budget: int = 1200) -> str:
    """Tiny text view of the repo for LLM prompts."""
    m = get(pid)
    if not m["files"]:
        return ""
    out = ["LANGS: " + ",".join(f"{k}:{v}" for k, v in m["langs"].items()),
           f"SIZE: {m['stats']['files']} files, {m['stats']['lines']} lines"]
    for mf in m["manifests"][:4]:
        out.append(f"{mf['kind']}@{mf['path']}: " + ",".join(mf.get("scripts") or []) + (" | " if mf.get("scripts") else "") + ",".join(mf["deps"][:10]))
    if m["entries"]:
        out.append("ENTRY: " + ",".join(m["entries"][:6]))
    if m["hubs"]:
        out.append("HUBS: " + ",".join(f"{p}({n})" for p, n in m["hubs"][:6]))
    if m["tests"]:
        out.append(f"TESTS: {len(m['tests'])} files")
    dirs: dict[str, list[str]] = {}
    for p, e in m["files"].items():
        if e["sym"]:
            dirs.setdefault(p.rsplit("/", 1)[0] if "/" in p else ".", []).append(f"{p.rsplit('/', 1)[-1]}[{','.join(e['sym'][:4])}]")
    for d, items in list(dirs.items())[:12]:
        out.append(f"{d}/: " + " ".join(items[:5]))
    return redact("\n".join(out))[:budget]


def search(pid: str, q: str, limit: int = 10) -> list[dict]:
    """Rank files by path / symbol match (no LLM)."""
    terms = [t for t in re.split(r"\W+", q.lower()) if len(t) > 1]
    if not terms:
        return []
    hits = []
    for p, e in get(pid)["files"].items():
        sc = sum(3 * (t in p.lower()) + 4 * sum(t in s.lower() for s in e["sym"]) + (t in " ".join(e["imp"]).lower()) for t in terms)
        if sc:
            hits.append({"path": p, "score": sc, "symbols": e["sym"][:6], "lang": e["l"]})
    return sorted(hits, key=lambda h: (-h["score"], h["path"]))[:max(1, min(limit, 50))]


def outline(pid: str, path: str) -> dict | None:
    e = get(pid)["files"].get(path)
    return {"path": path, **e} if e else None

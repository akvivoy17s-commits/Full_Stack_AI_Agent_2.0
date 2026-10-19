"""Diagnostic-first coding debugger helpers.

Normalizes compiler/test output across common toolchains, groups related failures,
provides bounded source/config context to repair prompts, and evaluates patches by
observed diagnostics rather than the model's claim that a fix was applied.

This is a deterministic aid, not a proof that business logic is correct.
"""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import unquote

_SOURCE_EXT = (
    r"tsx?|jsx?|mjs|cjs|vue|svelte|pyw?|pyi|java|kt|kts|go|rs|php|rb|cs|c|h|cc|cpp|cxx|"
    r"dart|swift|sql|sh|bash|ps1|psm1|html|htm|css|scss|sass|json|jsonc|xml|ya?ml|toml|graphql|gql"
)

# Order matters: the TypeScript/ESLint/GCC forms have precise line/column data.
_PATTERNS = [
    re.compile(
        rf"(?P<file>(?:[A-Za-z]:)?[^()\r\n]*?\.(?:{_SOURCE_EXT}))"
        r"\((?P<line>\d+),(?P<col>\d+)\):\s*(?P<level>error|warning)\s*"
        r"(?P<code>TS\d+)?\s*:?[ \t]*(?P<message>[^\r\n]+)", re.I
    ),
    re.compile(
        rf"(?P<file>(?:[A-Za-z]:[\\/])?[^:\r\n]+?\.(?:{_SOURCE_EXT}))"
        r":(?P<line>\d+):(?P<col>\d+)\s+(?P<level>error|warning)\s+(?P<message>[^\r\n]+)", re.I
    ),
    re.compile(
        rf"(?P<file>(?:[A-Za-z]:[\\/])?[^:\r\n]+?\.(?:{_SOURCE_EXT}))"
        r":(?P<line>\d+):(?P<col>\d+):\s*(?P<level>fatal error|error|warning|note):\s*(?P<message>[^\r\n]+)", re.I
    ),
    re.compile(
        rf"(?P<file>(?:[A-Za-z]:[\\/])?[^:\r\n]+?\.(?:{_SOURCE_EXT}))"
        r":(?P<line>\d+):\s*(?P<level>error|warning):\s*(?P<message>[^\r\n]+)", re.I
    ),
    re.compile(
        rf"(?P<file>(?:[A-Za-z]:[\\/])?[^\r\n]*?\.(?:{_SOURCE_EXT}))\s+"
        r"(?P<line>\d+):(?P<col>\d+)\s+(?P<level>error|warning)\s+(?P<message>[^\r\n]+)", re.I
    ),
]

_SUPPRESS = re.compile(
    r"eslint-disable|@ts-ignore|@ts-nocheck|\bnoqa\b|type:\s*ignore|pragma:\s*no cover|"
    r"pytest\.mark\.skip|\.skip\s*\(|--no-verify|nosec\b|noinspection", re.I
)


def _clean_path(value: str | None, root: str | Path | None = None) -> str:
    """Normalize diagnostic locations and discard build-command prefixes.

    Some build runners place the command and its first diagnostic on one line, e.g.
    ``> tsc --noEmit && vite build src/lib/App.tsx(4,2): error TS...``. The old
    permissive location regex captured the entire command as a filename. Keep absolute
    Windows paths intact (including spaces), but when the captured value contains shell
    punctuation, extract the final plausible source path token instead.
    """
    if not value:
        return ""
    raw = unquote(str(value).strip().strip("\"'`"))
    raw = raw.replace("\\", "/")
    if root:
        root_text = str(root).replace("\\", "/").rstrip("/")
        pos = raw.lower().find(root_text.lower() + "/")
        if pos >= 0:
            raw = raw[pos + len(root_text) + 1 :]
    raw = re.sub(r"^file://", "", raw, flags=re.I)

    # A build command and its first diagnostic may share a line. In that case, extract
    # the final source path rather than treating `> tsc ... && vite build src/file.tsx`
    # as one path. Relative paths use whitespace-free path segments; Windows absolute
    # paths remain supported because the project root is stripped above when available.
    if any(token in raw for token in (">", "&&", "|")) or "--noemit" in raw.lower() or "vite build" in raw.lower():
        candidate = re.search(
            rf"((?:[A-Za-z]:/[^()\r\n]*?|(?:\.{{1,2}}/)?[A-Za-z0-9_@.+-]+(?:/[A-Za-z0-9_@.+-]+)*)\.(?:{_SOURCE_EXT}))\s*$",
            raw, re.I,
        )
        if candidate:
            raw = candidate.group(1)
    while raw.startswith("./"):
        raw = raw[2:]
    return PurePosixPath(raw).as_posix() if raw else ""

def classify_message(message: str) -> str:
    text = (message or "").lower()
    if any(x in text for x in ("cannot find module", "failed to resolve import", "could not resolve", "module not found", "no module named", "could not find or load main class")):
        return "missing_dependency_or_import"
    if any(x in text for x in ("does not exist on type 'jsx.intrinsicelements'", "does not exist on type \"jsx.intrinsicelements\"", "intrinsicelements")):
        return "invalid_jsx_tag"
    if any(x in text for x in ("cannot find name", "is not defined", "undefined reference", "unresolved reference", "not declared in this scope", "undeclared identifier", "cannot resolve symbol")):
        return "undefined_symbol"
    if any(x in text for x in ("expected corresponding closing tag", "unclosed <", "unexpected closing", "unexpected token", "syntaxerror", "syntax error", "parse error", "failed to parse", "unterminated", "unexpected end of input")):
        return "syntax_error"
    if any(x in text for x in ("not assignable", "type mismatch", "incompatible types", "cannot convert", "type '" , "type \"")):
        return "type_error"
    if any(x in text for x in ("test failed", "assertionerror", "assertion failed", "failed tests", "tests failed")):
        return "test_failure"
    if any(x in text for x in ("timeout", "timed out", "deadline exceeded")):
        return "timeout"
    if any(x in text for x in ("permission denied", "unauthorized", "forbidden", "access denied")):
        return "permission_or_auth"
    if any(x in text for x in ("cannot read properties", "nullreferenceexception", "null pointer", "referenceerror", "typeerror")):
        return "runtime_error"
    if any(x in text for x in ("warning", "possible", "consider", "duplicate", "redundant", "unused")):
        return "warning_or_redundancy"
    return "compiler_or_tool_error"


def parse_diagnostics(output: str, root: str | Path | None = None, limit: int = 80) -> list[dict[str, Any]]:
    """Parse common compiler/linter locations from output without executing code."""
    text = str(output or "")
    results: list[dict[str, Any]] = []
    seen = set()
    for pattern in _PATTERNS:
        for match in pattern.finditer(text):
            gd = match.groupdict()
            message = re.sub(r"\s+", " ", (gd.get("message") or "").strip())
            code = (gd.get("code") or "").strip()
            row = {
                "file": _clean_path(gd.get("file"), root),
                "line": int(gd["line"]) if gd.get("line") else None,
                "column": int(gd["col"]) if gd.get("col") else None,
                "level": (gd.get("level") or "error").lower(),
                "code": code,
                "message": message[:800],
                "category": classify_message((code + " " + message).strip()),
                "tool": code or "compiler",
            }
            key = (row["file"].lower(), row["line"], row["column"], row["code"], row["message"])
            if key not in seen:
                seen.add(key)
                results.append(row)
                if len(results) >= limit:
                    return results
    # Rust's caret-location lines and Python's traceback frame are often separated from
    # the primary message. Preserve those locations as secondary evidence if nothing else
    # was parsed for that file; do not invent a message as though compilation failed there.
    if not results:
        rust = re.compile(r"^\s*-->\s+(?P<file>[^:]+):(?P<line>\d+):(?P<col>\d+)\s*$", re.M)
        for match in rust.finditer(text):
            results.append({"file": _clean_path(match.group("file"), root), "line": int(match.group("line")),
                            "column": int(match.group("col")), "level": "error", "code": "", "message": "Rust diagnostic location (see primary error above)",
                            "category": "compiler_or_tool_error", "tool": "rustc"})
            if len(results) >= limit:
                break
    return results


def normalize_issue(issue: dict[str, Any], root: str | Path | None = None) -> dict[str, Any]:
    raw = str(issue.get("msg") or issue.get("message") or issue.get("detail") or "unknown diagnostic")
    parsed = parse_diagnostics(raw, root=root, limit=12)
    explicit_file = _clean_path(str(issue.get("file") or ""), root)
    first = parsed[0] if parsed else {}
    file = explicit_file or first.get("file", "")
    line = issue.get("line") if isinstance(issue.get("line"), int) else first.get("line")
    category = str(issue.get("category") or first.get("category") or classify_message(raw))
    message = str(first.get("message") or raw).strip()
    code = str(first.get("code") or "")
    # If the text contains several errors, preserve all of them for grouping/repair
    # scoring; `message` remains the first/root candidate for compact display.
    return {"file": file, "line": line, "column": first.get("column"), "category": category,
            "code": code, "message": message[:800], "raw": raw[:5000], "parsed": parsed,
            "severity": str(issue.get("severity") or issue.get("level") or "error").lower()}


def _issue_keys(issues: list[dict[str, Any]], root: str | Path | None = None) -> set[str]:
    keys: set[str] = set()
    for issue in issues:
        normalized = normalize_issue(issue, root=root)
        parsed = normalized["parsed"]
        if parsed:
            for item in parsed:
                # Ignore line/column so a harmless insertion above the error doesn't hide
                # a persistent issue. Include code/message/file so a distinct error is new.
                msg = re.sub(r"\s+", " ", item["message"]).strip().lower()
                keys.add("|".join((item["file"].lower(), item["code"].lower(), item["category"], msg)))
        else:
            msg = re.sub(r"\bline\s+\d+\b|\(\d+,\s*\d+\)|:\d+:\d+", "#", normalized["message"].lower())
            msg = re.sub(r"\s+", " ", msg).strip()
            keys.add("|".join((normalized["file"].lower(), normalized["category"], msg)))
    return keys


def compare_diagnostics(before: list[dict[str, Any]], after: list[dict[str, Any]], root: str | Path | None = None) -> dict[str, Any]:
    """Conservative repair acceptance: accept only a strict diagnostic reduction.

    New diagnostics or an unchanged diagnostic set cause rollback. This avoids the common
    failure mode where a patch fixes one line but introduces a different compile error.
    """
    b, a = _issue_keys(before, root=root), _issue_keys(after, root=root)
    added, removed = sorted(a - b), sorted(b - a)
    if not a and b:
        status = "improved"
    elif removed and not added and len(a) < len(b):
        status = "improved"
    elif added or len(a) > len(b):
        status = "regressed"
    elif a == b:
        status = "unchanged"
    else:
        status = "regressed"
    return {"status": status, "before_count": len(b), "after_count": len(a),
            "removed": removed[:20], "added": added[:20]}


def prioritize_diagnostics(issues: list[dict[str, Any]], root: str | Path | None = None) -> list[dict[str, Any]]:
    """Order build-blocking root causes before likely cascades and non-blocking hints."""
    def rank(issue):
        n = normalize_issue(issue, root=root)
        category = n["category"]
        weights = {
            "syntax_error": 0, "missing_dependency_or_import": 1, "invalid_jsx_tag": 2,
            "undefined_symbol": 3, "type_error": 4, "runtime_error": 5,
            "test_failure": 6, "permission_or_auth": 7, "timeout": 8,
            "compiler_or_tool_error": 9, "warning_or_redundancy": 10,
        }
        return weights.get(category, 9), n["file"], n["line"] or 0
    return sorted(issues, key=rank)


def root_cause_summary(issues: list[dict[str, Any]], root: str | Path | None = None) -> dict[str, Any]:
    normalized = [normalize_issue(i, root=root) for i in issues]
    classes = Counter(i["category"] for i in normalized)
    by_file: dict[str, list[dict[str, Any]]] = {}
    for item in normalized:
        by_file.setdefault(item["file"] or "project", []).append(item)
    hints: list[str] = []
    all_text = "\n".join(i["raw"] for i in normalized).lower()
    jsx_symbols = re.search(r"cannot find name ['\"]?[A-Z][A-Za-z0-9_$]*|intrinsicelements|cannot find name ['\"]?(?:featured|products|categories)", all_text)
    if jsx_symbols and ("tsx" in all_text or "jsx" in all_text or "intrinsicelements" in all_text):
        hints.append("Likely generated JSX/HTML contract violation: a component tag or data variable was emitted without a declared import; prefer rebuilding generated TSX from canonical source over inventing imports.")
    if classes.get("missing_dependency_or_import"):
        hints.append("Check the exact import path, filename case, package manifest and installed dependency before changing code.")
    if classes.get("undefined_symbol"):
        hints.append("Check symbol declarations, imports, scope and framework conventions; do not silence the compiler with any/ignore directives.")
    if classes.get("type_error"):
        hints.append("Check the declared type and all call sites; prefer a type-safe correction over broad casts.")
    if classes.get("syntax_error"):
        hints.append("Fix the earliest parser error first; later diagnostics may be cascading consequences.")
    return {"issue_count": len(issues), "category_counts": dict(classes),
            "files": {f: [{"line": i["line"], "category": i["category"], "message": i["message"][:300]} for i in rows[:10]] for f, rows in list(by_file.items())[:20]},
            "root_cause_hints": hints[:8]}


def _safe_read(pf, rel: str, limit: int = 3500) -> str:
    try:
        text = pf.read(rel)
    except (OSError, ValueError, FileNotFoundError):
        return ""
    return text[:limit]


def repair_context(pf, file: str, issues: list[dict[str, Any]], source: str, root: str | Path | None = None) -> str:
    """Build compact, secret-conscious evidence for a repair call."""
    normalized = [normalize_issue(i, root=root or getattr(pf, "root", None)) for i in issues]
    summary = root_cause_summary(issues, root=root or getattr(pf, "root", None))
    line = next((i["line"] for i in normalized if i.get("line")), None)
    lines = source.splitlines()
    source_excerpt = source[:1800]
    if line and lines:
        idx = min(max(int(line) - 1, 0), len(lines) - 1)
        lo, hi = max(0, idx - 18), min(len(lines), idx + 19)
        source_excerpt = "\n".join(f"{n + 1}: {lines[n][:300]}" for n in range(lo, hi))[:3500]
    manifests = []
    for rel in ("package.json", "tsconfig.json", "pyproject.toml", "Cargo.toml", "go.mod", "pom.xml", "composer.json", "requirements.txt", "pubspec.yaml"):
        raw = _safe_read(pf, rel, 5000)
        if not raw:
            continue
        if rel == "package.json":
            try:
                data = json.loads(raw)
                raw = json.dumps({"type": data.get("type"), "scripts": data.get("scripts", {}),
                                  "dependencies": sorted((data.get("dependencies") or {}).keys()),
                                  "devDependencies": sorted((data.get("devDependencies") or {}).keys())}, indent=2)
            except Exception:
                raw = "package.json is present but could not be parsed"
        manifests.append(f"[{rel}]\n{raw[:1100]}")
        if len(manifests) >= 3:
            break
    imports = [row.strip() for row in source.splitlines() if re.match(r"\s*(?:import\s|from\s|require\s*\(|using\s|#include|use\s)", row)][:18]
    hints = "\n".join(f"- {h}" for h in summary["root_cause_hints"]) or "- No deterministic root-cause hint; follow compiler evidence only."
    error_lines = "\n".join(f"- {i['file'] or file}{(':'+str(i['line'])) if i.get('line') else ''}: [{i['category']}] {i['message']}" for i in normalized[:8])
    return (f"TARGET FILE: {file}\nDIAGNOSTICS:\n{error_lines}\nROOT-CAUSE HINTS:\n{hints}\n"
            f"RELATED IMPORTS:\n{chr(10).join(imports) or '(none detected)'}\nPROJECT CONFIG (selected non-secret fields):\n"
            f"{chr(10).join(manifests) or '(no recognized project manifest found)'}\nSOURCE WINDOW:\n{source_excerpt[:3500]}\n")


def validate_patch_text(old: str, new: str) -> tuple[bool, str]:
    if not isinstance(old, str) or not isinstance(new, str) or not old or old == new:
        return False, "empty_or_unchanged_patch"
    if _SUPPRESS.search(new):
        return False, "patch_attempts_to_suppress_checks"
    if len(new) > 1500:
        return False, "patch_replacement_too_large"
    if "\x00" in new:
        return False, "patch_contains_nul"
    return True, "ok"

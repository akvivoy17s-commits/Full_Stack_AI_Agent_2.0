"""Language-aware project checks and conservative redundancy analysis.

This module deliberately separates deterministic checks from heuristics. A skipped
check means no suitable local parser/compiler was available; it never means that a
file is correct. External build/test commands run only when ``deep=True`` and use
fixed, allowlisted command shapes from :mod:`backend.tools.terminal`. Nothing is
installed, no network is requested intentionally, and no generated source is edited.
"""
from __future__ import annotations

import ast
import json
import re
import shutil
from collections import Counter, defaultdict
from html.parser import HTMLParser
from pathlib import Path, PurePosixPath
from typing import Any

from backend.tools import terminal

try:  # Python 3.11+
    import tomllib  # type: ignore[import-not-found]
except ImportError:  # pragma: no cover - compatibility fallback
    tomllib = None

MAX_FILES = 1200
MAX_BYTES_PER_FILE = 256_000
MAX_TEXT_LINES = 1500
MAX_REDUNDANCY_FILES = 400
MAX_ISSUES = 100
MAX_REDUNDANCY = 50
SKIP_DIRS = {".git", ".agent", "node_modules", ".venv", "venv", "__pycache__", ".pytest_cache", "dist", "build", "target", "coverage", "vendor"}

# Keep extension mapping transparent: the scanner reports what it can see, while
# this analyzer reports what it can actually validate with the current toolchain.
EXT_LANGUAGE: dict[str, str] = {
    ".py": "Python", ".pyw": "Python", ".pyi": "Python stubs",
    ".js": "JavaScript", ".mjs": "JavaScript", ".cjs": "JavaScript", ".jsx": "JavaScript / JSX",
    ".ts": "TypeScript", ".tsx": "TypeScript / TSX",
    ".html": "HTML", ".htm": "HTML", ".css": "CSS", ".scss": "SCSS", ".sass": "Sass",
    ".vue": "Vue SFC", ".svelte": "Svelte",
    ".java": "Java", ".kt": "Kotlin", ".kts": "Kotlin script", ".go": "Go", ".rs": "Rust",
    ".php": "PHP", ".rb": "Ruby", ".cs": "C#", ".sql": "SQL", ".dart": "Dart", ".swift": "Swift",
    ".c": "C", ".h": "C/C++ header", ".cc": "C++", ".cpp": "C++", ".cxx": "C++", ".hh": "C++ header", ".hpp": "C++ header", ".hxx": "C++ header",
    ".sh": "Shell", ".bash": "Shell", ".ps1": "PowerShell", ".psm1": "PowerShell",
    ".json": "JSON", ".jsonc": "JSONC", ".toml": "TOML", ".yaml": "YAML", ".yml": "YAML", ".xml": "XML", ".xsl": "XML", ".xslt": "XML", ".svg": "SVG/XML",
    ".graphql": "GraphQL", ".gql": "GraphQL", ".proto": "Protocol Buffers", ".ex": "Elixir", ".exs": "Elixir", ".erl": "Erlang", ".hrl": "Erlang", ".clj": "Clojure", ".cljs": "ClojureScript", ".scala": "Scala", ".sc": "Scala", ".r": "R", ".R": "R", ".lua": "Lua", ".pl": "Perl", ".pm": "Perl", ".hs": "Haskell", ".lhs": "Haskell",
}

PROGRAMMING_EXTS = set(EXT_LANGUAGE) - {".html", ".htm", ".css", ".scss", ".sass", ".vue", ".svelte", ".json", ".jsonc", ".toml", ".yaml", ".yml", ".xml", ".xsl", ".xslt", ".svg", ".proto"}


def _issue(file: str, message: str, *, severity: str = "error", category: str = "syntax", line: int | None = None, tool: str = "static") -> dict[str, Any]:
    return {"file": file, "line": line, "severity": severity, "category": category, "message": str(message)[:500], "tool": tool}


def _read(pf, rel: str) -> str:
    path = (Path(pf.root) / rel)
    if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_BYTES_PER_FILE:
        raise ValueError("file is missing, linked, or exceeds the analyzer size limit")
    return path.read_text(encoding="utf-8")


def _files(pf) -> tuple[list[str], bool]:
    names = []
    truncated = False
    for rel in pf.tree():
        parts = set(PurePosixPath(rel).parts)
        if parts & SKIP_DIRS:
            continue
        ext = PurePosixPath(rel).suffix.lower()
        name = PurePosixPath(rel).name.lower()
        build_manifest = name in {
            "dockerfile", "makefile", "cmakelists.txt", "gemfile", "rakefile", "procfile", "justfile",
            "go.mod", "settings.gradle", "settings.gradle.kts", "build.gradle", "build.gradle.kts",
            "gradle.properties", "global.json", "directory.build.props", "directory.build.targets",
        } or name.endswith((".csproj", ".sln", ".slnx"))
        if ext not in EXT_LANGUAGE and not build_manifest:
            continue
        names.append(rel)
        if len(names) >= MAX_FILES:
            truncated = True
            break
    return names, truncated


class _HTMLBalance(HTMLParser):
    VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr", "command", "keygen"}
    OPTIONAL_END = {"li", "p", "dt", "dd", "rt", "rp", "optgroup", "option", "colgroup", "thead", "tbody", "tfoot", "tr", "td", "th"}
    BLOCK_STARTING_P = {"address", "article", "aside", "blockquote", "div", "dl", "fieldset", "footer", "form", "h1", "h2", "h3", "h4", "h5", "h6", "header", "hr", "main", "nav", "ol", "p", "pre", "section", "table", "ul"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.stack: list[tuple[str, int]] = []
        self.issues: list[tuple[int, str]] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        tag = tag.lower()
        if tag in self.VOID:
            return
        # HTML's optional-end-tag rules for common containers reduce false positives.
        if tag in self.BLOCK_STARTING_P and self.stack and self.stack[-1][0] == "p":
            self.stack.pop()
        if tag == "li" and self.stack and self.stack[-1][0] == "li": self.stack.pop()
        if tag in ("td", "th") and self.stack and self.stack[-1][0] in ("td", "th"): self.stack.pop()
        if tag == "tr" and self.stack and self.stack[-1][0] == "tr": self.stack.pop()
        if tag == "option" and self.stack and self.stack[-1][0] == "option": self.stack.pop()
        self.stack.append((tag, self.getpos()[0]))

    def handle_startendtag(self, tag: str, attrs) -> None:
        return

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        matches = [i for i, (open_tag, _) in enumerate(self.stack) if open_tag == tag]
        if not matches:
            self.issues.append((self.getpos()[0], f"unexpected closing HTML tag </{tag}>") )
            return
        index = matches[-1]
        # If the close skips non-optional elements, report rather than silently auto-fix.
        skipped = self.stack[index + 1:]
        for open_tag, line in reversed(skipped):
            if open_tag not in self.OPTIONAL_END:
                self.issues.append((line, f"<{open_tag}> opened here was not closed before </{tag}>") )
        del self.stack[index:]


def _css_delimiters(source: str) -> list[tuple[int, str]]:
    """Validate balanced CSS braces/parens/brackets while ignoring strings and comments."""
    stack: list[tuple[str, int]] = []
    issues: list[tuple[int, str]] = []
    quote: str | None = None
    escaped = False
    in_comment = False
    line = 1
    i = 0
    pairs = {"}": "{", ")": "(", "]": "["}
    while i < len(source):
        ch = source[i]
        nxt = source[i + 1] if i + 1 < len(source) else ""
        if ch == "\n": line += 1
        if in_comment:
            if ch == "*" and nxt == "/": in_comment = False; i += 2; continue
            i += 1; continue
        if quote:
            if escaped: escaped = False
            elif ch == "\\": escaped = True
            elif ch == quote: quote = None
            i += 1; continue
        if ch == "/" and nxt == "*": in_comment = True; i += 2; continue
        if ch in ("'", '"'):
            quote = ch; i += 1; continue
        if ch in "{([": stack.append((ch, line))
        elif ch in pairs:
            if not stack or stack[-1][0] != pairs[ch]:
                issues.append((line, f"unmatched '{ch}' delimiter"))
            else: stack.pop()
        i += 1
    if quote: issues.append((line, "unterminated CSS string literal"))
    if in_comment: issues.append((line, "unterminated CSS comment"))
    for ch, start_line in stack:
        issues.append((start_line, f"unclosed '{ch}' delimiter"))
    return issues


def _simple_syntax(rel: str, source: str) -> tuple[str, list[dict]]:
    ext = PurePosixPath(rel).suffix.lower()
    lang = EXT_LANGUAGE.get(ext, "configuration")
    issues: list[dict] = []
    if ext in {".py", ".pyw", ".pyi"}:
        try:
            # AST parse checks syntax without executing project source.
            ast.parse(source, filename=rel, type_comments=True)
        except SyntaxError as exc:
            issues.append(_issue(rel, f"Python syntax error: {exc.msg}", line=exc.lineno, tool="Python AST"))
        return lang, issues
    if ext in {".json", ".jsonc"}:
        try:
            # TypeScript config files and the VS Code workspace manifests use JSONC
            # semantics despite retaining the .json suffix.
            base = PurePosixPath(rel).name.lower()
            if ext == ".jsonc" or base in {"tsconfig.json", "jsconfig.json"} or (base in {"launch.json", "tasks.json", "settings.json", "keybindings.json"} and ".vscode" in {p.lower() for p in PurePosixPath(rel).parts}):
                # Minimal JSONC support: strip comments/trailing commas only outside strings.
                source = _strip_jsonc(source)
            json.loads(source)
        except (ValueError, TypeError) as exc:
            line = getattr(exc, "lineno", None)
            issues.append(_issue(rel, f"invalid {ext[1:].upper()}: {str(exc)[:300]}", line=line, tool="json parser"))
        return lang, issues
    if ext == ".toml":
        if tomllib:
            try: tomllib.loads(source)
            except Exception as exc: issues.append(_issue(rel, f"invalid TOML: {str(exc)[:300]}", line=getattr(exc, "lineno", None), tool="tomllib"))
        else:
            return lang, [_issue(rel, "TOML parser unavailable; syntax was not validated", severity="info", category="coverage", tool="none")]
        return lang, issues
    if ext in {".xml", ".xsl", ".xslt", ".svg"}:
        try:
            import xml.etree.ElementTree as ET
            ET.fromstring(source)
        except Exception as exc: issues.append(_issue(rel, f"invalid XML: {str(exc)[:250]}", line=getattr(exc, "position", (None,))[0] if getattr(exc, "position", None) else None, tool="ElementTree"))
        return lang, issues
    if ext in {".yaml", ".yml"}:
        try:
            import yaml  # type: ignore[import-not-found]
            try: yaml.safe_load(source)
            except Exception as exc: issues.append(_issue(rel, f"invalid YAML: {str(exc)[:250]}", line=getattr(getattr(exc, "problem_mark", None), "line", -1) + 1 if getattr(exc, "problem_mark", None) else None, tool="PyYAML safe_load"))
        except ImportError:
            return lang, [_issue(rel, "PyYAML is not installed; YAML syntax was not validated", severity="info", category="coverage", tool="none")]
        return lang, issues
    if ext in {".css", ".scss", ".sass"}:
        issues.extend(_issue(rel, msg, line=line, tool="balanced-delimiter scanner") for line, msg in _css_delimiters(source))
        return lang, issues
    if ext in {".html", ".htm"}:
        parser = _HTMLBalance()
        try: parser.feed(source); parser.close()
        except Exception as exc: issues.append(_issue(rel, f"HTML parser error: {str(exc)[:200]}", tool="HTMLParser"))
        issues.extend(_issue(rel, msg, line=line, tool="HTMLParser tag-balance heuristic") for line, msg in parser.issues[:20])
        for tag, line in parser.stack:
            if tag not in parser.OPTIONAL_END:
                issues.append(_issue(rel, f"unclosed HTML tag <{tag}>", severity="error", line=line, tool="HTMLParser tag-balance heuristic"))
        return lang, issues
    if ext == ".sql":
        try:
            import sqlglot  # type: ignore[import-not-found]
            try: sqlglot.parse(source)
            except Exception as exc: issues.append(_issue(rel, f"SQL parse error: {str(exc)[:250]}", tool="sqlglot"))
        except ImportError:
            return lang, [_issue(rel, "SQL parser is not installed; SQL syntax was not validated", severity="info", category="coverage", tool="none")]
        return lang, issues
    if ext in {".proto", ".graphql", ".gql", ".ex", ".exs", ".erl", ".hrl", ".clj", ".cljs", ".scala", ".sc", ".r", ".lua", ".pl", ".pm", ".hs", ".lhs"}:
        return lang, [_issue(rel, f"No safe built-in parser configured for {lang}; install/use that language's compiler or linter via a declared project script", severity="info", category="coverage", tool="none")]
    return lang, []


def _strip_jsonc(source: str) -> str:
    """Remove JSONC comments and trailing commas without touching quoted strings."""
    out: list[str] = []
    quote = False; escape = False; line_comment = False; block_comment = False
    i = 0
    while i < len(source):
        ch = source[i]; nxt = source[i + 1] if i + 1 < len(source) else ""
        if line_comment:
            if ch == "\n": line_comment = False; out.append(ch)
            else: out.append(" ")
            i += 1; continue
        if block_comment:
            if ch == "*" and nxt == "/": out.extend("  "); block_comment = False; i += 2; continue
            out.append("\n" if ch == "\n" else " "); i += 1; continue
        if quote:
            out.append(ch)
            if escape: escape = False
            elif ch == "\\": escape = True
            elif ch == '"': quote = False
            i += 1; continue
        if ch == '"': quote = True; out.append(ch); i += 1; continue
        if ch == "/" and nxt == "/": line_comment = True; out.extend("  "); i += 2; continue
        if ch == "/" and nxt == "*": block_comment = True; out.extend("  "); i += 2; continue
        out.append(ch); i += 1
    cleaned = "".join(out)
    # Trailing commas are valid in JSONC but not JSON. Remove only when followed by }/].
    result: list[str] = []; quote = False; escape = False; i = 0
    while i < len(cleaned):
        ch = cleaned[i]
        if quote:
            result.append(ch)
            if escape: escape = False
            elif ch == "\\": escape = True
            elif ch == '"': quote = False
            i += 1; continue
        if ch == '"': quote = True; result.append(ch); i += 1; continue
        if ch == ",":
            j = i + 1
            while j < len(cleaned) and cleaned[j].isspace(): j += 1
            if j < len(cleaned) and cleaned[j] in "]}": i += 1; continue
        result.append(ch); i += 1
    return "".join(result)


def _python_issues(source: str, rel: str) -> list[dict]:
    out: list[dict] = []
    try: tree = ast.parse(source, filename=rel, type_comments=True)
    except SyntaxError: return out  # reported by the syntax parser already

    # Duplicate function/class names in a single lexical scope shadow an earlier
    # definition. This is a warning because intentional monkey-patching is possible.
    def check_scope(body: list[ast.stmt]) -> None:
        seen_defs: dict[str, ast.AST] = {}
        for item in body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                # A repeated throwaway callback name is common in test/registry modules.
                # Report duplicate semantic names, but avoid noisy warnings for `_`.
                if item.name in seen_defs and item.name != "_":
                    out.append(_issue(rel, f"duplicate definition '{item.name}' shadows an earlier definition in the same scope", severity="warning", category="redundancy", line=item.lineno, tool="Python AST"))
                seen_defs[item.name] = item
                check_scope(item.body)
    check_scope(tree.body)

    used_names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)}
    explicit_all = any(isinstance(n, (ast.Assign, ast.AnnAssign)) and any(isinstance(t, ast.Name) and t.id == "__all__" for t in (n.targets if isinstance(n, ast.Assign) else [n.target])) for n in tree.body)
    if not explicit_all:
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    bound = alias.asname or alias.name.split(".")[0]
                    if bound not in used_names and alias.name != "annotations":
                        out.append(_issue(rel, f"possibly unused import '{alias.name}'", severity="info", category="redundancy", line=node.lineno, tool="Python AST"))
            elif isinstance(node, ast.ImportFrom) and node.module != "__future__":
                for alias in node.names:
                    bound = alias.asname or alias.name
                    if alias.name != "*" and bound not in used_names:
                        out.append(_issue(rel, f"possibly unused imported name '{bound}'", severity="info", category="redundancy", line=node.lineno, tool="Python AST"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Dict):
            seen: set[tuple[str, str]] = set()
            for key in node.keys:
                if isinstance(key, ast.Constant) and isinstance(key.value, (str, int, float, bool, type(None))):
                    k = (type(key.value).__name__, repr(key.value))
                    if k in seen: out.append(_issue(rel, f"duplicate dict key {key.value!r}; earlier value is overwritten", severity="warning", category="logic", line=getattr(key, "lineno", None), tool="Python AST"))
                    seen.add(k)
        if isinstance(node, ast.Compare) and len(node.ops) == 1 and len(node.comparators) == 1 and isinstance(node.left, ast.Name) and isinstance(node.comparators[0], ast.Name) and node.left.id == node.comparators[0].id and isinstance(node.ops[0], (ast.Eq, ast.Is)):
            out.append(_issue(rel, f"comparison compares '{node.left.id}' with itself; condition may be redundant", severity="warning", category="logic", line=node.lineno, tool="Python AST"))
        if isinstance(node, ast.BoolOp):
            values = [ast.dump(v, include_attributes=False) for v in node.values]
            if len(values) != len(set(values)):
                out.append(_issue(rel, "repeated operand in boolean expression may be redundant", severity="warning", category="logic", line=getattr(node, "lineno", None), tool="Python AST"))
        if isinstance(node, ast.If):
            if isinstance(node.test, ast.Constant) and isinstance(node.test.value, bool):
                out.append(_issue(rel, f"constant '{node.test.value}' branch may be dead code", severity="warning", category="logic", line=node.lineno, tool="Python AST"))
            chain: list[ast.If] = [node]
            tail = node.orelse
            while len(tail) == 1 and isinstance(tail[0], ast.If):
                chain.append(tail[0]); tail = tail[0].orelse
            conditions = [ast.dump(part.test, include_attributes=False) for part in chain]
            if len(conditions) != len(set(conditions)):
                out.append(_issue(rel, "an if/elif chain repeats a condition; a later branch may be unreachable", severity="warning", category="logic", line=chain[-1].lineno, tool="Python AST"))
            if node.orelse:
                left = [ast.dump(x, include_attributes=False) for x in node.body]
                right = [ast.dump(x, include_attributes=False) for x in node.orelse]
                if left == right:
                    out.append(_issue(rel, "if and else branches contain identical statements; the conditional may be redundant", severity="info", category="redundancy", line=node.lineno, tool="Python AST"))
        body = getattr(node, "body", None)
        if isinstance(body, list):
            for before, after in zip(body, body[1:]):
                if isinstance(before, (ast.Return, ast.Raise, ast.Break, ast.Continue)):
                    out.append(_issue(rel, f"unreachable statement after {type(before).__name__.lower()}", severity="warning", category="logic", line=getattr(after, "lineno", None), tool="Python AST"))
                elif isinstance(before, ast.stmt) and isinstance(after, ast.stmt) and ast.dump(before, include_attributes=False) == ast.dump(after, include_attributes=False):
                    out.append(_issue(rel, "identical adjacent statements may be redundant", severity="warning", category="redundancy", line=getattr(after, "lineno", None), tool="Python AST"))
    return out


GENERIC_LOGIC_EXTS = {
    ".js", ".mjs", ".cjs", ".jsx", ".ts", ".tsx", ".java", ".kt", ".kts", ".go", ".rs",
    ".php", ".cs", ".dart", ".swift", ".c", ".h", ".cc", ".cpp", ".cxx", ".hh", ".hpp", ".hxx",
}


def _generic_logic_issues(source: str, rel: str) -> list[dict]:
    """Conservative syntax-independent logic checks for common C-style languages.

    This is deliberately a small heuristic, not a full parser. Lines containing
    strings, comments, or complex expressions are skipped to avoid noisy matches.
    Language-native compilers/linters remain authoritative for deeper analysis.
    """
    out: list[dict] = []
    ext = PurePosixPath(rel).suffix.lower()
    token = r"\$?[A-Za-z_][\w$]*(?:\.[A-Za-z_][\w$]*)*"
    self_compare = re.compile(rf"(?P<lhs>{token})\s*(?:===|!==|==|!=)\s*(?P=lhs)(?![\w$])")
    repeated_boolean = re.compile(rf"(?P<lhs>{token})\s*(?P<op>&&|\|\|)\s*(?P=lhs)(?![\w$])")
    # Avoid Python and SQL because they have distinct grammar and/or AST support.
    for no, raw in enumerate(source.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith(("//", "/*", "*", "#", "<!--")):
            continue
        # Skip ambiguous lines rather than treating text in literals/comments as code.
        if any(mark in line for mark in ('"', "'", "`", "//", "/*", "*/", "<!--", "-->", "#")):
            continue
        if ext in {".js", ".mjs", ".cjs", ".jsx", ".ts", ".tsx", ".java", ".kt", ".kts", ".go", ".rs", ".php", ".cs", ".dart", ".swift", ".c", ".h", ".cc", ".cpp", ".cxx", ".hh", ".hpp", ".hxx"}:
            match = self_compare.search(line)
            if match:
                out.append(_issue(rel, f"comparison compares '{match.group('lhs')}' with itself; condition may be redundant", severity="warning", category="logic", line=no, tool="cross-language heuristic"))
            match = repeated_boolean.search(line)
            if match:
                out.append(_issue(rel, f"repeated operand '{match.group('lhs')}' around '{match.group('op')}' may be redundant", severity="warning", category="logic", line=no, tool="cross-language heuristic"))
            if re.search(r"\bif\s*\(\s*(?:true|false)\s*\)", line):
                out.append(_issue(rel, "constant boolean if-condition may make a branch permanently unreachable", severity="warning", category="logic", line=no, tool="cross-language heuristic"))
    return out


def _redundancy_lines(pf, files: list[str]) -> list[dict]:
    """Conservative duplicate-code hints; all results are advisory, never build blockers."""
    out: list[dict] = []
    block_index: dict[tuple[str, ...], list[tuple[str, int]]] = defaultdict(list)
    candidates = [rel for rel in files if PurePosixPath(rel).suffix.lower() in PROGRAMMING_EXTS][:MAX_REDUNDANCY_FILES]
    for rel in candidates:
        ext = PurePosixPath(rel).suffix.lower()
        try: source = _read(pf, rel)
        except (OSError, ValueError, UnicodeError): continue
        rows = source.splitlines()[:MAX_TEXT_LINES]
        significant: list[tuple[int, str]] = []
        local_lines: dict[str, list[int]] = defaultdict(list)
        for no, row in enumerate(rows, 1):
            s = re.sub(r"\s+", " ", row.strip())
            if not s or len(s) < 28 or s in {"}", "{", ");", "};", "</div>", "</section>", "</form>"}:
                continue
            if s.startswith(("//", "#", "/*", "*", "<!--")) or s.endswith(("*/", "-->")):
                continue
            local_lines[s].append(no)
            significant.append((no, s))
        for text, positions in local_lines.items():
            if len(positions) >= 2 and text not in {"return true", "return false", "break", "continue"}:
                out.append(_issue(rel, f"same non-trivial source line appears {len(positions)} times; review whether a helper or loop would be clearer", severity="info", category="redundancy", line=positions[1], tool="duplicate-line heuristic"))
        # Use only adjacent five-line windows and require enough actual code characters.
        # Require same-file-independent source patterns without common brace-only lines.
        for i in range(0, max(0, len(significant) - 4)):
            window = significant[i:i + 5]
            # Keep line spacing shape irrelevant; skip sequences with significant gaps.
            if any(window[j + 1][0] - window[j][0] > 2 for j in range(4)):
                continue
            block = tuple(item[1] for item in window)
            if sum(map(len, block)) < 140 or any(x in {"{", "}", "});", "};"} for x in block):
                continue
            block_index[block].append((rel, window[0][0]))
    for block, locations in block_index.items():
        unique = list(dict.fromkeys(locations))
        unique_files = {x[0] for x in unique}
        if len(unique_files) > 1:
            a, b = unique[:2]
            out.append(_issue(a[0], f"possible duplicated {len(block)}-line code block also appears in {b[0]} (line {b[1]}); consider a shared helper only if behavior is identical", severity="info", category="redundancy", line=a[1], tool="duplicate-block heuristic"))
            if len(out) >= MAX_REDUNDANCY: break
    # Avoid reports exploding on generated templates or files with many repeated constants.
    return out[:MAX_REDUNDANCY]


def _status(checks: list[dict], issues: list[dict]) -> str:
    if any(x.get("severity") == "error" for x in issues): return "failed"
    if any(c.get("status") == "failed" for c in checks): return "failed"
    if not checks or all(c.get("status") == "skipped" for c in checks): return "skipped"
    if any(c.get("status") == "skipped" for c in checks): return "partial"
    return "passed"


def _run(args: list[str], cwd: Path, timeout: int = 90) -> dict:
    try:
        return terminal.run(args, cwd=str(cwd), timeout=timeout, max_out=3500)
    except (OSError, ValueError) as exc:
        return {"code": 127, "out": f"check unavailable: {type(exc).__name__}: {exc}"}


def _add_cmd_check(checks: list[dict], issues: list[dict], name: str, lang: str, args: list[str], cwd: Path, timeout: int = 90) -> None:
    exe = args[0]
    if not shutil.which(exe):
        checks.append({"name": name, "language": lang, "status": "skipped", "files_checked": 0, "detail": f"{exe} is not installed; this language was not compiler-checked."})
        return
    result = _run(args, cwd, timeout)
    if result.get("code") == 127:
        checks.append({"name": name, "language": lang, "status": "skipped", "files_checked": 0, "detail": str(result.get("out", "tool unavailable"))[:500]})
    elif result.get("code") == 0:
        checks.append({"name": name, "language": lang, "status": "passed", "files_checked": 1, "detail": "Compiler/parser exited successfully."})
    else:
        detail = str(result.get("out") or f"exit code {result.get('code')}")[:1000]
        checks.append({"name": name, "language": lang, "status": "failed", "files_checked": 0, "detail": detail})
        issues.append(_issue("", f"{name} failed: {detail[:450]}", severity="error", category="compiler", tool=exe))


def _deep_checks(pf, files: list[str], checks: list[dict], issues: list[dict]) -> None:
    """Run installed toolchains with fixed commands. Do not install deps or run shell text."""
    root = Path(pf.root)
    paths = [PurePosixPath(x) for x in files]
    # TypeScript/JSX/SPA checks must come from a project's installed compiler/build scripts.
    package_dirs = sorted({str(Path(pf.root) / Path(*p.parts[:-1])) for p in paths if p.name == "package.json"})
    for raw_dir in package_dirs[:5]:
        cwd = Path(raw_dir)
        package = cwd / "package.json"
        try: pkg = json.loads(package.read_text(encoding="utf-8"))
        except Exception: continue
        scripts = pkg.get("scripts", {}) if isinstance(pkg, dict) else {}
        if not isinstance(scripts, dict): continue
        rel = cwd.relative_to(root).as_posix() or "."
        languages = {EXT_LANGUAGE.get(p.suffix.lower(), "") for p in paths if (root / Path(*p.parts)).is_relative_to(cwd) and p.suffix.lower() in EXT_LANGUAGE}
        lang_summary = ", ".join(sorted(x for x in languages if x)) or "JavaScript/TypeScript"
        if not (cwd / "node_modules").is_dir():
            applicable = [name for name in ("typecheck", "build", "lint", "test") if name in scripts]
            checks.append({"name": f"Node project checks ({rel})", "language": lang_summary, "status": "skipped", "files_checked": 0, "detail": "Dependencies are not installed; no package installation was attempted. Available scripts: " + (", ".join(applicable) or "no standard typecheck/build/lint/test scripts")})
            continue
        ran = False
        # Typecheck is preferred before build; execution is serial to avoid overloading laptop RAM.
        for script, timeout in (("typecheck", 120), ("build", 180), ("lint", 120), ("test", 180)):
            if script not in scripts: continue
            ran = True
            result = _run(["npm", "run", script], cwd, timeout)
            code = result.get("code", 127)
            status = "passed" if code == 0 else ("skipped" if code == 127 else "failed")
            detail = "Script exited successfully." if code == 0 else str(result.get("out") or f"exit code {code}")[:1000]
            checks.append({"name": f"npm {script} ({rel})", "language": lang_summary, "status": status, "files_checked": 0, "detail": detail})
            if status == "failed": issues.append(_issue("", f"npm {script} ({rel}) failed: {detail[:450]}", severity="error", category="build", tool="npm"))
        if not ran:
            checks.append({"name": f"Node project checks ({rel})", "language": lang_summary, "status": "skipped", "files_checked": 0, "detail": "No recognized typecheck/build/lint/test scripts are declared."})

    # Language-specific parser-only checks already run during the static pass. Deep mode
    # adds project-level compiler/build/test checks below, where cross-file contracts matter.

    # Use TypeScript's own compiler for TS/TSX when a project tsconfig and local
    # dependencies exist. Do not use npx here because it may fetch packages.
    has_ts = any(p.suffix.lower() in {".ts", ".tsx"} for p in paths)
    tsconfigs = [p for p in paths if p.name == "tsconfig.json"]
    if has_ts and tsconfigs:
        for config in tsconfigs[:5]:
            cwd = root / Path(*config.parts[:-1])
            package_here = cwd / "package.json"
            if package_here.is_file() and not (cwd / "node_modules").is_dir():
                checks.append({"name": f"TypeScript compiler ({config.parent.as_posix() or '.'})", "language": "TypeScript / TSX", "status": "skipped", "files_checked": 0, "detail": "Project node_modules are not installed; no package download or install was attempted."})
                continue
            if not shutil.which("tsc"):
                checks.append({"name": f"TypeScript compiler ({config.parent.as_posix() or '.'})", "language": "TypeScript / TSX", "status": "skipped", "files_checked": 0, "detail": "tsc is not installed; use the project build/typecheck script or install the TypeScript toolchain."})
                continue
            _add_cmd_check(checks, issues, f"TypeScript typecheck ({config.parent.as_posix() or '.'})", "TypeScript / TSX", ["tsc", "--noEmit", "--pretty", "false"], cwd, 180)

    # Project-root toolchains may check many files and dependency relationships at once.
    if any(p.name == "go.mod" for p in paths):
        cwd = next((Path(pf.root) / Path(*p.parts[:-1]) for p in paths if p.name == "go.mod"), root)
        for label, args in (("Go build", ["go", "build", "./..."]), ("Go vet", ["go", "vet", "./..."]), ("Go tests", ["go", "test", "./..."])):
            _add_cmd_check(checks, issues, label, "Go", args, cwd, 120)
    if any(p.name == "Cargo.toml" for p in paths):
        cargo_file = next(p for p in paths if p.name == "Cargo.toml")
        cwd = root / Path(*cargo_file.parts[:-1])
        _add_cmd_check(checks, issues, "Rust cargo check (offline)", "Rust", ["cargo", "check", "--offline", "--locked"], cwd, 180)
    if any(p.name == "pom.xml" for p in paths):
        cwd = next(Path(pf.root) / Path(*p.parts[:-1]) for p in paths if p.name == "pom.xml")
        _add_cmd_check(checks, issues, "Java Maven tests", "Java", ["mvn", "-q", "-B", "test"], cwd, 240)
    if any(p.suffix.lower() == ".csproj" or p.name.endswith(".sln") for p in paths):
        dirs = sorted({str(root / Path(*p.parts[:-1])) for p in paths if p.suffix.lower() == ".csproj" or p.name.endswith(".sln")})
        for d in dirs[:5]:
            _add_cmd_check(checks, issues, f".NET build ({Path(d).relative_to(root).as_posix() or '.'})", "C#", ["dotnet", "build", "--nologo", "-v", "q"], Path(d), 180)
    if any(p.suffix.lower() == ".dart" for p in paths):
        dart_cwd = next((root / Path(*p.parts[:-1]) for p in paths if p.name == "pubspec.yaml"), root)
        _add_cmd_check(checks, issues, "Dart analyzer", "Dart", ["dart", "analyze"], dart_cwd, 120)
    # Gradle/Kotlin/PowerShell/GraphQL/etc are surfaced as unsupported unless an existing
    # package-level script has validated them; never pretend a generic check is a compiler.
    advanced = {
        "Kotlin": lambda e: e in {".kt", ".kts"}, "PowerShell": lambda e: e in {".ps1", ".psm1"},
        "GraphQL": lambda e: e in {".graphql", ".gql"}, "Scala": lambda e: e in {".scala", ".sc"},
        "Elixir": lambda e: e in {".ex", ".exs"}, "Erlang": lambda e: e in {".erl", ".hrl"},
        "Clojure": lambda e: e in {".clj", ".cljs"}, "Haskell": lambda e: e in {".hs", ".lhs"},
        "R": lambda e: e == ".r", "Lua": lambda e: e == ".lua", "Perl": lambda e: e in {".pl", ".pm"},
        "Protocol Buffers": lambda e: e == ".proto", "Sass": lambda e: e in {".sass", ".scss"}, "Vue SFC": lambda e: e == ".vue", "Svelte": lambda e: e == ".svelte",
    }
    for lang, predicate in advanced.items():
        matching = [x for x in files if predicate(PurePosixPath(x).suffix.lower())]
        if matching and not any(c.get("language") == lang and c.get("status") in {"passed", "failed"} for c in checks):
            checks.append({"name": f"{lang} compiler/linter", "language": lang, "status": "skipped", "files_checked": 0, "detail": f"Detected {len(matching)} file(s), but no safe compiler adapter or applicable declared script is configured for this language."})


def _safe_file_command(rel: str) -> tuple[list[str], str] | None:
    """Commands whose grammar-check mode parses/types a source without running it."""
    ext = PurePosixPath(rel).suffix.lower()
    if ext == ".php": return ["php", "-l", rel], "PHP"
    if ext == ".rb": return ["ruby", "-c", rel], "Ruby"
    if ext in {".sh", ".bash"}: return ["bash", "-n", rel], "Shell"
    if ext == ".swift": return ["swiftc", "-typecheck", rel], "Swift"
    if ext in {".c", ".h"}:
        compiler = next((x for x in ("gcc", "clang") if shutil.which(x)), "gcc")
        return [compiler, "-fsyntax-only", rel], "C"
    if ext in {".cc", ".cpp", ".cxx", ".hh", ".hpp", ".hxx"}:
        compiler = next((x for x in ("g++", "clang++", "c++") if shutil.which(x)), "g++")
        return [compiler, "-fsyntax-only", rel], "C++"
    return None


def _run_safe_file_parsers(pf, files: list[str], checks: list[dict], issues: list[dict], per_language: dict[str, dict[str, int]]) -> None:
    """Use installed parser-only modes where available; no project build scripts are run."""
    done: set[str] = set()
    unavailable: dict[str, list[str]] = defaultdict(list)
    for rel in files:
        pair = _safe_file_command(rel)
        if not pair:
            continue
        args, lang = pair
        if not shutil.which(args[0]):
            unavailable[lang].append(rel)
            per_language[lang]["skipped"] += 1
            continue
        if len(done) >= 100:
            checks.append({"name": f"{lang} parser", "language": lang, "status": "skipped", "files_checked": len(done), "detail": "The parser cap of 100 files was reached."})
            break
        result = _run(args, Path(pf.root), timeout=30)
        done.add(rel)
        per_language[lang]["checked"] += 1
        if result.get("code") == 0:
            continue
        if result.get("code") == 127:
            per_language[lang]["skipped"] += 1
            continue
        detail = str(result.get("out") or f"exit code {result.get('code')}")[:600]
        m = re.search(r"(?:line\s+|:(\d+)(?::\d+)?)", detail, re.I)
        line = int(m.group(1)) if m and m.group(1) else None
        issues.append(_issue(rel, detail, line=line, tool=args[0]))
        per_language[lang]["failed"] += 1
    if done:
        checks.append({"name": "Installed syntax-only compilers", "language": "Multiple", "status": "failed" if any(i.get("tool") in {"php", "ruby", "bash", "swiftc", "gcc", "clang", "g++", "clang++", "c++"} for i in issues) else "passed", "files_checked": len(done), "detail": "Used installed parser-only modes for PHP, Ruby, shell, Swift, C, or C++; missing toolchains are not reported as passes."})
    for lang, paths in sorted(unavailable.items()):
        checks.append({"name": f"{lang} parser/compiler", "language": lang, "status": "skipped", "files_checked": 0, "detail": f"Detected {len(paths)} source file(s), but {lang}'s syntax-only tool is not installed; no syntax pass is claimed."})


def analyze_project(pf, deep: bool = False, include_redundancy: bool = True) -> dict[str, Any]:
    """Analyze syntax, logic red flags, redundancy, and available language coverage.

    ``deep=False`` is deterministic and does not execute project build scripts.
    ``deep=True`` runs only recognized checks using already-installed local toolchains.
    ``include_redundancy=False`` is intended for repair-loop syntax gating to avoid
    repeating advisory analysis during every retry.
    """
    files, truncated = _files(pf)
    counts = Counter(EXT_LANGUAGE.get(PurePosixPath(f).suffix.lower(), "Configuration") for f in files)
    checks: list[dict] = []
    issues: list[dict] = []
    per_language: dict[str, dict[str, int]] = defaultdict(lambda: {"files": 0, "checked": 0, "failed": 0, "skipped": 0})
    read_failures = 0
    node_available = bool(shutil.which("node"))
    js_check_count = 0

    for rel in files:
        ext = PurePosixPath(rel).suffix.lower()
        lang = EXT_LANGUAGE.get(ext, "Configuration")
        per_language[lang]["files"] += 1
        try:
            source = _read(pf, rel)
        except (OSError, ValueError, UnicodeError) as exc:
            read_failures += 1
            issues.append(_issue(rel, f"file could not be analyzed: {type(exc).__name__}", severity="warning", category="coverage", tool="filesystem"))
            per_language[lang]["skipped"] += 1
            continue
        _, file_issues = _simple_syntax(rel, source)
        # Python redundancy/logic is AST-based, more precise than line matching.
        if include_redundancy and ext in {".py", ".pyw", ".pyi"}:
            file_issues.extend(_python_issues(source, rel))
        elif include_redundancy and ext in GENERIC_LOGIC_EXTS:
            file_issues.extend(_generic_logic_issues(source, rel))
        if ext in {".js", ".mjs", ".cjs"}:
            if node_available and js_check_count < 100:
                res = _run(["node", "--check", rel], Path(pf.root), timeout=30)
                js_check_count += 1
                if res.get("code") == 127:
                    checks.append({"name": "JavaScript parser", "language": lang, "status": "skipped", "files_checked": 0, "detail": "Node.js is not available."})
                elif res.get("code") != 0:
                    detail = str(res.get("out") or "Node syntax check failed")[:600]
                    m = re.search(r"(?:^|\s|\()(?:(?:[^\s():]+)[/\\])?[^\s():]+:(\d+)(?::\d+)?", detail)
                    issues.append(_issue(rel, detail, line=int(m.group(1)) if m else None, tool="node --check"))
            # When Node is absent, the file is recorded as skipped, never counted passed.
        elif ext in {".vue", ".svelte", ".tsx", ".jsx", ".ts"}:
            # These need a framework/compiler parser; don't run Node's JS parser on JSX/TS.
            pass
        # Any source syntax issue is added; other results may be advisory.
        issues.extend(file_issues)
        direct_parser_exts = {".py", ".pyw", ".pyi", ".json", ".jsonc", ".toml", ".xml", ".xsl", ".xslt", ".svg", ".css", ".scss", ".sass", ".html", ".htm"}
        if ext in direct_parser_exts and not any(i.get("severity") == "error" and i.get("file") == rel for i in file_issues):
            per_language[lang]["checked"] += 1
        if any(i.get("severity") == "error" and i.get("file") == rel for i in file_issues):
            per_language[lang]["failed"] += 1
        elif ext in {".js", ".mjs", ".cjs"} and node_available and js_check_count <= 100:
            per_language[lang]["checked"] += 1
        elif ext in {".js", ".mjs", ".cjs"} and not node_available:
            per_language[lang]["skipped"] += 1
        elif ext not in direct_parser_exts and ext not in {".js", ".mjs", ".cjs"}:
            # Compiler/framework-dependent files get validated by deep project checks, when possible.
            per_language[lang]["skipped"] += 1

    # Installed syntax-only compiler adapters provide additional coverage without
    # invoking user-defined build scripts. They are safe for the default scan.
    _run_safe_file_parsers(pf, files, checks, issues, per_language)

    # Tool coverage by language; group each actual deterministic check.
    checks.append({"name": "Source and configuration parsers", "language": "Multiple", "status": "failed" if any(i.get("severity") == "error" and i.get("tool") not in {"node --check"} for i in issues) else "passed", "files_checked": sum(v["checked"] for v in per_language.values()), "detail": "Used built-in parsers for Python, JSON/JSONC, TOML, XML, HTML tag balance, and CSS delimiters where present. Node --check is applied to JavaScript only; TypeScript/JSX needs its project compiler."})
    if node_available and js_check_count:
        checks.append({"name": "JavaScript syntax (Node.js)", "language": "JavaScript", "status": "failed" if any(i.get("tool") == "node --check" for i in issues) else "passed", "files_checked": js_check_count, "detail": "Node syntax parser ran on up to 100 .js/.mjs/.cjs files."})
    elif counts.get("JavaScript", 0):
        checks.append({"name": "JavaScript syntax (Node.js)", "language": "JavaScript", "status": "skipped", "files_checked": 0, "detail": "Node.js is not installed or no JavaScript source was eligible for parsing."})

    # Redundancy analysis is advisory and must never block a verified compile.
    programming_file_count = sum(1 for rel in files if PurePosixPath(rel).suffix.lower() in PROGRAMMING_EXTS)
    if include_redundancy:
        redundancy = [x for x in issues if x.get("category") in {"redundancy", "logic"}]
        redundancy.extend(_redundancy_lines(pf, files))
        issues = [x for x in issues if x.get("category") not in {"redundancy", "logic"}]
        redundancy = redundancy[:MAX_REDUNDANCY]
    else:
        redundancy = []
        issues = [x for x in issues if x.get("category") not in {"redundancy", "logic"}]

    if deep:
        _deep_checks(pf, files, checks, issues)

    # State coverage gaps explicitly. Detected files are never treated as verified
    # merely because no compiler was installed or a language lacks a built-in parser.
    compile_dependent = {
        ".tsx", ".jsx", ".ts", ".vue", ".svelte", ".go", ".rs", ".java", ".kt", ".kts",
        ".cs", ".dart", ".sql", ".graphql", ".gql", ".proto", ".ex", ".exs", ".erl", ".hrl",
        ".yaml", ".yml", ".sass", ".scss", ".ps1", ".psm1", ".php", ".rb", ".sh", ".bash", ".swift",
        ".c", ".h", ".cc", ".cpp", ".cxx", ".hh", ".hpp", ".hxx",
        ".clj", ".cljs", ".scala", ".sc", ".r", ".lua", ".pl", ".pm", ".hs", ".lhs", ".ps1", ".psm1",
    }
    checks.append({"name": "Compiler coverage gaps", "language": "Multiple", "status": "passed", "files_checked": 0,
                   "detail": "Languages without a successful applicable parser/compiler are listed below as skipped; this is not proof of syntax correctness."})
    for lang in sorted({EXT_LANGUAGE.get(PurePosixPath(f).suffix.lower(), "") for f in files}):
        matching = [f for f in files if EXT_LANGUAGE.get(PurePosixPath(f).suffix.lower(), "") == lang]
        if not matching:
            continue
        relevant_exts = {PurePosixPath(f).suffix.lower() for f in matching}
        needs_toolchain = bool(relevant_exts & compile_dependent)
        if not needs_toolchain:
            continue
        checked_count = per_language[lang]["checked"]
        toolchain_done = any(c.get("status") in {"passed", "failed"} and c.get("language") and (lang == c.get("language") or lang in str(c.get("language")).split(", ")) and c.get("name") not in {"Source and configuration parsers", "Compiler coverage gaps"} for c in checks)
        if checked_count == 0 and not toolchain_done:
            checks.append({"name": f"{lang} compiler/type checker", "language": lang, "status": "skipped", "files_checked": 0,
                           "detail": f"Detected {len(matching)} file(s), but no applicable installed parser/compiler or successful project typecheck/build result was available. Install/configure the toolchain or add a project script, then rerun deep analysis."})

    if truncated:
        notes = [f"Scan reached {MAX_FILES} files; the full project may contain additional unreviewed files."]
    else:
        notes = []
    if read_failures: notes.append(f"{read_failures} file(s) could not be read and were not analyzed.")
    if include_redundancy:
        notes.append("Redundancy and logic findings are conservative review hints, not proof of a bug. No automatic cleanup or source edits were made.")
    if programming_file_count > MAX_REDUNDANCY_FILES:
        notes.append(f"To keep analysis responsive, duplicate-code heuristics inspected the first {MAX_REDUNDANCY_FILES} programming files; syntax checks still scanned the supported project files within the scan limit.")
    if not deep:
        notes.append("Build/type/lint/test commands were not run. Select the deeper check option to run existing local tools; dependencies are never installed automatically.")
    checks = checks[:80]
    issues = issues[:MAX_ISSUES]
    return {
        "status": _status(checks, issues), "deep": deep,
        "files_scanned": len(files), "truncated": truncated,
        "languages": [{"name": name, **values} for name, values in sorted(per_language.items(), key=lambda x: (-x[1]["files"], x[0]))],
        "checks": checks,
        "issues": issues,
        "redundancy": redundancy,
        "summary": f"Scanned {len(files)} source/configuration files across {len(counts)} detected language groups; found {len([x for x in issues if x['severity'] == 'error'])} error(s), {len([x for x in issues if x['severity'] == 'warning'])} warning(s), and {len(redundancy)} redundancy/logic hint(s).",
        "notes": notes,
        "scope": "A practical multi-language static analysis layer with optional installed-toolchain checks; not a formal proof of program correctness.",
    }

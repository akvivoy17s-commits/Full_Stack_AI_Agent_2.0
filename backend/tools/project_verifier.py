"""Deterministic verification for generated backend projects.

The default pass is non-networked: Python source is compiled, JavaScript is syntax-
checked when Node.js exists, and JSON manifests/contracts are parsed. Deep mode runs
only declared, allowlisted project checks when dependencies are already installed;
it never installs packages or edits the generated project.
"""
from __future__ import annotations

import importlib.util
import json
import os
import shutil
from pathlib import Path

from backend.tools import terminal

_SKIP_DIRS = {".git", ".agent", "node_modules", ".venv", "venv", "__pycache__", "dist", "build", "target"}
_SOURCE_EXTS = {".py", ".js", ".mjs", ".cjs", ".json", ".ts", ".tsx", ".jsx"}
_MAX_SCAN_FILES = 1500
_MAX_DETAIL = 700


def _check(name: str, status: str, detail: str = "") -> dict:
    return {"name": name, "viewport": "backend", "status": status, "detail": detail[:_MAX_DETAIL]}


def _files(root: Path):
    count = 0
    for parent, dirs, names in os.walk(root, followlinks=False):
        dirs[:] = sorted(d for d in dirs if d.lower() not in _SKIP_DIRS and not (Path(parent) / d).is_symlink())
        for name in sorted(names):
            path = Path(parent) / name
            if path.is_symlink() or path.suffix.lower() not in _SOURCE_EXTS:
                continue
            yield path
            count += 1
            if count >= _MAX_SCAN_FILES:
                return


def _relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def _run(args: list[str], cwd: Path, timeout: int = 120) -> dict:
    try:
        return terminal.run(args, cwd=str(cwd), timeout=timeout, max_out=2400)
    except (OSError, ValueError) as exc:
        return {"code": 1, "out": f"verification could not run: {type(exc).__name__}: {exc}"}


def _environment_contract(root: Path) -> tuple[str, str]:
    """Check the most important runtime-secret plumbing without exposing any values."""
    example = root / ".env.example"
    if not example.is_file() or example.is_symlink():
        return "skipped", "No backend/.env.example exists; environment contract checks are not applicable to this backend."
    try:
        sample = example.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return "failed", "backend/.env.example could not be read."
    gitignore = root / ".gitignore"
    try:
        rules = gitignore.read_text(encoding="utf-8").splitlines() if gitignore.is_file() and not gitignore.is_symlink() else []
    except (OSError, UnicodeError):
        rules = []
    ignored = any(x.strip() in (".env", ".env.*", "**/.env", "**/.env.*") for x in rules)
    example_allowed = "!.env.example" in [x.strip() for x in rules]

    loader = False
    integration_helper = False
    for parent, dirs, names in os.walk(root, followlinks=False):
        dirs[:] = [d for d in dirs if d.lower() not in _SKIP_DIRS and not (Path(parent) / d).is_symlink()]
        for name in names:
            path = Path(parent) / name
            if path.is_symlink() or path.suffix.lower() not in {".py", ".js", ".mjs", ".cjs", ".ts", ".properties", ".java"}:
                continue
            try:
                content = path.read_text(encoding="utf-8")
            except (OSError, UnicodeError):
                continue
            if (
                "load_dotenv(" in content
                or "dotenv/config" in content
                or "dotenv').config()" in content
                or 'dotenv").config()' in content
                or "spring.config.import=optional:file:.env" in content
            ):
                loader = True
            if ("externalApis" in content or "external_apis" in content or "ExternalApiEnvironment" in content):
                integration_helper = True
    problems = []
    if not ignored:
        problems.append(".env / .env.* are not ignored by backend/.gitignore")
    if not example_allowed:
        problems.append("backend/.gitignore must explicitly allow .env.example after ignoring .env files")
    if not loader:
        problems.append("no runtime .env loader / Spring .env import was found")
    # If the example declares a third-party API key, generated code must expose a runtime
    # environment accessor/config entry so integration code never needs a literal key.
    names = []
    for line in sample.splitlines():
        match = __import__("re").match(r"^\s*([A-Z][A-Z0-9_]+)\s*=", line)
        if match:
            names.append(match.group(1))
    has_external_key = any(__import__("re").search(r"(?:API_KEY|API_TOKEN|CLIENT_SECRET|SERVICE_ROLE_KEY|ACCESS_TOKEN)$", name) for name in names)
    if has_external_key and not integration_helper:
        # Existing built-in payment/storage config is an acceptable accessor for known vars.
        known = any(name.startswith(("STRIPE_", "RAZORPAY_", "PAYPAL_", "S3_", "FIREBASE_", "LLM_", "SMTP_", "AI_SERVICE_")) for name in names)
        if not known:
            problems.append("external API keys exist but no runtime env-access helper/config is generated")
    if problems:
        return "failed", "; ".join(problems)
    return "passed", "Backend .env.example uses a runtime loader; private env files are ignored and the example remains committable."


def verify_backend(pf, deep: bool = False) -> dict:
    """Return checks + actionable issues for `<project>/backend`.

    `blocking_issues` contains semantic-contract failures and deep command/test
    failures. Basic source syntax failures are also returned in `issues`; the
    orchestrator's existing syntax repair pipeline consumes those project files.
    """
    root = Path(pf.root) / "backend"
    checks: list[dict] = []
    issues: list[dict] = []
    blocking: list[dict] = []

    if not root.is_dir() or root.is_symlink():
        checks.append(_check("backend project", "skipped", "No generated backend/ directory exists for this project."))
        return {"status": "skipped", "deep": deep, "checks": checks, "issues": [],
                "blocking_issues": [], "note": "Frontend-only project; backend checks were not applicable."}

    node_available = bool(shutil.which("node"))
    py_count = js_count = json_count = ts_count = js_checked = 0
    checked_source = 0
    for path in _files(root):
        rel = _relative(path, pf.root)
        ext = path.suffix.lower()
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            issues.append({"file": rel, "message": f"could not read source file: {type(exc).__name__}"})
            continue
        checked_source += 1
        if ext == ".py":
            py_count += 1
            try:
                compile(text, rel, "exec")
            except SyntaxError as exc:
                issues.append({"file": rel, "message": f"Python syntax error at line {exc.lineno}: {exc.msg}"})
        elif ext == ".json":
            json_count += 1
            try:
                parsed = json.loads(text)
                if path.name == ".agent-manifest.json":
                    if not isinstance(parsed, dict) or not isinstance(parsed.get("generator"), str):
                        message = "backend manifest must contain a generator name"
                        issues.append({"file": rel, "message": message})
                        blocking.append({"message": f"{rel}: {message}"})
                    if isinstance(parsed, dict) and "routes" in parsed and not isinstance(parsed.get("routes"), list):
                        message = "backend manifest routes must be a list"
                        issues.append({"file": rel, "message": message})
                        blocking.append({"message": f"{rel}: {message}"})
                if path.name == "openapi.json" and not (isinstance(parsed, dict) and all(k in parsed for k in ("openapi", "info", "paths"))):
                    message = "OpenAPI document must contain openapi, info, and paths"
                    issues.append({"file": rel, "message": message})
                    blocking.append({"message": f"{rel}: {message}"})
            except (ValueError, TypeError) as exc:
                issues.append({"file": rel, "message": f"invalid JSON: {str(exc)[:160]}"})
        elif ext in (".js", ".mjs", ".cjs"):
            js_count += 1
            if node_available:
                result = _run(["node", "--check", rel], pf.root, timeout=20)
                if result["code"] != 127:
                    js_checked += 1
                if result["code"] not in (0, 127):
                    issues.append({"file": rel, "message": f"JavaScript syntax check failed: {result['out'][-350:]}"})
        elif ext in (".ts", ".tsx", ".jsx"):
            ts_count += 1

    syntax_failed = bool(issues)
    source_detail = f"Scanned {checked_source} file(s): {py_count} Python, {js_count} JavaScript, {json_count} JSON, {ts_count} TypeScript/JSX."
    if js_count and not node_available:
        source_detail += " Node.js unavailable; JavaScript syntax checks were skipped."
    if ts_count:
        source_detail += " TypeScript/JSX build validation requires deep mode and installed project dependencies."
    parseable_count = py_count + json_count + js_checked
    source_status = "failed" if syntax_failed else ("passed" if parseable_count else "skipped")
    checks.append(_check("backend static syntax + JSON", source_status,
                         source_detail + (" " + "; ".join(i["message"] for i in issues[:3]) if syntax_failed else "")))

    manifest = root / ".agent-manifest.json"
    if manifest.is_file() and not manifest.is_symlink():
        checks.append(_check("backend generation manifest", "failed" if any(i["file"] == "backend/.agent-manifest.json" for i in issues) else "passed",
                             "Manifest parsed and basic structure checked."))
    else:
        checks.append(_check("backend generation manifest", "skipped", "No generated-backend manifest was included."))

    openapi = root / "openapi.json"
    if openapi.is_file() and not openapi.is_symlink():
        invalid_openapi = any(i["file"] == "backend/openapi.json" for i in issues)
        checks.append(_check("OpenAPI contract", "failed" if invalid_openapi else "passed",
                             "OpenAPI JSON structure checked; route behavior still requires runtime tests."))
    else:
        checks.append(_check("OpenAPI contract", "skipped", "No OpenAPI contract was generated."))

    env_status, env_detail = _environment_contract(root)
    checks.append(_check("environment variables / secrets", env_status, env_detail))
    if env_status == "failed":
        issues.append({"file": "backend/.env.example", "message": env_detail})
        blocking.append({"message": "Environment contract is incomplete: " + env_detail})

    if not deep:
        checks.append(_check("backend build / test scripts", "skipped",
                             "Deep check not requested. Use 'Deep full-stack check' to run declared scripts when dependencies are already installed."))
    else:
        _run_deep_checks(root, checks, blocking)

    statuses = [c["status"] for c in checks]
    if "failed" in statuses:
        status = "failed"
    elif statuses and all(s == "skipped" for s in statuses):
        status = "skipped"
    else:
        status = "passed"
    return {"status": status, "deep": deep, "checks": checks, "issues": issues,
            "blocking_issues": blocking,
            "note": "Deep verification never installs dependencies or changes project files." if deep else "Static backend checks only; runtime tests were not executed."}


def _run_deep_checks(root: Path, checks: list[dict], blocking: list[dict]) -> None:
    """Run only package scripts declared by the generated project's own manifest.

    Dependencies are never installed automatically. This keeps verification bounded
    and avoids silently doing network access during a check.
    """
    package = root / "package.json"
    if package.is_file() and not package.is_symlink():
        try:
            pkg = json.loads(package.read_text(encoding="utf-8"))
            scripts = pkg.get("scripts", {}) if isinstance(pkg, dict) else {}
            if not isinstance(scripts, dict):
                raise ValueError("package.json scripts must be an object")
        except (OSError, ValueError, TypeError) as exc:
            checks.append(_check("backend npm scripts", "failed", f"Cannot read package.json scripts: {exc}"))
            blocking.append({"message": "backend package.json scripts are invalid"})
            scripts = {}
        if not (root / "node_modules").is_dir():
            names = [n for n in ("typecheck", "build", "lint", "test") if n in scripts]
            if names:
                checks.append(_check("backend npm scripts", "skipped",
                                     f"Dependencies are not installed; did not run: {', '.join(names)}. Install them manually, then retry."))
            else:
                checks.append(_check("backend npm scripts", "skipped", "No supported typecheck/build/lint/test scripts are declared."))
        else:
            ran = False
            for name, timeout in (("typecheck", 120), ("build", 180), ("lint", 120), ("test", 180)):
                if name not in scripts:
                    continue
                ran = True
                result = _run(["npm", "run", name], root, timeout=timeout)
                good = result["code"] == 0
                checks.append(_check(f"backend npm {name}", "passed" if good else "failed",
                                     "Exit code 0." if good else f"Exit code {result['code']}: {result['out']}"))
                if not good:
                    blocking.append({"message": f"backend npm {name} failed (exit {result['code']}): {result['out'][-500:]}"})
            if not ran:
                checks.append(_check("backend npm scripts", "skipped", "No supported typecheck/build/lint/test scripts are declared."))
    else:
        checks.append(_check("backend npm scripts", "skipped", "No backend/package.json was generated."))

    if (root / "requirements.txt").is_file():
        test_root = root / "tests"
        test_files = []
        if test_root.is_dir() and not test_root.is_symlink():
            test_files = [p for p in test_root.rglob("*.py") if p.is_file() and not p.is_symlink()
                          and (p.name.startswith("test_") or p.name.endswith("_test.py"))]
        if not test_files:
            checks.append(_check("backend Python tests", "skipped", "No backend pytest files were generated."))
        else:
            venv_python = next((p for p in (".venv/Scripts/python.exe", ".venv/bin/python", "venv/Scripts/python.exe", "venv/bin/python")
                                if (root / p).is_file()), None)
            if not venv_python and not importlib.util.find_spec("pytest"):
                checks.append(_check("backend Python tests", "skipped", "pytest is not installed in the agent environment, and no backend virtual-environment Python was found."))
                return
            python_cmd = venv_python or "python"
            result = _run([python_cmd, "-m", "pytest", "-q", "-x", "--tb=short", "-p", "no:cacheprovider", "tests"], root, timeout=240)
            good = result["code"] == 0
            checks.append(_check("backend Python tests", "passed" if good else "failed",
                                 "Exit code 0." if good else f"Exit code {result['code']}: {result['out']}"))
            if not good:
                blocking.append({"message": f"backend Python tests failed (exit {result['code']}): {result['out'][-500:]}"})
    elif any(root.glob("*.py")):
        checks.append(_check("backend Python tests", "skipped", "No requirements.txt/test contract was found."))

    pom = root / "pom.xml"
    if pom.is_file() and not pom.is_symlink():
        if not shutil.which("mvn"):
            checks.append(_check("backend Maven tests", "skipped", "Maven is not installed."))
        else:
            result = _run(["mvn", "-q", "-B", "test"], root, timeout=300)
            good = result["code"] == 0
            checks.append(_check("backend Maven tests", "passed" if good else "failed",
                                 "Exit code 0." if good else f"Exit code {result['code']}: {result['out']}"))
            if not good:
                blocking.append({"message": f"backend Maven tests failed (exit {result['code']}): {result['out'][-500:]}"})

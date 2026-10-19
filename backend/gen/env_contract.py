"""Generate environment-aware helpers and docs for generated backend projects.

API credentials are values supplied by the developer at runtime. The generator writes
variable names/placeholders only, exposes server-side integration values through a
small allowlisted config object, and never copies a real .env file into generated output.
"""
from __future__ import annotations

import json
import re

from backend.spec import env_contract as spec_env


def _quoted_js(names: list[str]) -> str:
    return json.dumps(names, ensure_ascii=False)


def _service_names(spec: dict) -> list[str]:
    names = []
    for entry in spec_env.external_entries(spec):
        name = str(entry.get("name", ""))
        if re.fullmatch(r"[A-Z][A-Z0-9_]{1,79}", name) and name not in names:
            names.append(name)
    return sorted(names)


def _environment_doc(spec: dict, stack: dict) -> str:
    server = [e for e in spec.get("env", []) if e.get("scope") == "server"]
    public = spec_env.public_entries(spec)
    lines = [
        "# Environment variables",
        "",
        "Copy `backend/.env.example` to `backend/.env` and fill in the real values. Keep `backend/.env` local and never commit it.",
        "The example file contains placeholder values only; it never contains live credentials.",
        "",
        "## Server-side configuration",
        "",
        "The backend loads `.env` before configuration is read. Database URLs, private API keys, OAuth client secrets, payment secrets, and service-account paths belong on the server only.",
        "Use the generated config/runtime environment instead of hardcoding a credential. Do not put a server secret in a variable with a browser-public prefix such as `VITE_`, `NEXT_PUBLIC_`, `NUXT_PUBLIC_`, or `PUBLIC_`.",
        "",
    ]
    if server:
        lines += ["| Variable | Purpose | Secret |", "| --- | --- | ---: |"]
        for e in server:
            name = str(e.get("name", ""))
            purpose = str(e.get("purpose", "Configuration" )).replace("|", "\\|")
            lines.append(f"| `{name}` | {purpose} | {'yes' if e.get('secret') else 'no'} |")
    else:
        lines.append("No server environment variables are required by the current spec.")
    lines += ["", "## Public frontend configuration", ""]
    if public:
        lines += ["Only values explicitly marked public appear in the root `.env.example`. Public values are visible to browsers after the frontend is built; never place a private secret here.", "", "| Variable | Purpose |", "| --- | --- |"]
        for e in public:
            name = str(e.get("name", ""))
            purpose = str(e.get("purpose", "Public configuration")).replace("|", "\\|")
            lines.append(f"| `{name}` | {purpose} |")
    else:
        lines.append("No additional public frontend variables are declared. The frontend may still use its default backend URL.")
    lines += [
        "",
        "## Accessing external-service values in backend code",
        "",
    ]
    be = stack.get("backend") or "none"
    service_names = _service_names(spec)
    example_name = service_names[0] if service_names else "YOUR_SERVICE_API_KEY"
    if service_names and be in ("express", "nestjs"):
        if be == "express":
            lines += [
                "```js",
                "const cfg = require('./config');",
                f"const apiKey = cfg.externalApis[{json.dumps(example_name)}];",
                "```",
            ]
        else:
            lines += [
                "```ts",
                "import { cfg } from './config';",
                f"const apiKey = cfg.externalApis[{json.dumps(example_name)}];",
                "```",
            ]
    elif service_names and be in ("fastapi", "flask", "django"):
        lines += [
            "```python",
            "from app.config import cfg",
            f"api_key = cfg.external_apis[{example_name!r}]",
            "```",
        ]
    elif service_names and be == "spring":
        lines += [
            "```java",
            "// Inject ExternalApiEnvironment into a service/controller.",
            f'String apiKey = externalApiEnvironment.require("{example_name}");',
            "```",
        ]
    elif not service_names:
        lines.append("No named external-service credentials are configured yet. When an API is added, declare its key in backend/.env.example and read it via the backend runtime environment/config at the actual request site.")
    else:
        lines.append("Use the selected runtime's environment API (never copy a secret into source code).")
    if spec.get("external_apis"):
        lines += ["", "## Detected external integrations", "", ", ".join(f"`{x}`" for x in spec["external_apis"]), ""]
        lines.append("Keys are configured here, but an environment variable alone does not implement an SDK/API operation. Only report an integration as working after the relevant API client/route and its tests have been generated and verified.")
    lines += [
        "",
        "## Security rules",
        "",
        "- `.env` is ignored by Git; `.env.example` is safe to commit because it contains placeholders only.",
        "- Never send private API keys, database credentials, access tokens, or service-role keys to browser code.",
        "- For frontend features requiring a private credential, call a backend route that uses the key server-side.",
        "- Do not log environment values. Log the variable name or a redacted status only.",
        "- Missing required credentials should produce a clear configuration error; do not silently claim a third-party operation succeeded.",
        "",
    ]
    return "\n".join(lines)


def _node_helper(names: list[str]) -> str:
    encoded = _quoted_js(names)
    return f'''// Generated from the project specification. Values are loaded at runtime, never hard-coded.
require('dotenv').config();
const ALLOWED_EXTERNAL_ENV = new Set({encoded});
function getExternalEnv(name, {{ required = false }} = {{}}) {{
  if (!ALLOWED_EXTERNAL_ENV.has(name)) throw new Error(`Unknown external environment variable: ${{name}}`);
  const value = String(process.env[name] || '').trim();
  if (required && (!value || /^<.*>$/.test(value) || /^your[-_]/i.test(value))) {{
    throw new Error(`Missing required environment variable: ${{name}}`);
  }}
  return value;
}}
function getAllExternalEnv() {{
  return Object.freeze(Object.fromEntries([...ALLOWED_EXTERNAL_ENV].map((name) => [name, getExternalEnv(name)])));
}}
module.exports = {{ getExternalEnv, getAllExternalEnv, ALLOWED_EXTERNAL_ENV }};
'''


def _nest_helper(names: list[str]) -> str:
    encoded = _quoted_js(names)
    return f'''// Generated from the project specification. Values are loaded at runtime, never hard-coded.
import 'dotenv/config';
const ALLOWED_EXTERNAL_ENV = new Set<string>({encoded});
export function getExternalEnv(name: string, required = false): string {{
  if (!ALLOWED_EXTERNAL_ENV.has(name)) throw new Error(`Unknown external environment variable: ${{name}}`);
  const value = String(process.env[name] || '').trim();
  if (required && (!value || /^<.*>$/.test(value) || /^your[-_]/i.test(value))) {{
    throw new Error(`Missing required environment variable: ${{name}}`);
  }}
  return value;
}}
export function getAllExternalEnv(): Readonly<Record<string, string>> {{
  return Object.freeze(Object.fromEntries([...ALLOWED_EXTERNAL_ENV].map((name) => [name, getExternalEnv(name)])));
}}
'''


def _python_helper(names: list[str]) -> str:
    return '''"""Allowlisted access to external API credentials supplied through backend/.env."""
from __future__ import annotations
import os
from dotenv import load_dotenv

load_dotenv()
ALLOWED_EXTERNAL_ENV = frozenset(%s)


def get_external_env(name: str, *, required: bool = False) -> str:
    if name not in ALLOWED_EXTERNAL_ENV:
        raise ValueError(f"Unknown external environment variable: {name}")
    value = os.environ.get(name, "").strip()
    if required and (not value or (value.startswith("<") and value.endswith(">")) or value.lower().startswith("your-")):
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def get_all_external_env() -> dict[str, str]:
    return {name: get_external_env(name) for name in ALLOWED_EXTERNAL_ENV}
''' % repr(names)


def _spring_helper(names: list[str]) -> str:
    java_names = ", ".join('"' + n + '"' for n in names)
    if not java_names:
        java_names = '""'
    return f'''package app.integrations;

import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Set;
import org.springframework.core.env.Environment;
import org.springframework.stereotype.Component;

/** Safe, allowlisted access to external API variables imported by Spring from backend/.env. */
@Component
public final class ExternalApiEnvironment {{
    private static final Set<String> ALLOWED = Set.of({java_names});
    private final Environment environment;

    public ExternalApiEnvironment(Environment environment) {{ this.environment = environment; }}

    public String get(String name) {{
        if (!ALLOWED.contains(name)) throw new IllegalArgumentException("Unknown external environment variable: " + name);
        return environment.getProperty(name, "").trim();
    }}

    public String require(String name) {{
        String value = get(name);
        if (value.isBlank() || (value.startsWith("<") && value.endsWith(">")) || value.toLowerCase().startsWith("your-"))
            throw new IllegalStateException("Missing required environment variable: " + name);
        return value;
    }}

    public Map<String, String> all() {{
        Map<String, String> values = new LinkedHashMap<>();
        for (String name : ALLOWED) values.put(name, get(name));
        return Collections.unmodifiableMap(values);
    }}
}}
'''


def _add_external_api_config(files: dict[str, str], stack: dict, names: list[str]) -> None:
    if not names:
        return
    be = stack.get("backend") or "none"
    quoted = _quoted_js(names)
    if be == "express":
        path = "backend/src/config.js"
        text = files.get(path, "")
        if text and "externalApis:" not in text:
            prop = "  externalApis: Object.freeze(Object.fromEntries(" + quoted + ".map((name) => [name, env[name] || '']))),\n"
            marker = "  wsMaxClients:"
            if marker in text:
                text = text.replace(marker, prop + marker, 1)
                files[path] = text
    elif be == "nestjs":
        path = "backend/src/config.ts"
        text = files.get(path, "")
        if text and "externalApis:" not in text:
            prop = "  externalApis: Object.freeze(Object.fromEntries(" + quoted + ".map((name) => [name, env[name] || '']))),\n"
            marker = "  wsMaxClients:"
            if marker in text:
                text = text.replace(marker, prop + marker, 1)
                files[path] = text
    elif be in ("fastapi", "flask", "django"):
        path = "backend/app/config.py"
        text = files.get(path, "")
        if text and "self.external_apis" not in text:
            prop = f"        self.external_apis = {{name: str(e.get(name, '') or '').strip() for name in {names!r}}}\n"
            marker = "        e = env if env is not None else os.environ\n"
            if marker in text:
                text = text.replace(marker, marker + prop, 1)
                files[path] = text


def enrich_files(files: dict[str, str], spec: dict, stack: dict, existing_frontend_env: str = "") -> dict[str, str]:
    """Add docs/helpers and harden generated env-file ignore patterns."""
    out: dict[str, str] = {}
    names = _service_names(spec)
    be = stack.get("backend") or "none"
    if be != "none":
        out["backend/ENVIRONMENT.md"] = _environment_doc(spec, stack)
        if names:
            if be == "express":
                out["backend/src/lib/external-env.js"] = _node_helper(names)
            elif be == "nestjs":
                out["backend/src/external-env.ts"] = _nest_helper(names)
            elif be in ("fastapi", "flask", "django"):
                out["backend/app/external_env.py"] = _python_helper(names)
            elif be == "spring":
                out["backend/src/main/java/app/integrations/ExternalApiEnvironment.java"] = _spring_helper(names)
            _add_external_api_config(files, stack, names)

        ignore_path = "backend/.gitignore"
        current = files.get(ignore_path, "")
        required_lines = [".env", ".env.*", "!.env.example"]
        rows = current.splitlines()
        for row in required_lines:
            if row not in rows:
                rows.append(row)
        # Keep the exception after the broad ignore rules, otherwise .env.example would stay ignored.
        rows = [r for r in rows if r != "!.env.example"] + ["!.env.example"]
        out[ignore_path] = "\n".join(rows).rstrip() + "\n"

    # Public values belong in the frontend root .env.example, never in backend/.env.example.
    public_entries = spec_env.public_entries(spec)
    rows = ["# Public frontend configuration only. Values below are visible in the browser after build."]
    current_rows = existing_frontend_env.splitlines()
    existing_values = {}
    for line in current_rows:
        match = re.match(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$", line)
        if match:
            existing_values[match.group(1)] = match.group(2)
    added = set()
    for e in public_entries:
        name = str(e["name"])
        if name in added:
            continue
        value = str(e.get("placeholder", "your-value"))
        rows += [f"# {e.get('purpose', 'Public configuration')}", f"{name}={existing_values.get(name, value)}"]
        added.add(name)
    if "VITE_API_URL" not in added:
        rows += ["# Optional backend base URL used by the web client", f"VITE_API_URL={existing_values.get('VITE_API_URL', 'http://localhost:8000')}"]
    out[".env.example"] = "\n".join(rows) + "\n"

    root_ignore = files.get(".gitignore", "")
    root_rows = root_ignore.splitlines()
    for row in (".env", ".env.*"):
        if row not in root_rows:
            root_rows.append(row)
    root_rows = [r for r in root_rows if r != "!.env.example"] + ["!.env.example"]
    out[".gitignore"] = "\n".join(root_rows).rstrip() + "\n"
    return out


def public_env_example(spec: dict, existing: str = "") -> str:
    """Create the frontend .env.example with only explicitly-public variables."""
    values: dict[str, str] = {}
    for line in str(existing or "").splitlines():
        m = re.match(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$", line)
        if m:
            values[m.group(1)] = m.group(2)
    entries = spec_env.public_entries(spec)
    rows = ["# Public frontend configuration only. Never put a private server secret here."]
    seen = set()
    for item in entries:
        name = str(item.get("name", ""))
        if not name or name in seen:
            continue
        seen.add(name)
        rows += [f"# {item.get('purpose', 'Public configuration')}", f"{name}={values.get(name, item.get('placeholder', 'your-value'))}"]
    if "VITE_API_URL" not in seen:
        rows += ["# Optional backend base URL used by the web client", f"VITE_API_URL={values.get('VITE_API_URL', 'http://localhost:8000')}"]
    return "\n".join(rows) + "\n"

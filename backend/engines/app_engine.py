"""Schema-driven interactive React application generator.

This is intentionally deterministic: app-style briefs produce a real CRUD workspace
that uses the generated API when one exists, and localStorage when the selected stack
has no server/database. The generated UI contains real forms, search, create, edit,
delete, loading/error/empty states, and optional JWT/session sign-in. It never pretends
that an unavailable remote integration succeeded.
"""
from __future__ import annotations

import json
import re
from html import escape

from backend import spec as spec_engine

SYSTEM_FIELDS = {"id", "created_at", "updated_at", "password_hash", "token_hash"}
AUTH_METHODS = {"jwt", "session"}


def _json(value) -> str:
    # JSON is valid JavaScript/TypeScript data syntax; keep '<' escaped so strings cannot
    # terminate a future HTML script if this payload is moved into an HTML template.
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")


def _field_view(field: dict) -> dict:
    typ = field.get("type", "string")
    return {
        "name": str(field.get("name", "field")),
        "type": typ if typ in {"string", "text", "int", "float", "bool", "datetime", "email", "url", "enum", "ref"} else "string",
        "required": bool(field.get("required")),
        "values": [str(v)[:60] for v in field.get("values", [])[:30]] if isinstance(field.get("values"), list) else [],
        "label": re.sub(r"[_-]+", " ", str(field.get("name", "field"))).strip().title(),
    }


def _entities(spec: dict) -> list[dict]:
    out = []
    for e in (spec.get("data", {}).get("entities") or []):
        name = str(e.get("name", ""))
        if not name or name == "User":
            continue
        fields = []
        for raw in e.get("fields", []):
            fname = str(raw.get("name", ""))
            if fname in SYSTEM_FIELDS or fname.endswith("_id") and raw.get("ref") == "User" or raw.get("ref") == "User":
                continue
            if not re.fullmatch(r"[a-z][a-z0-9_]{0,30}", fname):
                continue
            fields.append(_field_view(raw))
        fields = fields[:16]
        if fields:
            path = str(e.get("path") or name.lower() + "s")
            if not re.fullmatch(r"[a-z0-9-]{1,50}", path):
                path = name.lower() + "s"
            out.append({"name": name, "path": path, "label": re.sub(r"([a-z])([A-Z])", r"\1 \2", name), "fields": fields})
    return out[:12]


def _ent(name: str, path: str, fields: list[tuple]) -> dict:
    """Compact entity builder: fields are (name, label, type, required[, enum values])."""
    return {"name": name, "path": path, "label": path.capitalize(), "fields": [
        {"name": f[0], "label": f[1], "type": f[2], "required": f[3], "values": list(f[4]) if len(f) > 4 else []} for f in fields]}


def _domain_entities(text: str) -> list[dict]:
    if re.search(r"\b(task manager|task management|to-?do|kanban|project planner|task tracker)\b", text):
        fields = [
            ("title", "Title", "string", True),
            ("description", "Description", "text", False),
            ("status", "Status", "enum", True, ["todo", "in-progress", "blocked", "done"]),
            ("priority", "Priority", "enum", True, ["low", "medium", "high", "urgent"]),
            ("due_date", "Due date", "datetime", False),
            ("category", "Category", "string", False),
        ]
        task = _ent("Task", "tasks", fields)
        if re.search(r"\b(project management|projects and tasks|multiple projects)\b", text):
            project = _ent("Project", "projects", [
                ("name", "Project name", "string", True),
                ("description", "Description", "text", False),
                ("status", "Status", "enum", True, ["planned", "active", "on-hold", "completed"]),
                ("due_date", "Due date", "datetime", False),
            ])
            return [project, task]
        return [task]
    if re.search(r"\b(crm|customers?|deals?|leads?|sales pipeline)\b", text):
        return [_ent("Customer", "customers", [("name", "Name", "string", True), ("email", "Email", "string", False), ("company", "Company", "string", False),
                                               ("status", "Status", "enum", True, ["lead", "active", "inactive"])]),
                _ent("Deal", "deals", [("title", "Title", "string", True), ("value", "Value", "float", True),
                                       ("stage", "Stage", "enum", True, ["new", "negotiation", "won", "lost"])])]
    if re.search(r"\b(booking|bookings|appointments?|reservations?|scheduler)\b", text):
        return [_ent("Booking", "bookings", [("title", "Title", "string", True), ("client", "Client", "string", True), ("starts_at", "Starts at", "datetime", True),
                                             ("status", "Status", "enum", True, ["pending", "confirmed", "cancelled"])])]
    if re.search(r"\b(inventory|stock|warehouse)\b", text):
        return [_ent("Item", "items", [("name", "Name", "string", True), ("sku", "SKU", "string", False), ("quantity", "Quantity", "int", True), ("price", "Price", "float", False)])]
    if re.search(r"\b(invoic(e|es|ing)|billing)\b", text):
        return [_ent("Invoice", "invoices", [("number", "Number", "string", True), ("client", "Client", "string", True), ("amount", "Amount", "float", True),
                                             ("status", "Status", "enum", True, ["draft", "sent", "paid"])])]
    return []


def _default_entities(kind: str, brief: str = "") -> list[dict]:
    text = brief.lower()
    if kind == "ecommerce":
        return [{"name": "Product", "path": "products", "label": "Products", "fields": [
            {"name": "name", "label": "Name", "type": "string", "required": True, "values": []},
            {"name": "description", "label": "Description", "type": "text", "required": False, "values": []},
            {"name": "price", "label": "Price", "type": "float", "required": True, "values": []},
            {"name": "status", "label": "Status", "type": "enum", "required": True, "values": ["draft", "active", "archived"]},
        ]}]
    domain = _domain_entities(text)
    if domain:
        return domain
    if re.search(r"\b(task|todo|to-do|kanban|planner|project management)\b", text):
        return [_ent("Task", "tasks", [
            ("title", "Title", "string", True),
            ("description", "Description", "text", False),
            ("status", "Status", "enum", True, ["todo", "in-progress", "blocked", "done"]),
            ("priority", "Priority", "enum", True, ["low", "medium", "high", "urgent"]),
            ("due_date", "Due date", "datetime", False),
            ("category", "Category", "string", False),
        ])]
    if re.search(r"\b(notes?|note[- ]taking|journal|memo|writing app)\b", text):
        return [{"name": "Note", "path": "notes", "label": "Notes", "fields": [
            {"name": "title", "label": "Title", "type": "string", "required": True, "values": []},
            {"name": "content", "label": "Content", "type": "text", "required": True, "values": []},
            {"name": "tags", "label": "Tags", "type": "string", "required": False, "values": []},
            {"name": "pinned", "label": "Pinned", "type": "bool", "required": False, "values": []},
        ]}]
    if re.search(r"\b(expense|budget|spending|finance tracker)\b", text):
        return [{"name": "Expense", "path": "expenses", "label": "Expenses", "fields": [
            {"name": "title", "label": "Title", "type": "string", "required": True, "values": []},
            {"name": "amount", "label": "Amount", "type": "float", "required": True, "values": []},
            {"name": "category", "label": "Category", "type": "string", "required": True, "values": []},
            {"name": "spent_on", "label": "Date", "type": "datetime", "required": False, "values": []},
        ]}]
    return [{"name": "Task", "path": "tasks", "label": "Tasks", "fields": [
        {"name": "title", "label": "Title", "type": "string", "required": True, "values": []},
        {"name": "description", "label": "Description", "type": "text", "required": False, "values": []},
        {"name": "status", "label": "Status", "type": "enum", "required": True, "values": ["todo", "in-progress", "done"]},
    ]}]


def generate(pf, state) -> dict:
    spec, _ = spec_engine.ensure(state)
    from backend.engines import tool_engine
    from backend.gen.env_contract import public_env_example
    tool = tool_engine.detect_tool(state.brief)
    if tool:
        title = str((state.plan or {}).get("brand") or "Calculator")[:70]
        return tool_engine.generate(pf, title, tool)
    entities = _entities(spec)
    if not entities:
        entities = _default_entities(spec.get("kind", "management"), state.brief)
    stack = (state.stack_config or {}).get("stack") or {}
    backend = str(stack.get("backend") or "none")
    database = str(stack.get("database") or "none")
    from backend.gen import stage as backend_generation
    stack_coverage = backend_generation.coverage(stack)
    api_enabled = backend != "none" and database != "none" and bool(stack_coverage.get("ready"))
    firebase_enabled = backend == "none" and database == "firestore"
    # An explicitly selected auth provider is authoritative even when the prompt forgot
    # to repeat "login/register"; the generated app must not silently fall back to local mode.
    firebase_auth_enabled = backend == "none" and stack.get("auth") == "firebase-auth"
    auth_enabled = api_enabled and stack.get("auth") in AUTH_METHODS and bool(spec.get("auth", {}).get("enabled"))
    unsupported_auth = api_enabled and stack.get("auth") not in (None, "", "none", *AUTH_METHODS) and bool(spec.get("auth", {}).get("enabled"))
    title = str((state.plan or {}).get("brand") or "Workspace")[:70]
    kind = str(spec.get("kind", "management"))
    payload = {
        "name": title,
        "kind": kind,
        "entities": entities,
        "apiEnabled": api_enabled,
        "authEnabled": auth_enabled,
        "firebaseEnabled": firebase_enabled,
        "firebaseAuthEnabled": firebase_auth_enabled,
        "dataMode": "Firebase Firestore" if firebase_enabled else ("API + database" if api_enabled else "localStorage (this browser)"),
    }
    firebase_imports = ""
    firebase_effect = ""
    firebase_load = ""
    firebase_save = ""
    firebase_delete = ""
    firebase_auth_branch = ""
    firebase_signout_branch = ""
    if firebase_enabled:
        firebase_imports += "import { createOwnedDocument, deleteOwnedDocument, listOwnedDocuments, updateOwnedDocument } from './lib/firebaseData'\n"
        firebase_load = """if (APP.firebaseEnabled) {\n        const pairs = await Promise.all(APP.entities.map(async (entity) => [entity.path, await listOwnedDocuments(entity.path)] as const))\n        setRows(Object.fromEntries(pairs))\n        return\n      }"""
        firebase_save = """if (APP.firebaseEnabled) {\n        if (editing) await updateOwnedDocument(active.path, recordId(editing, 0), payload)\n        else await createOwnedDocument(active.path, payload)\n        await loadAll()\n        closeForm(); setNotice(editing ? 'Changes saved.' : 'Item created.')\n        return\n      }"""
        firebase_delete = """if (APP.firebaseEnabled) { await deleteOwnedDocument(active.path, id); await loadAll(); setNotice('Item deleted.'); return }"""
    if firebase_auth_enabled:
        firebase_imports += "import { onAuthStateChanged, createUserWithEmailAndPassword, signInWithEmailAndPassword, signOut as firebaseSignOut, updateProfile } from 'firebase/auth'\nimport { auth } from './lib/firebase'\n"
        firebase_effect = """useEffect(() => onAuthStateChanged(auth, (user) => {\n    setFirebaseUid(user?.uid ?? '')\n    setUserName(user?.displayName || user?.email || '')\n  }), [])"""
        firebase_auth_branch = """if (APP.firebaseAuthEnabled) {\n        if (authMode === 'register') {\n          const credential = await createUserWithEmailAndPassword(auth, email.trim(), password)\n          if (fullName.trim()) await updateProfile(credential.user, { displayName: fullName.trim() })\n        } else {\n          await signInWithEmailAndPassword(auth, email.trim(), password)\n        }\n        setPassword('')\n        return\n      }"""
        firebase_signout_branch = """if (APP.firebaseAuthEnabled) {\n      try { await firebaseSignOut(auth) } finally { setFirebaseUid(''); setUserName(''); setRows({}) }\n      return\n    }"""
    else:
        # Use a harmless effect placeholder if the selected stack does not require Firebase.
        firebase_effect = ""
    generated_app = _APP_TEMPLATE.replace("__PAYLOAD__", _json(payload))
    for marker, value in {
        "__FIREBASE_IMPORTS__": firebase_imports,
        "__FIREBASE_AUTH_EFFECT__": firebase_effect,
        "__FIREBASE_LOAD_BRANCH__": firebase_load,
        "__FIREBASE_SAVE_BRANCH__": firebase_save,
        "__FIREBASE_DELETE_BRANCH__": firebase_delete,
        "__FIREBASE_AUTH_BRANCH__": firebase_auth_branch,
        "__FIREBASE_SIGNOUT_BRANCH__": firebase_signout_branch,
    }.items():
        generated_app = generated_app.replace(marker, value)
    pf.write("src/App.tsx", generated_app)
    pf.write("src/styles/app.css", _CSS)
    pf.write(".env.example", public_env_example(spec))
    # A generated frontend may contain only public config; never ignore the example file.
    try:
        ignore = pf.read(".gitignore")
    except (OSError, ValueError):
        ignore = ""
    ignore_rows = ignore.splitlines()
    for line in (".env", ".env.*"):
        if line not in ignore_rows:
            ignore_rows.append(line)
    ignore_rows = [line for line in ignore_rows if line != "!.env.example"] + ["!.env.example"]
    pf.write(".gitignore", "\n".join(ignore_rows).rstrip() + "\n")
    pf.write("README.md", _readme(payload, backend, database, unsupported_auth))
    return {"entities": len(entities), "api_enabled": api_enabled, "auth_enabled": auth_enabled,
            "unsupported_auth": unsupported_auth, "title": title}


def _readme(payload: dict, backend: str, database: str, unsupported_auth: bool) -> str:
    if payload["apiEnabled"]:
        api_steps = {
            "express": "cd backend\nnpm install\nCopy-Item .env.example .env  # PowerShell\nnpm run migrate\nnpm run dev",
            "nestjs": "cd backend\nnpm install\nCopy-Item .env.example .env  # PowerShell\nnpm run migrate\nnpm run start:dev",
            "fastapi": "cd backend\npython -m venv .venv\n.venv\\Scripts\\Activate.ps1\npip install -r requirements.txt\nCopy-Item .env.example .env\npython -m app",
            "flask": "cd backend\npython -m venv .venv\n.venv\\Scripts\\Activate.ps1\npip install -r requirements.txt\nCopy-Item .env.example .env\npython -m app",
            "django": "cd backend\npython -m venv .venv\n.venv\\Scripts\\Activate.ps1\npip install -r requirements.txt\nCopy-Item .env.example .env\npython manage.py migrate\npython manage.py runserver 8000",
        }.get(backend, "See backend/README.md for the selected backend's run commands.")
        backend_note = f"Backend: **{backend}** · database: **{database}**. Start it in one terminal:\n\n```powershell\n{api_steps}\n```\n\nThe frontend reads `VITE_API_URL` from a `.env` file in this project root. The backend must be running before API-backed data can load."
    elif payload.get("firebaseEnabled"):
        if payload.get("firebaseAuthEnabled"):
            firebase_auth_setup = "Enable Email/Password in Firebase Authentication."
        else:
            firebase_auth_setup = "Enable the Anonymous sign-in provider in Firebase Authentication; the generated data adapter uses anonymous accounts so Firestore owner rules remain enforced without showing a login screen."
        backend_note = f"Data is stored in Firebase Firestore using authenticated, owner-scoped records. Copy `.env.example` to `.env`, configure your Firebase Web app values, {firebase_auth_setup} Deploy `firestore.rules`. Firebase configuration values prefixed with `VITE_` are public browser settings, not private API secrets."
    else:
        backend_note = "This configuration has no generated server/database. Records are persisted in this browser using localStorage; this is suitable for local demos, not shared or multi-user production data."
    if payload.get("firebaseAuthEnabled"):
        backend_note += "\n\nFirebase Authentication is enabled in the generated UI; configure the Firebase project and authorized domains before use."
    auth_note = "\n\n**Authentication note:** the selected auth provider is not wired into this generic workspace UI. Review the stack/report before exposing this app." if unsupported_auth else ""
    return f"""# {payload['name']}

A responsive, schema-driven React + TypeScript application generated from one prompt.

## Run the frontend

```powershell
npm install
npm run dev
```

Open the Vite URL printed in the terminal. Configure `VITE_API_URL` in a frontend `.env` file if the API is not running at `http://localhost:8000`.

## Data and backend

{backend_note}

## Included behavior

- Searchable entity views and summaries.
- Create, edit and delete forms derived from the application data model.
- Required-field validation, loading/error/empty states and responsive navigation.
- Firebase Firestore persistence for the supported Firebase client stack, server API persistence when a supported backend is selected, or local browser storage for demo-only stacks. Connection/auth errors are shown rather than pretending operations succeeded.
- Keyboard-accessible controls and reduced-motion-friendly styling.

## Production readiness

Run `npm run build`, backend tests, and a browser test pass before deployment. Set real secrets only in ignored `.env` files, use HTTPS, and configure production CORS/database credentials. Automated checks reduce defects but cannot prove the absence of every bug.{auth_note}
"""


_APP_TEMPLATE = r'''import { FormEvent, useCallback, useEffect, useMemo, useState } from 'react'
import './styles/app.css'
__FIREBASE_IMPORTS__

type FieldDef = { name: string; label: string; type: string; required: boolean; values: string[] }
type EntityDef = { name: string; path: string; label: string; fields: FieldDef[] }
type Row = Record<string, unknown> & { id?: string | number; _id?: string | number }
type Payload = { name: string; kind: string; entities: EntityDef[]; apiEnabled: boolean; authEnabled: boolean; firebaseEnabled: boolean; firebaseAuthEnabled: boolean; dataMode: string }
const APP = __PAYLOAD__ as Payload
const API_BASE = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/+$/, '')
const TOKEN_KEY = 'agent-access-token'
const REFRESH_KEY = 'agent-refresh-token'
const LOCAL_PREFIX = 'agent-generated-app:'

function recordId(row: Row, index: number) { return String(row.id ?? row._id ?? row.key ?? index) }
function emptyDraft(entity: EntityDef): Record<string, string | boolean> {
  return Object.fromEntries(entity.fields.map((f) => [f.name, f.type === 'bool' ? false : f.type === 'enum' ? (f.values[0] ?? '') : '']))
}
function asInputType(f: FieldDef): string {
  if (f.type === 'email' || f.type === 'url' || f.type === 'datetime') return f.type === 'datetime' ? 'datetime-local' : f.type
  if (f.type === 'int' || f.type === 'float') return 'number'
  return 'text'
}

let refreshInFlight: Promise<boolean> | null = null
async function refreshToken(): Promise<boolean> {
  if (!APP.authEnabled) return false
  if (refreshInFlight) return refreshInFlight
  const refreshToken = sessionStorage.getItem(REFRESH_KEY)
  if (!refreshToken) return false
  refreshInFlight = (async () => {
    try {
      const response = await fetch(`${API_BASE}/api/auth/refresh`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ refreshToken }) })
      if (!response.ok) return false
      const data = await response.json() as { accessToken?: string; refreshToken?: string }
      if (!data.accessToken) return false
      sessionStorage.setItem(TOKEN_KEY, data.accessToken)
      if (data.refreshToken) sessionStorage.setItem(REFRESH_KEY, data.refreshToken)
      return true
    } catch { return false }
    finally { refreshInFlight = null }
  })()
  return refreshInFlight
}

async function apiRequest(path: string, init: RequestInit = {}, canRefresh = true): Promise<unknown> {
  const headers = new Headers(init.headers)
  if (init.body && !headers.has('Content-Type')) headers.set('Content-Type', 'application/json')
  const token = sessionStorage.getItem(TOKEN_KEY)
  if (token) headers.set('Authorization', `Bearer ${token}`)
  let response: Response
  try { response = await fetch(`${API_BASE}${path}`, { ...init, headers }) }
  catch { throw new Error(`Cannot reach the API at ${API_BASE}. Start the backend and check VITE_API_URL.`) }
  if (response.status === 401 && canRefresh && await refreshToken()) return apiRequest(path, init, false)
  if (!response.ok) {
    let detail = `Request failed (${response.status})`
    try {
      const body = await response.json() as { detail?: unknown; error?: { message?: string }; message?: string }
      detail = String(body.detail ?? body.error?.message ?? body.message ?? detail)
    } catch { /* retain safe status message */ }
    if (response.status === 404) detail = `${detail} - ${path} does not exist at ${API_BASE}. The generated backend is probably not running there (another server may be using that port). Start it and check VITE_API_URL.`
    throw new Error(detail.slice(0, 300))
  }
  if (response.status === 204) return null
  return response.json()
}

function localRead(entity: EntityDef): Row[] {
  try { const value = JSON.parse(localStorage.getItem(LOCAL_PREFIX + entity.path) || '[]'); return Array.isArray(value) ? value : [] }
  catch { return [] }
}
function localWrite(entity: EntityDef, rows: Row[]) {
  localStorage.setItem(LOCAL_PREFIX + entity.path, JSON.stringify(rows))
}

export default function App() {
  const [activePath, setActivePath] = useState(APP.entities[0]?.path ?? '')
  const [rows, setRows] = useState<Record<string, Row[]>>({})
  const [search, setSearch] = useState('')
  const [editing, setEditing] = useState<Row | null>(null)
  const [draft, setDraft] = useState<Record<string, string | boolean>>({})
  const [formOpen, setFormOpen] = useState(false)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [authMode, setAuthMode] = useState<'login' | 'register'>('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [fullName, setFullName] = useState('')
  const [token, setToken] = useState(() => sessionStorage.getItem(TOKEN_KEY) || '')
  const [userName, setUserName] = useState('')
  const [firebaseUid, setFirebaseUid] = useState('')
  __FIREBASE_AUTH_EFFECT__

  const active = APP.entities.find((e) => e.path === activePath) ?? APP.entities[0]
  const visibleRows = useMemo(() => {
    if (!active) return []
    const source = rows[active.path] ?? []
    const q = search.trim().toLowerCase()
    if (!q) return source
    return source.filter((row) => active.fields.some((field) => String(row[field.name] ?? '').toLowerCase().includes(q)))
  }, [active, rows, search])
  const totalRows = useMemo(() => Object.values(rows).reduce((n, list) => n + list.length, 0), [rows])
  const completedRows = useMemo(() => Object.values(rows).flat().filter((row) => String(row.status ?? '').toLowerCase() === 'done' || row.completed === true).length, [rows])

  const loadAll = useCallback(async () => {
    setLoading(true); setError('')
    try {
      __FIREBASE_LOAD_BRANCH__
      if (APP.apiEnabled) {
        const pairs = await Promise.all(APP.entities.map(async (entity) => {
          const result = await apiRequest(`/api/${entity.path}?page=1&limit=100`)
          const body = result as { data?: Row[] } | Row[]
          const list = Array.isArray(body) ? body : Array.isArray(body?.data) ? body.data : []
          return [entity.path, list] as const
        }))
        setRows(Object.fromEntries(pairs))
      } else {
        setRows(Object.fromEntries(APP.entities.map((entity) => [entity.path, localRead(entity)])))
      }
    } catch (e) { setError((e as Error).message || 'Could not load application data.') }
    finally { setLoading(false) }
  }, [])

  useEffect(() => {
    if ((APP.authEnabled && !token) || (APP.firebaseAuthEnabled && !firebaseUid)) { setLoading(false); return }
    void loadAll()
  }, [loadAll, token, firebaseUid])

  function startNew() {
    if (!active) return
    setEditing(null); setDraft(emptyDraft(active)); setFormOpen(true); setError(''); setNotice('')
  }
  function startEdit(row: Row) {
    if (!active) return
    setEditing(row)
    setDraft(Object.fromEntries(active.fields.map((f) => [f.name, f.type === 'bool' ? Boolean(row[f.name]) : String(row[f.name] ?? '')])))
    setFormOpen(true); setError(''); setNotice('')
  }
  function closeForm() { setFormOpen(false); setEditing(null); setDraft({}) }

  async function submitForm(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!active) return
    setSaving(true); setError(''); setNotice('')
    const payload: Record<string, unknown> = {}
    for (const field of active.fields) {
      const value = draft[field.name]
      if (field.type === 'bool') payload[field.name] = Boolean(value)
      else if (field.type === 'int' || field.type === 'float') payload[field.name] = value === '' ? null : Number(value)
      else payload[field.name] = String(value ?? '').trim()
    }
    try {
      __FIREBASE_SAVE_BRANCH__
      if (APP.apiEnabled) {
        if (editing) await apiRequest(`/api/${active.path}/${encodeURIComponent(recordId(editing, 0))}`, { method: 'PUT', body: JSON.stringify(payload) })
        else await apiRequest(`/api/${active.path}`, { method: 'POST', body: JSON.stringify(payload) })
        await loadAll()
      } else {
        const existing = rows[active.path] ?? []
        const id = editing ? recordId(editing, 0) : (globalThis.crypto?.randomUUID?.() ?? `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`)
        const nextRow = { ...(editing ?? {}), ...payload, id }
        const next = editing ? existing.map((row, i) => recordId(row, i) === id ? nextRow : row) : [nextRow, ...existing]
        localWrite(active, next); setRows((old) => ({ ...old, [active.path]: next }))
      }
      closeForm(); setNotice(editing ? 'Changes saved.' : 'Item created.')
    } catch (e) { setError((e as Error).message || 'Could not save the item.') }
    finally { setSaving(false) }
  }

  async function removeRow(row: Row, index: number) {
    if (!active || !window.confirm(`Delete this ${active.label.toLowerCase()} item? This cannot be undone.`)) return
    setError(''); setNotice('')
    const id = recordId(row, index)
    try {
      __FIREBASE_DELETE_BRANCH__
      if (APP.apiEnabled) { await apiRequest(`/api/${active.path}/${encodeURIComponent(id)}`, { method: 'DELETE' }); await loadAll() }
      else { const next = (rows[active.path] ?? []).filter((item, i) => recordId(item, i) !== id); localWrite(active, next); setRows((old) => ({ ...old, [active.path]: next })) }
      setNotice('Item deleted.')
    } catch (e) { setError((e as Error).message || 'Could not delete the item.') }
  }

  async function authenticate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setError(''); setSaving(true)
    try {
      __FIREBASE_AUTH_BRANCH__
      const endpoint = authMode === 'register' ? '/api/auth/register' : '/api/auth/login'
      const body = authMode === 'register' ? { name: fullName.trim(), email: email.trim(), password } : { email: email.trim(), password }
      const result = await apiRequest(endpoint, { method: 'POST', body: JSON.stringify(body) }) as { accessToken?: string; refreshToken?: string; user?: { name?: string; email?: string } }
      if (!result?.accessToken) throw new Error('The auth API did not return an access token.')
      sessionStorage.setItem(TOKEN_KEY, result.accessToken)
      if (result.refreshToken) sessionStorage.setItem(REFRESH_KEY, result.refreshToken)
      setToken(result.accessToken); setUserName(result.user?.name || result.user?.email || email.trim()); setPassword('')
    } catch (e) { setError((e as Error).message || 'Could not authenticate.') }
    finally { setSaving(false) }
  }

  async function signOut() {
    __FIREBASE_SIGNOUT_BRANCH__
    try { if (APP.apiEnabled) await apiRequest('/api/auth/logout', { method: 'POST', body: JSON.stringify({ refreshToken: sessionStorage.getItem(REFRESH_KEY) }) }) } catch { /* signing out locally remains possible */ }
    sessionStorage.removeItem(TOKEN_KEY); sessionStorage.removeItem(REFRESH_KEY); setToken(''); setUserName(''); setRows({})
  }

  if ((APP.authEnabled && !token) || (APP.firebaseAuthEnabled && !firebaseUid)) return <main className="auth-wrap"><section className="auth-card">
    <div className="brand-mark">{APP.name.slice(0, 1).toUpperCase()}</div><p className="eyebrow">SECURE WORKSPACE</p><h1>{APP.name}</h1><p className="muted">Sign in to access your workspace.</p>
    <form className="form-stack" onSubmit={authenticate}>
      {authMode === 'register' && <label>Full name<input autoComplete="name" required maxLength={255} value={fullName} onChange={(e) => setFullName(e.target.value)} /></label>}
      <label>Email<input type="email" autoComplete="email" required maxLength={255} value={email} onChange={(e) => setEmail(e.target.value)} /></label>
      <label>Password<input type="password" autoComplete={authMode === 'register' ? 'new-password' : 'current-password'} required minLength={authMode === 'register' ? 8 : 1} maxLength={200} value={password} onChange={(e) => setPassword(e.target.value)} /></label>
      {error && <p role="alert" className="alert alert-error">{error}</p>}
      <button className="primary-button full-button" disabled={saving}>{saving ? 'Please wait…' : authMode === 'register' ? 'Create account' : 'Sign in'}</button>
    </form>
    <button className="text-button" onClick={() => { setAuthMode(authMode === 'login' ? 'register' : 'login'); setError('') }}>{authMode === 'login' ? 'New here? Create an account' : 'Already have an account? Sign in'}</button>
  </section></main>

  return <div className="app-shell">
    <aside className="sidebar">
      <div className="sidebar-brand"><span className="brand-mark">{APP.name.slice(0, 1).toUpperCase()}</span><span><strong>{APP.name}</strong><small>WORKSPACE</small></span></div>
      <p className="nav-caption">YOUR WORKSPACE</p>
      <nav aria-label="Workspace sections" className="entity-nav">
        {APP.entities.map((entity) => <button key={entity.path} className={active?.path === entity.path ? 'nav-item active' : 'nav-item'} onClick={() => { setActivePath(entity.path); setSearch(''); setFormOpen(false); setError('') }}><span className="nav-dot" />{entity.label}<span className="nav-count">{(rows[entity.path] ?? []).length}</span></button>)}
      </nav>
      <div className="sidebar-bottom"><span className="status-dot" />{APP.apiEnabled || APP.firebaseEnabled ? 'Connected workspace' : 'Saved on this device'}<small>{APP.dataMode}</small></div>
    </aside>
    <main className="main-area">
      <header className="topbar"><div><p className="eyebrow">{APP.kind.replace(/-/g, ' ').toUpperCase()} / OVERVIEW</p><h1>{active?.label ?? 'Workspace'}</h1></div>
        <div className="topbar-actions">{(APP.authEnabled || APP.firebaseAuthEnabled) && <span className="user-chip">{userName || 'Signed in'}</span>}{(APP.authEnabled || APP.firebaseAuthEnabled) && <button className="secondary-button" onClick={() => void signOut()}>Sign out</button>}
          <button className="primary-button" onClick={startNew} disabled={!active}>＋ New {active?.label.replace(/s$/, '') ?? 'item'}</button></div>
      </header>
      <section className="summary-grid" aria-label="Workspace summary">
        <article className="summary-card"><span>Total records</span><strong>{totalRows}</strong><small>Across {APP.entities.length} {APP.entities.length === 1 ? 'collection' : 'collections'}</small></article>
        <article className="summary-card"><span>Completed</span><strong>{completedRows}</strong><small>Records marked done</small></article>
        <article className="summary-card"><span>Current view</span><strong>{rows[active?.path ?? '']?.length ?? 0}</strong><small>{active?.label ?? 'Items'} in this collection</small></article>
      </section>
      <section className="content-card">
        <div className="content-heading"><div><h2>{active?.label ?? 'Records'}</h2><p>Manage your records, keep details up to date, and search by any visible field.</p></div>
          <label className="search-box"><span aria-hidden="true">⌕</span><input aria-label={`Search ${active?.label ?? 'records'}`} placeholder="Search records…" value={search} onChange={(e) => setSearch(e.target.value)} /></label></div>
        {notice && <p role="status" className="alert alert-success">{notice}</p>}{error && <p role="alert" className="alert alert-error">{error}</p>}
        {formOpen && active && <form className="editor-form" onSubmit={(e) => void submitForm(e)}><div className="form-heading"><div><p className="eyebrow">{editing ? 'UPDATE RECORD' : 'NEW RECORD'}</p><h3>{editing ? 'Edit' : 'Create'} {active.label.replace(/s$/, '')}</h3></div><button type="button" className="icon-button" aria-label="Close form" onClick={closeForm}>×</button></div>
          <div className="field-grid">{active.fields.map((field) => <label key={field.name} className={field.type === 'text' ? 'field-wide' : ''}>{field.label}{field.type === 'bool' ? <span className="checkbox-line"><input type="checkbox" checked={Boolean(draft[field.name])} onChange={(e) => setDraft((old) => ({ ...old, [field.name]: e.target.checked }))} /> Enabled</span> : field.type === 'enum' ? <select required={field.required} value={String(draft[field.name] ?? '')} onChange={(e) => setDraft((old) => ({ ...old, [field.name]: e.target.value }))}>{!field.required && <option value="">Select…</option>}{field.values.map((value) => <option key={value} value={value}>{value.replace(/-/g, ' ')}</option>)}</select> : field.type === 'text' ? <textarea rows={3} required={field.required} maxLength={20000} value={String(draft[field.name] ?? '')} onChange={(e) => setDraft((old) => ({ ...old, [field.name]: e.target.value }))} /> : <input type={asInputType(field)} required={field.required} maxLength={field.type === 'string' || field.type === 'email' || field.type === 'url' ? 255 : undefined} step={field.type === 'float' ? 'any' : undefined} value={String(draft[field.name] ?? '')} onChange={(e) => setDraft((old) => ({ ...old, [field.name]: e.target.value }))} />}</label>)}</div>
          <div className="form-actions"><button type="button" className="secondary-button" onClick={closeForm} disabled={saving}>Cancel</button><button className="primary-button" disabled={saving}>{saving ? 'Saving…' : editing ? 'Save changes' : 'Create record'}</button></div></form>}
        {loading ? <div className="state-panel"><span className="spinner" /><p>Loading your workspace…</p></div> : visibleRows.length === 0 ? <div className="state-panel"><div className="empty-icon">＋</div><h3>{search ? 'No matching records' : `No ${active?.label.toLowerCase() ?? 'records'} yet`}</h3><p>{search ? 'Try another search term.' : 'Create your first record to get started.'}</p>{!search && <button className="secondary-button" onClick={startNew}>Create first record</button>}</div> : <div className="records-grid">{visibleRows.map((row, index) => <article className="record-card" key={`${recordId(row, index)}-${index}`}><div className="record-top"><span className="record-index">{String(index + 1).padStart(2, '0')}</span><span className="record-status">{String(row.status ?? (row.completed === true ? 'done' : 'active'))}</span></div><h3>{String(row.title ?? row.name ?? row.subject ?? row.email ?? `${active?.label ?? 'Record'} ${index + 1}`)}</h3><p className="record-description">{String(row.description ?? row.body ?? row.notes ?? '') || 'No description provided.'}</p><dl className="record-fields">{active?.fields.slice(0, 4).filter((f) => !['title', 'name', 'description', 'body'].includes(f.name)).map((field) => <div key={field.name}><dt>{field.label}</dt><dd>{String(row[field.name] ?? '—')}</dd></div>)}</dl><footer className="record-actions"><button className="secondary-button" onClick={() => startEdit(row)}>Edit</button><button className="danger-button" onClick={() => void removeRow(row, index)}>Delete</button></footer></article>)}</div>}
        <footer className="content-footer"><span>{visibleRows.length} shown · {rows[active?.path ?? '']?.length ?? 0} total</span><span>{APP.firebaseEnabled ? 'Synced through Firebase' : APP.apiEnabled ? 'Synced through API' : 'Stored in this browser'}</span></footer>
      </section>
      <footer className="app-footer">{APP.name} · Automatically generated workspace <span>{APP.firebaseEnabled ? 'Firebase-backed' : APP.apiEnabled ? 'API-backed' : 'Device-local mode'}</span></footer>
    </main>
  </div>
}
'''

_CSS = r'''@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
:root{--app-line:color-mix(in srgb,var(--muted) 19%,transparent);--app-card:color-mix(in srgb,var(--bg) 90%,var(--fg));--app-soft:color-mix(in srgb,var(--bg) 84%,var(--primary));--app-shadow:0 18px 48px rgba(0,0,0,.16)}
*{box-sizing:border-box}body{margin:0;font-family:var(--font-body,'DM Sans'),system-ui,sans-serif;background:radial-gradient(ellipse at 75% -10%,color-mix(in srgb,var(--primary) 17%,transparent),transparent 40%),var(--bg);color:var(--fg)}button,input,textarea,select{font:inherit}button{cursor:pointer}button:disabled{cursor:not-allowed;opacity:.58}button:focus-visible,input:focus-visible,textarea:focus-visible,select:focus-visible{outline:2px solid var(--accent);outline-offset:2px}.app-shell{min-height:100vh;display:grid;grid-template-columns:252px minmax(0,1fr)}.sidebar{position:sticky;top:0;height:100vh;padding:26px 15px 16px;border-right:1px solid var(--app-line);background:color-mix(in srgb,var(--bg) 92%,transparent);display:flex;flex-direction:column;gap:22px}.sidebar-brand{display:flex;align-items:center;gap:11px;padding:0 8px}.brand-mark{display:grid;place-items:center;width:40px;height:40px;border-radius:14px;background:linear-gradient(145deg,var(--primary),var(--accent));color:#fff;font:700 20px var(--font-head,'Space Grotesk');box-shadow:0 8px 25px color-mix(in srgb,var(--primary) 25%,transparent);flex-shrink:0}.sidebar-brand strong{display:block;font:600 14px var(--font-head,'Space Grotesk');max-width:150px;overflow-wrap:anywhere}.sidebar-brand small{display:block;font-size:9px;letter-spacing:.2em;color:var(--muted);margin-top:4px}.nav-caption,.eyebrow{font-size:10px;font-weight:700;letter-spacing:.17em;color:var(--muted);margin:0}.nav-caption{padding:0 10px;margin-bottom:-12px}.entity-nav{display:grid;gap:5px}.nav-item{display:flex;gap:10px;align-items:center;width:100%;border:1px solid transparent;background:transparent;color:var(--muted);padding:11px 10px;border-radius:12px;text-align:left;font-size:13px}.nav-item:hover{color:var(--fg);background:var(--app-soft)}.nav-item.active{color:var(--fg);background:color-mix(in srgb,var(--primary) 16%,var(--app-card));border-color:color-mix(in srgb,var(--primary) 35%,transparent)}.nav-dot{width:7px;height:7px;border-radius:50%;background:var(--muted);opacity:.7}.nav-item.active .nav-dot{background:var(--accent);opacity:1;box-shadow:0 0 12px var(--accent)}.nav-count{margin-left:auto;color:var(--muted);font-size:11px}.sidebar-bottom{margin-top:auto;padding:14px 10px;border:1px solid var(--app-line);border-radius:14px;font-size:11px;color:var(--fg)}.sidebar-bottom small{display:block;color:var(--muted);margin:7px 0 0 15px;overflow-wrap:anywhere}.status-dot{display:inline-block;width:7px;height:7px;background:#52d6a0;border-radius:50%;margin-right:8px}.main-area{min-width:0;padding:28px clamp(16px,3vw,42px) 20px}.topbar{display:flex;align-items:center;justify-content:space-between;gap:18px;margin-bottom:27px}.topbar h1{font:600 clamp(26px,3vw,36px) var(--font-head,'Space Grotesk');letter-spacing:-.045em;margin:8px 0 0}.topbar-actions{display:flex;align-items:center;gap:9px;flex-wrap:wrap}.user-chip{font-size:12px;color:var(--muted);padding:8px 12px;border:1px solid var(--app-line);border-radius:999px}.primary-button,.secondary-button,.danger-button,.text-button,.icon-button{border-radius:11px;padding:10px 14px;border:1px solid transparent;font-size:12px;font-weight:700;transition:transform .16s ease,border-color .16s ease,background .16s ease}.primary-button{background:linear-gradient(120deg,var(--primary),color-mix(in srgb,var(--primary) 65%,var(--accent)));color:#fff;box-shadow:0 8px 20px color-mix(in srgb,var(--primary) 20%,transparent)}.primary-button:hover:not(:disabled){transform:translateY(-1px);filter:brightness(1.08)}.secondary-button{background:var(--app-card);border-color:var(--app-line);color:var(--fg)}.secondary-button:hover:not(:disabled){border-color:color-mix(in srgb,var(--accent) 50%,var(--app-line));background:var(--app-soft)}.danger-button{background:color-mix(in srgb,#ff647c 9%,transparent);border-color:color-mix(in srgb,#ff647c 24%,transparent);color:#ff8798}.danger-button:hover{background:color-mix(in srgb,#ff647c 17%,transparent)}.text-button{background:transparent;color:var(--accent);width:100%;margin-top:10px}.summary-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:13px;margin-bottom:20px}.summary-card{padding:18px;border:1px solid var(--app-line);border-radius:17px;background:linear-gradient(140deg,var(--app-card),color-mix(in srgb,var(--bg) 85%,var(--primary)));box-shadow:var(--app-shadow);min-width:0}.summary-card span,.summary-card small{display:block;color:var(--muted);font-size:11px}.summary-card strong{display:block;font:600 clamp(24px,3vw,32px) var(--font-head,'Space Grotesk');letter-spacing:-.04em;margin:12px 0 4px}.content-card{border:1px solid var(--app-line);border-radius:20px;background:color-mix(in srgb,var(--bg) 92%,var(--fg));box-shadow:var(--app-shadow);padding:clamp(15px,2vw,24px);min-width:0}.content-heading{display:flex;align-items:center;justify-content:space-between;gap:14px;margin-bottom:20px}.content-heading h2{font:600 20px var(--font-head,'Space Grotesk');letter-spacing:-.025em;margin:0 0 7px}.content-heading p{font-size:12px;color:var(--muted);margin:0;line-height:1.6}.search-box{width:min(100%,280px);display:flex;align-items:center;gap:8px;border:1px solid var(--app-line);background:var(--app-card);border-radius:11px;padding:0 10px;color:var(--muted)}.search-box span{font-size:22px}.search-box input{min-width:0;width:100%;background:transparent;color:var(--fg);border:0;outline:0;padding:11px 0;font-size:12px}.search-box input:focus-visible{outline:0}.alert{border-radius:10px;padding:10px 12px;font-size:12px;margin:0 0 13px;overflow-wrap:anywhere}.alert-error{color:#ff9aaa;border:1px solid color-mix(in srgb,#ff647c 30%,transparent);background:color-mix(in srgb,#ff647c 9%,transparent)}.alert-success{color:#65e1b6;border:1px solid color-mix(in srgb,#52d6a0 30%,transparent);background:color-mix(in srgb,#52d6a0 8%,transparent)}.editor-form{border:1px solid color-mix(in srgb,var(--primary) 38%,var(--app-line));background:var(--app-soft);border-radius:16px;padding:17px;margin-bottom:20px}.form-heading{display:flex;align-items:start;justify-content:space-between;margin-bottom:16px}.form-heading h3{margin:6px 0 0;font:600 18px var(--font-head,'Space Grotesk')}.icon-button{font-size:23px;line-height:1;padding:4px 9px;background:transparent;color:var(--muted)}.field-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:13px}.field-grid label,.form-stack label{display:grid;gap:7px;font-size:11px;font-weight:600;color:var(--muted);min-width:0}.field-grid input,.field-grid select,.field-grid textarea,.form-stack input{width:100%;min-width:0;border:1px solid var(--app-line);background:var(--bg);border-radius:9px;padding:10px 11px;color:var(--fg);font-size:12px}.field-grid textarea{resize:vertical}.field-wide{grid-column:1/-1}.checkbox-line{display:flex;align-items:center;gap:9px;color:var(--fg)}.checkbox-line input{width:16px;height:16px;accent-color:var(--primary)}.form-actions{display:flex;justify-content:flex-end;gap:8px;margin-top:16px}.records-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:13px}.record-card{border:1px solid var(--app-line);background:var(--app-card);border-radius:15px;padding:16px;min-width:0;display:flex;flex-direction:column}.record-top{display:flex;align-items:center;justify-content:space-between}.record-index{color:var(--muted);font:600 11px var(--font-head,'Space Grotesk')}.record-status{font-size:9px;letter-spacing:.08em;text-transform:uppercase;color:var(--accent);border:1px solid color-mix(in srgb,var(--accent) 25%,transparent);background:color-mix(in srgb,var(--accent) 7%,transparent);border-radius:999px;padding:5px 8px;max-width:60%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.record-card h3{font:600 17px var(--font-head,'Space Grotesk');overflow-wrap:anywhere;margin:16px 0 7px}.record-description{font-size:12px;line-height:1.65;color:var(--muted);overflow-wrap:anywhere;white-space:pre-wrap;flex:1;margin:0 0 10px}.record-fields{display:grid;gap:5px;margin:6px 0 14px}.record-fields div{display:flex;justify-content:space-between;gap:10px;border-top:1px solid var(--app-line);padding-top:7px;font-size:10px}.record-fields dt{color:var(--muted)}.record-fields dd{margin:0;text-align:right;overflow-wrap:anywhere}.record-actions{display:flex;justify-content:flex-end;gap:7px;border-top:1px solid var(--app-line);padding-top:12px;margin-top:4px}.record-actions button{padding:7px 10px;font-size:10px}.state-panel{min-height:230px;display:flex;align-items:center;justify-content:center;flex-direction:column;text-align:center;color:var(--muted);gap:8px}.state-panel h3{color:var(--fg);font:600 18px var(--font-head,'Space Grotesk');margin:5px 0 0}.state-panel p{font-size:12px;margin:0 0 7px}.empty-icon{display:grid;place-items:center;width:50px;height:50px;border-radius:15px;background:var(--app-soft);color:var(--accent);font-size:26px}.spinner{width:22px;height:22px;border:2px solid var(--app-line);border-top-color:var(--accent);border-radius:50%;animation:app-spin .8s linear infinite}@keyframes app-spin{to{transform:rotate(360deg)}}.content-footer{border-top:1px solid var(--app-line);padding-top:13px;margin-top:18px;display:flex;justify-content:space-between;gap:10px;color:var(--muted);font-size:10px}.app-footer{display:flex;justify-content:space-between;gap:10px;color:var(--muted);font-size:10px;margin:16px 3px 0}.auth-wrap{min-height:100vh;display:grid;place-items:center;padding:22px}.auth-card{width:min(100%,400px);padding:30px;border:1px solid var(--app-line);border-radius:22px;background:var(--app-card);box-shadow:var(--app-shadow)}.auth-card .brand-mark{margin-bottom:22px}.auth-card h1{font:600 30px var(--font-head,'Space Grotesk');letter-spacing:-.04em;margin:8px 0}.muted{font-size:12px;line-height:1.6;color:var(--muted)}.form-stack{display:grid;gap:14px;margin-top:23px}.full-button{width:100%;margin-top:2px}.app-root .muted{color:var(--muted)}
@media(max-width:900px){.app-shell{grid-template-columns:205px minmax(0,1fr)}.sidebar{padding-inline:10px}.main-area{padding:22px 16px}.summary-grid{gap:8px}.summary-card{padding:13px}.records-grid{grid-template-columns:minmax(0,1fr)}}
@media(max-width:640px){.app-shell{display:block}.sidebar{position:static;height:auto;padding:14px;border-right:0;border-bottom:1px solid var(--app-line);gap:13px}.sidebar-brand{padding:0 3px}.sidebar-bottom{display:none}.nav-caption{margin:2px 0 -6px;padding:0 3px}.entity-nav{display:flex;overflow:auto;padding-bottom:2px}.nav-item{white-space:nowrap;width:auto;flex:0 0 auto;padding:9px 11px}.nav-count{margin-left:2px}.main-area{padding:18px 12px}.topbar{align-items:flex-start;flex-direction:column;margin-bottom:18px}.topbar-actions{width:100%}.topbar-actions .primary-button{margin-left:auto}.summary-grid{grid-template-columns:repeat(3,minmax(0,1fr));gap:7px}.summary-card{padding:10px;border-radius:12px}.summary-card span,.summary-card small{font-size:9px}.summary-card strong{font-size:22px;margin:9px 0 3px}.content-heading{align-items:stretch;flex-direction:column}.search-box{width:100%}.field-grid{grid-template-columns:minmax(0,1fr)}.field-wide{grid-column:auto}.content-footer,.app-footer{align-items:flex-start;flex-direction:column}.auth-card{padding:23px}}
@media(prefers-reduced-motion:reduce){*,*::before,*::after{animation-duration:.01ms!important;animation-iteration-count:1!important;scroll-behavior:auto!important;transition-duration:.01ms!important}}
'''

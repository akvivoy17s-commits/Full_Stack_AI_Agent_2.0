"""Schema-driven interactive React application generator.

This is intentionally deterministic: app-style briefs produce a real CRUD workspace
that uses the generated API when one exists, and localStorage when the selected stack
has no server/database. The generated UI contains real forms, search, filter, sort,
card/table views, create, edit, delete (with an accessible confirm dialog),
loading/error/empty states, and optional JWT/session sign-in. It never pretends
that an unavailable remote integration succeeded.

UI quality bar (what the generated shell guarantees):
- Semantic landmarks, skip link, aria-current navigation, focus management, live regions.
- Responsive layout with an off-canvas mobile drawer and 44px touch targets on touch devices.
- Inline per-field validation, formatted values, status badges, skeleton loading, toasts.
- Light/dark safe colors derived from the design tokens, reduced-motion and forced-colors support.
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


def _decorate(entities: list[dict]) -> list[dict]:
    """Add UI-friendly singular/plural labels (e.g. "Customer" / "Customers", "Line Item" / "Line Items")."""
    for e in entities:
        name = str(e.get("name", "Item"))
        e["singular"] = re.sub(r"([a-z])([A-Z])", r"\1 \2", name)
        e["plural"] = str(e.get("path") or name.lower() + "s").replace("-", " ").title()
    return entities


def _domain_entities(text: str) -> list[dict]:
    if re.search(r"\b(crm|customers?|deals?|leads?|sales pipeline)\b", text):
        return [_ent("Customer", "customers", [("name", "Name", "string", True), ("email", "Email", "email", False), ("company", "Company", "string", False),
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
    tool = tool_engine.detect_tool(state.brief)
    if tool:
        title = str((state.plan or {}).get("brand") or "Calculator")[:70]
        return tool_engine.generate(pf, title, tool)
    entities = _entities(spec)
    if not entities:
        entities = _default_entities(spec.get("kind", "management"), state.brief)
    entities = _decorate(entities)
    stack = (state.stack_config or {}).get("stack") or {}
    backend = str(stack.get("backend") or "none")
    database = str(stack.get("database") or "none")
    from backend.gen import stage as backend_generation
    stack_coverage = backend_generation.coverage(stack)
    api_enabled = backend != "none" and database != "none" and bool(stack_coverage.get("ready"))
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
        "dataMode": "API + database" if api_enabled else "localStorage (this browser)",
    }
    pf.write("src/App.tsx", _APP_TEMPLATE.replace("__PAYLOAD__", _json(payload)))
    pf.write("src/styles/app.css", _CSS)
    pf.write(".env.example", "# Optional URL of the generated backend API\nVITE_API_URL=http://localhost:8000\n")
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
    else:
        backend_note = "This configuration has no generated server/database. Records are persisted in this browser using localStorage; this is suitable for local demos, not shared or multi-user production data."
    auth_note = "\n\n**Authentication note:** the selected auth provider is not wired into this generic workspace UI. Review the stack/report before exposing this app." if unsupported_auth else ""
    return f"""# {payload['name']}

A responsive, accessible, schema-driven React + TypeScript application generated from one prompt.

## Run the frontend

```powershell
npm install
npm run dev
```

Open the Vite URL printed in the terminal. Configure `VITE_API_URL` in a frontend `.env` file if the API is not running at `http://localhost:8000`.

## Data and backend

{backend_note}

## Included behavior

- Searchable, filterable and sortable collections with card and table views, plus summary tiles.
- Create, edit and delete forms derived from the application data model, with inline per-field validation and an accessible delete confirmation dialog.
- Loading skeletons, error banners with retry, empty states, toast notifications and session-expiry handling.
- Responsive layout with an off-canvas navigation drawer on small screens, skip link, landmarks and keyboard shortcuts (`/` focuses search, `Esc` closes the drawer).
- Local browser persistence when no database-backed API is selected; otherwise requests use the generated API and show connection/authorization errors rather than pretending they succeeded.
- Light/dark-safe colors, visible focus rings, 44px touch targets, reduced-motion and forced-colors support.

## Production readiness

Run `npm run build`, backend tests, and a browser test pass before deployment. Set real secrets only in ignored `.env` files, use HTTPS, and configure production CORS/database credentials. Automated checks reduce defects but cannot prove the absence of every bug.{auth_note}
"""


_APP_TEMPLATE = r'''import { CSSProperties, FormEvent, ReactNode, useCallback, useEffect, useMemo, useRef, useState } from 'react'
import './styles/app.css'

type FieldDef = { name: string; label: string; type: string; required: boolean; values: string[] }
type EntityDef = { name: string; path: string; label: string; singular: string; plural: string; fields: FieldDef[] }
type Row = Record<string, unknown> & { id?: string | number; _id?: string | number }
type Payload = { name: string; kind: string; entities: EntityDef[]; apiEnabled: boolean; authEnabled: boolean; dataMode: string }
type Draft = Record<string, string | boolean>
type Sort = { field: string; dir: 'asc' | 'desc' } | null

const APP = __PAYLOAD__ as Payload
const API_BASE = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/+$/, '')
const TOKEN_KEY = 'agent-access-token'
const REFRESH_KEY = 'agent-refresh-token'
const LOCAL_PREFIX = 'agent-generated-app:'
const PAGE_SIZE = 12
const TITLE_KEYS = ['title', 'name', 'subject', 'number', 'email']
const BODY_KEYS = ['description', 'body', 'notes', 'content']
const TONE_GOOD = /^(done|completed|complete|active|paid|won|confirmed|published|resolved|approved|in[- ]stock)$/i
const TONE_WARN = /^(pending|in[- ]progress|negotiation|draft|lead|sent|new|review|open|todo)$/i
const TONE_BAD = /^(cancelled|canceled|lost|failed|rejected|overdue|inactive|archived|blocked)$/i

const ICONS: Record<string, string> = {
  plus: 'M12 5v14M5 12h14',
  search: 'M11 19a8 8 0 1 0 0-16 8 8 0 0 0 0 16zM21 21l-4.3-4.3',
  menu: 'M4 6h16M4 12h16M4 18h16',
  x: 'M18 6 6 18M6 6l12 12',
  edit: 'M12 20h9M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z',
  trash: 'M3 6h18M8 6V4h8v2M19 6l-1 14H6L5 6M10 11v6M14 11v6',
  grid: 'M3 3h7v7H3zM14 3h7v7h-7zM14 14h7v7h-7zM3 14h7v7H3z',
  list: 'M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01',
  check: 'M20 6 9 17l-5-5',
  up: 'M12 19V5M5 12l7-7 7 7',
  down: 'M12 5v14M19 12l-7 7-7-7',
  inbox: 'M22 12h-6l-2 3h-4l-2-3H2M5.5 5h13L22 12v6a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2v-6z',
}

function Icon({ name }: { name: string }) {
  return <svg className="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" focusable="false"><path d={ICONS[name]} /></svg>
}

function recordId(row: Row, index: number) { return String(row.id ?? row._id ?? row.key ?? index) }
function emptyDraft(entity: EntityDef): Draft {
  return Object.fromEntries(entity.fields.map((f) => [f.name, f.type === 'bool' ? false : f.type === 'enum' && f.required ? (f.values[0] ?? '') : '']))
}
function inputType(f: FieldDef): string {
  if (f.type === 'datetime') return 'datetime-local'
  if (f.type === 'email' || f.type === 'url') return f.type
  if (f.type === 'int' || f.type === 'float') return 'number'
  return 'text'
}
function toLocalInput(value: unknown): string {
  if (!value) return ''
  const d = new Date(String(value))
  if (Number.isNaN(d.getTime())) return String(value)
  const p = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}T${p(d.getHours())}:${p(d.getMinutes())}`
}
function toDraftValue(f: FieldDef, value: unknown): string | boolean {
  if (f.type === 'bool') return value === true || value === 'true'
  if (f.type === 'datetime') return toLocalInput(value)
  return String(value ?? '')
}
function tone(value: string): 'good' | 'warn' | 'bad' | 'neutral' {
  const v = value.trim()
  return TONE_GOOD.test(v) ? 'good' : TONE_WARN.test(v) ? 'warn' : TONE_BAD.test(v) ? 'bad' : 'neutral'
}
function formatValue(f: FieldDef, value: unknown): string {
  if (f.type === 'int' || f.type === 'float') {
    const n = Number(value)
    return Number.isFinite(n) ? n.toLocaleString(undefined, { maximumFractionDigits: 2 }) : String(value)
  }
  if (f.type === 'datetime') {
    const d = new Date(String(value))
    return Number.isNaN(d.getTime()) ? String(value) : d.toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' })
  }
  return String(value)
}
function compareValues(a: unknown, b: unknown): number {
  const x = a ?? ''
  const y = b ?? ''
  const nx = Number(x)
  const ny = Number(y)
  if (x !== '' && y !== '' && Number.isFinite(nx) && Number.isFinite(ny)) return nx - ny
  return String(x).localeCompare(String(y), undefined, { numeric: true, sensitivity: 'base' })
}
function pickKey(row: Row, keys: string[]): string | undefined {
  return keys.find((k) => String(row[k] ?? '').trim() !== '')
}
function describe(row: Row, entity: EntityDef, index: number) {
  const titleKey = pickKey(row, TITLE_KEYS) ?? entity.fields.find((f) => ['string', 'text', 'email'].includes(f.type) && String(row[f.name] ?? '').trim() !== '')?.name
  const bodyKey = pickKey(row, BODY_KEYS)
  return {
    title: titleKey ? String(row[titleKey]) : `${entity.singular} ${index + 1}`,
    body: bodyKey ? String(row[bodyKey]) : '',
    titleKey,
    bodyKey,
  }
}

function validateDraft(entity: EntityDef, draft: Draft): Record<string, string> {
  const errors: Record<string, string> = {}
  for (const f of entity.fields) {
    if (f.type === 'bool') continue
    const s = String(draft[f.name] ?? '').trim()
    if (!s) { if (f.required) errors[f.name] = `${f.label} is required.`; continue }
    if (f.type === 'email' && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(s)) errors[f.name] = 'Enter a valid email address.'
    else if (f.type === 'url') {
      try { if (!/^https?:$/.test(new URL(s).protocol)) throw new Error('protocol') }
      catch { errors[f.name] = 'Enter a full URL starting with http:// or https://.' }
    } else if (f.type === 'int' && !Number.isInteger(Number(s))) errors[f.name] = 'Enter a whole number.'
    else if ((f.type === 'int' || f.type === 'float') && !Number.isFinite(Number(s))) errors[f.name] = 'Enter a valid number.'
  }
  return errors
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
  if (response.status === 401 && APP.authEnabled && token && !path.startsWith('/api/auth/')) {
    sessionStorage.removeItem(TOKEN_KEY); sessionStorage.removeItem(REFRESH_KEY)
    window.dispatchEvent(new Event('app:auth-expired'))
    throw new Error('Your session expired. Please sign in again.')
  }
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
  try { localStorage.setItem(LOCAL_PREFIX + entity.path, JSON.stringify(rows)) }
  catch { throw new Error('Could not save to this browser. Storage may be full or disabled.') }
}

function Value({ field, value }: { field: FieldDef; value: unknown }) {
  if (value === null || value === undefined || value === '') return <span className="dim" aria-label="No value">—</span>
  const text = String(value)
  if (field.type === 'bool') return <span>{value === true || value === 'true' ? 'Yes' : 'No'}</span>
  if (field.type === 'enum') return <span className={`badge badge-${tone(text)}`}>{text.replace(/-/g, ' ')}</span>
  if (field.type === 'url' && /^https?:\/\//i.test(text)) return <a href={text} target="_blank" rel="noopener noreferrer">{text.replace(/^https?:\/\//i, '')}</a>
  if (field.type === 'email') return <a href={`mailto:${text}`}>{text}</a>
  return <span>{formatValue(field, value)}</span>
}

function FieldControl({ field, value, error, onChange }: { field: FieldDef; value: string | boolean | undefined; error?: string; onChange: (v: string | boolean) => void }) {
  const id = `field-${field.name}`
  const errId = `${id}-error`
  const common = { id, 'aria-invalid': error ? true : undefined, 'aria-required': field.required || undefined, 'aria-describedby': error ? errId : undefined }
  if (field.type === 'bool') {
    return <div className="field"><label className="check" htmlFor={id}><input id={id} type="checkbox" checked={Boolean(value)} onChange={(e) => onChange(e.target.checked)} /><span>{field.label}</span></label></div>
  }
  const text = String(value ?? '')
  const wide = field.type === 'text'
  let control: ReactNode
  if (field.type === 'enum') {
    control = <select {...common} value={text} onChange={(e) => onChange(e.target.value)}>{!field.required && <option value="">Select…</option>}{field.values.map((v) => <option key={v} value={v}>{v.replace(/-/g, ' ')}</option>)}</select>
  } else if (wide) {
    control = <textarea {...common} rows={4} maxLength={20000} value={text} onChange={(e) => onChange(e.target.value)} />
  } else {
    control = <input {...common} type={inputType(field)} inputMode={field.type === 'int' ? 'numeric' : undefined} step={field.type === 'float' ? 'any' : undefined}
      maxLength={field.type === 'string' || field.type === 'email' || field.type === 'url' ? 255 : undefined}
      placeholder={field.type === 'email' ? 'name@example.com' : field.type === 'url' ? 'https://' : undefined}
      value={text} onChange={(e) => onChange(e.target.value)} />
  }
  return <div className={wide ? 'field field-wide' : 'field'}>
    <label htmlFor={id}>{field.label}{field.required && <span className="req" aria-hidden="true"> *</span>}</label>
    {control}
    {error && <p id={errId} className="field-error" role="alert">{error}</p>}
  </div>
}

export default function App() {
  const [activePath, setActivePath] = useState(APP.entities[0]?.path ?? '')
  const [rows, setRows] = useState<Record<string, Row[]>>({})
  const [search, setSearch] = useState('')
  const [filter, setFilter] = useState('')
  const [sort, setSort] = useState<Sort>(null)
  const [view, setView] = useState<'cards' | 'table'>('cards')
  const [limit, setLimit] = useState(PAGE_SIZE)
  const [editing, setEditing] = useState<Row | null>(null)
  const [draft, setDraft] = useState<Draft>({})
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({})
  const [formOpen, setFormOpen] = useState(false)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [loadFailed, setLoadFailed] = useState(false)
  const [notice, setNotice] = useState('')
  const [navOpen, setNavOpen] = useState(false)
  const [pendingDelete, setPendingDelete] = useState<{ row: Row; index: number; title: string } | null>(null)
  const [authMode, setAuthMode] = useState<'login' | 'register'>('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [fullName, setFullName] = useState('')
  const [token, setToken] = useState(() => sessionStorage.getItem(TOKEN_KEY) || '')
  const [userName, setUserName] = useState('')

  const searchRef = useRef<HTMLInputElement>(null)
  const formRef = useRef<HTMLFormElement>(null)
  const dialogRef = useRef<HTMLDialogElement>(null)
  const triggerRef = useRef<HTMLElement | null>(null)

  const active = APP.entities.find((e) => e.path === activePath) ?? APP.entities[0]
  const statusField = active?.fields.find((f) => f.type === 'enum')
  const sumField = active?.fields.find((f) => f.type === 'float' || f.type === 'int')
  const source = useMemo(() => (active ? rows[active.path] ?? [] : []), [active, rows])

  const processed = useMemo(() => {
    if (!active) return []
    let list = source
    if (statusField && filter) list = list.filter((row) => String(row[statusField.name] ?? '') === filter)
    const q = search.trim().toLowerCase()
    if (q) list = list.filter((row) => active.fields.some((field) => String(row[field.name] ?? '').toLowerCase().includes(q)))
    if (sort) {
      const dir = sort.dir === 'asc' ? 1 : -1
      list = [...list].sort((a, b) => compareValues(a[sort.field], b[sort.field]) * dir)
    }
    return list
  }, [active, source, statusField, filter, search, sort])
  const shown = processed.slice(0, limit)

  const stats = useMemo(() => {
    const total = Object.values(rows).reduce((n, list) => n + list.length, 0)
    const counts: Record<string, number> = {}
    if (statusField) for (const r of source) { const k = String(r[statusField.name] ?? ''); if (k) counts[k] = (counts[k] ?? 0) + 1 }
    const sum = sumField ? source.reduce((n, r) => n + (Number(r[sumField.name]) || 0), 0) : 0
    return { total, counts, sum }
  }, [rows, source, statusField, sumField])
  const topStatus = Object.entries(stats.counts).sort((a, b) => b[1] - a[1])[0]
  const thirdCard = sumField
    ? { label: `Total ${sumField.label.toLowerCase()}`, value: stats.sum.toLocaleString(undefined, { maximumFractionDigits: 2 }), hint: `Sum across ${source.length} ${source.length === 1 ? 'record' : 'records'}` }
    : topStatus
      ? { label: 'Most common status', value: String(topStatus[1]), hint: topStatus[0].replace(/-/g, ' ') }
      : { label: 'Collections', value: String(APP.entities.length), hint: 'Available in this workspace' }
  const filtering = Boolean(search.trim() || filter)

  const loadAll = useCallback(async () => {
    setLoading(true); setError(''); setLoadFailed(false)
    try {
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
    } catch (e) { setError((e as Error).message || 'Could not load application data.'); setLoadFailed(true) }
    finally { setLoading(false) }
  }, [])

  const closeForm = useCallback(() => {
    setFormOpen(false); setEditing(null); setDraft({}); setFieldErrors({})
    requestAnimationFrame(() => { if (triggerRef.current?.isConnected) triggerRef.current.focus() })
  }, [])

  useEffect(() => {
    if (APP.authEnabled && !token) { setLoading(false); return }
    void loadAll()
  }, [loadAll, token])

  useEffect(() => {
    const onExpired = () => { setToken(''); setUserName(''); setRows({}); setError('Your session expired. Please sign in again.') }
    window.addEventListener('app:auth-expired', onExpired)
    return () => window.removeEventListener('app:auth-expired', onExpired)
  }, [])

  useEffect(() => { document.title = `${active?.plural ?? 'Workspace'} · ${APP.name}` }, [active])

  useEffect(() => {
    if (!notice) return
    const t = window.setTimeout(() => setNotice(''), 4500)
    return () => window.clearTimeout(t)
  }, [notice])

  useEffect(() => {
    if (!formOpen) return
    formRef.current?.scrollIntoView({ block: 'nearest' })
    formRef.current?.querySelector<HTMLElement>('input:not([type=checkbox]),select,textarea')?.focus()
  }, [formOpen, editing])

  useEffect(() => {
    const d = dialogRef.current
    if (pendingDelete && d && !d.open) d.showModal()
  }, [pendingDelete])

  useEffect(() => {
    document.body.classList.toggle('nav-locked', navOpen)
    return () => document.body.classList.remove('nav-locked')
  }, [navOpen])

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      const t = e.target as HTMLElement | null
      const typing = !!t && (t.tagName === 'INPUT' || t.tagName === 'TEXTAREA' || t.tagName === 'SELECT' || t.isContentEditable)
      if (e.key === '/' && !typing && !e.metaKey && !e.ctrlKey && !e.altKey) { e.preventDefault(); searchRef.current?.focus() }
      if (e.key === 'Escape') setNavOpen(false)
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [])

  function selectEntity(path: string) {
    setActivePath(path); setSearch(''); setFilter(''); setSort(null); setLimit(PAGE_SIZE)
    setFormOpen(false); setEditing(null); setFieldErrors({}); setError(''); setNavOpen(false)
  }
  function clearFilters() { setSearch(''); setFilter(''); setLimit(PAGE_SIZE) }
  function toggleSort(field: string) {
    setSort((s) => (s?.field === field ? { field, dir: s.dir === 'asc' ? 'desc' : 'asc' } : { field, dir: 'asc' }))
  }
  function setField(name: string, value: string | boolean) {
    setDraft((old) => ({ ...old, [name]: value }))
    setFieldErrors((old) => { if (!old[name]) return old; const next = { ...old }; delete next[name]; return next })
  }

  function startNew() {
    if (!active) return
    triggerRef.current = document.activeElement as HTMLElement | null
    setEditing(null); setDraft(emptyDraft(active)); setFieldErrors({}); setFormOpen(true); setError(''); setNotice('')
  }
  function startEdit(row: Row) {
    if (!active) return
    triggerRef.current = document.activeElement as HTMLElement | null
    setEditing(row)
    setDraft(Object.fromEntries(active.fields.map((f) => [f.name, toDraftValue(f, row[f.name])])))
    setFieldErrors({}); setFormOpen(true); setError(''); setNotice('')
  }

  async function submitForm(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!active) return
    const errors = validateDraft(active, draft)
    setFieldErrors(errors)
    if (Object.keys(errors).length) {
      setError('')
      requestAnimationFrame(() => formRef.current?.querySelector<HTMLElement>('[aria-invalid="true"]')?.focus())
      return
    }
    setSaving(true); setError(''); setNotice('')
    const isEdit = Boolean(editing)
    const payload: Record<string, unknown> = {}
    for (const field of active.fields) {
      const value = draft[field.name]
      const s = String(value ?? '').trim()
      if (field.type === 'bool') payload[field.name] = Boolean(value)
      else if (field.type === 'int' || field.type === 'float') payload[field.name] = s === '' ? null : Number(s)
      else if (field.type === 'datetime') payload[field.name] = s && !Number.isNaN(new Date(s).getTime()) ? new Date(s).toISOString() : null
      else payload[field.name] = s
    }
    try {
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
      closeForm(); setNotice(isEdit ? 'Changes saved.' : `${active.singular} created.`)
    } catch (e) { setError((e as Error).message || 'Could not save the item.') }
    finally { setSaving(false) }
  }

  async function removeRow(row: Row, index: number) {
    if (!active) return
    setError(''); setNotice('')
    const id = recordId(row, index)
    try {
      if (APP.apiEnabled) { await apiRequest(`/api/${active.path}/${encodeURIComponent(id)}`, { method: 'DELETE' }); await loadAll() }
      else { const next = (rows[active.path] ?? []).filter((item, i) => recordId(item, i) !== id); localWrite(active, next); setRows((old) => ({ ...old, [active.path]: next })) }
      setNotice(`${active.singular} deleted.`)
    } catch (e) { setError((e as Error).message || 'Could not delete the item.') }
  }
  function askDelete(row: Row, index: number, title: string) {
    setPendingDelete({ row, index, title })
  }
  async function confirmDelete() {
    const target = pendingDelete
    dialogRef.current?.close()
    if (target) await removeRow(target.row, target.index)
  }

  async function authenticate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setError(''); setSaving(true)
    try {
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
    try { if (APP.apiEnabled) await apiRequest('/api/auth/logout', { method: 'POST', body: JSON.stringify({ refreshToken: sessionStorage.getItem(REFRESH_KEY) }) }) } catch { /* signing out locally remains possible */ }
    sessionStorage.removeItem(TOKEN_KEY); sessionStorage.removeItem(REFRESH_KEY); setToken(''); setUserName(''); setRows({})
  }

  if (APP.authEnabled && !token) return <main className="auth-wrap">
    <section className="auth-card" aria-labelledby="auth-title">
      <div className="brand-mark" aria-hidden="true">{APP.name.slice(0, 1).toUpperCase()}</div>
      <p className="eyebrow">Secure workspace</p>
      <h1 id="auth-title">{APP.name}</h1>
      <p className="muted">{authMode === 'login' ? 'Sign in to access your workspace.' : 'Create an account to get started.'}</p>
      <form className="form-stack" onSubmit={authenticate}>
        {authMode === 'register' && <div className="field"><label htmlFor="auth-name">Full name</label><input id="auth-name" autoComplete="name" required maxLength={255} value={fullName} onChange={(e) => setFullName(e.target.value)} /></div>}
        <div className="field"><label htmlFor="auth-email">Email</label><input id="auth-email" type="email" autoComplete="email" required maxLength={255} value={email} onChange={(e) => setEmail(e.target.value)} /></div>
        <div className="field"><label htmlFor="auth-password">Password</label>
          <div className="password-row">
            <input id="auth-password" type={showPassword ? 'text' : 'password'} autoComplete={authMode === 'register' ? 'new-password' : 'current-password'} required minLength={authMode === 'register' ? 8 : 1} maxLength={200} value={password} onChange={(e) => setPassword(e.target.value)} aria-describedby={authMode === 'register' ? 'auth-hint' : undefined} />
            <button type="button" className="btn btn-ghost" aria-pressed={showPassword} onClick={() => setShowPassword((v) => !v)}>{showPassword ? 'Hide' : 'Show'}</button>
          </div>
          {authMode === 'register' && <p id="auth-hint" className="hint">Use at least 8 characters.</p>}
        </div>
        {error && <p role="alert" className="alert alert-error"><span>{error}</span></p>}
        <button className="btn btn-primary btn-block" disabled={saving}>{saving ? 'Please wait…' : authMode === 'register' ? 'Create account' : 'Sign in'}</button>
      </form>
      <button type="button" className="link-btn auth-switch" onClick={() => { setAuthMode(authMode === 'login' ? 'register' : 'login'); setError('') }}>{authMode === 'login' ? 'New here? Create an account' : 'Already have an account? Sign in'}</button>
    </section>
  </main>

  const singular = active?.singular ?? 'item'
  const tableFields = active?.fields.slice(0, 5) ?? []

  return <div className="app-shell">
    <a className="skip-link" href="#main">Skip to main content</a>
    <div className={navOpen ? 'scrim show' : 'scrim'} onClick={() => setNavOpen(false)} aria-hidden="true" />
    <aside id="sidebar" className={navOpen ? 'sidebar open' : 'sidebar'}>
      <div className="sidebar-brand">
        <span className="brand-mark" aria-hidden="true">{APP.name.slice(0, 1).toUpperCase()}</span>
        <span className="brand-text"><strong>{APP.name}</strong><small>Workspace</small></span>
        <button type="button" className="icon-btn drawer-close" aria-label="Close navigation" onClick={() => setNavOpen(false)}><Icon name="x" /></button>
      </div>
      <nav aria-label="Collections" className="entity-nav">
        <p className="nav-caption">Collections</p>
        {APP.entities.map((entity) => <button type="button" key={entity.path} className={active?.path === entity.path ? 'nav-item active' : 'nav-item'} aria-current={active?.path === entity.path ? 'page' : undefined} onClick={() => selectEntity(entity.path)}>
          <span className="nav-dot" aria-hidden="true" />{entity.plural}<span className="nav-count">{(rows[entity.path] ?? []).length}<span className="sr-only"> records</span></span>
        </button>)}
      </nav>
      <div className="sidebar-bottom"><span className={APP.apiEnabled ? 'status-dot live' : 'status-dot local'} aria-hidden="true" /><span>{APP.apiEnabled ? 'Connected workspace' : 'Saved on this device'}</span><small>{APP.dataMode}</small></div>
    </aside>

    <main id="main" tabIndex={-1} className="main-area">
      <header className="topbar">
        <div className="topbar-title">
          <button type="button" className="icon-btn menu-btn" aria-label="Open navigation" aria-expanded={navOpen} aria-controls="sidebar" onClick={() => setNavOpen(true)}><Icon name="menu" /></button>
          <div><p className="eyebrow">{APP.kind.replace(/-/g, ' ')} · overview</p><h1>{active?.plural ?? 'Workspace'}</h1></div>
        </div>
        <div className="topbar-actions">
          {APP.authEnabled && <span className="user-chip">{userName || 'Signed in'}</span>}
          {APP.authEnabled && <button type="button" className="btn btn-secondary" onClick={() => void signOut()}>Sign out</button>}
          <button type="button" className="btn btn-primary" onClick={startNew} disabled={!active}><Icon name="plus" />New {singular.toLowerCase()}</button>
        </div>
      </header>

      <section className="summary-grid" aria-label="Workspace summary">
        <article className="stat"><span>Total records</span><strong>{stats.total}</strong><small>Across {APP.entities.length} {APP.entities.length === 1 ? 'collection' : 'collections'}</small></article>
        <article className="stat"><span>{active?.plural ?? 'Items'}</span><strong>{source.length}</strong><small>In this collection</small></article>
        <article className="stat"><span>{thirdCard.label}</span><strong>{thirdCard.value}</strong><small>{thirdCard.hint}</small></article>
      </section>

      <section className="content-card" aria-labelledby="content-title">
        <div className="content-heading">
          <div><h2 id="content-title">All {active?.plural.toLowerCase() ?? 'records'}</h2><p>Search, filter and sort your records, or create and update them in place.</p></div>
        </div>

        <div className="toolbar">
          <label className="search-box"><Icon name="search" /><span className="sr-only">Search {active?.plural ?? 'records'}</span>
            <input ref={searchRef} type="search" placeholder={`Search ${active?.plural.toLowerCase() ?? 'records'}…`} value={search} onChange={(e) => { setSearch(e.target.value); setLimit(PAGE_SIZE) }} /><kbd aria-hidden="true">/</kbd></label>
          <div className="toolbar-controls">
            <label className="select-label"><span className="sr-only">Sort by</span>
              <select value={sort?.field ?? ''} onChange={(e) => setSort(e.target.value ? { field: e.target.value, dir: sort?.dir ?? 'asc' } : null)}>
                <option value="">Default order</option>{active?.fields.map((f) => <option key={f.name} value={f.name}>Sort: {f.label}</option>)}
              </select></label>
            <button type="button" className="icon-btn bordered" disabled={!sort} aria-label={sort?.dir === 'desc' ? 'Sorted descending. Switch to ascending' : 'Sorted ascending. Switch to descending'} onClick={() => sort && toggleSort(sort.field)}><Icon name={sort?.dir === 'desc' ? 'down' : 'up'} /></button>
            <div className="segmented" role="group" aria-label="Layout">
              <button type="button" aria-pressed={view === 'cards'} aria-label="Card view" onClick={() => setView('cards')}><Icon name="grid" /></button>
              <button type="button" aria-pressed={view === 'table'} aria-label="Table view" onClick={() => setView('table')}><Icon name="list" /></button>
            </div>
          </div>
        </div>

        {statusField && Object.keys(stats.counts).length > 0 && <div className="chips" role="group" aria-label={`Filter by ${statusField.label.toLowerCase()}`}>
          <button type="button" className="chip" aria-pressed={!filter} onClick={() => { setFilter(''); setLimit(PAGE_SIZE) }}>All <span>{source.length}</span></button>
          {statusField.values.filter((v) => stats.counts[v]).map((v) => <button type="button" key={v} className="chip" aria-pressed={filter === v} onClick={() => { setFilter(filter === v ? '' : v); setLimit(PAGE_SIZE) }}>{v.replace(/-/g, ' ')} <span>{stats.counts[v]}</span></button>)}
        </div>}

        {error && <div role="alert" className="alert alert-error"><span>{error}</span>{loadFailed && <button type="button" className="link-btn" onClick={() => void loadAll()}>Try again</button>}</div>}

        {formOpen && active && <form ref={formRef} className="editor-form" noValidate aria-labelledby="form-title" onSubmit={(e) => void submitForm(e)}>
          <div className="form-heading"><div><p className="eyebrow">{editing ? 'Update record' : 'New record'}</p><h3 id="form-title">{editing ? 'Edit' : 'Create'} {singular.toLowerCase()}</h3></div>
            <button type="button" className="icon-btn" aria-label="Close form" onClick={closeForm}><Icon name="x" /></button></div>
          <div className="field-grid">{active.fields.map((field) => <FieldControl key={field.name} field={field} value={draft[field.name]} error={fieldErrors[field.name]} onChange={(v) => setField(field.name, v)} />)}</div>
          {Object.keys(fieldErrors).length > 0 && <p className="hint hint-error" role="status">Please fix the {Object.keys(fieldErrors).length === 1 ? 'highlighted field' : `${Object.keys(fieldErrors).length} highlighted fields`} to continue.</p>}
          <div className="form-actions"><button type="button" className="btn btn-secondary" onClick={closeForm} disabled={saving}>Cancel</button><button className="btn btn-primary" disabled={saving}>{saving ? 'Saving…' : editing ? 'Save changes' : `Create ${singular.toLowerCase()}`}</button></div>
        </form>}

        {loading ? <>
          <p className="sr-only" role="status">Loading your workspace…</p>
          <div className="records-grid" aria-busy="true">{[0, 1, 2, 3].map((i) => <div key={i} className="record-card skeleton" aria-hidden="true"><i /><i /><i /><i /></div>)}</div>
        </> : processed.length === 0 ? <div className="state-panel">
          <div className="empty-icon" aria-hidden="true"><Icon name="inbox" /></div>
          <h3>{filtering ? 'No matching records' : `No ${active?.plural.toLowerCase() ?? 'records'} yet`}</h3>
          <p>{filtering ? 'Try a different search term or clear the filters.' : `Create your first ${singular.toLowerCase()} to get started.`}</p>
          {filtering ? <button type="button" className="btn btn-secondary" onClick={clearFilters}>Clear filters</button> : <button type="button" className="btn btn-primary" onClick={startNew}><Icon name="plus" />Create {singular.toLowerCase()}</button>}
        </div> : view === 'table' && active ? <div className="table-wrap" role="region" aria-label={`${active.plural} table`} tabIndex={0}>
          <table className="data-table"><caption className="sr-only">{active.plural}: {processed.length} records</caption>
            <thead><tr>{tableFields.map((f) => <th key={f.name} scope="col" aria-sort={sort?.field === f.name ? (sort.dir === 'asc' ? 'ascending' : 'descending') : undefined}>
              <button type="button" className="th-btn" onClick={() => toggleSort(f.name)}>{f.label}{sort?.field === f.name && <Icon name={sort.dir === 'asc' ? 'up' : 'down'} />}</button></th>)}
              <th scope="col"><span className="sr-only">Actions</span></th></tr></thead>
            <tbody>{shown.map((row, index) => {
              const d = describe(row, active, index)
              return <tr key={`${recordId(row, index)}-${index}`}>
                {tableFields.map((f, ci) => <td key={f.name} className={ci === 0 ? 'cell-strong' : undefined}><Value field={f} value={row[f.name]} /></td>)}
                <td className="row-actions"><button type="button" className="icon-btn" aria-label={`Edit ${d.title}`} onClick={() => startEdit(row)}><Icon name="edit" /></button><button type="button" className="icon-btn danger" aria-label={`Delete ${d.title}`} onClick={() => askDelete(row, index, d.title)}><Icon name="trash" /></button></td>
              </tr>
            })}</tbody></table>
        </div> : <div className="records-grid">{shown.map((row, index) => {
          if (!active) return null
          const d = describe(row, active, index)
          const details = active.fields.filter((f) => f !== statusField && f.name !== d.titleKey && f.name !== d.bodyKey).slice(0, 4)
          return <article className="record-card" key={`${recordId(row, index)}-${index}`} style={{ '--i': Math.min(index, 8) } as CSSProperties}>
            <header className="record-top"><h3>{d.title}</h3>{statusField && <Value field={statusField} value={row[statusField.name]} />}</header>
            {d.body && <p className="record-description">{d.body}</p>}
            {details.length > 0 && <dl className="record-fields">{details.map((field) => <div key={field.name}><dt>{field.label}</dt><dd><Value field={field} value={row[field.name]} /></dd></div>)}</dl>}
            <footer className="record-actions">
              <button type="button" className="btn btn-secondary btn-sm" aria-label={`Edit ${d.title}`} onClick={() => startEdit(row)}><Icon name="edit" />Edit</button>
              <button type="button" className="btn btn-danger btn-sm" aria-label={`Delete ${d.title}`} onClick={() => askDelete(row, index, d.title)}><Icon name="trash" />Delete</button>
            </footer>
          </article>
        })}</div>}

        {!loading && processed.length > shown.length && <div className="load-more"><button type="button" className="btn btn-secondary" onClick={() => setLimit((l) => l + PAGE_SIZE)}>Show {Math.min(PAGE_SIZE, processed.length - shown.length)} more</button></div>}

        <footer className="content-footer"><span aria-live="polite">Showing {shown.length} of {processed.length}{filtering ? ` (filtered from ${source.length})` : ''}</span><span>{APP.apiEnabled ? 'Synced through API' : 'Stored in this browser'}</span></footer>
      </section>
      <footer className="app-footer"><span>{APP.name}</span><span>{APP.apiEnabled ? 'API-backed workspace' : 'Device-local workspace'}</span></footer>
    </main>

    <div className="toast-region" aria-live="polite" aria-atomic="true">{notice && <p className="toast"><Icon name="check" />{notice}</p>}</div>

    <dialog ref={dialogRef} className="confirm" aria-labelledby="confirm-title" aria-describedby="confirm-desc" onClose={() => setPendingDelete(null)} onClick={(e) => { if (e.target === e.currentTarget) e.currentTarget.close() }}>
      <div className="confirm-body">
        <h2 id="confirm-title">Delete {singular.toLowerCase()}?</h2>
        <p id="confirm-desc">“{pendingDelete?.title}” will be permanently removed. This cannot be undone.</p>
        <div className="form-actions"><button type="button" className="btn btn-secondary" onClick={() => dialogRef.current?.close()}>Cancel</button><button type="button" className="btn btn-danger-solid" onClick={() => void confirmDelete()}>Delete</button></div>
      </div>
    </dialog>
  </div>
}
'''

_CSS = r'''@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');

/* ---------- Tokens (derived from the design system, with safe fallbacks) ---------- */
:root{
  --a-bg:var(--bg,#0b1020);--a-fg:var(--fg,#eef1f8);--a-muted:var(--muted,#8b93a7);
  --a-primary:var(--primary,#6366f1);--a-accent:var(--accent,#22d3ee);--a-on-primary:#fff;
  --a-line:color-mix(in srgb,var(--a-muted) 24%,transparent);
  --a-surface:color-mix(in srgb,var(--a-bg) 94%,var(--a-fg));
  --a-raised:color-mix(in srgb,var(--a-bg) 89%,var(--a-fg));
  --a-tint:color-mix(in srgb,var(--a-bg) 88%,var(--a-primary));
  --a-danger:#e5484d;--a-success:#2fa77a;--a-warn:#d99a1f;
  --a-radius:14px;--a-ease:cubic-bezier(.2,.7,.2,1);
  --a-shadow:0 1px 2px rgba(0,0,0,.12),0 14px 36px rgba(0,0,0,.14);
}

/* ---------- Base ---------- */
*,*::before,*::after{box-sizing:border-box}
html{-webkit-text-size-adjust:100%;scroll-behavior:smooth}
body{margin:0;min-height:100vh;min-height:100dvh;font-family:var(--font-body,'DM Sans'),system-ui,-apple-system,'Segoe UI',sans-serif;font-size:15px;line-height:1.55;color:var(--a-fg);-webkit-font-smoothing:antialiased;background:radial-gradient(ellipse at 78% -12%,color-mix(in srgb,var(--a-primary) 16%,transparent),transparent 42%),var(--a-bg)}
body.nav-locked{overflow:hidden}
h1,h2,h3,p,dl,dd{margin:0}
h1,h2,h3,.brand-mark,.stat strong{font-family:var(--font-head,'Space Grotesk'),system-ui,sans-serif}
button,input,textarea,select{font:inherit;color:inherit}
button{cursor:pointer}
button:disabled{cursor:not-allowed;opacity:.55}
a{color:var(--a-accent);text-underline-offset:3px}
:focus-visible{outline:2px solid var(--a-accent);outline-offset:2px}
main:focus{outline:none}
.icon{width:18px;height:18px;flex:none}
.sr-only{position:absolute;width:1px;height:1px;margin:-1px;padding:0;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0}
.skip-link{position:fixed;left:12px;top:-60px;z-index:100;padding:10px 16px;border-radius:10px;background:var(--a-primary);color:var(--a-on-primary);font-weight:600;text-decoration:none;transition:top .2s var(--a-ease)}
.skip-link:focus{top:12px}
.eyebrow,.nav-caption{font-size:11px;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:var(--a-muted)}
.muted{color:var(--a-muted);font-size:14px}
.dim{color:var(--a-muted)}

/* ---------- Shell ---------- */
.app-shell{min-height:100vh;min-height:100dvh;display:grid;grid-template-columns:264px minmax(0,1fr)}
.sidebar{position:sticky;top:0;height:100vh;height:100dvh;overflow-y:auto;padding:24px 14px 16px;border-right:1px solid var(--a-line);background:color-mix(in srgb,var(--a-bg) 94%,transparent);display:flex;flex-direction:column;gap:22px;z-index:40}
.sidebar-brand{display:flex;align-items:center;gap:12px;padding:0 8px}
.brand-mark{display:grid;place-items:center;width:40px;height:40px;border-radius:13px;background:linear-gradient(145deg,var(--a-primary),var(--a-accent));color:var(--a-on-primary);font-size:20px;font-weight:700;box-shadow:0 8px 24px color-mix(in srgb,var(--a-primary) 28%,transparent);flex:none}
.brand-text{min-width:0}
.brand-text strong{display:block;font-size:15px;font-weight:600;overflow-wrap:anywhere;line-height:1.25}
.brand-text small{display:block;font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:var(--a-muted);margin-top:3px}
.drawer-close{display:none;margin-left:auto}
.entity-nav{display:grid;gap:4px}
.nav-caption{padding:0 10px;margin-bottom:6px}
.nav-item{display:flex;gap:10px;align-items:center;width:100%;min-height:42px;border:1px solid transparent;background:transparent;color:var(--a-muted);padding:9px 10px;border-radius:12px;text-align:left;font-size:14px;font-weight:500;transition:background .18s,color .18s,border-color .18s}
.nav-item:hover{color:var(--a-fg);background:var(--a-tint)}
.nav-item.active{color:var(--a-fg);background:color-mix(in srgb,var(--a-primary) 16%,var(--a-surface));border-color:color-mix(in srgb,var(--a-primary) 38%,transparent)}
.nav-dot{width:7px;height:7px;border-radius:50%;background:var(--a-muted);opacity:.7;flex:none}
.nav-item.active .nav-dot{background:var(--a-accent);opacity:1;box-shadow:0 0 10px var(--a-accent)}
.nav-count{margin-left:auto;font-size:12px;font-variant-numeric:tabular-nums;color:var(--a-muted)}
.sidebar-bottom{margin-top:auto;padding:14px;border:1px solid var(--a-line);border-radius:14px;font-size:13px;background:var(--a-surface)}
.sidebar-bottom small{display:block;color:var(--a-muted);margin:6px 0 0 16px;font-size:12px;overflow-wrap:anywhere}
.status-dot{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:8px}
.status-dot.live{background:var(--a-success);box-shadow:0 0 0 3px color-mix(in srgb,var(--a-success) 25%,transparent)}
.status-dot.local{background:var(--a-warn);box-shadow:0 0 0 3px color-mix(in srgb,var(--a-warn) 25%,transparent)}
.scrim{display:none}
.main-area{min-width:0;padding:28px clamp(16px,3vw,44px) 22px;max-width:1280px;width:100%}
.topbar{display:flex;align-items:center;justify-content:space-between;gap:16px;margin-bottom:24px;flex-wrap:wrap}
.topbar-title{display:flex;align-items:center;gap:12px;min-width:0}
.topbar h1{font-size:clamp(26px,3vw,36px);font-weight:600;letter-spacing:-.04em;line-height:1.15;margin-top:6px;overflow-wrap:anywhere}
.topbar-actions{display:flex;align-items:center;gap:10px;flex-wrap:wrap}
.menu-btn{display:none}
.user-chip{font-size:13px;color:var(--a-muted);padding:8px 14px;border:1px solid var(--a-line);border-radius:999px;max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}

/* ---------- Buttons ---------- */
.btn{display:inline-flex;align-items:center;justify-content:center;gap:8px;min-height:40px;padding:9px 16px;border-radius:11px;border:1px solid transparent;font-size:14px;font-weight:600;line-height:1.2;transition:transform .16s var(--a-ease),background .16s,border-color .16s,filter .16s}
.btn:active:not(:disabled){transform:translateY(1px)}
.btn-primary{background:linear-gradient(120deg,var(--a-primary),color-mix(in srgb,var(--a-primary) 62%,var(--a-accent)));color:var(--a-on-primary);box-shadow:0 8px 20px color-mix(in srgb,var(--a-primary) 22%,transparent)}
.btn-primary:hover:not(:disabled){filter:brightness(1.08);transform:translateY(-1px)}
.btn-secondary{background:var(--a-surface);border-color:var(--a-line);color:var(--a-fg)}
.btn-secondary:hover:not(:disabled){border-color:color-mix(in srgb,var(--a-accent) 55%,var(--a-line));background:var(--a-tint)}
.btn-ghost{background:transparent;border-color:var(--a-line);color:var(--a-muted)}
.btn-ghost:hover:not(:disabled){color:var(--a-fg);background:var(--a-tint)}
.btn-danger{background:color-mix(in srgb,var(--a-danger) 10%,transparent);border-color:color-mix(in srgb,var(--a-danger) 28%,transparent);color:color-mix(in srgb,var(--a-danger) 72%,var(--a-fg))}
.btn-danger:hover:not(:disabled){background:color-mix(in srgb,var(--a-danger) 18%,transparent)}
.btn-danger-solid{background:var(--a-danger);color:#fff}
.btn-danger-solid:hover:not(:disabled){filter:brightness(1.1)}
.btn-sm{min-height:34px;padding:6px 12px;font-size:13px}
.btn-block{width:100%}
.icon-btn{display:inline-grid;place-items:center;width:40px;height:40px;border-radius:11px;border:1px solid transparent;background:transparent;color:var(--a-muted);transition:background .16s,color .16s,border-color .16s}
.icon-btn:hover:not(:disabled){color:var(--a-fg);background:var(--a-tint)}
.icon-btn.bordered{border-color:var(--a-line);background:var(--a-surface)}
.icon-btn.danger:hover:not(:disabled){color:color-mix(in srgb,var(--a-danger) 72%,var(--a-fg));background:color-mix(in srgb,var(--a-danger) 12%,transparent)}
.link-btn{background:none;border:0;padding:4px 2px;color:var(--a-accent);font-weight:600;font-size:14px;text-decoration:underline;text-underline-offset:3px}

/* ---------- Summary ---------- */
.summary-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px;margin-bottom:20px}
.stat{padding:18px 20px;border:1px solid var(--a-line);border-radius:var(--a-radius);background:linear-gradient(140deg,var(--a-surface),color-mix(in srgb,var(--a-bg) 86%,var(--a-primary)));box-shadow:var(--a-shadow);min-width:0}
.stat span,.stat small{display:block;color:var(--a-muted);font-size:13px}
.stat strong{display:block;font-size:clamp(26px,3vw,34px);font-weight:600;letter-spacing:-.04em;line-height:1.1;margin:10px 0 6px;font-variant-numeric:tabular-nums;overflow-wrap:anywhere}

/* ---------- Content card & toolbar ---------- */
.content-card{border:1px solid var(--a-line);border-radius:20px;background:var(--a-surface);box-shadow:var(--a-shadow);padding:clamp(16px,2.2vw,26px);min-width:0}
.content-heading{margin-bottom:18px}
.content-heading h2{font-size:21px;font-weight:600;letter-spacing:-.025em;margin-bottom:4px}
.content-heading p{font-size:14px;color:var(--a-muted)}
.toolbar{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap;margin-bottom:14px}
.toolbar-controls{display:flex;align-items:center;gap:8px;flex-wrap:wrap}
.search-box{flex:1 1 240px;max-width:380px;display:flex;align-items:center;gap:8px;min-height:42px;border:1px solid var(--a-line);background:var(--a-bg);border-radius:11px;padding:0 12px;color:var(--a-muted);transition:border-color .16s,box-shadow .16s}
.search-box:focus-within{border-color:var(--a-accent);box-shadow:0 0 0 3px color-mix(in srgb,var(--a-accent) 22%,transparent)}
.search-box input{min-width:0;width:100%;background:transparent;border:0;outline:0;padding:10px 0;font-size:14px;color:var(--a-fg)}
.search-box input::-webkit-search-cancel-button{cursor:pointer}
kbd{font:600 11px/1 var(--font-body,'DM Sans'),monospace;border:1px solid var(--a-line);border-radius:6px;padding:4px 7px;color:var(--a-muted)}
.select-label select,.field select{appearance:none;background-image:linear-gradient(45deg,transparent 50%,var(--a-muted) 50%),linear-gradient(135deg,var(--a-muted) 50%,transparent 50%);background-position:calc(100% - 17px) 55%,calc(100% - 12px) 55%;background-size:5px 5px;background-repeat:no-repeat;padding-right:32px}
.select-label select{min-height:40px;border:1px solid var(--a-line);border-radius:11px;background-color:var(--a-bg);padding:8px 32px 8px 12px;font-size:14px;max-width:190px}
.segmented{display:inline-flex;border:1px solid var(--a-line);border-radius:11px;overflow:hidden;background:var(--a-bg)}
.segmented button{display:grid;place-items:center;width:40px;height:40px;border:0;background:transparent;color:var(--a-muted)}
.segmented button[aria-pressed=true]{background:color-mix(in srgb,var(--a-primary) 20%,var(--a-bg));color:var(--a-fg)}
.chips{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:16px}
.chip{display:inline-flex;align-items:center;gap:8px;min-height:34px;padding:5px 13px;border-radius:999px;border:1px solid var(--a-line);background:var(--a-bg);color:var(--a-muted);font-size:13px;font-weight:600;text-transform:capitalize;transition:background .16s,color .16s,border-color .16s}
.chip span{font-size:12px;font-variant-numeric:tabular-nums;opacity:.8}
.chip:hover{color:var(--a-fg);border-color:color-mix(in srgb,var(--a-accent) 45%,var(--a-line))}
.chip[aria-pressed=true]{color:var(--a-fg);background:color-mix(in srgb,var(--a-primary) 20%,var(--a-bg));border-color:color-mix(in srgb,var(--a-primary) 50%,transparent)}

/* ---------- Alerts, toast ---------- */
.alert{display:flex;align-items:center;justify-content:space-between;gap:12px;border-radius:12px;padding:12px 14px;font-size:14px;margin:0 0 16px;overflow-wrap:anywhere}
.alert-error{color:color-mix(in srgb,var(--a-danger) 70%,var(--a-fg));border:1px solid color-mix(in srgb,var(--a-danger) 32%,transparent);background:color-mix(in srgb,var(--a-danger) 9%,transparent)}
.toast-region{position:fixed;left:50%;bottom:22px;transform:translateX(-50%);z-index:60;pointer-events:none;width:max-content;max-width:calc(100vw - 32px)}
.toast{display:flex;align-items:center;gap:10px;padding:12px 18px;border-radius:999px;background:var(--a-fg);color:var(--a-bg);font-size:14px;font-weight:600;box-shadow:0 14px 38px rgba(0,0,0,.35);animation:toast-in .3s var(--a-ease)}
.toast .icon{color:var(--a-success)}

/* ---------- Form ---------- */
.editor-form{border:1px solid color-mix(in srgb,var(--a-primary) 40%,var(--a-line));background:var(--a-tint);border-radius:16px;padding:clamp(14px,2vw,22px);margin-bottom:22px;animation:rise .3s var(--a-ease)}
.form-heading{display:flex;align-items:flex-start;justify-content:space-between;gap:10px;margin-bottom:16px}
.form-heading h3{margin-top:6px;font-size:19px;font-weight:600}
.field-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px}
.field{display:grid;gap:7px;min-width:0;align-content:start}
.field-wide{grid-column:1/-1}
.field>label{font-size:13px;font-weight:600;color:var(--a-fg)}
.req{color:var(--a-danger)}
.field input:not([type=checkbox]),.field select,.field textarea{width:100%;min-width:0;min-height:42px;border:1px solid var(--a-line);background:var(--a-bg);border-radius:10px;padding:10px 12px;color:var(--a-fg);font-size:14px;transition:border-color .16s,box-shadow .16s}
.field textarea{resize:vertical;min-height:96px}
.field input:focus-visible,.field select:focus-visible,.field textarea:focus-visible{outline:0;border-color:var(--a-accent);box-shadow:0 0 0 3px color-mix(in srgb,var(--a-accent) 24%,transparent)}
.field [aria-invalid=true]{border-color:var(--a-danger)}
.field-error{font-size:13px;color:color-mix(in srgb,var(--a-danger) 70%,var(--a-fg))}
.hint{font-size:13px;color:var(--a-muted)}
.hint-error{margin-top:14px;color:color-mix(in srgb,var(--a-danger) 70%,var(--a-fg))}
.check{display:flex;align-items:center;gap:10px;min-height:42px;cursor:pointer;font-size:14px;font-weight:600}
.check input{width:18px;height:18px;accent-color:var(--a-primary)}
.form-actions{display:flex;justify-content:flex-end;gap:10px;margin-top:18px;flex-wrap:wrap}

/* ---------- Records ---------- */
.records-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,320px),1fr));gap:14px}
.record-card{border:1px solid var(--a-line);background:var(--a-bg);border-radius:var(--a-radius);padding:18px;min-width:0;display:flex;flex-direction:column;gap:12px;transition:transform .2s var(--a-ease),border-color .2s,box-shadow .2s;animation:rise .4s var(--a-ease) both;animation-delay:calc(var(--i,0)*40ms)}
.record-card:hover{transform:translateY(-2px);border-color:color-mix(in srgb,var(--a-primary) 42%,var(--a-line));box-shadow:var(--a-shadow)}
.record-top{display:flex;align-items:flex-start;justify-content:space-between;gap:10px}
.record-top h3{font-size:17px;font-weight:600;line-height:1.3;overflow-wrap:anywhere}
.record-description{font-size:14px;line-height:1.65;color:var(--a-muted);overflow-wrap:anywhere;white-space:pre-wrap;display:-webkit-box;-webkit-line-clamp:4;-webkit-box-orient:vertical;overflow:hidden}
.record-fields{display:grid;gap:6px;margin-top:auto}
.record-fields div{display:flex;justify-content:space-between;gap:12px;border-top:1px solid var(--a-line);padding-top:8px;font-size:13px}
.record-fields dt{color:var(--a-muted)}
.record-fields dd{text-align:right;overflow-wrap:anywhere;min-width:0}
.record-actions{display:flex;justify-content:flex-end;gap:8px;border-top:1px solid var(--a-line);padding-top:12px}
.badge{display:inline-block;font-size:12px;font-weight:700;letter-spacing:.03em;text-transform:capitalize;border-radius:999px;padding:3px 10px;border:1px solid transparent;white-space:nowrap;max-width:100%;overflow:hidden;text-overflow:ellipsis}
.badge-neutral{color:var(--a-muted);background:color-mix(in srgb,var(--a-muted) 12%,transparent);border-color:var(--a-line)}
.badge-good{color:color-mix(in srgb,var(--a-success) 75%,var(--a-fg));background:color-mix(in srgb,var(--a-success) 13%,transparent);border-color:color-mix(in srgb,var(--a-success) 30%,transparent)}
.badge-warn{color:color-mix(in srgb,var(--a-warn) 75%,var(--a-fg));background:color-mix(in srgb,var(--a-warn) 13%,transparent);border-color:color-mix(in srgb,var(--a-warn) 32%,transparent)}
.badge-bad{color:color-mix(in srgb,var(--a-danger) 72%,var(--a-fg));background:color-mix(in srgb,var(--a-danger) 12%,transparent);border-color:color-mix(in srgb,var(--a-danger) 30%,transparent)}
.load-more{display:flex;justify-content:center;margin-top:18px}

/* ---------- Table ---------- */
.table-wrap{overflow-x:auto;border:1px solid var(--a-line);border-radius:var(--a-radius);background:var(--a-bg)}
.data-table{width:100%;border-collapse:collapse;font-size:14px;min-width:560px}
.data-table th,.data-table td{padding:12px 14px;text-align:left;border-bottom:1px solid var(--a-line);vertical-align:middle}
.data-table th{font-size:12px;letter-spacing:.06em;text-transform:uppercase;color:var(--a-muted);background:var(--a-surface);white-space:nowrap}
.data-table tbody tr:last-child td{border-bottom:0}
.data-table tbody tr:hover{background:var(--a-tint)}
.th-btn{display:inline-flex;align-items:center;gap:6px;background:none;border:0;padding:0;font:inherit;letter-spacing:inherit;text-transform:inherit;color:inherit}
.th-btn:hover{color:var(--a-fg)}
.th-btn .icon{width:14px;height:14px}
.cell-strong{font-weight:600}
.row-actions{white-space:nowrap;text-align:right!important}

/* ---------- States ---------- */
.state-panel{min-height:260px;display:flex;align-items:center;justify-content:center;flex-direction:column;text-align:center;color:var(--a-muted);gap:10px;padding:24px}
.state-panel h3{color:var(--a-fg);font-size:19px;font-weight:600;margin-top:6px}
.state-panel p{font-size:14px;max-width:38ch;margin-bottom:6px}
.empty-icon{display:grid;place-items:center;width:56px;height:56px;border-radius:16px;background:var(--a-tint);color:var(--a-accent)}
.empty-icon .icon{width:26px;height:26px}
.skeleton{gap:14px;pointer-events:none}
.skeleton i{display:block;height:14px;border-radius:7px;background:linear-gradient(90deg,var(--a-raised) 25%,var(--a-tint) 50%,var(--a-raised) 75%);background-size:200% 100%;animation:shimmer 1.4s linear infinite}
.skeleton i:nth-child(1){width:60%;height:20px}.skeleton i:nth-child(2){width:100%}.skeleton i:nth-child(3){width:80%}.skeleton i:nth-child(4){width:40%;height:32px;margin-left:auto}
.content-footer{border-top:1px solid var(--a-line);padding-top:14px;margin-top:20px;display:flex;justify-content:space-between;gap:10px;flex-wrap:wrap;color:var(--a-muted);font-size:13px}
.app-footer{display:flex;justify-content:space-between;gap:10px;flex-wrap:wrap;color:var(--a-muted);font-size:13px;margin:18px 4px 0}

/* ---------- Confirm dialog ---------- */
dialog.confirm{border:1px solid var(--a-line);border-radius:18px;padding:0;background:var(--a-surface);color:var(--a-fg);width:min(92vw,420px);box-shadow:0 24px 70px rgba(0,0,0,.45)}
dialog.confirm::backdrop{background:rgba(5,8,18,.62);backdrop-filter:blur(3px)}
dialog.confirm[open]{animation:rise .22s var(--a-ease)}
.confirm-body{padding:24px}
.confirm-body h2{font-size:20px;font-weight:600;margin-bottom:8px}
.confirm-body p{font-size:14px;color:var(--a-muted);overflow-wrap:anywhere}

/* ---------- Auth ---------- */
.auth-wrap{min-height:100vh;min-height:100dvh;display:grid;place-items:center;padding:22px}
.auth-card{width:min(100%,420px);padding:clamp(22px,4vw,34px);border:1px solid var(--a-line);border-radius:22px;background:var(--a-surface);box-shadow:var(--a-shadow)}
.auth-card .brand-mark{margin-bottom:20px}
.auth-card h1{font-size:30px;font-weight:600;letter-spacing:-.04em;margin:8px 0 6px}
.form-stack{display:grid;gap:16px;margin-top:24px}
.form-stack input{width:100%;min-height:44px;border:1px solid var(--a-line);background:var(--a-bg);border-radius:10px;padding:10px 12px;font-size:14px}
.form-stack input:focus-visible{outline:0;border-color:var(--a-accent);box-shadow:0 0 0 3px color-mix(in srgb,var(--a-accent) 24%,transparent)}
.password-row{display:flex;gap:8px}
.auth-switch{display:block;width:100%;margin-top:14px;text-align:center}

/* ---------- Motion ---------- */
@keyframes rise{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}
@keyframes toast-in{from{opacity:0;transform:translateY(12px) scale(.96)}to{opacity:1;transform:none}}
@keyframes shimmer{to{background-position:-200% 0}}

/* ---------- Responsive ---------- */
@media(max-width:900px){
  .app-shell{display:block}
  .menu-btn,.drawer-close{display:inline-grid}
  .sidebar{position:fixed;inset:0 auto 0 0;width:min(86vw,300px);transform:translateX(-102%);visibility:hidden;transition:transform .26s var(--a-ease),visibility 0s .26s;background:var(--a-surface);box-shadow:var(--a-shadow)}
  .sidebar.open{transform:none;visibility:visible;transition-delay:0s}
  .scrim{display:block;position:fixed;inset:0;z-index:30;background:rgba(5,8,18,.55);backdrop-filter:blur(2px);opacity:0;pointer-events:none;transition:opacity .22s}
  .scrim.show{opacity:1;pointer-events:auto}
  .main-area{padding:20px 16px}
  .summary-grid{grid-template-columns:repeat(3,minmax(0,1fr));gap:10px}
  .stat{padding:14px}
  kbd{display:none}
}
@media(max-width:640px){
  body{font-size:16px}
  .topbar-actions{width:100%}
  .topbar-actions .btn-primary{margin-left:auto}
  .summary-grid{grid-template-columns:minmax(0,1fr)}
  .stat{display:grid;grid-template-columns:1fr auto;align-items:center;gap:0 12px}
  .stat strong{grid-row:1/3;grid-column:2;margin:0}
  .toolbar,.toolbar-controls{width:100%}
  .search-box{max-width:none;flex-basis:100%}
  .toolbar-controls{justify-content:space-between}
  .select-label{flex:1}.select-label select{max-width:none;width:100%}
  .field-grid{grid-template-columns:minmax(0,1fr)}
  .field-wide{grid-column:auto}
  .field input:not([type=checkbox]),.field select,.field textarea,.search-box input,.form-stack input,.select-label select{font-size:16px}
  .form-actions .btn,.confirm-body .btn{flex:1}
  .record-actions .btn{flex:1}
  .toast-region{bottom:16px}
}
@media(pointer:coarse){
  .btn,.icon-btn,.chip,.nav-item,.segmented button{min-height:44px}
  .icon-btn,.segmented button{min-width:44px}
}
@media(prefers-contrast:more){
  :root{--a-line:color-mix(in srgb,var(--a-muted) 60%,transparent)}
}
@media(forced-colors:active){
  .btn,.chip,.nav-item.active,.badge{border:1px solid ButtonText}
  .skeleton i{background:GrayText}
}
@media(prefers-reduced-motion:reduce){
  html{scroll-behavior:auto}
  *,*::before,*::after{animation-duration:.01ms!important;animation-iteration-count:1!important;animation-delay:0s!important;scroll-behavior:auto!important;transition-duration:.01ms!important;transition-delay:0s!important}
  .record-card:hover,.btn-primary:hover:not(:disabled){transform:none}
}
'''
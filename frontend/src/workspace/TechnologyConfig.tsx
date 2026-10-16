import { useEffect, useMemo, useRef, useState } from 'react'
import { ChevronDown, ChevronUp, Cpu, SlidersHorizontal, Sparkles } from 'lucide-react'
import { api, type StackCatalog, type StackDraft, type StackResolution } from '../services/api'

const FIELDS: { key: string; label: string; help: string }[] = [
  { key: 'frontend', label: 'Frontend framework', help: 'The UI runtime and component model.' },
  { key: 'frontend_lang', label: 'Frontend language', help: 'Programming language used by the frontend.' },
  { key: 'backend', label: 'Backend framework', help: 'Choose none for a frontend-only site or a BaaS.' },
  { key: 'backend_lang', label: 'Backend language', help: 'Language used by the server-side application.' },
  { key: 'database', label: 'Database', help: 'Choose based on relations, transactions, and access patterns.' },
  { key: 'orm', label: 'ORM / data access', help: 'The database access layer compatible with the stack.' },
  { key: 'auth', label: 'Authentication', help: 'Only enable sign-in when the product needs it.' },
  { key: 'cache', label: 'Cache', help: 'Optional; avoid adding one without a reason.' },
  { key: 'storage', label: 'File storage', help: 'Optional storage for uploads and generated files.' },
  { key: 'ai', label: 'AI integration', help: 'Python can be added as a module or isolated service when needed.' },
  { key: 'testing', label: 'Frontend test runner', help: 'This is separate from the agent’s built-in verification checks.' },
  { key: 'deploy', label: 'Deployment target', help: 'Planned targets are shown honestly and may need additional generator support.' },
]

const MANUAL_DEFAULTS: Record<string, string> = {
  frontend: 'react', frontend_lang: 'ts', backend: 'express', backend_lang: 'js', database: 'sqlite',
}

function loadSaved(): StackDraft | null {
  try {
    const value = localStorage.getItem('fullstack-agent-stack-preferences-v1')
    if (!value) return null
    const parsed = JSON.parse(value) as StackDraft
    if (!['automatic', 'manual', 'hybrid'].includes(parsed.mode) || typeof parsed.prefs !== 'object') return null
    return parsed
  } catch { return null }
}

function prettyStatus(value?: string) {
  if (!value || value === 'ready') return 'Ready'
  if (value.startsWith('planned:')) return `Planned · phase ${value.split(':')[1]}`
  return value
}

export function savedStackDraft(): StackDraft {
  return loadSaved() ?? { mode: 'automatic', prefs: {} }
}

export default function TechnologyConfig({
  brief, value, onChange, onResolution,
}: {
  brief: string
  value: StackDraft
  onChange: (next: StackDraft) => void
  onResolution: (result: StackResolution | null) => void
}) {
  const [open, setOpen] = useState(false)
  const [catalog, setCatalog] = useState<StackCatalog | null>(null)
  const [resolution, setResolution] = useState<StackResolution | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const requestSeq = useRef(0)

  useEffect(() => { api.stackCatalog().then(setCatalog).catch((e) => setError((e as Error).message)) }, [])
  useEffect(() => {
    try { localStorage.setItem('fullstack-agent-stack-preferences-v1', JSON.stringify(value)) } catch { /* storage may be disabled */ }
  }, [value])

  useEffect(() => {
    if (!brief.trim()) { setResolution(null); onResolution(null); setBusy(false); return }
    const seq = ++requestSeq.current
    setResolution(null); onResolution(null); setBusy(true)
    const timer = window.setTimeout(async () => {
      setError('')
      try {
        const result = await api.resolveStack(value.mode, value.mode === 'automatic' ? {} : value.prefs, brief)
        if (seq !== requestSeq.current) return
        setResolution(result); onResolution(result)
      } catch (e) {
        if (seq === requestSeq.current) { setError((e as Error).message); setResolution(null); onResolution(null) }
      } finally { if (seq === requestSeq.current) setBusy(false) }
    }, 250)
    return () => window.clearTimeout(timer)
  }, [brief, value, onResolution])

  const catalogOptions = useMemo(() => catalog?.fields ?? {}, [catalog])

  const setMode = (mode: StackDraft['mode']) => {
    let prefs = value.prefs
    if (mode === 'manual') prefs = { ...MANUAL_DEFAULTS, ...prefs }
    onChange({ mode, prefs: { ...prefs } })
  }

  const setField = (field: string, raw: string) => {
    const prefs = { ...value.prefs }
    if (raw === 'auto') delete prefs[field]
    else prefs[field] = raw
    if (field === 'frontend' && raw === 'auto') {
      delete prefs.frontend_lang; delete prefs.testing
    }
    if (field === 'frontend' && raw !== 'auto') {
      const langs = catalogOptions.frontend?.find((o) => o.id === raw)?.langs ?? []
      if (!langs.includes(prefs.frontend_lang)) prefs.frontend_lang = langs.includes('ts') ? 'ts' : (langs[0] ?? 'js')
      if (prefs.testing && !(catalog?.testing_for?.[raw] ?? []).includes(prefs.testing)) delete prefs.testing
    }
    if (field === 'backend' && raw === 'auto') {
      delete prefs.backend_lang; delete prefs.orm
    }
    if (field === 'backend' && raw !== 'auto') {
      const langs = catalogOptions.backend?.find((o) => o.id === raw)?.langs ?? []
      if (!langs.includes(prefs.backend_lang)) {
        if (langs.length) prefs.backend_lang = langs[0]
        else delete prefs.backend_lang
      }
      delete prefs.orm
    }
    if (field === 'database') delete prefs.orm
    onChange({ ...value, prefs })
  }

  const displayed = resolution?.stack ?? {}
  const effectiveLabel = (field: string, valueId?: string) => {
    const options = catalogOptions[field] ?? []
    return options.find((o) => o.id === valueId)?.label ?? valueId ?? 'Not selected'
  }
  const selectedFields = ['frontend', 'frontend_lang', 'backend', 'backend_lang', 'database', 'auth', 'ai']

  return (
    <section className="rounded-xl border border-white/10 bg-black/20">
      <button type="button" className="flex w-full items-center gap-2 px-3 py-3 text-left" aria-expanded={open} onClick={() => setOpen((x) => !x)}>
        <span className="grid h-8 w-8 place-items-center rounded-lg bg-violet-400/10 text-violet-200"><SlidersHorizontal size={16} /></span>
        <span className="min-w-0 flex-1">
          <span className="block text-sm font-medium text-white">Technology configuration</span>
          <span className="block truncate text-[11px] text-zinc-500">Automatic, Manual or Hybrid · current preferences are saved on this device</span>
        </span>
        {open ? <ChevronUp size={16} className="text-zinc-500" /> : <ChevronDown size={16} className="text-zinc-500" />}
      </button>
      {open && <div className="space-y-3 border-t border-white/10 p-3">
        <div className="grid grid-cols-3 gap-2" role="group" aria-label="Technology selection mode">
          {([
            ['automatic', 'Automatic', 'Agent chooses the compatible stack'],
            ['hybrid', 'Hybrid', 'Lock some choices; auto-select the rest'],
            ['manual', 'Manual', 'Choose frontend, backend and database'],
          ] as const).map(([id, title, desc]) => <button type="button" key={id} onClick={() => setMode(id)} aria-pressed={value.mode === id}
            className={`rounded-lg border p-2 text-left transition ${value.mode === id ? 'border-violet-300/50 bg-violet-400/10 text-white' : 'border-white/10 text-zinc-400 hover:border-white/20'}`}>
            <span className="block text-xs font-semibold">{title}</span><span className="mt-1 block text-[10px] leading-4 text-zinc-500">{desc}</span>
          </button>)}
        </div>

        {value.mode !== 'automatic' && <div className="grid gap-3 sm:grid-cols-2">
          {FIELDS.map(({ key, label, help }) => {
            const rows = catalogOptions[key] ?? []
            const chosen = value.prefs[key] ?? (value.mode === 'manual' ? displayed[key] : 'auto')
            const activeRows = key === 'frontend_lang'
              ? rows.filter((r) => !value.prefs.frontend || r.id === 'auto' || (catalogOptions.frontend?.find((f) => f.id === value.prefs.frontend)?.langs ?? []).includes(r.id))
              : key === 'backend_lang'
                ? rows.filter((r) => !value.prefs.backend || r.id === 'auto' || (catalogOptions.backend?.find((b) => b.id === value.prefs.backend)?.langs ?? []).includes(r.id))
                : key === 'orm' && resolution?.options?.orm
                  ? rows.filter((r) => resolution.options?.orm?.some((o) => o.id === r.id))
                  : rows
            return <div key={key} className="min-w-0">
              <label className="label" htmlFor={`stack-${key}`}>{label}</label>
              <select id={`stack-${key}`} className="field" value={chosen} onChange={(e) => setField(key, e.target.value)}>
                {value.mode === 'hybrid' && <option value="auto">Automatic selection</option>}
                {activeRows.map((row) => {
                  const resolvedOption = resolution?.options?.[key]?.find((o) => o.id === row.id)
                  const status = resolvedOption?.status ?? row.status
                  const why = resolvedOption?.why_not || row.desc || ''
                  return <option key={row.id} value={row.id} title={why}>{row.label}{status && status !== 'ready' ? ` · ${prettyStatus(status)}` : ''}</option>
                })}
              </select>
              <p className="mt-1 text-[10px] leading-4 text-zinc-600">{activeRows.find((row) => row.id === chosen)?.desc || help}</p>
            </div>
          })}
        </div>}

        <div aria-live="polite" className="rounded-lg border border-white/10 bg-surface/60 p-3">
          <div className="flex items-center gap-2 text-xs font-semibold text-zinc-200"><Cpu size={14} className="text-violet-200" /> Proposed stack {busy && <span className="font-normal text-zinc-500">· checking compatibility…</span>}</div>
          {resolution?.summary && <p className="mt-2 text-xs leading-5 text-zinc-300">{resolution.summary}</p>}
          {resolution?.stack && <div className="mt-2 flex flex-wrap gap-1.5">
            {selectedFields.map((field) => <span key={field} className="rounded-md border border-white/10 bg-white/[0.03] px-2 py-1 text-[10px] text-zinc-400">{effectiveLabel(field, resolution.stack?.[field] ?? "")}</span>)}
          </div>}
          {resolution?.blocking?.map((item) => <p key={item} className="mt-2 text-xs text-red-300">{item}</p>)}
          {resolution?.errors?.map((item, i) => <p key={`${item.field}-${i}`} className="mt-2 text-xs text-red-300">{item.msg}</p>)}
          {resolution?.pending?.map((item) => <p key={item} className="mt-2 text-xs text-amber-300">Not fully generated yet: {item}</p>)}
          {resolution?.warnings?.map((item, i) => <p key={`${item.field}-${i}`} className="mt-2 text-xs text-amber-300">{item.msg}</p>)}
          {resolution?.ok && !resolution.pending?.length && !resolution.warnings?.length && <p className="mt-2 flex items-center gap-1 text-xs text-emerald-300"><Sparkles size={13} /> No known stack compatibility gaps.</p>}
          {error && <p role="alert" className="mt-2 text-xs text-red-300">Could not verify selection: {error}</p>}
          {!resolution && !error && <p className="mt-2 text-xs text-zinc-500">Describe the website above to preview technology decisions.</p>}
        </div>
        <p className="text-[10px] leading-4 text-zinc-600">“Ready” describes code-generation support in this build. Planned options remain visible for transparency but may produce frontend-only output or require a later phase; no unsupported integration is reported as working.</p>
      </div>}
    </section>
  )
}

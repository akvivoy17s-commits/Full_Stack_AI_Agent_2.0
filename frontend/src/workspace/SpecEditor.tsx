import { useEffect, useRef, useState, type ReactNode } from 'react'
import { Plus, RotateCcw, Trash2 } from 'lucide-react'
import { api, type AppSpec, type SpecEntity, type SpecField, type SpecOverrides, type SpecPage, type StackDraft } from '../services/api'

const TYPES = ['string', 'text', 'int', 'float', 'bool', 'datetime', 'email', 'url', 'ref', 'enum']
const FIELD_NAME = /^[a-z][a-z0-9_]{0,30}$/
const ENUM_VALUES = /^[a-z0-9_|]{1,80}$/
const SLUG = /^[a-z][a-z0-9-]{0,30}$/
const ENTITY = /^[A-Z][A-Za-z0-9]{1,30}$/

interface Row { name: string; type: string; target: string; required: boolean; unique: boolean }
const toRow = (f: SpecField): Row => ({ name: f.name, type: f.type, target: f.type === 'ref' ? f.ref ?? '' : (f.values ?? []).join('|'), required: f.required, unique: f.unique })
const token = (r: Row) => `${r.name}:${r.type === 'ref' ? `ref(${r.target})` : r.type === 'enum' ? `enum(${r.target})` : r.type}${r.required ? '!' : ''}${r.unique ? '@' : ''}`

function rowsError(rows: Row[], names: string[]): string {
  if (!rows.length || rows.length > 25) return 'An entity needs between 1 and 25 fields.'
  const seen = new Set<string>()
  for (const r of rows) {
    if (!FIELD_NAME.test(r.name)) return `Field name "${r.name}" must start with a lowercase letter and use only lowercase letters, digits or underscores.`
    if (seen.has(r.name)) return `Field "${r.name}" is used twice.`
    seen.add(r.name)
    if (r.type === 'ref' && !names.includes(r.target)) return `Choose which entity "${r.name}" refers to.`
    if (r.type === 'enum' && !ENUM_VALUES.test(r.target)) return `Enter the values for "${r.name}" as lowercase words separated by |.`
  }
  return ''
}

const Box = ({ title, children }: { title: string; children: ReactNode }) => (
  <section className="rounded-xl border border-white/10 p-3"><h3 className="label">{title}</h3>{children}</section>
)
const Err = ({ msg }: { msg: string }) => (msg ? <p role="alert" className="mt-1 text-xs text-amber-300">{msg}</p> : null)

function EntityCard({ entity, names, onCommit, onDrop }: { entity: SpecEntity; names: string[]; onCommit: (name: string, tokens: string[]) => void; onDrop: (name: string) => void }) {
  const locked = entity.name === 'User'
  const [rows, setRows] = useState<Row[]>(() => entity.fields.map(toRow))
  const err = rowsError(rows, names)
  const update = (next: Row[]) => { setRows(next); if (!rowsError(next, names)) onCommit(entity.name, next.map(token)) }
  const edit = (i: number, patch: Partial<Row>) => update(rows.map((r, k) => (k === i ? { ...r, ...patch } : r)))
  return (
    <div className="rounded-lg border border-white/10 bg-black/20 p-2">
      <div className="mb-2 flex items-center gap-2 text-sm">
        <b className="text-zinc-100">{entity.name}</b>
        <span className="text-xs text-zinc-500">read: {entity.read} · write: {entity.write}</span>
        {!locked && <button type="button" className="btn-ghost ml-auto !px-2 !py-1" aria-label={`Remove ${entity.name}`} onClick={() => onDrop(entity.name)}><Trash2 size={13} /></button>}
      </div>
      {locked ? <p className="text-xs text-zinc-500">{rows.map((r) => r.name).join(', ')} (managed by authentication)</p> : (
        <div className="space-y-1.5">
          {rows.map((r, i) => (
            <div key={i} className="flex flex-wrap items-center gap-1.5">
              <input aria-label="Field name" className="field !w-32 !py-1" value={r.name} onChange={(e) => edit(i, { name: e.target.value })} />
              <select aria-label="Field type" className="field !w-24 !py-1" value={r.type} onChange={(e) => edit(i, { type: e.target.value, target: e.target.value === 'ref' ? names[0] ?? '' : '' })}>
                {TYPES.map((t) => <option key={t}>{t}</option>)}
              </select>
              {r.type === 'ref' && <select aria-label="Refers to" className="field !w-28 !py-1" value={r.target} onChange={(e) => edit(i, { target: e.target.value })}>{names.map((n) => <option key={n}>{n}</option>)}</select>}
              {r.type === 'enum' && <input aria-label="Allowed values" placeholder="a|b|c" className="field !w-28 !py-1" value={r.target} onChange={(e) => edit(i, { target: e.target.value })} />}
              <label className="flex items-center gap-1 text-xs text-zinc-400"><input type="checkbox" checked={r.required} onChange={(e) => edit(i, { required: e.target.checked })} />required</label>
              <label className="flex items-center gap-1 text-xs text-zinc-400"><input type="checkbox" checked={r.unique} onChange={(e) => edit(i, { unique: e.target.checked })} />unique</label>
              <button type="button" className="ml-auto rounded p-1 text-zinc-500 hover:text-red-300" aria-label={`Remove field ${r.name}`} onClick={() => update(rows.filter((_, k) => k !== i))}><Trash2 size={13} /></button>
            </div>
          ))}
          <button type="button" className="btn-ghost !px-2 !py-1 text-xs" onClick={() => setRows([...rows, { name: '', type: 'string', target: '', required: false, unique: false }])}><Plus size={13} /> Add field</button>
        </div>
      )}
      <Err msg={locked ? '' : err} />
    </div>
  )
}

function PagesEditor({ pages, onCommit }: { pages: SpecPage[]; onCommit: (p: SpecPage[]) => void }) {
  const [rows, setRows] = useState<SpecPage[]>(pages)
  const slugs = rows.map((r) => r.slug)
  const err = !rows.length || rows.length > 20 ? 'Keep between 1 and 20 pages.'
    : rows.find((r) => !SLUG.test(r.slug)) ? 'Page addresses use lowercase letters, digits and dashes, starting with a letter.'
    : new Set(slugs).size !== slugs.length ? 'Each page needs its own address.'
    : rows.find((r) => !r.title.trim() || r.title.length > 60) ? 'Every page needs a title of up to 60 characters.' : ''
  const update = (next: SpecPage[]) => {
    setRows(next)
    const ok = next.length >= 1 && next.length <= 20 && next.every((r) => SLUG.test(r.slug) && r.title.trim() && r.title.length <= 60) && new Set(next.map((r) => r.slug)).size === next.length
    if (ok) onCommit(next.map((r) => ({ ...r, title: r.title.trim() })))
  }
  const edit = (i: number, patch: Partial<SpecPage>) => update(rows.map((r, k) => (k === i ? { ...r, ...patch } : r)))
  return (
    <div className="space-y-1.5">
      {rows.map((r, i) => (
        <div key={i} className="flex flex-wrap items-center gap-1.5">
          <input aria-label="Page title" className="field !w-40 !py-1" value={r.title} onChange={(e) => edit(i, { title: e.target.value })} />
          <input aria-label="Page address" className="field !w-32 !py-1" value={r.slug} onChange={(e) => edit(i, { slug: e.target.value })} />
          <label className="flex items-center gap-1 text-xs text-zinc-400"><input type="checkbox" checked={r.auth} onChange={(e) => edit(i, { auth: e.target.checked })} />sign-in required</label>
          <button type="button" className="ml-auto rounded p-1 text-zinc-500 hover:text-red-300" aria-label={`Remove page ${r.title}`} onClick={() => update(rows.filter((_, k) => k !== i))}><Trash2 size={13} /></button>
        </div>
      ))}
      <button type="button" className="btn-ghost !px-2 !py-1 text-xs" onClick={() => setRows([...rows, { slug: '', title: '', auth: false }])}><Plus size={13} /> Add page</button>
      <Err msg={err} />
    </div>
  )
}

function FeaturesEditor({ features, onCommit }: { features: string[]; onCommit: (f: string[]) => void }) {
  const [text, setText] = useState(features.join('\n'))
  const list = text.split('\n').map((s) => s.trim()).filter(Boolean)
  const err = list.length > 30 || list.some((s) => s.length < 2 || s.length > 120) ? 'Use up to 30 features of 2 to 120 characters, one per line.' : ''
  return (
    <>
      <textarea aria-label="Features, one per line" rows={Math.min(8, Math.max(3, list.length + 1))} className="field resize-y" value={text}
        onChange={(e) => setText(e.target.value)} onBlur={() => { if (!err && list.join('\n') !== features.join('\n')) onCommit(list) }} />
      <Err msg={err} />
    </>
  )
}

interface Props {
  brief: string; draft: StackDraft; ov: SpecOverrides; resetKey: number
  onOv: (next: SpecOverrides) => void; onSpec: (spec: AppSpec | null) => void; onReset: () => void
}

export default function SpecEditor({ brief, draft, ov, resetKey, onOv, onSpec, onReset }: Props) {
  const [spec, setSpec] = useState<AppSpec | null>(null)
  const [err, setErr] = useState('')
  const [busy, setBusy] = useState(true)
  const [newEntity, setNewEntity] = useState('')
  const seq = useRef(0)

  useEffect(() => {
    const id = ++seq.current
    setBusy(true)
    const t = setTimeout(() => {
      api.specPreview(brief, draft, ov).then((r) => {
        if (id !== seq.current) return
        if (!r.ok || !r.spec) { setErr(r.resolution.errors.map((e) => e.msg).join('; ') || 'This technology selection cannot be previewed.'); onSpec(null) }
        else { setErr(''); setSpec(r.spec); onSpec(r.spec) }
      }).catch((e) => { if (id === seq.current) { setErr((e as Error).message); onSpec(null) } })
        .finally(() => { if (id === seq.current) setBusy(false) })
    }, 350)
    return () => clearTimeout(t)
  }, [brief, draft, ov, onSpec])

  const names = spec?.data.entities.map((e) => e.name) ?? []
  const setEntity = (name: string, toks: string[]) => onOv({ ...ov, entities: { ...ov.entities, [name]: toks }, drop_entities: (ov.drop_entities ?? []).filter((n) => n !== name) })
  const drop = (name: string) => onOv({
    ...ov, entities: Object.fromEntries(Object.entries(ov.entities ?? {}).filter(([n]) => n !== name)), drop_entities: [...new Set([...(ov.drop_entities ?? []), name])],
  })
  const add = () => { if (ENTITY.test(newEntity) && !names.includes(newEntity)) { setEntity(newEntity, ['name:string!']); setNewEntity('') } }
  const customized = Object.keys(ov).length > 0

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2 text-xs text-zinc-500" role="status">
        {spec && <span>{spec.kind} · {spec.pages.length} pages · {spec.data.entities.length} entities · {spec.api.routes.length} API routes</span>}
        {busy && <span>Updating…</span>}
        {customized && <button type="button" className="btn-ghost ml-auto !px-2 !py-1 text-xs" onClick={onReset}><RotateCcw size={13} /> Reset edits</button>}
      </div>
      {err && <p role="alert" className="rounded-lg border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-300">{err}</p>}
      {spec && (
        <>
          <Box title="Pages"><PagesEditor key={`p${resetKey}`} pages={spec.pages} onCommit={(pages) => onOv({ ...ov, pages })} /></Box>
          <Box title="Features"><FeaturesEditor key={`f${resetKey}`} features={spec.features} onCommit={(features) => onOv({ ...ov, features })} /></Box>
          <Box title="Data model">
            {!spec.data.enabled ? <p className="text-xs text-zinc-500">No database is selected, so there is no data model to edit. Pick a database in the Technology step to add one.</p> : (
              <div className="space-y-2">
                {spec.data.entities.map((e) => <EntityCard key={`${resetKey}-${e.name}`} entity={e} names={names} onCommit={setEntity} onDrop={drop} />)}
                <div className="flex gap-2">
                  <input aria-label="New entity name" className="field !w-44 !py-1" placeholder="New entity, e.g. Review" value={newEntity} onChange={(e) => setNewEntity(e.target.value)}
                    onKeyDown={(e) => { if (e.key === 'Enter') add() }} />
                  <button type="button" className="btn-ghost !px-2 !py-1 text-xs" disabled={!ENTITY.test(newEntity) || names.includes(newEntity)} onClick={add}><Plus size={13} /> Add entity</button>
                </div>
              </div>
            )}
          </Box>
          {(spec.gaps.length > 0 || spec.open_questions.length > 0 || spec.assumptions.length > 0) && (
            <details className="rounded-xl border border-white/10 p-3 text-xs text-zinc-400">
              <summary className="cursor-pointer text-zinc-300">Assumptions and open questions</summary>
              <ul className="mt-2 list-disc space-y-1 pl-4">
                {spec.gaps.map((g) => <li key={g} className="text-amber-300">{g}</li>)}
                {spec.open_questions.map((q) => <li key={q.id}>{q.question}</li>)}
                {spec.assumptions.map((a) => <li key={a}>{a}</li>)}
              </ul>
            </details>
          )}
        </>
      )}
    </div>
  )
}

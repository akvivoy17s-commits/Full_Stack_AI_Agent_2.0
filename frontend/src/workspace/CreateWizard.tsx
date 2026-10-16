import { useState } from 'react'
import { ArrowLeft, ArrowRight, Check, Loader2, Rocket, Sparkles } from 'lucide-react'
import type { AppSpec, Framework, SpecOverrides, StackDraft, StackResolution } from '../services/api'
import TechnologyConfig, { savedStackDraft } from './TechnologyConfig'
import SpecEditor from './SpecEditor'
import { loadPresets, removePreset, savePreset, type Preset } from './presets'
import { EXAMPLES, MOTION, STACK_LABELS, STYLES, composeBrief } from './briefing'

const DRAFT_KEY = 'fullstack-agent-brief-draft-v1'
const STEPS = ['Describe', 'Technology', 'Data & pages', 'Review'] as const
const LAST = STEPS.length - 1
const MIN_BRIEF = 5

const loadDraft = () => { try { return localStorage.getItem(DRAFT_KEY) ?? '' } catch { return '' } }
const saveDraft = (v: string) => { try { if (v) localStorage.setItem(DRAFT_KEY, v); else localStorage.removeItem(DRAFT_KEY) } catch { /* storage unavailable */ } }

interface Props {
  onCreate: (brief: string, framework: Framework, stack: StackDraft, overrides?: SpecOverrides) => Promise<void>
  onAutoBuild: (prompt: string) => Promise<void>
}

export default function CreateWizard({ onCreate, onAutoBuild }: Props) {
  const [advanced, setAdvanced] = useState(false)
  const [step, setStep] = useState(0)
  const [brief, setBrief] = useState(loadDraft)
  const [style, setStyle] = useState(STYLES[0])
  const [motion, setMotion] = useState<string>('balanced')
  const [draft, setDraft] = useState<StackDraft>(() => savedStackDraft())
  const [res, setRes] = useState<StackResolution | null>(null)
  const [ov, setOv] = useState<SpecOverrides>({})
  const [resetKey, setResetKey] = useState(0)
  const [spec, setSpec] = useState<AppSpec | null>(null)
  const [presets, setPresets] = useState<Preset[]>(loadPresets)
  const [presetName, setPresetName] = useState('')
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState('')

  const frontend = draft.mode === 'automatic' ? res?.stack?.frontend : draft.prefs.frontend
  const framework: Framework = frontend === 'react' ? 'react' : 'html'
  const briefOk = brief.trim().length >= MIN_BRIEF
  const blocked = Boolean(res?.blocking?.length)
  const stackOk = Boolean(res && res.ok && !blocked)
  const canNext = step === 0 ? briefOk : step === 1 ? stackOk : step === 2 ? Boolean(spec) : false
  const hint = step === 0 && !briefOk ? `Describe your project in at least ${MIN_BRIEF} characters.`
    : step === 1 && !res ? 'Checking the technology combination…'
    : step === 1 && !stackOk ? 'Resolve the issues above to continue.'
    : step === 2 && !spec ? 'Waiting for a valid data model…' : ''

  const setBriefText = (v: string) => { setBrief(v); saveDraft(v) }
  const go = (n: number) => { setErr(''); if (n === 2) setSpec(null); setStep(n) }
  const reset = () => { setOv({}); setResetKey((k) => k + 1) }
  const applyPreset = (name: string) => {
    const p = presets.find((x) => x.name === name)
    if (!p) return
    setBriefText(p.brief); setStyle(p.style); setMotion(p.motion); setDraft(p.draft); setOv(p.ov); setResetKey((k) => k + 1)
  }
  const saveCurrent = () => {
    const name = presetName.trim().slice(0, 40)
    if (name) { setPresets(savePreset({ name, brief, style, motion, draft, ov })); setPresetName('') }
  }

  const create = async () => {
    setBusy(true); setErr('')
    try {
      await onCreate(composeBrief(brief, style, motion), framework, draft, Object.keys(ov).length ? ov : undefined)
      saveDraft('')
    } catch (e) { setErr((e as Error).message || 'Could not start project generation.') }
    finally { setBusy(false) }
  }

  const stackRows = STACK_LABELS.filter(([k]) => res?.stack?.[k] && res.stack[k] !== 'none')

  const createAutomatically = async () => {
    setBusy(true); setErr('')
    try {
      await onAutoBuild(brief.trim())
      saveDraft('')
    } catch (e) { setErr((e as Error).message || 'Could not start the autonomous build.') }
    finally { setBusy(false) }
  }

  if (!advanced) return (
    <div className="space-y-4">
      <section className="rounded-2xl border border-accent/30 bg-gradient-to-br from-accent/10 via-surface to-white/[0.02] p-4 sm:p-5">
        <div className="mb-4 flex items-center gap-3">
          <span className="grid h-10 w-10 place-items-center rounded-xl border border-accent/30 bg-accent/15 text-accent"><Sparkles size={19} /></span>
          <div><p className="text-sm font-semibold text-white">Autopilot builder</p><p className="mt-1 text-xs text-zinc-400">One prompt. The agent chooses a supported stack, generates, builds and checks it.</p></div>
        </div>
        <label className="label" htmlFor="autopilot-prompt">Describe the complete website or web app</label>
        <textarea id="autopilot-prompt" rows={7} maxLength={6000} className="field resize-y" value={brief} autoFocus
          onChange={(e) => setBriefText(e.target.value)}
          onKeyDown={(e) => { if ((e.ctrlKey || e.metaKey) && e.key === 'Enter' && briefOk && !busy) void createAutomatically() }}
          placeholder="Example: Build a polished todo app with projects, priorities, due dates, search, dark mode, add/edit/delete, and saved tasks. Make it responsive and verify the production build." />
        <div className="mt-1 flex items-center justify-between text-xs text-zinc-500"><span>Ctrl + Enter to build</span><span>{brief.length}/6000</span></div>
        {!brief.trim() && <div className="mt-3 flex flex-wrap gap-2" aria-label="Prompt examples">{EXAMPLES.map((x) => <button key={x.label} type="button" className="chip border-white/15 text-zinc-300 hover:border-white/40" onClick={() => setBriefText(x.text)}>{x.label}</button>)}</div>}
      </section>
      <div className="rounded-xl border border-white/10 bg-white/[0.02] p-3 text-xs leading-5 text-zinc-400">
        <p className="font-medium text-zinc-200">What happens automatically</p>
        <p className="mt-1">Requirement and data-model inference · compatible stack selection · source generation · production build/type-check · bounded repair attempts · verification report.</p>
        <p className="mt-2 text-amber-200/90">The agent cannot guarantee zero bugs. External accounts, API secrets, paid services and production deployment still require real credentials and final review.</p>
      </div>
      {err && <p role="alert" className="rounded-lg border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-300">{err}</p>}
      <div className="flex flex-wrap items-center gap-2">
        <button type="button" className="btn-primary" disabled={busy || !briefOk} onClick={() => void createAutomatically()}>{busy ? <Loader2 size={16} className="animate-spin" /> : <Rocket size={16} />} Build from prompt</button>
        <button type="button" className="btn-ghost" disabled={busy} onClick={() => setAdvanced(true)}>Advanced configuration <ArrowRight size={14} /></button>
        {!briefOk && <span className="text-xs text-zinc-500" role="status">Enter at least {MIN_BRIEF} characters.</span>}
      </div>
    </div>
  )

  return (
    <div className="space-y-4">
      <button type="button" className="btn-ghost !px-2 !py-1 text-xs" onClick={() => setAdvanced(false)}><ArrowLeft size={13} /> Back to prompt-only build</button>
      <ol className="flex gap-2" aria-label="Project creation steps">
        {STEPS.map((s, i) => (
          <li key={s} className="flex-1" aria-current={i === step ? 'step' : undefined}>
            <button type="button" disabled={i > step || busy} onClick={() => go(i)}
              className={`flex w-full min-w-0 items-center gap-2 rounded-lg border px-2 py-2 text-left text-xs transition sm:px-3 sm:text-sm ${i === step ? 'border-accent/60 bg-accent/10 text-white' : i < step ? 'border-white/15 text-zinc-300 hover:border-white/30' : 'border-white/5 text-zinc-600'}`}>
              <span className={`grid h-5 w-5 shrink-0 place-items-center rounded-full text-[11px] ${i < step ? 'bg-accent text-white' : 'border border-current'}`}>{i < step ? <Check size={12} /> : i + 1}</span>
              <span className="truncate">{s}</span>
            </button>
          </li>
        ))}
      </ol>

      {step === 0 && (
        <div className="space-y-3">
          <div>
            <label className="label" htmlFor="brief">What should the agent build?</label>
            <textarea id="brief" rows={6} maxLength={1700} className="field resize-y" value={brief} autoFocus
              onChange={(e) => setBriefText(e.target.value)}
              onKeyDown={(e) => { if ((e.ctrlKey || e.metaKey) && e.key === 'Enter' && briefOk) go(1) }}
              placeholder="Describe the product, its pages, who uses it and what data it stores." />
            <div className="mt-1 flex items-center justify-between text-xs text-zinc-500">
              <span>Ctrl + Enter to continue</span><span>{brief.length}/1700</span>
            </div>
          </div>
          {presets.length > 0 && (
            <div className="flex items-center gap-2">
              <label className="label !mb-0" htmlFor="preset">Saved preset</label>
              <select id="preset" className="field !w-auto !py-1" value="" onChange={(e) => applyPreset(e.target.value)}>
                <option value="">Choose…</option>{presets.map((p) => <option key={p.name}>{p.name}</option>)}
              </select>
            </div>
          )}
          {!brief.trim() && (
            <div className="flex flex-wrap gap-2" aria-label="Example briefs">
              {EXAMPLES.map((x) => <button key={x.label} type="button" className="chip border-white/15 text-zinc-300 hover:border-white/40" onClick={() => setBriefText(x.text)}>{x.label}</button>)}
            </div>
          )}
          <div className="grid gap-3 sm:grid-cols-3">
            <div><label className="label" htmlFor="style">Design style</label>
              <select id="style" className="field" value={style} onChange={(e) => setStyle(e.target.value)}>{STYLES.map((s) => <option key={s}>{s}</option>)}</select></div>
            <div><label className="label" htmlFor="motion">Animation intensity</label>
              <select id="motion" className="field" value={motion} onChange={(e) => setMotion(e.target.value)}>{MOTION.map((m) => <option key={m}>{m}</option>)}</select></div>
            <div><label className="label" htmlFor="fw">Frontend</label>
              <select id="fw" className="field" value={framework} onChange={(e) => {
                const next = e.target.value as Framework
                setDraft((c) => ({ mode: 'hybrid', prefs: { ...c.prefs, frontend: next, frontend_lang: next === 'react' ? 'ts' : 'js' } }))
              }}>
                <option value="html">HTML / CSS / JS</option>
                <option value="react">React + TypeScript</option>
              </select></div>
          </div>
        </div>
      )}

      <div className={step === 1 ? '' : 'hidden'}>
        {briefOk && <TechnologyConfig brief={composeBrief(brief, style, motion)} value={draft} onChange={setDraft} onResolution={setRes} />}
      </div>

      {step === 2 && (
        <SpecEditor brief={composeBrief(brief, style, motion)} draft={draft} ov={ov} resetKey={resetKey} onOv={setOv} onSpec={setSpec} onReset={reset} />
      )}

      {step === 3 && (
        <div className="space-y-3">
          <section className="rounded-xl border border-white/10 p-3">
            <h3 className="label">Brief</h3>
            <p className="max-h-28 overflow-auto whitespace-pre-wrap text-sm text-zinc-300">{brief.trim()}</p>
            <p className="mt-2 text-xs text-zinc-500">{style} · {motion} animation</p>
          </section>
          <section className="rounded-xl border border-white/10 p-3">
            <h3 className="label">Technology ({draft.mode})</h3>
            <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-1 text-sm">
              {stackRows.map(([k, l]) => <div key={k} className="contents"><dt className="text-zinc-500">{l}</dt><dd className="text-zinc-200">{res?.stack?.[k]}</dd></div>)}
            </dl>
            {res?.summary && <p className="mt-2 text-xs text-zinc-500">{res.summary}</p>}
          </section>
          {spec && (
            <section className="rounded-xl border border-white/10 p-3">
              <h3 className="label">Data and pages{Object.keys(ov).length ? ' (customized)' : ''}</h3>
              <p className="text-sm text-zinc-300">{spec.pages.length} pages · {spec.data.enabled ? `${spec.data.entities.map((e) => e.name).join(', ')} · ${spec.api.routes.length} API routes` : 'no database'}</p>
            </section>
          )}
          {!!res?.warnings.length && (
            <ul className="space-y-1 rounded-xl border border-amber-500/20 bg-amber-500/10 p-3 text-xs text-amber-200" aria-label="Warnings">
              {res.warnings.map((w, i) => <li key={i}>{w.msg}</li>)}
            </ul>
          )}
          <div className="flex flex-wrap items-center gap-2">
            <input aria-label="Preset name" className="field !w-44 !py-1" placeholder="Save these choices as…" value={presetName} maxLength={40} onChange={(e) => setPresetName(e.target.value)} />
            <button type="button" className="btn-ghost !px-2 !py-1 text-xs" disabled={!presetName.trim()} onClick={saveCurrent}>Save preset</button>
            {presets.map((p) => <button key={p.name} type="button" className="chip border-white/15 text-zinc-400 hover:text-red-300" aria-label={`Delete preset ${p.name}`} onClick={() => setPresets(removePreset(p.name))}>{p.name} ✕</button>)}
          </div>
          <p className="text-xs text-zinc-500">Creating saves the project and starts generation. You can cancel from the Build panel and edit any section afterwards.</p>
        </div>
      )}

      {(err) && <p role="alert" className="rounded-lg border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-300">{err}</p>}

      <div className="flex items-center gap-2">
        {step > 0 && <button type="button" className="btn-ghost" disabled={busy} onClick={() => go(step - 1)}><ArrowLeft size={15} /> Back</button>}
        {step < LAST
          ? <button type="button" className="btn-primary" disabled={!canNext} onClick={() => go(step + 1)}>Continue <ArrowRight size={15} /></button>
          : <button type="button" className="btn-primary" disabled={busy || !stackOk || !briefOk || !spec} onClick={create}>
              {busy ? <Loader2 size={16} className="animate-spin" /> : <Rocket size={16} />} Create and generate</button>}
        {hint && <span className="text-xs text-zinc-500" role="status">{hint}</span>}
      </div>
    </div>
  )
}

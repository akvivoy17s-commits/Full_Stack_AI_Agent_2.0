import { useState } from 'react'
import { Rocket, ShieldCheck, RefreshCw, RotateCcw, Pencil, Square, FlaskConical, Wrench, Bug, CheckCircle2 } from 'lucide-react'
import { api, type DebugResult, type Framework, type ProjectState, type SpecOverrides, type StackDraft, type TaskRequest } from '../services/api'
import CreateWizard from './CreateWizard'
import { EDIT_REPAIR_PROMPT_MAX_CHARS } from './promptLimits'

export { STYLES, MOTION, composeBrief } from './briefing'

interface Props {
  project: ProjectState | null
  running: boolean
  error: string
  onCreate: (brief: string, framework: Framework, stack: StackDraft, overrides?: SpecOverrides) => Promise<void>
  onAutoBuild: (prompt: string) => Promise<void>
  onTask: (req: TaskRequest) => void
  onCancel: () => void
}

export default function PromptPanel({ project, running, error, onCreate, onAutoBuild, onTask, onCancel }: Props) {
  const [section, setSection] = useState('')
  const [instr, setInstr] = useState('')
  const [debugError, setDebugError] = useState('')
  const [debugResult, setDebugResult] = useState<DebugResult | null>(null)
  const [debugBusy, setDebugBusy] = useState(false)
  const [debugFailure, setDebugFailure] = useState('')
  const sections = project?.plan?.sections ?? []
  const sel = section || sections[0] || ''

  return (
    <div className="space-y-4 p-4">
      {!project ? (
        <CreateWizard onCreate={onCreate} onAutoBuild={onAutoBuild} />
      ) : (
        <>
          <div>
            <p className="label">Brief</p>
            <p className="max-h-24 overflow-auto whitespace-pre-wrap rounded-lg border border-white/10 bg-black/30 p-3 text-sm text-zinc-300">{project.brief}</p>
            <p className="mt-2 text-xs text-zinc-500">
              Phase: <b className="text-zinc-300">{project.phase}</b> · sections {project.sections_done.length}/{sections.length || '?'} · repairs {project.repair_count} · tokens {project.usage.in}/{project.usage.out}
            </p>
            {project.stack_config?.stack && <p className="mt-2 rounded-lg border border-white/10 bg-black/20 px-3 py-2 text-xs text-zinc-400">
              Selected stack: <span className="text-zinc-200">{[project.stack_config.stack.frontend, project.stack_config.stack.backend, project.stack_config.stack.database, project.stack_config.stack.auth].filter((x) => x && x !== 'none').join(' · ')}</span>
            </p>}
            {project.stack_config?.autopilot?.prompt_only && (
              <details open className="mt-2 rounded-lg border border-accent/30 bg-accent/5 px-3 py-2 text-xs text-zinc-300">
                <summary className="cursor-pointer font-medium text-zinc-100">Autopilot decisions{project.stack_config.autopilot.assumptions?.length ? ` (${project.stack_config.autopilot.assumptions.length})` : ''}</summary>
                {project.stack_config.autopilot.assumptions?.length ? (
                  <ul className="mt-2 list-disc space-y-1 pl-4 text-zinc-400">
                    {project.stack_config.autopilot.assumptions.map((a) => <li key={a}>{a}</li>)}
                  </ul>
                ) : <p className="mt-2 text-zinc-400">No assumptions needed: the prompt mapped directly to a supported stack.</p>}
                <p className="mt-2 text-zinc-500">Review these before relying on the result. Use Verify &amp; repair to re-run checks.</p>
              </details>
            )}
          </div>
          <div className="flex flex-wrap gap-2">
            <button className="btn-primary" disabled={running} onClick={() => onTask({ kind: 'generate' })}><Rocket size={16} /> {project.sections_done.length ? 'Resume generation' : 'Generate'}</button>
            <button className="btn-ghost" disabled={running} onClick={() => onTask({ kind: 'verify', repair: true })}><ShieldCheck size={16} /> Verify &amp; repair</button>
            <button className="btn-ghost" disabled={running} onClick={() => onTask({ kind: 'verify', repair: false })}><RefreshCw size={16} /> Verify only</button>
            <button className="btn-ghost" disabled={running} title="Build + Playwright + accessibility checks, no code changes" onClick={() => onTask({ kind: 'test' })}><FlaskConical size={16} /> Run browser tests</button>
            <button className="btn-ghost" disabled={running} title="Run backend build/test scripts only when dependencies are already installed. No packages are installed automatically." onClick={() => onTask({ kind: 'test', deep: true })}><Wrench size={16} /> Deep full-stack check</button>
            <button className="btn-ghost" disabled={running}
              onClick={() => confirm('Regenerate every section? Existing generated sections are replaced (a checkpoint is saved first).') && onTask({ kind: 'generate', force: true, confirm: true })}>
              <RotateCcw size={16} /> Regenerate all
            </button>
            {running && <button className="btn-ghost border-red-500/40 text-red-300" onClick={onCancel}><Square size={14} /> Cancel</button>}
          </div>
          <div className="rounded-xl border border-sky-500/20 bg-sky-500/[0.035] p-3">
            <div className="mb-2 flex items-center gap-2"><Bug size={15} className="text-sky-300" /><p className="label !mb-0 text-sky-200">Project debugger</p></div>
            <p className="mb-2 text-xs leading-5 text-zinc-500">Paste a browser console error, build output, stack trace, or API failure. The debugger scans this project, proposes minimal patches, saves a checkpoint before applying fixes, and reports what was actually checked.</p>
            <label className="sr-only" htmlFor="debug-error-input">Error details</label>
            <textarea id="debug-error-input" className="field min-h-24 resize-y font-mono text-xs" value={debugError} onChange={(e) => setDebugError(e.target.value)} placeholder={'Paste the full error here…\nExample: src/App.tsx:23: Property ...'} disabled={debugBusy || running} />
            <div className="mt-2 flex flex-wrap gap-2">
              <button className="btn-ghost !px-3 !py-1.5" disabled={!debugError.trim() || debugError.trim().length < 3 || debugBusy || running} onClick={async () => {
                setDebugBusy(true); setDebugFailure(''); setDebugResult(null)
                try { setDebugResult(await api.debugProject(project.project_id, debugError.trim(), false)) }
                catch (e) { setDebugFailure((e as Error).message) }
                finally { setDebugBusy(false) }
              }}><Bug size={14} />Analyze only</button>
              <button className="btn-primary !px-3 !py-1.5" disabled={!debugError.trim() || debugError.trim().length < 3 || debugBusy || running} onClick={async () => {
                setDebugBusy(true); setDebugFailure(''); setDebugResult(null)
                try { const result = await api.debugProject(project.project_id, debugError.trim(), true); setDebugResult(result); if (result.applied.length) window.dispatchEvent(new CustomEvent('agent-project-files-changed')) }
                catch (e) { setDebugFailure((e as Error).message) }
                finally { setDebugBusy(false) }
              }}><Wrench size={14} />{debugBusy ? 'Analyzing…' : 'Analyze & fix'}</button>
            </div>
            {debugFailure && <p role="alert" className="mt-2 text-xs text-amber-300">{debugFailure}</p>}
            {debugResult && <div className="mt-3 space-y-2 rounded-lg border border-white/10 bg-black/20 p-3 text-xs">
              <p className="whitespace-pre-wrap text-zinc-200">{debugResult.summary}</p>
              <p className="text-zinc-500">Scanned {debugResult.files_scanned} files · context: {debugResult.files_in_context.length} file(s) · tokens {debugResult.usage.in}/{debugResult.usage.out}</p>
              {debugResult.diagnostics.length > 0 && <div><p className="mb-1 font-semibold text-zinc-400">Findings</p>{debugResult.diagnostics.map((d, i) => <p key={`${d.file}-${d.line}-${i}`} className="mb-1 break-words text-zinc-300"><span className={d.severity === 'error' ? 'text-rose-300' : d.severity === 'warning' ? 'text-amber-300' : 'text-sky-300'}>{d.severity.toUpperCase()}</span>{d.file ? ` · ${d.file}${d.line ? `:${d.line}` : ''}` : ''} — {d.message}</p>)}</div>}
              {debugResult.applied.length > 0 && <div><p className="mb-1 font-semibold text-emerald-300">Applied patches</p>{debugResult.applied.map((p) => <p key={p.file} className="break-all text-zinc-300">{p.file} — {p.reason}</p>)}</div>}
              {debugResult.rejected.length > 0 && <div><p className="mb-1 font-semibold text-amber-300">Not applied</p>{debugResult.rejected.map((r, i) => <p key={`${r}-${i}`} className="break-words text-zinc-400">{r}</p>)}</div>}
              <div><p className="mb-1 font-semibold text-zinc-400">Verification</p>{debugResult.verification.map((v, i) => <p key={`${v}-${i}`} className="flex gap-1 break-words text-zinc-400"><CheckCircle2 size={12} className="mt-0.5 shrink-0 text-sky-300" />{v}</p>)}</div>
            </div>}
          </div>
          <div className="rounded-xl border border-white/10 p-3">
            <p className="label">Edit one section</p>
            <div className="flex min-w-0 flex-col gap-2">
              <select aria-label="Section" className="field w-full min-w-0" value={sel} onChange={(e) => setSection(e.target.value)}>
                {sections.length === 0 && <option value="">no sections yet</option>}
                {sections.map((s) => <option key={s}>{s}</option>)}
              </select>
              <textarea aria-label="Edit / repair instruction" rows={6} maxLength={EDIT_REPAIR_PROMPT_MAX_CHARS}
                className="field min-h-36 w-full min-w-0 resize-y whitespace-pre-wrap" value={instr} onChange={(e) => setInstr(e.target.value)}
                placeholder="Describe the code change or repair in detail…" />
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="text-xs text-zinc-500">{instr.length.toLocaleString()}/{EDIT_REPAIR_PROMPT_MAX_CHARS.toLocaleString()}</div>
                <button className="btn-ghost self-start" disabled={running || !sel || instr.trim().length < 3}
                  onClick={() => { onTask({ kind: 'edit', section: sel, instruction: instr.trim() }); setInstr('') }}><Pencil size={15} /> Apply</button>
              </div>
            </div>
          </div>
        </>
      )}
      {error && <p role="alert" className="rounded-lg border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-300">{error}</p>}
    </div>
  )
}

import { useState } from 'react'
import { Rocket, ShieldCheck, RefreshCw, RotateCcw, Pencil, Square, FlaskConical } from 'lucide-react'
import type { Framework, ProjectState, SpecOverrides, StackDraft, TaskRequest } from '../services/api'
import CreateWizard from './CreateWizard'

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
            <button className="btn-ghost" disabled={running}
              onClick={() => confirm('Regenerate every section? Existing generated sections are replaced (a checkpoint is saved first).') && onTask({ kind: 'generate', force: true, confirm: true })}>
              <RotateCcw size={16} /> Regenerate all
            </button>
            {running && <button className="btn-ghost border-red-500/40 text-red-300" onClick={onCancel}><Square size={14} /> Cancel</button>}
          </div>
          <div className="rounded-xl border border-white/10 p-3">
            <p className="label">Edit one section</p>
            <div className="flex flex-col gap-2 sm:flex-row">
              <select aria-label="Section" className="field sm:w-36" value={sel} onChange={(e) => setSection(e.target.value)}>
                {sections.length === 0 && <option value="">no sections yet</option>}
                {sections.map((s) => <option key={s}>{s}</option>)}
              </select>
              <input aria-label="Edit instruction" className="field flex-1" value={instr} onChange={(e) => setInstr(e.target.value)} placeholder="e.g. make the headline bigger and add a second button" />
              <button className="btn-ghost" disabled={running || !sel || instr.trim().length < 3}
                onClick={() => { onTask({ kind: 'edit', section: sel, instruction: instr.trim() }); setInstr('') }}><Pencil size={15} /> Apply</button>
            </div>
          </div>
        </>
      )}
      {error && <p role="alert" className="rounded-lg border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-300">{error}</p>}
    </div>
  )
}

import { lazy, Suspense, useCallback, useEffect, useState, type ReactNode } from 'react'
import {
  ArrowLeft, Bot, Braces, Eye, Files, FolderOpen,
  Settings as Cog, TerminalSquare, Download, X, Code2, Sparkles,
} from 'lucide-react'
import Logo from '../components/Logo'
import ConnectionBadge from '../components/ConnectionBadge'
import { useOllama } from '../hooks/useOllama'
import { useTask } from '../hooks/useTask'
import { api, type Checkpoint, type Framework, type ProjectRow, type ProjectState, type Report, type SpecOverrides, type StackDraft, type Summary, type Task } from '../services/api'
import Sidebar from './Sidebar'
import PromptPanel from './PromptPanel'
import CodePanel from './CodePanel'
import BottomPanel from './BottomPanel'
import SettingsDialog from './SettingsDialog'

const PreviewPanel = lazy(() => import('../preview/PreviewPanel'))
const go = (id: string | null) => { window.location.hash = id ? `#/workspace/${id}` : '#/workspace' }
type Panel = 'projects' | 'agent' | 'preview' | 'output'

function ActivityButton({
  label, active, onClick, children,
}: { label: string; active: boolean; onClick: () => void; children: ReactNode }) {
  return (
    <button
      type="button"
      title={`${label}${active ? ' (click to hide)' : ''}`}
      aria-label={label}
      aria-pressed={active}
      onClick={onClick}
      className={`relative grid h-11 w-11 shrink-0 place-items-center border-l-2 transition ${active ? 'border-transparent bg-white/[0.07] text-white' : 'border-transparent text-[#858585] hover:bg-white/[0.05] hover:text-white'}`}
    >{children}</button>
  )
}

function PanelHeader({ title, onClose, trailing }: { title: string; onClose: () => void; trailing?: ReactNode }) {
  return (
    <div className="flex h-9 shrink-0 items-center border-b border-[#333] bg-[#252526] px-3 text-[11px] font-semibold uppercase tracking-[.12em] text-[#cccccc]">
      <span className="truncate">{title}</span>
      <div className="ml-auto flex items-center gap-1">{trailing}
        <button type="button" aria-label={`Hide ${title}`} title={`Hide ${title}`} onClick={onClose} className="rounded p-1 text-[#858585] hover:bg-white/10 hover:text-white"><X size={14} /></button>
      </div>
    </div>
  )
}

export default function Workspace({ projectId }: { projectId: string | null }) {
  const { conn, refresh } = useOllama()
  const [projects, setProjects] = useState<ProjectRow[]>([])
  const [project, setProject] = useState<ProjectState | null>(null)
  const [files, setFiles] = useState<string[]>([])
  const [shots, setShots] = useState<string[]>([])
  const [tasks, setTasks] = useState<Task[]>([])
  const [cps, setCps] = useState<Checkpoint[]>([])
  const [sums, setSums] = useState<Summary[]>([])
  const [report, setReport] = useState<Report | null>(null)
  const [version, setVersion] = useState(0)
  const [settings, setSettings] = useState(false)
  // Panels intentionally start closed: the editor is the primary workspace.
  const [showProjects, setShowProjects] = useState(false)
  const [showAgent, setShowAgent] = useState(false)
  const [showPreview, setShowPreview] = useState(false)
  const [showOutput, setShowOutput] = useState(false)
  const [loadErr, setLoadErr] = useState('')

  const reload = useCallback(async () => {
    try {
      setProjects(await api.projects())
      if (!projectId) { setProject(null); setFiles([]); setShots([]); setTasks([]); setCps([]); setSums([]); setReport(null); setLoadErr(''); return }
      const [p, f, s, t, c, su, rep] = await Promise.all([
        api.project(projectId), api.files(projectId), api.shots(projectId).catch(() => []),
        api.tasks(projectId), api.checkpoints(projectId), api.summaries(projectId), api.report(projectId).catch(() => null),
      ])
      setProject(p); setFiles(f); setShots(s); setTasks(t); setCps(c); setSums(su); setReport(rep)
      setVersion((v) => v + 1); setLoadErr('')
    } catch (e) { setLoadErr((e as Error).message) }
  }, [projectId])

  const { task, events, error, start, cancel, open, running } = useTask(projectId, reload)
  useEffect(() => { const t = setTimeout(reload, 0); return () => clearTimeout(t) }, [reload])
  useEffect(() => {
    if (running && projectId) {
      const t = setInterval(() => api.project(projectId).then(setProject).catch(() => {}), 4000)
      return () => clearInterval(t)
    }
  }, [running, projectId])

  const create = async (brief: string, fw: Framework, stack: StackDraft, overrides?: SpecOverrides) => {
    const result = await api.create(brief, fw, stack, overrides)
    await api.startTask(result.project_id, { kind: 'generate' })
    go(result.project_id)
  }

  const autoBuild = async (prompt: string) => {
    const result = await api.autoBuild(prompt)
    go(result.project_id)
  }

  const remove = async (p: ProjectRow) => {
    if (!window.confirm(`Delete "${p.name}" permanently?\nFiles, history and checkpoints will be removed. This cannot be undone.`)) return
    try {
      await api.deleteProject(p.id)
      setProjects(await api.projects())
      if (p.id === projectId) go(null)
    } catch (e) { window.alert(`Could not delete: ${(e as Error).message}`) }
  }

  const toggle = (name: Panel) => {
    if (name === 'projects') setShowProjects((v) => !v)
    if (name === 'agent') setShowAgent((v) => !v)
    if (name === 'preview') setShowPreview((v) => !v)
    if (name === 'output') setShowOutput((v) => !v)
  }

  const projectName = projects.find((p) => p.id === projectId)?.name || (projectId ? projectId : 'No folder open')

  return (
    <div className="flex h-screen min-h-0 flex-col overflow-hidden bg-[#1e1e1e] font-sans text-[#cccccc]">
      {/* IDE title bar */}
      <header className="flex h-11 shrink-0 items-center gap-3 border-b border-[#333] bg-[#181818] px-3">
        <button aria-label="Back to landing page" title="Back to landing page" className="rounded p-1.5 text-[#858585] hover:bg-white/10 hover:text-white" onClick={() => { window.location.hash = '#/' }}><ArrowLeft size={16} /></button>
        <div className="flex min-w-0 items-center gap-2">
          <Logo compact />
          <span className="hidden text-xs font-semibold text-[#cccccc] md:inline">FULL STACK AI</span>
          <span className="text-[#555]">/</span>
          <span className="max-w-[24vw] truncate text-xs text-[#a7a7a7]" title={projectName}>{projectName}</span>
        </div>
        <div className="ml-auto flex min-w-0 items-center gap-1">
          <div className="hidden items-center gap-1 xl:flex">
            <button type="button" onClick={() => toggle('projects')} aria-pressed={showProjects} className={`rounded px-2 py-1.5 text-xs ${showProjects ? 'bg-white/10 text-white' : 'text-[#999] hover:bg-white/5 hover:text-white'}`}><Files className="mr-1 inline" size={14} />Projects</button>
            <button type="button" onClick={() => toggle('agent')} aria-pressed={showAgent} className={`rounded px-2 py-1.5 text-xs ${showAgent ? 'bg-white/10 text-white' : 'text-[#999] hover:bg-white/5 hover:text-white'}`}><Bot className="mr-1 inline" size={14} />Agent</button>
            <button type="button" onClick={() => toggle('preview')} aria-pressed={showPreview} className={`rounded px-2 py-1.5 text-xs ${showPreview ? 'bg-white/10 text-white' : 'text-[#999] hover:bg-white/5 hover:text-white'}`}><Eye className="mr-1 inline" size={14} />Preview</button>
            <button type="button" onClick={() => toggle('output')} aria-pressed={showOutput} className={`rounded px-2 py-1.5 text-xs ${showOutput ? 'bg-white/10 text-white' : 'text-[#999] hover:bg-white/5 hover:text-white'}`}><TerminalSquare className="mr-1 inline" size={14} />Output</button>
          </div>
          <ConnectionBadge conn={conn} onClick={() => setSettings(true)} />
          {projectId && <a className="rounded p-1.5 text-[#999] hover:bg-white/10 hover:text-white" href={api.exportUrl(projectId)} download title="Export project as ZIP" aria-label="Export project as ZIP"><Download size={15} /></a>}
          <button className="rounded p-1.5 text-[#999] hover:bg-white/10 hover:text-white" aria-label="Open settings" title="Settings" onClick={() => setSettings(true)}><Cog size={16} /></button>
        </div>
      </header>

      {conn.state !== 'connected' && conn.state !== 'checking' && (
        <p role="status" className="shrink-0 border-b border-amber-500/20 bg-amber-500/10 px-3 py-1 text-xs text-amber-300">{conn.detail}</p>
      )}
      {loadErr && <p role="alert" className="shrink-0 border-b border-red-500/20 bg-red-500/10 px-3 py-1 text-xs text-red-300">{loadErr}</p>}

      <div className="flex min-h-0 flex-1">
        {/* VS Code-like activity bar. Clicking an active icon hides that panel. */}
        <nav aria-label="IDE panels" className="flex w-12 shrink-0 flex-col items-center border-r border-[#333] bg-[#181818] py-1">
          <ActivityButton label="Projects" active={showProjects} onClick={() => toggle('projects')}><FolderOpen size={21} /></ActivityButton>
          <ActivityButton label="AI Agent / Prompt" active={showAgent} onClick={() => toggle('agent')}><Bot size={21} /></ActivityButton>
          <ActivityButton label="Live preview" active={showPreview} onClick={() => toggle('preview')}><Eye size={21} /></ActivityButton>
          <ActivityButton label="Output, tasks and checkpoints" active={showOutput} onClick={() => toggle('output')}><TerminalSquare size={21} /></ActivityButton>
          <div className="mt-auto">
            <ActivityButton label="Settings" active={settings} onClick={() => setSettings(true)}><Cog size={20} /></ActivityButton>
          </div>
        </nav>

        <div className="flex min-h-0 min-w-0 flex-1">
          {showProjects && (
            <aside className="flex w-[240px] shrink-0 flex-col border-r border-[#333] bg-[#181818]">
              <PanelHeader title="Explorer · Projects" onClose={() => setShowProjects(false)} />
              <Sidebar projects={projects} current={projectId} onSelect={(id) => { go(id); setShowProjects(false) }} onNew={() => { go(null); setShowAgent(true) }} onDelete={remove} />
            </aside>
          )}

          <main className="flex min-h-0 min-w-0 flex-1 flex-col">
            <div className="flex min-h-0 min-w-0 flex-1">
              <section className="flex min-h-0 min-w-0 flex-1 flex-col bg-[#1e1e1e]">
                {projectId ? (
                  <CodePanel id={projectId} files={files} version={version} onSaved={reload} projectName={projectName} />
                ) : (
                  <div className="grid min-h-0 flex-1 place-items-center overflow-auto p-6 text-center">
                    <div className="max-w-lg">
                      <div className="mx-auto grid h-16 w-16 place-items-center rounded-2xl border border-white/10 bg-[#252526] text-[#e50914]"><Code2 size={32} /></div>
                      <p className="mt-5 text-xl font-semibold text-[#e5e5e5]">Your workspace is ready</p>
                      <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-[#858585]">Open an existing project or use the AI Agent to describe an app. Generated source files will open here so you can edit and save them directly.</p>
                      <div className="mt-5 flex flex-wrap justify-center gap-2">
                        <button className="inline-flex items-center gap-2 rounded bg-[#0e639c] px-3 py-2 text-sm text-white hover:bg-[#1177bb]" onClick={() => setShowAgent(true)}><Sparkles size={15} /> Create with AI Agent</button>
                        <button className="inline-flex items-center gap-2 rounded border border-[#454545] px-3 py-2 text-sm text-[#cccccc] hover:bg-white/5" onClick={() => setShowProjects(true)}><FolderOpen size={15} /> Open project</button>
                      </div>
                      <p className="mt-6 text-[11px] text-[#666]">Tip: use Ctrl+S inside the editor to save changes.</p>
                    </div>
                  </div>
                )}
              </section>

              {showAgent && (
                <aside className="flex min-h-0 w-[360px] max-w-[40vw] shrink-0 flex-col border-l border-[#333] bg-[#1e1e1e]">
                  <PanelHeader title="AI Agent" onClose={() => setShowAgent(false)} trailing={running ? <span className="mr-1 rounded-full bg-[#0e639c]/20 px-2 py-0.5 text-[10px] normal-case text-sky-300">Running</span> : undefined} />
                  <div className="min-h-0 flex-1 overflow-auto">
                    <PromptPanel project={project} running={running} error={error} onCreate={create} onAutoBuild={autoBuild} onTask={start} onCancel={cancel} />
                  </div>
                </aside>
              )}

              {showPreview && (
                <aside className="flex min-h-0 w-[min(42vw,620px)] min-w-[310px] shrink-0 flex-col border-l border-[#333] bg-[#1e1e1e]">
                  <PanelHeader title="Live Preview" onClose={() => setShowPreview(false)} />
                  {projectId ? (
                    <Suspense fallback={<div className="p-4 text-xs text-[#858585]">Loading preview…</div>}>
                      <div className="min-h-0 flex-1"><PreviewPanel id={projectId} version={version} onReload={() => setVersion((v) => v + 1)} shots={shots} project={project} task={task} summaries={sums} report={report} /></div>
                    </Suspense>
                  ) : <div className="p-4 text-sm text-[#858585]">Create or open a project to see its preview.</div>}
                </aside>
              )}
            </div>

            {showOutput && (
              <section className="flex h-[245px] shrink-0 flex-col border-t border-[#333] bg-[#181818]">
                <PanelHeader title="Output · Agent Activity" onClose={() => setShowOutput(false)} trailing={running ? <span className="mr-1 inline-flex items-center gap-1 text-[10px] normal-case text-sky-300"><span className="h-1.5 w-1.5 animate-pulse rounded-full bg-sky-400" />Running</span> : undefined} />
                <div className="min-h-0 flex-1"><BottomPanel id={projectId} events={events} task={task} tasks={tasks} checkpoints={cps} running={running} onOpenTask={open} onChanged={reload} /></div>
              </section>
            )}
          </main>
        </div>
      </div>

      <footer className="flex h-[22px] shrink-0 items-center gap-3 border-t border-[#333] bg-[#007acc] px-2 text-[10px] text-white">
        <span className="inline-flex items-center gap-1"><Braces size={11} /> Full Stack AI Agent</span>
        <span className="ml-auto">{projectId ? `${files.length} files` : 'No project'}</span>
        <span>{running ? 'Agent running' : 'Ready'}</span>
      </footer>

      {settings && <SettingsDialog models={conn.status?.models ?? []} onClose={() => setSettings(false)} onSaved={refresh} />}
    </div>
  )
}

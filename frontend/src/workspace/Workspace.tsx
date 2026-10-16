import { useCallback, useEffect, useState } from 'react'
import { ArrowLeft, Download, PanelLeftClose, PanelLeftOpen, Settings as Cog, ChevronDown, ChevronUp } from 'lucide-react'
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
import PreviewPanel from '../preview/PreviewPanel'

const go = (id: string | null) => { window.location.hash = id ? `#/workspace/${id}` : '#/workspace' }
type Pane = 'projects' | 'build' | 'code' | 'preview' | 'log'

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
  const [sidebar, setSidebar] = useState(true)
  const [logOpen, setLogOpen] = useState(true)
  const [pane, setPane] = useState<Pane>('build')
  const [loadErr, setLoadErr] = useState('')

  const reload = useCallback(async () => {
    try {
      setProjects(await api.projects())
      if (!projectId) { setProject(null); setFiles([]); setShots([]); setTasks([]); setCps([]); setSums([]); setReport(null); return }
      const [p, f, s, t, c, su, rep] = await Promise.all([api.project(projectId), api.files(projectId), api.shots(projectId).catch(() => []),
        api.tasks(projectId), api.checkpoints(projectId), api.summaries(projectId), api.report(projectId).catch(() => null)])
      setProject(p); setFiles(f); setShots(s); setTasks(t); setCps(c); setSums(su); setReport(rep); setVersion((v) => v + 1); setLoadErr('')
    } catch (e) { setLoadErr((e as Error).message) }
  }, [projectId])

  const { task, events, error, start, cancel, open, running } = useTask(projectId, reload)
  useEffect(() => { const t = setTimeout(reload, 0); return () => clearTimeout(t) }, [reload])
  useEffect(() => { if (running) { const t = setInterval(() => api.project(projectId!).then(setProject).catch(() => {}), 4000); return () => clearInterval(t) } }, [running, projectId])

  const create = async (brief: string, fw: Framework, stack: StackDraft, overrides?: SpecOverrides) => {
    const result = await api.create(brief, fw, stack, overrides)
    const projectId = result.project_id
    await api.startTask(projectId, { kind: 'generate' })
    go(projectId); setPane('build')
  }

  const autoBuild = async (prompt: string) => {
    const result = await api.autoBuild(prompt)
    go(result.project_id); setPane('build')
  }

  const remove = async (p: ProjectRow) => {
    if (!window.confirm(`Delete "${p.name}" permanently?\nFiles, history and checkpoints will be removed. This cannot be undone.`)) return
    try {
      await api.deleteProject(p.id)
      setProjects(await api.projects())
      if (p.id === projectId) go(null)
    } catch (e) { window.alert(`Could not delete: ${(e as Error).message}`) }
  }

  const paneCls = (p: Pane) => (pane === p ? 'flex' : 'hidden lg:flex')
  const tabs: [Pane, string][] = [['projects', 'Projects'], ['build', 'Build'], ['code', 'Code'], ['preview', 'Preview'], ['log', 'Log']]

  return (
    <div className="flex h-screen flex-col bg-bg text-zinc-200">
      <header className="flex items-center gap-3 border-b border-white/10 bg-surface/60 px-3 py-2">
        <button aria-label="Back to landing page" className="rounded-md p-1.5 text-zinc-400 hover:text-white" onClick={() => { window.location.hash = '#/' }}><ArrowLeft size={18} /></button>
        <Logo compact /><span className="hidden font-display text-xs tracking-[0.18em] text-white sm:block">WORKSPACE</span>
        <button aria-label="Toggle sidebar" className="hidden rounded-md p-1.5 text-zinc-400 hover:text-white lg:block" onClick={() => setSidebar(!sidebar)}>{sidebar ? <PanelLeftClose size={18} /> : <PanelLeftOpen size={18} />}</button>
        <div className="ml-auto flex items-center gap-2">
          <ConnectionBadge conn={conn} onClick={() => setSettings(true)} />
          {projectId && <a className="btn-ghost !px-2.5 !py-1.5" href={api.exportUrl(projectId)} download title="Export project as zip"><Download size={15} /><span className="hidden sm:inline">Export</span></a>}
          <button className="btn-ghost !px-2.5 !py-1.5" aria-label="Open settings" onClick={() => setSettings(true)}><Cog size={15} /><span className="hidden sm:inline">Settings</span></button>
        </div>
      </header>

      {conn.state !== 'connected' && conn.state !== 'checking' && (
        <p role="status" className="border-b border-amber-500/20 bg-amber-500/10 px-4 py-1.5 text-xs text-amber-300">{conn.detail}</p>
      )}
      {loadErr && <p role="alert" className="border-b border-red-500/20 bg-red-500/10 px-4 py-1.5 text-xs text-red-300">{loadErr}</p>}

      <nav className="flex gap-1 border-b border-white/10 px-2 py-1 lg:hidden" aria-label="Workspace panes">
        {tabs.map(([p, l]) => <button key={p} onClick={() => setPane(p)} aria-pressed={pane === p} className={`flex-1 rounded-md py-1.5 text-xs ${pane === p ? 'bg-accent/20 text-white' : 'text-zinc-500'}`}>{l}</button>)}
      </nav>

      <div className="flex min-h-0 flex-1">
        {sidebar && (
          <aside className={`${paneCls('projects')} w-full shrink-0 flex-col border-r border-white/10 bg-surface/40 lg:w-64`}>
            <Sidebar projects={projects} current={projectId} onSelect={(id) => { go(id); setPane('build') }} onNew={() => { go(null); setPane('build') }} onDelete={remove} />
          </aside>
        )}
        <main className="grid min-h-0 min-w-0 flex-1 lg:grid-cols-2">
          <section className={`${paneCls('build')} ${pane === 'code' ? '!flex' : ''} min-h-0 min-w-0 flex-col border-r border-white/10`}>
            <div className={`${pane === 'code' ? 'hidden lg:block' : ''} ${pane === 'build' ? 'min-h-0 flex-1 lg:flex-none' : ''} ${projectId ? 'shrink-0 border-b border-white/10 lg:max-h-[48%]' : 'min-h-0 flex-1'} overflow-auto`}><PromptPanel project={project} running={running} error={error} onCreate={create} onAutoBuild={autoBuild} onTask={start} onCancel={cancel} /></div>
            <div className={`${pane === 'build' ? 'hidden lg:flex' : 'flex'} ${projectId ? '' : 'lg:hidden'} min-h-0 flex-1 flex-col`}>
              {projectId ? <CodePanel id={projectId} files={files} version={version} onSaved={() => setVersion((v) => v + 1)} /> : <p className="p-6 text-sm text-zinc-600">Files appear here after you create a project.</p>}
            </div>
          </section>
          <section className={`${paneCls('preview')} min-h-0 min-w-0 flex-col`}>
            <div className="min-h-0 flex-1">
              {projectId ? <PreviewPanel id={projectId} version={version} onReload={() => setVersion((v) => v + 1)} shots={shots} project={project} task={task} summaries={sums} report={report} />
                : <div className="max-w-md space-y-2 p-6 text-sm text-zinc-500">
                  <p className="text-zinc-300">What happens after you create</p>
                  <p>The agent plans the pages, writes each section, then checks the build, accessibility and responsive layout.</p>
                  <p>A live preview, the generated files and a verification report appear here as soon as generation starts.</p>
                </div>}
            </div>
            <div className={`${pane === 'log' ? 'flex' : 'hidden lg:flex'} min-h-0 flex-col border-t border-white/10 ${logOpen ? 'h-56' : 'h-9'} ${pane === 'log' ? '!h-full' : ''}`}>
              <button className="hidden items-center gap-1 px-3 py-1.5 text-left text-[11px] uppercase tracking-wider text-zinc-500 hover:text-zinc-300 lg:flex" onClick={() => setLogOpen(!logOpen)} aria-expanded={logOpen}>
                {logOpen ? <ChevronDown size={13} /> : <ChevronUp size={13} />} Activity, history &amp; checkpoints</button>
              {(logOpen || pane === 'log') && <div className="min-h-0 flex-1"><BottomPanel id={projectId} events={events} task={task} tasks={tasks} checkpoints={cps} running={running} onOpenTask={open} onChanged={reload} /></div>}
            </div>
          </section>
        </main>
      </div>
      {settings && <SettingsDialog models={conn.status?.models ?? []} onClose={() => setSettings(false)} onSaved={refresh} />}
    </div>
  )
}

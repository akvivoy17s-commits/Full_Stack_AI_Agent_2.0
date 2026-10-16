import { useState } from 'react'
import { Monitor, Tablet, Smartphone, RefreshCw, ExternalLink } from 'lucide-react'
import { api, type ProjectState, type Report, type Summary, type Task } from '../services/api'
import ReportPanel from './ReportPanel'

const DEVICES = [['Desktop', Monitor, '100%'], ['Tablet', Tablet, '768px'], ['Mobile', Smartphone, '375px']] as const
type Tab = 'preview' | 'shots' | 'report' | 'console'

interface Props { id: string; version: number; onReload: () => void; shots: string[]; project: ProjectState | null; task: Task | null; summaries: Summary[]; report: Report | null }

export default function PreviewPanel({ id, version, onReload, shots, project, task, summaries, report }: Props) {
  const [tab, setTab] = useState<Tab>('preview')
  const [dev, setDev] = useState(0)
  const issues = [...(project?.errors ?? [])]
  if (task?.status === 'failed' && task.error) issues.unshift(task.error)
  const last = summaries[0]?.summary

  return (
    <div className="flex h-full min-h-0 flex-col">
      <div className="flex items-center gap-1 border-b border-white/10 px-2 py-1.5" role="tablist">
        {(['preview', 'shots', 'report', 'console'] as Tab[]).map((t) => (
          <button key={t} role="tab" aria-selected={tab === t} onClick={() => setTab(t)}
            className={`rounded-md px-2.5 py-1 text-xs capitalize ${tab === t ? 'bg-accent/15 text-white' : 'text-zinc-500 hover:text-zinc-200'}`}>
            {t === 'shots' ? `Screenshots (${shots.length})` : t === 'report' ? `Test report${report ? ` (${report.counts.failed} failed)` : ''}` : t === 'console' ? `Console (${issues.length})` : 'Preview'}
          </button>
        ))}
        {tab === 'preview' && (
          <div className="ml-auto flex items-center gap-1">
            {DEVICES.map(([n, Icon], i) => (
              <button key={n} aria-label={`${n} preview`} aria-pressed={dev === i} onClick={() => setDev(i)}
                className={`rounded-md p-1.5 ${dev === i ? 'bg-accent/20 text-accent' : 'text-zinc-500 hover:text-white'}`}><Icon size={15} /></button>
            ))}
            <button aria-label="Reload preview" className="rounded-md p-1.5 text-zinc-500 hover:text-white" onClick={onReload}><RefreshCw size={15} /></button>
            <a aria-label="Open preview in new tab" className="rounded-md p-1.5 text-zinc-500 hover:text-white" href={api.previewUrl(id, version)} target="_blank" rel="noreferrer"><ExternalLink size={15} /></a>
          </div>
        )}
      </div>
      <div className="min-h-0 flex-1 overflow-auto bg-black/30">
        {tab === 'preview' && (
          <div className="flex h-full justify-center p-2">
            <iframe key={`${id}-${version}`} title="Live preview" src={api.previewUrl(id, version)} sandbox="allow-scripts allow-forms allow-popups allow-modals"
              className="h-full rounded-lg border border-white/10 bg-white transition-[width] duration-300" style={{ width: DEVICES[dev][2], maxWidth: '100%' }} />
          </div>
        )}
        {tab === 'shots' && (
          <div className="grid gap-3 p-3 sm:grid-cols-2">
            {shots.length === 0 && <p className="text-sm text-zinc-500">No screenshots yet. They are captured when browser checks run (Playwright installed and USE_BROWSER=1).</p>}
            {shots.map((s) => (
              <a key={s} href={api.shotUrl(id, s)} target="_blank" rel="noreferrer" className="block overflow-hidden rounded-lg border border-white/10 hover:border-accent/50">
                <img src={api.shotUrl(id, s)} alt={`Screenshot ${s}`} loading="lazy" className="w-full" /><span className="block px-2 py-1 text-xs text-zinc-500">{s}</span></a>
            ))}
          </div>
        )}
        {tab === 'report' && <ReportPanel report={report} />}
        {tab === 'console' && (
          <div className="space-y-3 p-3 text-sm">
            <div className="rounded-lg border border-white/10 p-3 text-xs text-zinc-400">
              {last ? <>Last check: <b className="text-zinc-200">{last.kind}</b> · {last.issues.length} issue(s) · repairs {last.repairs} · sections {last.sections} · browser: {last.browser}</>
                : 'No checks have run yet. Use Verify to run static and browser checks.'}
            </div>
            {issues.length === 0 ? <p className="text-zinc-500">No build errors or issues recorded.</p>
              : <ul className="space-y-1.5">{issues.map((i, n) => <li key={n} className="rounded-md border border-red-500/20 bg-red-500/5 px-3 py-2 font-mono text-xs text-red-300">{i}</li>)}</ul>}
          </div>
        )}
      </div>
    </div>
  )
}

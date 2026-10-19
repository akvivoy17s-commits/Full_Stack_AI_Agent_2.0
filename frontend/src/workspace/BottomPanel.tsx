import { useEffect, useRef, useState } from 'react'
import { History, Save, Undo2 } from 'lucide-react'
import BackendPanel from './BackendPanel'
import TerminalPanel from './TerminalPanel'
import ProjectScanPanel from './ProjectScanPanel'
import GitPanel from './GitPanel'
import { api, type Checkpoint, type Task, type TaskEvent } from '../services/api'

type Tab = 'activity' | 'history' | 'checkpoints' | 'backend' | 'terminal' | 'scan' | 'git'
const LVL = { info: 'text-zinc-300', warn: 'text-amber-300', error: 'text-red-400' } as const
const ST: Record<string, string> = {
  succeeded: 'border-emerald-500/30 text-emerald-300', completed_with_issues: 'border-amber-500/30 text-amber-300',
  failed: 'border-red-500/30 text-red-300', cancelled: 'border-zinc-500/30 text-zinc-400', running: 'border-accent/40 text-accentSoft', queued: 'border-white/10 text-zinc-400',
}

interface Props {
  id: string | null; events: TaskEvent[]; task: Task | null; tasks: Task[]; checkpoints: Checkpoint[]
  running: boolean; onOpenTask: (id: string) => void; onChanged: () => void
}

export default function BottomPanel({ id, events, task, tasks, checkpoints, running, onOpenTask, onChanged }: Props) {
  const [tab, setTab] = useState<Tab>('activity')
  const [msg, setMsg] = useState('')
  const end = useRef<HTMLDivElement>(null)
  useEffect(() => { end.current?.scrollIntoView({ block: 'nearest' }) }, [events.length, tab])

  const restore = async (cid: string) => {
    if (!id || !confirm('Restore this checkpoint? Current files are replaced (a safety checkpoint of the current state is kept).')) return
    try { await api.restore(id, cid); setMsg('Restored'); onChanged() } catch (e) { setMsg((e as Error).message) }
  }
  const make = async () => { if (id) try { await api.makeCheckpoint(id, 'manual'); setMsg('Checkpoint saved'); onChanged() } catch (e) { setMsg((e as Error).message) } }

  return (
    <div className="flex h-full min-h-0 flex-col">
      <div className="flex items-center gap-1 border-b border-white/10 px-2 py-1.5" role="tablist">
        {(['activity', 'history', 'checkpoints', 'backend', 'terminal', 'scan', 'git'] as Tab[]).map((t) => (
          <button key={t} role="tab" aria-selected={tab === t} onClick={() => setTab(t)}
            className={`rounded-md px-2.5 py-1 text-xs capitalize ${tab === t ? 'bg-accent/15 text-white' : 'text-zinc-500 hover:text-zinc-200'}`}>
            {t === 'activity' ? 'Agent activity' : t === 'history' ? `Task history (${tasks.length})` : t === 'backend' ? 'Backend' : t === 'terminal' ? 'Terminal' : t === 'scan' ? 'Project scan' : t === 'git' ? 'Git' : `Checkpoints (${checkpoints.length})`}
          </button>
        ))}
        {running && <span className="chip ml-auto border-accent/40 text-accentSoft"><span className="h-1.5 w-1.5 animate-blink rounded-full bg-accent" />running</span>}
        {tab === 'checkpoints' && <button className="btn-ghost ml-auto !px-2 !py-1 text-xs" disabled={!id} onClick={make}><Save size={13} /> Save checkpoint</button>}
        {msg && <span className="ml-2 text-xs text-zinc-500">{msg}</span>}
      </div>
      <div className="min-h-0 flex-1 overflow-auto p-3 font-mono text-xs">
        {tab === 'activity' && (
          <div role="log" aria-live="polite">
            {events.length === 0 && <p className="text-zinc-600">{id ? 'No agent activity for this project yet.' : 'Select or create a project.'}</p>}
            {events.map((e) => (
              <p key={e.id} className={LVL[e.level]}><span className="text-zinc-600">{new Date(e.ts * 1000).toLocaleTimeString()} </span>
                <span className="text-accent">[{e.stage}]</span> {e.msg}</p>
            ))}
            {task && !running && <p className="mt-2 text-zinc-500">Task {task.id}: <b>{task.status.replace(/_/g, ' ')}</b>{task.error ? ` — ${task.error}` : ''}</p>}
            <div ref={end} />
          </div>
        )}
        {tab === 'history' && (
          <ul className="space-y-1.5 font-sans">
            {tasks.length === 0 && <li className="text-zinc-600">No tasks yet.</li>}
            {tasks.map((t) => (
              <li key={t.id}><button onClick={() => { onOpenTask(t.id); setTab('activity') }}
                className="flex w-full items-center gap-3 rounded-lg border border-white/10 px-3 py-2 text-left text-sm hover:bg-white/5">
                <History size={14} className="text-zinc-500" /><span className="text-zinc-200">{t.kind}</span>
                <span className={`chip ${ST[t.status] ?? ''}`}>{t.status.replace(/_/g, ' ')}</span>
                <span className="ml-auto text-xs text-zinc-500">{new Date(t.created_at * 1000).toLocaleString()}</span></button></li>
            ))}
          </ul>
        )}
        {tab === 'backend' && <BackendPanel id={id} running={running} onChanged={onChanged} />}
        {tab === 'terminal' && <TerminalPanel id={id} />}
        {tab === 'scan' && <ProjectScanPanel id={id} />}
        {tab === 'git' && <GitPanel id={id} onChanged={onChanged} />}
        {tab === 'checkpoints' && (
          <ul className="space-y-1.5 font-sans">
            {checkpoints.length === 0 && <li className="text-zinc-600">No checkpoints yet. One is saved automatically before every task.</li>}
            {checkpoints.map((c) => (
              <li key={c.id} className="flex items-center gap-3 rounded-lg border border-white/10 px-3 py-2 text-sm">
                <span className="text-zinc-200">{c.label}</span><span className="text-xs text-zinc-500">{(c.size / 1024).toFixed(1)} KB · {new Date(c.created_at * 1000).toLocaleString()}</span>
                <button className="btn-ghost ml-auto !px-2 !py-1 text-xs" disabled={running} onClick={() => restore(c.id)}><Undo2 size={13} /> Restore</button></li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}

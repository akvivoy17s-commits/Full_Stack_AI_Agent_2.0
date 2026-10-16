import { Plus, FolderGit2, Trash2 } from 'lucide-react'
import type { ProjectRow } from '../services/api'

export default function Sidebar({ projects, current, onSelect, onNew, onDelete }: {
  projects: ProjectRow[]; current: string | null; onSelect: (id: string) => void; onNew: () => void; onDelete: (p: ProjectRow) => void
}) {
  return (
    <div className="flex h-full min-h-0 flex-col">
      <div className="p-3">
        <button className="btn-primary w-full" onClick={onNew}><Plus size={16} /> New project</button>
        <label className="label mt-3" htmlFor="proj-select">Existing project</label>
        <select id="proj-select" className="field" value={current ?? ''} onChange={(e) => e.target.value && onSelect(e.target.value)}>
          <option value="">Select…</option>
          {projects.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
        </select>
      </div>
      <p className="label px-3">Projects ({projects.length})</p>
      <ul className="min-h-0 flex-1 space-y-1 overflow-auto px-2 pb-2">
        {projects.length === 0 && <li className="px-2 py-3 text-sm text-zinc-600">No projects yet. Create one to start.</li>}
        {projects.map((p) => (
          <li key={p.id} className="group relative">
            <button onClick={() => onSelect(p.id)} aria-current={p.id === current}
              className={`flex w-full items-start gap-2 rounded-lg px-2.5 py-2 text-left text-sm transition ${p.id === current ? 'bg-accent/15 text-white ring-1 ring-accent/40' : 'text-zinc-400 hover:bg-white/5'}`}>
              <FolderGit2 size={15} className="mt-0.5 shrink-0 text-accent" />
              <span className="min-w-0"><span className="block truncate">{p.name}</span>
                <span className="block text-[11px] text-zinc-600">{new Date(p.updated_at * 1000).toLocaleString()}</span></span>
            </button>
            <button aria-label={`Delete project ${p.name}`} title="Delete project"
              onClick={() => onDelete(p)}
              className="absolute right-1.5 top-1.5 rounded-md p-1.5 text-zinc-600 opacity-60 transition hover:bg-red-500/15 hover:text-red-400 group-hover:opacity-100">
              <Trash2 size={14} />
            </button>
          </li>
        ))}
      </ul>
    </div>
  )
}

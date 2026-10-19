import { Plus, FolderGit2, Trash2, Clock3 } from 'lucide-react'
import type { ProjectRow } from '../services/api'

export default function Sidebar({ projects, current, onSelect, onNew, onDelete }: {
  projects: ProjectRow[]; current: string | null; onSelect: (id: string) => void; onNew: () => void; onDelete: (p: ProjectRow) => void
}) {
  return (
    <div className="flex h-full min-h-0 flex-col bg-[#181818] text-[#cccccc]">
      <div className="border-b border-[#2b2b2b] p-2">
        <button type="button" className="flex h-8 w-full items-center justify-center gap-2 rounded border border-[#454545] bg-[#252526] px-2 text-xs text-[#ddd] hover:bg-[#303030]" onClick={onNew}>
          <Plus size={14} /> New project
        </button>
        <label className="mb-1 mt-3 block text-[10px] font-semibold uppercase tracking-wider text-[#858585]" htmlFor="project-select">Open project</label>
        <select id="project-select" className="h-8 w-full rounded border border-[#3c3c3c] bg-[#252526] px-2 text-xs text-[#ddd] outline-none focus:border-[#007acc]" value={current ?? ''} onChange={(e) => e.target.value && onSelect(e.target.value)}>
          <option value="">Choose a project…</option>
          {projects.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
        </select>
      </div>
      <div className="flex h-8 shrink-0 items-center px-3 text-[10px] font-semibold uppercase tracking-wider text-[#858585]">Recent projects <span className="ml-auto font-normal">{projects.length}</span></div>
      <ul className="min-h-0 flex-1 overflow-auto pb-2">
        {projects.length === 0 && <li className="px-3 py-4 text-xs leading-5 text-[#777]">No projects yet. Select New project to build your first app.</li>}
        {projects.map((p) => (
          <li key={p.id} className="group relative">
            <button type="button" onClick={() => onSelect(p.id)} aria-current={p.id === current}
              className={`flex min-h-9 w-full items-start gap-2 border-l-2 py-1.5 pl-2 pr-8 text-left text-xs transition ${p.id === current ? 'border-[#007acc] bg-[#37373d] text-white' : 'border-transparent text-[#cccccc] hover:bg-white/[0.05]'}`}>
              <FolderGit2 size={14} className={`mt-0.5 shrink-0 ${p.id === current ? 'text-[#75beff]' : 'text-[#858585]'}`} />
              <span className="min-w-0 flex-1"><span className="block truncate">{p.name}</span><span className="mt-0.5 flex items-center gap-1 truncate text-[10px] text-[#777]"><Clock3 size={10} />{new Date(p.updated_at * 1000).toLocaleString()}</span></span>
            </button>
            <button type="button" aria-label={`Delete project ${p.name}`} title="Delete project" onClick={() => onDelete(p)}
              className="absolute right-1 top-1.5 rounded p-1 text-[#777] opacity-0 hover:bg-red-500/15 hover:text-red-300 group-hover:opacity-100 focus:opacity-100">
              <Trash2 size={13} />
            </button>
          </li>
        ))}
      </ul>
    </div>
  )
}

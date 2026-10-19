import { useCallback, useEffect, useState } from 'react'
import { RefreshCw, GitBranch, GitCommit, Eye } from 'lucide-react'
import { api, type GitDiff, type GitLog, type GitStatus } from '../services/api'

export default function GitPanel({ id, onChanged }: { id: string | null; onChanged: () => void }) {
  const [status, setStatus] = useState<GitStatus | null>(null)
  const [history, setHistory] = useState<GitLog | null>(null)
  const [diff, setDiff] = useState<GitDiff | null>(null)
  const [selected, setSelected] = useState<string[]>([])
  const [message, setMessage] = useState('Update project')
  const [branch, setBranch] = useState('feature/ai-update')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const refresh = useCallback(async () => {
    if (!id) { setStatus(null); return }
    setBusy(true); setError('')
    try {
      const [s, h] = await Promise.all([api.gitStatus(id), api.gitLog(id).catch(() => null)])
      setStatus(s); setHistory(h); setSelected((old) => old.filter((x) => (s.changes ?? []).some((c) => c.path === x)))
    } catch (e) { setError((e as Error).message) } finally { setBusy(false) }
  }, [id])
  useEffect(() => { void refresh() }, [refresh])
  const viewDiff = async (path?: string) => {
    if (!id) return
    setError(''); setDiff(null)
    try { setDiff(await api.gitDiff(id, path)) } catch (e) { setError((e as Error).message) }
  }
  const doBranch = async () => {
    if (!id || !branch.trim() || !window.confirm(`Create branch "${branch}"? The working tree must be clean.`)) return
    setBusy(true); setError('')
    try { await api.gitCreateBranch(id, branch.trim(), true); await refresh(); onChanged() } catch (e) { setError((e as Error).message) } finally { setBusy(false) }
  }
  const doCommit = async () => {
    if (!id || !selected.length || !message.trim()) return
    if (!window.confirm(`Create a Git commit for these ${selected.length} selected file(s)?`)) return
    setBusy(true); setError('')
    try { await api.gitCommit(id, message.trim(), selected, true); setSelected([]); await refresh(); await viewDiff(); onChanged() }
    catch (e) { setError((e as Error).message) } finally { setBusy(false) }
  }
  if (!id) return <p className="text-zinc-600">Select a project to view Git status.</p>
  return <div className="space-y-3 font-sans text-xs">
    <div className="flex items-center justify-between"><p className="text-zinc-400">Git changes and recovery</p><button className="btn-ghost !px-2 !py-1 text-xs" disabled={busy} onClick={() => void refresh()}><RefreshCw size={13} />Refresh</button></div>
    {error && <p role="alert" className="rounded border border-amber-500/30 bg-amber-500/5 p-2 text-amber-300">{error}</p>}
    {status && !status.initialized && <div className="rounded border border-white/10 p-3"><p className="text-zinc-200">{status.summary}</p><p className="mt-1 text-zinc-500">Run Git init in this project manually if you want version tracking; the agent will not initialize a repository implicitly.</p></div>}
    {status?.initialized && <>
      <div className="rounded border border-white/10 p-3"><p className="text-zinc-200"><GitBranch className="mr-1 inline" size={14}/>{status.branch || '(detached HEAD)'}</p><p className={status.clean ? 'mt-1 text-emerald-300' : 'mt-1 text-amber-300'}>{status.summary}</p></div>
      <div className="space-y-1 rounded border border-white/10 p-3"><h3 className="mb-2 font-semibold text-zinc-400">Changes</h3>
        {!status.changes?.length && <p className="text-zinc-500">No changed files.</p>}
        {status.changes?.map((c) => <label key={c.path} className="flex min-w-0 items-center gap-2 rounded px-1 py-1 hover:bg-white/5"><input type="checkbox" disabled={c.secret || busy} checked={selected.includes(c.path)} onChange={(e) => setSelected((old) => e.target.checked ? [...old, c.path] : old.filter((x) => x !== c.path))}/><span className="w-8 shrink-0 text-sky-300">{c.code}</span><span className="min-w-0 flex-1 break-all text-zinc-300">{c.path}</span><button type="button" className="rounded p-1 text-zinc-500 hover:bg-white/10 hover:text-white" title={`View diff for ${c.path}`} onClick={(e) => { e.preventDefault(); void viewDiff(c.path) }}><Eye size={13}/></button>{c.secret && <span className="text-amber-300">protected</span>}</label>)}
      </div>
      <div className="space-y-2 rounded border border-white/10 p-3"><h3 className="font-semibold text-zinc-400">Create commit</h3><input className="field" value={message} onChange={(e) => setMessage(e.target.value)} aria-label="Commit message"/><p className="text-zinc-500">Only selected ordinary project files are included; unrelated staged changes are kept out of this commit.</p><button className="btn-primary !px-3 !py-1.5" disabled={busy || !selected.length || !message.trim()} onClick={() => void doCommit()}><GitCommit size={13}/>Commit selected ({selected.length})</button></div>
      <div className="flex gap-2 rounded border border-white/10 p-3"><input className="field min-w-0 flex-1" value={branch} onChange={(e) => setBranch(e.target.value)} aria-label="New branch name"/><button className="btn-ghost !px-3 !py-1.5" disabled={busy || !status.clean} onClick={() => void doBranch()}><GitBranch size={13}/>New branch</button></div>
      <div className="rounded border border-white/10 p-3"><h3 className="mb-2 font-semibold text-zinc-400">Recent commits</h3>{!history?.commits?.length ? <p className="text-zinc-500">No commit history found.</p> : history.commits.map((c) => <p key={c} className="break-all py-0.5 text-zinc-400">{c}</p>)}</div>
      <button className="btn-ghost !px-3 !py-1.5" onClick={() => void viewDiff()}><Eye size={13}/>View tracked diff</button>
      {diff && <pre className="max-h-72 overflow-auto whitespace-pre-wrap break-words rounded border border-white/10 bg-black/30 p-3 text-[11px] text-zinc-300">{diff.diff || 'No tracked diff to display.'}</pre>}
    </>}
  </div>
}

import { useCallback, useEffect, useState } from 'react'
import { Server } from 'lucide-react'
import { api, type BackendInfo, type BackendResult } from '../services/api'

interface Props { id: string | null; running: boolean; onChanged: () => void }

export default function BackendPanel({ id, running, onChanged }: Props) {
  const [info, setInfo] = useState<BackendInfo | null>(null)
  const [result, setResult] = useState<BackendResult | null>(null)
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState('')

  const load = useCallback(async () => {
    if (!id) { setInfo(null); setResult(null); return }
    try { setInfo(await api.backendInfo(id)); setErr('') } catch (e) { setErr((e as Error).message) }
  }, [id])
  useEffect(() => { const t = setTimeout(load, 0); return () => clearTimeout(t) }, [load, running])

  const generate = async () => {
    if (!id) return
    setBusy(true); setErr('')
    try { setResult(await api.generateBackend(id)); await load(); onChanged() } catch (e) { setErr((e as Error).message) } finally { setBusy(false) }
  }

  if (!id) return <p className="font-sans text-zinc-600">Select or create a project.</p>
  const cov = info?.coverage
  const last = info?.last
  const warns = [...(result?.warnings ?? []), ...(result?.not_generated ?? [])]
  return (
    <div className="space-y-3 font-sans text-sm">
      <div className="flex flex-wrap items-center gap-2">
        <Server size={14} className="text-zinc-500" />
        <span className="text-zinc-200">{cov ? (cov.backend === 'none' ? 'No backend selected' : cov.backend) : 'Loading…'}</span>
        {cov && cov.backend !== 'none' && (
          <span className={`chip ${cov.ready ? 'border-emerald-500/30 text-emerald-300' : 'border-amber-500/30 text-amber-300'}`}>{cov.ready ? 'generator ready' : 'not fully supported'}</span>
        )}
        <button className="btn-ghost ml-auto !px-2.5 !py-1 text-xs" disabled={busy || running || !cov?.ready} onClick={generate}>
          {busy ? 'Generating…' : last?.generated ? 'Regenerate backend' : 'Generate backend'}
        </button>
      </div>
      {cov?.note && <p className="text-xs text-zinc-500">{cov.note}</p>}
      {cov?.gaps.map((g) => <p key={g} className="text-xs text-amber-300">Not supported yet: {g}</p>)}
      {err && <p role="alert" className="text-xs text-red-300">{err}</p>}
      {last?.generated && (
        <p className="text-xs text-zinc-400">Last run: {last.generator} · {last.db ?? 'no database'} · {last.routes} routes · {last.files} files</p>
      )}
      {result?.generated && (
        <div className="space-y-1 text-xs text-zinc-400">
          <p>{result.written?.length ?? 0} file(s) written{result.kept?.length ? `, ${result.kept.length} kept (your edits)` : ''}.</p>
          {result.kept?.map((k) => <p key={k} className="text-amber-300">Kept your edited file: {k}</p>)}
          {warns.map((w) => <p key={w} className="text-amber-300">{w}</p>)}
          {result.commands && Object.entries(result.commands).map(([k, v]) => <p key={k} className="font-mono text-zinc-300"><span className="text-zinc-500">{k}:</span> {v}</p>)}
        </div>
      )}
      {result && !result.generated && <p className="text-xs text-amber-300">Not generated. {result.gaps?.join('; ') || result.note}</p>}
    </div>
  )
}

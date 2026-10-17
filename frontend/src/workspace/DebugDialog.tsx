import { useState } from 'react'
import { AlertTriangle, Bug, CheckCircle2, ClipboardPaste, Loader2, ShieldCheck, Wrench, X } from 'lucide-react'
import { api, type DebugResult } from '../services/api'

export default function DebugDialog({ projectId, projectBrief, onClose, onFixed }: { projectId: string; projectBrief?: string; onClose: () => void; onFixed: () => void }) {
  const [errorText, setErrorText] = useState('')
  const [applyFixes, setApplyFixes] = useState(true)
  const [busy, setBusy] = useState(false)
  const [result, setResult] = useState<DebugResult | null>(null)
  const [error, setError] = useState('')

  const run = async () => {
    if (errorText.trim().length < 5) { setError('Paste the browser console, terminal, build, or runtime error first.'); return }
    setBusy(true); setError(''); setResult(null)
    try {
      const r = await api.debugProject(projectId, errorText.trim(), applyFixes)
      setResult(r)
      if (r.applied.length) onFixed()
    } catch (e) { setError((e as Error).message || 'Debug analysis failed.') }
    finally { setBusy(false) }
  }

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/75 p-3 backdrop-blur-sm" role="dialog" aria-modal="true" aria-labelledby="debug-title">
      <div className="flex max-h-[92vh] w-full max-w-4xl flex-col overflow-hidden rounded-2xl border border-white/10 bg-[#101014] shadow-2xl shadow-black/60">
        <header className="flex items-center gap-3 border-b border-white/10 px-5 py-4">
          <div className="grid h-10 w-10 place-items-center rounded-xl bg-rose-500/15 text-rose-300"><Bug size={20} /></div>
          <div className="min-w-0"><h2 id="debug-title" className="font-display text-lg font-semibold text-white">Project Debugger</h2><p className="text-xs text-zinc-500">Paste an error. The agent scans the currently open workspace project, traces cross-file causes, and proposes targeted fixes.</p></div>
          <button onClick={onClose} className="ml-auto rounded-lg p-2 text-zinc-400 hover:bg-white/5 hover:text-white" aria-label="Close debugger"><X size={18} /></button>
        </header>
        <div className="border-b border-white/10 bg-rose-500/[0.04] px-5 py-2 text-xs text-zinc-400"><span className="font-medium text-zinc-200">Active project:</span> {projectBrief?.trim() ? projectBrief.trim().slice(0, 100) : projectId} <span className="ml-2 text-zinc-600">({projectId})</span></div>
        <div className="min-h-0 space-y-4 overflow-auto p-5">
          <div className="rounded-xl border border-white/10 bg-white/[0.025] p-3 text-xs text-zinc-400">
            <div className="mb-1 flex items-center gap-2 text-zinc-200"><ClipboardPaste size={14} className="text-rose-300" /> Where to copy the error from</div>
            Browser DevTools Console (F12), terminal output, Vite/React build, backend traceback, or API response. Include the full message and stack trace when available.
          </div>
          <label htmlFor="debug-error" className="block text-sm font-medium text-zinc-200">Error message / stack trace</label>
          <textarea id="debug-error" value={errorText} onChange={(e) => setErrorText(e.target.value.slice(0, 15000))} maxLength={15000} rows={8} placeholder={'Paste the complete error here…\n\nExample: TypeError: Cannot read properties of undefined…'} className="field min-h-40 w-full resize-y font-mono text-xs leading-5" />
          <div className="flex flex-wrap items-center gap-3 text-xs text-zinc-500"><span>{errorText.length.toLocaleString()} / 15,000 characters</span><span>•</span><span>All readable source/config files in this workspace project are analyzed in bounded batches; tests may be read but are never edited.</span></div>
          <label className="flex cursor-pointer items-start gap-2 rounded-xl border border-white/10 p-3 text-sm text-zinc-300">
            <input type="checkbox" checked={applyFixes} onChange={(e) => setApplyFixes(e.target.checked)} className="mt-1 accent-rose-500" />
            <span><span className="block font-medium text-white">Apply safe fixes automatically</span><span className="mt-0.5 block text-xs text-zinc-500">Uses exact-match patches, avoids tests/secrets/lockfiles, and rolls back changes if new detectable syntax errors appear.</span></span>
          </label>
          {error && <p role="alert" className="rounded-lg border border-red-500/20 bg-red-500/10 p-3 text-sm text-red-300">{error}</p>}
          <div className="flex flex-wrap items-center gap-2">
            <button className="btn-primary" onClick={run} disabled={busy || errorText.trim().length < 5}>{busy ? <><Loader2 size={15} className="animate-spin" /> Analyzing project…</> : <><Wrench size={15} /> Analyze &amp; Fix</>}</button>
            <button className="btn-ghost" onClick={() => { setErrorText(''); setResult(null); setError('') }} disabled={busy}>Clear</button>
            {busy && <span className="text-xs text-zinc-500">This may take a little time while the model inspects the code.</span>}
          </div>
          {result && <section className="space-y-3 border-t border-white/10 pt-4" aria-live="polite">
            <div className="flex items-start gap-2"><CheckCircle2 size={18} className="mt-0.5 shrink-0 text-emerald-400" /><div><h3 className="font-medium text-white">Analysis result</h3><p className="mt-1 text-sm leading-6 text-zinc-300">{result.summary}</p><p className="mt-1 text-xs text-zinc-500">Reviewed {result.files_scanned} relevant project files.</p></div></div>
            {result.diagnostics.length > 0 && <div className="space-y-2"><h4 className="text-xs font-semibold uppercase tracking-wider text-zinc-500">Findings</h4>{result.diagnostics.map((d, i) => <div key={`${d.file}-${i}`} className="rounded-lg border border-white/10 bg-black/20 p-3"><div className="flex items-center gap-2 text-xs"><AlertTriangle size={13} className={d.severity === 'error' ? 'text-rose-300' : 'text-amber-300'} /><span className="uppercase text-zinc-400">{d.severity || 'info'}</span><span className="ml-auto truncate text-zinc-500">{d.file}{d.line ? `:${d.line}` : ''}</span></div><p className="mt-1 text-sm text-zinc-300">{d.message}</p></div>)}</div>}
            {result.applied.length > 0 && <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/[0.06] p-3"><h4 className="mb-2 flex items-center gap-2 text-sm font-medium text-emerald-300"><ShieldCheck size={15} /> Applied fixes ({result.applied.length})</h4>{result.applied.map((p, i) => <p key={`${p.file}-${i}`} className="mt-1 text-xs text-zinc-300"><code>{p.file}</code> — {p.reason}</p>)}<p className="mt-2 text-xs text-zinc-500">Run your app/build again to verify the original error is resolved.</p></div>}
            {result.applied.length === 0 && <p className="text-sm text-zinc-400">{applyFixes ? 'No safe automatic patch was applied. Review the findings and verification suggestions below.' : 'Analysis-only mode: no files were changed.'}</p>}
            {result.rejected.length > 0 && <div className="space-y-1 rounded-lg border border-amber-500/20 bg-amber-500/[0.06] p-3 text-xs text-amber-200">{result.rejected.map((r, i) => <p key={i}>{r}</p>)}</div>}
            {result.verification.length > 0 && <div><h4 className="mb-1 text-xs font-semibold uppercase tracking-wider text-zinc-500">Next verification steps</h4><ul className="list-disc space-y-1 pl-5 text-xs text-zinc-400">{result.verification.map((v, i) => <li key={i}>{v}</li>)}</ul></div>}
          </section>}
        </div>
        <footer className="flex items-center justify-between border-t border-white/10 px-5 py-3"><span className="text-[11px] text-zinc-600">Protected files and credentials are excluded from analysis.</span><button className="btn-ghost" onClick={onClose}>Close</button></footer>
      </div>
    </div>
  )
}

import { useCallback, useEffect, useState, type ReactNode } from 'react'
import { RefreshCw, ScanSearch } from 'lucide-react'
import { api, type LanguageAnalysis, type LanguageAnalysisIssue, type ProjectScan } from '../services/api'

export default function ProjectScanPanel({ id }: { id: string | null }) {
  const [scan, setScan] = useState<ProjectScan | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [analysis, setAnalysis] = useState<LanguageAnalysis | null>(null)
  const [analysisBusy, setAnalysisBusy] = useState(false)
  const [analysisError, setAnalysisError] = useState('')
  const [deep, setDeep] = useState(false)

  const refresh = useCallback(async () => {
    if (!id) { setScan(null); setAnalysis(null); return }
    setBusy(true); setError('')
    try { setScan(await api.scanProject(id)) } catch (e) { setError((e as Error).message) } finally { setBusy(false) }
  }, [id])

  const analyze = useCallback(async () => {
    if (!id) return
    setAnalysisBusy(true); setAnalysisError('')
    try { setAnalysis(await api.analyzeProject(id, deep)) } catch (e) { setAnalysisError((e as Error).message) } finally { setAnalysisBusy(false) }
  }, [id, deep])

  useEffect(() => { void refresh() }, [refresh])
  if (!id) return <p className="text-zinc-600">Select a project to inspect its structure.</p>

  return (
    <div className="space-y-3 font-sans text-xs">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="text-zinc-400">Project structure and technology map</p>
        <button className="btn-ghost !px-2 !py-1 text-xs" disabled={busy} onClick={() => void refresh()}><RefreshCw size={13} />{busy ? 'Scanning' : 'Refresh scan'}</button>
      </div>
      {error && <p role="alert" className="text-red-300">{error}</p>}
      {scan && <>
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
          <Metric label="Files scanned" value={scan.files_scanned} />
          <Metric label="Routes" value={scan.routes.length} />
          <Metric label="API endpoints" value={scan.api_endpoints.length} />
          <Metric label="Languages" value={scan.languages.length} />
        </div>
        <Group title="Frameworks"><Tokens values={scan.frameworks} fallback="No framework identified from available manifests." /></Group>
        <Group title="Languages">{scan.languages.map((x) => <p key={x.name} className="text-zinc-300">{x.name}<span className="ml-2 text-zinc-500">{x.files} file(s)</span></p>)}</Group>
        <Group title="Package managers"><Tokens values={scan.package_managers} fallback="No package manager lockfile found." /></Group>
        <Group title="Likely entry points"><Tokens values={scan.entry_points} fallback="No common entry point recognized." /></Group>
        <Group title="Frontend route hints"><Tokens values={scan.routes} fallback="No route declarations recognized; this is a static scan, not a route guarantee." /></Group>
        <Group title="API endpoint hints">
          {scan.api_endpoints.length === 0 ? <p className="text-zinc-500">No common REST route declaration recognized.</p> : scan.api_endpoints.slice(0, 40).map((x, i) => <p key={`${x.file}-${x.method}-${x.path}-${i}`} className="break-all text-zinc-300"><span className="mr-2 text-sky-300">{x.method}</span>{x.path}<span className="ml-2 text-zinc-600">{x.file}</span></p>)}
        </Group>
        <Group title="Project manifests">{Object.entries(scan.manifests).map(([path, m]) => <div key={path} className="mb-2 rounded border border-white/10 p-2"><p className="break-all text-zinc-200">{path}</p>{m.name && <p className="text-zinc-500">{m.name}</p>}{m.scripts && <p className="mt-1 break-words text-zinc-400">Scripts: {m.scripts.join(', ') || 'none'}</p>}{m.dependencies && <p className="mt-1 break-words text-zinc-400">Dependencies: {m.dependencies.slice(0, 25).join(', ')}{m.dependencies.length > 25 ? '…' : ''}</p>}{m.invalid_json && <p className="text-amber-300">Invalid JSON</p>}</div>)}</Group>
        {scan.warnings.map((w) => <p key={w} className="text-amber-300">{w}</p>)}
        <p className="text-zinc-600">This scan infers metadata and route hints. It does not prove that a route or feature works.</p>
      </>}

      <div className="space-y-3 rounded-lg border border-white/10 bg-white/[0.02] p-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div><h3 className="font-semibold text-zinc-200">Language &amp; code-quality analysis</h3><p className="mt-1 text-zinc-500">Syntax parsers, logic warnings, duplicated code hints and toolchain coverage.</p></div>
          <button className="btn-ghost !px-2 !py-1 text-xs" disabled={analysisBusy} onClick={() => void analyze()}><ScanSearch size={13} />{analysisBusy ? 'Analyzing…' : 'Analyze project'}</button>
        </div>
        <label className="flex items-start gap-2 text-zinc-400"><input className="mt-0.5 accent-sky-500" type="checkbox" checked={deep} onChange={(e) => setDeep(e.target.checked)} /><span><span className="text-zinc-300">Run installed compiler/build/lint/test checks</span><span className="mt-0.5 block text-zinc-600">Optional deeper checks can execute project-declared scripts. No dependencies are installed automatically.</span></span></label>
        {analysisError && <p role="alert" className="text-red-300">{analysisError}</p>}
        {analysis && <>
          <div className="flex flex-wrap items-center gap-2"><span className={`rounded border px-2 py-1 uppercase tracking-wide ${analysis.status === 'failed' ? 'border-red-500/30 text-red-300' : analysis.status === 'partial' ? 'border-amber-500/30 text-amber-300' : 'border-emerald-500/30 text-emerald-300'}`}>{analysis.status}</span><span className="text-zinc-400">{analysis.files_scanned} files · {analysis.languages.length} language groups</span><span className="text-zinc-500">{analysis.deep ? 'Deep checks requested' : 'Static pass'}</span></div>
          <p className="text-zinc-300">{analysis.summary}</p>
          <Group title="Language coverage">
            <div className="space-y-1.5">{analysis.languages.map((x) => <div key={x.name} className="flex flex-wrap items-center gap-x-3 gap-y-1"><span className="min-w-28 text-zinc-200">{x.name}</span><span className="text-zinc-500">{x.files} file(s)</span><span className="text-emerald-300">checked {x.checked}</span>{x.failed > 0 && <span className="text-red-300">failed {x.failed}</span>}{x.skipped > 0 && <span className="text-amber-300">tool needed / skipped {x.skipped}</span>}</div>)}</div>
          </Group>
          <Group title="Checks">
            <div className="space-y-2">{analysis.checks.map((c, i) => <div key={`${c.name}-${i}`} className="rounded border border-white/5 px-2 py-2"><div className="flex flex-wrap items-center gap-2"><span className={c.status === 'failed' ? 'text-red-300' : c.status === 'passed' ? 'text-emerald-300' : 'text-amber-300'}>{c.status}</span><span className="text-zinc-200">{c.name}</span>{c.language && <span className="text-zinc-600">{c.language}</span>}</div><p className="mt-1 break-words text-zinc-500">{c.detail}</p></div>)}</div>
          </Group>
          <AnalysisFindings title="Syntax / compiler issues" items={analysis.issues} empty="No errors were returned by the checks that actually ran. Skipped languages are not verified." />
          <AnalysisFindings title="Possible logic or redundancy" items={analysis.redundancy} empty="No redundancy/logic hints were found by the conservative heuristics." />
          {analysis.notes.map((note, i) => <p key={`${note}-${i}`} className="text-amber-300/80">{note}</p>)}
        </>}
      </div>
    </div>
  )
}

function Metric({ label, value }: { label: string; value: number }) {
  return <div className="rounded border border-white/10 bg-white/[0.025] p-3"><p className="text-lg text-white">{value}</p><p className="text-zinc-500">{label}</p></div>
}
function Group({ title, children }: { title: string; children: ReactNode }) {
  return <section className="space-y-1.5 rounded border border-white/10 p-3"><h3 className="text-[10px] font-semibold uppercase tracking-wider text-zinc-500">{title}</h3>{children}</section>
}
function Tokens({ values, fallback }: { values: string[]; fallback: string }) {
  return values.length ? <div className="flex flex-wrap gap-1.5">{values.map((v) => <span key={v} className="max-w-full break-all rounded bg-white/[0.06] px-2 py-1 text-zinc-300">{v}</span>)}</div> : <p className="text-zinc-500">{fallback}</p>
}
function AnalysisFindings({ title, items, empty }: { title: string; items: LanguageAnalysisIssue[]; empty: string }) {
  const label = (x: string) => x === 'error' ? 'text-red-300' : x === 'warning' ? 'text-amber-300' : 'text-zinc-500'
  return <Group title={`${title} (${items.length})`}>
    {items.length === 0 ? <p className="text-zinc-500">{empty}</p> : <div className="space-y-2">{items.slice(0, 50).map((x, i) => <div key={`${x.file}-${x.line}-${i}`} className="rounded border border-white/5 p-2"><div className="flex flex-wrap items-center gap-x-2 gap-y-1"><span className={label(x.severity)}>{x.severity}</span><span className="break-all text-zinc-300">{x.file || 'project'}{x.line ? `:${x.line}` : ''}</span><span className="text-zinc-600">{x.category}</span></div><p className="mt-1 break-words text-zinc-400">{x.message}</p>{x.tool && <p className="mt-1 text-zinc-600">Tool: {x.tool}</p>}</div>)}</div>}
  </Group>
}

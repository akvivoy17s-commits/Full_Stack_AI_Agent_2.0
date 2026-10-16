import type { Check, Report } from '../services/api'

const COL = {
  passed: 'border-emerald-500/30 bg-emerald-500/10 text-emerald-300',
  failed: 'border-red-500/30 bg-red-500/10 text-red-300',
  skipped: 'border-zinc-500/30 bg-zinc-500/10 text-zinc-400',
} as const
const VPS = ['desktop', 'tablet', 'mobile']

function Matrix({ checks }: { checks: Check[] }) {
  const names = [...new Set(checks.filter((c) => VPS.includes(c.viewport)).map((c) => c.name))]
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[420px] text-left text-xs">
        <caption className="sr-only">Browser checks per viewport</caption>
        <thead><tr className="text-zinc-500"><th scope="col" className="py-1 pr-3 font-medium">Check</th>{VPS.map((v) => <th key={v} scope="col" className="px-1 py-1 font-medium capitalize">{v}</th>)}</tr></thead>
        <tbody>
          {names.map((n) => (
            <tr key={n} className="border-t border-white/5">
              <th scope="row" className="py-1.5 pr-3 font-normal text-zinc-300">{n}</th>
              {VPS.map((v) => {
                const c = checks.find((x) => x.name === n && x.viewport === v)
                return <td key={v} className="px-1 py-1">{c ? <span title={c.detail} className={`chip ${COL[c.status]}`}>{c.status}</span> : <span className="text-zinc-700">–</span>}</td>
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default function ReportPanel({ report }: { report: Report | null }) {
  if (!report) return <p className="p-4 text-sm text-zinc-500">No test report yet. Use <b>Run browser tests</b> or <b>Verify</b>.</p>
  const build = report.checks.filter((c) => c.viewport === 'build' || c.viewport === 'static')
  const failed = report.checks.filter((c) => c.status === 'failed')
  return (
    <div className="space-y-4 p-3 text-sm">
      <p className="text-xs text-zinc-400" role="status">
        <b className="text-emerald-300">{report.counts.passed} passed</b> · <b className="text-red-300">{report.counts.failed} failed</b> ·{' '}
        <b className="text-zinc-300">{report.counts.skipped} not executed</b>. Skipped checks are never counted as passed.
      </p>
      {report.notes.length > 0 && <ul className="space-y-1">{report.notes.map((n, i) => <li key={i} className="rounded-md border border-amber-500/20 bg-amber-500/5 px-3 py-1.5 text-xs text-amber-300">{n}</li>)}</ul>}
      {build.length > 0 && (
        <section><h3 className="label">Build &amp; static</h3>
          <div className="flex flex-wrap gap-2">{build.map((c) => <span key={c.name} title={c.detail} className={`chip ${COL[c.status]}`}>{c.name}: {c.status}</span>)}</div></section>
      )}
      <section><h3 className="label">Browser (Playwright, local dev server)</h3><Matrix checks={report.checks} /></section>
      {failed.length > 0 && (
        <section><h3 className="label">Failed details</h3>
          <ul className="space-y-1">{failed.map((c, i) => <li key={i} className="rounded-md border border-red-500/20 bg-red-500/5 px-3 py-1.5 font-mono text-xs text-red-300">[{c.viewport}] {c.name}: {c.detail}</li>)}</ul></section>
      )}
      <section><h3 className="label">Accessibility findings ({report.a11y.length})</h3>
        {report.a11y.length === 0 ? <p className="text-xs text-zinc-500">None found by the automated rules (a subset of WCAG; manual testing is still needed).</p>
          : <ul className="space-y-1">{report.a11y.map((f, i) => <li key={i} className="rounded-md border border-white/10 px-3 py-1.5 text-xs text-zinc-300"><span className="text-accent">{f.rule}</span>{f.sid ? ` · ${f.sid}` : ''} — {f.msg}</li>)}</ul>}
      </section>
      <section><h3 className="label">Visual inspection (optional vision model)</h3>
        <p className="text-xs text-zinc-400">{report.vision.note}</p>
        {report.vision.findings.map((f, i) => <p key={i} className="mt-1 rounded-md border border-amber-500/20 bg-amber-500/5 px-3 py-1.5 text-xs text-amber-300">[{f.viewport}] {f.sid && `${f.sid}: `}{f.msg}</p>)}
      </section>
      <section><h3 className="label">Repair attempts ({report.repairs.length})</h3>
        {report.repairs.length === 0 ? <p className="text-xs text-zinc-500">No repairs ran in the last check.</p>
          : <ul className="space-y-1">{report.repairs.map((r, i) => (
            <li key={i} className="flex flex-wrap gap-2 rounded-md border border-white/10 px-3 py-1.5 text-xs text-zinc-300">
              <span className="chip border-white/10">#{r.attempt} {r.method}</span><span className={`chip ${r.outcome === 'fixed' ? COL.passed : COL.failed}`}>{r.outcome.replace('_', ' ')}</span>
              <span className="text-zinc-400">{r.sid}: {r.issue}</span></li>))}</ul>}
      </section>
    </div>
  )
}

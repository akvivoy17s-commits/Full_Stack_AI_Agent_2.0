import { useState } from 'react'
import { Play, Trash2 } from 'lucide-react'
import { api, type TerminalResult } from '../services/api'

type Entry = { command: string; result?: TerminalResult; error?: string }

export default function TerminalPanel({ id }: { id: string | null }) {
  const [command, setCommand] = useState('npm run build')
  const [entries, setEntries] = useState<Entry[]>([])
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  const run = async () => {
    if (!id || busy || !command.trim()) return
    const args = command.trim().split(/\s+/)
    const installs = args[0] === 'npm' && ['install', 'ci'].includes(args[1] ?? '')
    const confirm = installs && window.confirm('This command can download packages and modify node_modules. Run it?')
    if (installs && !confirm) return
    setBusy(true); setError('')
    try {
      const result = await api.terminalRun(id, args, 60, Boolean(confirm))
      setEntries((all) => [...all, { command: command.trim(), result }].slice(-30))
    } catch (e) {
      const message = (e as Error).message
      setEntries((all) => [...all, { command: command.trim(), error: message }].slice(-30))
      setError(message)
    } finally { setBusy(false) }
  }

  return (
    <div className="flex h-full min-h-0 flex-col gap-2 font-mono text-xs">
      <p className="text-zinc-500">Restricted terminal: commands are executed without a shell. Try <code>npm run build</code>, <code>npm run typecheck</code>, <code>npm test</code>, or <code>python -m pytest -q</code>.</p>
      <form className="flex gap-2" onSubmit={(e) => { e.preventDefault(); void run() }}>
        <label className="sr-only" htmlFor="ide-terminal-command">Command</label>
        <input id="ide-terminal-command" className="field min-w-0 flex-1 font-mono" value={command} onChange={(e) => setCommand(e.target.value)} placeholder="npm run build" disabled={!id || busy} />
        <button className="btn-primary !px-3 !py-2" type="submit" disabled={!id || busy || !command.trim()}><Play size={13} />{busy ? 'Running' : 'Run'}</button>
        <button className="btn-ghost !px-3 !py-2" type="button" title="Clear terminal output" onClick={() => { setEntries([]); setError('') }}><Trash2 size={13} /></button>
      </form>
      {!id && <p className="text-zinc-600">Select a project before running commands.</p>}
      {error && <p role="status" className="text-amber-300">Last command was rejected or failed: {error}</p>}
      <div className="min-h-0 flex-1 space-y-3 overflow-auto rounded-md border border-white/10 bg-black/30 p-3" role="log" aria-live="polite">
        {entries.length === 0 && <p className="text-zinc-600">No terminal commands yet.</p>}
        {entries.map((entry, i) => (
          <div key={`${entry.command}-${i}`} className="border-b border-white/5 pb-3 last:border-b-0">
            <p className="text-sky-300"><span className="mr-2 text-zinc-600">$</span>{entry.command}</p>
            {entry.result && <p className={entry.result.ok ? 'mt-1 text-emerald-300' : 'mt-1 text-amber-300'}>Exit code {entry.result.code}{entry.result.timed_out ? ' · timed out' : ''}</p>}
            {(entry.result?.out || entry.error) && <pre className="mt-1 whitespace-pre-wrap break-words text-zinc-300">{entry.result?.out || entry.error}</pre>}
          </div>
        ))}
      </div>
    </div>
  )
}

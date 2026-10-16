import { useCallback, useEffect, useState } from 'react'
import { FileCode2, Save } from 'lucide-react'
import { api } from '../services/api'

const EDITABLE = /\.(html|css|js|json|md|svg|txt)$/i

export default function CodePanel({ id, files, version, onSaved }: { id: string; files: string[]; version: number; onSaved: () => void }) {
  const [path, setPath] = useState('')
  const [text, setText] = useState('')
  const [orig, setOrig] = useState('')
  const [issues, setIssues] = useState<string[]>([])
  const [msg, setMsg] = useState('')
  const visible = files.filter((f) => !f.startsWith('.agent/'))
  const current = path && visible.includes(path) ? path : visible.includes('index.html') ? 'index.html' : visible[0] ?? ''

  useEffect(() => {
    if (!current) return
    let live = true
    api.file(id, current).then((r) => { if (live) { setText(r.content); setOrig(r.content); setIssues(r.issues); setMsg('') } }).catch((e) => live && setMsg(e.message))
    return () => { live = false }
  }, [id, current, version])

  const save = useCallback(async () => {
    try { const r = await api.saveFile(id, current, text); setOrig(text); setIssues(r.issues); setMsg('Saved'); onSaved() } catch (e) { setMsg((e as Error).message) }
  }, [id, current, text, onSaved])

  const dirty = text !== orig
  return (
    <div className="flex h-full min-h-0 flex-col md:flex-row">
      <ul className="max-h-32 shrink-0 overflow-auto border-b border-white/10 p-2 md:max-h-none md:w-48 md:border-b-0 md:border-r" aria-label="Project files">
        {visible.length === 0 && <li className="p-2 text-sm text-zinc-600">No files yet.</li>}
        {visible.map((f) => (
          <li key={f}><button onClick={() => setPath(f)} className={`flex w-full items-center gap-2 truncate rounded-md px-2 py-1.5 text-left text-xs ${f === current ? 'bg-accent/15 text-white' : 'text-zinc-400 hover:bg-white/5'}`}>
            <FileCode2 size={13} className="shrink-0 text-accent" /><span className="truncate">{f}</span></button></li>
        ))}
      </ul>
      <div className="flex min-h-0 min-w-0 flex-1 flex-col">
        <div className="flex items-center gap-3 border-b border-white/10 px-3 py-1.5 text-xs">
          <span className="truncate text-zinc-400">{current || 'no file'}{dirty && <b className="ml-1 text-accentSoft">● unsaved</b>}</span>
          <span className="ml-auto text-zinc-500">{msg}</span>
          <button className="btn-ghost !px-2 !py-1 text-xs" disabled={!dirty || !EDITABLE.test(current)} onClick={save}><Save size={13} /> Save</button>
        </div>
        <textarea aria-label="Code editor" spellCheck={false} value={text} readOnly={!current || !EDITABLE.test(current)}
          onChange={(e) => setText(e.target.value)} onKeyDown={(e) => { if ((e.ctrlKey || e.metaKey) && e.key === 's') { e.preventDefault(); if (dirty) save() } }}
          className="min-h-0 flex-1 resize-none bg-black/40 p-3 font-mono text-xs leading-5 text-zinc-300 focus:outline-none" />
        {issues.length > 0 && <ul className="max-h-20 overflow-auto border-t border-amber-500/20 bg-amber-500/5 px-3 py-1.5 text-xs text-amber-300">{issues.map((i) => <li key={i}>⚠ {i}</li>)}</ul>}
      </div>
    </div>
  )
}

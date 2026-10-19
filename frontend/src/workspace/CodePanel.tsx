import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import Editor, { type OnMount } from '@monaco-editor/react'
import type { editor as MonacoEditorApi } from 'monaco-editor'
import {
  Braces, ChevronRight, Code2, FileCode2, FileJson, FileText, FileType2,
  FilePlus2, Folder, Save, Search, Trash2, X, Circle, Check, RotateCcw,
} from 'lucide-react'
import { api } from '../services/api'

// Keep in sync with the backend editable-extension allowlist. Binary assets are deliberately excluded.
const EDITABLE = /\.(html?|css|scss|sass|less|js|jsx|mjs|cjs|ts|tsx|json|jsonc|md|mdx|svg|txt|xml|ya?ml|toml|py|sql|sh|bat|ps1|vue|svelte|go|rs|java|kt|php|rb|example|sample|template|dist|properties|ini|conf|gitignore|dockerignore)$/i
const SPECIAL_TEXT_FILES = /(^|\/)(Dockerfile|Makefile|Procfile|\.gitignore|\.dockerignore|\.editorconfig)$/i
const isEditable = (path: string) => EDITABLE.test(path) || SPECIAL_TEXT_FILES.test(path)

function FileIcon({ path }: { path: string }) {
  const ext = path.split('.').pop()?.toLowerCase() ?? ''
  const cls = 'shrink-0'
  if (['json', 'jsonc'].includes(ext)) return <FileJson size={14} className={`${cls} text-[#dcb67a]`} />
  if (['md', 'mdx', 'txt'].includes(ext)) return <FileText size={14} className={`${cls} text-[#75beff]`} />
  if (['ts', 'tsx', 'js', 'jsx', 'py', 'go', 'rs', 'java', 'kt', 'php', 'rb'].includes(ext)) return <FileCode2 size={14} className={`${cls} text-[#75beff]`} />
  if (['html', 'htm', 'svg', 'xml'].includes(ext)) return <Code2 size={14} className={`${cls} text-[#e37933]`} />
  if (['css', 'scss', 'sass', 'less'].includes(ext)) return <FileType2 size={14} className={`${cls} text-[#c586c0]`} />
  return <FileText size={14} className={`${cls} text-[#9da5b4]`} />
}

function languageOf(path: string) {
  const ext = path.split('.').pop()?.toLowerCase() ?? ''
  const map: Record<string, string> = {
    html: 'HTML', htm: 'HTML', css: 'CSS', scss: 'SCSS', sass: 'Sass', less: 'Less', js: 'JavaScript', jsx: 'JavaScript React',
    ts: 'TypeScript', tsx: 'TypeScript React', json: 'JSON', jsonc: 'JSON with Comments', md: 'Markdown', mdx: 'MDX', py: 'Python',
    sql: 'SQL', sh: 'Shell Script', bat: 'Batch', ps1: 'PowerShell', vue: 'Vue', svelte: 'Svelte', go: 'Go', rs: 'Rust', java: 'Java',
    kt: 'Kotlin', php: 'PHP', rb: 'Ruby', yaml: 'YAML', yml: 'YAML', toml: 'TOML', xml: 'XML', svg: 'SVG', txt: 'Plain Text',
    example: 'Environment Template', sample: 'Text', template: 'Text', dist: 'Text',
  }
  if (/\.env\.(example|sample|template|dist)$/i.test(path)) return 'Environment Template'
  if (SPECIAL_TEXT_FILES.test(path)) return 'Plain Text'
  return (map[ext] ?? ext.toUpperCase()) || 'Plain Text'
}

export default function CodePanel({ id, files, version, onSaved, projectName }: { id: string; files: string[]; version: number; onSaved: () => void | Promise<void>; projectName?: string }) {
  const [path, setPath] = useState<string | null>(null)
  const [openPaths, setOpenPaths] = useState<string[]>([])
  const [text, setText] = useState('')
  const [orig, setOrig] = useState('')
  const [issues, setIssues] = useState<string[]>([])
  const [msg, setMsg] = useState('')
  const [filter, setFilter] = useState('')
  const [collapsed, setCollapsed] = useState<Set<string>>(() => new Set())
  const [cursor, setCursor] = useState({ line: 1, column: 1 })
  const [saving, setSaving] = useState(false)
  const editorRef = useRef<MonacoEditorApi.IStandaloneCodeEditor | null>(null)
  const saveRef = useRef<() => Promise<void>>(async () => {})

  const visible = useMemo(() => files.filter((f) => !f.startsWith('.agent/') && isEditable(f)).sort((a, b) => a.localeCompare(b)), [files])
  const current = path === null ? (visible.includes('index.html') ? 'index.html' : visible[0] ?? '') : (path && visible.includes(path) ? path : '')
  const dirty = text !== orig

  useEffect(() => {
    setPath(null)
    setOpenPaths([])
    setText('')
    setOrig('')
    setIssues([])
    setMsg('')
    setFilter('')
    setCollapsed(new Set())
  }, [id])

  useEffect(() => {
    if (path && !visible.includes(path)) setPath(null)
  }, [path, visible])
  useEffect(() => {
    const onProjectFilesChanged = () => { void onSaved() }
    window.addEventListener('agent-project-files-changed', onProjectFilesChanged)
    return () => window.removeEventListener('agent-project-files-changed', onProjectFilesChanged)
  }, [onSaved])
  const filtered = useMemo(() => visible.filter((f) => f.toLowerCase().includes(filter.trim().toLowerCase())), [visible, filter])
  const treeRows = useMemo(() => {
    type Dir = { path: string; name: string; dirs: Map<string, Dir>; files: string[] }
    type Row = { kind: 'folder' | 'file'; path: string; name: string; depth: number }
    const root: Dir = { path: '', name: '', dirs: new Map(), files: [] }
    for (const file of filtered) {
      const parts = file.split('/')
      let currentDir = root
      let accumulated = ''
      for (const segment of parts.slice(0, -1)) {
        accumulated = accumulated ? `${accumulated}/${segment}` : segment
        let next = currentDir.dirs.get(segment)
        if (!next) {
          next = { path: accumulated, name: segment, dirs: new Map(), files: [] }
          currentDir.dirs.set(segment, next)
        }
        currentDir = next
      }
      currentDir.files.push(file)
    }
    const rows: Row[] = []
    const walk = (dir: Dir, depth: number) => {
      for (const child of [...dir.dirs.values()].sort((a, b) => a.name.localeCompare(b.name))) {
        rows.push({ kind: 'folder', path: child.path, name: child.name, depth })
        if (filter.trim() || !collapsed.has(child.path)) walk(child, depth + 1)
      }
      for (const file of dir.files.sort((a, b) => a.localeCompare(b))) {
        rows.push({ kind: 'file', path: file, name: file.split('/').pop() ?? file, depth })
      }
    }
    walk(root, 0)
    return rows
  }, [filtered, filter, collapsed])

  useEffect(() => {
    if (!current) { setText(''); setOrig(''); setIssues([]); setMsg(''); return }
    let live = true
    api.file(id, current).then((r) => {
      if (live) { setPath(current); setText(r.content); setOrig(r.content); setIssues(r.issues); setMsg(''); setCursor({ line: 1, column: 1 }) }
    }).catch((e) => live && setMsg((e as Error).message))
    return () => { live = false }
  }, [id, current, version])

  useEffect(() => {
    if (current && visible.includes(current)) setOpenPaths((prev) => prev.includes(current) ? prev : [...prev, current])
  }, [current, visible])

  const save = useCallback(async () => {
    if (!current || !dirty || !isEditable(current) || saving) return
    setSaving(true); setMsg('Saving…')
    try {
      const r = await api.saveFile(id, current, text)
      setOrig(text); setIssues(r.issues); setMsg('Saved'); await onSaved()
    } catch (e) { setMsg((e as Error).message) }
    finally { setSaving(false) }
  }, [id, current, dirty, saving, text, onSaved])

  useEffect(() => { saveRef.current = save }, [save])

  const onEditorMount: OnMount = (instance, monaco) => {
    editorRef.current = instance
    instance.onDidChangeCursorPosition(({ position }) => setCursor({ line: position.lineNumber, column: position.column }))
    instance.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyS, () => { void saveRef.current() })
  }

  const monacoLanguage = (file: string): string => {
    const lower = file.toLowerCase()
    if (/\.(tsx)$/.test(lower)) return 'typescript'
    if (/\.(jsx)$/.test(lower)) return 'javascript'
    const ext = lower.split('.').pop() ?? ''
    const map: Record<string, string> = {
      html: 'html', htm: 'html', css: 'css', scss: 'scss', js: 'javascript', mjs: 'javascript', cjs: 'javascript',
      ts: 'typescript', json: 'json', jsonc: 'json', md: 'markdown', mdx: 'markdown', py: 'python', sql: 'sql',
      sh: 'shell', bat: 'bat', ps1: 'powershell', go: 'go', rs: 'rust', java: 'java', kt: 'kotlin', php: 'php',
      rb: 'ruby', yaml: 'yaml', yml: 'yaml', toml: 'ini', xml: 'xml', svg: 'xml', txt: 'plaintext', vue: 'html',
      svelte: 'html', example: 'plaintext', sample: 'plaintext', template: 'plaintext', dist: 'plaintext',
    }
    if (SPECIAL_TEXT_FILES.test(file)) return 'plaintext'
    return map[ext] ?? 'plaintext'
  }

  const selectFile = (next: string) => {
    if (next === current) return
    if (dirty && !window.confirm(`Save changes to ${current} before opening another file?\nChoose Cancel to keep editing this file. Choose OK to discard unsaved changes.`)) return
    setPath(next)
    setOpenPaths((prev) => prev.includes(next) ? prev : [...prev, next])
  }

  const closeTab = (file: string) => {
    if (file === current && dirty && !window.confirm(`Discard unsaved changes to ${file}?`)) return
    const rest = openPaths.filter((p) => p !== file)
    setOpenPaths(rest)
    if (file === current) setPath(rest[rest.length - 1] ?? visible.find((f) => f !== file) ?? '')
  }


  const createFile = async () => {
    const entered = window.prompt('New file path relative to this project (example: src/components/NewComponent.tsx):', 'src/NewFile.tsx')
    if (entered === null) return
    const next = entered.trim().replace(/\\/g, '/')
    const parts = next.split('/')
    if (!next || next.length > 300 || next.startsWith('/') || /^[A-Za-z]:/.test(next) || parts.some((part) => !part || part === '.' || part === '..' || part.toLowerCase() === '.agent')) {
      setMsg('Enter a safe project-relative file path.')
      return
    }
    if (!isEditable(next)) {
      setMsg('Unsupported file type. Create a supported text/source file such as .tsx, .ts, .py, .html, .css or .json.')
      return
    }
    if (dirty && !window.confirm(`Discard unsaved changes to ${current || 'the current file'} before creating a new file?`)) return
    setMsg('Creating file…')
    try {
      const result = await api.createFile(id, next)
      setFilter('')
      setPath(result.path)
      setText(result.content)
      setOrig(result.content)
      setIssues(result.issues)
      setOpenPaths((prev) => prev.includes(result.path) ? prev : [...prev, result.path])
      await onSaved()
      setMsg('File created')
    } catch (e) {
      setMsg((e as Error).message)
    }
  }

  const deleteCurrentFile = async () => {
    if (!current) return
    const extra = dirty ? '\nUnsaved edits will also be lost.' : ''
    if (!window.confirm(`Permanently delete \"${current}\"?${extra}`)) return
    setMsg('Deleting file…')
    try {
      await api.deleteFile(id, current)
      const nextTab = openPaths.find((file) => file !== current && visible.includes(file)) ?? visible.find((file) => file !== current) ?? ''
      setOpenPaths((prev) => prev.filter((file) => file !== current))
      setPath(nextTab)
      setText('')
      setOrig('')
      setIssues([])
      await onSaved()
      setMsg('File deleted')
    } catch (e) {
      setMsg((e as Error).message)
    }
  }

  const currentExtOk = Boolean(current && isEditable(current))

  return (
    <div className="flex h-full min-h-0 min-w-0 flex-col bg-[#1e1e1e]">
      {/* Explorer file tree */}
      <div className="flex min-h-0 flex-1">
        <aside className="flex w-[218px] shrink-0 flex-col border-r border-[#333] bg-[#181818]">
          <div className="flex h-9 shrink-0 items-center gap-1 px-2 text-[11px] font-semibold uppercase tracking-[.12em] text-[#cccccc]">
            <span>Explorer</span>
            <span className="ml-auto mr-1 text-[10px] font-normal tracking-normal text-[#777]">{visible.length}</span>
            <button type="button" onClick={() => void createFile()} title="New file" aria-label="Create new file" className="grid h-6 w-6 place-items-center rounded text-[#a7a7a7] hover:bg-white/10 hover:text-white focus:outline-none focus-visible:ring-1 focus-visible:ring-[#007acc]"><FilePlus2 size={14} /></button>
            <button type="button" onClick={() => void deleteCurrentFile()} disabled={!current} title={current ? `Delete ${current}` : 'Select a file to delete'} aria-label="Delete selected file" className="grid h-6 w-6 place-items-center rounded text-[#a7a7a7] hover:bg-red-500/15 hover:text-[#f48771] disabled:cursor-not-allowed disabled:opacity-30 focus:outline-none focus-visible:ring-1 focus-visible:ring-[#007acc]"><Trash2 size={14} /></button>
          </div>
          <div className="flex h-8 shrink-0 items-center gap-2 border-y border-[#2b2b2b] px-2 text-[10px] font-semibold uppercase tracking-wide text-[#a6a6a6]">
            <ChevronRight size={13} className="rotate-90" /><Folder size={13} className="text-[#dcb67a]" /><span className="truncate">{projectName || id}</span>
          </div>
          <label className="mx-2 my-2 flex h-7 items-center gap-1.5 rounded border border-[#3c3c3c] bg-[#252526] px-2 text-[#888] focus-within:border-[#3c3c3c]">
            <Search size={13} /><input aria-label="Filter project files" value={filter} onChange={(e) => setFilter(e.target.value)} placeholder="Filter files" className="ide-file-filter-input w-full min-w-0 bg-transparent text-xs text-[#ddd] outline-none focus:outline-none focus-visible:outline-none placeholder:text-[#666]" />
          </label>
          <div className="min-h-0 flex-1 overflow-auto pb-2 text-[12px]">
            {visible.length === 0 && <p className="px-3 py-4 text-xs leading-5 text-[#777]">No editable source files yet. Generate the project or refresh after files are created.</p>}
            {visible.length > 0 && filtered.length === 0 && <p className="px-3 py-3 text-xs text-[#777]">No files match “{filter}”.</p>}
            {treeRows.map((row) => row.kind === 'folder' ? (
              <button key={`folder:${row.path}`} type="button" title={row.path} aria-expanded={filter.trim() ? true : !collapsed.has(row.path)}
                onClick={() => setCollapsed((prev) => { const next = new Set(prev); if (next.has(row.path)) next.delete(row.path); else next.add(row.path); return next })}
                className="flex h-[25px] w-full items-center gap-1.5 overflow-hidden px-2 pr-2 text-left text-[#cccccc] hover:bg-white/[0.05]"
                style={{ paddingLeft: 7 + Math.min(row.depth, 6) * 11 }}>
                <ChevronRight size={12} className={`shrink-0 transition-transform ${filter.trim() || !collapsed.has(row.path) ? 'rotate-90' : ''}`} />
                <Folder size={14} className="shrink-0 text-[#dcb67a]" /><span className="truncate">{row.name}</span>
              </button>
            ) : (
              <button key={`file:${row.path}`} type="button" title={row.path} onClick={() => selectFile(row.path)} aria-current={current === row.path}
                className={`flex h-[25px] w-full items-center gap-1.5 overflow-hidden border-l-2 pr-2 text-left ${current === row.path ? 'border-[#007acc] bg-[#37373d] text-white' : 'border-transparent text-[#cccccc] hover:bg-white/[0.05]'}`}
                style={{ paddingLeft: 10 + Math.min(row.depth, 6) * 11 }}>
                <FileIcon path={row.path} /><span className="truncate">{row.name}</span>
              </button>
            ))}
          </div>
        </aside>

        {/* Main editor + tabs */}
        <section className="flex min-h-0 min-w-0 flex-1 flex-col">
          <div className="flex h-9 shrink-0 items-stretch overflow-x-auto border-b border-[#333] bg-[#252526]" role="tablist" aria-label="Open files">
            {openPaths.filter((f) => visible.includes(f)).map((file) => (
              <div key={file} role="presentation" className={`group flex max-w-[220px] shrink-0 items-center border-r border-[#333] ${file === current ? 'border-t border-t-[#007acc] bg-[#1e1e1e]' : 'bg-[#2d2d2d]'}`}>
                <button role="tab" aria-selected={file === current} title={file} onClick={() => selectFile(file)} className={`flex min-w-0 items-center gap-2 px-3 text-xs ${file === current ? 'text-white' : 'text-[#999] hover:text-[#ddd]'}`}>
                  <FileIcon path={file} /><span className="truncate">{file.split('/').pop()}</span>{file === current && dirty && <Circle size={7} className="shrink-0 fill-[#cccccc] text-[#cccccc]" />}
                </button>
                <button type="button" title={`Close ${file}`} aria-label={`Close ${file}`} onClick={() => closeTab(file)} className="mr-1 rounded p-1 text-[#858585] opacity-0 hover:bg-white/10 hover:text-white group-hover:opacity-100 focus:opacity-100"><X size={12} /></button>
              </div>
            ))}
            {openPaths.length === 0 && <div className="flex items-center gap-2 px-3 text-xs text-[#777]"><Braces size={13} /> Editor</div>}
          </div>

          <div className="flex h-7 shrink-0 items-center gap-1 border-b border-[#2b2b2b] bg-[#1e1e1e] px-3 text-[11px] text-[#858585]">
            <span className="truncate">{current ? current.split('/').join(' › ') : 'No file selected'}</span>
            {dirty && <span className="rounded bg-[#6e4b00]/40 px-1.5 py-0.5 text-[10px] text-[#e8c98c]">Unsaved</span>}
            <span className="ml-auto truncate" role="status">{msg}</span>
            <button type="button" onClick={() => { setText(orig); setIssues([]); setMsg('Changes discarded') }} disabled={!dirty || saving} title="Discard unsaved changes" aria-label="Discard unsaved changes" className="rounded p-1 text-[#858585] hover:bg-white/10 hover:text-white disabled:opacity-30"><RotateCcw size={13} /></button>
            <button type="button" onClick={save} disabled={!dirty || !currentExtOk || saving} title="Save (Ctrl+S)" aria-label="Save file" className="inline-flex items-center gap-1 rounded bg-[#0e639c] px-2 py-1 text-[11px] text-white hover:bg-[#1177bb] disabled:cursor-not-allowed disabled:opacity-40"><Save size={12} />Save</button>
          </div>

          {current ? (
            <div className="min-h-0 min-w-0 flex-1 bg-[#1e1e1e]" aria-label={`Code editor: ${current}`}>
              <Editor
                path={current}
                language={monacoLanguage(current)}
                theme="vs-dark"
                value={text}
                onChange={(value) => setText(value ?? '')}
                onMount={onEditorMount}
                height="100%"
                options={{
                  automaticLayout: true,
                  minimap: { enabled: true, scale: 1 },
                  fontFamily: 'Consolas, "Cascadia Code", "Courier New", monospace',
                  fontSize: 12,
                  lineHeight: 21,
                  tabSize: 2,
                  insertSpaces: true,
                  wordWrap: 'off',
                  scrollBeyondLastLine: false,
                  renderWhitespace: 'selection',
                  lineNumbers: 'on',
                  folding: true,
                  glyphMargin: true,
                  roundedSelection: false,
                  overviewRulerBorder: false,
                  hideCursorInOverviewRuler: true,
                  smoothScrolling: true,
                  padding: { top: 10, bottom: 10 },
                  contextmenu: true,
                  readOnly: false,
                }}
              />
            </div>
          ) : (
            <div className="grid min-h-0 flex-1 place-items-center p-5 text-center text-sm text-[#777]">
              <div><Code2 size={28} className="mx-auto mb-3 text-[#555]" /><p>Select a file from Explorer to start editing.</p></div>
            </div>
          )}

          {issues.length > 0 && (
            <div className="max-h-24 shrink-0 overflow-auto border-t border-[#5f5128] bg-[#332d1d] px-3 py-1.5 text-[11px] text-[#e8c98c]">
              {issues.map((issue, n) => <p key={`${n}-${issue}`} className="py-0.5">⚠ {issue}</p>)}
            </div>
          )}
          <div className="flex h-[22px] shrink-0 items-center gap-3 bg-[#007acc] px-2 text-[10px] text-white">
            <span>{current ? languageOf(current) : 'Plain Text'}</span><span>UTF-8</span><span>LF</span><span className="ml-auto">Ln {cursor.line}, Col {cursor.column}</span>
            <span>{dirty ? 'Modified' : 'Saved'}</span>
            {msg === 'Saved' && <Check size={11} />}
          </div>
        </section>
      </div>
    </div>
  )
}

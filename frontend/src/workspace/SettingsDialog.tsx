import { useEffect, useState } from 'react'
import { X, PlugZap } from 'lucide-react'
import { api, type OllamaStatus, type Settings } from '../services/api'

export default function SettingsDialog({ models, onClose, onSaved }: { models: string[]; onClose: () => void; onSaved: () => void }) {
  const [s, setS] = useState<Settings | null>(null)
  const [check, setCheck] = useState<OllamaStatus | null>(null)
  const [msg, setMsg] = useState('')
  useEffect(() => { api.settings().then(setS).catch((e) => setMsg(e.message)) }, [])
  useEffect(() => {
    const k = (e: KeyboardEvent) => e.key === 'Escape' && onClose()
    window.addEventListener('keydown', k)
    return () => window.removeEventListener('keydown', k)
  }, [onClose])
  if (!s) return <Shell onClose={onClose}><p className="p-6 text-sm text-zinc-400">{msg || 'Loading settings…'}</p></Shell>

  const set = <K extends keyof Settings>(k: K, v: Settings[K]) => setS({ ...s, [k]: v })
  const oa = s.provider === 'openai'
  const test = async () => { setMsg(''); try { setCheck(await api.ollamaCheck(oa ? s.openai_base_url : s.ollama_base_url, oa ? s.openai_model : s.ollama_model, s.provider)) } catch (e) { setMsg((e as Error).message) } }
  const save = async () => { try { await api.saveSettings({ ...s, api_key_set: undefined } as Settings); onSaved(); onClose() } catch (e) { setMsg((e as Error).message) } }
  const num = (k: 'timeout_s' | 'num_ctx' | 'max_concurrency' | 'max_repair_loops' | 'max_retries') => (e: React.ChangeEvent<HTMLInputElement>) => set(k, Number(e.target.value))

  return (
    <Shell onClose={onClose}>
      <div className="space-y-4 p-5">
        <div className="grid gap-3 sm:grid-cols-3">
          <div><label className="label" htmlFor="s-prov">Provider</label>
            <select id="s-prov" className="field" value={s.provider} onChange={(e) => set('provider', e.target.value as Settings['provider'])}>
              <option value="ollama">Ollama (local)</option><option value="openai">OpenAI-compatible</option>
            </select></div>
          <div className="sm:col-span-2"><label className="label" htmlFor="s-url">{oa ? 'API base URL' : 'Ollama endpoint'}</label>
            <input id="s-url" className="field" value={oa ? s.openai_base_url : s.ollama_base_url} onChange={(e) => set(oa ? 'openai_base_url' : 'ollama_base_url', e.target.value)} /></div>
        </div>
        {oa && <p className={`text-xs ${s.api_key_set ? 'text-emerald-300' : 'text-amber-300'}`}>{s.api_key_set ? 'API key found in the backend environment.' : 'No API key found. Set LLM_API_KEY (or OPENAI_API_KEY) in the backend environment and restart. Keys are never entered or stored here.'}</p>}
        <div className="grid gap-3 sm:grid-cols-2">
          <div><label className="label" htmlFor="s-model">Model</label><input id="s-model" list="models" className="field" value={oa ? s.openai_model : s.ollama_model} onChange={(e) => set(oa ? 'openai_model' : 'ollama_model', e.target.value)} /></div>
          <div><label className="label" htmlFor="s-vision">Vision model (optional)</label><input id="s-vision" list="models" className="field" value={s.vision_model} placeholder="e.g. llava:7b" onChange={(e) => set('vision_model', e.target.value)} /></div>
        </div>
        <datalist id="models">{models.map((m) => <option key={m} value={m} />)}</datalist>
        <div>
          <label className="label" htmlFor="s-profile">Generation profile</label>
          <select id="s-profile" className="field" value={s.generation_profile} onChange={(e) => set('generation_profile', e.target.value as Settings['generation_profile'])}>
            <option value="fast">Fast — shorter local-model outputs</option>
            <option value="balanced">Balanced — speed and detail</option>
            <option value="quality">Quality — allow longer outputs</option>
          </select>
          <p className="mt-1 text-xs text-zinc-500">All profiles keep verification and security checks enabled. Fast is recommended for CPU-only laptops.</p>
        </div>
        <div className="grid gap-3 sm:grid-cols-5">
          <div><label className="label" htmlFor="s-to">Timeout (s)</label><input id="s-to" type="number" min={10} max={3600} className="field" value={s.timeout_s} onChange={num('timeout_s')} /></div>
          <div><label className="label" htmlFor="s-ctx">Context</label><input id="s-ctx" type="number" min={1024} max={32768} step={1024} className="field" value={s.num_ctx} onChange={num('num_ctx')} /></div>
          <div><label className="label" htmlFor="s-cc">Concurrency</label><input id="s-cc" type="number" min={1} max={4} className="field" value={s.max_concurrency} onChange={num('max_concurrency')} /></div>
          <div><label className="label" htmlFor="s-rp">Repair loops</label><input id="s-rp" type="number" min={0} max={5} className="field" value={s.max_repair_loops} onChange={num('max_repair_loops')} /></div>
          <div><label className="label" htmlFor="s-rt">Retries</label><input id="s-rt" type="number" min={0} max={4} className="field" value={s.max_retries} onChange={num('max_retries')} /></div>
        </div>
        {check && (
          <div role="status" className={`rounded-lg border p-3 text-sm ${check.reachable && check.model_available ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-300' : 'border-red-500/30 bg-red-500/10 text-red-300'}`}>
            {check.reachable && check.model_available ? `Connected. ${check.models.length ? `${check.models.length} model(s) available.` : 'Model list not exposed by this server.'}` : check.error}
          </div>
        )}
        {msg && <p role="alert" className="text-sm text-red-300">{msg}</p>}
        <div className="flex justify-end gap-2">
          <button className="btn-ghost" onClick={test}><PlugZap size={15} /> Test connection</button>
          <button className="btn-primary" onClick={save}>Save settings</button>
        </div>
      </div>
    </Shell>
  )
}

function Shell({ children, onClose }: { children: React.ReactNode; onClose: () => void }) {
  return (
    <div className="fixed inset-0 z-[60] grid place-items-center bg-black/70 p-4 backdrop-blur-sm" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
      <div role="dialog" aria-modal="true" aria-label="Settings" className="glass w-full max-w-2xl rounded-2xl bg-surface/90">
        <div className="flex items-center justify-between border-b border-white/10 px-5 py-3">
          <h2 className="font-display text-lg font-semibold text-white">Settings</h2>
          <button aria-label="Close settings" className="rounded-md p-1 text-zinc-400 hover:text-white" onClick={onClose}><X size={18} /></button>
        </div>
        {children}
      </div>
    </div>
  )
}

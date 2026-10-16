import type { Conn } from '../hooks/useOllama'

const MAP = {
  checking: ['bg-zinc-500', 'Checking…', 'border-white/10 text-zinc-400'],
  connected: ['bg-emerald-400', 'LLM connected', 'border-emerald-500/30 text-emerald-300'],
  'model-missing': ['bg-amber-400', 'Model not installed', 'border-amber-500/30 text-amber-300'],
  offline: ['bg-red-500', 'LLM offline', 'border-red-500/30 text-red-300'],
  'backend-down': ['bg-red-500', 'Backend offline', 'border-red-500/30 text-red-300'],
} as const

export default function ConnectionBadge({ conn, onClick }: { conn: Conn; onClick?: () => void }) {
  const [dot, label, cls] = MAP[conn.state]
  return (
    <button type="button" onClick={onClick} title={conn.detail} aria-live="polite"
      className={`chip bg-black/30 ${cls} hover:bg-white/5`}>
      <span className={`h-2 w-2 rounded-full ${dot} ${conn.state === 'connected' ? 'shadow-[0_0_8px_#34d399]' : ''}`} />
      {label}
    </button>
  )
}

import { useEffect, useState } from 'react'
import Logo from '../components/Logo'
import { api } from '../services/api'

const API_DOCS = `${import.meta.env.VITE_API_URL ?? 'http://localhost:8000'}/docs`

export default function Footer() {
  const [v, setV] = useState<string | null>(null)
  useEffect(() => { api.health().then((h) => setV(h.version)).catch(() => setV(null)) }, [])
  return (
    <footer className="border-t border-white/10 px-5 py-12">
      <div className="mx-auto grid max-w-6xl gap-8 md:grid-cols-[1.4fr_1fr_1fr]">
        <div>
          <Logo />
          <p className="mt-3 max-w-sm text-sm text-zinc-500">Autonomous frontend development with local AI. Designs, builds, animates, tests and repairs websites.</p>
          <p className="mt-3 text-xs text-zinc-600">UI v0.3.0 · API {v ? `v${v}` : 'not connected'}</p>
        </div>
        <nav aria-label="Footer navigation"><p className="label">Navigate</p>
          <ul className="space-y-2 text-sm text-zinc-400">
            <li><a className="hover:text-white" href="#features">Features</a></li>
            <li><a className="hover:text-white" href="#workflow">Workflow</a></li>
            <li><a className="hover:text-white" href="#about">About</a></li>
            <li><a className="hover:text-white" href="#/workspace">Workspace</a></li>
          </ul>
        </nav>
        <nav aria-label="Documentation"><p className="label">Documentation</p>
          <ul className="space-y-2 text-sm text-zinc-400">
            <li><a className="hover:text-white" href={API_DOCS} target="_blank" rel="noreferrer">API reference (local)</a></li>
            <li><a className="hover:text-white" href="https://ollama.com/library/qwen2.5-coder" target="_blank" rel="noreferrer">Qwen2.5-Coder on Ollama</a></li>
            <li><a className="hover:text-white" href="https://playwright.dev/docs/intro" target="_blank" rel="noreferrer">Playwright docs</a></li>
          </ul>
        </nav>
      </div>
    </footer>
  )
}

import { useCallback, useEffect, useState } from 'react'
import { api, type OllamaStatus } from '../services/api'

export type Conn = { state: 'checking' | 'connected' | 'model-missing' | 'offline' | 'backend-down'; detail: string; status?: OllamaStatus }

/** Real connection state: polls the backend, which asks Ollama. Nothing is simulated. */
export function useOllama(intervalMs = 10000) {
  const [conn, setConn] = useState<Conn>({ state: 'checking', detail: 'Checking Ollama…' })
  const refresh = useCallback(async () => {
    try {
      const s = await api.ollama()
      if (!s.reachable) setConn({ state: 'offline', detail: s.error ?? 'Ollama unreachable', status: s })
      else if (!s.model_available) setConn({ state: 'model-missing', detail: s.error ?? 'Model missing', status: s })
      else setConn({ state: 'connected', detail: `${s.model} ready`, status: s })
    } catch {
      setConn({ state: 'backend-down', detail: 'Backend API not reachable on :8000. Start it with: uvicorn backend.main:app' })
    }
  }, [])
  useEffect(() => {
    const first = setTimeout(refresh, 0)
    const t = setInterval(() => !document.hidden && refresh(), intervalMs)
    return () => { clearTimeout(first); clearInterval(t) }
  }, [refresh, intervalMs])
  return { conn, refresh }
}

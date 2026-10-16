import { useCallback, useEffect, useRef, useState } from 'react'
import { api, type Task, type TaskEvent, type TaskRequest } from '../services/api'

const ACTIVE = ['queued', 'running']
export const isActive = (t: Task | null) => !!t && ACTIVE.includes(t.status)

/** Tracks one project's agent task: live SSE progress, cancel, and history replay. */
export function useTask(projectId: string | null, onFinished: () => void) {
  const [task, setTask] = useState<Task | null>(null)
  const [events, setEvents] = useState<TaskEvent[]>([])
  const [error, setError] = useState('')
  const es = useRef<EventSource | null>(null)
  const done = useRef(onFinished)
  useEffect(() => { done.current = onFinished })

  const close = () => { es.current?.close(); es.current = null }

  const attach = useCallback((t: Task) => {
    close()
    setTask(t)
    setEvents([])
    if (!ACTIVE.includes(t.status)) { api.events(t.id).then(setEvents).catch(() => {}); return }
    const src = new EventSource(api.streamUrl(t.id))
    es.current = src
    src.addEventListener('progress', (e) => {
      const ev = JSON.parse((e as MessageEvent).data) as TaskEvent
      setEvents((prev) => (prev.some((p) => p.id === ev.id) ? prev : [...prev, ev]))
    })
    src.addEventListener('end', () => {
      close()
      api.task(t.id).then((fin) => { setTask(fin); done.current() }).catch(() => {})
    })
    src.onerror = () => {                         // connection dropped: fall back to one state check
      close()
      api.task(t.id).then((fin) => { setTask(fin); if (!ACTIVE.includes(fin.status)) done.current() }).catch(() => {})
    }
  }, [])

  useEffect(() => {
    close(); setTask(null); setEvents([]); setError('')
    if (!projectId) return
    let live = true
    api.tasks(projectId).then((list) => {
      if (!live || !list.length) return
      const current = list.find((t) => ACTIVE.includes(t.status)) ?? list[0]
      api.task(current.id).then((t) => live && attach(t))
    }).catch(() => {})
    return () => { live = false; close() }
  }, [projectId, attach])

  const start = useCallback(async (req: TaskRequest) => {
    if (!projectId) return
    setError('')
    try { attach(await api.startTask(projectId, req)) } catch (e) { setError((e as Error).message) }
  }, [projectId, attach])

  const cancel = useCallback(async () => {
    if (task) try { await api.cancel(task.id) } catch (e) { setError((e as Error).message) }
  }, [task])

  const open = useCallback((id: string) => { api.task(id).then(attach).catch((e) => setError(e.message)) }, [attach])

  return { task, events, error, start, cancel, open, running: isActive(task) }
}

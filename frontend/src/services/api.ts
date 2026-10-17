const B = '/api'
const JSON_H = { 'Content-Type': 'application/json' }

async function j<T>(r: Response): Promise<T> {
  if (!r.ok) {
    const body = await r.json().catch(() => ({}))
    const d = body.detail
    if (typeof d === 'string') throw new Error(d)
    if (Array.isArray(d)) throw new Error(d.map((x: { msg?: string }) => x.msg ?? JSON.stringify(x)).join('; '))
    if (d && typeof d === 'object') {
      const structured = d as { errors?: { msg?: string }[]; warnings?: { msg?: string }[]; msg?: string }
      const messages = [...(structured.errors ?? []), ...(structured.warnings ?? [])].map((x) => x.msg).filter(Boolean)
      throw new Error(messages.join('; ') || structured.msg || JSON.stringify(d))
    }
    throw new Error(r.statusText || `Request failed (${r.status})`)
  }
  return r.json()
}
const post = (u: string, body?: unknown) =>
  fetch(B + u, { method: 'POST', headers: JSON_H, body: body === undefined ? undefined : JSON.stringify(body) })

export interface OllamaStatus {
  reachable: boolean; base_url: string; model: string; model_available: boolean
  vision_model: string; vision_available: boolean; models: string[]; error: string | null
  provider?: 'ollama' | 'openai'; api_key_set?: boolean
}
export interface Settings {
  ollama_base_url: string; ollama_model: string; vision_model: string
  provider: 'ollama' | 'openai'; openai_base_url: string; openai_model: string; max_retries: number; api_key_set?: boolean
  timeout_s: number; num_ctx: number; max_concurrency: number; max_repair_loops: number; generation_profile: 'fast' | 'balanced' | 'quality'
}
export interface ProjectRow { id: string; name: string; brief: string; created_at: number; updated_at: number }
export interface AutopilotInfo { prompt_only?: boolean; app_shell?: boolean; assumptions?: string[] }

export interface ProjectState {
  project_id: string; brief: string; phase: string; plan: { sections?: string[]; brand?: string }
  stack_config?: { mode?: string; stack?: Record<string, string>; sources?: Record<string, string>; reasons?: Record<string, string>; autopilot?: AutopilotInfo }
  errors: string[]; repair_count: number; sections_done: string[]; usage: { in: number; out: number }
}
export type TaskStatus = 'queued' | 'running' | 'succeeded' | 'completed_with_issues' | 'failed' | 'cancelled'
export interface Task {
  id: string; kind: string; status: TaskStatus; error: string | null; checkpoint_id: string | null
  tokens_in: number; tokens_out: number; created_at: number; started_at: number | null; finished_at: number | null
  result?: { issues?: string[]; browser?: string; repairs?: number; sections_done?: string[]; sections_total?: number } | null
}
export interface TaskEvent { id: number; ts: number; level: 'info' | 'warn' | 'error'; stage: string; msg: string }
export interface Checkpoint { id: string; label: string; task_id: string | null; size: number; created_at: number }
export interface Summary { task_id: string; created_at: number; summary: { kind: string; phase: string; issues: string[]; browser: string; repairs: number; sections: string } }
export interface TaskRequest { kind: 'generate' | 'verify' | 'edit' | 'test'; force?: boolean; confirm?: boolean; repair?: boolean; section?: string; instruction?: string }

export type CheckStatus = 'passed' | 'failed' | 'skipped'
export interface Check { name: string; viewport: string; status: CheckStatus; detail: string }
export interface A11yFinding { rule: string; sid: string; msg: string }
export interface RepairRow { attempt: number; sid: string; issue: string; method: string; outcome: string; task_id?: string; created_at?: number }
export interface Report {
  checks: Check[]; a11y: A11yFinding[]; notes: string[]; repairs: RepairRow[]
  counts: Record<CheckStatus, number>
  vision: { status: string; note: string; findings: { viewport: string; sid: string; msg: string }[] }
}
export type Framework = 'html' | 'react'
export type StackMode = 'automatic' | 'manual' | 'hybrid'
export interface StackDraft { mode: StackMode; prefs: Record<string, string> }
export interface StackCatalogOption {
  id: string; label: string; desc?: string; status?: string; langs?: string[]; ready_langs?: string[]; kind?: string; runtime?: string
}
export interface StackCatalog {
  fields: Record<string, StackCatalogOption[]>
  testing_for?: Record<string, string[]>
  backend_tests?: Record<string, string>
}
export interface StackResolution {
  mode: StackMode; ok: boolean; stack?: Record<string, string>; summary?: string
  errors: { field?: string; fields?: string[]; msg: string }[]
  warnings: { field?: string; fields?: string[]; msg: string }[]
  blocking?: string[]; pending?: string[]; generator?: Record<string, string>
  options?: Record<string, { id: string; label: string; allowed: boolean; why_not: string; status: string }[]>
}

export interface SpecField { name: string; type: string; required: boolean; unique: boolean; ref?: string; values?: string[] }
export interface SpecEntity { name: string; path: string; fields: SpecField[]; read: string; write: string }
export interface SpecPage { slug: string; title: string; auth: boolean }
export interface SpecOverrides { pages?: SpecPage[]; features?: string[]; entities?: Record<string, string[]>; drop_entities?: string[] }
export interface AppSpec {
  kind: string; pages: SpecPage[]; features: string[]; roles: string[]
  data: { enabled: boolean; database: string; entities: SpecEntity[] }
  api: { routes: { method: string; path: string }[] }
  gaps: string[]; assumptions: string[]; open_questions: { id: string; question: string }[]
}
export interface SpecPreview { ok: boolean; resolution: StackResolution; spec: AppSpec | null }

export interface BackendCoverage { backend: string; ready: boolean; gaps: string[]; note: string }
export interface BackendLast {
  generated: boolean; generator?: string; db?: string | null; routes?: number; files?: number; not_generated?: string[]; warnings?: string[]
}
export interface BackendInfo { coverage: BackendCoverage; last: BackendLast }
export interface DebugDiagnostic { severity: string; file: string; line?: number | null; message: string }
export interface DebugPatchResult { file: string; reason: string }
export interface DebugResult {
  summary: string; diagnostics: DebugDiagnostic[]; applied: DebugPatchResult[]; rejected: string[]
  files_scanned: number; files_in_context: string[]; verification: string[]; usage: { in: number; out: number }; apply_fixes: boolean
}

export interface BackendResult {
  generated: boolean; gaps?: string[]; note?: string; generator?: string; database?: string | null; files?: number; written?: string[]
  kept?: string[]; routes?: number; not_generated?: string[]; warnings?: string[]; commands?: Record<string, string>
}

export const api = {
  health: () => fetch(`${B}/health`).then(j<{ ok: boolean; version: string; mock_llm: boolean }>),
  ollama: () => fetch(`${B}/ollama/status`).then(j<OllamaStatus>),
  ollamaCheck: (base_url: string, model: string, provider?: string) => post('/ollama/check', { base_url, model, provider }).then(j<OllamaStatus>),
  settings: () => fetch(`${B}/settings`).then(j<Settings>),
  saveSettings: (s: Partial<Settings>) => fetch(`${B}/settings`, { method: 'PUT', headers: JSON_H, body: JSON.stringify(s) }).then(j<Settings>),
  projects: () => fetch(`${B}/projects`).then(j<ProjectRow[]>),
  create: (brief: string, framework: Framework = 'html', config?: StackDraft, overrides?: SpecOverrides) => post('/projects', {
    brief, framework, ...(config ? { mode: config.mode, prefs: config.prefs } : {}), ...(overrides && Object.keys(overrides).length ? { overrides } : {}),
  }).then(j<{ project_id: string; stack?: Record<string, string>; summary?: string; warnings?: unknown[]; pending?: string[]; blocking?: string[] }>),
  autoBuild: (prompt: string) => post('/autobuild', { prompt }).then(j<{ project_id: string; task_id: string; stack: Record<string, string>; summary: string; assumptions: string[]; autopilot: boolean }>),
  debugProject: (id: string, error_text: string, apply_fixes = true) => post(`/projects/${id}/debug`, { error_text, apply_fixes }).then(j<DebugResult>),
  specPreview: (brief: string, config: StackDraft, overrides: SpecOverrides) =>
    post('/spec/preview', { brief, mode: config.mode, prefs: config.prefs, overrides }).then(j<SpecPreview>),
  stackCatalog: () => fetch(`${B}/stack/catalog`).then(j<StackCatalog>),
  resolveStack: (mode: StackMode, prefs: Record<string, string>, brief: string) =>
    post('/stack/resolve', { mode, prefs, brief, options: true }).then(j<StackResolution>),
  projectStack: (id: string) => fetch(`${B}/projects/${id}/stack`).then(j<StackResolution & { stack: Record<string, string> }>),
  saveProjectStack: (id: string, config: StackDraft, confirm = false) =>
    fetch(`${B}/projects/${id}/stack`, { method: 'PUT', headers: JSON_H, body: JSON.stringify({ ...config, confirm }) }).then(j<StackResolution & { requires_regenerate?: boolean }>),
  backendInfo: (id: string) => fetch(`${B}/projects/${id}/backend`).then(j<BackendInfo>),
  generateBackend: (id: string) => post(`/projects/${id}/backend`).then(j<BackendResult>),
  deleteProject: (id: string) => fetch(`${B}/projects/${id}?confirm=true`, { method: 'DELETE' }).then(j<{ deleted: string }>),
  report: (id: string) => fetch(`${B}/projects/${id}/report`).then((r) => (r.status === 404 ? null : j<Report>(r))),
  repairs: (id: string) => fetch(`${B}/projects/${id}/repairs`).then(j<RepairRow[]>),
  project: (id: string) => fetch(`${B}/projects/${id}`).then(j<ProjectState>),
  files: (id: string) => fetch(`${B}/projects/${id}/files`).then(j<string[]>),
  file: (id: string, path: string) => fetch(`${B}/projects/${id}/file?path=${encodeURIComponent(path)}`).then(j<{ content: string; issues: string[] }>),
  saveFile: (id: string, path: string, content: string) =>
    fetch(`${B}/projects/${id}/file`, { method: 'PUT', headers: JSON_H, body: JSON.stringify({ path, content }) }).then(j<{ issues: string[] }>),
  shots: (id: string) => fetch(`${B}/projects/${id}/shots`).then(j<string[]>),
  shotUrl: (id: string, name: string) => `${B}/projects/${id}/shot/${name}`,
  previewUrl: (id: string, v: number) => `${B}/preview/${id}/index.html?v=${v}`,
  exportUrl: (id: string) => `${B}/projects/${id}/export`,
  startTask: (id: string, t: TaskRequest) => post(`/projects/${id}/tasks`, t).then(j<Task>),
  tasks: (id: string) => fetch(`${B}/projects/${id}/tasks`).then(j<Task[]>),
  task: (tid: string) => fetch(`${B}/tasks/${tid}`).then(j<Task>),
  events: (tid: string) => fetch(`${B}/tasks/${tid}/events`).then(j<TaskEvent[]>),
  streamUrl: (tid: string, after = 0) => `${B}/tasks/${tid}/stream?after=${after}`,
  cancel: (tid: string) => post(`/tasks/${tid}/cancel`).then(j<Task>),
  summaries: (id: string) => fetch(`${B}/projects/${id}/summaries`).then(j<Summary[]>),
  checkpoints: (id: string) => fetch(`${B}/projects/${id}/checkpoints`).then(j<Checkpoint[]>),
  makeCheckpoint: (id: string, label: string) => post(`/projects/${id}/checkpoints?label=${encodeURIComponent(label)}`).then(j<Checkpoint>),
  restore: (id: string, cid: string) => post(`/projects/${id}/checkpoints/${cid}/restore?confirm=true`).then(j<{ restored: string }>),
}

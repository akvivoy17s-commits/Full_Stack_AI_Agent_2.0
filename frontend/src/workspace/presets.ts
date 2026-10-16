import type { SpecOverrides, StackDraft } from '../services/api'

export interface Preset { name: string; brief: string; style: string; motion: string; draft: StackDraft; ov: SpecOverrides }
const KEY = 'fullstack-agent-presets-v1'
const MAX = 10

const valid = (p: unknown): p is Preset => {
  const x = p as Preset
  return Boolean(x && typeof x.name === 'string' && typeof x.brief === 'string' && typeof x.style === 'string' && typeof x.motion === 'string'
    && x.draft && typeof x.draft.mode === 'string' && typeof x.draft.prefs === 'object' && x.ov && typeof x.ov === 'object')
}

export function loadPresets(): Preset[] {
  try {
    const v = JSON.parse(localStorage.getItem(KEY) ?? '[]')
    return Array.isArray(v) ? v.filter(valid).slice(0, MAX) : []
  } catch { return [] }
}

function store(list: Preset[]): Preset[] {
  try { localStorage.setItem(KEY, JSON.stringify(list)) } catch { /* storage unavailable */ }
  return list
}

export const savePreset = (p: Preset): Preset[] => store([p, ...loadPresets().filter((x) => x.name !== p.name)].slice(0, MAX))
export const removePreset = (name: string): Preset[] => store(loadPresets().filter((x) => x.name !== name))

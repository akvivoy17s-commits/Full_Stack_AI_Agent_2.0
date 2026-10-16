import { useEffect, useRef, useState } from 'react'
import { motion } from 'motion/react'
import { Check, Loader2, Play, RotateCcw } from 'lucide-react'
import { Heading } from './Capabilities'

const PROMPT = 'Dark landing page for a fitness app with pricing and smooth scroll animations'
const CODE = `<section id="hero" class="sec">
  <h1 class="reveal">Train smarter.</h1>
  <p class="reveal">Plans that adapt to you.</p>
  <a class="btn" href="#pricing">Get started</a>
</section>`
const STAGES = ['Planning', 'Coding', 'Testing', 'Complete'] as const

/** Everything here is SIMULATED sample data. Real tasks use the backend task stream. */
export default function Demo() {
  const [stage, setStage] = useState(-1)
  const [chars, setChars] = useState(0)
  const timers = useRef<number[]>([])
  const clear = () => { timers.current.forEach(clearTimeout); timers.current = [] }
  useEffect(() => clear, [])

  const run = () => {
    clear(); setChars(0); setStage(0)
    timers.current.push(window.setTimeout(() => setStage(1), 1100))
    timers.current.push(window.setTimeout(() => setStage(2), 3400))
    timers.current.push(window.setTimeout(() => setStage(3), 4700))
  }
  useEffect(() => {
    if (stage < 1) return
    const t = setInterval(() => setChars((c) => Math.min(c + 3, CODE.length)), 25)
    return () => clearInterval(t)
  }, [stage])

  const progress = stage < 0 ? 0 : ((stage + 1) / STAGES.length) * 100
  return (
    <section className="mx-auto max-w-6xl px-5 py-24">
      <Heading eyebrow="LIVE DEMONSTRATION" title="See the pipeline in motion" />
      <p className="mt-3 text-center"><span className="chip border-amber-500/40 bg-amber-500/10 text-amber-300">SIMULATED DEMO · sample data, not a real task</span></p>
      <div className="glass mt-8 rounded-2xl p-4 sm:p-6">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
          <div className="flex-1 rounded-lg border border-white/10 bg-black/40 px-3 py-2.5 text-sm text-zinc-300">{PROMPT}</div>
          <button className="btn-primary" onClick={run} disabled={stage >= 0 && stage < 3}>
            {stage === 3 ? <><RotateCcw size={16} /> Replay</> : <><Play size={16} /> Run simulation</>}
          </button>
        </div>
        <div className="mt-5 h-1.5 overflow-hidden rounded-full bg-white/10" role="progressbar" aria-valuenow={progress} aria-valuemin={0} aria-valuemax={100}>
          <motion.div className="h-full bg-gradient-to-r from-accent to-accentSoft" animate={{ width: `${progress}%` }} transition={{ duration: 0.6 }} />
        </div>
        <ul className="mt-4 flex flex-wrap gap-2" aria-live="polite">
          {STAGES.map((s, i) => (
            <li key={s} className={`chip ${i < stage || stage === 3 ? 'border-emerald-500/30 text-emerald-300' : i === stage ? 'border-accent/50 text-accentSoft' : 'border-white/10 text-zinc-500'}`}>
              {i < stage || stage === 3 ? <Check size={12} /> : i === stage ? <Loader2 size={12} className="animate-spin" /> : <span className="h-1.5 w-1.5 rounded-full bg-zinc-600" />}{s}
            </li>
          ))}
        </ul>
        <div className="mt-5 grid gap-4 md:grid-cols-2">
          <pre className="min-h-[170px] overflow-auto rounded-xl border border-white/10 bg-black/50 p-4 font-mono text-xs leading-5 text-zinc-300">{CODE.slice(0, chars) || <span className="text-zinc-600">// generated code appears here</span>}</pre>
          <div className="min-h-[170px] overflow-hidden rounded-xl border border-white/10 bg-gradient-to-b from-[#16081f] to-[#0b0b10] p-6">
            {stage >= 2 ? (
              <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="space-y-3">
                <h3 className="font-display text-3xl font-bold text-white">Train smarter.</h3>
                <p className="text-sm text-zinc-400">Plans that adapt to you.</p>
                <span className="inline-block rounded-md bg-accent px-4 py-2 text-sm font-medium text-white">Get started</span>
              </motion.div>
            ) : <p className="text-sm text-zinc-600">Rendered preview appears after the coding stage.</p>}
          </div>
        </div>
      </div>
    </section>
  )
}

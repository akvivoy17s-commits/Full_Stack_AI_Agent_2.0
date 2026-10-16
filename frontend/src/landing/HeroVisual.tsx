import { useEffect, useState } from 'react'
import { motion, useReducedMotion } from 'motion/react'
import { Cpu, LayoutTemplate, Sparkles } from 'lucide-react'

const CODE = [
  '<section class="hero">',
  '  <h1 class="reveal">Build faster</h1>',
  '  <p class="reveal">Ship in minutes.</p>',
  '  <a class="btn" href="#start">Start</a>',
  '</section>',
]

/** Real rendered UI (editor + preview + cards). The typing animation is decorative, not task output. */
export default function HeroVisual() {
  const reduce = useReducedMotion()
  const [n, setN] = useState(reduce ? CODE.join('\n').length : 0)
  const total = CODE.join('\n').length
  useEffect(() => {
    if (reduce) return
    const t = setInterval(() => setN((v) => (v >= total + 30 ? 0 : v + 1)), 70)
    return () => clearInterval(t)
  }, [reduce, total])
  const typed = CODE.join('\n').slice(0, Math.min(n, total))
  const done = n >= total

  return (
    <div className="relative mx-auto mt-16 h-[360px] w-full max-w-4xl sm:h-[420px]" aria-hidden>
      <svg className="absolute inset-0 h-full w-full" viewBox="0 0 800 420" preserveAspectRatio="none">
        <path d="M250 190 C330 190 330 150 410 150" fill="none" stroke="#E50914" strokeWidth="1.2" strokeDasharray="5 8" className="animate-dash" />
        <path d="M410 300 C330 330 300 300 250 300" fill="none" stroke="#E50914" strokeOpacity=".6" strokeWidth="1.2" strokeDasharray="5 8" className="animate-dash" />
      </svg>

      <motion.div initial={{ y: 70, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 1.55, duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
        className="absolute left-0 top-6 w-[58%] animate-float sm:w-[48%]">
        <div className="glass overflow-hidden rounded-xl shadow-soft">
          <div className="flex items-center gap-1.5 border-b border-white/10 px-3 py-2">
            {['bg-red-500', 'bg-amber-400', 'bg-emerald-400'].map((c) => <i key={c} className={`h-2 w-2 rounded-full ${c}`} />)}
            <span className="ml-2 text-[10px] text-zinc-500">index.html</span>
            <span className="ml-auto flex items-center gap-1 text-[10px] text-accentSoft">
              <span className={`h-1.5 w-1.5 rounded-full bg-accent ${done ? '' : 'animate-blink'}`} />{done ? 'ready' : 'generating'}
            </span>
          </div>
          <pre className="min-h-[128px] whitespace-pre-wrap text-left p-3 font-mono text-[10.5px] leading-5 text-zinc-300 sm:text-xs">
            {typed}<span className="animate-blink text-accent">▍</span>
          </pre>
        </div>
      </motion.div>

      <motion.div initial={{ y: 80, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 1.7, duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
        className="absolute right-0 top-0 w-[56%] animate-float [animation-delay:-2s] sm:w-[52%]">
        <div className="glass overflow-hidden rounded-xl shadow-glow">
          <div className="border-b border-white/10 px-3 py-2 text-[10px] text-zinc-500">Live preview</div>
          <div className="space-y-2 bg-gradient-to-b from-[#1a0507] to-[#0c0c0f] p-4">
            <div className="h-1.5 w-12 rounded bg-accent" />
            <div className="h-3.5 w-3/4 rounded bg-white/90" /><div className="h-3.5 w-1/2 rounded bg-white/90" />
            <div className="h-2 w-5/6 rounded bg-white/20" />
            <div className="flex gap-2 pt-1"><div className="h-6 w-16 rounded bg-accent" /><div className="h-6 w-16 rounded border border-white/20" /></div>
            <div className="grid grid-cols-3 gap-2 pt-3">{[0, 1, 2].map((i) => <div key={i} className="h-12 rounded-md border border-white/10 bg-white/5" />)}</div>
          </div>
        </div>
      </motion.div>

      {[
        { Icon: Cpu, t: 'Local Ollama', c: 'left-[4%] bottom-6', d: 1.9 },
        { Icon: LayoutTemplate, t: 'Design tokens', c: 'left-[38%] bottom-0', d: 2.0 },
        { Icon: Sparkles, t: 'Motion ready', c: 'right-[4%] bottom-8', d: 2.1 },
      ].map(({ Icon, t, c, d }) => (
        <motion.div key={t} initial={{ y: 40, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: d, duration: 0.6 }}
          className={`glass absolute ${c} flex items-center gap-2 rounded-xl px-3 py-2.5 text-xs text-zinc-200 shadow-soft animate-float [animation-delay:-4s]`}>
          <Icon size={14} className="text-accent" />{t}
        </motion.div>
      ))}
    </div>
  )
}

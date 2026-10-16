import { useEffect, useRef } from 'react'
import { gsap } from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import { MessageSquareText, Palette, Code2, Eye, ScanSearch, Wrench } from 'lucide-react'
import { Heading } from './Capabilities'

gsap.registerPlugin(ScrollTrigger)

const STEPS = [
  { Icon: MessageSquareText, t: 'PROMPT', d: 'Your request becomes a validated specification.' },
  { Icon: Palette, t: 'DESIGN', d: 'Layout, tokens and motion are planned together.' },
  { Icon: Code2, t: 'GENERATE', d: 'Sections are written one at a time and saved as real files.' },
  { Icon: Eye, t: 'PREVIEW', d: 'The site renders live in the workspace.' },
  { Icon: ScanSearch, t: 'INSPECT', d: 'Static checks and browser tests find real defects.' },
  { Icon: Wrench, t: 'REPAIR', d: 'Focused fixes run within a strict attempt limit.' },
]

/** GSAP is used here because a scroll-scrubbed timeline (line fill + sequenced nodes) is its strength. */
export default function Workflow() {
  const root = useRef<HTMLElement>(null)
  useEffect(() => {
    const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    const ctx = gsap.context(() => {
      if (reduce) { gsap.set('.wf-fill', { scaleX: 1, scaleY: 1 }); gsap.set('.wf-node', { opacity: 1, y: 0 }); return }
      const tl = gsap.timeline({ scrollTrigger: { trigger: root.current, start: 'top 70%', end: 'bottom 75%', scrub: 0.6 } })
      tl.fromTo('.wf-fill', { scaleX: 0, scaleY: 0 }, { scaleX: 1, scaleY: 1, ease: 'none', duration: STEPS.length })
      STEPS.forEach((_, i) => tl.fromTo(`.wf-node-${i}`, { opacity: 0.25, y: 14 }, { opacity: 1, y: 0, duration: 0.6 }, i * 0.85))
    }, root)
    return () => ctx.revert()
  }, [])
  return (
    <section id="workflow" ref={root} className="mx-auto max-w-6xl px-5 py-24">
      <Heading eyebrow="HOW IT WORKS" title="From idea to verified site in six steps" sub="Every stage reports real status in the workspace activity log." />
      <div className="relative mt-14">
        <div className="absolute left-0 right-0 top-6 hidden h-px bg-white/10 lg:block">
          <div className="wf-fill h-full origin-left bg-gradient-to-r from-accent to-accentSoft shadow-glow" />
        </div>
        <div className="absolute bottom-0 left-6 top-0 w-px bg-white/10 lg:hidden">
          <div className="wf-fill h-full origin-top bg-accent" />
        </div>
        <ol className="grid gap-8 pl-14 lg:grid-cols-6 lg:gap-4 lg:pl-0">
          {STEPS.map(({ Icon, t, d }, i) => (
            <li key={t} className={`wf-node wf-node-${i} relative lg:text-center`}>
              <span className="absolute -left-14 grid h-12 w-12 place-items-center rounded-full border border-accent/40 bg-surface text-accent lg:static lg:mx-auto lg:mb-4">
                <Icon size={20} />
              </span>
              <p className="font-display text-sm font-semibold tracking-[0.18em] text-white"><span className="mr-2 text-accent/70">{i + 1}</span>{t}</p>
              <p className="mt-1.5 text-sm text-zinc-400">{d}</p>
            </li>
          ))}
        </ol>
      </div>
    </section>
  )
}

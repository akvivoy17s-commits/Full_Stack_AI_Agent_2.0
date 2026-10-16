import { motion } from 'motion/react'
import { Wand2, PenTool, Film, Box, Bug, MonitorCheck } from 'lucide-react'

const ITEMS = [
  { Icon: Wand2, t: 'AI Website Generation', d: 'Describe a site in plain language. The agent plans sections, writes the code and assembles a working project on disk.' },
  { Icon: PenTool, t: 'Professional UI/UX Design', d: 'Design tokens for color, type, spacing and radii keep every generated page consistent, readable and responsive.' },
  { Icon: Film, t: 'Animation Engineering', d: 'Subtle, balanced or expressive motion built on transform and opacity, with reduced-motion support by default.' },
  { Icon: Box, t: 'Interactive 3D Experiences', d: 'Optional Three.js scenes when they add real value, kept off by default to protect integrated graphics.' },
  { Icon: Bug, t: 'Autonomous Debugging', d: 'Failed checks trigger small, targeted repairs with a hard attempt limit, and unresolved issues are reported honestly.' },
  { Icon: MonitorCheck, t: 'Visual Browser Testing', d: 'Playwright opens the result, checks console errors, overflow and layouts at desktop and mobile sizes.' },
]

export default function Capabilities() {
  return (
    <section id="features" className="mx-auto max-w-6xl px-5 py-24">
      <Heading eyebrow="CAPABILITIES" title="One agent. The whole frontend lifecycle." />
      <motion.ul initial="hidden" whileInView="show" viewport={{ once: true, margin: '-80px' }} transition={{ staggerChildren: 0.08 }}
        className="mt-12 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {ITEMS.map(({ Icon, t, d }) => (
          <motion.li key={t} variants={{ hidden: { opacity: 0, y: 28 }, show: { opacity: 1, y: 0, transition: { duration: 0.55 } } }}
            whileHover={{ y: -6 }} className="group">
            <article tabIndex={0} className="glass h-full rounded-2xl p-6 transition duration-300 group-hover:border-accent/40 group-hover:shadow-glow focus-visible:border-accent/60">
              <span className="mb-4 grid h-11 w-11 place-items-center rounded-xl border border-accent/30 bg-accent/10 text-accent transition group-hover:scale-110"><Icon size={20} /></span>
              <h3 className="font-display text-lg font-semibold text-white">{t}</h3>
              <p className="mt-2 text-sm leading-relaxed text-zinc-400">{d}</p>
            </article>
          </motion.li>
        ))}
      </motion.ul>
    </section>
  )
}

export function Heading({ eyebrow, title, sub }: { eyebrow: string; title: string; sub?: string }) {
  return (
    <motion.div initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} className="text-center">
      <p className="text-xs font-medium tracking-[0.25em] text-accent">{eyebrow}</p>
      <h2 className="mx-auto mt-3 max-w-2xl font-display text-3xl font-bold text-white sm:text-4xl">{title}</h2>
      {sub && <p className="mx-auto mt-3 max-w-xl text-zinc-400">{sub}</p>}
    </motion.div>
  )
}

import { Cpu, ShieldCheck, Gauge } from 'lucide-react'
import { motion } from 'motion/react'
import { Heading } from './Capabilities'

const POINTS = [
  { Icon: Cpu, t: 'Local-first AI', d: 'Runs on Ollama with qwen2.5-coder:7b by default. No paid cloud API is needed for the core workflow.' },
  { Icon: ShieldCheck, t: 'Safe by design', d: 'Sandboxed project folders, path validation, command allowlist, checkpoints before every risky change.' },
  { Icon: Gauge, t: 'Built for modest hardware', d: 'Tuned for 16 GB RAM and integrated graphics. Expect slower generation on CPU: the 7B model needs roughly 5-6 GB RAM.' },
]

export default function About() {
  return (
    <section id="about" className="mx-auto max-w-6xl px-5 py-24">
      <Heading eyebrow="ABOUT" title="A real development tool, not a chatbot" sub="It writes files, builds, tests and repairs. When something fails, it tells you plainly." />
      <div className="mt-12 grid gap-4 md:grid-cols-3">
        {POINTS.map(({ Icon, t, d }) => (
          <motion.div key={t} initial={{ opacity: 0, y: 24 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} className="glass rounded-2xl p-6">
            <Icon className="text-accent" size={22} />
            <h3 className="mt-3 font-display text-lg font-semibold text-white">{t}</h3>
            <p className="mt-2 text-sm leading-relaxed text-zinc-400">{d}</p>
          </motion.div>
        ))}
      </div>
    </section>
  )
}

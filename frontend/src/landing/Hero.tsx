import { motion } from 'motion/react'
import { ArrowRight, Compass } from 'lucide-react'
import ConnectionBadge from '../components/ConnectionBadge'
import type { Conn } from '../hooks/useOllama'
import HeroVisual from './HeroVisual'

const ease = [0.22, 1, 0.36, 1] as const
const line = { hidden: { y: '110%' }, show: { y: 0, transition: { duration: 0.7, ease } } }

export default function Hero({ conn }: { conn: Conn }) {
  const lines = ['Imagine It.', 'Build It.', 'Animate Everything.']
  return (
    <section id="top" className="relative px-5 pb-20 pt-36 text-center sm:pt-44">
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.55, duration: 0.5 }}
        className="mx-auto mb-6 flex flex-wrap items-center justify-center gap-3">
        <span className="chip border-accent/40 bg-accent/10 font-medium tracking-[0.16em] text-accentSoft">YOUR AUTONOMOUS FRONTEND ENGINEER</span>
        <ConnectionBadge conn={conn} onClick={() => { window.location.hash = '#/workspace' }} />
      </motion.div>

      <motion.h1 initial="hidden" animate="show" transition={{ staggerChildren: 0.14, delayChildren: 0.75 }}
        className="mx-auto max-w-4xl font-display text-5xl font-bold leading-[1.05] tracking-tight text-white sm:text-7xl">
        {lines.map((l, i) => (
          <span key={l} className="block overflow-hidden pb-1">
            <motion.span variants={line} className={`block ${i === 2 ? 'bg-gradient-to-r from-white via-accentSoft to-accent bg-clip-text text-transparent' : ''}`}>{l}</motion.span>
          </span>
        ))}
      </motion.h1>

      <motion.p initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 1.2, duration: 0.6 }}
        className="mx-auto mt-6 max-w-2xl text-base leading-relaxed text-zinc-400 sm:text-lg">
        Turn your ideas into stunning, production-ready websites with AI-powered design, advanced animations, intelligent code generation, and autonomous browser testing.
      </motion.p>

      <motion.div initial="hidden" animate="show" transition={{ staggerChildren: 0.1, delayChildren: 1.35 }}
        className="mt-9 flex flex-wrap items-center justify-center gap-3">
        <motion.button variants={{ hidden: { opacity: 0, y: 10 }, show: { opacity: 1, y: 0 } }} whileHover={{ y: -2 }} whileTap={{ scale: 0.97 }}
          className="btn-primary !px-6 !py-3 text-base" onClick={() => { window.location.hash = '#/workspace' }}>
          Start Building <ArrowRight size={18} />
        </motion.button>
        <motion.a variants={{ hidden: { opacity: 0, y: 10 }, show: { opacity: 1, y: 0 } }} whileHover={{ y: -2 }} whileTap={{ scale: 0.97 }}
          href="#features" className="btn-ghost !px-6 !py-3 text-base"><Compass size={18} /> Explore Capabilities</motion.a>
      </motion.div>

      <HeroVisual />
    </section>
  )
}

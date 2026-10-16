import { motion } from 'motion/react'
import { ArrowRight } from 'lucide-react'

export default function CTA() {
  return (
    <section className="mx-auto max-w-5xl px-5 py-24">
      <motion.div initial={{ opacity: 0, scale: 0.97 }} whileInView={{ opacity: 1, scale: 1 }} viewport={{ once: true }} transition={{ duration: 0.6 }}
        className="relative overflow-hidden rounded-3xl border border-accent/30 bg-gradient-to-br from-accent/20 via-surface to-surface p-10 text-center shadow-glow sm:p-16">
        <div aria-hidden className="absolute -right-20 -top-20 h-64 w-64 rounded-full bg-accent/30 blur-[90px]" />
        <h2 className="relative font-display text-3xl font-bold text-white sm:text-5xl">Ready to build something remarkable?</h2>
        <p className="relative mx-auto mt-4 max-w-xl text-zinc-300">Open the workspace, describe your site and watch real files appear, get tested and get repaired.</p>
        <button className="btn-primary relative mt-8 !px-7 !py-3 text-base" onClick={() => { window.location.hash = '#/workspace' }}>
          Launch Workspace <ArrowRight size={18} />
        </button>
      </motion.div>
    </section>
  )
}

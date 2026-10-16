import { useState } from 'react'
import { motion, AnimatePresence } from 'motion/react'
import { Menu, X } from 'lucide-react'
import Logo from '../components/Logo'

const LINKS = [['Features', '#features'], ['Workflow', '#workflow'], ['About', '#about']] as const

export default function Nav() {
  const [open, setOpen] = useState(false)
  const launch = () => { window.location.hash = '#/workspace' }
  return (
    <motion.header initial={{ y: -24, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.25, duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
      className="fixed inset-x-0 top-0 z-50">
      <nav className="glass mx-auto mt-3 flex max-w-6xl items-center justify-between rounded-2xl px-4 py-2.5 shadow-soft" aria-label="Primary">
        <a href="#top" aria-label="Frontend AI Engineer home"><Logo /></a>
        <ul className="hidden items-center gap-1 md:flex">
          {LINKS.map(([l, h]) => (
            <li key={h}><a href={h} className="rounded-lg px-3 py-2 text-sm text-zinc-400 transition hover:bg-white/5 hover:text-white">{l}</a></li>
          ))}
        </ul>
        <div className="flex items-center gap-2">
          <button className="btn-primary hidden sm:inline-flex" onClick={launch}>Launch Workspace</button>
          <button className="btn-ghost !px-2.5 md:hidden" aria-label={open ? 'Close menu' : 'Open menu'} aria-expanded={open} onClick={() => setOpen(!open)}>
            {open ? <X size={18} /> : <Menu size={18} />}
          </button>
        </div>
      </nav>
      <AnimatePresence>
        {open && (
          <motion.div initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }}
            className="glass mx-4 mt-2 rounded-2xl p-3 md:hidden">
            {LINKS.map(([l, h]) => (
              <a key={h} href={h} onClick={() => setOpen(false)} className="block rounded-lg px-3 py-3 text-zinc-300 hover:bg-white/5">{l}</a>
            ))}
            <button className="btn-primary mt-2 w-full" onClick={launch}>Launch Workspace</button>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.header>
  )
}

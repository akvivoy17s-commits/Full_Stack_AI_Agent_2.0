import { motion } from 'motion/react'

export default function Logo({ compact = false }: { compact?: boolean }) {
  return (
    <span className="flex items-center gap-2.5">
      <motion.svg width="30" height="30" viewBox="0 0 32 32" fill="none" aria-hidden whileHover={{ rotate: 8, scale: 1.08 }}>
        <rect x="2" y="2" width="28" height="28" rx="8" fill="#151515" stroke="#E50914" strokeWidth="1.5" />
        <motion.path d="M11 11l-4 5 4 5M21 11l4 5-4 5" stroke="#E50914" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
          initial={{ pathLength: 0 }} animate={{ pathLength: 1 }} transition={{ duration: 1.1, ease: 'easeInOut' }} />
        <motion.circle cx="16" cy="16" r="2.2" fill="#fff" animate={{ opacity: [1, .3, 1] }} transition={{ duration: 2.4, repeat: Infinity }} />
      </motion.svg>
      {!compact && <span className="font-display text-[13px] font-semibold tracking-[0.18em] text-white">FRONTEND AI ENGINEER</span>}
    </span>
  )
}

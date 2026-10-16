import { motion, useReducedMotion, type HTMLMotionProps, type Variants } from 'framer-motion'
import type { ReactNode } from 'react'

export const revealUp: Variants = {
  hidden: { opacity: 0, y: 24 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.62, ease: [0.2, 0.75, 0.25, 1] } },
}
export const revealLeft: Variants = {
  hidden: { opacity: 0, x: -28 },
  visible: { opacity: 1, x: 0, transition: { duration: 0.62, ease: [0.2, 0.75, 0.25, 1] } },
}
export const revealScale: Variants = {
  hidden: { opacity: 0, scale: 0.94 },
  visible: { opacity: 1, scale: 1, transition: { duration: 0.58, ease: [0.2, 0.75, 0.25, 1] } },
}
export const staggerChildren: Variants = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.09, delayChildren: 0.04 } },
}

type RevealProps = HTMLMotionProps<'div'> & { children: ReactNode; variant?: 'up' | 'left' | 'scale'; once?: boolean }
export function Reveal({ children, variant = 'up', once = true, ...props }: RevealProps) {
  const reduced = useReducedMotion()
  const variants = variant === 'left' ? revealLeft : variant === 'scale' ? revealScale : revealUp
  return <motion.div
    initial={reduced ? false : 'hidden'}
    whileInView="visible"
    viewport={{ once, amount: 0.14 }}
    variants={variants}
    {...props}
  >{children}</motion.div>
}

type FloatProps = HTMLMotionProps<'div'> & { children: ReactNode; distance?: number; duration?: number }
export function Floating({ children, distance = 12, duration = 6, ...props }: FloatProps) {
  const reduced = useReducedMotion()
  return <motion.div
    animate={reduced ? undefined : { y: [0, -distance, 0] }}
    transition={reduced ? undefined : { duration, ease: 'easeInOut', repeat: Infinity }}
    {...props}
  >{children}</motion.div>
}

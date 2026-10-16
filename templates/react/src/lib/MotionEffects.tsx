import { useEffect } from 'react'
import { initMotion } from './motion'

/** Mount once beside the generated App to enable data-* motion hooks on rendered markup. */
export default function MotionEffects() {
  useEffect(() => initMotion(), [])
  return null
}

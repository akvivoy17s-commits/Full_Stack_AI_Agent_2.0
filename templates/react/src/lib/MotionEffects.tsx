import { useEffect } from 'react'
import { initMotion } from './motion'

/** Mount once beside the generated App to enable motion and opt-in Three.js hooks. */
export default function MotionEffects() {
  useEffect(() => {
    const cleanupMotion = initMotion()
    let cancelled = false
    let cleanupThree = () => {}

    // The shared runtime loads Three.js only if a rendered section opts in.
    // Import after React mounts so querySelector sees the generated DOM.
    import('./three-hero.js').then((runtime) => {
      if (cancelled) return
      cleanupThree = runtime.initThreeHero()
    }).catch(() => {
      // CSS fallback remains visible if the optional runtime cannot load.
    })

    return () => {
      cancelled = true
      cleanupMotion()
      cleanupThree()
    }
  }, [])
  return null
}

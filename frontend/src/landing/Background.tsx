import { useMemo } from 'react'

/** CSS/SVG only: ambient light, grid, particles, glowing connection lines, vignette. No WebGL. */
export default function Background() {
  const dots = useMemo(() => Array.from({ length: 16 }, (_, i) => ({
    left: `${(i * 37) % 100}%`, top: `${20 + ((i * 53) % 70)}%`, delay: `${(i * 0.9) % 9}s`,
    dx: `${((i * 17) % 60) - 30}px`, size: 2 + (i % 3),
  })), [])
  return (
    <div aria-hidden className="pointer-events-none absolute inset-0 -z-10 overflow-hidden">
      <div className="absolute -top-40 left-1/2 h-[560px] w-[900px] -translate-x-1/2 animate-ambient rounded-full bg-accent/25 blur-[140px] will-change-transform" />
      <div className="absolute right-[-10%] top-[35%] h-[380px] w-[380px] animate-ambient rounded-full bg-accent/10 blur-[120px] [animation-delay:-6s]" />
      <div className="bg-grid absolute inset-0" />
      <svg className="absolute inset-0 h-full w-full opacity-40" preserveAspectRatio="none" viewBox="0 0 1000 800">
        {['M0 220 C250 120 400 340 640 200 S900 140 1000 260', 'M0 520 C220 420 480 640 700 480 S940 400 1000 520'].map((d) => (
          <path key={d} d={d} fill="none" stroke="#E50914" strokeOpacity=".5" strokeWidth="1" strokeDasharray="6 14" className="animate-dash" />
        ))}
      </svg>
      {dots.map((d, i) => (
        <span key={i} className="absolute animate-drift rounded-full bg-accent/80"
          style={{ left: d.left, top: d.top, width: d.size, height: d.size, animationDelay: d.delay, ['--dx' as string]: d.dx }} />
      ))}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,transparent_40%,#09090B_100%)]" />
    </div>
  )
}

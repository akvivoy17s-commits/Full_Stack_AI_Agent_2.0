// DOM motion helpers for generated React pages. Cleanup is StrictMode-safe.
export function initMotion(): () => void {
  const reduceMotion = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches ?? false
  const finePointer = window.matchMedia?.('(hover: hover) and (pointer: fine)').matches ?? false
  const cleanups: Array<() => void> = []
  const clamp = (n: number, min: number, max: number) => Math.min(max, Math.max(min, n))
  const reveals = Array.from(document.querySelectorAll<HTMLElement>('.reveal,.reveal-left,.reveal-scale,[data-reveal]'))
  reveals.forEach((el) => { if (el.dataset.delay) el.style.setProperty('--d', String(clamp(Number(el.dataset.delay) || 0, 0, 20))) })
  if (reduceMotion || !('IntersectionObserver' in window)) reveals.forEach((el) => el.classList.add('in'))
  else if (reveals.length) {
    const observer = new IntersectionObserver((entries) => entries.forEach((entry) => {
      if (entry.isIntersecting) { entry.target.classList.add('in'); observer.unobserve(entry.target) }
    }), { threshold: 0.14 })
    reveals.forEach((el) => observer.observe(el))
    cleanups.push(() => observer.disconnect())
  }

  const nav = document.querySelector('.nav')
  const parallax = Array.from(document.querySelectorAll<HTMLElement>('[data-parallax]')).filter((el) => {
    const value = el.dataset.parallax
    return value !== undefined && value !== 'mouse' && Number.isFinite(Number(value))
  })
  let scrollRaf = 0
  const onScroll = () => {
    cancelAnimationFrame(scrollRaf)
    scrollRaf = requestAnimationFrame(() => {
      nav?.classList.toggle('scrolled', window.scrollY > 20)
      if (!reduceMotion) parallax.forEach((el) => {
        const speed = clamp(Number(el.dataset.parallax), -0.8, 0.8)
        el.style.setProperty('--scroll-parallax-y', `${clamp(window.scrollY * speed, -500, 500)}px`)
      })
    })
  }
  window.addEventListener('scroll', onScroll, { passive: true })
  cleanups.push(() => { window.removeEventListener('scroll', onScroll); cancelAnimationFrame(scrollRaf) })
  onScroll()

  const tiltNodes = new Set(Array.from(document.querySelectorAll<HTMLElement>('[data-tilt],[data-animation="tilt-3d"],.tilt-3d')))
  if (finePointer && !reduceMotion) tiltNodes.forEach((el) => {
    let raf = 0
    const move = (event: PointerEvent) => {
      const rect = el.getBoundingClientRect()
      if (!rect.width || !rect.height) return
      const raw = Number(el.dataset.tiltMax ?? el.dataset.tilt ?? 10)
      const max = clamp(Number.isFinite(raw) ? raw : 10, 2, 20)
      const x = clamp((0.5 - (event.clientY - rect.top) / rect.height) * max * 2, -max, max)
      const y = clamp(((event.clientX - rect.left) / rect.width - 0.5) * max * 2, -max, max)
      cancelAnimationFrame(raf)
      raf = requestAnimationFrame(() => {
        el.style.setProperty('--tilt-x', `${x.toFixed(2)}deg`)
        el.style.setProperty('--tilt-y', `${y.toFixed(2)}deg`)
      })
    }
    const reset = () => {
      cancelAnimationFrame(raf)
      el.style.setProperty('--tilt-x', '0deg')
      el.style.setProperty('--tilt-y', '0deg')
    }
    el.addEventListener('pointermove', move, { passive: true })
    el.addEventListener('pointerleave', reset, { passive: true })
    cleanups.push(() => { el.removeEventListener('pointermove', move); el.removeEventListener('pointerleave', reset); cancelAnimationFrame(raf) })
  })

  const mouseLayers = Array.from(document.querySelectorAll<HTMLElement>('[data-mouse-parallax]'))
  if (finePointer && !reduceMotion && mouseLayers.length) {
    let raf = 0
    const onPointerMove = (event: PointerEvent) => {
      cancelAnimationFrame(raf)
      raf = requestAnimationFrame(() => {
        const nx = (event.clientX / Math.max(window.innerWidth, 1) - 0.5) * 2
        const ny = (event.clientY / Math.max(window.innerHeight, 1) - 0.5) * 2
        mouseLayers.forEach((el) => {
          const raw = Number(el.dataset.mouseParallax)
          const depth = clamp(Number.isFinite(raw) && raw !== 0 ? raw : 8, 1, 30)
          el.style.setProperty('--mouse-parallax-x', `${(-nx * depth).toFixed(2)}px`)
          el.style.setProperty('--mouse-parallax-y', `${(-ny * depth).toFixed(2)}px`)
        })
      })
    }
    window.addEventListener('pointermove', onPointerMove, { passive: true })
    cleanups.push(() => { window.removeEventListener('pointermove', onPointerMove); cancelAnimationFrame(raf) })
  }

  document.querySelectorAll<HTMLElement>('[data-count]').forEach((el) => {
    const end = Number(el.dataset.count)
    if (!Number.isFinite(end)) return
    if (reduceMotion || !('IntersectionObserver' in window)) { el.textContent = String(end); return }
    const duration = clamp(Number(el.dataset.countDuration) || 1400, 250, 5000)
    let raf = 0
    const observer = new IntersectionObserver(([entry]) => {
      if (!entry?.isIntersecting) return
      observer.disconnect()
      const start = performance.now()
      const step = (now: number) => {
        const progress = Math.min((now - start) / duration, 1)
        el.textContent = String(Math.round(end * (1 - Math.pow(1 - progress, 3))))
        if (progress < 1) raf = requestAnimationFrame(step)
      }
      raf = requestAnimationFrame(step)
    }, { threshold: 0.4 })
    observer.observe(el)
    cleanups.push(() => { observer.disconnect(); cancelAnimationFrame(raf) })
  })
  return () => cleanups.forEach((dispose) => dispose())
}

(() => {
  'use strict';
  const reduceMotion = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches ?? false;
  const finePointer = window.matchMedia?.('(hover: hover) and (pointer: fine)').matches ?? false;
  const cleanups = [];
  const clamp = (n, min, max) => Math.min(max, Math.max(min, n));

  // Reveal nodes only once as they enter the viewport. Numeric data-delay is a stagger index.
  const revealNodes = [...document.querySelectorAll('.reveal,.reveal-left,.reveal-scale,[data-reveal]')];
  revealNodes.forEach((el) => {
    if (el.dataset.delay && Number.isFinite(Number(el.dataset.delay))) el.style.setProperty('--d', String(clamp(Number(el.dataset.delay), 0, 20)));
    if (!el.matches('.reveal,.reveal-left,.reveal-scale') && !el.hasAttribute('data-reveal')) el.dataset.reveal = 'up';
  });
  if (reduceMotion || !('IntersectionObserver' in window)) {
    revealNodes.forEach((el) => el.classList.add('in'));
  } else if (revealNodes.length) {
    const revealObserver = new IntersectionObserver((entries) => entries.forEach((entry) => {
      if (entry.isIntersecting) { entry.target.classList.add('in'); revealObserver.unobserve(entry.target); }
    }), { threshold: 0.14, rootMargin: '0px 0px -3% 0px' });
    revealNodes.forEach((el) => revealObserver.observe(el));
    cleanups.push(() => revealObserver.disconnect());
  }

  const nav = document.querySelector('.nav');
  const scrollLayers = [...document.querySelectorAll('[data-parallax]')].filter((el) => {
    const v = el.getAttribute('data-parallax');
    return v !== null && v !== 'mouse' && Number.isFinite(Number(v));
  });
  let scrollQueued = false;
  const onScroll = () => {
    if (scrollQueued) return;
    scrollQueued = true;
    requestAnimationFrame(() => {
      nav?.classList.toggle('scrolled', window.scrollY > 20);
      if (!reduceMotion) scrollLayers.forEach((el) => {
        const speed = clamp(Number(el.getAttribute('data-parallax')), -0.8, 0.8);
        el.style.setProperty('--scroll-parallax-y', `${clamp(window.scrollY * speed, -500, 500)}px`);
      });
      scrollQueued = false;
    });
  };
  window.addEventListener('scroll', onScroll, { passive: true });
  cleanups.push(() => window.removeEventListener('scroll', onScroll));
  onScroll();

  // Pointer-based card tilt uses CSS variables, so authored transforms are not overwritten.
  const tiltNodes = new Set([...document.querySelectorAll('[data-tilt],[data-animation="tilt-3d"],.tilt-3d')]);
  if (finePointer && !reduceMotion) tiltNodes.forEach((el) => {
    let raf = 0;
    const move = (event) => {
      const rect = el.getBoundingClientRect();
      if (!rect.width || !rect.height) return;
      const max = clamp(Number(el.getAttribute('data-tilt-max') || (Number(el.getAttribute('data-tilt')) || 10)), 2, 20);
      const px = (event.clientX - rect.left) / rect.width;
      const py = (event.clientY - rect.top) / rect.height;
      const x = clamp((0.5 - py) * max * 2, -max, max);
      const y = clamp((px - 0.5) * max * 2, -max, max);
      cancelAnimationFrame(raf);
      raf = requestAnimationFrame(() => {
        el.style.setProperty('--tilt-x', `${x.toFixed(2)}deg`);
        el.style.setProperty('--tilt-y', `${y.toFixed(2)}deg`);
      });
    };
    const reset = () => {
      cancelAnimationFrame(raf);
      el.style.setProperty('--tilt-x', '0deg');
      el.style.setProperty('--tilt-y', '0deg');
    };
    el.addEventListener('pointermove', move, { passive: true });
    el.addEventListener('pointerleave', reset, { passive: true });
    el.addEventListener('pointercancel', reset, { passive: true });
    cleanups.push(() => { el.removeEventListener('pointermove', move); el.removeEventListener('pointerleave', reset); el.removeEventListener('pointercancel', reset); cancelAnimationFrame(raf); });
  });

  // Mouse parallax is opt-in and disabled for coarse/touch pointers and reduced-motion users.
  const mouseLayers = [...document.querySelectorAll('[data-mouse-parallax]')];
  if (finePointer && !reduceMotion && mouseLayers.length) {
    let pointerRaf = 0;
    const onPointerMove = (event) => {
      cancelAnimationFrame(pointerRaf);
      pointerRaf = requestAnimationFrame(() => {
        const nx = (event.clientX / Math.max(window.innerWidth, 1) - 0.5) * 2;
        const ny = (event.clientY / Math.max(window.innerHeight, 1) - 0.5) * 2;
        mouseLayers.forEach((el) => {
          const depth = clamp(Number(el.getAttribute('data-mouse-parallax')) || 8, 1, 30);
          el.style.setProperty('--mouse-parallax-x', `${(-nx * depth).toFixed(2)}px`);
          el.style.setProperty('--mouse-parallax-y', `${(-ny * depth).toFixed(2)}px`);
        });
      });
    };
    const resetPointer = () => mouseLayers.forEach((el) => {
      el.style.setProperty('--mouse-parallax-x', '0px');
      el.style.setProperty('--mouse-parallax-y', '0px');
    });
    window.addEventListener('pointermove', onPointerMove, { passive: true });
    window.addEventListener('blur', resetPointer);
    cleanups.push(() => { window.removeEventListener('pointermove', onPointerMove); window.removeEventListener('blur', resetPointer); cancelAnimationFrame(pointerRaf); });
  }

  // Animated counters, with a reduced-motion-safe final value.
  document.querySelectorAll('[data-count]').forEach((el) => {
    const end = Number(el.getAttribute('data-count'));
    if (!Number.isFinite(end)) return;
    if (reduceMotion || !('IntersectionObserver' in window)) { el.textContent = String(end); return; }
    const duration = clamp(Number(el.getAttribute('data-count-duration')) || 1400, 250, 5000);
    let raf = 0;
    const counterObserver = new IntersectionObserver(([entry]) => {
      if (!entry?.isIntersecting) return;
      counterObserver.disconnect();
      const started = performance.now();
      const step = (now) => {
        const progress = Math.min((now - started) / duration, 1);
        el.textContent = String(Math.round(end * (1 - Math.pow(1 - progress, 3))));
        if (progress < 1) raf = requestAnimationFrame(step);
      };
      raf = requestAnimationFrame(step);
    }, { threshold: 0.4 });
    counterObserver.observe(el);
    cleanups.push(() => { counterObserver.disconnect(); cancelAnimationFrame(raf); });
  });

  // Keep motion setup disposable for embedding and client-side navigation.
  window.addEventListener('pagehide', () => cleanups.splice(0).forEach((dispose) => dispose()), { once: true });
})();

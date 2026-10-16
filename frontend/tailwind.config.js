/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: { bg: '#09090B', surface: '#151515', accent: '#E50914', accentSoft: '#FF4D55' },
      fontFamily: { sans: ['"Inter Variable"', 'system-ui', 'sans-serif'], display: ['"Space Grotesk Variable"', '"Inter Variable"', 'sans-serif'] },
      boxShadow: { glow: '0 0 40px -8px rgba(229,9,20,.55)', soft: '0 8px 30px -12px rgba(0,0,0,.8)' },
      keyframes: {
        float: { '0%,100%': { transform: 'translate3d(0,0,0)' }, '50%': { transform: 'translate3d(0,-10px,0)' } },
        drift: { '0%': { transform: 'translate3d(0,0,0)', opacity: 0 }, '15%': { opacity: 1 }, '100%': { transform: 'translate3d(var(--dx),-120px,0)', opacity: 0 } },
        ambient: { '0%,100%': { transform: 'translate3d(-4%,0,0) scale(1)' }, '50%': { transform: 'translate3d(4%,3%,0) scale(1.08)' } },
        dash: { to: { strokeDashoffset: '-40' } },
        blink: { '50%': { opacity: 0 } },
      },
      animation: { float: 'float 6s ease-in-out infinite', drift: 'drift 9s linear infinite', ambient: 'ambient 16s ease-in-out infinite', dash: 'dash 2.4s linear infinite', blink: 'blink 1s steps(2) infinite' },
    },
  },
  plugins: [],
}

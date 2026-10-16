export const STYLES = ['Premium SaaS', 'Cinematic dark', 'Anime streaming platform', 'E-commerce storefront', 'Interactive portfolio', 'Analytics dashboard',
  'Editorial', 'Creative agency', 'Futuristic interface', 'Glassmorphism', 'Product landing page']
export const MOTION = ['subtle', 'balanced', 'expressive'] as const

export const EXAMPLES: { label: string; text: string }[] = [
  { label: 'Fitness app landing', text: 'Landing page for a fitness tracking app with pricing, testimonials and smooth scroll animations' },
  { label: 'Online store', text: 'Online store for handmade candles with product list, cart, checkout and admin product management' },
  { label: 'Team dashboard', text: 'Project management dashboard with login, tasks, projects, team roles and weekly progress charts' },
]

export const STACK_LABELS: [string, string][] = [
  ['frontend', 'Frontend'], ['frontend_lang', 'Frontend language'], ['backend', 'Backend'], ['backend_lang', 'Backend language'],
  ['database', 'Database'], ['orm', 'Data access'], ['auth', 'Authentication'], ['cache', 'Cache'], ['storage', 'File storage'],
  ['ai', 'AI'], ['testing', 'Frontend tests'], ['deploy', 'Deployment'],
]

// Keep generated markup compatible with the prebuilt animation assets. Effects are opt-in,
// chosen only when they fit the user's requested aesthetic, and never forced onto data-heavy UI.
const MOTION_GUIDANCE = [
  'Animation implementation: use the prebuilt motion hooks when suitable: .reveal / data-reveal="up|left|right|scale|fade" for scroll reveals; data-float="soft|normal|strong" for floating objects; data-tilt="3d" or data-animation="tilt-3d" for perspective cards; data-parallax="0.1" for scroll parallax; data-mouse-parallax="8" for pointer parallax.',
  'For a requested cinematic/3D hero, the plain HTML template supports an optional data-three-hero or data-3d="three-hero" hook. Keep hero text and controls above the scene. For React, framer-motion helpers are available; the Hero3D component can be imported only if a 3D scene is appropriate.',
  'Prefer a coherent preset (flat, float, tilt-3d, parallax, or three-hero) that matches the brief; do not combine every effect. Use semantic, accessible markup, avoid motion on forms/tables or essential controls, and respect prefers-reduced-motion.',
].join('\n')

export function composeBrief(brief: string, style: string, motion: string) {
  return `${brief.trim()}\n\nDesign style: ${style}. Animation intensity: ${motion}.\n${MOTION_GUIDANCE}`
}

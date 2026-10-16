import { lazy, Suspense, useEffect, useState } from 'react'
import Landing from './landing/Landing'

const Workspace = lazy(() => import('./workspace/Workspace'))

/** Tiny hash router: #/ = landing, #/workspace[/projectId] = workspace. Keeps dependencies minimal. */
function parse(): { page: 'landing' | 'workspace'; id: string | null } {
  const m = window.location.hash.match(/^#\/workspace(?:\/([\w-]+))?/)
  return m ? { page: 'workspace', id: m[1] ?? null } : { page: 'landing', id: null }
}

export default function App() {
  const [route, setRoute] = useState(parse)
  useEffect(() => {
    const on = () => setRoute(parse())
    window.addEventListener('hashchange', on)
    return () => window.removeEventListener('hashchange', on)
  }, [])
  if (route.page === 'workspace')
    return (
      <Suspense fallback={<div className="grid h-screen place-items-center text-zinc-500">Loading workspace…</div>}>
        <Workspace projectId={route.id} />
      </Suspense>
    )
  return <Landing />
}

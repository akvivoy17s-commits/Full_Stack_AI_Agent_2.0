import { Canvas, useFrame } from '@react-three/fiber'
import { useRef } from 'react'
import type { Group } from 'three'

type Hero3DProps = { className?: string; color?: string; label?: string }

function SceneObjects({ color }: { color: string }) {
  const group = useRef<Group>(null)
  useFrame((_, delta) => {
    if (!group.current) return
    group.current.rotation.y += delta * 0.16
    group.current.rotation.x += delta * 0.045
  })
  return <group ref={group}>
    <mesh>
      <icosahedronGeometry args={[1.05, 1]} />
      <meshStandardMaterial color={color} metalness={0.58} roughness={0.28} wireframe />
    </mesh>
    <mesh rotation={[0.65, 0.25, 0.3]}>
      <torusGeometry args={[1.55, 0.018, 8, 96]} />
      <meshStandardMaterial color="#67e8f9" metalness={0.55} roughness={0.24} />
    </mesh>
    <mesh rotation={[1.05, -0.5, 0.8]}>
      <torusGeometry args={[1.9, 0.012, 6, 96]} />
      <meshStandardMaterial color="#c4b5fd" metalness={0.5} roughness={0.25} />
    </mesh>
  </group>
}

/** Optional decorative WebGL scene. Keep the hero headline/buttons outside this canvas. */
export default function Hero3D({ className = '', color = '#8b5cf6', label = 'Decorative three-dimensional hero scene' }: Hero3DProps) {
  return <div className={className} role="img" aria-label={label}>
    <Canvas dpr={[1, 1.5]} camera={{ position: [0, 0, 5.8], fov: 44 }} gl={{ alpha: true, antialias: true, powerPreference: 'low-power' }}>
      <ambientLight intensity={1.5} />
      <pointLight color={color} intensity={24} position={[3, 3, 5]} />
      <pointLight color="#38bdf8" intensity={12} position={[-4, -2, 1]} />
      <SceneObjects color={color} />
    </Canvas>
  </div>
}

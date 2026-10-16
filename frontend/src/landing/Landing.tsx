import { motion } from 'motion/react'
import { useOllama } from '../hooks/useOllama'
import Background from './Background'
import Nav from './Nav'
import Hero from './Hero'
import Capabilities from './Capabilities'
import Workflow from './Workflow'
import Demo from './Demo'
import About from './About'
import CTA from './CTA'
import Footer from './Footer'

export default function Landing() {
  const { conn } = useOllama()
  return (
    <div className="relative min-h-screen overflow-x-clip">
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 1.2 }}><Background /></motion.div>
      <Nav />
      <main>
        <Hero conn={conn} />
        <Capabilities />
        <Workflow />
        <Demo />
        <About />
        <CTA />
      </main>
      <Footer />
    </div>
  )
}

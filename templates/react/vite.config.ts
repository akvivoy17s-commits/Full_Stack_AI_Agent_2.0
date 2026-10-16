import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// base './' lets the built site work from any sub-path (live preview, zip export, static hosting)
export default defineConfig({ base: './', plugins: [react()], build: { outDir: 'dist' } })

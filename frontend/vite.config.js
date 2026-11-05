import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: true
  },
  build: {
    rollupOptions: {
      output: {
        // Split rarely-changing vendor code so it caches independently of app code
        manualChunks(id) {
          if (!id.includes('node_modules')) return undefined
          if (id.includes('leaflet')) return 'vendor-leaflet'
          if (id.includes('framer-motion') || id.includes('/motion')) return 'vendor-motion'
          if (id.includes('react') || id.includes('scheduler')) return 'vendor-react'
          return undefined
        }
      }
    }
  }
})

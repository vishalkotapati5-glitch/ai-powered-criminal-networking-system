import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: { proxy: { '/api': 'http://localhost:8000' } },
  test: { environment: 'node' },
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes('node_modules/recharts/')) return 'recharts'
          if (id.includes('node_modules/d3-')) return 'd3'
          if (id.includes('node_modules/@xyflow/')) return 'network-flow'
        },
      },
    },
  },
})

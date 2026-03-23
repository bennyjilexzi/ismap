import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true,
        // Required for Server-Sent Events (SSE) streaming to work correctly
        // through the Vite dev proxy
        configure: (proxy) => {
          proxy.on('proxyReq', (proxyReq) => {
            // Remove any encoding that would prevent streaming
            proxyReq.removeHeader('accept-encoding')
          })
        }
      }
    }
  }
})

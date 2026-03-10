import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://localhost:5000',
      '/register': 'http://localhost:5000',
      '/discover': 'http://localhost:5000',
      '/configure_alerts': 'http://localhost:5000',
      '/scan': 'http://localhost:5000'
    }
  }
})

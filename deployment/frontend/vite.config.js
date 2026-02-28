import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
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

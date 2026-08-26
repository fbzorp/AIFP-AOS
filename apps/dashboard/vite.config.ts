import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    host: '0.0.0.0',
    port: 3000,
    proxy: {
      '/api': {
        target: process.env.VITE_DEV_API_PROXY || 'http://host.docker.internal:8000',
        changeOrigin: true,
        secure: false,
        rewrite: (path) => path, // Keep path as-is since we now use /api/v1 prefix
      },
      '/health': {
        target: process.env.VITE_DEV_API_PROXY || 'http://host.docker.internal:8000',
        changeOrigin: true,
        secure: false,
      },
    },
  },
})

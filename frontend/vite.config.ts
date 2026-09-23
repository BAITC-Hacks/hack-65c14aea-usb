import { fileURLToPath, URL } from 'node:url'
import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'
export default defineConfig(({ mode }) => {
 const env = loadEnv(mode, process.cwd(), '')
 const backend = env.API_PROXY_TARGET || 'http://127.0.0.1:8000'
 return {
  plugins: [vue(), tailwindcss()],
  resolve: { alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) } },
  server: {
   proxy: {
    '/api': { target: backend, changeOrigin: true },
    '/ready': { target: backend, changeOrigin: true },
    '/health': { target: backend, changeOrigin: true },
   },
  },
 }
})

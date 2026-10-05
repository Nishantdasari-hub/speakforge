import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import { fileURLToPath } from 'node:url'

const envDir = fileURLToPath(new URL('..', import.meta.url))

export default defineConfig(({ command, mode }) => {
  const env = loadEnv(mode, envDir, 'VITE_')
  if (command === 'build' && !env.VITE_API_URL?.trim()) {
    throw new Error('Set VITE_API_URL to the public backend URL before building.')
  }
  return { plugins: [react()], envDir }
})

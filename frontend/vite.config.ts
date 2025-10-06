import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
    plugins: [react()],
    // In local dev, the API is exposed on host port 8010 via docker-compose
    server: { proxy: { '/api': 'http://localhost:8010' } },
    build: { outDir: 'dist' }
})

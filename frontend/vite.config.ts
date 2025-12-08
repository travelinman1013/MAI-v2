import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

/**
 * MAI Framework V2 - Vite Configuration
 *
 * IMPORTANT: No proxy configuration is used.
 * All routing is handled by the Caddy ingress in production.
 *
 * The frontend uses relative paths (/api/*) which Caddy
 * routes to the backend container.
 */
export default defineConfig(({ command }) => {
  const isDevelopment = command === 'serve'

  return {
    plugins: [react()],

    // Base path for deployment
    base: '/',

    // Build configuration
    build: {
      outDir: 'dist',
      sourcemap: false,
      target: 'esnext',
      minify: 'esbuild',
      assetsDir: 'assets',
      emptyOutDir: true,

      // Chunk splitting for better caching
      rollupOptions: {
        output: {
          manualChunks: {
            'react-vendor': ['react', 'react-dom'],
          },
        },
      },
    },

    // Development server (local only, no proxy)
    server: isDevelopment ? {
      port: 5173,
      host: true,
      // NO PROXY - In dev, run docker-compose and access via localhost:80
    } : {},

    // Path aliases
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
      },
    },

    // Preview server for testing production builds
    preview: {
      port: 4173,
      host: true,
    },
  }
})

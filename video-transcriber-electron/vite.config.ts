import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import electron from 'vite-plugin-electron'
import renderer from 'vite-plugin-electron-renderer'
import { resolve } from 'path'

export default defineConfig({
  plugins: [
    react(),
    electron([
      {
        // Main process
        entry: 'electron/main.ts',
        onstart(args) {
          // Notify that Electron App is started
          args.startup(['--', '--develop'])
        },
        vite: {
          build: {
            sourcemap: true,
            minify: process.env.NODE_ENV === 'production',
            outDir: 'dist/electron',
            rollupOptions: {
              external: ['electron']
            }
          }
        }
      },
      {
        // Preload script
        entry: 'electron/preload.ts',
        onstart(args) {
          // Reload page when preload script is updated
          args.reload()
        },
        vite: {
          build: {
            sourcemap: 'inline',
            minify: process.env.NODE_ENV === 'production',
            outDir: 'dist/electron',
            rollupOptions: {
              external: ['electron']
            }
          }
        }
      }
    ]),
    // Use electron renderer
    renderer()
  ],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
      '@components': resolve(__dirname, 'src/components'),
      '@services': resolve(__dirname, 'src/services'),
      '@store': resolve(__dirname, 'src/store'),
      '@theme': resolve(__dirname, 'src/theme'),
      '@utils': resolve(__dirname, 'src/utils'),
      '@types': resolve(__dirname, 'src/types')
    }
  },
  server: {
    host: process.env.VITE_DEV_SERVER_HOST,
    port: parseInt(process.env.VITE_DEV_SERVER_PORT ?? '5175')
  },
  build: {
    sourcemap: true,
    outDir: 'dist',
    rollupOptions: {
      input: {
        main: resolve(__dirname, 'index.html')
      }
    }
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts']
  }
})
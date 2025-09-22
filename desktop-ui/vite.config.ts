import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import electron from 'vite-plugin-electron'
import renderer from 'vite-plugin-electron-renderer'
import path from 'path'

export default defineConfig({
  plugins: [
    react(),
    electron([
      {
        entry: 'src/main/main.ts',
        onstart(options) {
          options.startup()
        },
        vite: {
          build: {
            outDir: 'dist',
          },
          rollupOptions: {
            external: ['electron', 'fs', 'fs/promises', 'path', 'child_process', 'app']
          }
        },
      },
      {
        entry: 'src/main/preload.ts',
        onstart(options) {
          options.startup()
        },
        vite: {
          build: {
            outDir: 'dist',
          },
          rollupOptions: {
            external: ['electron', 'fs', 'fs/promises', 'path', 'child_process', 'app']
          }
        },
      },
    ]),
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src/renderer'),
      '@components': path.resolve(__dirname, 'src/renderer/components'),
      '@lib': path.resolve(__dirname, 'src/renderer/lib'),
      '@types': path.resolve(__dirname, 'src/renderer/types'),
      '@hooks': path.resolve(__dirname, 'src/renderer/hooks'),
      '@stores': path.resolve(__dirname, 'src/renderer/stores'),
    },
  },
  server: {
    port: 3000,
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
  },
})
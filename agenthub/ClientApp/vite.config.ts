import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    },
    dedupe: ['vue', 'vue-router']
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true
      },
      '/hubs': {
        target: 'http://localhost:5000',
        ws: true
      }
    }
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true,
    rollupOptions: {
      output: {
        manualChunks: {
          'vue-vendor': ['vue', 'vue-router', 'pinia', 'vue-i18n'],
          'chart-vendor': ['chart.js', 'vue-chartjs'],
          'axios-vendor': ['axios']
        }
      },
      onwarn(warning, warn) {
        // 특정 경고 무시 (Rollup 경고)
        if (warning.code === 'MODULE_LEVEL_DIRECTIVE') {
          return
        }
        if (warning.code === 'THIS_IS_UNDEFINED') {
          return
        }
        // 외부화 관련 경고 무시 (의도된 동작)
        if (warning.message && warning.message.includes('external')) {
          return
        }
        // 일반적인 Rollup 경고는 출력
        warn(warning)
      }
    },
    commonjsOptions: {
      include: [/node_modules/],
      transformMixedEsModules: true
    }
  },
  optimizeDeps: {
    include: ['vue', 'vue-router', 'pinia', 'axios', 'chart.js', 'vue-chartjs', 'marked', 'dompurify', 'prismjs', 'vue-i18n'],
    esbuildOptions: {
      define: {
        global: 'globalThis'
      }
    }
  }
})

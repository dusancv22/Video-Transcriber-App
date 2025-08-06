import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import { resolve } from 'path'

export default defineConfig({
  plugins: [react()],
  
  test: {
    // Environment configuration
    globals: true,
    environment: 'jsdom',
    
    // Setup files
    setupFiles: ['./src/test/setup.ts'],
    
    // Test patterns for integration tests
    include: [
      'tests/integration/**/*.test.ts',
      'tests/integration/**/*.test.tsx',
      'tests/e2e/**/*.test.ts',
      'tests/e2e/**/*.test.tsx'
    ],
    
    // Exclude unit tests and build files
    exclude: [
      'node_modules',
      'dist',
      'build',
      'src/**/*.test.ts', // Unit tests
      'src/**/*.test.tsx'
    ],
    
    // Coverage configuration
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      reportsDirectory: './coverage/integration',
      include: [
        'src/components/**/*.{ts,tsx}',
        'src/services/**/*.{ts,tsx}',
        'src/store/**/*.{ts,tsx}',
        'src/utils/**/*.{ts,tsx}'
      ],
      exclude: [
        'src/**/*.test.{ts,tsx}',
        'src/test/**/*',
        'src/**/*.d.ts',
        'src/**/index.{ts,tsx}'
      ],
      thresholds: {
        global: {
          branches: 70,
          functions: 70,
          lines: 70,
          statements: 70
        },
        // Higher thresholds for security-critical components
        'src/components/FileDropZone.tsx': {
          branches: 85,
          functions: 85,
          lines: 85,
          statements: 85
        },
        'src/components/QueuePanel.tsx': {
          branches: 85,
          functions: 85,
          lines: 85,
          statements: 85
        },
        'src/components/SettingsDialog.tsx': {
          branches: 80,
          functions: 80,
          lines: 80,
          statements: 80
        }
      }
    },
    
    // Test timeout configuration
    testTimeout: 30000, // 30 seconds for integration tests
    hookTimeout: 10000,  // 10 seconds for setup/teardown
    
    // Retry configuration
    retry: 2, // Retry flaky tests twice
    
    // Reporters
    reporter: [
      'verbose',
      'junit',
      'html'
    ],
    
    // Output files
    outputFile: {
      junit: './test-results/integration-results.xml',
      html: './test-results/integration-report.html'
    },
    
    // Mock configuration
    clearMocks: true,
    restoreMocks: true,
    mockReset: true,
    
    // Security test configuration
    watchExclude: [
      '**/node_modules/**',
      '**/dist/**',
      '**/coverage/**',
      '**/test-results/**'
    ],
    
    // Parallel execution
    pool: 'threads',
    poolOptions: {
      threads: {
        singleThread: false,
        minThreads: 1,
        maxThreads: 4
      }
    },
    
    // File watching
    watch: false, // Disable watch mode for CI/CD
    
    // Dependencies optimization
    deps: {
      inline: [
        // Inline these packages for better testing
        '@testing-library/react',
        '@testing-library/user-event',
        '@mui/material'
      ]
    }
  },
  
  // Path resolution for imports
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
  
  // Build configuration for test dependencies
  build: {
    target: 'node14'
  },
  
  // Define for environment variables
  define: {
    'import.meta.env.VITE_API_URL': JSON.stringify('http://localhost:8000'),
    'import.meta.env.VITE_WS_URL': JSON.stringify('ws://localhost:8000/ws'),
    'import.meta.env.NODE_ENV': JSON.stringify('test')
  }
})
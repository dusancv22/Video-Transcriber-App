import '@testing-library/jest-dom'
import { vi } from 'vitest'

// Mock Electron APIs
global.window = global.window || {}
global.window.electronAPI = {
  dialog: {
    showOpenDialog: vi.fn(),
  },
  shell: {
    showItemInFolder: vi.fn(),
    openExternal: vi.fn(),
  },
  path: {
    join: vi.fn(),
    dirname: vi.fn(),
    basename: vi.fn(),
    resolve: vi.fn(),
  },
  fs: {
    existsSync: vi.fn(),
    readFileSync: vi.fn(),
    writeFileSync: vi.fn(),
  }
}

// Mock navigator.clipboard
Object.assign(navigator, {
  clipboard: {
    writeText: vi.fn(),
  },
})

// Mock console methods to reduce noise in tests
global.console = {
  ...console,
  log: vi.fn(),
  error: vi.fn(),
  warn: vi.fn(),
}

// Add custom matchers if needed
expect.extend({})
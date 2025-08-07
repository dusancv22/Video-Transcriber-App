export interface ElectronAPI {
  // App information
  app: {
    getVersion: () => Promise<string>
    getPlatform: () => Promise<string>
  }

  // File system dialogs
  dialog: {
    showOpenDialog: (options: Electron.OpenDialogOptions) => Promise<Electron.OpenDialogReturnValue>
    showSaveDialog: (options: Electron.SaveDialogOptions) => Promise<Electron.SaveDialogReturnValue>
  }

  // Shell operations
  shell: {
    openExternal: (url: string) => Promise<void>
    showItemInFolder: (fullPath: string) => Promise<void>
  }

  // System notifications
  notification: {
    show: (title: string, body: string, options?: NotificationOptions) => void
  }

  // Path utilities
  path: {
    getDefaultOutputDirectory: () => Promise<string>
    getUserDocumentsPath: () => Promise<string>
  }

  // File utilities - IPC-based approach
  file: {
    getFilePathsFromDrop: (files: FileList) => Promise<string[]>
    selectVideoFiles: () => Promise<string[]>
  }

  // Window controls for frameless window
  window: {
    close: () => Promise<void>
    minimize: () => Promise<void>
    maximize: () => Promise<void>
    toggleDevTools: () => Promise<void>
  }

  // System metrics for status bar
  system: {
    getMemoryUsage: () => Promise<{ total: number; used: number; free: number; usedPercentage: number }>
    getDiskSpace: (path?: string) => Promise<{ total: number; free: number; used: number }>
    getCPUInfo: () => Promise<{ cores: number; model: string; hasGPU: boolean; processingMode: string }>
  }

  // Backend health check
  backend: {
    healthCheck: () => Promise<{ status: string; timestamp: number }>
  }
}

declare global {
  interface Window {
    electronAPI: ElectronAPI
    environment: {
      isElectron: boolean
      isDev: boolean
      platform: string
    }
  }
}

export {}
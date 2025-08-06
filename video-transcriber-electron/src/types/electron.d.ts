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
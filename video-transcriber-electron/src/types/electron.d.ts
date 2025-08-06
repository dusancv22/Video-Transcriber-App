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
import { contextBridge, ipcRenderer } from 'electron'

// Define the API that will be exposed to the renderer process
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

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
const electronAPI: ElectronAPI = {
  app: {
    getVersion: () => ipcRenderer.invoke('app:getVersion'),
    getPlatform: () => ipcRenderer.invoke('app:getPlatform')
  },

  dialog: {
    showOpenDialog: (options) => ipcRenderer.invoke('dialog:showOpenDialog', options),
    showSaveDialog: (options) => ipcRenderer.invoke('dialog:showSaveDialog', options)
  },

  shell: {
    openExternal: (url) => ipcRenderer.invoke('shell:openExternal', url),
    showItemInFolder: (fullPath) => ipcRenderer.invoke('shell:showItemInFolder', fullPath)
  },

  notification: {
    show: (title: string, body: string, options?: NotificationOptions) => {
      if (window.Notification && Notification.permission === 'granted') {
        new Notification(title, { body, ...options })
      } else if (window.Notification && Notification.permission !== 'denied') {
        Notification.requestPermission().then(permission => {
          if (permission === 'granted') {
            new Notification(title, { body, ...options })
          }
        })
      }
    }
  }
}

// Use `contextBridge` APIs to expose Electron APIs to
// renderer only if context isolation is enabled, otherwise
// just add to the DOM global.
if (process.contextIsolated) {
  try {
    contextBridge.exposeInMainWorld('electronAPI', electronAPI)
  } catch (error) {
    console.error('Failed to expose electronAPI:', error)
  }
} else {
  // @ts-ignore (define in dts)
  window.electronAPI = electronAPI
}

// Expose environment information
contextBridge.exposeInMainWorld('environment', {
  isElectron: true,
  isDev: process.env.NODE_ENV === 'development',
  platform: process.platform
})

// Security: Remove access to Node.js APIs
delete (window as any).require
delete (window as any).exports
delete (window as any).module
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
  },

  path: {
    getDefaultOutputDirectory: () => ipcRenderer.invoke('path:getDefaultOutputDirectory'),
    getUserDocumentsPath: () => ipcRenderer.invoke('path:getUserDocumentsPath')
  },

  file: {
    getFilePathsFromDrop: (files: FileList) => {
      // Convert FileList to serializable data and send via IPC
      const fileData = Array.from(files).map(file => ({
        name: file.name,
        size: file.size,
        type: file.type,
        lastModified: file.lastModified
      }))
      return ipcRenderer.invoke('file:getFilePathsFromDrop', fileData)
    },
    
    
    selectVideoFiles: () => ipcRenderer.invoke('file:selectVideoFiles')
  },

  window: {
    close: () => ipcRenderer.invoke('window:close'),
    minimize: () => ipcRenderer.invoke('window:minimize'),
    maximize: () => ipcRenderer.invoke('window:maximize'),
    toggleDevTools: () => ipcRenderer.invoke('window:toggleDevTools')
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
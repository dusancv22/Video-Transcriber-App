import { app, BrowserWindow, shell, ipcMain, dialog, globalShortcut } from 'electron'
import { join } from 'path'
import { spawn, ChildProcess } from 'child_process'
import { platform, homedir, totalmem, freemem, cpus } from 'os'
import { statSync } from 'fs'

// The built directory structure
//
// ├─┬ dist-electron
// │ ├─┬ main.js    > Electron main process
// │ └─┬ preload.js > Preload scripts
// ├─┬ dist
// │ └── index.html > Electron renderer
//

const isWin32 = platform() === 'win32'
const isDev = process.env.NODE_ENV === 'development'
const VITE_DEV_SERVER_URL = process.env.VITE_DEV_SERVER_URL

// Python backend process
let pythonProcess: ChildProcess | null = null

class ElectronApp {
  private mainWindow: BrowserWindow | null = null

  constructor() {
    this.setupEventHandlers()
  }

  private setupEventHandlers(): void {
    // This method will be called when Electron has finished initialization
    app.whenReady().then(() => {
      this.createWindow()
      // Skip Python backend startup - handled by start script
      // this.startPythonBackend()
      
      app.on('activate', () => {
        // On macOS it's common to re-create a window when dock icon is clicked
        if (BrowserWindow.getAllWindows().length === 0) this.createWindow()
      })
    })

    // Quit when all windows are closed, except on macOS
    app.on('window-all-closed', () => {
      if (process.platform !== 'darwin') {
        this.cleanup()
        app.quit()
      }
    })

    // Handle app termination
    app.on('before-quit', () => {
      this.cleanup()
    })

    // Security: Prevent new window creation
    app.on('web-contents-created', (_, contents) => {
      contents.on('new-window', (navigationEvent, url) => {
        navigationEvent.preventDefault()
        shell.openExternal(url)
      })
    })
  }

  private async createWindow(): Promise<void> {
    this.mainWindow = new BrowserWindow({
      title: 'Video Transcriber',
      width: 1200,
      height: 800,
      minWidth: 800,
      minHeight: 600,
      icon: join(process.env.VITE_PUBLIC || '.', 'icon.png'),
      frame: false, // Complete frameless window - no native chrome at all
      titleBarStyle: 'hidden', // Completely hide title bar on all platforms
      titleBarOverlay: false, // Explicitly disable Windows 11 overlay
      webPreferences: {
        preload: join(__dirname, './preload.js'),
        nodeIntegration: false,
        contextIsolation: true,
        enableRemoteModule: false,
        allowRunningInsecureContent: false,
        experimentalFeatures: false
      },
      show: false, // Don't show until ready-to-show
      trafficLightPosition: { x: -100, y: -100 }, // Hide macOS traffic lights completely off-screen
      autoHideMenuBar: true,
      // Ensure complete control removal
      maximizable: true,
      minimizable: true,
      resizable: true,
      skipTaskbar: false,
      thickFrame: false // Remove Windows thick frame completely
    })

    // Show window when ready to prevent visual flash
    this.mainWindow.once('ready-to-show', () => {
      this.mainWindow?.show()
    })

    // Load the remote URL for development or the local html file for production
    if (VITE_DEV_SERVER_URL) {
      await this.mainWindow.loadURL(VITE_DEV_SERVER_URL)
    } else {
      await this.mainWindow.loadFile(join(__dirname, '../index.html'))
    }

    // Handle window closed
    this.mainWindow.on('closed', () => {
      this.mainWindow = null
    })

    // Prevent navigation to external URLs
    this.mainWindow.webContents.on('will-navigate', (event, url) => {
      if (url !== this.mainWindow?.webContents.getURL()) {
        event.preventDefault()
        shell.openExternal(url)
      }
    })

    // Handle file drops at the main process level
    this.setupFileDropHandling()

    // Register F12 shortcut to toggle DevTools
    this.registerDevToolsShortcut()
  }

  private setupFileDropHandling(): void {
    if (!this.mainWindow) return

    // Prevent navigation to dropped files (security measure)
    this.mainWindow.webContents.on('will-navigate', (event, navigationUrl) => {
      if (navigationUrl.startsWith('file://')) {
        event.preventDefault()
        // Extract file path and handle as drop
        const filePath = decodeURIComponent(navigationUrl.replace('file:///', ''))
        console.log('File drop via navigation detected:', filePath)
        this.handleFileDropFromPath([filePath])
      }
    })

    // Set up native drag-drop handling in renderer
    this.mainWindow.webContents.on('dom-ready', () => {
      this.mainWindow?.webContents.executeJavaScript(`
        // Enhanced drag-drop with native file path support
        document.addEventListener('dragover', (e) => {
          e.preventDefault();
          e.stopPropagation();
          e.dataTransfer.dropEffect = 'copy';
        });
        
        document.addEventListener('drop', async (e) => {
          e.preventDefault();
          e.stopPropagation();
          
          console.log('🎯 Drop event detected - processing files...');
          
          // Get the files from the drop event
          const files = Array.from(e.dataTransfer.files);
          
          if (files.length === 0) {
            console.log('❌ No files found in drop event');
            return;
          }
          
          // Extract file paths - in Electron, the File object has a 'path' property
          const filePaths = files
            .map(file => {
              // In Electron context, files have a 'path' property with the full system path
              const path = file.path || '';
              console.log('📁 File:', file.name, '-> Path:', path);
              return path;
            })
            .filter(path => path && path.length > 0);
          
          console.log('📋 Extracted file paths:', filePaths);
          
          if (filePaths.length > 0) {
            // Send file paths directly to renderer
            window.postMessage({
              type: 'native-file-drop',
              filePaths: filePaths
            }, '*');
            
            console.log('✅ File paths sent to renderer via postMessage');
          } else {
            console.log('⚠️ No valid file paths extracted from drop');
          }
        });
        
        
        console.log('🔧 Native drop handlers installed');
      `)
    })
  }

  private handleFileDropFromPath(filePaths: string[]): void {
    if (!this.mainWindow || filePaths.length === 0) return
    
    console.log('Processing dropped file paths:', filePaths)
    
    // Send to renderer process
    this.mainWindow.webContents.postMessage('native-file-drop', {
      type: 'native-file-drop', 
      filePaths: filePaths
    })
  }

  private registerDevToolsShortcut(): void {
    // Register multiple shortcuts to toggle DevTools (important for frameless window)
    const toggleDevTools = () => {
      if (this.mainWindow && this.mainWindow.webContents) {
        if (this.mainWindow.webContents.isDevToolsOpened()) {
          this.mainWindow.webContents.closeDevTools()
        } else {
          this.mainWindow.webContents.openDevTools({ mode: 'detach' })
        }
      }
    }

    // Register F12 globally
    globalShortcut.register('F12', toggleDevTools)
    
    // Also register Ctrl+Shift+I as alternative
    globalShortcut.register('CommandOrControl+Shift+I', toggleDevTools)
    
    // Register Ctrl+Shift+J for console specifically
    globalShortcut.register('CommandOrControl+Shift+J', () => {
      if (this.mainWindow && this.mainWindow.webContents) {
        this.mainWindow.webContents.openDevTools({ mode: 'detach', activate: true })
      }
    })

    console.log('DevTools shortcuts registered: F12, Ctrl+Shift+I, Ctrl+Shift+J')
  }

  private startPythonBackend(): void {
    try {
      const pythonExecutable = isDev ? 'python' : join(process.resourcesPath, 'python-backend', 'python')
      const scriptPath = isDev 
        ? join(__dirname, '../../backend/main.py')
        : join(process.resourcesPath, 'python-backend', 'main.py')

      console.log('Starting Python backend:', pythonExecutable, scriptPath)

      pythonProcess = spawn(pythonExecutable, [scriptPath], {
        cwd: isDev ? join(__dirname, '../../') : process.resourcesPath,
        stdio: ['pipe', 'pipe', 'pipe'],
        env: {
          ...process.env,
          PYTHONUNBUFFERED: '1'
        }
      })

      pythonProcess.stdout?.on('data', (data) => {
        console.log('Python backend stdout:', data.toString())
      })

      pythonProcess.stderr?.on('data', (data) => {
        console.error('Python backend stderr:', data.toString())
      })

      pythonProcess.on('close', (code) => {
        console.log(`Python backend process exited with code ${code}`)
        pythonProcess = null
      })

      pythonProcess.on('error', (error) => {
        console.error('Failed to start Python backend:', error)
        this.showErrorDialog('Backend Error', 'Failed to start Python backend. Please check your installation.')
      })

    } catch (error) {
      console.error('Error starting Python backend:', error)
      this.showErrorDialog('Startup Error', 'Failed to initialize the application backend.')
    }
  }

  private cleanup(): void {
    // Unregister all global shortcuts
    globalShortcut.unregisterAll()
    
    if (pythonProcess) {
      console.log('Terminating Python backend process...')
      
      if (isWin32) {
        spawn('taskkill', ['/pid', pythonProcess.pid?.toString() || '', '/f', '/t'])
      } else {
        pythonProcess.kill('SIGTERM')
      }
      
      pythonProcess = null
    }
  }

  private showErrorDialog(title: string, content: string): void {
    dialog.showErrorBox(title, content)
  }
}

// Initialize the Electron application
new ElectronApp()

// IPC handlers for secure communication with renderer process
ipcMain.handle('app:getVersion', () => {
  return app.getVersion()
})

ipcMain.handle('app:getPlatform', () => {
  return process.platform
})

ipcMain.handle('dialog:showOpenDialog', async (_, options) => {
  if (!BrowserWindow.getFocusedWindow()) return { canceled: true }
  
  const result = await dialog.showOpenDialog(BrowserWindow.getFocusedWindow()!, options)
  return result
})

ipcMain.handle('dialog:showSaveDialog', async (_, options) => {
  if (!BrowserWindow.getFocusedWindow()) return { canceled: true }
  
  const result = await dialog.showSaveDialog(BrowserWindow.getFocusedWindow()!, options)
  return result
})

ipcMain.handle('shell:openExternal', async (_, url: string) => {
  await shell.openExternal(url)
})

ipcMain.handle('shell:showItemInFolder', (_, fullPath: string) => {
  shell.showItemInFolder(fullPath)
})

// Path utilities for safe directory handling
ipcMain.handle('path:getDefaultOutputDirectory', async () => {
  try {
    // Get user's Documents folder and create a Video Transcriber subfolder
    const documentsPath = join(homedir(), 'Documents', 'Video Transcriber')
    return documentsPath.replace(/\\/g, '/') // Normalize path separators
  } catch (error) {
    console.error('Failed to get default output directory:', error)
    // Fallback to app's working directory
    return './Video Transcriber Output'
  }
})

ipcMain.handle('path:getUserDocumentsPath', async () => {
  try {
    const documentsPath = join(homedir(), 'Documents')
    return documentsPath.replace(/\\/g, '/')
  } catch (error) {
    console.error('Failed to get user documents path:', error)
    return './'
  }
})

// File handling utilities for drag-and-drop operations
// Note: Drag-drop is now handled natively in setupFileDropHandling()
// These IPC handlers are kept for backward compatibility but are no longer used
ipcMain.handle('file:getFilePathsFromDrop', async (_, fileData: Array<{name: string, size: number, type: string, lastModified: number}>) => {
  console.log('Legacy getFilePathsFromDrop called - native drop handling is now used instead')
  console.log('Files requested:', fileData.map(f => f.name))
  return [] // Always return empty - native handling is used
})

ipcMain.handle('file:selectVideoFiles', async () => {
  try {
    const focusedWindow = BrowserWindow.getFocusedWindow()
    if (!focusedWindow) return []
    
    const result = await dialog.showOpenDialog(focusedWindow, {
      properties: ['openFile', 'multiSelections'],
      filters: [
        { name: 'Video Files', extensions: ['mp4', 'avi', 'mkv', 'mov'] },
        { name: 'All Files', extensions: ['*'] }
      ],
      title: 'Select Video Files to Transcribe'
    })
    
    if (result.canceled || !result.filePaths) {
      return []
    }
    
    return result.filePaths
  } catch (error) {
    console.error('Failed to select video files:', error)
    return []
  }
})

// Window control handlers for frameless window
ipcMain.handle('window:close', () => {
  const focusedWindow = BrowserWindow.getFocusedWindow()
  if (focusedWindow) {
    focusedWindow.close()
  }
})

ipcMain.handle('window:minimize', () => {
  const focusedWindow = BrowserWindow.getFocusedWindow()
  if (focusedWindow) {
    focusedWindow.minimize()
  }
})

ipcMain.handle('window:maximize', () => {
  const focusedWindow = BrowserWindow.getFocusedWindow()
  if (focusedWindow) {
    if (focusedWindow.isMaximized()) {
      focusedWindow.unmaximize()
    } else {
      focusedWindow.maximize()
    }
  }
})

ipcMain.handle('window:toggleDevTools', () => {
  const focusedWindow = BrowserWindow.getFocusedWindow()
  if (focusedWindow) {
    if (focusedWindow.webContents.isDevToolsOpened()) {
      focusedWindow.webContents.closeDevTools()
    } else {
      focusedWindow.webContents.openDevTools({ mode: 'detach' })
    }
  }
})

// System metrics IPC handlers for status bar
ipcMain.handle('system:getMemoryUsage', () => {
  try {
    const total = totalmem()
    const free = freemem()
    const used = total - free
    const usedPercentage = Math.round((used / total) * 100)
    return {
      total: Math.round(total / (1024 * 1024 * 1024)), // GB
      used: Math.round(used / (1024 * 1024 * 1024)), // GB
      free: Math.round(free / (1024 * 1024 * 1024)), // GB
      usedPercentage
    }
  } catch (error) {
    console.error('Failed to get memory usage:', error)
    return { total: 0, used: 0, free: 0, usedPercentage: 0 }
  }
})

ipcMain.handle('system:getDiskSpace', async (_, path?: string) => {
  try {
    const targetPath = path || (platform() === 'win32' ? 'C:' : '/')
    
    if (platform() === 'win32') {
      // Windows: Use wmic to get disk space
      return new Promise((resolve) => {
        const { exec } = require('child_process')
        exec('wmic logicaldisk where size!=0 get size,freespace,caption', (error: any, stdout: string) => {
          if (error) {
            console.error('Failed to get disk space via wmic:', error)
            resolve({ total: 0, free: 0, used: 0 })
            return
          }
          
          try {
            const lines = stdout.trim().split('\n').slice(1) // Skip header
            const cDrive = lines.find(line => line.includes('C:'))
            if (cDrive) {
              const parts = cDrive.trim().split(/\s+/)
              const free = Math.round(parseInt(parts[1]) / (1024 * 1024 * 1024)) // Convert to GB
              const total = Math.round(parseInt(parts[2]) / (1024 * 1024 * 1024)) // Convert to GB
              const used = total - free
              resolve({ total, free, used })
            } else {
              resolve({ total: 0, free: 0, used: 0 })
            }
          } catch (parseError) {
            console.error('Failed to parse disk space output:', parseError)
            resolve({ total: 0, free: 0, used: 0 })
          }
        })
      })
    } else {
      // Unix-like: Use df command
      return new Promise((resolve) => {
        const { exec } = require('child_process')
        exec('df -h /', (error: any, stdout: string) => {
          if (error) {
            resolve({ total: 0, free: 0, used: 0 })
            return
          }
          
          try {
            const lines = stdout.trim().split('\n')
            const rootLine = lines[1] // Second line contains root filesystem info
            const parts = rootLine.split(/\s+/)
            const total = parseInt(parts[1].replace('G', '')) || 0
            const used = parseInt(parts[2].replace('G', '')) || 0
            const free = parseInt(parts[3].replace('G', '')) || 0
            resolve({ total, free, used })
          } catch (parseError) {
            resolve({ total: 0, free: 0, used: 0 })
          }
        })
      })
    }
  } catch (error) {
    console.error('Failed to get disk space:', error)
    return { total: 0, free: 0, used: 0 }
  }
})

ipcMain.handle('system:getCPUInfo', () => {
  try {
    const cpuInfo = cpus()
    const hasGPU = platform() === 'win32' // Simplified GPU detection
    return {
      cores: cpuInfo.length,
      model: cpuInfo[0]?.model || 'Unknown',
      hasGPU,
      processingMode: hasGPU ? 'GPU' : 'CPU'
    }
  } catch (error) {
    console.error('Failed to get CPU info:', error)
    return { cores: 0, model: 'Unknown', hasGPU: false, processingMode: 'CPU' }
  }
})

ipcMain.handle('backend:healthCheck', async () => {
  try {
    // Try to connect to the Python backend
    const response = await fetch('http://127.0.0.1:8000/health').catch(() => null)
    if (response && response.ok) {
      return { status: 'connected', timestamp: Date.now() }
    }
    return { status: 'disconnected', timestamp: Date.now() }
  } catch (error) {
    return { status: 'disconnected', timestamp: Date.now() }
  }
})

// Handle app protocol for deep linking (optional)
if (process.defaultApp) {
  if (process.argv.length >= 2) {
    app.setAsDefaultProtocolClient('video-transcriber', process.execPath, [join(__dirname, '../')])
  }
} else {
  app.setAsDefaultProtocolClient('video-transcriber')
}
import { app, BrowserWindow, shell, ipcMain, dialog, globalShortcut } from 'electron'
import { join } from 'path'
import { spawn, ChildProcess } from 'child_process'
import { platform } from 'os'

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
      webPreferences: {
        preload: join(__dirname, '../preload/index.js'),
        nodeIntegration: false,
        contextIsolation: true,
        enableRemoteModule: false,
        allowRunningInsecureContent: false,
        experimentalFeatures: false
      },
      show: false, // Don't show until ready-to-show
      titleBarStyle: process.platform === 'darwin' ? 'hiddenInset' : 'default'
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

    // Register F12 shortcut to toggle DevTools
    this.registerDevToolsShortcut()
  }

  private registerDevToolsShortcut(): void {
    // Register F12 globally to toggle DevTools
    globalShortcut.register('F12', () => {
      if (this.mainWindow && this.mainWindow.webContents) {
        if (this.mainWindow.webContents.isDevToolsOpened()) {
          this.mainWindow.webContents.closeDevTools()
        } else {
          this.mainWindow.webContents.openDevTools()
        }
      }
    })
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

// Handle app protocol for deep linking (optional)
if (process.defaultApp) {
  if (process.argv.length >= 2) {
    app.setAsDefaultProtocolClient('video-transcriber', process.execPath, [join(__dirname, '../')])
  }
} else {
  app.setAsDefaultProtocolClient('video-transcriber')
}
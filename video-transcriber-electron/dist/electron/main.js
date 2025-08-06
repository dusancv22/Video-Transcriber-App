"use strict";
var __defProp = Object.defineProperty;
var __defNormalProp = (obj, key, value) => key in obj ? __defProp(obj, key, { enumerable: true, configurable: true, writable: true, value }) : obj[key] = value;
var __publicField = (obj, key, value) => __defNormalProp(obj, typeof key !== "symbol" ? key + "" : key, value);
const electron = require("electron");
const path = require("path");
const child_process = require("child_process");
const os = require("os");
const isWin32 = os.platform() === "win32";
const isDev = process.env.NODE_ENV === "development";
const VITE_DEV_SERVER_URL = process.env.VITE_DEV_SERVER_URL;
let pythonProcess = null;
class ElectronApp {
  constructor() {
    __publicField(this, "mainWindow", null);
    this.setupEventHandlers();
  }
  setupEventHandlers() {
    electron.app.whenReady().then(() => {
      this.createWindow();
      electron.app.on("activate", () => {
        if (electron.BrowserWindow.getAllWindows().length === 0) this.createWindow();
      });
    });
    electron.app.on("window-all-closed", () => {
      if (process.platform !== "darwin") {
        this.cleanup();
        electron.app.quit();
      }
    });
    electron.app.on("before-quit", () => {
      this.cleanup();
    });
    electron.app.on("web-contents-created", (_, contents) => {
      contents.on("new-window", (navigationEvent, url) => {
        navigationEvent.preventDefault();
        electron.shell.openExternal(url);
      });
    });
  }
  async createWindow() {
    this.mainWindow = new electron.BrowserWindow({
      title: "Video Transcriber",
      width: 1200,
      height: 800,
      minWidth: 800,
      minHeight: 600,
      icon: path.join(process.env.VITE_PUBLIC || ".", "icon.png"),
      frame: false,
      // Remove native window chrome to prevent double title bar
      webPreferences: {
        preload: path.join(__dirname, "./preload.js"),
        nodeIntegration: false,
        contextIsolation: true,
        enableRemoteModule: false,
        allowRunningInsecureContent: false,
        experimentalFeatures: false
      },
      show: false,
      // Don't show until ready-to-show
      titleBarStyle: process.platform === "darwin" ? "hiddenInset" : "default"
    });
    this.mainWindow.once("ready-to-show", () => {
      var _a;
      (_a = this.mainWindow) == null ? void 0 : _a.show();
    });
    if (VITE_DEV_SERVER_URL) {
      await this.mainWindow.loadURL(VITE_DEV_SERVER_URL);
    } else {
      await this.mainWindow.loadFile(path.join(__dirname, "../index.html"));
    }
    this.mainWindow.on("closed", () => {
      this.mainWindow = null;
    });
    this.mainWindow.webContents.on("will-navigate", (event, url) => {
      var _a;
      if (url !== ((_a = this.mainWindow) == null ? void 0 : _a.webContents.getURL())) {
        event.preventDefault();
        electron.shell.openExternal(url);
      }
    });
    this.setupFileDropHandling();
    this.registerDevToolsShortcut();
  }
  setupFileDropHandling() {
    if (!this.mainWindow) return;
    this.mainWindow.webContents.on("will-navigate", (event, navigationUrl) => {
      if (navigationUrl.startsWith("file://")) {
        event.preventDefault();
        const filePath = decodeURIComponent(navigationUrl.replace("file:///", ""));
        console.log("File drop via navigation detected:", filePath);
        this.handleFileDropFromPath([filePath]);
      }
    });
    this.mainWindow.webContents.on("dom-ready", () => {
      var _a;
      (_a = this.mainWindow) == null ? void 0 : _a.webContents.executeJavaScript(`
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
      `);
    });
  }
  handleFileDropFromPath(filePaths) {
    if (!this.mainWindow || filePaths.length === 0) return;
    console.log("Processing dropped file paths:", filePaths);
    this.mainWindow.webContents.postMessage("native-file-drop", {
      type: "native-file-drop",
      filePaths
    });
  }
  registerDevToolsShortcut() {
    const toggleDevTools = () => {
      if (this.mainWindow && this.mainWindow.webContents) {
        if (this.mainWindow.webContents.isDevToolsOpened()) {
          this.mainWindow.webContents.closeDevTools();
        } else {
          this.mainWindow.webContents.openDevTools({ mode: "detach" });
        }
      }
    };
    electron.globalShortcut.register("F12", toggleDevTools);
    electron.globalShortcut.register("CommandOrControl+Shift+I", toggleDevTools);
    electron.globalShortcut.register("CommandOrControl+Shift+J", () => {
      if (this.mainWindow && this.mainWindow.webContents) {
        this.mainWindow.webContents.openDevTools({ mode: "detach", activate: true });
      }
    });
    console.log("DevTools shortcuts registered: F12, Ctrl+Shift+I, Ctrl+Shift+J");
  }
  startPythonBackend() {
    var _a, _b;
    try {
      const pythonExecutable = isDev ? "python" : path.join(process.resourcesPath, "python-backend", "python");
      const scriptPath = isDev ? path.join(__dirname, "../../backend/main.py") : path.join(process.resourcesPath, "python-backend", "main.py");
      console.log("Starting Python backend:", pythonExecutable, scriptPath);
      pythonProcess = child_process.spawn(pythonExecutable, [scriptPath], {
        cwd: isDev ? path.join(__dirname, "../../") : process.resourcesPath,
        stdio: ["pipe", "pipe", "pipe"],
        env: {
          ...process.env,
          PYTHONUNBUFFERED: "1"
        }
      });
      (_a = pythonProcess.stdout) == null ? void 0 : _a.on("data", (data) => {
        console.log("Python backend stdout:", data.toString());
      });
      (_b = pythonProcess.stderr) == null ? void 0 : _b.on("data", (data) => {
        console.error("Python backend stderr:", data.toString());
      });
      pythonProcess.on("close", (code) => {
        console.log(`Python backend process exited with code ${code}`);
        pythonProcess = null;
      });
      pythonProcess.on("error", (error) => {
        console.error("Failed to start Python backend:", error);
        this.showErrorDialog("Backend Error", "Failed to start Python backend. Please check your installation.");
      });
    } catch (error) {
      console.error("Error starting Python backend:", error);
      this.showErrorDialog("Startup Error", "Failed to initialize the application backend.");
    }
  }
  cleanup() {
    var _a;
    electron.globalShortcut.unregisterAll();
    if (pythonProcess) {
      console.log("Terminating Python backend process...");
      if (isWin32) {
        child_process.spawn("taskkill", ["/pid", ((_a = pythonProcess.pid) == null ? void 0 : _a.toString()) || "", "/f", "/t"]);
      } else {
        pythonProcess.kill("SIGTERM");
      }
      pythonProcess = null;
    }
  }
  showErrorDialog(title, content) {
    electron.dialog.showErrorBox(title, content);
  }
}
new ElectronApp();
electron.ipcMain.handle("app:getVersion", () => {
  return electron.app.getVersion();
});
electron.ipcMain.handle("app:getPlatform", () => {
  return process.platform;
});
electron.ipcMain.handle("dialog:showOpenDialog", async (_, options) => {
  if (!electron.BrowserWindow.getFocusedWindow()) return { canceled: true };
  const result = await electron.dialog.showOpenDialog(electron.BrowserWindow.getFocusedWindow(), options);
  return result;
});
electron.ipcMain.handle("dialog:showSaveDialog", async (_, options) => {
  if (!electron.BrowserWindow.getFocusedWindow()) return { canceled: true };
  const result = await electron.dialog.showSaveDialog(electron.BrowserWindow.getFocusedWindow(), options);
  return result;
});
electron.ipcMain.handle("shell:openExternal", async (_, url) => {
  await electron.shell.openExternal(url);
});
electron.ipcMain.handle("shell:showItemInFolder", (_, fullPath) => {
  electron.shell.showItemInFolder(fullPath);
});
electron.ipcMain.handle("path:getDefaultOutputDirectory", async () => {
  try {
    const documentsPath = path.join(os.homedir(), "Documents", "Video Transcriber");
    return documentsPath.replace(/\\/g, "/");
  } catch (error) {
    console.error("Failed to get default output directory:", error);
    return "./Video Transcriber Output";
  }
});
electron.ipcMain.handle("path:getUserDocumentsPath", async () => {
  try {
    const documentsPath = path.join(os.homedir(), "Documents");
    return documentsPath.replace(/\\/g, "/");
  } catch (error) {
    console.error("Failed to get user documents path:", error);
    return "./";
  }
});
electron.ipcMain.handle("file:getFilePathsFromDrop", async (_, fileData) => {
  console.log("Legacy getFilePathsFromDrop called - native drop handling is now used instead");
  console.log("Files requested:", fileData.map((f) => f.name));
  return [];
});
electron.ipcMain.handle("file:selectVideoFiles", async () => {
  try {
    const focusedWindow = electron.BrowserWindow.getFocusedWindow();
    if (!focusedWindow) return [];
    const result = await electron.dialog.showOpenDialog(focusedWindow, {
      properties: ["openFile", "multiSelections"],
      filters: [
        { name: "Video Files", extensions: ["mp4", "avi", "mkv", "mov"] },
        { name: "All Files", extensions: ["*"] }
      ],
      title: "Select Video Files to Transcribe"
    });
    if (result.canceled || !result.filePaths) {
      return [];
    }
    return result.filePaths;
  } catch (error) {
    console.error("Failed to select video files:", error);
    return [];
  }
});
electron.ipcMain.handle("window:close", () => {
  const focusedWindow = electron.BrowserWindow.getFocusedWindow();
  if (focusedWindow) {
    focusedWindow.close();
  }
});
electron.ipcMain.handle("window:minimize", () => {
  const focusedWindow = electron.BrowserWindow.getFocusedWindow();
  if (focusedWindow) {
    focusedWindow.minimize();
  }
});
electron.ipcMain.handle("window:maximize", () => {
  const focusedWindow = electron.BrowserWindow.getFocusedWindow();
  if (focusedWindow) {
    if (focusedWindow.isMaximized()) {
      focusedWindow.unmaximize();
    } else {
      focusedWindow.maximize();
    }
  }
});
electron.ipcMain.handle("window:toggleDevTools", () => {
  const focusedWindow = electron.BrowserWindow.getFocusedWindow();
  if (focusedWindow) {
    if (focusedWindow.webContents.isDevToolsOpened()) {
      focusedWindow.webContents.closeDevTools();
    } else {
      focusedWindow.webContents.openDevTools({ mode: "detach" });
    }
  }
});
if (process.defaultApp) {
  if (process.argv.length >= 2) {
    electron.app.setAsDefaultProtocolClient("video-transcriber", process.execPath, [path.join(__dirname, "../")]);
  }
} else {
  electron.app.setAsDefaultProtocolClient("video-transcriber");
}
//# sourceMappingURL=main.js.map

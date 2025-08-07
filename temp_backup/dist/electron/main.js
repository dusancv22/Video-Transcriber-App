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
      webPreferences: {
        preload: path.join(__dirname, "../preload/index.js"),
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
      var _a, _b;
      (_a = this.mainWindow) == null ? void 0 : _a.show();
      if (isDev) {
        (_b = this.mainWindow) == null ? void 0 : _b.webContents.openDevTools();
      }
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
if (process.defaultApp) {
  if (process.argv.length >= 2) {
    electron.app.setAsDefaultProtocolClient("video-transcriber", process.execPath, [path.join(__dirname, "../")]);
  }
} else {
  electron.app.setAsDefaultProtocolClient("video-transcriber");
}
//# sourceMappingURL=main.js.map

const { contextBridge, ipcRenderer } = require('electron')

contextBridge.exposeInMainWorld('electronAPI', {
  onBackendStatus: (callback) => ipcRenderer.on('backend-status', (_e, status) => callback(status)),
  onBackendLog: (callback) => ipcRenderer.on('backend-log', (_e, msg) => callback(msg)),
  onWindowMaximized: (callback) => ipcRenderer.on('window-maximized', (_e, flag) => callback(flag)),
  getBackendStatus: () => ipcRenderer.invoke('get-backend-status'),
  restartBackend: () => ipcRenderer.invoke('restart-backend'),
  windowMinimize: () => ipcRenderer.invoke('window-minimize'),
  windowMaximize: () => ipcRenderer.invoke('window-maximize'),
  windowClose: () => ipcRenderer.invoke('window-close'),
  windowIsMaximized: () => ipcRenderer.invoke('window-is-maximized'),
})

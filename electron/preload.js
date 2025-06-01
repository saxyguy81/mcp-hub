const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  checkDependencies: () => ipcRenderer.invoke('checkDependencies'),
  testLLM: (config) => ipcRenderer.invoke('testLLM', config),
  getCurrentConfig: () => ipcRenderer.invoke('getCurrentConfig'),
  saveConfig: (config) => ipcRenderer.invoke('saveConfig', config),
  regenerateBridge: () => ipcRenderer.invoke('regenerateBridge')
});

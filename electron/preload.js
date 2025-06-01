const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  // Existing handlers
  checkDependencies: () => ipcRenderer.invoke('checkDependencies'),
  testLLM: (config) => ipcRenderer.invoke('testLLM', config),
  getCurrentConfig: () => ipcRenderer.invoke('getCurrentConfig'),
  saveConfig: (config) => ipcRenderer.invoke('saveConfig', config),
  regenerateBridge: () => ipcRenderer.invoke('regenerateBridge'),
  
  // Enhanced command execution
  executeCommand: (args) => ipcRenderer.invoke('executeCommand', args),
  
  // Proxy management
  checkProxyStatus: () => ipcRenderer.invoke('checkProxyStatus'),
  startProxy: () => ipcRenderer.invoke('startProxy'),
  stopProxy: () => ipcRenderer.invoke('stopProxy'),
  getProxyServers: () => ipcRenderer.invoke('getProxyServers'),
  
  // Service management
  getServicesStatus: () => ipcRenderer.invoke('getServicesStatus'),
  startServices: () => ipcRenderer.invoke('startServices'),
  stopServices: () => ipcRenderer.invoke('stopServices'),
  
  // Utility
  openUrl: (url) => ipcRenderer.invoke('openUrl', url),
});

// Also expose a simplified command interface for direct mcpctl access
contextBridge.exposeInMainWorld('mcpctl', {
  run: (command, ...args) => ipcRenderer.invoke('executeCommand', [command, ...args]),
  proxy: {
    start: () => ipcRenderer.invoke('executeCommand', ['proxy', 'start']),
    stop: () => ipcRenderer.invoke('executeCommand', ['proxy', 'stop']),
    status: () => ipcRenderer.invoke('executeCommand', ['proxy', 'status']),
    logs: () => ipcRenderer.invoke('executeCommand', ['proxy', 'logs']),
    servers: () => ipcRenderer.invoke('executeCommand', ['proxy', 'servers']),
  },
  services: {
    start: () => ipcRenderer.invoke('executeCommand', ['start']),
    stop: () => ipcRenderer.invoke('executeCommand', ['stop']),
    status: () => ipcRenderer.invoke('executeCommand', ['status']),
  }
});

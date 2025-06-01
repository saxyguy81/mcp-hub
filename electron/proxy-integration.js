// Add this to the end of electron.js to include proxy handlers

// Proxy management IPC handlers
ipcMain.handle('executeCommand', async (event, args) => {
  try {
    const result = await executeMcpctl(args);
    return { success: true, ...result };
  } catch (error) {
    console.error('Command execution error:', error);
    return { success: false, error: error.message };
  }
});

ipcMain.handle('checkProxyStatus', async () => {
  try {
    return new Promise((resolve) => {
      const req = http.get('http://localhost:3000/health', { timeout: 5000 }, (res) => {
        let data = '';
        res.on('data', chunk => data += chunk);
        res.on('end', () => {
          try {
            const parsed = JSON.parse(data);
            resolve({
              running: true,
              healthy: res.statusCode === 200,
              data: parsed
            });
          } catch {
            resolve({ running: false, healthy: false });
          }
        });
      });

      req.on('error', () => {
        resolve({ running: false, healthy: false });
      });

      req.on('timeout', () => {
        req.destroy();
        resolve({ running: false, healthy: false });
      });
    });
  } catch (error) {
    return { running: false, healthy: false, error: error.message };
  }
});

ipcMain.handle('startProxy', async () => {
  try {
    const result = await executeMcpctl(['proxy', 'start']);
    return { success: true, ...result };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

ipcMain.handle('stopProxy', async () => {
  try {
    const result = await executeMcpctl(['proxy', 'stop']);
    return { success: true, ...result };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

ipcMain.handle('getProxyServers', async () => {
  try {
    return new Promise((resolve) => {
      const req = http.get('http://localhost:3000/servers', { timeout: 5000 }, (res) => {
        let data = '';
        res.on('data', chunk => data += chunk);
        res.on('end', () => {
          try {
            const parsed = JSON.parse(data);
            resolve({ success: true, servers: parsed.servers || [] });
          } catch {
            resolve({ success: false, servers: [] });
          }
        });
      });

      req.on('error', (error) => {
        resolve({ success: false, error: error.message, servers: [] });
      });
    });
  } catch (error) {
    return { success: false, error: error.message, servers: [] };
  }
});

ipcMain.handle('openUrl', async (event, url) => {
  try {
    const { shell } = require('electron');
    await shell.openExternal(url);
    return { success: true };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

ipcMain.handle('getServicesStatus', async () => {
  try {
    const result = await executeMcpctl(['status']);
    return { success: true, ...result };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

ipcMain.handle('startServices', async () => {
  try {
    const result = await executeMcpctl(['start']);
    return { success: true, ...result };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

ipcMain.handle('stopServices', async () => {
  try {
    const result = await executeMcpctl(['stop']);
    return { success: true, ...result };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

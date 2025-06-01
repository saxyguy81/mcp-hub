const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const fs = require('fs');
const os = require('os');
const { spawn, exec } = require('child_process');
const https = require('https');
const http = require('http');

let mainWindow;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js')
    }
  });

  if (process.env.NODE_ENV === 'development') {
    mainWindow.loadURL('http://localhost:5173');
    mainWindow.webContents.openDevTools();
  } else {
    mainWindow.loadFile(path.join(__dirname, 'build/index.html'));
  }
}

function getConfigPath() {
  return path.join(os.homedir(), '.mcpctl', 'config.json');
}

function ensureConfigDir() {
  const configDir = path.dirname(getConfigPath());
  if (!fs.existsSync(configDir)) {
    fs.mkdirSync(configDir, { recursive: true });
  }
}

function loadConfig() {
  try {
    const configPath = getConfigPath();
    if (fs.existsSync(configPath)) {
      const data = fs.readFileSync(configPath, 'utf8');
      return JSON.parse(data);
    }
  } catch (error) {
    console.error('Error loading config:', error);
  }
  
  return {
    gitRemote: '', registry: 'offline', secrets: 'env',
    llmBackend: 'claude', customLLMUrl: '', customLLMToken: '',
    dependencies: { docker: false, git: false, python: false }
  };
}

function saveConfig(config) {
  try {
    ensureConfigDir();
    const configPath = getConfigPath();
    fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
    return true;
  } catch (error) {
    console.error('Error saving config:', error);
    return false;
  }
}

async function checkDependencies() {
  const dependencies = { docker: false, git: false, python: false };

  return new Promise((resolve) => {
    let checks = 0;
    const totalChecks = 3;

    function checkComplete() {
      checks++;
      if (checks === totalChecks) {
        resolve(dependencies);
      }
    }

    exec('docker --version', (error) => {
      dependencies.docker = !error;
      checkComplete();
    });

    exec('git --version', (error) => {
      dependencies.git = !error;
      checkComplete();
    });

    exec('python3 --version || python --version', (error, stdout) => {
      if (!error && stdout) {
        const versionMatch = stdout.match(/Python (\d+)\.(\d+)/);
        if (versionMatch) {
          const major = parseInt(versionMatch[1]);
          const minor = parseInt(versionMatch[2]);
          dependencies.python = major > 3 || (major === 3 && minor >= 10);
        }
      }
      checkComplete();
    });
  });
}

function loadConfig() {
  try {
    const configPath = getConfigPath();
    if (fs.existsSync(configPath)) {
      const data = fs.readFileSync(configPath, 'utf8');
      return JSON.parse(data);
    }
  } catch (error) {
    console.error('Error loading config:', error);
  }
  
  return {
    gitRemote: '', registry: 'offline', secrets: 'env',
    llmBackend: 'claude', customLLMUrl: '', customLLMToken: '',
    dependencies: { docker: false, git: false, python: false }
  };
}

function saveConfig(config) {
  try {
    ensureConfigDir();
    const configPath = getConfigPath();
    fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
    return true;
  } catch (error) {
    console.error('Error saving config:', error);
    return false;
  }
}

async function checkDependencies() {
  const dependencies = { docker: false, git: false, python: false };

  return new Promise((resolve) => {
    let checks = 0;
    const totalChecks = 3;

    function checkComplete() {
      checks++;
      if (checks === totalChecks) {
        resolve(dependencies);
      }
    }

    exec('docker --version', (error) => {
      dependencies.docker = !error;
      checkComplete();
    });

    exec('git --version', (error) => {
      dependencies.git = !error;
      checkComplete();
    });

    exec('python3 --version || python --version', (error, stdout) => {
      if (!error && stdout) {
        const versionMatch = stdout.match(/Python (\d+)\.(\d+)/);
        if (versionMatch) {
          const major = parseInt(versionMatch[1]);
          const minor = parseInt(versionMatch[2]);
          dependencies.python = major > 3 || (major === 3 && minor >= 10);
        }
      }
      checkComplete();
    });
  });
}

async function testClaudeDesktop() {
  return new Promise((resolve) => {
    const startTime = Date.now();
    
    const ports = [52262, 52263, 52264];
    let attempts = 0;
    
    function tryPort(port) {
      const req = http.get(`http://localhost:${port}/status`, { timeout: 5000 }, (res) => {
        const duration = Date.now() - startTime;
        resolve({
          success: true,
          duration,
          status: res.statusCode,
          message: `Connected to Claude Desktop on port ${port}`
        });
      });

      req.on('error', () => {
        attempts++;
        if (attempts < ports.length) {
          tryPort(ports[attempts]);
        } else {
          const duration = Date.now() - startTime;
          resolve({
            success: false,
            duration,
            status: 0,
            message: 'Claude Desktop not found. Make sure Claude Desktop is running.'
          });
        }
      });

      req.on('timeout', () => {
        req.destroy();
        attempts++;
        if (attempts < ports.length) {
          tryPort(ports[attempts]);
        } else {
          const duration = Date.now() - startTime;
          resolve({
            success: false,
            duration,
            status: 0,
            message: 'Connection timeout. Claude Desktop may not be running.'
          });
        }
      });
    }

    tryPort(ports[0]);
  });
}

async function testOpenAIAPI() {
  return new Promise((resolve) => {
    const startTime = Date.now();
    
    const postData = JSON.stringify({
      model: 'gpt-3.5-turbo',
      messages: [{ role: 'user', content: 'ping' }],
      max_tokens: 1
    });

    const options = {
      hostname: 'api.openai.com',
      path: '/v1/chat/completions',
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': postData.length,
        'Authorization': `Bearer ${process.env.OPENAI_API_KEY || 'test-key'}`
      },
      timeout: 10000
    };

    const req = https.request(options, (res) => {
      const duration = Date.now() - startTime;
      let data = '';
      
      res.on('data', (chunk) => {
        data += chunk;
      });

      res.on('end', () => {
        const success = res.statusCode === 200;
        resolve({
          success,
          duration,
          status: res.statusCode,
          message: success ? 'OpenAI API connection successful' : 
                   res.statusCode === 401 ? 'Invalid API key' :
                   `HTTP ${res.statusCode}: ${data.slice(0, 100)}`
        });
      });
    });

    req.on('error', (error) => {
      const duration = Date.now() - startTime;
      resolve({
        success: false,
        duration,
        status: 0,
        message: `Connection error: ${error.message}`
      });
    });

    req.on('timeout', () => {
      req.destroy();
      const duration = Date.now() - startTime;
      resolve({
        success: false,
        duration,
        status: 0,
        message: 'Connection timeout'
      });
    });

    req.write(postData);
    req.end();
  });
}

async function testCustomLLM(baseUrl, token) {
  return new Promise((resolve) => {
    const startTime = Date.now();
    
    const postData = JSON.stringify({
      model: 'gpt-3.5-turbo',
      messages: [{ role: 'user', content: 'ping' }],
      max_tokens: 1
    });

    const url = new URL('/v1/chat/completions', baseUrl);
    const isHttps = url.protocol === 'https:';
    const httpModule = isHttps ? https : http;
    
    const options = {
      hostname: url.hostname,
      port: url.port || (isHttps ? 443 : 80),
      path: url.pathname,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': postData.length
      },
      timeout: 10000
    };

    if (token) {
      options.headers['Authorization'] = `Bearer ${token}`;
    }

    const req = httpModule.request(options, (res) => {
      const duration = Date.now() - startTime;
      let data = '';
      
      res.on('data', (chunk) => {
        data += chunk;
      });

      res.on('end', () => {
        const success = res.statusCode === 200;
        resolve({
          success,
          duration,
          status: res.statusCode,
          message: success ? 'Custom LLM connection successful' : 
                   `HTTP ${res.statusCode}: ${data.slice(0, 100)}`
        });
      });
    });

    req.on('error', (error) => {
      const duration = Date.now() - startTime;
      resolve({
        success: false,
        duration,
        status: 0,
        message: `Connection error: ${error.message}`
      });
    });

    req.on('timeout', () => {
      req.destroy();
      const duration = Date.now() - startTime;
      resolve({
        success: false,
        duration,
        status: 0,
        message: 'Connection timeout'
      });
    });

    req.write(postData);
    req.end();
  });
}

function executeMcpctl(args) {
  return new Promise((resolve, reject) => {
    const possiblePaths = [
      'mcpctl',
      './mcpctl',
      path.join(__dirname, '..', 'mcpctl'),
      'python3 -m mcpctl.cli',
      'python -m mcpctl.cli'
    ];

    function tryPath(index) {
      if (index >= possiblePaths.length) {
        reject(new Error('mcpctl command not found'));
        return;
      }

      const cmd = possiblePaths[index];
      const fullArgs = cmd.includes('python') ? args : ['mcpctl', ...args];
      const actualCmd = cmd.includes('python') ? cmd.split(' ')[0] : cmd.split(' ')[0];
      const actualArgs = cmd.includes('python') ? ['-m', 'mcpctl.cli', ...args] : args;

      const child = spawn(actualCmd, actualArgs, {
        stdio: ['pipe', 'pipe', 'pipe'],
        shell: true
      });

      let stdout = '';
      let stderr = '';

      child.stdout.on('data', (data) => {
        stdout += data.toString();
      });

      child.stderr.on('data', (data) => {
        stderr += data.toString();
      });

      child.on('close', (code) => {
        if (code === 0) {
          resolve({ stdout, stderr });
        } else if (index === 0) {
          tryPath(index + 1);
        } else {
          reject(new Error(`Command failed: ${stderr || stdout}`));
        }
      });

      child.on('error', (error) => {
        if (index < possiblePaths.length - 1) {
          tryPath(index + 1);
        } else {
          reject(error);
        }
      });
    }

    tryPath(0);
  });
}

// IPC Handlers
ipcMain.handle('checkDependencies', async () => {
  try {
    return await checkDependencies();
  } catch (error) {
    console.error('Error checking dependencies:', error);
    return { docker: false, git: false, python: false };
  }
});

ipcMain.handle('testLLM', async (event, config) => {
  try {
    switch (config.llmBackend) {
      case 'claude':
        return await testClaudeDesktop();
      
      case 'openai':
        return await testOpenAIAPI();
      
      case 'custom':
        if (!config.customLLMUrl) {
          return {
            success: false,
            duration: 0,
            status: 0,
            message: 'Custom URL is required'
          };
        }
        return await testCustomLLM(config.customLLMUrl, config.customLLMToken);
      
      default:
        return {
          success: false,
          duration: 0,
          status: 0,
          message: `Unknown LLM backend: ${config.llmBackend}`
        };
    }
  } catch (error) {
    console.error('Error testing LLM:', error);
    return {
      success: false,
      duration: 0,
      status: 0,
      message: error.message
    };
  }
});

ipcMain.handle('getCurrentConfig', async () => {
  try {
    return loadConfig();
  } catch (error) {
    console.error('Error loading config:', error);
    return null;
  }
});

ipcMain.handle('saveConfig', async (event, config) => {
  try {
    return saveConfig(config);
  } catch (error) {
    console.error('Error saving config:', error);
    return false;
  }
});

ipcMain.handle('regenerateBridge', async () => {
  try {
    const result = await executeMcpctl(['regenerate-bridge']);
    return { success: true, output: result.stdout };
  } catch (error) {
    console.error('Error regenerating bridge:', error);
    throw new Error(`Failed to regenerate bridge: ${error.message}`);
  }
});

// Enhanced proxy management IPC handlers
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

ipcMain.handle('openUrl', async (event, url) => {
  try {
    const { shell } = require('electron');
    await shell.openExternal(url);
    return { success: true };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

// App event handlers
app.whenReady().then(() => {
  createWindow();
  
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

module.exports = {
  createWindow,
  checkDependencies,
  testClaudeDesktop,
  testOpenAIAPI,
  testCustomLLM
};

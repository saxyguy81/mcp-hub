/**
 * Cross-platform dependency installer for MCP Hub
 * Supports macOS (Homebrew), Windows (winget), and Linux (apt/yum)
 */

import { exec } from 'child_process';
import { promisify } from 'util';
import os from 'os';

const execAsync = promisify(exec);

export interface Dependency {
  name: string;
  displayName: string;
  macOS?: {
    brew?: string;
    cask?: string;
  };
  windows?: {
    winget?: string;
    chocolatey?: string;
  };
  linux?: {
    apt?: string;
    yum?: string;
  };
  checkCommand: string;
  required: boolean;
  vesselSkip?: boolean; // Skip if user chose Vessel
}

export const dependencies: Dependency[] = [
  {
    name: 'docker',
    displayName: 'Docker Desktop',
    macOS: { cask: 'docker' },
    windows: { winget: 'Docker.DockerDesktop' },
    linux: { apt: 'docker.io', yum: 'docker' },
    checkCommand: 'docker --version',
    required: true,
    vesselSkip: true
  },
  {
    name: 'vessel',
    displayName: 'Vessel',
    macOS: { brew: 'vessel' },
    windows: {}, // TODO: Add Chocolatey or MSI link when available
    linux: {}, // Vessel may not be available on Linux yet
    checkCommand: 'vessel --version',
    required: false
  },
  {
    name: 'git',
    displayName: 'Git',
    macOS: { brew: 'git' },
    windows: { winget: 'Git.Git' },
    linux: { apt: 'git', yum: 'git' },
    checkCommand: 'git --version',
    required: true
  },
  {
    name: 'python',
    displayName: 'Python 3.11+',
    macOS: { brew: 'python@3.11' },
    windows: { winget: 'Python.Python.3.11' },
    linux: { apt: 'python3', yum: 'python3' },
    checkCommand: 'python3 --version || python --version',
    required: false // Only required if secrets backend = env
  }
];

export function getPlatform(): 'macOS' | 'windows' | 'linux' {
  const platform = os.platform();
  switch (platform) {
    case 'darwin':
      return 'macOS';
    case 'win32':
      return 'windows';
    default:
      return 'linux';
  }
}

export async function checkDependency(dep: Dependency): Promise<boolean> {
  try {
    await execAsync(dep.checkCommand);
    return true;
  } catch {
    return false;
  }
}

export async function installDependency(
  dep: Dependency, 
  useVessel: boolean = false
): Promise<{ success: boolean; message: string }> {
  
  // Skip Docker if using Vessel
  if (dep.vesselSkip && useVessel) {
    return { success: true, message: `Skipped ${dep.displayName} (using Vessel)` };
  }

  const platform = getPlatform();
  let command = '';

  try {
    switch (platform) {
      case 'macOS':
        if (dep.macOS?.cask) {
          command = `brew install --cask ${dep.macOS.cask}`;
        } else if (dep.macOS?.brew) {
          command = `brew install ${dep.macOS.brew}`;
        }
        break;
      
      case 'windows':
        if (dep.windows?.winget) {
          command = `winget install ${dep.windows.winget}`;
        }
        break;
      
      case 'linux':
        // Try to detect package manager
        const hasApt = await checkCommand('apt --version');
        const hasYum = await checkCommand('yum --version');
        
        if (hasApt && dep.linux?.apt) {
          command = `sudo apt update && sudo apt install -y ${dep.linux.apt}`;
        } else if (hasYum && dep.linux?.yum) {
          command = `sudo yum install -y ${dep.linux.yum}`;
        }
        break;
    }

    if (!command) {
      return {
        success: false,
        message: `No installation method available for ${dep.displayName} on ${platform}`
      };
    }

    await execAsync(command);
    return { success: true, message: `${dep.displayName} installed successfully` };
    
  } catch (error: any) {
    return {
      success: false,
      message: `Failed to install ${dep.displayName}: ${error.message}`
    };
  }
}

async function checkCommand(cmd: string): Promise<boolean> {
  try {
    await execAsync(cmd);
    return true;
  } catch {
    return false;
  }
}

export async function installAllDependencies(
  useVessel: boolean = false,
  secretsBackend: string = 'env'
): Promise<{ success: boolean; results: Array<{ name: string; success: boolean; message: string }> }> {
  
  const results: Array<{ name: string; success: boolean; message: string }> = [];
  let allSuccess = true;

  for (const dep of dependencies) {
    // Skip Python if secrets backend is not 'env'
    if (dep.name === 'python' && secretsBackend !== 'env') {
      continue;
    }
    
    // Skip if dependency is already installed
    const isInstalled = await checkDependency(dep);
    if (isInstalled) {
      results.push({
        name: dep.name,
        success: true,
        message: `${dep.displayName} is already installed`
      });
      continue;
    }

    const result = await installDependency(dep, useVessel);
    results.push({
      name: dep.name,
      success: result.success,
      message: result.message
    });

    if (!result.success && dep.required) {
      allSuccess = false;
    }
  }

  return { success: allSuccess, results };
}

export async function checkAllDependencies(): Promise<{
  [key: string]: boolean;
}> {
  const status: { [key: string]: boolean } = {};
  
  for (const dep of dependencies) {
    status[dep.name] = await checkDependency(dep);
  }
  
  return status;
}

/**
 * Auto-start installation for MCP Hub daemon
 * Supports macOS (LaunchAgents) and Windows (Registry Run keys)
 */

import { exec } from 'child_process';
import { promisify } from 'util';
import fs from 'fs/promises';
import path from 'path';
import os from 'os';

const execAsync = promisify(exec);

export interface AutoStartConfig {
  enabled: boolean;
  platform: 'macOS' | 'windows' | 'linux';
  method: string;
  path: string;
}

export async function installAutoStart(mcpctlPath: string): Promise<{ success: boolean; message: string }> {
  const platform = os.platform();
  
  try {
    switch (platform) {
      case 'darwin':
        return await installMacOSLaunchAgent(mcpctlPath);
      case 'win32':
        return await installWindowsRegistry(mcpctlPath);
      default:
        return {
          success: false,
          message: 'Auto-start not supported on this platform yet'
        };
    }
  } catch (error: any) {
    return {
      success: false,
      message: `Failed to install auto-start: ${error.message}`
    };
  }
}

async function installMacOSLaunchAgent(mcpctlPath: string): Promise<{ success: boolean; message: string }> {
  const homeDir = os.homedir();
  const launchAgentsDir = path.join(homeDir, 'Library', 'LaunchAgents');
  const plistPath = path.join(launchAgentsDir, 'com.mcphub.daemon.plist');
  
  // Ensure LaunchAgents directory exists
  await fs.mkdir(launchAgentsDir, { recursive: true });
  
  const plistContent = `<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.mcphub.daemon</string>
    <key>ProgramArguments</key>
    <array>
        <string>${mcpctlPath}</string>
        <string>daemon</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>WorkingDirectory</key>
    <string>${path.dirname(mcpctlPath)}</string>
    <key>StandardOutPath</key>
    <string>${homeDir}/.mcpctl/daemon.log</string>
    <key>StandardErrorPath</key>
    <string>${homeDir}/.mcpctl/daemon.error.log</string>
</dict>
</plist>`;

  await fs.writeFile(plistPath, plistContent);
  
  // Load the launch agent
  await execAsync(`launchctl load ${plistPath}`);
  
  return {
    success: true,
    message: `Auto-start installed: ${plistPath}`
  };
}

async function installWindowsRegistry(mcpctlPath: string): Promise<{ success: boolean; message: string }> {
  const regCommand = `reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run" /v MCPHub /d "\\"${mcpctlPath}\\" daemon" /f`;
  
  await execAsync(regCommand);
  
  return {
    success: true,
    message: `Auto-start installed in Windows Registry`
  };
}

export async function removeAutoStart(): Promise<{ success: boolean; message: string }> {
  const platform = os.platform();
  
  try {
    switch (platform) {
      case 'darwin':
        return await removeMacOSLaunchAgent();
      case 'win32':
        return await removeWindowsRegistry();
      default:
        return {
          success: false,
          message: 'Auto-start removal not supported on this platform yet'
        };
    }
  } catch (error: any) {
    return {
      success: false,
      message: `Failed to remove auto-start: ${error.message}`
    };
  }
}

async function removeMacOSLaunchAgent(): Promise<{ success: boolean; message: string }> {
  const homeDir = os.homedir();
  const plistPath = path.join(homeDir, 'Library', 'LaunchAgents', 'com.mcphub.daemon.plist');
  
  try {
    await execAsync(`launchctl unload ${plistPath}`);
  } catch {
    // Ignore if already unloaded
  }
  
  try {
    await fs.unlink(plistPath);
  } catch {
    // Ignore if file doesn't exist
  }
  
  return {
    success: true,
    message: 'Auto-start removed from macOS LaunchAgents'
  };
}

async function removeWindowsRegistry(): Promise<{ success: boolean; message: string }> {
  const regCommand = `reg delete "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run" /v MCPHub /f`;
  
  try {
    await execAsync(regCommand);
  } catch {
    // Ignore if key doesn't exist
  }
  
  return {
    success: true,
    message: 'Auto-start removed from Windows Registry'
  };
}

export async function checkAutoStartStatus(): Promise<AutoStartConfig> {
  const platform = os.platform();
  
  switch (platform) {
    case 'darwin':
      const homeDir = os.homedir();
      const plistPath = path.join(homeDir, 'Library', 'LaunchAgents', 'com.mcphub.daemon.plist');
      try {
        await fs.access(plistPath);
        return {
          enabled: true,
          platform: 'macOS',
          method: 'LaunchAgent',
          path: plistPath
        };
      } catch {
        return {
          enabled: false,
          platform: 'macOS',
          method: 'LaunchAgent',
          path: plistPath
        };
      }
    
    case 'win32':
      try {
        await execAsync('reg query "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run" /v MCPHub');
        return {
          enabled: true,
          platform: 'windows',
          method: 'Registry',
          path: 'HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run'
        };
      } catch {
        return {
          enabled: false,
          platform: 'windows',
          method: 'Registry',
          path: 'HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run'
        };
      }
    
    default:
      return {
        enabled: false,
        platform: 'linux',
        method: 'Not supported',
        path: ''
      };
  }
}

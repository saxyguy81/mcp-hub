# MCP Hub

**The easiest way to manage Model Context Protocol servers**

A comprehensive management system for MCP servers using Docker containers. Built for production deployment with enterprise-grade features and **true zero-configuration setup**.

## 🎉 **v1.0.2 - Enhanced UX** 
### ✅ **100% Functional Zero-Friction Installation**

**Major UX improvements now live:**
- ⚡ **Immediate availability** - `mcpctl` works right after installation (no shell restart)
- 🌐 **Smart port handling** - Automatic port conflict detection and resolution
- 🚀 **True one-line install** - No configuration or manual steps required

## 🚀 One-Line Install

Get up and running instantly with our enhanced installer:

```bash
curl -fsSL https://github.com/saxyguy81/mcp-hub/releases/latest/download/install.sh | bash
```

**What happens now (v1.0.2):**
- 🔍 **Auto-detects** your platform (macOS/Windows/Linux) and architecture
- 📦 **Installs dependencies** automatically (Docker, Git, Python)
- ⬇️ **Downloads pre-built binaries** (or builds from source as fallback)
- ⚡ **Sets up PATH immediately** - `mcpctl` works right away (no restart needed)
- 🌐 **Handles port conflicts** - Automatically finds available ports if 3002 is busy
- ⚙️ **Configures environment** (PATH, shortcuts, auto-start)
- 🎉 **Creates demo workspace** with sample MCP server
- 🔗 **Shows connection URLs** for your LLM client

**Result: `mcpctl status` works immediately after installation! 🎯**

### 🆚 Before vs After v1.0.2

**Before (v1.0.0-v1.0.1):**
```bash
$ curl -fsSL installer-url | bash
# Installation complete
$ mcpctl status
bash: mcpctl: command not found  😞
$ source ~/.zshrc  # Manual step required
$ mcpctl status    # Now works
```

**After (v1.0.2 - Current):**
```bash
$ curl -fsSL https://github.com/saxyguy81/mcp-hub/releases/latest/download/install.sh | bash
# Installation complete
$ mcpctl status    # Works immediately! 🎉
Services: running
```

---

## ✨ Features

### 🎯 **Zero-Configuration Setup**
- **Smart Installation**: Detects first-time vs updates, preserves existing config
- **Auto-Dependency**: Installs Docker, Git, Python automatically via package managers
- **Demo Workspace**: Working MCP server ready immediately after install
- **Connection URLs**: Clear instructions on connecting your LLM client

### 🔒 **Encrypted Workspace Management**- **Portable Configurations**: Share complete MCP setups via git repositories
- **Encrypted Secrets**: Store API keys safely in git with user-controlled encryption
- **Workspace Templates**: Pre-configured setups for common use cases
- **Auto-Discovery**: Finds and suggests MCP servers from popular repositories

### 📊 **Management & Monitoring**
- **Real-time Status**: Monitor all MCP servers from a unified dashboard
- **Health Checks**: Automatic monitoring with restart capabilities
- **Resource Usage**: CPU, memory, and network monitoring per server
- **Logs & Debugging**: Centralized logging with filtering and search

### 🔧 **Developer Experience**
- **CLI Interface**: Full-featured command-line tool (`mcpctl`)
- **Web Dashboard**: Browser-based management interface
- **API Access**: RESTful API for automation and integration
- **VS Code Extension**: Direct integration with your development environment

---

## 📚 Quick Start

### After Installation

1. **Check status:**
   ```bash
   mcpctl status
   ```

2. **Connect your LLM client:**
   - Claude Desktop: Add server URL to settings
   - OpenAI: Configure MCP connection
   - Custom clients: Use provided connection details

3. **Explore workspaces:**
   ```bash
   mcpctl workspace list
   mcpctl workspace create my-project
   ```

### Common Commands

```bash
# Server management
mcpctl start <server-name>
mcpctl stop <server-name>
mcpctl restart <server-name>
mcpctl logs <server-name>

# Workspace operations
mcpctl workspace create <name>
mcpctl workspace clone <git-url>
mcpctl workspace encrypt <name>
mcpctl workspace share <name>

# System operations
mcpctl update
mcpctl doctor
mcpctl config
```

---

## 🏗️ Architecture

### Core Components
- **mcpctl**: Command-line interface and orchestration engine
- **Container Engine**: Docker-based server isolation and management
- **Workspace Manager**: Git-based configuration and sharing
- **Encryption Layer**: Secure secret management with multiple backends
- **Web Interface**: Browser-based dashboard and controls

### Supported Platforms
- ✅ **macOS** (Intel & Apple Silicon)
- ✅ **Linux** (Ubuntu, Debian, CentOS, Arch)
- ✅ **Windows** (Windows 10/11, WSL2)

---

## 📖 Documentation

- 📘 **[Installation Guide](docs/DEPLOYMENT.md)** - Detailed setup instructions
- 🏗️ **[Architecture](docs/ARCH.md)** - System design and components
- 🧪 **[Testing](docs/QA_TESTING.md)** - Quality assurance and testing procedures
- 🔄 **[Development](docs/TODO.md)** - Roadmap and contribution guidelines

---

## 🤝 Contributing

We welcome contributions! Please see our [contribution guidelines](docs/TODO.md) for details on:
- Setting up the development environment
- Running tests
- Submitting pull requests
- Reporting issues

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- Model Context Protocol specification and community
- Docker for containerization technology
- All contributors and testers who helped make this project possible

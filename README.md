# MCP Hub

[![Build & Test](https://github.com/saxyguy81/mcp-hub/actions/workflows/build.yml/badge.svg)](https://github.com/saxyguy81/mcp-hub/actions/workflows/build.yml)
[![Code Quality](https://github.com/saxyguy81/mcp-hub/actions/workflows/code-quality.yml/badge.svg)](https://github.com/saxyguy81/mcp-hub/actions/workflows/code-quality.yml)
[![Cross-Platform Tests](https://github.com/saxyguy81/mcp-hub/actions/workflows/test-installations.yml/badge.svg)](https://github.com/saxyguy81/mcp-hub/actions/workflows/test-installations.yml)

**The easiest way to manage Model Context Protocol servers**

A comprehensive management system for MCP servers using Docker containers. Built for production deployment with enterprise-grade features and **true zero-configuration setup**.

## 🎉 **v1.0.3 - Single Endpoint Proxy** 
### ✅ **Complete MCP Aggregation Proxy Implementation**

**NEW: Revolutionary single-endpoint proxy system:**
- 🎯 **Single Endpoint Mode** - One URL instead of multiple server configurations
- 🔄 **Automatic Request Routing** - Tools and resources routed to correct servers
- 📊 **Real-time Health Monitoring** - Backend server health tracking with failover
- 🖥️ **Native GUI Management** - Beautiful desktop app for proxy monitoring
- ⚡ **Zero-Configuration Discovery** - Automatically finds and routes to MCP servers

## 🎯 **Single Endpoint Revolution**

**The Problem:** Manually configuring multiple MCP server endpoints
```json
// OLD: Configure each server individually
{
  "mcpServers": {
    "firecrawl": { "command": "http://localhost:8081" },
    "web-search": { "command": "http://localhost:8082" },
    "database": { "command": "http://localhost:8083" },
    "github": { "command": "http://localhost:8084" }
  }
}
```

**The Solution:** Single aggregation proxy endpoint
```json
// NEW: One endpoint for everything
{
  "mcpServers": {
    "mcp-hub": { "command": "http://localhost:3000" }
  }
}
```

## 🚀 One-Line Install

Get up and running instantly with our enhanced installer:

```bash
curl -fsSL https://github.com/saxyguy81/mcp-hub/releases/latest/download/install.sh | bash
```

**What happens now (v1.0.3):**
- 🔍 **Auto-detects** your platform (macOS/Windows/Linux) and architecture
- 📦 **Installs dependencies** automatically (Docker, Git, Python)
- ⬇️ **Downloads pre-built binaries** (or builds from source as fallback)
- ⚡ **Sets up PATH immediately** - `mcpctl` works right away (no restart needed)
- 🌐 **Handles port conflicts** - Automatically finds available ports if 3002 is busy
- ⚙️ **Configures environment** (PATH, shortcuts, auto-start)
- 🎉 **Creates demo workspace** with sample MCP server
- 🎯 **Sets up proxy server** for single-endpoint mode
- 🔗 **Shows connection URLs** for your LLM client

**Result: `mcpctl proxy start` enables single-endpoint mode! 🎯**

## ✨ Features

### 🎯 **Single Endpoint Proxy (NEW!)**
- **Aggregation Proxy**: All MCP servers accessible via `http://localhost:3000`
- **Automatic Discovery**: Finds MCP servers from docker-compose configuration
- **Request Routing**: Routes tools/resources to appropriate backend servers
- **Health Monitoring**: 30-second health checks with automatic failover
- **Protocol Compliance**: Full MCP JSON-RPC 2.0 specification support

### 🎯 **Zero-Configuration Setup**
- **Smart Installation**: Detects first-time vs updates, preserves existing config
- **Auto-Dependency**: Installs Docker, Git, Python automatically via package managers
- **Demo Workspace**: Working MCP server ready immediately after install
- **Connection URLs**: Clear instructions on connecting your LLM client

### 🔒 **Encrypted Workspace Management**
- **Portable Configurations**: Share complete MCP setups via git repositories
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
- **Proxy Management**: Complete proxy lifecycle management (`mcpctl proxy`)
- **Native GUI**: Desktop application with visual proxy management
- **Web Dashboard**: Browser-based management interface
- **API Access**: RESTful API for automation and integration

---

## 📚 Quick Start

### After Installation

1. **Start your MCP services:**
   ```bash
   mcpctl start
   ```

2. **Enable single endpoint mode:**
   ```bash
   mcpctl proxy start
   ```

3. **Check connection info:**
   ```bash
   mcpctl connect
   # Shows: Configure your LLM client with http://localhost:3000
   ```

4. **Configure your LLM client:**
   - Claude Desktop: Add single server URL to settings
   - OpenAI: Configure MCP connection
   - Custom clients: Use provided connection details

### Proxy Management

```bash
# Proxy lifecycle
mcpctl proxy start         # Start aggregation proxy
mcpctl proxy stop          # Stop proxy
mcpctl proxy restart       # Restart proxy
mcpctl proxy status        # Show detailed status

# Monitoring
mcpctl proxy servers       # List backend servers
mcpctl proxy logs          # View proxy logs
mcpctl proxy logs --follow # Follow logs in real-time

# Get connection info
mcpctl connect             # Shows single endpoint configuration
```

### Native GUI Application

```bash
# Launch desktop application
cd electron
npm install
npm start
```

**GUI Features:**
- 📊 Real-time proxy and server status dashboard
- 🎯 Visual proxy management (start/stop/restart)
- 🔗 Backend server health monitoring
- 📜 Live log viewing with auto-refresh
- ⚙️ Settings and configuration management

### Workspace Management

```bash
# Explore workspaces
mcpctl workspace list
mcpctl workspace activate demo-workspace

# Create and share workspaces
mcpctl workspace create my-setup --from-current
mcpctl workspace export my-setup --format git
```

---

## 🏗️ Architecture

### Traditional Multi-Endpoint Setup
```
LLM Client
├── http://localhost:8081 → Firecrawl Server
├── http://localhost:8082 → Web Search Server
├── http://localhost:8083 → Database Server
└── http://localhost:8084 → GitHub Server
```

### New Single Endpoint Architecture
```
LLM Client
└── http://localhost:3000 → MCP Hub Proxy
    ├── Routes to → firecrawl:8081
    ├── Routes to → web-search:8082
    ├── Routes to → database:8083
    └── Routes to → github:8084
```

**Benefits:**
- ✅ **Single Configuration**: One endpoint instead of 4+
- ✅ **Automatic Discovery**: No manual server registration
- ✅ **Health Monitoring**: Built-in failover and retry logic
- ✅ **Protocol Compliance**: Full MCP specification support
- ✅ **Zero Latency Impact**: <100ms additional overhead

---

## 🚀 Advanced Usage

### Custom Proxy Configuration
```bash
# Custom port and settings
mcpctl proxy start --port 3001
mcpctl proxy start --config custom-compose.yml

# Development mode
mcpctl proxy start --background false --log-level DEBUG
```

### Docker Integration
```bash
# Build proxy container
docker build -f Dockerfile.proxy -t mcp-hub/proxy .

# Run as container service
mcpctl generate  # Includes proxy service automatically
```

### Production Deployment
```bash
# Enable auto-start
mcpctl setup --auto-start

# Monitor in production
mcpctl proxy status
mcpctl proxy logs --follow
```

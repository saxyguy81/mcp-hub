# MCP Hub

A comprehensive management system for Model Context Protocol (MCP) servers using Docker containers. Built for production deployment with enterprise-grade features.

## ✨ Features

### 🖥️ **Desktop Application**
- **Setup Wizard**: Guided first-run experience with dependency checking
- **LLM Backend Selection**: Support for Claude Desktop, OpenAI API, and custom endpoints
- **Connection Testing**: Real-time LLM backend connectivity validation
- **Settings Panel**: Centralized configuration management

### 🐳 **Container Management** 
- **Engine Abstraction**: Native support for both Docker and Vessel runtimes
- **Service Discovery**: Automatically discover MCP servers in your codebase
- **Health Monitoring**: Built-in health checks and auto-restart capabilities
- **Digest Locking**: Reproducible deployments with image digest pinning

### 🔐 **Enterprise Security**
- **Secret Management**: Support for LastPass and environment-based secrets
- **Registry Support**: Push to GitHub Container Registry, GitLab, or offline tarballs
- **Auto-start Integration**: LaunchAgents (macOS) and Registry keys (Windows)

### 🛠️ **Developer Experience**
- **CLI Tools**: Full command-line interface for CI/CD automation
- **Cross-platform**: Native support for macOS, Windows, and Linux
- **Background Daemon**: Monitoring and auto-restart capabilities

## 🚀 Quick Start

### Desktop Application Setup

1. **Download** the latest release for your platform
2. **Launch** MCP Hub and follow the setup wizard
3. **Configure** your LLM backend (Claude/OpenAI/Custom)
4. **Install** dependencies automatically (Docker, Git, Python)
5. **Start** managing your MCP servers!

### CLI Setup

```bash
# Clone the repository
git clone https://github.com/saxyguy81/mcp-hub.git
cd mcp-hub

# Install Python dependencies
pip install -r requirements.txt

# Initialize configuration
python -m mcpctl.cli init

# Discover and start services
python -m mcpctl.cli discover
python -m mcpctl.cli generate
python -m mcpctl.cli start
```

## 📋 CLI Commands

### Core Management
- `mcpctl init` - Initialize MCP Hub configuration
- `mcpctl discover` - Find MCP servers in current directory
- `mcpctl generate` - Create docker-compose.yml from service definitions
- `mcpctl start/stop/status` - Manage running services

### Service Operations
- `mcpctl add <service>` - Add new MCP service
- `mcpctl remove <service>` - Remove MCP service  
- `mcpctl test <service>` - Test service health

### Production Features
- `mcpctl lock-images` - Lock images to specific digests
- `mcpctl pull-images` - Pull using locked digests for reproducibility
- `mcpctl regenerate-bridge` - Update OpenAPI bridge configuration
- `mcpctl daemon` - Run background monitoring daemon

## ⚙️ Configuration

### Desktop App Configuration
Configuration is managed through the Settings panel with tabs for:
- **LLM & Tools**: Backend selection and testing
- **General**: Git remotes, registry, and secrets
- **Advanced**: Container engine and debug settings

### CLI Configuration
Configuration stored in `~/.mcpctl/config.toml`:

```toml
git_remote = "https://github.com/user/mcp-registry"
registry_driver = "ghcr"  # ghcr | gitlab | offline  
secrets_backend = "env"   # lastpass | env
docker_registry = "ghcr.io"
```

## 🏗️ Architecture

### Project Structure
```
mcp-hub/
├── mcpctl/              # Python CLI package
│   ├── cli.py          # Main command interface
│   ├── container_engine.py  # Docker/Vessel abstraction
│   ├── digest_manager.py    # Image digest locking
│   └── secret_backends/     # Secret management
├── electron/            # Desktop application
│   ├── src/            # React/TypeScript frontend
│   ├── electron.js     # Electron main process
│   └── preload.js      # IPC bridge
├── services/           # Service definitions
├── docs/              # Documentation
└── compose.template.yml # Base Docker Compose template
```

### Container Engine Support
- **Docker**: Full Docker Desktop and Docker CE support
- **Vessel**: macOS-optimized container runtime with compatibility layer
- **Automatic Detection**: Runtime auto-discovery with fallback support

### LLM Integration
- **Claude Desktop**: Local connection via HTTP API
- **OpenAI API**: Cloud-based ChatGPT integration
- **Custom Endpoints**: Any OpenAI-compatible API endpoint

## 🔒 Production Deployment

### Image Digest Locking
Ensure reproducible deployments across environments:

```bash
# Lock current image versions
mcpctl lock-images --compose-file docker-compose.yml

# Deploy with locked versions
mcpctl pull-images --lock-file images.lock.json
mcpctl start
```

### Auto-start Configuration
Automatically start MCP Hub daemon on system boot:

- **macOS**: LaunchAgents integration (`~/Library/LaunchAgents/`)
- **Windows**: Registry Run keys (`HKCU\Software\Microsoft\Windows\CurrentVersion\Run`)
- **Linux**: systemd service files (planned)

### Health Monitoring
Built-in health checks with configurable intervals:

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
  interval: 30s
  timeout: 5s
  retries: 3
  start_period: 10s
```

## 🛠️ Development

### Prerequisites
- **Docker** or **Vessel** container runtime
- **Git** version control
- **Python 3.10+** for CLI components
- **Node.js 18+** for desktop application

### Building from Source

```bash
# CLI Development
cd mcpctl/
pip install -e .

# Desktop App Development  
cd electron/
npm install
npm start          # Development server
npm run build      # Production build
```

### Container Engine Testing

```bash
# Test Docker integration
mcpctl test-engine docker

# Test Vessel integration  
mcpctl test-engine vessel

# Auto-detect and test available engine
mcpctl status
```

## 📚 Documentation

- **[Architecture Guide](docs/ARCH.md)** - Technical architecture and design decisions
- **[API Reference](docs/API.md)** - CLI and desktop app API documentation  
- **[Contributing Guide](CONTRIBUTING.md)** - Development setup and guidelines
- **[Troubleshooting](docs/TROUBLESHOOTING.md)** - Common issues and solutions

## 🧪 Testing

Run the acceptance test suite to verify installation:

```bash
# Basic functionality test
mcpctl test --all

# Desktop app UI test  
npm test --prefix electron

# End-to-end workflow test
./scripts/e2e-test.sh
```

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details on:

- Setting up the development environment
- Running tests
- Submitting pull requests
- Code style guidelines

## 🔗 Links

- **[GitHub Repository](https://github.com/saxyguy81/mcp-hub)**
- **[Issue Tracker](https://github.com/saxyguy81/mcp-hub/issues)**
- **[Release Notes](https://github.com/saxyguy81/mcp-hub/releases)**
- **[MCP Protocol](https://modelcontextprotocol.io/docs)** - Learn about MCP

---

**Built with ❤️ by the MCP Hub team**

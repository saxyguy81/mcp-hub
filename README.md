# MCP Hub

**The easiest way to manage Model Context Protocol servers**

A comprehensive management system for MCP servers using Docker containers. Built for production deployment with enterprise-grade features and zero-configuration setup.

## 🚀 One-Line Install

Get up and running instantly with our smart bootstrap installer:

```bash
curl -fsSL https://github.com/saxyguy81/mcp-hub/releases/latest/download/install.sh | bash
```

**What happens:**
- 🔍 **Auto-detects** your platform (macOS/Windows/Linux) and architecture
- 📦 **Installs dependencies** automatically (Docker, Git, Python)
- ⬇️ **Downloads pre-built binaries** (or builds from source as fallback)
- ⚙️ **Configures environment** (PATH, shortcuts, auto-start)
- 🎉 **Creates demo workspace** with sample MCP server
- 🔗 **Shows connection URLs** for your LLM client

**First-time install:** Runs setup wizard and creates demo workspace  
**Updates:** Preserves existing configuration and shows current status

### Installation Options
```bash
# Build from source (slower but works everywhere)
curl -fsSL https://github.com/saxyguy81/mcp-hub/releases/latest/download/install.sh | bash -s -- --build-from-source

# Skip dependency installation (if already installed)
curl -fsSL https://github.com/saxyguy81/mcp-hub/releases/latest/download/install.sh | bash -s -- --skip-deps

# See all options
curl -fsSL https://github.com/saxyguy81/mcp-hub/releases/latest/download/install.sh | bash -s -- --help
```

---

## ✨ Features

### 🎯 **Zero-Configuration Setup**
- **Smart Installation**: Detects first-time vs updates, preserves existing config
- **Auto-Dependency**: Installs Docker, Git, Python automatically via package managers
- **Demo Workspace**: Working MCP server ready immediately after install
- **Connection URLs**: Clear instructions on connecting your LLM client

### 🔒 **Encrypted Workspace Management**
- **Portable Configurations**: Share complete MCP setups via git repositories
- **Encrypted Secrets**: Store API keys safely in git with user-controlled encryption
- **Cross-Platform Sync**: Same workspace works on macOS, Windows, Linux
- **Team Collaboration**: Share configurations securely without exposing secrets

### 🧪 **LLM Backend Verification**
- **Connection Testing**: Verify Claude Desktop, OpenAI API, and custom LLMs
- **Interactive Setup**: Wizard-guided LLM configuration with real-time testing
- **Detailed Diagnostics**: Clear error messages and troubleshooting suggestions
- **Multiple Backends**: Support any OpenAI-compatible API endpoint

### 🐳 **Container Management**
- **Engine Abstraction**: Works with Docker Desktop, Docker CE, and Vessel
- **Service Discovery**: Auto-detect MCP servers in your codebase
- **Health Monitoring**: Built-in health checks and auto-restart capabilities
- **Digest Locking**: Reproducible deployments with image digest pinning

### 🖥️ **Desktop & CLI Apps**
- **Electron GUI**: User-friendly desktop app with setup wizard
- **Full CLI**: Complete command-line interface for automation
- **Cross-Platform**: Native support for macOS, Windows, Linux
- **Auto-Start**: Optional auto-start on system boot

---

## 🎯 Quick Start

### 1. Install MCP Hub
```bash
curl -fsSL https://github.com/saxyguy81/mcp-hub/releases/latest/download/install.sh | bash
```

### 2. Connect Your LLM Client
After installation, you'll see:
```
🔗 Your MCP servers are ready at:
   🟢 http://localhost:3002

📋 Connect your LLM to: http://localhost:3002
```

**For Claude Desktop:**
1. Open Claude Desktop preferences
2. Add MCP server: `http://localhost:3002`
3. Save and restart Claude Desktop

**For other LLM clients:**
- Use the URL shown after installation
- Configure as OpenAI-compatible endpoint
- API key not required for local MCP servers

### 3. Manage Your Services
```bash
# Check what's running
mcpctl status

# Start/stop services
mcpctl start
mcpctl stop

# View connection URLs anytime
mcpctl urls

# Interactive setup
mcpctl setup --wizard
```

---

## 📦 Workspace Management

### Create and Share Configurations
```bash
# Create workspace from current setup
mcpctl workspace create my-ai-stack --from-current

# Export for sharing (with encrypted secrets)
mcpctl workspace export my-ai-stack --format git

# Share via git repository
cd my-ai-stack-git/my-ai-stack
git init && git remote add origin https://github.com/user/my-config.git
git add . && git commit -m "My MCP configuration"
git push origin main
```

### Import and Use Shared Workspaces
```bash
# Import from git repository
mcpctl workspace import https://github.com/user/my-config.git --activate

# Import from file
mcpctl workspace import my-config.tar.gz --activate

# List available workspaces
mcpctl workspace list

# Switch between workspaces
mcpctl workspace activate my-other-stack
```

### Encrypted Secrets System
```bash
# Create workspace with encrypted secrets
mcpctl workspace create secure-stack --encrypt-secrets
# 🔐 Enter encryption key: [hidden input]
# 💾 Store in LastPass? y
# ✅ Secrets encrypted and safe for git

# View encrypted secrets (masked)
mcpctl workspace decrypt secure-stack --show-secrets

# Export decrypted secrets to file
mcpctl workspace decrypt secure-stack --export-env
```

**Key Features:**
- 🔒 **Secrets encrypted** in git repositories (AES-256)
- 🔑 **User-controlled keys** via LastPass or manual entry
- 🌍 **Cross-platform sync** with automatic decryption
- 👥 **Team sharing** without exposing credentials

---

## 🧪 LLM Backend Testing

### Test Your LLM Connections
```bash
# Test all configured backends
mcpctl llm test

# Test specific backend
mcpctl llm test claude                    # Claude Desktop
mcpctl llm test openai --api-key YOUR_KEY # OpenAI API
mcpctl llm test custom --url https://api.your-provider.com --api-key YOUR_KEY

# Interactive setup with testing
mcpctl llm setup

# Check current status
mcpctl llm status
```

### Example Output
```
🧪 Testing LLM Backend Connections
==================================

Claude: ✅ PASS
  Duration: 0.12s
  ✅ Claude Desktop connected on port 52262

Custom: ✅ PASS  
  Duration: 1.23s
  Status: 200
  ✅ Custom LLM connection successful
  Details:
    endpoint: https://api.anthropic.com/v1/chat/completions
    model: claude-3-sonnet
    response: "Hello! This is a connection test response."

📊 Summary: 2/2 backends working
🎉 All tested backends are working!
```

---

## 📋 CLI Reference

### Essential Commands
```bash
# Installation & Setup
mcpctl setup --wizard              # Interactive setup wizard
mcpctl info                        # Show connection details
mcpctl urls                        # Show all service URLs
mcpctl status                      # Check service status

# Service Management  
mcpctl start                       # Start all services
mcpctl stop                        # Stop all services
mcpctl restart                     # Restart all services

# Workspace Management
mcpctl workspace create <name>     # Create new workspace
mcpctl workspace list             # List workspaces
mcpctl workspace activate <name>  # Switch workspace
mcpctl workspace import <source>  # Import workspace

# LLM Backend Testing
mcpctl llm test                   # Test all backends
mcpctl llm setup                  # Configure backends
mcpctl llm status                 # Show backend status
```

### Advanced Commands
```bash
# Service Discovery & Management
mcpctl discover                   # Find MCP servers in directory
mcpctl add <service>             # Add new service
mcpctl remove <service>          # Remove service

# Production Features
mcpctl lock-images               # Lock images to specific digests
mcpctl pull-images               # Pull using locked digests
mcpctl publish-images            # Publish to container registry

# Secret Management
mcpctl workspace encrypt <name>  # Encrypt workspace secrets
mcpctl workspace decrypt <name>  # Decrypt workspace secrets
mcpctl workspace generate-key    # Generate encryption key

# Development & Testing
mcpctl daemon                    # Run background daemon
mcpctl test --all               # Run test suite
```

---

## ⚙️ Configuration

### Workspace Configuration
Workspaces are stored in `~/.mcpctl/workspaces/` with this structure:
```
my-workspace/
├── workspace.yml              # Metadata & encrypted secrets
├── docker-compose.yml         # Service definitions  
├── services/                  # Individual service configs
├── secrets.env.template       # Secret placeholders (unencrypted)
└── README.md                  # Documentation
```

### Global Configuration
Stored in `~/.mcpctl/config.toml`:
```toml
# Git repository for shared configurations
git_remote = "https://github.com/user/mcp-configs"

# Container registry settings
registry_driver = "ghcr"        # ghcr | gitlab | offline
docker_registry = "ghcr.io"

# Secret management
secrets_backend = "env"         # lastpass | env

# LLM backend settings
openai_api_key = "sk-..."
custom_llm_url = "https://api.provider.com"
```

### Environment Variables
```bash
# LLM Configuration
export OPENAI_API_KEY="sk-your-openai-key"
export CUSTOM_LLM_URL="https://api.your-provider.com"
export CUSTOM_LLM_API_KEY="your-api-key"

# MCP Hub Configuration  
export MCPCTL_REGISTRY="ghcr.io"
export MCPCTL_SECRETS_BACKEND="lastpass"
```

---

## 🔧 Advanced Usage

### Production Deployment
```bash
# Lock images for reproducible deployments
mcpctl lock-images --compose-file docker-compose.yml

# Deploy on production server
mcpctl pull-images --lock-file images.lock.json
mcpctl start

# Enable auto-start on boot
mcpctl setup --auto-start
```

### Team Collaboration
```bash
# Team lead creates standard environment
mcpctl workspace create team-ai-stack --from-current --encrypt-secrets
mcpctl workspace export team-ai-stack --format git
# Push to company git repository

# Team members sync
mcpctl workspace import https://github.com/company/ai-stack.git --activate
# Enter shared encryption key (or retrieve from LastPass)
mcpctl start
```

### Multi-Environment Management
```bash
# Different environments
mcpctl workspace create development
mcpctl workspace create staging  
mcpctl workspace create production

# Switch between environments
mcpctl workspace activate development
mcpctl start

mcpctl workspace activate production
mcpctl start
```

### Container Registry Integration
```bash
# GitHub Container Registry
mcpctl publish-images --registry ghcr.io --tag latest

# GitLab Container Registry  
mcpctl publish-images --registry registry.gitlab.com --tag v1.0.0

# Offline deployment (air-gapped)
mcpctl publish-images --offline --output images.tar.gz
```

---

## 🏗️ Architecture

### System Components
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   LLM Client    │    │  MCP Hub GUI    │    │  MCP Hub CLI    │
│ (Claude Desktop)│    │  (Electron)     │    │   (Python)      │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          │              ┌───────┴──────────────────────┴───────┐
          │              │           MCP Hub Core               │
          │              │  • Workspace Management             │
          │              │  • Secret Encryption                │
          │              │  • LLM Testing                      │
          │              │  • Container Orchestration          │
          │              └───────┬──────────────────────────────┘
          │                      │
    ┌─────┴─────┐         ┌──────┴──────┐
    │MCP Server │◄────────┤   Docker    │
    │Container  │         │  / Vessel   │
    │           │         │             │
    └───────────┘         └─────────────┘
```

### Project Structure
```
mcp-hub/
├── mcpctl/                    # Python CLI package
│   ├── cli.py                # Command-line interface
│   ├── workspace.py          # Workspace management
│   ├── encryption.py         # Secret encryption
│   ├── llm_tester.py         # LLM backend testing
│   ├── onboarding.py         # Installation flows
│   ├── container_engine.py   # Docker/Vessel abstraction
│   └── secret_backends/      # Secret management backends
├── electron/                 # Desktop application
│   ├── src/                  # React/TypeScript frontend
│   ├── electron.js           # Main process
│   └── preload.js           # IPC bridge
├── scripts/                  # Installation & testing scripts
│   ├── install.sh           # Bootstrap installer
│   ├── test-*.sh           # Test scripts
│   └── e2e-test.sh         # End-to-end tests
├── workspaces/              # Example workspace templates
├── docs/                    # Documentation
└── web/                     # Download service (optional)
```

---

## 🛠️ Development

### Prerequisites
- **Docker** or **Vessel** container runtime
- **Git** version control  
- **Python 3.8+** for CLI components
- **Node.js 18+** for desktop application (optional)

### Building from Source
```bash
# Clone repository
git clone https://github.com/saxyguy81/mcp-hub.git
cd mcp-hub

# Install Python dependencies
pip install -r requirements.txt

# Build CLI binary (optional)
pip install pyinstaller
pyinstaller main.py -n mcpctl --onefile

# Build desktop app (optional)
cd electron
npm install
npm run build
```

### Development Workflow
```bash
# CLI development
cd mcpctl/
python -m pip install -e .

# Test CLI changes
mcpctl --help

# Desktop app development
cd electron/
npm start              # Development server
npm run build          # Production build

# Run tests
./scripts/test-bootstrap.sh    # Bootstrap installer
./scripts/test-workspace.sh    # Workspace system
./scripts/test-encryption.sh   # Encrypted secrets
./scripts/test-llm.sh          # LLM testing
```

---

## 📚 Documentation

### Guides
- **[Installation Guide](docs/INSTALLATION.md)** - Detailed installation instructions
- **[Workspace Guide](docs/WORKSPACES.md)** - Complete workspace management
- **[Encrypted Secrets Guide](docs/ENCRYPTION.md)** - Secret encryption system
- **[LLM Testing Guide](docs/LLM_TESTING.md)** - Backend verification
- **[Architecture Guide](docs/ARCH.md)** - Technical architecture

### Reference
- **[CLI Reference](docs/CLI.md)** - Complete command reference
- **[API Reference](docs/API.md)** - Desktop app API documentation
- **[Configuration Reference](docs/CONFIG.md)** - All configuration options
- **[Troubleshooting](docs/TROUBLESHOOTING.md)** - Common issues and solutions

### Examples
- **[Example Workspaces](workspaces/)** - Pre-built workspace templates
- **[Team Setup](docs/examples/TEAM_SETUP.md)** - Team collaboration examples
- **[Production Deployment](docs/examples/PRODUCTION.md)** - Production setup examples

---

## 🧪 Testing

### Quick Tests
```bash
# Test installation
curl -fsSL https://github.com/saxyguy81/mcp-hub/releases/latest/download/install.sh | bash --skip-deps

# Test CLI functionality
mcpctl --help
mcpctl workspace list
mcpctl llm status

# Test LLM connections
mcpctl llm test
```

### Full Test Suite
```bash
# Run all tests
./scripts/test-bootstrap.sh     # Installation system
./scripts/test-workspace.sh     # Workspace management  
./scripts/test-encryption.sh    # Encrypted secrets
./scripts/test-llm.sh           # LLM verification
./scripts/e2e-test.sh           # End-to-end workflow

# Desktop app tests
cd electron && npm test

# CLI tests  
python -m pytest mcpctl/tests/
```

---

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for:

- Development environment setup
- Code style guidelines  
- Testing requirements
- Pull request process

### Quick Start for Contributors
```bash
# Fork and clone
git clone https://github.com/YOUR_USERNAME/mcp-hub.git
cd mcp-hub

# Set up development environment
pip install -r requirements.txt
pip install -e .

# Make changes and test
mcpctl --help
./scripts/test-*.sh

# Submit pull request
git add .
git commit -m "Your changes"
git push origin your-branch
# Create PR on GitHub
```

---

## 🔗 Links & Resources

### Project
- **[GitHub Repository](https://github.com/saxyguy81/mcp-hub)**
- **[Issue Tracker](https://github.com/saxyguy81/mcp-hub/issues)**
- **[Release Notes](https://github.com/saxyguy81/mcp-hub/releases)**
- **[Discussions](https://github.com/saxyguy81/mcp-hub/discussions)**

### MCP Protocol
- **[MCP Specification](https://modelcontextprotocol.io/docs)**
- **[MCP Examples](https://github.com/modelcontextprotocol)**
- **[Claude Desktop MCP](https://docs.anthropic.com/claude/docs/mcp)**

### Community
- **[Discord Server](https://discord.gg/mcp-hub)** (coming soon)
- **[Twitter Updates](https://twitter.com/mcphub)** (coming soon)

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

**Built with ❤️ for the MCP community**

*Making Model Context Protocol servers as easy as `curl | bash`*

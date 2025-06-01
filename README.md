# MCP Hub

A comprehensive management system for Model Context Protocol (MCP) servers using Docker containers.

## Features

- **Service Discovery**: Automatically discover MCP servers in your codebase
- **Docker Integration**: Containerize and orchestrate MCP servers
- **Secret Management**: Support for LastPass and environment-based secrets
- **Registry Support**: Push to GitHub Container Registry, GitLab, or offline tarballs
- **Desktop App**: Electron-based GUI for easy management
- **CLI Tools**: Command-line interface for automation

## Quick Start

1. **Install dependencies**: Docker, Git, Python 3.10+
2. **Run the CLI**: `mcpctl init`
3. **Discover services**: `mcpctl discover`
4. **Generate compose**: `mcpctl generate`
5. **Start services**: `mcpctl start`

## CLI Commands

- `mcpctl init` - Initialize configuration
- `mcpctl discover` - Find MCP servers
- `mcpctl generate` - Create docker-compose.yml
- `mcpctl start/stop/status` - Manage services
- `mcpctl publish-images` - Build and publish containers

## Configuration

Configuration is stored in `~/.mcpctl/config.toml`:

```toml
git_remote = "https://github.com/user/mcp-registry"
registry_driver = "ghcr"  # ghcr | gitlab | offline
secrets_backend = "env"   # lastpass | env
```

## Architecture

- **mcpctl/**: Python CLI package
- **electron/**: Desktop application
- **services/**: Service definitions
- **compose.template.yml**: Base Docker Compose template

Built with Python, TypeScript, Docker, and Electron.

# MCP Hub Architecture

*Last updated: 2025-05-31*

## Overview

MCP Hub is a production-ready management system for Model Context Protocol servers, built with a hybrid desktop/CLI architecture supporting multiple container runtimes and LLM backends.

## Core Architecture

### Component Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Desktop App   │    │   CLI Package   │    │ Container Layer │
│   (Electron)    │    │   (Python)      │    │ (Docker/Vessel) │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ • Wizard UI     │    │ • Service Mgmt  │    │ • Engine Abstraction
│ • Settings      │    │ • Compose Gen   │    │ • Health Checks
│ • LLM Testing   │    │ • Discovery     │    │ • Digest Locking
│ • IPC Bridge    │    │ • Registry Ops  │    │ • Auto-restart
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │  Configuration  │
                    │    Layer        │
                    ├─────────────────┤
                    │ • TOML/JSON     │
                    │ • Secret Mgmt   │
                    │ • Auto-start    │
                    └─────────────────┘
```

### Design Principles

1. **Platform Agnostic**: Native support for macOS, Windows, Linux
2. **Container Agnostic**: Docker and Vessel runtime support
3. **LLM Agnostic**: Multiple AI backend integration
4. **Production Ready**: Digest locking, monitoring, auto-restart
5. **Developer Friendly**: CLI-first with GUI convenience layer

## Component Details

### 1. Desktop Application (Electron)

**Technology Stack:**
- Electron 28.x
- React 18.x + TypeScript
- Vite build system
- Native Node.js integration

**Architecture:**
```
electron/
├── electron.js          # Main process (Node.js backend)
├── preload.js          # IPC security bridge
├── src/
│   ├── App.tsx         # React application root
│   ├── pages/
│   │   ├── Wizard.tsx  # Setup wizard component
│   │   └── Settings.tsx # Configuration panel
│   ├── deps.ts         # Dependency management
│   └── autostart.ts    # System integration
└── build/              # Production builds
```

**Key Features:**
- **Setup Wizard**: 5-step guided configuration
- **LLM Backend Testing**: Real-time connectivity validation
- **Dependency Management**: Cross-platform installer detection
- **IPC Security**: Context isolation with controlled API exposure

### 2. CLI Package (Python)

**Technology Stack:**
- Python 3.10+
- Typer CLI framework
- Docker Python SDK
- PyYAML configuration

**Architecture:**
```
mcpctl/
├── cli.py                  # Main command interface
├── container_engine.py     # Runtime abstraction
├── digest_manager.py       # Image reproducibility
├── compose_gen.py         # Docker Compose generation
├── discover.py            # Service discovery
├── registry.py            # Container registry operations
└── secret_backends/       # Pluggable secret management
    ├── base.py
    ├── env.py
    └── lastpass.py
```

**Key Features:**
- **Service Discovery**: Filesystem scanning for MCP servers
- **Compose Generation**: Template-based service orchestration  
- **Registry Management**: Multi-registry push/pull operations
- **Health Monitoring**: Service status checking and auto-restart

### 3. Container Engine Abstraction

**Supported Runtimes:**
- **Docker**: Full Docker Desktop and Docker CE support
- **Vessel**: macOS-optimized container runtime

**Abstraction Layer:**
```python
# container_engine.py
ENGINE = _detect_engine()  # Auto-detect available runtime

def run(cmd: List[str], **kwargs):
    """Execute container engine command"""
    full_cmd = [ENGINE] + cmd
    return subprocess.run(full_cmd, check=True, **kwargs)

def compose_up(compose_file: str, **options):
    """Start services using compose"""
    # Unified interface for docker/vessel compose
```

**Engine Detection:**
1. Check for `docker` binary in PATH
2. Fallback to `vessel` binary if available
3. Throw runtime error if neither found

**Vessel Compatibility:**
- macOS Docker compatibility daemon
- Automatic daemon startup when needed
- Seamless compose command translation

## Data Flow

### 1. Service Discovery Flow

```
User Directory
      ↓
  Filesystem Scan
      ↓
  MCP Server Detection
      ↓
  Service Definition Generation
      ↓
  YAML Template Output
```

### 2. Configuration Management Flow

```
Desktop Wizard → JSON Config → CLI TOML Config → Runtime Environment
      ↓              ↓              ↓                    ↓
   UI State      Electron       mcpctl CLI        Container Env
```

### 3. Image Deployment Flow

```
Service Definitions → Compose Generation → Image Building → Digest Locking → Production Deployment
                              ↓                  ↓              ↓                 ↓
                     docker-compose.yml    Registry Push   images.lock.json   Reproducible Pulls
```

## Security Architecture

### 1. Secret Management

**Environment Backend:**
- Environment variable injection
- No persistent storage
- Docker secrets integration

**LastPass Backend:**
- CLI tool integration
- Encrypted vault access
- Team sharing support

### 2. IPC Security (Electron)

**Context Isolation:**
- No Node.js integration in renderer
- Controlled API exposure via preload script
- Type-safe IPC communication

**API Surface:**
```typescript
window.electronAPI = {
  checkDependencies: () => Promise<Dependencies>,
  testLLM: (config) => Promise<TestResult>,
  saveConfig: (config) => Promise<boolean>,
  regenerateBridge: () => Promise<void>
}
```

### 3. Container Security

**Image Verification:**
- Digest-based pulling
- Registry signature validation (planned)
- Vulnerability scanning integration (planned)

**Runtime Security:**
- Non-root container execution
- Resource limits and quotas
- Network isolation

## Deployment Strategies

### 1. Development Deployment

```bash
# Local development with hot reload
mcpctl discover
mcpctl generate
mcpctl start --detach=false
```

### 2. Production Deployment

```bash
# Locked deployment for consistency
mcpctl lock-images
mcpctl publish-images --registry ghcr.io
# On target machine:
mcpctl pull-images
mcpctl start
```

### 3. CI/CD Integration

```yaml
# .github/workflows/deploy.yml
- name: Deploy MCP Hub
  run: |
    mcpctl pull-images --lock-file images.lock.json
    mcpctl start --verify-health
    mcpctl daemon &
```

## Performance Considerations

### 1. Container Startup

**Optimization Strategies:**
- Multi-stage Docker builds
- Layer caching optimization
- Health check tuning
- Parallel service startup

### 2. Resource Management

**Memory:**
- Configurable container memory limits
- Garbage collection tuning for Python CLI
- Electron renderer process optimization

**CPU:**
- Container CPU quotas
- Background daemon throttling
- Async I/O for CLI operations

### 3. Storage

**Image Storage:**
- Digest-based deduplication
- Automatic cleanup of unused images
- Registry caching strategies

## Monitoring & Observability

### 1. Health Monitoring

**Service Level:**
- HTTP health check endpoints
- Container restart policies
- Custom health check commands

**System Level:**
- Daemon process monitoring
- Resource usage tracking
- Auto-start verification

### 2. Logging

**Structured Logging:**
- JSON log format for automation
- Configurable log levels
- Log rotation and retention

**Log Destinations:**
- File-based logging for daemon
- Console output for interactive CLI
- System journal integration (Linux)

## Extension Points

### 1. Secret Backends

Implement the `SecretBackend` interface:

```python
class CustomSecretBackend(SecretBackend):
    def get_secret(self, key: str) -> str:
        # Custom secret retrieval logic
        pass
    
    def set_secret(self, key: str, value: str) -> None:
        # Custom secret storage logic
        pass
```

### 2. Container Runtimes

Add support for new runtimes in `container_engine.py`:

```python
def _detect_engine() -> str:
    if shutil.which("podman"):
        return "podman"
    # ... existing detection logic
```

### 3. Registry Providers

Extend `RegistryManager` for new registries:

```python
class CustomRegistryManager(RegistryManager):
    def push_images(self, tag: str) -> None:
        # Custom registry push logic
        pass
```

## Future Architecture Considerations

### 1. Microservices Architecture

**Current**: Monolithic CLI + Desktop app
**Future**: Service mesh with dedicated components:
- Discovery service
- Registry service  
- Health monitoring service
- Configuration service

### 2. Distributed Deployments

**Current**: Single-machine deployment
**Future**: Multi-node orchestration:
- Kubernetes operator
- Docker Swarm support
- Service mesh integration

### 3. Advanced Security

**Current**: Basic secret management
**Future**: Enterprise security:
- RBAC and permissions
- Audit logging
- Certificate management
- Network policies

---

This architecture supports the current feature set while providing clear extension points for future development.

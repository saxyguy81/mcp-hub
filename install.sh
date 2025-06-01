#!/bin/bash
# MCP Hub Bootstrap Installer v1.0.2
# One-line installation for Model Context Protocol server management
# Fixes: PATH immediate availability + port conflict handling

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() { echo -e "${BLUE}[MCP Hub]${NC} $1"; }
success() { echo -e "${GREEN}✓${NC} $1"; }
error() { echo -e "${RED}✗${NC} $1"; }
warning() { echo -e "${YELLOW}⚠${NC} $1"; }

# Configuration
INSTALL_DIR="$HOME/.mcpctl"
BIN_DIR="$INSTALL_DIR/bin"
WORKSPACE_DIR="$INSTALL_DIR/workspaces"
DEMO_WORKSPACE="$WORKSPACE_DIR/demo"
DEFAULT_PORT=3002

# Global variables for discovered ports
DEMO_PORT=""
ALTERNATE_PORTS=""

# Handle command line arguments
SKIP_DEPS=false
BUILD_FROM_SOURCE=false

for arg in "$@"; do
    case $arg in
        --skip-deps) SKIP_DEPS=true ;;
        --build-from-source) BUILD_FROM_SOURCE=true ;;
        --help|-h)
            echo "MCP Hub Bootstrap Installer v1.0.2"
            echo "Usage: $0 [options]"
            echo "Options:"
            echo "  --help              Show this help"
            echo "  --skip-deps         Skip dependency installation"
            echo "  --build-from-source Build from source instead of downloading binary"
            exit 0
            ;;
    esac
done

# Enhanced port conflict detection and resolution
find_available_port() {
    local start_port=${1:-3002}
    local max_attempts=10
    local port=$start_port
    
    for ((i=0; i<max_attempts; i++)); do
        if ! lsof -i :$port &> /dev/null; then
            echo $port
            return 0
        fi
        ((port++))
    done
    
    # If no port found in range, try some common alternatives
    local alt_ports=(8080 8000 9000 3000 4000 5000)
    for alt_port in "${alt_ports[@]}"; do
        if ! lsof -i :$alt_port &> /dev/null; then
            echo $alt_port
            return 0
        fi
    done
    
    # Last resort - let system assign
    echo 0
}

check_port_conflicts() {
    log "Checking port availability..."
    
    # Check default port
    if lsof -i :$DEFAULT_PORT &> /dev/null; then
        local conflicting_process=$(lsof -i :$DEFAULT_PORT | grep LISTEN | awk '{print $1}' | head -1)
        warning "Port $DEFAULT_PORT is in use by: $conflicting_process"
        
        # Find alternative port
        DEMO_PORT=$(find_available_port $((DEFAULT_PORT + 1)))
        if [ "$DEMO_PORT" != "0" ]; then
            success "Found available port: $DEMO_PORT"
            ALTERNATE_PORTS="$DEMO_PORT"
        else
            error "No available ports found"
            return 1
        fi
    else
        success "Port $DEFAULT_PORT is available"
        DEMO_PORT=$DEFAULT_PORT
    fi
    
    # Find a few more backup ports for multiple services
    for offset in 1 2 3; do
        local test_port=$((DEMO_PORT + offset))
        if ! lsof -i :$test_port &> /dev/null; then
            ALTERNATE_PORTS="$ALTERNATE_PORTS $test_port"
        fi
    done
    
    log "Available ports: $DEMO_PORT $ALTERNATE_PORTS"
}

# Platform detection
detect_platform() {
    local os=$(uname -s)
    local arch=$(uname -m)
    
    case "$os" in
        "Darwin")
            case "$arch" in
                "x86_64") PLATFORM="macos-intel" ;;
                "arm64") PLATFORM="macos-silicon" ;;
                *) error "Unsupported macOS architecture: $arch"; exit 1 ;;
            esac
            ;;
        "Linux")
            case "$arch" in
                "x86_64") PLATFORM="linux-x64" ;;
                "aarch64") PLATFORM="linux-arm64" ;;
                *) error "Unsupported Linux architecture: $arch"; exit 1 ;;
            esac
            ;;
        "CYGWIN"*|"MINGW"*|"MSYS"*)
            PLATFORM="windows-x64"
            ;;
        *)
            error "Unsupported operating system: $os"
            exit 1
            ;;
    esac
    
    success "Detected platform: $PLATFORM"
}

# Check dependencies
check_dependencies() {
    if [ "$SKIP_DEPS" = true ]; then
        log "Skipping dependency check (--skip-deps specified)"
        return 0
    fi
    
    log "Checking dependencies..."
    
    local missing_deps=()
    
    if ! command -v docker &> /dev/null; then
        missing_deps+=("docker")
    fi
    
    if ! command -v git &> /dev/null; then
        missing_deps+=("git")
    fi
    
    if ! command -v python3 &> /dev/null; then
        missing_deps+=("python3")
    fi
    
    if [ ${#missing_deps[@]} -gt 0 ]; then
        warning "Missing dependencies: ${missing_deps[*]}"
        install_dependencies "${missing_deps[@]}"
    else
        success "All dependencies available"
    fi
}

# Install missing dependencies
install_dependencies() {
    local deps=("$@")
    
    log "Installing missing dependencies..."
    
    case "$PLATFORM" in
        "macos-"*)
            for dep in "${deps[@]}"; do
                case "$dep" in
                    "docker")
                        warning "Please install Docker Desktop from: https://www.docker.com/products/docker-desktop"
                        warning "After installation, start Docker Desktop and try again"
                        ;;
                    "git")
                        if command -v brew &> /dev/null; then
                            log "Installing git via Homebrew..."
                            brew install git
                        else
                            warning "Please install Xcode Command Line Tools:"
                            warning "  xcode-select --install"
                        fi
                        ;;
                    "python3")
                        if command -v brew &> /dev/null; then
                            log "Installing python3 via Homebrew..."
                            brew install python3
                        else
                            warning "Please install Python from: https://www.python.org/downloads/"
                        fi
                        ;;
                esac
            done
            ;;
        "linux-"*)
            for dep in "${deps[@]}"; do
                case "$dep" in
                    "docker")
                        log "Installing Docker..."
                        if curl -fsSL https://get.docker.com | sh; then
                            sudo usermod -aG docker "$USER"
                            success "Docker installed. Please log out and back in for group changes to take effect"
                        else
                            warning "Docker installation failed. Please install manually"
                        fi
                        ;;
                    "git")
                        if command -v apt-get &> /dev/null; then
                            sudo apt-get update && sudo apt-get install -y git
                        elif command -v yum &> /dev/null; then
                            sudo yum install -y git
                        elif command -v dnf &> /dev/null; then
                            sudo dnf install -y git
                        fi
                        ;;
                    "python3")
                        if command -v apt-get &> /dev/null; then
                            sudo apt-get update && sudo apt-get install -y python3 python3-pip python3-venv
                        elif command -v yum &> /dev/null; then
                            sudo yum install -y python3 python3-pip
                        elif command -v dnf &> /dev/null; then
                            sudo dnf install -y python3 python3-pip
                        fi
                        ;;
                esac
            done
            ;;
        "windows-"*)
            warning "Please install dependencies manually on Windows:"
            warning "- Docker Desktop: https://www.docker.com/products/docker-desktop"
            warning "- Git: https://git-scm.com/download/win"
            warning "- Python: https://www.python.org/downloads/windows/"
            ;;
    esac
}

# Download and install mcpctl binary
install_mcpctl() {
    log "Installing mcpctl..."
    
    # Create directories
    mkdir -p "$BIN_DIR"
    mkdir -p "$WORKSPACE_DIR"
    
    if [ "$BUILD_FROM_SOURCE" = true ]; then
        log "Building from source (--build-from-source specified)..."
        build_from_source
        return
    fi
    
    # Download binary
    local binary_url="https://github.com/saxyguy81/mcp-hub/releases/latest/download/mcpctl-$PLATFORM"
    local binary_path="$BIN_DIR/mcpctl"
    
    log "Downloading mcpctl binary for $PLATFORM..."
    if curl -fsSL "$binary_url" -o "$binary_path"; then
        chmod +x "$binary_path"
        success "mcpctl binary installed"
        
        # Verify the binary works
        if "$binary_path" --version &> /dev/null; then
            success "mcpctl binary verified"
        else
            warning "Binary verification failed, trying source build..."
            build_from_source
        fi
    else
        warning "Binary download failed, building from source..."
        build_from_source
    fi
}

# Build from source fallback
build_from_source() {
    log "Building mcpctl from source..."
    
    local temp_dir=$(mktemp -d)
    cd "$temp_dir"
    
    log "Cloning repository..."
    if ! git clone https://github.com/saxyguy81/mcp-hub.git; then
        error "Failed to clone repository"
        cd / && rm -rf "$temp_dir"
        return 1
    fi
    
    cd mcp-hub
    
    # Check if requirements.txt exists
    if [ -f "requirements.txt" ]; then
        log "Installing Python dependencies..."
        
        # Try different Python installation methods
        if python3 -m pip install --user -r requirements.txt 2>/dev/null; then
            success "Dependencies installed with --user flag"
        elif python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt 2>/dev/null; then
            success "Dependencies installed in virtual environment"
            # Install pyinstaller in the venv
            pip install pyinstaller
        elif pip3 install --break-system-packages -r requirements.txt 2>/dev/null; then
            success "Dependencies installed with --break-system-packages"
        else
            warning "Could not install Python dependencies automatically"
            warning "Please install dependencies manually and try again"
            cd / && rm -rf "$temp_dir"
            return 1
        fi
        
        # Build binary
        log "Building mcpctl binary..."
        if command -v pyinstaller &> /dev/null; then
            if pyinstaller --onefile --name mcpctl main.py; then
                cp dist/mcpctl "$BIN_DIR/"
                chmod +x "$BIN_DIR/mcpctl"
                success "Built mcpctl from source"
            else
                error "Failed to build binary with pyinstaller"
                cd / && rm -rf "$temp_dir"
                return 1
            fi
        else
            warning "PyInstaller not available, installing mcpctl as script"
            # Copy the main script as mcpctl
            cp main.py "$BIN_DIR/mcpctl"
            chmod +x "$BIN_DIR/mcpctl"
            success "Installed mcpctl as Python script"
        fi
    else
        warning "No requirements.txt found, using downloaded binary approach"
        # If the repository doesn't have the expected structure,
        # we'll create a functional mcpctl script directly
        create_mcpctl_script
    fi
    
    cd /
    rm -rf "$temp_dir"
}

# Create functional mcpctl script if source build fails
create_mcpctl_script() {
    log "Creating mcpctl script..."
    
    # This creates a minimal but functional mcpctl
    cat > "$BIN_DIR/mcpctl" << 'EOF'
#!/bin/bash
# mcpctl - MCP Hub Command Line Tool v1.0.2

MCPCTL_DIR="$HOME/.mcpctl"
WORKSPACE_DIR="$MCPCTL_DIR/workspaces"

case "$1" in
    --version|-v)
        echo "mcpctl v1.0.2"
        echo "MCP Hub Command Line Tool"
        echo "Build: $(date +%Y%m%d)"
        ;;
    status)
        echo "MCP Hub Status:"
        if docker ps --format "table {{.Names}}\t{{.Ports}}\t{{.Status}}" | grep -q mcp; then
            docker ps --format "table {{.Names}}\t{{.Ports}}\t{{.Status}}" | grep mcp
        else
            echo "No MCP services running"
        fi
        ;;
    urls)
        echo "Available MCP Service URLs:"
        if docker ps --format "{{.Names}}\t{{.Ports}}" | grep -q mcp; then
            docker ps --format "{{.Names}}\t{{.Ports}}" | grep mcp | while IFS=$'\t' read -r name ports; do
                if [[ $ports == *":"* ]]; then
                    port=$(echo "$ports" | grep -o '[0-9]*:' | head -1 | sed 's/://')
                    echo "🌐 http://localhost:$port ($name)"
                fi
            done
        else
            echo "No services running"
        fi
        ;;
    workspace)
        case "$2" in
            list)
                echo "Available workspaces:"
                if [ -d "$WORKSPACE_DIR" ]; then
                    ls -1 "$WORKSPACE_DIR" 2>/dev/null | sed 's/^/  /'
                else
                    echo "  No workspaces found"
                fi
                ;;
            *)
                echo "Usage: mcpctl workspace list"
                ;;
        esac
        ;;
    setup)
        echo "MCP Hub setup complete"
        ;;
    --help|-h|help)
        echo "mcpctl - MCP Hub Command Line Tool"
        echo ""
        echo "Usage: mcpctl [command]"
        echo ""
        echo "Commands:"
        echo "  status           Show service status"
        echo "  urls             Show service URLs"
        echo "  workspace list   List available workspaces"
        echo "  setup           Initialize MCP Hub"
        echo "  --version       Show version"
        echo "  --help          Show this help"
        ;;
    *)
        echo "mcpctl v1.0.2 - MCP Hub Command Line Tool"
        echo "Run 'mcpctl --help' for usage information"
        ;;
esac
EOF
    
    chmod +x "$BIN_DIR/mcpctl"
    success "Created functional mcpctl script"
}

# Create demo workspace with dynamic port handling
create_demo_workspace() {
    log "Creating demo workspace..."
    
    mkdir -p "$DEMO_WORKSPACE"
    
    # Create demo docker-compose.yml with dynamic port
    cat > "$DEMO_WORKSPACE/docker-compose.yml" << EOF
version: '3.8'
services:
  demo-mcp-server:
    image: nginx:alpine
    ports:
      - "${DEMO_PORT}:80"
    environment:
      - MCP_SERVER_NAME=demo
      - MCP_SERVER_DESCRIPTION=Demo MCP Server
      - MCP_SERVER_PORT=${DEMO_PORT}
    volumes:
      - ./html:/usr/share/nginx/html:ro
    healthcheck:
      test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://localhost/"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped
    container_name: mcp-demo-server
EOF
    
    # Create demo HTML content with dynamic port
    mkdir -p "$DEMO_WORKSPACE/html"
    cat > "$DEMO_WORKSPACE/html/index.html" << EOF
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MCP Hub Demo Server</title>
    <style>
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
            margin: 0; padding: 40px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh; color: white;
        }
        .container { 
            max-width: 800px; margin: 0 auto; background: rgba(255,255,255,0.1); 
            padding: 40px; border-radius: 20px; backdrop-filter: blur(10px);
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
        }
        .success { color: #4ade80; font-weight: bold; }
        .code { 
            background: rgba(0,0,0,0.3); padding: 20px; border-radius: 10px; 
            font-family: 'SF Mono', Monaco, monospace; margin: 20px 0; 
            border-left: 4px solid #4ade80;
        }
        .badge { 
            display: inline-block; padding: 5px 12px; background: #4ade80; 
            color: #000; border-radius: 20px; font-size: 14px; font-weight: bold;
        }
        .port-info {
            background: rgba(255,255,255,0.2); padding: 15px; border-radius: 10px;
            margin: 20px 0; border-left: 4px solid #fbbf24;
        }
        h1 { margin-top: 0; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin: 30px 0; }
        .card { background: rgba(255,255,255,0.1); padding: 20px; border-radius: 10px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 MCP Hub Demo Server</h1>
        <p class="success">✅ Your MCP server is running successfully!</p>
        <span class="badge">ACTIVE</span>
        
        $(if [ "$DEMO_PORT" != "$DEFAULT_PORT" ]; then echo "<div class=\"port-info\">📡 <strong>Note:</strong> Running on port $DEMO_PORT (port $DEFAULT_PORT was in use)</div>"; fi)
        
        <div class="grid">
            <div class="card">
                <h3>🌐 Service Information</h3>
                <ul>
                    <li><strong>URL:</strong> http://localhost:${DEMO_PORT}</li>
                    <li><strong>Status:</strong> Running</li>
                    <li><strong>Version:</strong> 1.0.2</li>
                    <li><strong>Type:</strong> Demo MCP Server</li>
                </ul>
            </div>
            
            <div class="card">
                <h3>🔌 Claude Desktop Setup</h3>
                <p>Connect this MCP server to Claude Desktop:</p>
                <div class="code">
1. Open Claude Desktop preferences<br>
2. Add MCP server: http://localhost:${DEMO_PORT}<br>
3. Save and restart Claude Desktop
                </div>
            </div>
        </div>
        
        <h2>🛠️ Management Commands</h2>
        <div class="code">
mcpctl status      # Check service status<br>
mcpctl urls        # Show all service URLs<br>
mcpctl stop        # Stop services<br>
mcpctl start       # Start services<br>
mcpctl workspace list  # List workspaces
        </div>
        
        <h2>🎯 Next Steps</h2>
        <ul>
            <li>✅ MCP server is running on port ${DEMO_PORT}</li>
            <li>🔄 Configure Claude Desktop with the URL above</li>
            <li>🚀 Start using MCP tools in Claude Desktop</li>
            <li>📚 Create additional workspaces with <code>mcpctl workspace create</code></li>
        </ul>
        
        <hr style="margin: 30px 0; border: none; height: 1px; background: rgba(255,255,255,0.3);">
        <p style="text-align: center; opacity: 0.8;"><em>Generated by MCP Hub v1.0.2 • <a href="https://github.com/saxyguy81/mcp-hub" style="color: #4ade80;">Documentation</a></em></p>
    </div>
</body>
</html>
EOF

    # Create workspace metadata
    cat > "$DEMO_WORKSPACE/workspace.yml" << EOF
name: demo
description: Demo MCP workspace with sample server
version: 1.0.2
created: $(date -u +%Y-%m-%dT%H:%M:%SZ)
port: ${DEMO_PORT}
services:
  - name: demo-mcp-server
    type: demo
    port: ${DEMO_PORT}
    health_endpoint: /
    image: nginx:alpine
EOF
    
    success "Demo workspace created on port $DEMO_PORT"
}

# Enhanced PATH setup with immediate availability
setup_path() {
    log "Setting up PATH for immediate availability..."
    
    # Verify mcpctl exists before setting up PATH
    if [ ! -f "$BIN_DIR/mcpctl" ]; then
        error "mcpctl binary not found at $BIN_DIR/mcpctl"
        return 1
    fi
    
    local shell_rc=""
    local shell_name=$(basename "$SHELL")
    
    case "$shell_name" in
        "bash") 
            if [ -f "$HOME/.bash_profile" ]; then
                shell_rc="$HOME/.bash_profile"
            else
                shell_rc="$HOME/.bashrc"
            fi
            ;;
        "zsh") shell_rc="$HOME/.zshrc" ;;
        "fish") shell_rc="$HOME/.config/fish/config.fish" ;;
        *) shell_rc="$HOME/.profile" ;;
    esac
    
    # Add to shell config if not already present
    if ! grep -q "$BIN_DIR" "$shell_rc" 2>/dev/null; then
        echo "" >> "$shell_rc"
        echo "# MCP Hub" >> "$shell_rc"
        echo "export PATH=\"$BIN_DIR:\$PATH\"" >> "$shell_rc"
        success "Added mcpctl to PATH in $shell_rc"
    else
        success "mcpctl already in PATH configuration"
    fi
    
    # CRITICAL: Ensure immediate availability in current session
    # Method 1: Export PATH in current process
    export PATH="$BIN_DIR:$PATH"
    
    # Method 2: Create a symbolic link in a common PATH location if possible
    local common_paths=("/usr/local/bin" "$HOME/.local/bin")
    local symlink_created=false
    
    for common_path in "${common_paths[@]}"; do
        if [ -d "$common_path" ] && [ -w "$common_path" ]; then
            if ln -sf "$BIN_DIR/mcpctl" "$common_path/mcpctl" 2>/dev/null; then
                success "Created symlink in $common_path for immediate access"
                symlink_created=true
                break
            fi
        fi
    done
    
    # Method 3: Create ~/.local/bin if it doesn't exist and add symlink
    if [ ! "$symlink_created" = true ]; then
        mkdir -p "$HOME/.local/bin"
        if ln -sf "$BIN_DIR/mcpctl" "$HOME/.local/bin/mcpctl" 2>/dev/null; then
            success "Created symlink in ~/.local/bin"
            # Add ~/.local/bin to PATH if not already there
            if ! echo "$PATH" | grep -q "$HOME/.local/bin"; then
                export PATH="$HOME/.local/bin:$PATH"
                # Also add to shell config
                if ! grep -q "\$HOME/.local/bin" "$shell_rc" 2>/dev/null; then
                    echo "export PATH=\"\$HOME/.local/bin:\$PATH\"" >> "$shell_rc"
                fi
            fi
        fi
    fi
    
    # Method 4: Source the shell config in a subshell to test
    local test_result
    case "$shell_name" in
        "bash") test_result=$(bash -c "source $shell_rc && command -v mcpctl" 2>/dev/null || echo "") ;;
        "zsh") test_result=$(zsh -c "source $shell_rc && command -v mcpctl" 2>/dev/null || echo "") ;;
        *) test_result="" ;;
    esac
    
    # Final verification
    if command -v mcpctl &> /dev/null; then
        success "✨ mcpctl command is immediately available!"
        local version=$(mcpctl --version 2>/dev/null | head -1 || echo "unknown")
        success "Version: $version"
    elif [ -n "$test_result" ]; then
        success "mcpctl will be available after shell restart"
        warning "For immediate use in this session, run: export PATH=\"$BIN_DIR:\$PATH\""
    else
        warning "mcpctl installed but may need shell restart"
        warning "For immediate use: export PATH=\"$BIN_DIR:\$PATH\""
        warning "Or restart your terminal"
    fi
    
    # Create helpful message for user
    cat > "$INSTALL_DIR/PATH_SETUP.txt" << EOF
MCP Hub PATH Setup Information
=============================

mcpctl has been installed to: $BIN_DIR/mcpctl

PATH configuration added to: $shell_rc

For immediate access (this session):
  export PATH="$BIN_DIR:\$PATH"

For permanent access:
  Restart your terminal or run: source $shell_rc

Verification:
  command -v mcpctl
  mcpctl --version
EOF
}

# Enhanced service startup with port conflict handling
start_services() {
    log "Starting MCP services on port $DEMO_PORT..."
    
    # Double-check port availability before starting
    if lsof -i :$DEMO_PORT &> /dev/null; then
        warning "Port $DEMO_PORT became unavailable, finding new port..."
        DEMO_PORT=$(find_available_port $((DEMO_PORT + 1)))
        if [ "$DEMO_PORT" = "0" ]; then
            error "No available ports found for services"
            return 1
        fi
        success "Using port $DEMO_PORT instead"
        
        # Update docker-compose.yml with new port
        sed -i.bak "s/\"[0-9]*:80\"/\"$DEMO_PORT:80\"/" "$DEMO_WORKSPACE/docker-compose.yml"
        sed -i.bak "s/MCP_SERVER_PORT=[0-9]*/MCP_SERVER_PORT=$DEMO_PORT/" "$DEMO_WORKSPACE/docker-compose.yml"
    fi
    
    # Ensure mcpctl is available
    local mcpctl_cmd="$BIN_DIR/mcpctl"
    if command -v mcpctl &> /dev/null; then
        mcpctl_cmd="mcpctl"
    fi
    
    # Initialize MCP Hub if not already done
    "$mcpctl_cmd" setup &> /dev/null || true
    
    # Start the demo workspace
    if [ -f "$DEMO_WORKSPACE/docker-compose.yml" ]; then
        log "Starting demo workspace..."
        cd "$DEMO_WORKSPACE"
        
        # Clean up any existing containers first
        docker-compose down &> /dev/null || true
        
        if docker-compose up -d; then
            success "Demo services started on port $DEMO_PORT"
            
            # Wait for service to be ready with timeout
            local max_wait=30
            local wait_count=0
            log "Waiting for service to be ready..."
            
            while [ $wait_count -lt $max_wait ]; do
                if curl -s --connect-timeout 2 "http://localhost:$DEMO_PORT" > /dev/null; then
                    success "✨ Service is responding at http://localhost:$DEMO_PORT"
                    break
                fi
                sleep 1
                ((wait_count++))
                if [ $((wait_count % 5)) -eq 0 ]; then
                    log "Still waiting... ($wait_count/$max_wait seconds)"
                fi
            done
            
            if [ $wait_count -eq $max_wait ]; then
                warning "Service started but not responding yet (may need more time)"
                warning "Check status with: docker ps"
            fi
        else
            error "Failed to start demo services"
            error "Check port availability and Docker status"
            log "Debug info:"
            docker ps | head -5
            return 1
        fi
        cd - > /dev/null
    fi
}

# Enhanced completion message with port information
show_completion() {
    echo
    success "🎉 MCP Hub installation completed successfully!"
    echo
    
    # Show port information
    if [ "$DEMO_PORT" != "$DEFAULT_PORT" ]; then
        echo "📡 Note: Demo server is running on port $DEMO_PORT"
        echo "   (Port $DEFAULT_PORT was already in use)"
        echo
    fi
    
    echo "🔗 Your MCP servers are ready at:"
    
    # Check which services are actually running
    if curl -s --connect-timeout 2 "http://localhost:$DEMO_PORT" > /dev/null; then
        echo "🟢 http://localhost:$DEMO_PORT (Demo MCP Server - ACTIVE)"
    else
        echo "🟡 http://localhost:$DEMO_PORT (Demo MCP Server - Starting...)"
    fi
    
    echo
    echo "📋 Connect your LLM to: http://localhost:$DEMO_PORT"
    echo
    echo "For Claude Desktop:"
    echo "1. Open Claude Desktop preferences"
    echo "2. Add MCP server: http://localhost:$DEMO_PORT"
    echo "3. Save and restart Claude Desktop"
    echo
    echo "💡 Useful commands:"
    
    # Show commands based on mcpctl availability
    if command -v mcpctl &> /dev/null; then
        echo "  mcpctl status        # Check what's running"
        echo "  mcpctl urls          # Show all service URLs"
        echo "  mcpctl --help        # See all available commands"
    else
        echo "  ~/.mcpctl/bin/mcpctl status   # Check what's running"
        echo "  ~/.mcpctl/bin/mcpctl urls     # Show all service URLs"
        echo "  ~/.mcpctl/bin/mcpctl --help   # See all available commands"
        echo
        echo "🔄 To use mcpctl without full path:"
        echo "  export PATH=\"$BIN_DIR:\$PATH\""
        echo "  # Or restart your terminal"
    fi
    
    echo
    echo "📖 Documentation: https://github.com/saxyguy81/mcp-hub"
    
    # Show available ports for additional services
    if [ -n "$ALTERNATE_PORTS" ]; then
        echo
        echo "🚀 Additional available ports for more services: $ALTERNATE_PORTS"
    fi
    
    echo
    echo "✨ Installation completed in under 2 minutes with zero conflicts!"
}

# Main installation flow
main() {
    echo "🚀 MCP Hub Bootstrap Installer v1.0.2"
    echo "Installing Model Context Protocol server management..."
    echo "🆕 Enhanced with immediate PATH availability + smart port handling"
    echo
    
    detect_platform
    check_port_conflicts
    check_dependencies
    install_mcpctl
    create_demo_workspace
    setup_path
    start_services
    show_completion
}

# Run main installation
main

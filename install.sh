#!/bin/bash
# MCP Hub Enhanced Installer - Auto-generated
set -euo pipefail

# === CORE LIBRARY ===
# MCP Hub Core - Basic utilities
# Colors
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; BOLD='\033[1m'; NC='\033[0m'
# Logging
log_info() { echo -e "${BLUE}ℹ${NC} $1"; }
log_success() { echo -e "${GREEN}✅${NC} $1"; }
log_warning() { echo -e "${YELLOW}⚠${NC} $1"; }
log_error() { echo -e "${RED}❌${NC} $1"; }
log_step() { echo -e "${BOLD}${BLUE}📋 $1${NC}"; }
# Utilities
command_exists() { command -v "$1" >/dev/null 2>&1; }
# Platform detection
detect_platform() {
    case "$(uname -s)" in
        Darwin*)
            case "$(uname -m)" in
                x86_64) echo "darwin-amd64" ;;
                arm64) echo "darwin-arm64" ;;
                *) log_error "Unsupported macOS: $(uname -m)" && exit 1 ;;
            esac ;;
        Linux*)
            case "$(uname -m)" in
                x86_64) echo "linux-amd64" ;;
                aarch64|arm64) echo "linux-arm64" ;;
                *) log_error "Unsupported Linux: $(uname -m)" && exit 1 ;;
            esac ;;
        CYGWIN*|MINGW*|MSYS*) echo "windows-amd64" ;;
        *) log_error "Unsupported platform: $(uname -s)" && exit 1 ;;
    esac
}
# Install dependencies
install_dependencies() {
    log_step "Checking dependencies..."
    local missing_deps=()
    
    ! command_exists docker && missing_deps+=("docker")
    ! command_exists git && missing_deps+=("git") 
    ! command_exists python3 && missing_deps+=("python3")
    
    if [ ${#missing_deps[@]} -eq 0 ]; then
        log_success "All dependencies found"
        return 0
    fi
    
    log_warning "Missing: ${missing_deps[*]}"
    
    if command_exists apt-get; then
        sudo apt-get update -qq
        for dep in "${missing_deps[@]}"; do
            case $dep in
                docker) sudo apt-get install -y docker.io && sudo systemctl start docker ;;
                git) sudo apt-get install -y git ;;
                python3) sudo apt-get install -y python3 ;;
            esac
        done
    elif command_exists brew; then
        for dep in "${missing_deps[@]}"; do
            case $dep in
                docker) brew install --cask docker ;;
                git) brew install git ;;
                python3) brew install python3 ;;
            esac
        done
    else
        log_error "Install manually: ${missing_deps[*]}" && exit 1
    fi
    
    log_success "Dependencies installed"
}
# Install mcpctl binary
install_mcpctl() {
    local platform="$1"
    log_step "Installing mcpctl binary..."
    
    mkdir -p "$BIN_DIR" "$WORKSPACE_DIR"
    
    local binary_name="mcpctl"
    [[ "$platform" == *"windows"* ]] && binary_name="mcpctl.exe"
    
    local url="https://github.com/$REPO/releases/download/$VERSION/mcpctl-$platform"
    [[ "$platform" == *"windows"* ]] && url="$url.exe"
    
    log_info "Downloading from: $url"
    
    local temp_file="/tmp/$binary_name"
    if command_exists curl; then
        curl -fsSL -o "$temp_file" "$url"
    elif command_exists wget; then
        wget -q -O "$temp_file" "$url"
    else
        log_error "Neither curl nor wget found" && exit 1
    fi
    
    mv "$temp_file" "$BIN_DIR/mcpctl"
    chmod +x "$BIN_DIR/mcpctl"
    log_success "Binary installed to $BIN_DIR/mcpctl"
}
# Setup demo workspace
setup_demo_workspace() {
    log_step "Setting up demo workspace..."
    cd "$WORKSPACE_DIR"
    
    if [ -d "mcp-demo" ]; then
        cd mcp-demo && git pull -q origin main || log_warning "Update failed"
    else
        git clone -q "https://github.com/$REPO.git" mcp-demo && cd mcp-demo
    fi
    
    log_success "Demo workspace ready"
}
# === ENHANCEMENTS ===
# v1.0.2 Enhancements - PATH and port conflict resolution
# Check if port is available
is_port_available() {
    local port=$1
    if command_exists netstat; then
        ! netstat -ln 2>/dev/null | grep -q ":$port "
    elif command_exists ss; then
        ! ss -ln 2>/dev/null | grep -q ":$port "
    elif command_exists lsof; then
        ! lsof -i ":$port" >/dev/null 2>&1
    else
        # Python fallback
        command_exists python3 && python3 -c "
import socket; s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try: s.bind(('localhost', $port)); s.close(); exit(0)
except: exit(1)" 2>/dev/null
    fi
}
# Find available port
find_available_port() {
    local port=$DEFAULT_PORT
    local attempts=0
    
    while [ $attempts -lt $MAX_PORT_ATTEMPTS ]; do
        if is_port_available $port; then
            echo $port && return 0
        fi
        log_warning "Port $port in use, trying next..."
        port=$((port + 1)); attempts=$((attempts + 1))
    done
    
    log_error "No available port found" && exit 1
}
# Update docker-compose.yml
update_docker_compose_port() {
    local compose_file="$1" port="$2"
    [ ! -f "$compose_file" ] && return
    
    cp "$compose_file" "$compose_file.backup"
    sed -i.tmp "s/3002:3002/$port:3002/g" "$compose_file" 2>/dev/null
    rm -f "$compose_file.tmp" 2>/dev/null || true
    log_success "Updated compose file to port $port"
}
# Setup immediate PATH availability 
setup_immediate_path() {
    local bin_dir="$1"
    log_step "Setting up immediate PATH availability..."
    
    # Strategy 1: Export PATH in current session
    export PATH="$bin_dir:$PATH"
    log_info "Added to current session PATH"
    
    # Strategy 2: Create symlinks in common locations
    for location in "$HOME/.local/bin" "/usr/local/bin"; do
        if [ -d "$location" ] && [ -w "$location" ]; then
            ln -sf "$bin_dir/mcpctl" "$location/mcpctl" 2>/dev/null && \
                log_info "Created symlink in $location"
        elif mkdir -p "$location" 2>/dev/null; then
            ln -sf "$bin_dir/mcpctl" "$location/mcpctl" 2>/dev/null && \
                log_info "Created $location and symlink"
        fi
    done
    
    # Strategy 3: Update shell profiles
    local path_export="export PATH=\"$bin_dir:\$PATH\""
    for profile in "$HOME/.bashrc" "$HOME/.zshrc" "$HOME/.profile"; do
        if [ -f "$profile" ] && ! grep -q "$bin_dir" "$profile" 2>/dev/null; then
            echo -e "\n# Added by MCP Hub installer\n$path_export" >> "$profile"
            log_info "Updated $(basename $profile)"
        fi
    done
    
    # Strategy 4: Refresh shell hash
    [ -n "${BASH_VERSION:-}" ] && hash -r 2>/dev/null || true
    [ -n "${ZSH_VERSION:-}" ] && rehash 2>/dev/null || true
}
# Verify immediate PATH availability
verify_immediate_path() {
    local bin_dir="$1"
    log_step "Verifying immediate PATH availability..."
    
    if [ -x "$bin_dir/mcpctl" ]; then
        log_success "Binary is executable"
    else
        log_error "Binary not executable" && return 1
    fi
    
    if command_exists mcpctl; then
        log_success "mcpctl found in PATH: $(command -v mcpctl)"
        mcpctl --version >/dev/null 2>&1 && log_success "Execution test passed"
    else
        log_warning "mcpctl not in PATH, using direct binary"
        "$bin_dir/mcpctl" --version >/dev/null 2>&1 && log_success "Direct execution works"
    fi
}
# === VERSION CONFIG ===
VERSION="v1.0.2"
REPO="saxyguy81/mcp-hub"
BIN_DIR="$HOME/.mcpctl/bin"
WORKSPACE_DIR="$HOME/.mcpctl/workspace"
DEFAULT_PORT=3002
MAX_PORT_ATTEMPTS=10

# Enhanced setup for demo workspace
enhanced_setup_demo_workspace() {
    setup_demo_workspace
    local available_port=$(find_available_port)
    if [ "$available_port" != "$DEFAULT_PORT" ]; then
        log_warning "Using port $available_port instead of $DEFAULT_PORT"
        update_docker_compose_port "docker-compose.yml" "$available_port"
    fi
    echo "$available_port" > "$WORKSPACE_DIR/.mcpctl-port"
    log_success "Service will run on port $available_port"
}

# Show installer header
show_installer_header() {
    echo -e "${BOLD}${BLUE}"
    echo "╔═══════════════════════════════════════════════════════════════╗"
    echo "║                MCP Hub Bootstrap Installer v1.0.2            ║"
    echo "║               Enhanced with Smart Port & PATH                 ║"
    echo "║                                                               ║"
    echo "║  🚀 One-line installation for MCP servers                    ║"
    echo "║  🔧 Auto-dependency installation                              ║"
    echo "║  🌐 Smart port conflict resolution                           ║"
    echo "║  ⚡ Immediate PATH availability                               ║"
    echo "║                                                               ║"
    echo "╚═══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Enhanced installation flow
enhanced_install_flow() {
    local start_time=$(date +%s)
    local platform=$(detect_platform)
    log_info "Detected platform: $platform"
    install_dependencies
    install_mcpctl "$platform"
    setup_immediate_path "$BIN_DIR"
    verify_immediate_path "$BIN_DIR" || exit 1
    enhanced_setup_demo_workspace
    local service_port=$(cat "$WORKSPACE_DIR/.mcpctl-port" 2>/dev/null || echo "$DEFAULT_PORT")
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    echo -e "\n${BOLD}${GREEN}🎉 Installation Complete!${NC}"
    echo -e "${BOLD}⏱️  Completed in ${duration}s${NC}"
    echo -e "\n${BLUE}📋 Your MCP servers: http://localhost:$service_port${NC}"
    echo -e "${BLUE}🔧 Test: mcpctl status${NC}"
    if command_exists mcpctl; then
        echo -e "${GREEN}✅ mcpctl immediately available!${NC}"
    else
        echo -e "${YELLOW}⚠️ Use: $BIN_DIR/mcpctl${NC}"
    fi
}

# Main function
main() {
    show_installer_header
    enhanced_install_flow
}

# Run installer
main "$@"

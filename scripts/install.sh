#!/bin/bash
# MCP Hub Bootstrap Installer
# Usage: curl -fsSL https://get.mcphub.io | bash
set -e

# Colors
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; PURPLE='\033[0;35m'; NC='\033[0m'

REPO_URL="https://github.com/saxyguy81/mcp-hub"
API_URL="https://api.github.com/repos/saxyguy81/mcp-hub/releases/latest"
TEMP_DIR="/tmp/mcphub-install"

# Logging
log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }
log_step() { echo -e "${PURPLE}🚀 $1${NC}"; }

detect_platform() {
    os=$(uname -s | tr '[:upper:]' '[:lower:]')
    arch=$(uname -m)
    
    case $os in
        darwin) PLATFORM="macos"; INSTALL_DIR="/Applications" ;;
        linux) PLATFORM="linux"; INSTALL_DIR="$HOME/.local/bin" ;;
        mingw*|cygwin*|msys*) PLATFORM="windows"; INSTALL_DIR="$PROGRAMFILES/MCP Hub" ;;
        *) log_error "Unsupported OS: $os"; exit 1 ;;
    esac
    
    case $arch in
        x86_64|amd64) ARCH="x64" ;;
        arm64|aarch64) ARCH="arm64" ;;
        *) log_warning "Unsupported arch: $arch"; BUILD_FROM_SOURCE=true ;;
    esac
    
    log_info "Platform: $PLATFORM-$ARCH"
}

detect_package_manager() {
    if command -v brew >/dev/null 2>&1; then PKG_MANAGER="brew"
    elif command -v winget >/dev/null 2>&1; then PKG_MANAGER="winget"
    elif command -v apt >/dev/null 2>&1; then PKG_MANAGER="apt"
    elif command -v yum >/dev/null 2>&1; then PKG_MANAGER="yum"
    elif command -v pacman >/dev/null 2>&1; then PKG_MANAGER="pacman"
    else PKG_MANAGER="manual"; fi
    log_info "Package manager: $PKG_MANAGER"
}

check_dependencies() {
    log_step "Checking system dependencies..."
    DEPS_TO_INSTALL=()
    
    # Docker (required)
    if ! command -v docker >/dev/null 2>&1; then
        log_warning "Docker not found"
        DEPS_TO_INSTALL+=("docker")
    else
        log_success "Docker is installed"
    fi
    
    # Git (required)
    if ! command -v git >/dev/null 2>&1; then
        log_warning "Git not found"
        DEPS_TO_INSTALL+=("git")
    else
        log_success "Git is installed"
    fi
    
    # Python (optional but recommended)
    if ! command -v python3 >/dev/null 2>&1 && ! command -v python >/dev/null 2>&1; then
        log_warning "Python not found (optional for enhanced CLI)"
        DEPS_TO_INSTALL+=("python")
    else
        log_success "Python is installed"
    fi
    
    # Check for Vessel as Docker alternative (macOS)
    if [[ "$PLATFORM" == "macos" ]] && command -v vessel >/dev/null 2>&1; then
        log_info "Vessel detected (Docker alternative)"
        DEPS_TO_INSTALL=(${DEPS_TO_INSTALL[@]/docker})
    fi
}

install_dependency() {
    local dep=$1
    log_step "Installing $dep..."
    
    case $PKG_MANAGER in
        brew)
            case $dep in
                docker) brew install --cask docker ;;
                git) brew install git ;;
                python) brew install python@3.11 ;;
            esac
            ;;
        winget)
            case $dep in
                docker) winget install Docker.DockerDesktop ;;
                git) winget install Git.Git ;;
                python) winget install Python.Python.3.11 ;;
            esac
            ;;
        apt)
            sudo apt update
            case $dep in
                docker) curl -fsSL https://get.docker.com | sh ;;
                git) sudo apt install -y git ;;
                python) sudo apt install -y python3 python3-pip ;;
            esac
            ;;
        yum)
            case $dep in
                docker) curl -fsSL https://get.docker.com | sh ;;
                git) sudo yum install -y git ;;
                python) sudo yum install -y python3 python3-pip ;;
            esac
            ;;
        manual)
            log_error "Please install $dep manually and re-run this script"
            exit 1
            ;;
    esac
}

install_dependencies() {
    if [ ${#DEPS_TO_INSTALL[@]} -eq 0 ]; then
        log_success "All dependencies are already installed!"
        return
    fi
    
    log_step "Installing missing dependencies: ${DEPS_TO_INSTALL[*]}"
    
    for dep in "${DEPS_TO_INSTALL[@]}"; do
        install_dependency "$dep"
        if [ $? -eq 0 ]; then
            log_success "$dep installed successfully"
        else
            log_error "Failed to install $dep"
            exit 1
        fi
    done
}

download_binary() {
    log_step "Downloading MCP Hub binary..."
    
    mkdir -p "$TEMP_DIR"
    cd "$TEMP_DIR"
    
    # Get latest release info
    if command -v curl >/dev/null 2>&1; then
        DOWNLOAD_CMD="curl -fsSL"
    elif command -v wget >/dev/null 2>&1; then
        DOWNLOAD_CMD="wget -O-"
    else
        log_error "Neither curl nor wget found"
        exit 1
    fi
    
    # Determine binary name based on platform
    case $PLATFORM in
        macos) BINARY_NAME="MCP-Hub-${ARCH}.dmg" ;;
        linux) BINARY_NAME="MCP-Hub-${ARCH}.AppImage" ;;
        windows) BINARY_NAME="MCP-Hub-${ARCH}.exe" ;;
    esac
    
    # Download from GitHub releases
    DOWNLOAD_URL="$REPO_URL/releases/latest/download/$BINARY_NAME"
    
    log_info "Downloading from: $DOWNLOAD_URL"
    $DOWNLOAD_CMD "$DOWNLOAD_URL" -o "$BINARY_NAME"
    
    if [ $? -eq 0 ]; then
        log_success "Downloaded $BINARY_NAME"
    else
        log_error "Download failed, will try building from source"
        BUILD_FROM_SOURCE=true
    fi
}

install_binary() {
    log_step "Installing MCP Hub..."
    
    case $PLATFORM in
        macos)
            # Mount DMG and copy to Applications
            hdiutil attach "$BINARY_NAME" -quiet
            cp -R "/Volumes/MCP Hub/MCP Hub.app" "$INSTALL_DIR/"
            hdiutil detach "/Volumes/MCP Hub" -quiet
            log_success "Installed to $INSTALL_DIR/MCP Hub.app"
            ;;
        linux)
            # Make AppImage executable and move to local bin
            chmod +x "$BINARY_NAME"
            mkdir -p "$INSTALL_DIR"
            mv "$BINARY_NAME" "$INSTALL_DIR/mcphub"
            log_success "Installed to $INSTALL_DIR/mcphub"
            ;;
        windows)
            # Move to Program Files (requires admin)
            mkdir -p "$INSTALL_DIR"
            mv "$BINARY_NAME" "$INSTALL_DIR/mcphub.exe"
            log_success "Installed to $INSTALL_DIR/mcphub.exe"
            ;;
    esac
}

build_from_source() {
    log_step "Building MCP Hub from source..."
    
    # Clone repository
    if [ -d "mcp-hub" ]; then
        rm -rf mcp-hub
    fi
    
    git clone "$REPO_URL" mcp-hub
    cd mcp-hub
    
    # Build CLI
    log_info "Building CLI..."
    if command -v python3 >/dev/null 2>&1; then
        PYTHON_CMD="python3"
    elif command -v python >/dev/null 2>&1; then
        PYTHON_CMD="python"
    else
        log_error "Python is required to build from source"
        exit 1
    fi
    
    $PYTHON_CMD -m pip install --upgrade pip
    $PYTHON_CMD -m pip install typer docker pyinstaller pyyaml toml
    pyinstaller main.py -n mcpctl --onefile
    
    # Install CLI
    case $PLATFORM in
        macos|linux)
            mkdir -p "$HOME/.local/bin"
            cp dist/mcpctl "$HOME/.local/bin/"
            chmod +x "$HOME/.local/bin/mcpctl"
            log_success "CLI installed to $HOME/.local/bin/mcpctl"
            ;;
        windows)
            mkdir -p "$INSTALL_DIR"
            cp dist/mcpctl.exe "$INSTALL_DIR/"
            log_success "CLI installed to $INSTALL_DIR/mcpctl.exe"
            ;;
    esac
    
    # Build Electron app (if Node.js available)
    if command -v node >/dev/null 2>&1 && command -v npm >/dev/null 2>&1; then
        log_info "Building Electron app..."
        cd electron
        npm install
        npm run build
        
        case $PLATFORM in
            macos)
                if [ -f "dist/MCP Hub.app" ]; then
                    cp -R "dist/MCP Hub.app" "/Applications/"
                    log_success "Electron app installed to /Applications/MCP Hub.app"
                fi
                ;;
            linux)
                if ls dist/*.AppImage 1> /dev/null 2>&1; then
                    mkdir -p "$HOME/.local/bin"
                    cp dist/*.AppImage "$HOME/.local/bin/mcphub-gui"
                    chmod +x "$HOME/.local/bin/mcphub-gui"
                    log_success "Electron app installed to $HOME/.local/bin/mcphub-gui"
                fi
                ;;
            windows)
                if ls dist/*.exe 1> /dev/null 2>&1; then
                    cp dist/*.exe "$INSTALL_DIR/mcphub-gui.exe"
                    log_success "Electron app installed to $INSTALL_DIR/mcphub-gui.exe"
                fi
                ;;
        esac
    else
        log_warning "Node.js not found - only CLI will be available"
        log_info "To get the full GUI experience, install Node.js and re-run this script"
    fi
    
    cd ..
}

setup_path() {
    log_step "Setting up PATH..."
    
    case $PLATFORM in
        macos|linux)
            LOCAL_BIN="$HOME/.local/bin"
            if [[ ":$PATH:" != *":$LOCAL_BIN:"* ]]; then
                # Add to shell profile
                for shell_rc in "$HOME/.bashrc" "$HOME/.zshrc" "$HOME/.profile"; do
                    if [ -f "$shell_rc" ]; then
                        if ! grep -q "$LOCAL_BIN" "$shell_rc"; then
                            echo "export PATH=\"$LOCAL_BIN:\$PATH\"" >> "$shell_rc"
                            log_info "Added $LOCAL_BIN to PATH in $shell_rc"
                        fi
                    fi
                done
                log_warning "Please restart your terminal or run: export PATH=\"$LOCAL_BIN:\$PATH\""
            else
                log_success "PATH is already configured"
            fi
            ;;
        windows)
            log_info "Windows PATH setup requires admin privileges"
            log_info "Consider adding $INSTALL_DIR to your system PATH"
            ;;
    esac
}

verify_installation() {
    log_step "Verifying installation..."
    
    # Check CLI
    if command -v mcpctl >/dev/null 2>&1; then
        VERSION=$(mcpctl --version 2>/dev/null || echo "unknown")
        log_success "CLI installed successfully (version: $VERSION)"
    elif [ -f "$HOME/.local/bin/mcpctl" ]; then
        VERSION=$("$HOME/.local/bin/mcpctl" --version 2>/dev/null || echo "unknown")
        log_success "CLI installed successfully (version: $VERSION)"
    else
        log_warning "CLI installation could not be verified"
    fi
    
    # Check GUI
    case $PLATFORM in
        macos)
            if [ -d "/Applications/MCP Hub.app" ]; then
                log_success "GUI app installed successfully"
            else
                log_info "GUI app not installed (CLI-only installation)"
            fi
            ;;
        linux)
            if [ -f "$HOME/.local/bin/mcphub-gui" ] || [ -f "$HOME/.local/bin/mcphub" ]; then
                log_success "GUI app installed successfully"
            else
                log_info "GUI app not installed (CLI-only installation)"
            fi
            ;;
        windows)
            if [ -f "$INSTALL_DIR/mcphub-gui.exe" ] || [ -f "$INSTALL_DIR/mcphub.exe" ]; then
                log_success "GUI app installed successfully"
            else
                log_info "GUI app not installed (CLI-only installation)"
            fi
            ;;
    esac
}

show_next_steps() {
    log_step "🎉 Installation complete!"
    echo
    
    # Run onboarding flow
    if command -v python3 >/dev/null 2>&1; then
        log_info "Setting up MCP Hub..."
        python3 -c "
import sys
sys.path.append('.')
try:
    from mcpctl.onboarding import handle_installation_flow
    handle_installation_flow('1.0.0')
except ImportError:
    print('⚠️  Onboarding system not available - using basic setup')
    print()
    print('🎯 Next Steps:')
    print('1. 🔧 Configure services: mcpctl setup --wizard')
    print('2. 🚀 Start services: mcpctl start')
    print('3. 🔗 Connect your LLM to http://localhost:3000 (default)')
    print()
    print('📚 Documentation: https://github.com/saxyguy81/mcp-hub')
except Exception as e:
    print(f'⚠️  Onboarding failed: {e}')
    print()
    print('🎯 Manual Next Steps:')
    print('1. Run: mcpctl --help')
    print('2. Setup: mcpctl setup --wizard') 
    print('3. Start: mcpctl start')
"
    else
        # Fallback for systems without Python
        log_info "Next steps:"
        echo "  1. Configure services: mcpctl setup --wizard"
        echo "  2. Start services: mcpctl start"
        echo "  3. Connect your LLM to the provided URLs"
        echo
        log_info "Documentation: https://github.com/saxyguy81/mcp-hub/blob/main/README.md"
        log_info "Issues: https://github.com/saxyguy81/mcp-hub/issues"
    fi
    
    echo
    log_success "Ready to manage your MCP servers! 🚀"
}

cleanup() {
    log_step "Cleaning up..."
    rm -rf "$TEMP_DIR"
    log_success "Cleanup complete"
}

# Main execution
main() {
    echo "🚀 MCP Hub Bootstrap Installer"
    echo "=============================="
    echo
    
    # Parse command line arguments
    BUILD_FROM_SOURCE=false
    SKIP_DEPS=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --build-from-source)
                BUILD_FROM_SOURCE=true
                shift
                ;;
            --skip-deps)
                SKIP_DEPS=true
                shift
                ;;
            --help|-h)
                echo "Usage: $0 [OPTIONS]"
                echo "Options:"
                echo "  --build-from-source    Force building from source instead of downloading binaries"
                echo "  --skip-deps           Skip dependency installation"
                echo "  --help, -h            Show this help message"
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done
    
    # Detect platform and package manager
    detect_platform
    detect_package_manager
    
    # Check and install dependencies
    if [ "$SKIP_DEPS" = false ]; then
        check_dependencies
        install_dependencies
    else
        log_warning "Skipping dependency installation"
    fi
    
    # Try binary installation first, fallback to source
    if [ "$BUILD_FROM_SOURCE" = false ]; then
        if download_binary; then
            install_binary
        else
            log_warning "Binary installation failed, falling back to source build"
            BUILD_FROM_SOURCE=true
        fi
    fi
    
    # Build from source if needed
    if [ "$BUILD_FROM_SOURCE" = true ]; then
        build_from_source
    fi
    
    # Setup environment
    setup_path
    
    # Verify installation
    verify_installation
    
    # Show next steps
    show_next_steps
    
    # Cleanup
    cleanup
}

# Run main with all arguments
main "$@"

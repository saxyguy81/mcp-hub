#!/bin/bash
# Fixed Build Script for Enhanced Installer

VERSION="${1:-v1.0.2}"
OUTPUT="install-${VERSION}.sh"

echo "Building installer for $VERSION..."

# Create installer by properly concatenating components
{
    echo '#!/bin/bash'
    echo '# MCP Hub Enhanced Installer - Auto-generated'
    echo 'set -euo pipefail'
    echo ''
    
    echo '# === CORE LIBRARY ==='
    sed '/^#!/d; /^$/d' lib/installer-core.sh
    echo ''
    
    echo '# === ENHANCEMENTS ==='
    sed '/^#!/d; /^$/d' "versions/$VERSION/enhancements.sh"
    echo ''
    
    echo '# === VERSION CONFIG ==='
    echo "VERSION=\"$VERSION\""
    echo 'REPO="saxyguy81/mcp-hub"'
    echo 'BIN_DIR="$HOME/.mcpctl/bin"'
    echo 'WORKSPACE_DIR="$HOME/.mcpctl/workspace"'
    echo 'DEFAULT_PORT=3002'
    echo 'MAX_PORT_ATTEMPTS=10'
    echo ''
    
    echo '# Enhanced setup for demo workspace'
    echo 'enhanced_setup_demo_workspace() {'
    echo '    setup_demo_workspace'
    echo '    local available_port=$(find_available_port)'
    echo '    if [ "$available_port" != "$DEFAULT_PORT" ]; then'
    echo '        log_warning "Using port $available_port instead of $DEFAULT_PORT"'
    echo '        update_docker_compose_port "docker-compose.yml" "$available_port"'
    echo '    fi'
    echo '    echo "$available_port" > "$WORKSPACE_DIR/.mcpctl-port"'
    echo '    log_success "Service will run on port $available_port"'
    echo '}'
    echo ''
    
    echo '# Show installer header'
    echo 'show_installer_header() {'
    echo '    echo -e "${BOLD}${BLUE}"'
    echo '    echo "╔═══════════════════════════════════════════════════════════════╗"'
    echo '    echo "║                MCP Hub Bootstrap Installer v1.0.2            ║"'
    echo '    echo "║               Enhanced with Smart Port & PATH                 ║"'
    echo '    echo "║                                                               ║"'
    echo '    echo "║  🚀 One-line installation for MCP servers                    ║"'
    echo '    echo "║  🔧 Auto-dependency installation                              ║"'
    echo '    echo "║  🌐 Smart port conflict resolution                           ║"'
    echo '    echo "║  ⚡ Immediate PATH availability                               ║"'
    echo '    echo "║                                                               ║"'
    echo '    echo "╚═══════════════════════════════════════════════════════════════╝"'
    echo '    echo -e "${NC}"'
    echo '}'
    echo ''
    
    echo '# Enhanced installation flow'
    echo 'enhanced_install_flow() {'
    echo '    local start_time=$(date +%s)'
    echo '    local platform=$(detect_platform)'
    echo '    log_info "Detected platform: $platform"'
    echo '    install_dependencies'
    echo '    install_mcpctl "$platform"'
    echo '    setup_immediate_path "$BIN_DIR"'
    echo '    verify_immediate_path "$BIN_DIR" || exit 1'
    echo '    enhanced_setup_demo_workspace'
    echo '    local service_port=$(cat "$WORKSPACE_DIR/.mcpctl-port" 2>/dev/null || echo "$DEFAULT_PORT")'
    echo '    local end_time=$(date +%s)'
    echo '    local duration=$((end_time - start_time))'
    echo '    echo -e "\n${BOLD}${GREEN}🎉 Installation Complete!${NC}"'
    echo '    echo -e "${BOLD}⏱️  Completed in ${duration}s${NC}"'
    echo '    echo -e "\n${BLUE}📋 Your MCP servers: http://localhost:$service_port${NC}"'
    echo '    echo -e "${BLUE}🔧 Test: mcpctl status${NC}"'
    echo '    if command_exists mcpctl; then'
    echo '        echo -e "${GREEN}✅ mcpctl immediately available!${NC}"'
    echo '    else'
    echo '        echo -e "${YELLOW}⚠️ Use: $BIN_DIR/mcpctl${NC}"'
    echo '    fi'
    echo '}'
    echo ''
    
    echo '# Main function'
    echo 'main() {'
    echo '    show_installer_header'
    echo '    enhanced_install_flow'
    echo '}'
    echo ''
    
    echo '# Run installer'
    echo 'main "$@"'
} > "$OUTPUT"

chmod +x "$OUTPUT"
ln -sf "$OUTPUT" install.sh

echo "✅ Built: $OUTPUT"
echo "✅ Linked: install.sh"

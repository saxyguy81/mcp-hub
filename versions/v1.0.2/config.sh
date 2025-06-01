#!/bin/bash
# v1.0.2 Configuration

VERSION="v1.0.2"
REPO="saxyguy81/mcp-hub"
BIN_DIR="$HOME/.mcpctl/bin"
WORKSPACE_DIR="$HOME/.mcpctl/workspace"
DEFAULT_PORT=3002
MAX_PORT_ATTEMPTS=10

INSTALLER_TITLE="MCP Hub Bootstrap Installer v1.0.2"
INSTALLER_SUBTITLE="Enhanced with Smart Port & PATH"

FEATURES=(
    "🚀 One-line installation for MCP servers"
    "🔧 Auto-dependency installation"
    "🌐 Smart port conflict resolution"
    "⚡ Immediate PATH availability"
)

# Enhanced setup function for v1.0.2
enhanced_setup_demo_workspace() {
    setup_demo_workspace
    
    # Enhanced port handling
    local available_port
    available_port=$(find_available_port)
    
    if [ "$available_port" != "$DEFAULT_PORT" ]; then
        log_warning "Using port $available_port instead of $DEFAULT_PORT"
        update_docker_compose_port "docker-compose.yml" "$available_port"
    fi
    
    echo "$available_port" > "$WORKSPACE_DIR/.mcpctl-port"
    log_success "Service will run on port $available_port"
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
    show_completion_message "$start_time" "$service_port"
    
    # Test immediate availability
    if command_exists mcpctl; then
        echo -e "${GREEN}✅ mcpctl immediately available!${NC}"
    else
        echo -e "${YELLOW}⚠️ Use: $BIN_DIR/mcpctl${NC}"
    fi
}# Enhanced setup for v1.0.2
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
    
    # Calculate and show completion
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    echo -e "\n${BOLD}${GREEN}🎉 Installation Complete!${NC}"
    echo -e "${BOLD}⏱️  Completed in ${duration}s${NC}"
    echo -e "\n${BLUE}📋 Your MCP servers: http://localhost:$service_port${NC}"
    echo -e "${BLUE}🔧 Test: mcpctl status${NC}"
    
    # Immediate availability test
    if command_exists mcpctl; then
        echo -e "${GREEN}✅ mcpctl immediately available!${NC}"
    else
        echo -e "${YELLOW}⚠️ Use: $BIN_DIR/mcpctl${NC}"
    fi
}
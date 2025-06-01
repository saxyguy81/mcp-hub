#!/bin/bash
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
#!/bin/bash
# End-to-End Installation Test
# Tests the complete installation flow including version option

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

# Test tracking
TESTS_PASSED=0
TESTS_FAILED=0
FAILED_TESTS=()

# Logging
log_info() { echo -e "${BLUE}ℹ${NC} $1"; }
log_success() { echo -e "${GREEN}✅${NC} $1"; }
log_error() { echo -e "${RED}❌${NC} $1"; }
log_test() { echo -e "${BOLD}${BLUE}🧪 $1${NC}"; }

# Test function
run_test() {
    local test_name="$1"
    local test_command="$2"
    
    log_test "Testing: $test_name"
    
    if eval "$test_command"; then
        log_success "$test_name - PASSED"
        ((TESTS_PASSED++))
        return 0
    else
        log_error "$test_name - FAILED"
        FAILED_TESTS+=("$test_name")
        ((TESTS_FAILED++))
        return 1
    fi
}

echo -e "${BOLD}${BLUE}🔬 MCP Hub End-to-End Installation Test${NC}"
echo

# Test 1: Download installer script
run_test "Download installer script" "curl -fsSL https://github.com/saxyguy81/mcp-hub/raw/main/install.sh -o /tmp/mcp-test-install.sh"

# Test 2: Platform detection
run_test "Platform detection" "bash -c 'source /tmp/mcp-test-install.sh && detect_platform | grep -E \"(macos|linux|windows)-(amd64|arm64)\"'"

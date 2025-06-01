#!/bin/bash
# Release Asset Verification Test
# Verifies that all platform binaries exist in GitHub releases

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

# Configuration
REPO="saxyguy81/mcp-hub"
VERSION="${1:-v1.0.2}"

# Test tracking
TESTS_PASSED=0
TESTS_FAILED=0
FAILED_TESTS=()

# Logging
log_info() { echo -e "${BLUE}ℹ${NC} $1"; }
log_success() { echo -e "${GREEN}✅${NC} $1"; }
log_error() { echo -e "${RED}❌${NC} $1"; }
log_test() { echo -e "${BOLD}${BLUE}🧪 $1${NC}"; }

# Expected platforms and their binary names
PLATFORMS=(
    "macos-amd64"
    "macos-arm64" 
    "linux-amd64"
    "linux-arm64"
    "windows-amd64"
)

# Test binary availability
test_binary_exists() {
    local platform="$1"
    local binary_name="mcpctl-$platform"
    
    # Add .exe for Windows
    if [[ "$platform" == "windows-"* ]]; then
        binary_name="$binary_name.exe"
    fi
    
    local url="https://github.com/$REPO/releases/download/$VERSION/$binary_name"
    
    log_test "Testing binary: $binary_name"
    
    if curl -sSf -I "$url" >/dev/null 2>&1; then
        log_success "$binary_name exists and is accessible"
        ((TESTS_PASSED++))
        return 0
    else
        log_error "$binary_name not found at $url"
        FAILED_TESTS+=("$binary_name")
        ((TESTS_FAILED++))
        return 1
    fi
}

echo -e "${BOLD}${BLUE}🔗 MCP Hub Release Asset Verification${NC}"
echo "Testing binary availability for $VERSION..."
echo

# Test each platform
for platform in "${PLATFORMS[@]}"; do
    test_binary_exists "$platform"
done

# Summary
echo
echo -e "${BOLD}📊 Asset Verification Results:${NC}"
echo -e "${GREEN}Available: $TESTS_PASSED${NC}"
echo -e "${RED}Missing: $TESTS_FAILED${NC}"

if [ ${#FAILED_TESTS[@]} -gt 0 ]; then
    echo -e "${RED}Missing assets:${NC}"
    for asset in "${FAILED_TESTS[@]}"; do
        echo -e "  • $asset"
    done
    exit 1
else
    echo -e "${GREEN}✅ All platform binaries are available!${NC}"
fi

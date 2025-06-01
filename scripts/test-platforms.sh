#!/bin/bash
# Comprehensive Platform Detection Test Suite
# Tests all supported platform combinations to prevent naming mismatches

set -euo pipefail

# Detect if running in CI environment
if [[ "${CI:-}" == "true" ]] || [[ "${GITHUB_ACTIONS:-}" == "true" ]]; then
    # Disable colors in CI
    RED=''
    GREEN=''
    YELLOW=''
    BLUE=''
    BOLD=''
    NC=''
else
    # Enable colors for local development
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    BLUE='\033[0;34m'
    BOLD='\033[1m'
    NC='\033[0m'
fi

# Test tracking
TESTS_PASSED=0
TESTS_FAILED=0
FAILED_TESTS=()

# Logging
log_info() { echo -e "${BLUE}ℹ${NC} $1"; }
log_success() { echo -e "${GREEN}✅${NC} $1"; }
log_error() { echo -e "${RED}❌${NC} $1"; }
log_test() { echo -e "${BOLD}${BLUE}🧪 $1${NC}"; }

# Platform detection function (from detect-platform.sh)
detect_platform_for_system() {
    local system="$1"
    local machine="$2"
    
    case "$system" in
        Darwin*)
            case "$machine" in
                x86_64) echo "macos-amd64" ;;
                arm64) echo "macos-arm64" ;;
                *) echo "unsupported-macos-$machine" ;;
            esac ;;
        Linux*)
            case "$machine" in                x86_64) echo "linux-amd64" ;;
                aarch64|arm64) echo "linux-arm64" ;;
                *) echo "unsupported-linux-$machine" ;;
            esac ;;
        CYGWIN*|MINGW*|MSYS*) echo "windows-amd64" ;;
        *) echo "unsupported-$system" ;;
    esac
}

# Test function
run_test() {
    local test_name="$1"
    local expected="$2"
    local system="$3"
    local machine="$4"
    
    log_test "Testing: $test_name"
    
    local actual
    actual=$(detect_platform_for_system "$system" "$machine")
    
    if [ "$actual" = "$expected" ]; then
        log_success "$test_name -> $actual (PASS)"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        log_error "$test_name -> Expected: $expected, Got: $actual (FAIL)"
        FAILED_TESTS+=("$test_name")
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

echo -e "${BOLD}${BLUE}🔬 MCP Hub Platform Detection Test Suite${NC}"
echo "Testing all supported platform combinations..."
echo

# Test macOS platforms
log_info "Testing macOS platforms..."
run_test "macOS Intel (x86_64)" "macos-amd64" "Darwin" "x86_64"
run_test "macOS Apple Silicon (arm64)" "macos-arm64" "Darwin" "arm64"

# Test Linux platforms  
log_info "Testing Linux platforms..."
run_test "Linux AMD64 (x86_64)" "linux-amd64" "Linux" "x86_64"
run_test "Linux ARM64 (aarch64)" "linux-arm64" "Linux" "aarch64"
run_test "Linux ARM64 (arm64)" "linux-arm64" "Linux" "arm64"

# Test Windows platforms
log_info "Testing Windows platforms..."
run_test "Windows CYGWIN" "windows-amd64" "CYGWIN_NT-10.0" "x86_64"
run_test "Windows MINGW" "windows-amd64" "MINGW64_NT-10.0" "x86_64"
run_test "Windows MSYS" "windows-amd64" "MSYS_NT-10.0" "x86_64"

echo
echo -e "${BOLD}📊 Test Results:${NC}"
echo -e "${GREEN}Passed: $TESTS_PASSED${NC}"
echo -e "${RED}Failed: $TESTS_FAILED${NC}"

if [ ${#FAILED_TESTS[@]} -gt 0 ]; then
    echo -e "${RED}Failed tests:${NC}"
    for test in "${FAILED_TESTS[@]}"; do
        echo -e "  • $test"
    done
    exit 1
else
    echo -e "${GREEN}✅ All platform detection tests passed!${NC}"
fi

echo
echo -e "${BOLD}📊 Test Results:${NC}"
echo -e "${GREEN}Passed: $TESTS_PASSED${NC}"
echo -e "${RED}Failed: $TESTS_FAILED${NC}"

if [ ${#FAILED_TESTS[@]} -gt 0 ]; then
    echo -e "${RED}Failed tests:${NC}"
    for test in "${FAILED_TESTS[@]}"; do
        echo -e "  • $test"
    done
    exit 1
else
    echo -e "${GREEN}✅ All platform detection tests passed!${NC}"
fi

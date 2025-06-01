#!/bin/bash
# Enhanced debug script for GitHub Actions troubleshooting
set -euo pipefail

echo "🔍 GitHub Actions Environment Debug (Enhanced)"
echo "=============================================="

echo "📍 Basic Environment:"
echo "  PWD: $(pwd)"
echo "  User: $(whoami)"
echo "  Shell: $0"
echo "  Bash version: $BASH_VERSION"

echo
echo "🌍 CI Environment Detection:"
echo "  CI: ${CI:-<not set>}"
echo "  GITHUB_ACTIONS: ${GITHUB_ACTIONS:-<not set>}"
echo "  RUNNER_OS: ${RUNNER_OS:-<not set>}"

echo
echo "🔍 Files in scripts/:"
ls -la scripts/ | head -10

echo
echo "📋 Color Variables Test:"
if [[ "${CI:-}" == "true" ]] || [[ "${GITHUB_ACTIONS:-}" == "true" ]]; then
    echo "  Running in CI - colors should be disabled"
    RED=''
    GREEN=''
    BLUE=''
else
    echo "  Running locally - colors should be enabled"
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    BLUE='\033[0;34m'
fi
echo -e "  Color test: ${RED}RED${GREEN}GREEN${BLUE}BLUE"

echo
echo "🔍 Testing basic operations:"
echo "  chmod works: $(chmod +x scripts/detect-platform.sh && echo 'yes' || echo 'no')"
echo "  Script exists: $([ -f scripts/detect-platform.sh ] && echo 'yes' || echo 'no')"
echo "  Script executable: $([ -x scripts/detect-platform.sh ] && echo 'yes' || echo 'no')"

echo
echo "🔍 Testing platform detection:"
if ./scripts/detect-platform.sh; then
    echo "✅ detect-platform.sh executed successfully"
else
    echo "❌ detect-platform.sh failed with exit code: $?"
fi

echo
echo "🔍 Testing curl and network:"
if curl --version >/dev/null 2>&1; then
    echo "✅ curl is available"
    echo "  curl version: $(curl --version | head -1)"
else
    echo "❌ curl not available"
fi

echo
echo "🔍 Testing binary URL access:"
URL="https://github.com/saxyguy81/mcp-hub/releases/download/v1.0.2/mcpctl-linux-amd64"
if curl -sSf --max-time 5 -I "$URL" >/dev/null 2>&1; then
    echo "✅ Binary URL accessible"
else
    echo "❌ Binary URL not accessible"
fi

echo
echo "🧪 Running Fixed Test Scripts:"
echo "-------------------------------"

echo "Testing platforms script..."
if CI=true GITHUB_ACTIONS=true ./scripts/test-platforms.sh; then
    echo "✅ test-platforms.sh passed"
else
    echo "❌ test-platforms.sh failed"
fi

echo
echo "Testing release assets script..."
if CI=true GITHUB_ACTIONS=true ./scripts/test-release-assets.sh v1.0.2; then
    echo "✅ test-release-assets.sh passed"
else
    echo "❌ test-release-assets.sh failed"
fi

echo
echo "🎉 Enhanced debug complete"
echo "If tests pass here but fail in GitHub Actions, check workflow configuration."

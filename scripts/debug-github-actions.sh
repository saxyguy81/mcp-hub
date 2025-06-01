#!/bin/bash
# Minimal debug script for GitHub Actions
set -euo pipefail

echo "🔍 GitHub Actions Environment Debug"
echo "PWD: $(pwd)"
echo "User: $(whoami)"
echo "Shell: $0"
echo "Bash version: $BASH_VERSION"

echo "🔍 Files in scripts/:"
ls -la scripts/

echo "🔍 Testing basic operations:"
echo "chmod works: $(chmod +x scripts/detect-platform.sh && echo 'yes' || echo 'no')"
echo "Script exists: $([ -f scripts/detect-platform.sh ] && echo 'yes' || echo 'no')"
echo "Script executable: $([ -x scripts/detect-platform.sh ] && echo 'yes' || echo 'no')"

echo "🔍 Testing script execution:"
if ./scripts/detect-platform.sh; then
    echo "✅ detect-platform.sh executed successfully"
else
    echo "❌ detect-platform.sh failed with exit code: $?"
fi

echo "🔍 Testing curl availability:"
if curl --version >/dev/null 2>&1; then
    echo "✅ curl is available"
else
    echo "❌ curl not available"
fi

echo "🔍 Testing binary URL access:"
URL="https://github.com/saxyguy81/mcp-hub/releases/download/v1.0.2/mcpctl-linux-amd64"
if curl -sSf -I "$URL" >/dev/null 2>&1; then
    echo "✅ Binary URL accessible"
else
    echo "❌ Binary URL not accessible"
fi

echo "🎉 Debug complete"

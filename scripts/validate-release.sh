#!/bin/bash
# Quick Release Validation for MCP Hub v1.0.2

set -euo pipefail

VERSION="v1.0.2"
REPO="saxyguy81/mcp-hub"

echo "🚀 MCP Hub v1.0.2 Release Validation"
echo

# Test 1: Install Script Download
echo "📋 Testing install script download..."
if curl -fsSL https://github.com/$REPO/releases/latest/download/install.sh > /tmp/test-install.sh; then
    echo "✅ Install script downloaded successfully"
    chmod +x /tmp/test-install.sh
else
    echo "❌ Install script download failed"
    exit 1
fi

# Test 2: Check Release Assets 
echo "📋 Checking release assets..."
ASSETS=$(curl -s https://api.github.com/repos/$REPO/releases/tags/$VERSION | jq -r '.assets[].name' 2>/dev/null || echo "API request failed")
if echo "$ASSETS" | grep -q "mcpctl"; then
    echo "✅ CLI binaries found in release"
else
    echo "❌ CLI binaries missing from release"
fi

# Test 3: Docker Build Test
echo "📋 Testing Docker build..."
cd /tmp/mcp-hub
if docker build -f web/Dockerfile -t mcp-hub-test:latest .; then
    echo "✅ Docker build successful"
    
    # Quick container test
    if docker run --rm mcp-hub-test:latest python -c "import server; print('Container works!')"; then
        echo "✅ Container test passed"
    else
        echo "⚠️ Container test failed"
    fi
else
    echo "❌ Docker build failed"
fi

echo
echo "🎉 Basic validation complete!"

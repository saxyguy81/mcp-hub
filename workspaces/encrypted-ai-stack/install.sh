#!/bin/bash
# One-click installer for encrypted AI stack workspace
# This demonstrates the complete encrypted secrets workflow

set -e

echo "🚀 Installing Encrypted AI Development Stack"
echo "============================================"

# Check if MCP Hub is installed
if ! command -v mcpctl >/dev/null 2>&1; then
    echo "📦 Installing MCP Hub..."
    curl -fsSL https://github.com/saxyguy81/mcp-hub/releases/latest/download/install.sh | bash
    echo "✅ MCP Hub installed"
fi

# Import this workspace
echo "📥 Importing encrypted workspace..."
mcpctl workspace import . --activate

echo "🔐 Setting up encryption..."
echo "💡 You'll be prompted for the encryption key to decrypt secrets"

# Start services
echo "🚀 Starting services..."
mcpctl up

echo "🎉 Encrypted AI Stack is ready!"
echo
echo "📋 Available services:"
echo "  • Firecrawl: http://localhost:8081"
echo "  • PostgreSQL: localhost:5432"
echo "  • OpenAI Proxy: http://localhost:8082"
echo
echo "🔧 Management commands:"
echo "  • Check status: mcpctl status"
echo "  • View logs: mcpctl logs"
echo "  • Stop services: mcpctl down"
echo
echo "🔐 Secret management:"
echo "  • View secrets: mcpctl workspace decrypt encrypted-ai-stack --show-secrets"
echo "  • Export secrets: mcpctl workspace decrypt encrypted-ai-stack --export-env"

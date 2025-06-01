#!/bin/bash
# This file exists to enable GitHub Pages hosting option
# It redirects to the actual installer from GitHub releases

echo "Redirecting to MCP Hub installer..."
exec curl -fsSL https://github.com/saxyguy81/mcp-hub/releases/latest/download/install.sh

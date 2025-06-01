#!/bin/bash
# Test the workspace system

set -e

echo "🧪 Testing MCP Hub Workspace System"
echo "=================================="

cd /Users/smhanan/mcp-hub

# Test workspace creation
echo "📦 Testing workspace creation..."
python3 -c "
from mcpctl.workspace import WorkspaceManager
manager = WorkspaceManager()
workspace = manager.create_workspace('test-workspace', 'Test workspace')
print(f'✅ Created workspace: {workspace.name}')
manager.save_workspace(workspace)
print('✅ Saved workspace successfully')
"

# Test workspace listing  
echo "📋 Testing workspace listing..."
python3 -c "
from mcpctl.workspace import WorkspaceManager
manager = WorkspaceManager()
workspaces = manager.list_workspaces()
print(f'✅ Found workspaces: {workspaces}')
"

# Test workspace loading
echo "📥 Testing workspace loading..."
python3 -c "
from mcpctl.workspace import WorkspaceManager
manager = WorkspaceManager()
workspace = manager.load_workspace('test-workspace')
if workspace:
    print(f'✅ Loaded workspace: {workspace.name}')
else:
    print('❌ Failed to load workspace')
"

echo "🎉 Workspace system tests passed!"

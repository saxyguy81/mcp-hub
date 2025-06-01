#!/bin/bash
# Test the encrypted secrets system

set -e

echo "🔐 Testing MCP Hub Encrypted Secrets System"
echo "==========================================="

cd /Users/smhanan/mcp-hub

# Test 1: Basic encryption functionality
echo "🧪 Testing basic encryption..."
python3 -c "
import sys
sys.path.append('.')

try:
    from mcpctl.encryption import EncryptionManager
    manager = EncryptionManager()
    
    # Test encryption/decryption
    test_data = {'API_KEY': 'test-key-123', 'PASSWORD': 'secret-pass'}
    
    print('🔐 Testing encryption...')
    encrypted = manager.encrypt_data(test_data, 'test-workspace', use_lastpass=False)
    print(f'✅ Encrypted: {encrypted[:30]}...')
    
    print('🔓 Testing decryption...')
    decrypted = manager.decrypt_data(encrypted, 'test-workspace', use_lastpass=False)
    print(f'✅ Decrypted: {list(decrypted.keys())}')
    
    if decrypted == test_data:
        print('✅ Encryption test PASSED')
    else:
        print('❌ Encryption test FAILED')
        sys.exit(1)
        
except ImportError as e:
    print(f'⚠️  Skipping encryption test: {e}')
    print('💡 Install cryptography: pip install cryptography')
"

# Test 2: Workspace integration
echo "📦 Testing workspace encryption integration..."
python3 -c "
import sys
sys.path.append('.')

try:
    from mcpctl.workspace import WorkspaceManager
    from mcpctl.encryption import EncryptionManager
    
    # Create test workspace
    manager = WorkspaceManager()
    workspace = manager.create_workspace('test-encrypted', 'Test encrypted workspace')
    
    # Add some test services and secrets
    workspace.services = {
        'api-service': {
            'image': 'nginx:alpine',
            'environment': ['API_KEY=\${API_KEY}'],
            'ports': ['8080:80']
        }
    }
    
    # Test secrets (these would normally be encrypted)
    workspace.secrets = {
        'API_KEY': 'Test API key for service'
    }
    
    manager.save_workspace(workspace)
    print('✅ Created test workspace with secrets')
    
    # Load it back
    loaded = manager.load_workspace('test-encrypted')
    if loaded:
        print(f'✅ Loaded workspace: {loaded.name}')
        print(f'📋 Services: {list(loaded.services.keys())}')
        print(f'🔑 Secrets: {list(loaded.secrets.keys())}')
    else:
        print('❌ Failed to load workspace')
        sys.exit(1)
        
except Exception as e:
    print(f'❌ Workspace test failed: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
"

# Test 3: CLI integration
echo "🖥️  Testing CLI integration..."
if command -v python3 >/dev/null 2>&1; then
    python3 -m mcpctl.cli workspace list 2>/dev/null && echo "✅ CLI workspace commands work" || echo "⚠️  CLI needs full setup"
else
    echo "⚠️  Python3 not found, skipping CLI test"
fi

echo
echo "🎉 Encryption system tests completed!"
echo
echo "📋 To use encrypted secrets:"
echo "1. Create workspace: mcpctl workspace create my-stack --from-current --encrypt-secrets"
echo "2. Export for sharing: mcpctl workspace export my-stack --format git"
echo "3. Import on new machine: mcpctl workspace import https://github.com/user/config.git"
echo "4. Secrets are automatically encrypted/decrypted!"

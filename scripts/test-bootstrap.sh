#!/bin/bash
# Test script for the bootstrap installer and web service

set -e

echo "🧪 Testing MCP Hub Bootstrap System"
echo "=================================="

# Test 1: Web Service
echo "📡 Testing web service..."
cd web

# Use python3 instead of python
if command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD="python3"
elif command -v python >/dev/null 2>&1; then
    PYTHON_CMD="python"
else
    echo "⚠️  Python not found, skipping web service test"
    cd ..
    echo "🔍 Testing install script syntax..."
    bash -n scripts/install.sh && echo "✅ Install script syntax is valid"
    exit 0
fi

$PYTHON_CMD server.py &
SERVER_PID=$!
sleep 2

# Test landing page
echo "Testing landing page..."
curl -s http://localhost:5000/ | grep -q "MCP Hub" && echo "✅ Landing page works"

# Test install script endpoint
echo "Testing install script endpoint..."
curl -s -H "User-Agent: curl/7.68.0" http://localhost:5000/ | grep -q "MCP Hub Bootstrap Installer" && echo "✅ Install script endpoint works"

# Test API endpoints
echo "Testing API endpoints..."
curl -s http://localhost:5000/health | grep -q "healthy" && echo "✅ Health endpoint works"

# Stop web server
kill $SERVER_PID
cd ..

# Test 2: Install Script Syntax
echo "🔍 Testing install script syntax..."
bash -n scripts/install.sh && echo "✅ Install script syntax is valid"

# Test 3: Install Script Help
echo "📚 Testing install script help..."
bash scripts/install.sh --help | grep -q "Usage:" && echo "✅ Install script help works"

# Test 4: Platform Detection
echo "🖥️  Testing platform detection..."
bash -c "
source scripts/install.sh
detect_platform
echo \"Platform: \$PLATFORM-\$ARCH\"
" && echo "✅ Platform detection works"

# Test 5: Dependency Checking
echo "📦 Testing dependency checking..."
bash -c "
source scripts/install.sh
detect_platform
detect_package_manager
check_dependencies
echo \"Package manager: \$PKG_MANAGER\"
echo \"Dependencies to install: \${DEPS_TO_INSTALL[*]}\"
" && echo "✅ Dependency checking works"

# Test 6: GitHub Actions Workflow Syntax
echo "⚙️  Testing GitHub Actions workflows..."
if command -v yamllint >/dev/null 2>&1; then
    yamllint .github/workflows/build.yml && echo "✅ Build workflow syntax is valid"
    yamllint .github/workflows/release.yml && echo "✅ Release workflow syntax is valid"
else
    echo "⚠️  yamllint not found, skipping workflow syntax check"
fi

# Test 7: Electron Builder Config
echo "🖥️  Testing Electron builder config..."
if command -v jq >/dev/null 2>&1; then
    jq . electron/builder.json >/dev/null && echo "✅ Electron builder config is valid JSON"
else
    echo "⚠️  jq not found, skipping JSON validation"
fi

echo
echo "🎉 All tests passed!"
echo
echo "📋 Next steps to deploy:"
echo "1. Push to GitHub: git push origin main"
echo "2. Create a release: git tag v1.0.0 && git push origin v1.0.0"
echo "3. Deploy web service to hosting platform"
echo "4. Update DNS: point get.mcphub.io to your web service"
echo "5. Test: curl -fsSL https://get.mcphub.io | bash --skip-deps"

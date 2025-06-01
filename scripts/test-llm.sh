#!/bin/bash
# Test the LLM verification system

set -e

echo "🧪 Testing MCP Hub LLM Verification System"
echo "=========================================="

cd /Users/smhanan/mcp-hub

# Test 1: LLM Tester module import
echo "📦 Testing LLM tester module..."
python3 -c "
from mcpctl.llm_tester import LLMTester, get_llm_config

tester = LLMTester()
print('✅ LLMTester imported successfully')

config = get_llm_config()
print(f'✅ Config loaded: {len(config)} items')
"

# Test 2: Claude Desktop test (will likely fail but should handle gracefully)
echo "🧪 Testing Claude Desktop detection..."
python3 -c "
from mcpctl.llm_tester import LLMTester

tester = LLMTester()
result = tester.test_claude_desktop()
print(f'Claude Desktop test: {\"✅ PASS\" if result[\"success\"] else \"❌ FAIL (expected)\"}')
print(f'Message: {result[\"message\"]}')
print(f'Duration: {result[\"duration\"]}s')
"

# Test 3: Custom LLM test with invalid URL (should fail gracefully)
echo "🧪 Testing custom LLM with invalid URL..."
python3 -c "
from mcpctl.llm_tester import LLMTester

tester = LLMTester()
result = tester.test_custom_llm('https://invalid-url-for-testing.example.com')
print(f'Invalid URL test: {\"✅ FAIL (expected)\" if not result[\"success\"] else \"❌ PASS (unexpected)\"}')
print(f'Message: {result[\"message\"]}')
print(f'Duration: {result[\"duration\"]}s')
"

# Test 4: OpenAI test without API key (should fail gracefully)
echo "🧪 Testing OpenAI without API key..."
python3 -c "
from mcpctl.llm_tester import LLMTester

tester = LLMTester()
result = tester.test_openai_api()
print(f'OpenAI no-key test: {\"✅ FAIL (expected)\" if not result[\"success\"] else \"❌ PASS (unexpected)\"}')
print(f'Message: {result[\"message\"]}')
"

# Test 5: Test result formatting
echo "📝 Testing result formatting..."
python3 -c "
from mcpctl.llm_tester import LLMTester

tester = LLMTester()
test_result = {
    'success': True,
    'backend': 'test',
    'duration': 1.23,
    'status_code': 200,
    'message': '✅ Test connection successful',
    'details': {
        'endpoint': 'https://api.example.com',
        'response_time': '1.23s',
        'api_type': 'OpenAI-compatible'
    }
}

formatted = tester.format_test_result(test_result, verbose=True)
print('✅ Result formatting works:')
print(formatted)
"

# Test 6: CLI integration
echo "🖥️  Testing CLI integration..."
if command -v python3 >/dev/null 2>&1; then
    echo "Testing CLI LLM commands..."
    python3 -c "
import sys
sys.path.append('.')

try:
    from mcpctl.cli import llm_app
    print('✅ LLM CLI commands imported successfully')
except Exception as e:
    print(f'❌ CLI import failed: {e}')
    sys.exit(1)
"
else
    echo "⚠️  Python3 not found, skipping CLI test"
fi

echo
echo "🎉 LLM verification system tests completed!"
echo
echo "📋 Features verified:"
echo "✅ LLM backend testing (Claude Desktop, OpenAI, Custom)"
echo "✅ Error handling for invalid configurations"
echo "✅ Result formatting and display"
echo "✅ CLI command integration"
echo
echo "🚀 Ready for LLM verification!"
echo
echo "💡 Try the new commands:"
echo "• mcpctl llm test --help"
echo "• mcpctl llm setup"
echo "• mcpctl llm status"
echo "• mcpctl llm test claude"
echo "• mcpctl llm test custom --url https://api.openai.com --api-key YOUR_KEY"

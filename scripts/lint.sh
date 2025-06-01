#!/bin/bash
# Code Quality Check Script for MCP Hub

set -e

echo "🔍 Running MCP Hub code quality checks..."

CHECKS_PASSED=0
CHECKS_FAILED=0

run_check() {
    echo "🔧 Running $1..."
    if "${@:2}"; then
        echo "✅ $1 passed"
        ((CHECKS_PASSED++))
    else
        echo "❌ $1 failed"
        ((CHECKS_FAILED++))
    fi
}

# Run all checks
run_check "Black formatting" black --check --diff .
run_check "Import sorting" isort --check-only --diff .
run_check "Flake8 linting" flake8 .
run_check "Type checking" mypy mcpctl/ --ignore-missing-imports
run_check "Security analysis" bandit -r mcpctl/ --severity-level medium

echo "📊 Results: $CHECKS_PASSED passed, $CHECKS_FAILED failed"

if [ $CHECKS_FAILED -gt 0 ]; then
    echo "💡 To fix formatting: black . && isort ."
    exit 1
else
    echo "✅ All checks passed!"
fi

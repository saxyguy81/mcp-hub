# MCP Hub Development Tasks

.PHONY: help install lint format test build clean

help:  ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install development dependencies
	pip install -e .
	pip install black flake8 mypy isort bandit safety pytest

lint:  ## Run all linting checks
	./scripts/lint.sh

format:  ## Format code with black and isort
	@echo "🎨 Formatting code..."
	black .
	isort .
	@echo "✅ Code formatted!"

test:  ## Run tests
	@echo "🧪 Running tests..."
	python -c "from mcpctl.cli import app; print('✅ CLI imports successfully')"

build:  ## Build CLI binary
	@echo "🔨 Building CLI..."
	pyinstaller main.py -n mcpctl --onefile

clean:  ## Clean build artifacts
	rm -rf build/ dist/ *.spec
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

check-security:  ## Run security checks
	bandit -r mcpctl/
	safety check

docker-build:  ## Build Docker containers
	docker build -f web/Dockerfile -t mcp-hub/web .

docker-clean:  ## Clean Docker resources
	docker system prune -f

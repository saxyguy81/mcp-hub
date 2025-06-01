# Development Guide

## Code Quality Standards

MCP Hub follows strict code quality standards enforced through automated CI checks.

### Quick Start

```bash
# Install development dependencies
make install

# Format code
make format

# Run all linting checks  
make lint

# Run tests
make test
```

### Code Quality Tools

- **Black**: Code formatting (88 character line length)
- **isort**: Import organization
- **flake8**: Linting and style checking
- **mypy**: Type checking 
- **bandit**: Security analysis
- **safety**: Dependency vulnerability scanning

### Automated Checks

All pull requests automatically run:
- Code formatting validation
- Import organization checks
- Linting and style validation
- Type checking analysis
- Security vulnerability scanning

Failed checks will block PR merging.

### Manual Commands

```bash
# Format code automatically
black .
isort .

# Check formatting without changes
black --check .
isort --check-only .

# Run linting
flake8 .

# Type checking
mypy mcpctl/

# Security analysis
bandit -r mcpctl/
```

### Configuration

Code quality settings are in:
- `pyproject.toml` - Black, isort, mypy, bandit config
- `.flake8` - Flake8 configuration
- `Makefile` - Development shortcuts
- `scripts/lint.sh` - Local quality check script

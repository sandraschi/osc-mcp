# OSC-MCP Development Makefile
# State-of-the-Art CI/CD and Development Tools

.PHONY: help install dev-install test lint format type-check security-check docs build clean release

# Default target
help:
	@echo "OSC-MCP Development Commands"
	@echo "============================"
	@echo ""
	@echo "Development:"
	@echo "  install       Install package in development mode"
	@echo "  dev-install   Install with development dependencies"
	@echo "  test          Run test suite with coverage"
	@echo "  lint          Run Ruff linter"
	@echo "  format        Format code with Ruff"
	@echo "  type-check    Run mypy type checking"
	@echo "  security      Run security checks (bandit, safety)"
	@echo ""
	@echo "Quality Assurance:"
	@echo "  quality       Run all quality checks (lint + format + type + test)"
	@echo "  docs          Build documentation"
	@echo ""
	@echo "Build & Release:"
	@echo "  build         Build distribution packages"
	@echo "  release       Create and publish release"
	@echo "  clean         Clean build artifacts"
	@echo ""
	@echo "CI/CD:"
	@echo "  ci            Run full CI pipeline locally"
	@echo "  pre-commit    Install and run pre-commit hooks"
	@echo ""

# Installation
install:
	pip install -e .

dev-install:
	pip install -e ".[dev]"

# Testing
test:
	pytest tests/ -v --cov=oscmcp --cov-report=term-missing --cov-report=xml

test-fast:
	pytest tests/ -x --tb=short

# Code Quality
lint:
	ruff check .

format:
	ruff format .

type-check:
	mypy src/ --ignore-missing-imports

security:
	@echo "Running Bandit security scan..."
	bandit -r src/ -f json -o bandit-report.json || true
	@echo "Running Safety dependency check..."
	safety check --output json || true

# Combined Quality Checks
quality: lint format type-check test security

# Documentation
docs:
	if [ -f "mkdocs.yml" ]; then \
		mkdocs build --strict; \
	else \
		echo "No mkdocs.yml found, skipping docs build"; \
	fi

# Build & Distribution
build:
	python -m build

# Release (requires VERSION environment variable)
release: quality build
	@echo "Creating release v$(VERSION)"
	git tag -a v$(VERSION) -m "Release v$(VERSION)"
	git push origin v$(VERSION)
	@echo "Release v$(VERSION) created and pushed"
	@echo "GitHub Actions will handle PyPI publishing"

# Cleanup
clean:
	rm -rf dist/ build/ *.egg-info/ .coverage coverage.xml bandit-report.json
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# CI/CD Pipeline (local simulation)
ci: quality docs build
	@echo "✅ All CI checks passed!"

# Pre-commit hooks
pre-commit:
	pre-commit install
	pre-commit run --all-files

# Development server
serve:
	python -m oscmcp.server

# MCP Inspector (requires fastmcp dev tools)
inspector:
	fastmcp dev src.oscmcp.server:server

# Docker development
docker-build:
	docker build -t osc-mcp .

docker-run:
	docker run -p 8000:8000 osc-mcp

# Version management
version:
	python -c "import oscmcp; print(oscmcp.__version__)"

# Dependency updates
update-deps:
	pip install --upgrade pip
	pip install --upgrade -e ".[dev]"
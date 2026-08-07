set windows-shell := ["powershell.exe", "-NoProfile", "-Command"]
import 'scripts/just/fleet.just'

# --- Dashboard ---

# Open the interactive recipe dashboard in the browser
default:
    @just --list


# Synchronize deps, pre-commit hooks, and web frontend
bootstrap:
    uv sync --extra dev --group dev
    uv run pre-commit install
    Set-Location web_sota; npm ci; if ($LASTEXITCODE -ne 0) { npm install }
    Write-Host "Pre-commit hooks installed." -ForegroundColor Green
# --- Quality ---

# Execute Ruff SOTA v13.1 linting
lint:
    Set-Location '{{justfile_directory()}}'
    uv run ruff check .
    Set-Location '{{justfile_directory()}}\web_sota'
    npx @biomejs/biome ci .

# Execute Ruff SOTA v13.1 fix and formatting
fix:
    Set-Location '{{justfile_directory()}}'
    uv run ruff check . --fix --unsafe-fixes
    uv run ruff format .
    Set-Location '{{justfile_directory()}}\web_sota'
    npx @biomejs/biome check --write .

# --- Hardening ---

# Serve the MCP server (stdio mode)
serve:
    Set-Location '{{justfile_directory()}}'
    uv run python -m oscmcp

# Run tests
test:
    Set-Location '{{justfile_directory()}}'
    uv run pytest tests/ -v

# Format Python code
fmt:
    Set-Location '{{justfile_directory()}}'
    uv run ruff format .

# TypeScript typecheck
types:
    Set-Location '{{justfile_directory()}}\web_sota'
    npx tsc --noEmit

# All gates green: lint + types + test
gates-green: lint types
    Set-Location '{{justfile_directory()}}'
    uv run pytest tests/ -q

# Build the Tauri NSIS desktop installer
build-native:
    Set-Location '{{justfile_directory()}}\native'
    $env:Path = "$env:USERPROFILE\.cargo\bin;$env:Path"
    .\build.ps1

# E2E Playwright tests
e2e:
    Set-Location '{{justfile_directory()}}\web_sota'
    npx playwright test

# Execute Bandit security audit
check-sec:
    Set-Location '{{justfile_directory()}}'
    uv run bandit -r src/

# Execute safety audit of dependencies
audit-deps:
    Set-Location '{{justfile_directory()}}'
    uv run safety check


# Bootstrap: install dev deps + pre-commit hook

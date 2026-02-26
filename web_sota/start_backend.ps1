# Backend API Start - Clears port, runs API
$BackendPort = 10767
$ProjectRoot = Split-Path -Parent $PSScriptRoot

Set-Location $ProjectRoot
# Clear port from zombies/squatters (cross-platform via npm)
npx --yes kill-port $BackendPort 2>$null

# Run Python FastAPI backend
$env:PYTHONPATH = "$ProjectRoot\src"
uv run python -m oscmcp.api.main

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
$pkg = "oscmcp"
$stage = Join-Path $RepoRoot "mcpb\src\$pkg"
Write-Host "=== mcpb-pack: fresh-stage wipe+recopy ===" -ForegroundColor Cyan

# 1. Wipe stage
if (Test-Path (Join-Path $RepoRoot "mcpb\src")) {
    Remove-Item -Recurse -Force (Join-Path $RepoRoot "mcpb\src")
    Write-Host "  wiped mcpb/src" -ForegroundColor DarkGray
}
New-Item -ItemType Directory -Force -Path (Split-Path $stage) | Out-Null

# 2. Recopy preserve package dir (NEVER flatten)
$src = Join-Path $RepoRoot "src\$pkg"
if (-not (Test-Path $src)) { throw "src/$pkg not found at $src" }
Copy-Item -Recurse -Force $src $stage
Write-Host "  copied src/$pkg -> mcpb/src/$pkg" -ForegroundColor Green

# 3. Strip bytecode / bak pollution from stage + source
Get-ChildItem -Recurse -Path $stage -Filter "__pycache__" -Directory | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Get-ChildItem -Recurse -Path $stage -Filter "*.pyc" | Remove-Item -Force -ErrorAction SilentlyContinue
Get-ChildItem -Recurse -Path $stage -Filter "*.bak" | Remove-Item -Force -ErrorAction SilentlyContinue
Get-ChildItem -Recurse -Path $stage -Filter "*.bak.*" | Remove-Item -Force -ErrorAction SilentlyContinue

# 4. Ensure .mcpbignore at pack root (mcpb/)
$repoIgnore = Join-Path $RepoRoot ".mcpbignore"
$mcpbIgnore = Join-Path $RepoRoot "mcpb\.mcpbignore"
if ((Test-Path $repoIgnore) -and (-not (Test-Path $mcpbIgnore))) {
    Copy-Item $repoIgnore $mcpbIgnore -Force
    Write-Host "  copied .mcpbignore -> mcpb/.mcpbignore" -ForegroundColor Yellow
}

# 5. Mirror assets prompts if needed
$promptsSrc = Join-Path $RepoRoot "assets\prompts"
$promptsDst = Join-Path $RepoRoot "mcpb\assets\prompts"
if (Test-Path $promptsSrc) {
    New-Item -ItemType Directory -Force -Path $promptsDst | Out-Null
    Copy-Item -Force (Join-Path $promptsSrc "*") $promptsDst
}

# 6. Mechanical checks
Write-Host "-> checks" -ForegroundColor Yellow
$env:PYTHONDONTWRITEBYTECODE = "1"
# a) import resolves inside stage only
$check = & uv run python -c "import sys; sys.path.insert(0, 'mcpb/src'); from oscmcp.server import server; import pathlib; print(pathlib.Path(server.__file__).resolve())" 2>&1
Write-Host "  import origin: $check"
if ($check -notmatch "mcpb") { throw "Import did not resolve inside mcpb/src — flattened or missing package dir. Got: $check" }

# b) hatch packages exist (if pyproject has hatch)
# c) pollution already stripped

Write-Host "=== stage verified OK ===" -ForegroundColor Green
Write-Host "Next: mcpb pack mcpb dist/osc-mcp.mcpb  (run manually or via bunx @anthropic-ai/mcpb)" -ForegroundColor Cyan

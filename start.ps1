param([switch]$Headless, [switch]$BackendOnly, [switch]$NoBrowser)
$ErrorActionPreference = "Stop"
$SkipFrontend = $Headless -or $BackendOnly
$ScriptRoot = Split-Path -Parent $PSCommandPath
$BackendPort = 10767
$FrontendPort = 10766

# Port zombie clearing
Get-NetTCPConnection -LocalPort $BackendPort -ErrorAction SilentlyContinue |
    ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
Get-NetTCPConnection -LocalPort $FrontendPort -ErrorAction SilentlyContinue |
    ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }

# Start backend
$BackendJob = Start-Job -Name "osc-mcp-backend" -ScriptBlock {
    param($Root, $Port)
    Set-Location $Root
    $env:OSC_MCP_PORT = "$Port"
    uv run -m oscmcp
} -ArgumentList $ScriptRoot, $BackendPort

# Readiness poll
Write-Host "Waiting for backend on port $BackendPort..." -ForegroundColor Yellow
for ($i = 0; $i -lt 60; $i++) {
    try {
        $r = Invoke-WebRequest -Uri "http://127.0.0.1:$BackendPort/api/v1/health" -TimeoutSec 2 -UseBasicParsing -ErrorAction SilentlyContinue
        if ($r.StatusCode -eq 200) { Write-Host "Backend ready OK" -ForegroundColor Green; break }
    } catch {}
    Start-Sleep 1
}
if ($SkipFrontend) { return }

# Start frontend
$WebRoot = Join-Path $ScriptRoot "web_sota"
Start-Process -NoNewWindow -FilePath "npx" -ArgumentList "vite --port $FrontendPort --host" -WorkingDirectory $WebRoot

# Auto-open browser
if (-not $NoBrowser) {
    Start-Sleep 2
    Start-Process "http://127.0.0.1:$FrontendPort"
}

# Keep-alive
while ($true) {
    if ($BackendJob.State -eq "Completed" -or $BackendJob.State -eq "Failed") {
        Receive-Job $BackendJob
        break
    }
    Start-Sleep 2
}

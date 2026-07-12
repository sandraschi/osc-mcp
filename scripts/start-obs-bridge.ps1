<#
.SYNOPSIS
    Launches the OSC-to-OBS WebSocket Bridge.
.DESCRIPTION
    Standard PowerShell script to spin up the python bridge under uv environment.
.PARAMETER Port
    OSC UDP receiver port (default: 7000)
.PARAMETER Host
    OSC UDP receiver host (default: 127.0.0.1)
.PARAMETER ObsHost
    OBS WebSocket server host (default: 127.0.0.1)
.PARAMETER ObsPort
    OBS WebSocket server port (default: 4455)
.PARAMETER ObsPassword
    OBS WebSocket password
.EXAMPLE
    .\scripts\start-obs-bridge.ps1 -ObsPassword "my_secret_password"
#>
param (
    [string]$HostIP = "127.0.0.1",
    [int]$Port = 7000,
    [string]$ObsHost = "127.0.0.1",
    [int]$ObsPort = 4455,
    [string]$ObsPassword = ""
)

Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "   OSC-to-OBS WebSocket Bridge Launcher      " -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan

# Check if password is set via environment variable if parameter is empty
if ([string]::IsNullOrEmpty($ObsPassword)) {
    if ([string]::IsNullOrEmpty($env:OBS_WEBSOCKET_PASSWORD)) {
        Write-Host "[info] No password passed. Connecting unauthenticated." -ForegroundColor Yellow
    } else {
        Write-Host "[info] Using password from OBS_WEBSOCKET_PASSWORD environment variable." -ForegroundColor Green
        $ObsPassword = $env:OBS_WEBSOCKET_PASSWORD
    }
}

$ArgsList = @("--host", $HostIP, "--port", $Port, "--obs-host", $ObsHost, "--obs-port", $ObsPort)

if (-not [string]::IsNullOrEmpty($ObsPassword)) {
    $ArgsList += @("--obs-password", $ObsPassword)
}

Write-Host "[info] Starting bridge (OSC: $HostIP`:$Port, OBS: $ObsHost`:$ObsPort)..." -ForegroundColor Gray
Write-Host "Press Ctrl+C to terminate the bridge." -ForegroundColor Yellow
Write-Host ""

# Run via uv
uv run python scripts/obs_websocket_bridge.py $ArgsList

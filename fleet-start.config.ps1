# Per-repo fleet start config for osc-mcp
# Edit ports/backend target here - start.ps1 is fleet-standard.
@{
    Name         = 'osc-mcp'
    BackendPort  = 10767
    FrontendPort = 10766
    HealthPath   = '/health'
    WebRoot      = 'D:\Dev\repos\osc-mcp\web_sota'
    Backend = @{
        Kind          = 'uvicorn'
        UvicornTarget = 'oscmcp.api.main:app'
        SyncExtras    = @('dev')
        Env           = @{ WEB_PORT = '10767' }
    }
    Frontend = @{
        Kind           = 'vite-npm'
        PackageManager = 'npm'
        PortEnvVar     = 'VITE_PORT'
        ApiTargetEnv   = 'VITE_API_TARGET'
    }
}

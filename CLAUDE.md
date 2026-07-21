# osc-mcp — Agent Instructions

FastMCP 3.4 OSC server for audio/visual application control.

## Quick Start
```powershell
uv run python -m oscmcp          # stdio mode
uv run python -m oscmcp --http   # HTTP mode on :10767
```

## Key Files
- `src/oscmcp/server.py` — main FastMCP server and tool declarations
- `src/oscmcp/api/main.py` — FastAPI REST wrapper (ports 10767)
- `src/oscmcp/apps/` — app-specific portmanteau tools (Ableton, VCV, TD, etc.)
- `run_server.py` — PyInstaller dual-transport entry point
- `web_sota/` — React frontend (Vite, :10766)
- `native/` — Tauri 2.0 NSIS desktop wrapper

## Commands
```powershell
just lint          # ruff + biome
just fix           # ruff --fix + ruff format + biome write
just gates-green   # lint + typecheck
```

## Standards
- Ports: BE :10767, FE :10766 (WEBAPP_PORTS.md)
- All tools return `{"success": bool, "message": str, "data": ...}`
- Use `Annotated[T, Field(description="...")]` for params (no Args: blocks)
- Prefab UI for list/status/stats tools via `@mcp.tool(app=True)`
- CORS: explicit origins + Tailscale/LAN regex (not `["*"]`)

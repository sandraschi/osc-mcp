# Configuration — osc-mcp

## Environment

Copy `.env.example` → `.env` (never commit `.env`).

| Variable | Default | Purpose |
|---|---|---|
| `OSC_MCP_HOST` | `127.0.0.1` | Backend bind |
| `OSC_MCP_PORT` | `10767` | Backend HTTP port (must match `start.ps1` `BackendPort` + Vite `API_BASE`) |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Local LLM sampler (optional) |
| `OBS_WS_HOST` | `127.0.0.1` | OBS WebSockets host |
| `OBS_WS_PORT` | `4455` | OBS WebSockets port |
| `OBS_WS_PASSWORD` | — | OBS WebSockets password (set in OBS) |

## Ports (fleet registry `WEBAPP_PORTS.md`)

- Backend `10767` — FastAPI (`src/oscmcp/api/main.py`, `src/oscmcp/server.py` `http_app()`)
- Frontend `10766` — Vite (strictPort, host `127.0.0.1`, `allowedHosts: [goliath]`)

Forbidden on fleet: `3000,5000,5173,8000,8080`. See `vite.config.ts` and `start.ps1`.

## Wrapped apps

All apps are external — install them separately, enable OSC input, then point the matching `*_manager` tool at `host:port`. See `docs/ONBOARDING.md` for per-app install, cost, and enablement checklist, and `GET /api/v1/onboarding/apps` for live `installed/running` detection.

## CORS

`src/oscmcp/api/main.py` `CORSMiddleware` allow_origins `http://localhost:10766`, `http://127.0.0.1:10766`, `http://localhost:10767`, `http://127.0.0.1:10767`, `tauri.localhost` plus `allow_origin_regex` for `*.ts.net` / Tailscale / LAN. Tauri CSP in `native/tauri.conf.json` mirrors this (`connect-src 'self' http://127.0.0.1:10767 ipc: http://ipc.localhost`).

## Tauri

`native/tauri.conf.json`: `frontendDist ../web_sota/dist`, `bundle targets nsis`, `resources [osc-mcp-backend.exe, .env.example]`, `windows.webviewInstallMode skip`, `nsis installMode currentUser + hooks.nsh`. Icons at `native/icons/icon.png|ico` (256×256). See `docs/TAURI_BUILD.md` (BUILD_LOG.md after a build).

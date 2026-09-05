# Development — osc-mcp

## Stack

- Python `3.12+`, `uv` (`pyproject.toml`), `ruff` (`line-length 120`), `mypy` (`strict`), `pytest` + `pytest-asyncio` (`asyncio_mode auto`)
- FastMCP `>=3.4.4,<4` (`src/oscmcp/server.py` `FastMCP("OSC-MCP")`, lifespan, prompts, Prefab `app=True`)
- Frontend `web_sota` (React 19, Vite 7, TS 5.9, Tailwind 3.4, Radix, Zustand 5, TanStack Query, `tsc --noEmit`, `biome ci`)

## Commands

```powershell
uv sync --extra dev --group dev   # deps
uv run ruff check src/ --fix
uv run ruff format src/
uv run pytest tests/ -v
just lint                          # ruff + biome ci web_sota
just fix                           # ruff --fix + biome --write
just types                         # tsc --noEmit in web_sota
just gates-green                   # lint + types + pytest
just serve                         # uv run python -m oscmcp (stdio) / uvicorn oscmcp.server:app --port 10767
.\start.ps1                        # backend 10767 + frontend 10766 + health poll + auto-browser
```

## Source map

- `src/oscmcp/server.py` — 47 tools, 6 Prefab cards (`DataTable key/header/rows`), `sampling.py` `ctx.sample`, `@server.lifespan`, `@server.prompt`
- `src/oscmcp/mcp_server.py` — legacy + per-app managers (`ableton/vcv/touchdesigner/...` portmanteaux + dual `send_osc`/`send_osc_message` code paths)
- `src/oscmcp/apps/` — `obs.py`, `qlab.py`, `vrchat.py`, `midibridge.py`, `oscquery.py` (7 dead files removed 2026-09)
- `src/oscmcp/api/main.py` — FastAPI + `GET /api/v1/health|stats|diagnostics|capabilities` + `POST /tools/call`
- `src/oscmcp/app_detect.py` — install/running detection for 10 wrapped apps (glob-versioned paths)

## Testing

`tests/test_tool_registration.py` gates the 2026-09-04 regression (11 managers reachable + Prefab no-crash). CUA smoke: `tests/cua/` (Tauri `pywinauto` NSIS) + Playwright `web_sota/e2e/` (see `standards/rules/cua_*`).

## Onboarding

`GET /api/v1/onboarding/apps` + `web_sota/src/components/AppsOnboarding.tsx` (`data-testid apps-onboarding`, `onboarding-app-{key}`) + `web_sota/src/pages/dashboard.tsx` hero CTA (`data-testid onboarding-cue`) + `MOCK`-until-onboarded banner (`mock-banner`). See `standards/ONBOARDING_STANDARD.md`.

Onboarding: N/A rationale — *not applicable*: every wrapped app is optional external; the server itself requires no account/wrappee. However `docs/ONBOARDING.md` is shipped because first-timer joy depends on external app OSC enablement.

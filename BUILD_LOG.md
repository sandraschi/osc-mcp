# BUILD_LOG — osc-mcp

## 2026-09-05 — 0.3.3 SOTA pack (no binary built — hygiene pass)

- **Tauri `native/build.ps1`** already fleet-SOTA: gates `tsc --noEmit && npm run build`, patches `fastmcp` metadata fallback (`PackageNotFoundError` → `0.0.0` fallback), `uv run pyinstaller osc-mcp-backend.spec`, copies `dist/osc-mcp-backend.exe → native/resources/osc-mcp-backend.exe + native/binaries/osc-mcp-backend-x86_64-pc-windows-msvc.exe`, bundles `.env.example` not `.env`, then `npx @tauri-apps/cli build --bundles nsis` with `currentUser + skip webviewInstallMode`. No change needed — verified `resources` and `binaries` both gitignored, `tauri.conf.json` CSP correct (`connect-src 'self' http://127.0.0.1:10767 ipc: http://ipc.localhost`).
- **Version sync** — `pyproject.toml 0.3.3`, `mcpb/manifest.json 0.3.3`, `native/tauri.conf.json 0.1.0→0.3.3`, `glama.json tools 47` (was 25, now live `server.list_tools()` count). Root `manifest.json` was CMS fiction — rewritten to `0.2` SOTA with 47 real tool descriptions.
- **Icon** — regenerated `assets/icon.png` + `mcpb/assets/icon.png` 256×256 (7840 bytes) — previous was 2203-byte placeholder.
- **Prompts 3-4-100** — `system.md 3245w`, `user.md 4238w`, `examples.json 105` (verified via `Word-Count` split + JSON length). Mirrored `assets/prompts → mcpb/assets/prompts`.
- **.mcpbignore** — added at root + `mcpb/` (covers `.venv/`, `node_modules/`, `__pycache__/`, `tests/`, `dist/`, `*.bak`, `target/`, `web_sota/dist/`). Previously missing at both locations — without this `mcpb pack` reported `ignored files: 0` and staged `__pycache__`.
- **`scripts/mcpb-pack.ps1`** — fresh wipe+recopy `src/oscmcp → mcpb/src/oscmcp` (preserve package dir), strip `__pycache__/*.pyc/*.bak`, ensure `.mcpbignore` at pack root, import-check `oscmcp.server` inside `mcpb/src` only (`PYTHONDONTWRITEBYTECODE=1` guard future).
- **Previous build — 0.3.2 (2026-07-21)** — Fixed CORS/`*` → explicit fleet origins, `uvicorn.Server` on `mcp.http_app()`, `build.ps1` multi-layer `free_port()` + `backend-status ready` emit, `.env.example` bundling, `.gitignore` `*.mcpb`/`target/`/`*.bak` expansion. See `CHANGELOG.md [0.3.2]`.

To actually produce an NSIS installer now: `just build-native` (runs `native/build.ps1` — `tsc` gate → frontend `vite build` → PyInstaller → embed → `tauri build nsis`).

## Verification (pre-push 2026-09-05)

- `uv run ruff check src/` — `All checks passed!`
- `uv run ruff format --check src/` — `34 files already formatted`
- `uv run pytest tests/ -q` — `47 passed, 3 skipped`
- `cd web_sota; npx tsc --noEmit` — `0 errors`
- `cd web_sota; npx @biomejs/biome ci .` — `0 errors` (after `useCallback` fixes; previously 3 `useExhaustiveDependencies`)
- `uv run python -c "from oscmcp.server import server; ..."`
  47 tools enumerated — `manifest.json` tool table regenerated from this.

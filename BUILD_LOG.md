# BUILD_LOG — osc-mcp

## 2026-09-05 (later) — 0.3.3 first actual NSIS build — 4 real bugs found and fixed

The hygiene pass below claimed `build.ps1` was "already fleet-SOTA" but that was
never verified against a real build. Actually running it surfaced real,
build-blocking bugs — a reminder that "reads correct" and "builds correct"
are different claims.

- **`native/build.ps1` used `uv run pyinstaller`** — the exact documented
  fleet anti-pattern (TAURI_PRODUCTION_PITFALLS.md #E/#13): can silently
  resolve to the isolated `uv tool` environment instead of the project venv.
  Fixed to call `.venv\Scripts\pyinstaller.exe` directly, with the
  auto-install-if-missing + stale-exe-cleanup pattern from the standard.
- **`osc-mcp-backend.spec` had a UTF-8 BOM** at byte 0 (classic
  `Set-Content -Encoding UTF8` fleet gotcha) — stripped.
- **`osc-mcp-backend.spec` was missing `mcp`/`fastmcp` from `copy_metadata`**
  — both call `importlib.metadata.version()` at import time; without their
  dist-info the frozen exe crashes with `PackageNotFoundError`. This is the
  single most-repeated bug across fleet Tauri postmortems (calibre, plex,
  virtualization-mcp, qcad-mcp all hit variants of it) and was present here
  too. Added `mcp`, `fastmcp`, `cachetools` to the metadata-preserve list;
  added `cachetools`, `joserfc`/`joserfc.jwk`/`joserfc.jwt`, and
  `collect_submodules` for `key_value`/`pydantic` to hiddenimports (FastMCP
  mount + 3.4+ JWT chain). A first attempt at also `collect_all("cachetools")`
  crashed `EXE()` with `ValueError: not enough values to unpack (expected 3,
  got 2)` — `collect_all` returns 2-tuples for datas/binaries, not the
  3-tuple TOC format `Analysis` produces; removed, unnecessary since
  cachetools is pure-Python (metadata + hiddenimport alone is sufficient).
- **`run_server.py`**: added `_datetime` eager import alongside the existing
  `_strptime`; added `import mcp.types` eager import before `fastmcp` touches
  it; added a frozen-mode guard for `console=False` leaving `sys.stderr as
  None` (uvicorn's logging setup calls `.isatty()` unconditionally and
  crashes with `AttributeError` otherwise) via a tiny null-stream shim.
- **`native/tauri.conf.json`**: added `https://library.vcvrack.com` to the
  CSP `img-src` — the new VCV Module Library page's screenshot thumbnails
  would otherwise be silently blocked in the production WebView (works fine
  in dev, since CSP isn't enforced there — exactly the dev-vs-prod mismatch
  class of bug this standard exists to catch). Also attempted
  `createDesktopShortcut`/`createStartMenuShortcut` per the standard's own
  NSIS checklist — **the real Tauri v2 NSIS config schema (fetched live from
  `schema.tauri.app/config/2`) has no such fields** (`additionalProperties:
  false`; real fields are `template`, `installMode`, `installerHooks`,
  `compression`, `startMenuFolder`, etc.) — reverted; that checklist item is
  stale for this Tauri version.

**Result**: full build succeeded. `OSC MCP_0.3.3_x64-setup.exe`, 35.9 MB.
Sidecar smoke test (standalone `osc-mcp-backend.exe`, `PORT=18768`): `/health`,
`/api/v1/vcv-library/status` (real SQLite-backed data, 4,468 modules), and
`/api/v1/diagnostics` (47 tools) all answered correctly; stderr clean of
every documented crash signature (`cachetools`, `isatty`, `webapp/backend`,
`_strptime`, `Traceback`, `PackageNotFoundError`).

**Not done this pass**: full Phase 6 install-and-verify (actually running the
NSIS installer, checking Start Menu/shortcuts, `%LOCALAPPDATA%` logs) — only
the sidecar smoke test was run. MCPB packaging (Phase 4) not attempted.

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

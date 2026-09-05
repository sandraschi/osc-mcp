# Troubleshooting — osc-mcp

## Silent no-op (most common)

OSC is UDP fire-and-forget — a `status: success` from `send_osc_message` means the datagram hit the OS, not that the app acted. Check: is the app running, is its OSC input enabled on the expected port (see `docs/ONBOARDING.md` per-app bullets), is the firewall open for UDP, and (Ableton = AbletonOSC installed+enabled in Link/Tempo/MIDI; VCV Rack = OSCelot Send/Receive toggles ON, send twice — first types slot, second applies value). Verify via read-back: `ableton_manager get_status`, `show_recent_messages`, or visual check.

## By app

- **Ableton Live** — No native OSC. Symptom: success but nothing moves → check Remote Scripts folder for AbletonOSC and controller surface enabled, then restart Live.
- **VCV Rack / OSCelot** — Only `/fader,/encoder,/button` with mapping-slot Id are implemented. `/param /cv /light /midi/* /transport/*` return `UNSUPPORTED_OPERATION`. Symptom: knob doesn't move until second identical send → correct per OSCelot `processOscMessage`, not a bug. Symptom: nothing at all → Send/Receive OFF by default.
- **Resolume** — Wrong path `/composition/layers/N/opacity` → use `/composition/layers/N/video/opacity`. Demo blacks frame periodically (paid license required for clean output).
- **SuperCollider** — Wrong port `57120` hits nothing; `scsynth` is `57110` (sclang is `57120`). Symptom: no reply → boot `scsynth`.
- **QLab** — `macOS only` on this host is `testable_here: false` — do not troubleshoot on Windows.
- **TouchDesigner** — Needs `OSC In CHOP/DAT` on the exact port/path. Symptom: no value → check In CHOP address ` /touch/in/*` vs `/chan1`.
- **Resolume/QLab/Max trials** — real vendor caps (Resolume black frame, QLab cue cap/watermark, Max 30-day trial).

## Backend offline (`GET /api/v1/health fails`) — `Dashboard` shows Offline

Run `.\start.ps1` (clears zombie ports 10766/10767, polls `/api/v1/health`, hosts Vite). Or `uv run uvicorn oscmcp.api.main:app --port 10767` + `npx vite --port 10766 --host 127.0.0.1` in `web_sota`. Check `netstat -ano | findstr 10767` for zombie PIDs.

## Build failures

- `tsc --noEmit` red → fix TS before `native/build.ps1` (it gates on this).
- `native/build.ps1` fastmcp `PackageNotFoundError` → the script patches `.venv/Lib/site-packages/fastmcp/__init__.py` fallback; if you replaced the venv, reinstall `fastmcp` then rebuild.
- Bundle shows stale code → run `just mcpb-pack` (wipes+recopies `src/<pkg> → mcpb/src/<pkg>` before `mcpb pack`; never edit `mcpb/src`).

## Verification

```powershell
uv run ruff check src/ --fix
uv run ruff format src/
uv run pytest tests/ -v          # includes test_tool_registration wiring+Prefab guard
cd web_sota; npx tsc --noEmit; npx @biomejs/biome ci .
```

Full SOTA verification: see `standards/VERIFICATION_STANDARDS.md`.

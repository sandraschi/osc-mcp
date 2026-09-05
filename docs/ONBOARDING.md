# Onboarding — osc-mcp

## What this is for

osc-mcp lets an AI agent (or the bundled dashboard) send and receive OSC (Open Sound
Control) messages to/from creative and AV applications — Ableton Live, TouchDesigner,
VRChat, VCV Rack, SuperCollider, Max/MSP, Resolume, QLab, Pure Data — plus a
MIDI-to-OSC bridge and an OBS Studio WebSocket bridge. It does not install, license,
or replace any of these apps. Each one is a separate host app you install and run
yourself; osc-mcp only talks to it over the network once it's running and configured
to speak OSC.

Check `GET /api/v1/onboarding/apps` (or the Dashboard) at any time to see install and
running status for every app below on the machine osc-mcp is running on.

## Cost and accounts (money / CC)

| App | Account needed? | Free tier? | Credit card? | Ongoing cost |
|---|---|---|---|---|
| Ableton Live | No | No — 90-day trial only | No for trial | Full purchase required after trial |
| TouchDesigner | No | Yes — free non-commercial license | No | Free for non-commercial use |
| VRChat | Yes (free Steam/VRChat account) | Yes, fully free | No | Free |
| VCV Rack | No | Yes — Rack 2 Free edition | No | Free (paid plugin packs optional) |
| SuperCollider | No | Yes, fully free/open-source | No | Free |
| Max/MSP | No | No — 30-day full trial only | No for trial | Full purchase required after trial |
| Resolume Avenue/Arena | No | Demo mode (unlimited time, no save, periodic black frame) | No | Full purchase to remove demo limits |
| QLab | No | Free to run (watermarked, limited cue count) | No | Paid license to remove watermark/limits |
| Pure Data | No | Yes, fully free/open-source | No | Free |
| OBS Studio (bridge) | No | Yes, fully free/open-source | No | Free |

Nobody bills through osc-mcp itself — every cost above is the app vendor's own
pricing, unrelated to this MCP server.

## Prerequisites outside this repo

- **The host app itself**, installed and reachable on the network osc-mcp runs on
  (same machine by default; LAN/Tailscale also work since each tool takes a `host`
  parameter).
- **Each app's own OSC configuration enabled** — OSC is rarely on by default:
  - *Ableton Live* has **no native OSC** at all — you must separately install the
    third-party [AbletonOSC](https://github.com/ideoforms/AbletonOSC) remote script
    into Live's Remote Scripts folder and enable it in
    Preferences → Link/Tempo/MIDI. Without this, `ableton_manager` sends land nowhere
    and OSC is a complete no-op with no error.
  - *TouchDesigner* needs an **OSC In CHOP or OSC In DAT** placed in the project,
    listening on the port you configure.
  - *VRChat*: Settings → OSC → **Enabled**.
  - *VCV Rack* has no native OSC either. Install **OSCelot** (TheModularMind, via
    the VCV Library — needs a free VCV account) and patch it in, then map
    parameters using OSCelot's **direct `/param` mode** (click Map, click the
    knob, note the Module ID/Param ID it shows) rather than its controller-slot
    fader/button/encoder mode - `vcv_manager`'s addressing
    (`/param [module_id, param_id, value]`) matches OSCelot's direct-param
    format exactly. See `docs/OSCELOT_MAPPING_GUIDE.md` for the full click-through
    and `docs/OSCELOT_UI_MAPPING_EXPLAINED.md` for how the slot-type-by-address
    behavior works. `trowaSoft`'s cvOSCcv module family is a documented
    alternative with a different address scheme - not what this repo's
    `vcv_manager` currently assumes, so stick with OSCelot unless you're willing
    to adjust the addresses yourself.
  - *SuperCollider*: run `scsynth` (the audio server) — the IDE (`scide`) alone does
    not answer OSC.
  - *Max/MSP*: patch `udpreceive`/`udpsend` or `[oscformat]`/`[oscparse]` objects.
  - *Resolume*: OSC input is on by default on port 7000; check Preferences → OSC if
    it doesn't respond.
  - *QLab*: OSC is on by default; **macOS only** — cannot run or be tested on a
    Windows host at all, structurally, regardless of licensing.
  - *Pure Data*: patch `[netreceive]`/`[netsend]` or the OSC library objects.
  - *OBS Studio*: Tools → WebSocket Server Settings → Enable WebSocket server (built
    into OBS 28+; this is obs-websocket, not OSC).
- **Firewall**: if connecting across LAN/Tailscale rather than localhost, allow the
  relevant OSC port through Windows Firewall for both osc-mcp and the target app.

## First-timer setup steps

1. Install osc-mcp itself (`just` / see `INSTALL.md`) and start it (`just serve` or
   the desktop app).
2. Check `GET /api/v1/onboarding/apps` (or open the Dashboard) to see which of the
   apps above are already installed on this machine and which aren't.
3. For each app you actually want to control: install it (see the Cost table above
   for licensing), launch it, and enable its OSC/WebSocket input per the
   app-specific bullet above.
4. Use the matching `*_manager` MCP tool (e.g. `ableton_manager`, `vcv_manager`,
   `resolume_manager`) or the app's dashboard page, pointing at the host/port you
   configured in step 3.
5. Verify with a simple, low-risk operation first — e.g.
   `vcv_manager("get_status")`/an app-specific status/read op — before anything
   that changes state.

## Pitfalls

- **Silent no-ops are the norm here, not the exception.** OSC is fire-and-forget
  UDP — sending to a wrong port, an app that isn't listening, or (Ableton
  specifically) an app with no OSC bridge installed at all produces **no error**,
  just nothing happening. If a tool call "succeeds" but nothing changes in the app,
  check that app's OSC input is actually configured and listening.
- **Ableton Live's OSC dependency is undiscoverable from inside osc-mcp** — there is
  no native OSC in Live to detect. If `ableton_manager` calls aren't landing, the
  first thing to check is whether AbletonOSC is actually installed and enabled.
- **Resolume/QLab/Max trials/demos have real limits** — Resolume's demo periodically
  overlays a black frame, QLab caps cue count and watermarks output, Max's trial
  expires after 30 days. Fine for testing OSC control; not for production use.
- **QLab cannot run on Windows at all** — if you're on Windows, don't spend time
  troubleshooting a QLab connection; there is nothing to install here.
- **Version-numbered install paths** — apps like SuperCollider install to a
  version-specific directory (e.g. `SuperCollider-3.14.1\`). osc-mcp's detection
  handles this via glob patterns, but a portable/custom install location won't be
  auto-detected — you can still connect manually by host/port even if detection
  says "not installed."

## Sanity check

- `GET /api/v1/onboarding/apps` shows `"installed": true` for an app you've
  installed, with a real `installed_path`.
- `"running": true` once you've actually launched it.
- A simple read-only `*_manager` tool call against that app returns real data (not
  a generic error) once its OSC input is configured.
- For OBS specifically: `obs_manager` status calls return real OBS state once
  the WebSocket server is enabled in OBS.

## Declared doubles

None. There is no mock/sample-data mode in this repo's webapp for these
integrations — a tool call against an app that isn't running or isn't OSC-configured
either errors cleanly (where the underlying transport can detect that) or silently
does nothing (inherent to fire-and-forget OSC/UDP, not a design choice osc-mcp makes).

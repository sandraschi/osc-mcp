# OBS Studio Expert

## What is OBS Studio

Free, open-source software for **live streaming and screen/video
recording** — it combines multiple sources (cameras, screen capture,
images, browser overlays) into scenes you switch between during a
broadcast or recording.

**Core features:** scene/source composition and live switching, streaming
to platforms like Twitch/YouTube, local recording, per-source audio
mixing, a large plugin ecosystem, and remote control via its own
`obs-websocket` API — which is the only reason it appears in an
"OSC-MCP" server at all, since (unlike QLab or VRChat) it has no OSC of
its own.

You are an expert on controlling OBS Studio via `osc-mcp`'s `obs_manager`
tool. Read this before touching anything OBS-related — the architecture
here is different from every other app in this fleet in one crucial way:

**OBS Studio has no OSC support of any kind, native or otherwise.** There
is no OSC listener anywhere in stock OBS. What OBS *does* have, built in
since OBS Studio 28 (no plugin install needed), is **obs-websocket v5** —
a JSON-over-WebSocket RPC protocol, not OSC at all. Every `obs_manager`
call in this repo is OSC on the wire only as far as a **separate bridge
process this repo also ships** (`scripts/obs_websocket_bridge.py`); that
bridge is the thing that actually speaks obs-websocket to OBS. If you
forget this, you will misdiagnose "obs_manager isn't doing anything" as an
OSC problem when it's almost always "the bridge script isn't running."

## Why an "OSC-MCP" server touches a non-OSC protocol at all

This project's whole premise is unifying disparate creative-app control
protocols under one MCP surface. OBS is included because it's a common
part of the same audio/visual production chain as everything else here
(QLab, Ableton, VCV Rack) — but since OBS never speaks OSC, the only way
to fit it into an "OSC-MCP" tool is to run something that translates OSC
in one side and obs-websocket JSON out the other. That's exactly what
`scripts/obs_websocket_bridge.py` is: a wrapper/adapter, not a
protocol-native integration. `obs_manager` itself is unaware of any of
this — it just sends OSC packets to a UDP port and trusts something is
listening there and doing the translation.

## The chain: obs_manager → OSC/UDP → bridge script → obs-websocket/JSON → OBS

```
obs_manager()  --OSC/UDP (port 7000)-->  obs_websocket_bridge.py  --WebSocket/JSON (port 4455)-->  OBS Studio (obs-websocket v5, built into OBS 28+)
```

Setup, in order:

1. **OBS Studio 28 or newer** — obs-websocket v5 ships built in; nothing
   to install for the OBS side. Enable it: OBS menu → Tools →
   "WebSocket Server Settings" → check "Enable WebSocket server" (per
   `docs/ONBOARDING.md`). Note the port (default **4455**) and, if a
   password is set, the password.
2. **Start this repo's bridge script** — it is a separate, long-running
   Python process, not something `obs_manager` launches for you:
   ```powershell
   .\scripts\start-obs-bridge.ps1 -ObsPassword "your_obs_websocket_password"
   ```
   This starts a UDP OSC listener on **port 7000** (default) and connects
   out to OBS's WebSocket server on **port 4455** (default), performing
   the SHA256-based challenge/response auth handshake obs-websocket v5
   requires when a password is set (`scripts/obs_websocket_bridge.py`,
   `compute_auth_response`).
3. **Only then** does calling `obs_manager(...)` (which sends OSC to
   127.0.0.1:7000 by default) do anything in OBS. If the bridge isn't
   running, the OSC packets go into a UDP void — no error surfaces
   anywhere, in `obs_manager`'s return value or otherwise, because UDP is
   connectionless. This is the single most likely cause of "nothing
   happened."

There is also a documented alternative most users are *not* using here:
native C++ plugins that give OBS a real UDP OSC listener directly
(`OBSC` by benaclejames, `ObSC` by CarloCattano — see
`docs/OBS_PLUGINS_GUIDE.md`). This repo does not depend on either; it
ships its own Python bridge instead specifically to avoid the plugin
fragility problem (native OBS plugins break across OBS version upgrades).

## The real obs-websocket v5 protocol (what the bridge translates into)

Verified against `github.com/obsproject/obs-websocket`'s own generated
protocol docs:

| Bridge OSC address it listens for | Real obs-websocket v5 RequestType | Real request fields |
|---|---|---|
| `/scene <scene_name>` | `SetCurrentProgramScene` | `sceneName` (or `sceneUuid`) |
| `/mute <source_name>` | `ToggleInputMute` | `inputName` (or `inputUuid`) — toggles, does not set an explicit on/off state |
| `/volume <source_name> <volume>` | `SetInputVolume` | `inputVolumeMul` (linear multiplier; obs-websocket also separately supports `inputVolumeDb` but the bridge only ever sends the multiplier field) |
| `/stream/start` | `StartStream` | none |
| `/stream/stop` | `StopStream` | none |
| `/obs/request <request_type> [json_data]` | whatever `request_type` names, passed through | arbitrary JSON, forwarded verbatim — an escape hatch for any real obs-websocket request not otherwise wired up |

obs-websocket also defines `SetInputMute` (explicit on/off, distinct from
the toggle-only `ToggleInputMute` the bridge uses) and `ToggleStream` —
neither is used by this bridge or by `obs_manager`.

## `obs_manager` — what osc-mcp actually implements

```python
obs_manager(operation, scene_name=None, source_name=None, volume=None,
            host="127.0.0.1", port=7000)
```

| Operation | Sends (OSC, to the bridge) | Bridge forwards as | Notes |
|---|---|---|---|
| `switch_scene` | `/scene, scene_name` | `SetCurrentProgramScene` | Requires `scene_name` |
| `toggle_mute` | `/mute, source_name` | `ToggleInputMute` | Requires `source_name`; toggles, cannot force mute on or off |
| `set_volume` | `/volume, source_name, volume` | `SetInputVolume` | Requires `source_name` + `volume` |
| `start_stream` | `/stream/start` | `StartStream` | |
| `stop_stream` | `/stream/stop` | `StopStream` | |

The default port (7000) in `obs_manager`'s signature and
`OBSOSC.DEFAULT_PORT` in `src/oscmcp/apps/obs.py` matches the bridge
script's own default OSC listen port — that part is internally
consistent. `app_detect.py`'s entry for `key="obs"` deliberately sets
`default_osc_port=None` (not 7000) precisely because OBS itself has no
OSC port at all; 7000 is the bridge's port, not OBS's, and conflating the
two is exactly the kind of error `app_detect.py` is trying to avoid.

## Known gaps

Fixed during this pass:
- ~~`obs_manager`'s docstring never mentioned the bridge~~ — now states
  plainly that OBS has no native OSC, names the bridge script and its
  real obs-websocket request mappings, and warns that every call is a
  silent no-op if the bridge isn't running.
- ~~`set_volume`'s documented range was narrower than what the bridge
  accepts~~ — docstring said "0.0 to 1.0"; the bridge actually clamps to
  0.0-2.0 (linear multiplier, 1.0 = unity gain). Now documented correctly
  as "0.0 to 2.0 (1.0 = unity gain)".

Still open:
- **No explicit set-mute, only toggle.** Neither the bridge nor
  `obs_manager` exposes obs-websocket's real `SetInputMute` (explicit
  on/off) — only `ToggleInputMute`. Calling `toggle_mute` twice in a row
  cancels itself out; there's no way to idempotently "ensure muted."
- **No scene-list, source-list, or input-list read operations.** Every
  `obs_manager` operation is a blind write — there's no way to ask OBS
  (via this tool) what scenes or sources currently exist before targeting
  one by name. A typo in `scene_name`/`source_name` fails silently at the
  obs-websocket layer in a way `obs_manager` cannot see or report (it
  returns `{"status": "success"}` once the OSC packet is sent, regardless
  of whether the bridge or OBS did anything with it).
- **The `/obs/request` escape hatch in the bridge script is not exposed by
  `obs_manager` at all.** It exists in `scripts/obs_websocket_bridge.py`
  (`osc_handle_custom_request`) as a way to reach any real obs-websocket
  request type by name with raw JSON data, but there's no `obs_manager`
  operation that sends `/obs/request` — it's only reachable by constructing
  the OSC message manually outside this tool.
- **No liveness/health check.** Neither `obs_manager` nor the bridge
  exposes a way to confirm the bridge process is actually running and
  actually connected/authenticated to OBS before sending a real command —
  confirm manually (check the bridge's own console output, which logs
  "Connected and authenticated with OBS WebSocket successfully!" on a
  successful handshake).

## Best practices

1. **Before assuming `obs_manager` is broken, confirm the bridge script
   is running** and its console shows a successful OBS WebSocket
   authentication — this is the OBS equivalent of "check Send/Receive are
   green" for VCV Rack's OSCelot.
2. **Confirm OBS's own WebSocket server is enabled** (Tools → WebSocket
   Server Settings) and get the real password from there if one is set —
   there is no way to discover it externally.
3. **Never conflate port 7000 (the bridge's OSC listen port) with port
   4455 (OBS's own obs-websocket port).** `obs_manager` only ever talks to
   7000; it never talks to OBS directly.
4. **Don't claim OBS "has OSC support"** in any user-facing explanation —
   say it has obs-websocket, and that OSC only enters the picture because
   this repo's own bridge translates it.
5. If a user needs something `obs_manager` doesn't expose (explicit
   set-mute, scene/source enumeration, arbitrary requests), point to the
   real obs-websocket v5 protocol docs and the bridge's `/obs/request`
   escape hatch rather than inventing a new OSC address that neither
   `obs_manager` nor the bridge actually implements.

## Primary sources

- `github.com/obsproject/obs-websocket/blob/master/docs/generated/protocol.md`
  — obs-websocket v5's own generated protocol reference (`SetCurrentProgramScene`,
  `ToggleInputMute`, `SetInputMute`, `SetInputVolume`'s `inputVolumeMul`/
  `inputVolumeDb`, `StartStream`, `StopStream`, `ToggleStream`)
- `scripts/obs_websocket_bridge.py` (this repo) — the actual bridge
  implementation: OSC addresses it listens for, the obs-websocket auth
  handshake, and the volume clamp range
- `scripts/start-obs-bridge.ps1` (this repo) — launcher, default ports
- `src/oscmcp/apps/obs.py` (`OBSOSC`) — what `obs_manager` actually sends
- `src/oscmcp/app_detect.py` (`key="obs"`) — `default_osc_port=None`
  (deliberate) and the "Connects via obs-websocket, not OSC" note
- `docs/OBS_PLUGINS_GUIDE.md` (this repo) — native-plugin alternatives
  (OBSC, ObSC) this repo does not use, and why the bridge approach was
  chosen instead
- `docs/ONBOARDING.md` — OBS section: enabling the WebSocket server in
  OBS's own Tools menu
- README.md, "OBS Studio WebSockets Bridge" section — the bridge launch
  command and its default ports

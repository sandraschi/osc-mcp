# OSC-MCP Expert

You are an expert on the OSC-MCP server — a FastMCP 3.4+ server that bridges
the Open Sound Control (OSC) protocol with AI agent workflows. OSC-MCP lets you
send, receive, and orchestrate OSC messages with Ableton Live, TouchDesigner,
VRChat, QLab, OBS Studio, Max/MSP, SuperCollider, VCV Rack, Pure Data, Resolume,
and any other OSC-capable application on the local network. REAPER also gets
a narrow cross-app-sync mention (`skills/reaper-expert/`) — for full REAPER
automation, the fleet's dedicated `reaper-mcp` server is the right tool, not
this one.

## Core Concepts

OSC (Open Sound Control) is a UDP-based protocol for real-time communication
between media applications. Messages consist of an address pattern (e.g.
`/volume`, `/live/track/1/mute`) and a list of typed values.

OSC-MCP provides:
- Direct message send/receive over UDP
- AI-assisted workflow generation via MCP sampling
- Reactive triggers (OSC-in → tool-out)
- OSCQuery service discovery
- Virtual MIDI bridge (MIDI ↔ OSC translation)
- Application-specific control surfaces (VRChat, OBS, QLab)
- Subnet scanning for active OSC devices

## Core Tools

### send_osc_message(host, port, address, values)
Send a raw OSC message to any UDP endpoint. Values are auto-typed.

### start_osc_listener(port, address="0.0.0.0")
Start a background OSC server on the given port. Incoming messages are logged and
routed through the reactive trigger engine.

### test_osc_echo(port=9000)
Full connectivity test: starts a listener, sends a test message, and validates
the round-trip (with optional LLM analysis when sampling is available).

## Workflow Tools

### generate_osc_workflow(workflow_description, target_application, host, port)
Uses LLM sampling (FastMCP ctx.sample) to design a multi-step OSC automation
sequence from a natural-language description. Returns structured step data.

### execute_osc_workflow(workflow_data, validate_first=True)
Runs a previously generated workflow with optional pre-execution validation.
Validates timing, addresses, and value ranges before sending.

### save_workflow_descriptor(workflow_id, title, description, steps)
Persist a workflow as an Arazzo YAML descriptor in the workflows directory.

### list_arazzo_workflows()
List all saved Arazzo workflow descriptors.

## Discovery Tools

### scan_subnet_osc(subnet_prefix, ports, protocol="udp")
Scan a subnet prefix (e.g. "192.168.1") for hosts responding on common OSC
ports. Reports active IPs and responding ports.

### oscquery_list_services()
List OSCQuery devices discovered on the local network via mDNS/DNS-SD.

### oscquery_get_parameters(service_name)
Fetch the full OSC parameter tree from a named OSCQuery device.

## Reactive Trigger System

OSC-MCP can listen for incoming OSC messages and automatically execute tools
when a pattern matches.

### register_reactive_trigger(address_pattern, target_tool, args_template)
Map an OSC address glob pattern (e.g. `/live/beat`, `/vco/*`) to a tool call.
The args_template supports variable substitution (`$value`, `$0`, `$1`).

### get_reactive_triggers()
List all registered reactive triggers.

### remove_reactive_trigger(address_pattern)
Remove a reactive trigger by pattern.

## Application-Specific Tools

### obs_manager(operation, scene_name, source_name, volume, host, port)
Control OBS Studio: switch_scene, toggle_mute, set_volume, start_stream,
stop_stream. Default port 7000.

### qlab_manager(operation, cue_id, slider_index, level, host, port)
Control Figure 53 QLab: go, stop, panic, trigger_cue, set_slider_level.
Default port 53000.

### VRChat Tools
- trigger_vrchat_haptic_lfo(device, pattern, duration, frequency_hz) — haptic
  feedback with LFO modulation (sine/sawtooth/square).
- set_vrchat_expression(expression, intensity) — set Unified Expression
  parameters (confirmed real names: EyeLidLeft, JawOpen; "Smile" is not
  a real Unified Expressions name, see `skills/vrchat-expert/`).

## Prefab App Tools (Rich In-Chat UI)

These tools render interactive data tables in MCP hosts that support Apps:

- show_active_mappings() — MIDI and reactive trigger mapping table
- show_discovered_devices() — OSCQuery device table
- show_recent_messages(port, limit) — recent OSC message log
- show_available_workflows() — Arazzo workflow table
- show_control_faders() — interactive fader control surface
- show_osc_oscilloscope() — simulated signal activity monitor

## MIDI Bridge

The server exposes virtual MIDI ↔ OSC translation via `register_midi_tools()`.
MIDI CC messages on a virtual port are bidirectionally mapped to OSC addresses.

## Best Practices

1. **Start with test_osc_echo** — always verify UDP connectivity before building
   complex workflows.
2. **Use generate_osc_workflow** for multi-step sequences — it handles timing,
   validation, and error recovery better than manual step-by-step.
3. **Keep listeners scoped** — start a listener on the target port first, then
   send messages. Listeners are lightweight but each consumes a UDP socket.
4. **OSCQuery before hardcoding** — use oscquery_list_services to discover
   parameter trees dynamically instead of hardcoding addresses.
5. **Use reactive triggers for live performance** — map MIDI controllers or
   application events to OSC outputs via the trigger engine.
6. **Subnet scan for unknown networks** — if devices aren't responding, scan
   the subnet to find active OSC hosts.

## Configuration

| Env Variable | Default | Purpose |
|---|---|---|
| MCP_TRANSPORT | stdio | Transport mode (stdio, http, sse) |
| MCP_HOST | 127.0.0.1 | Bind address for HTTP mode |
| MCP_PORT | 10767 | Port for HTTP/SSE transport |
| MCP_PATH | /mcp | HTTP endpoint path |
| OSC_DEFAULT_HOST | 127.0.0.1 | Default OSC target host |
| OSC_DEFAULT_PORT | 9000 | Default OSC target port |

## Common Ports

Verified against `src/oscmcp/app_detect.py` (the fleet's own detection registry,
corrected after several of these were found fabricated earlier in the project's
history — see each app's dedicated skill for the full story and primary sources):

| Application | Default OSC Port | Notes |
|---|---|---|
| Ableton Live | 11000 | No native OSC — needs the third-party AbletonOSC remote script |
| TouchDesigner | 9000 | Needs an OSC In CHOP/DAT configured in the project |
| VRChat | 9000 (send), 9001 (receive) | Must be enabled in-game: Settings > OSC > Enabled |
| VCV Rack | **no fixed default** | OSCelot's receive port is fully user-configured — see `skills/vcvrack-expert/` |
| SuperCollider | 57110 | scsynth (the audio server) answers OSC — running scide alone isn't enough |
| Max/MSP | 7400 | Needs `[udpreceive]`/`[udpsend]` or CNMAT's odot package patched in — not `oscformat`/`oscparse`, those are Pure Data objects |
| Resolume | 7000 | |
| QLab | 53000 | macOS-only |
| Pure Data | 9000 | Needs `[netreceive]`/`[netsend]` or an OSC library patched in |
| OBS Studio | **not OSC** | Connects via obs-websocket, not OSC — see `docs/OBS_PLUGINS_GUIDE.md` |

For deeper per-app OSC address conventions, gotchas, and primary-source references,
see the dedicated skill for that application under `skills/{app}-expert/`.

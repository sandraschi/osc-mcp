# OSC-MCP — Open Sound Control for AI

Natural language control of audio/visual applications (Ableton Live, TouchDesigner, VRChat, VCV Rack, SuperCollider, Max/MSP, Resolume, QLab, Pure Data) through the OSC protocol.

**FastMCP 3.4** | 25+ MCP tools | Dashboard at :10766 | Backend at :10767

<p align="center">
  <img src="https://img.shields.io/badge/FastMCP-3.4-7c5cfc?style=flat-square" alt="FastMCP">
  <img src="https://img.shields.io/badge/Python-3.12+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/License-MIT-yellow?style=flat-square" alt="MIT">
  <img src="https://img.shields.io/badge/status-production-brightgreen?style=flat-square" alt="Status">
  <img src="https://img.shields.io/badge/zustand-5.0-orange?style=flat-square" alt="Zustand">
</p>

## Features

- Send OSC messages to any application (Ableton, TouchDesigner, VRChat, VCV Rack, SuperCollider, Max/MSP, Resolume, QLab, Pure Data)
- Bidirectional communication — start an OSC server, receive and buffer messages
- Application-specific portmanteau managers with 40+ operations each (TouchDesigner: COMP, CHOP, SOP, TOP, DAT, MAT)
- OSCQuery service discovery (Zeroconf/mDNS)
- MIDI-to-OSC bridge with configurable CC/note mappings
- Reactive triggers — incoming OSC patterns trigger MCP tool calls
- Arazzo workflow engine for multi-step mission descriptors
- LLM sampling via SEP-1577 for autonomous workflow generation
- SOTA web dashboard with real-time monitoring and app-specific controllers

## Quick Install

```powershell
git clone https://github.com/sandraschi/osc-mcp
cd osc-mcp
just
```

See [INSTALL.md](INSTALL.md) for manual setup and Claude Desktop configuration.

## What You Can Do

```
"Set Ableton Live tempo to 120 BPM and play"
"Start an OSC server on port 9000 to receive from TouchDesigner"
"Map MIDI CC 1 on channel 1 to /mixer/volume with range 0-127 → 0.0-1.0"
"Discover OSCQuery services on the local network"
"Synthesize a 440 Hz sine wave in SuperCollider"
```

## How It Runs

| Mode | Host App | When |
|------|----------|------|
| Headless (default) | None | Server-to-server, Claude Desktop, CI |
| Live GUI (optional) | Any OSC-enabled app | Interactive control |

## Tools

47 tools, verified against `server.list_tools()` (see `tests/test_tool_registration.py`):

| Category | Tools |
|----------|-------|
| **Core OSC** | `send_osc`, `send_osc_message`, `start_osc_server`, `start_osc_listener`, `stop_osc_server`, `get_received_messages`, `get_latest_message`, `get_osc_server_stats`, `clear_osc_message_buffer`, `test_osc_echo`, `scan_subnet_osc` |
| **Discovery** | `oscquery_list_services`, `oscquery_get_parameters` |
| **MIDI Bridge** | `get_midi_ports`, `start_midi_bridge`, `stop_midi_bridge`, `add_midi_mapping`, `get_midi_mappings` |
| **Reactive** | `register_reactive_trigger`, `get_reactive_triggers`, `remove_reactive_trigger` |
| **Managers** | `ableton_manager`, `vcv_manager`, `touchdesigner_manager`, `vrchat_manager`, `supercollider_manager`, `maxmsp_manager`, `resolume_manager`, `puredata_manager`, `audio_workflow_manager`, `osc_recorder_manager`, `music_orchestrator`, `music_loader_manager`, `obs_manager`, `qlab_manager`, `set_vrchat_expression`, `trigger_vrchat_haptic_lfo` |
| **Workflows** | `list_arazzo_workflows`, `execute_osc_workflow`, `generate_osc_workflow`, `save_workflow_descriptor` |
| **Dashboard cards** | `show_active_mappings`, `show_discovered_devices`, `show_recent_messages`, `show_available_workflows`, `show_control_faders`, `show_osc_oscilloscope` |

`send_osc`/`send_osc_message` and `start_osc_server`/`start_osc_listener` are two independent
implementations (older + newer code paths, both wired) rather than aliases — pick one per
workflow rather than mixing them for the same port/session.

## Stack

| Layer | Technology |
|-------|-----------|
| **Framework** | FastMCP 3.4 / FastAPI |
| **Runtime** | Python 3.12+ (uv) |
| **Frontend** | React 19, Vite 7, TypeScript 5.9 |
| **Styling** | Tailwind CSS 3.4, Radix UI, Lucide Icons |
| **State** | Zustand 5, TanStack React Query |
| **Desktop** | Tauri 2.0 (NSIS installer) |
| **Build** | PyInstaller, setuptools, MCPB |

## Dashboard

SOTA web interface at `http://localhost:10766` — real-time OSC monitoring, application-specific controllers, integrated chat for natural language command orchestration.

**Keyboard shortcuts:** Ctrl+L → Logs, Ctrl+H → Help, Ctrl+K → Tools, Ctrl+Scroll → Zoom

## Links

- [Installation Guide](INSTALL.md) — all install methods
- [Arazzo Workflows](docs/ARAZZO_WORKFLOWS_GUIDE.md) — multi-step mission descriptors
- [OBS Studio Guide](docs/OBS_PLUGINS_GUIDE.md) — C++ plugins, SLOBS history, VTubers, and built-in bridge setup
- [Tool Analysis](docs/APPLICATION_TOOLS_ANALYSIS.md) — comprehensive tool reference
- [Project Analysis](docs/PROJECT_ANALYSIS.md) — maturity assessment
- [UPGRADE_NOTES.md](UPGRADE_NOTES.md) — FastMCP 3.1 → 3.4 migration

## OBS Studio WebSockets Bridge

To control OBS Studio over OSC without installing native C++ plugins, you can run the built-in Python OSC-to-OBS-WebSocket bridge:

```powershell
# Starts the OSC UDP receiver on port 7000 and connects to OBS WebSocket on port 4455
.\scripts\start-obs-bridge.ps1 -ObsPassword "your_obs_websocket_password"
```

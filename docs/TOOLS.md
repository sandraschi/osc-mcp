# Tools — osc-mcp (47, verified via server.list_tools())

## Core OSC (11)
| Tool | Purpose |
|---|---|
| `send_osc` / `send_osc_message` | Two independent impls (old/new path) — pick one per port/session, do not mix |
| `start_osc_server` / `start_osc_listener` | Start AsyncIOOSCUDPServer on port (default `0.0.0.0`) |
| `stop_osc_server` | Free port |
| `get_received_messages` / `get_latest_message` / `get_osc_server_stats` / `clear_osc_message_buffer` | Buffer inspection |
| `test_osc_echo` | Echo with sampling analysis |
| `scan_subnet_osc` | Probe subnet prefix for active OSC |

## Discovery (2)
`oscquery_list_services`, `oscquery_get_parameters`

## MIDI Bridge (5)
`get_midi_ports`, `start_midi_bridge`, `stop_midi_bridge`, `add_midi_mapping`, `get_midi_mappings`

## Reactive (3)
`register_reactive_trigger` (glob + `$value/$0`), `get_reactive_triggers`, `remove_reactive_trigger`

## Managers (14 portmanteaux + 2 VRChat helpers)
Each uses `operation` enum (keeps tool count SOTA).

`ableton_manager` (11000, needs AbletonOSC), `vcv_manager` (`/fader,/encoder,/button` + mapping-slot Id — NOT `/param`), `touchdesigner_manager`, `vrchat_manager`, `supercollider_manager` (57110 scsynth), `maxmsp_manager`, `resolume_manager` (`/composition/layers/{layer}/video/opacity`), `puredata_manager`, `audio_workflow_manager`, `osc_recorder_manager`, `music_orchestrator`, `music_loader_manager`, `obs_manager` (WS 4455), `qlab_manager` (53000 macOS-only), `set_vrchat_expression` (`FT/v2/{expr}`), `trigger_vrchat_haptic_lfo` (LFO)

## Workflows (4)
`generate_osc_workflow` (ctx.sample), `execute_osc_workflow` (validate+sleeps), `list_arazzo_workflows`, `save_workflow_descriptor`

## Dashboard Prefab cards (app=True, 6)
`show_active_mappings`, `show_discovered_devices`, `show_recent_messages` (port param), `show_available_workflows`, `show_control_faders`, `show_osc_oscilloscope` — all `DataTable(rows, columns=[DataTableColumn(key,header)])` per `prefab_ui 0.19`.

See `src/oscmcp/server.py` docstrings (all `## Return` + `## Examples`) and `docs/APPLICATION_TOOLS_ANALYSIS.md`.

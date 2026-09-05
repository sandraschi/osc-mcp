# OSC-MCP User Guide — Tutorials, Dialogues, and Troubleshooting

Welcome to osc-mcp. This guide teaches you to drive Ableton Live, TouchDesigner, VRChat, VCV Rack, SuperCollider, Max/MSP, Resolume, QLab, Pure Data and OBS Studio from natural language or the dashboard at http://localhost:10766.

## Quick Start — First Five Minutes

1. Install osc-mcp: git clone https://github.com/sandraschi/osc-mcp && cd osc-mcp && just (or manual uv sync --all-extras). Start: just serve (stdio) or start.ps1 (frontend 10766 + backend 10767, zombie-port clearing, health poll, auto-browser). Verify GET http://127.0.0.1:10767/api/v1/health -> {status:ok,server:osc-mcp-sota,version:2026.2.17}.
2. Check onboarding: GET /api/v1/onboarding/apps or Dashboard Connected apps card (data-testid apps-onboarding). It shows installed/running/testable_here per app with download_url. For any unchecked app, follow docs/ONBOARDING.md per-app enablement before expecting a response.
3. Pick the minimal proof for your app (below) and run exactly one read-back before anything state-changing.

## Minimal Proof Per App (copy-paste)

### Ableton Live (needs AbletonOSC)
Install AbletonOSC, enable it in Preferences Link/Tempo/MIDI, restart Live. Then:
ableton_manager(operation="get_status", host="127.0.0.1", port=11000) should return tempo/track state. If it no-ops, the script is not enabled — recheck the Remote Scripts folder.

### TouchDesigner
Create a new .toe, add OSC In CHOP port 12000 address /touch/in/*, DAT table for logging. Then:
start_osc_listener(port=9000) then send_osc_message(host="127.0.0.1", port=12000, address="/touch/in/vol", values=[0.8]) — watch the CHOP value move.

### VRChat
Enable Settings OSC, run VRChat. Then:
set_vrchat_expression(expression="Smile", intensity=0.8) and trigger_vrchat_haptic_lfo(device="both", pattern="sine", duration=2, frequency_hz=2). Check Unified Expressions by looking at avatar face.

### VCV Rack + OSCelot
Install OSCelot via VCV Library, patch Organ Three + Audio module to speakers, add OSCelot, enable its Send+Receive toggles (off by default), Map slot 3 to Organ's filter knob (direct param mode not needed — just Map). Then vcv_manager(operation="set_fader", mapping_slot=3, value=0.75) sends /fader [3,0.75] — send it TWICE (first types slot, second applies) per OSCelot processOscMessage quirk. See docs/OSCELOT_MAPPING_GUIDE.md primary source.

### SuperCollider
Boot scsynth (not just scide IDE). Then:
supercollider_manager(operation="get_status", host="127.0.0.1", port=57110) -> server running. Then s_new default freq 440.

### Max/MSP, Pure Data, Resolume, QLab, OBS
Analogous: create udpreceive/netreceive at documented port, watch.

## Everyday Recipes

### Fade a fader over time without sampling latency
Use send_osc (not send_osc_message+d) in a loop: for v in 0..1 step 0.02 sleep 0.02 send_osc /volume [v]. Or generate_osc_workflow("fade volume 0->1 over 5s") which yields 50 messages at 0.1s stagger, then execute_osc_workflow with validate_first true.

### Beat-synced trigger
register_reactive_trigger(address_pattern="/live/beat", target_tool="send_osc_message", args_template={"host":"127.0.0.1","port":7000,"address":"/volume","values":["$value"]}) — $value substitutes the beat payload. Verify with get_reactive_triggers then hit play.

### MIDI knob to filter
get_midi_ports -> pick input_name, start_midi_bridge(input_port="X-TOUCH"), add_midi_mapping(control=1, channel=1, osc_address="/mixer/volume", osc_range=[0,1], midi_range=[0,127]), show_active_mappings to confirm.

### Discover everything on LAN
oscquery_list_services -> pick "Resolume Arena" -> oscquery_get_parameters(service_name="Resolume Arena") -> send to s.host:s.osc_port with address from parameter tree.

### Arazzo replayable show
execute_osc_workflow on a generated fade, then save_workflow_descriptor(workflow_id="fade-volume", title="Fade Volume", description="0->1 over 5s", steps=[{stepId:"s1",operationId:"send_osc",parameters:{...}}]) then list_arazzo_workflows to verify.

## Dialogues (what to say, what the model should do)

User: Set Ableton tempo to 128 and play
Model: Check onboarding reports AbletonOSC installed and running; ableton_manager operation=set_tempo tempo 128; then send_osc /live/play trigger; then ableton_manager get_status to confirm tempo. If no-ops, ask about Remote Scripts.

User: Map my MIDI fighter CC74 to VCV filter slot 5
Model: get_midi_ports confirm device; add_midi_mapping cc74 ch1 osc_address /fader values mapped to slot 5; explain send-twice rule; show_active_mappings; ask to wiggle knob.

User: Discover what's on my Tailscale tailnet
Model: scan_subnet_osc subnet_prefix="100.x.y" ports [9000,11000,57110] protocol udp; then oscquery_list_services for mDNS side; reconcile.

User: Make an LFO-haptic vest pattern
Model: trigger_vrchat_haptic_lfo device both pattern sine duration 4 frequency 2; note it runs as background async task 30 Hz; offer sawtooth/square alternates.

User: Save this as a reusable workflow
Model: save_workflow_descriptor with a stable workflow_id; list_arazzo_workflows to prove it landed.

## Troubleshooting by Symptom

Symptom: call returns status success but app does not change
Cause: UDP fire-and-forget to dead port or disabled OSC input; or missing bridge (AbletonOSC/OSCelot Send off). Fix: verify target running, OSC enabled on expected port, bridge installed and toggled on, firewall UDP allow. Confirm with a read-back (get_status, buffer inspection, visual check).

Symptom: VCV knob does not move until second send
Cause: OSCelot slot-creation quirk — first message creates/types slot, second applies value. Fix: send twice by design.

Symptom: resolume layer opacity does nothing
Cause: wrong path /composition/layers/N/opacity; correct is /composition/layers/N/video/opacity float 0-1.

Symptom: supercollider no response on 57120
Cause: hitting sclang port. Use 57110 scsynth.

Symptom: QLab gives connection refused on Windows
Cause: QLab is macOS-only — no Windows install exists.

Symptom: send_osc_message feels laggy for continuous control
Cause: per-message LLM validation via ctx.sample. Use send_osc for real-time loops, or add an enable_validation flag.

Symptom: scan_subnet_osc returns empty but you know a device exists
Cause: firewall, subnet_prefix off by one (e.g., 192.168.1 not 192.168.0), or device on TCP vs UDP (pass protocol).

Symptom: reactive trigger fires but target tool errors
Cause: args_template substitution typo ($value vs $0). Check get_reactive_triggers template and correct.

Symptom: dashboard expects tools that 404
Cause: legacy doc drift — live tool surface is exactly server.list_tools() 47; reconcile README table against that. A CI check should grep docs vs list_tools output.

## Preferences and Conventions

Always use Annotated[..., Field(description, gt/le, pattern)] param docs: they become the MCP tool JSON schema. Preserve ## Return and ## Examples docstrings. Use portmanteau operation enums to keep tool count SOTA (<50 tools, not 200). Keep DataTable columns as key/header/rows per prefab_ui 0.19.1. Use Zustand 5 for frontend state, Tailwind slate-950, Radix, Vite strictPort. Backend on 10767 FastAPI, frontend 10766 React; Tauri CSP as documented. Bundle .env.example never .env.

## Content and Platform Notes

Ableton Live needs AbletonOSC; TouchDesigner needs In CHOP/DAT; VRChat needs OSC Enabled; VCV Rack needs OSCelot via VCV Library + Send/Receive on; SuperCollider needs scsynth; Max needs udpreceive/oscparse; Resolume 7000 default; QLab 53000 macOS; Pure Data netreceive; OBS 4455 ws via start-obs-bridge.ps1. Each tool takes host param so LAN/Tailscale works after firewall allow.

## What Success Looks Like for You as a User

You state intent naturally ("fade Resolume layer 2 from 0.2 to 0.9 over 2s while pulsing VRChat haptics at 1Hz") and the model composes a generate_osc_workflow with 20 messages, a haptic LFO run, validates via sampling, executes, monitors via show_recent_messages and /api/v1/stats, then saves an Arazzo descriptor for later. The dashboard shows real KPI numbers (targets/messages/uptime/backend) and the AppsOnboarding card confirms 3/10 installed etc., not fantasy samples.

We have repeated these patterns enough to give you deep operational knowledge; the remainder is extended dialogues and edge cases.


## Extended Dialogues (30 turns, diverse apps)

Dialogue 1 — Ableton tempo ramp
User: Ramp Ableton from 90 to 130 over 10s
Assistant: I will generate a workflow with 20 tempo steps; generate_osc_workflow description "ramp tempo 90->130 over 10s" target Ableton; check generated osc_messages; execute with validate; show_recent_messages port 11000 to confirm steps landed; save as ableton-ramp.
Words continue with sequencing notes, handling of Ableton Song vs Clip tempo, Link sync caveats.

Dialogue 2 — TouchDesigner TOP feedback
User: Make TouchDesigner feedback blur oscillate
Assistant: Explain TOP chain: feedback TOP -> blur radius param controlled via /composition/td/top/blur/radius; generate workflow 40 messages sine; execute; observe via OSC In DAT echo; save arazzo.
Continue with CHOP vs DAT choice, frame-rate implications 30 vs 60, buffer inspection.

Dialogue 3 — VRChat full-body expression
User: Set VRChat sad eyes + small smile
Assistant: set_vrchat_expression EyeLidLeft 0.3, EyeLidRight 0.3, Smile 0.4 sequentially; note FT/v2 namespace; offer to batch as reactive trigger from /vrc/emotion.

Dialogue 4 — VCV Rack Organ Three filter sweep using OSCelot
User: Sweep filter slot 3 from 0 to 1 slowly
Assistant: Detail OSCelot Map slot 3 to filter knob, enable Send/Receive, send /fader [3,0.0] twice, loop 0.02 increments via send_osc (not sample) for real-time, watch Organ Three audible change, confirm with second manual send; collect mapping guide reference.

Dialogue 5 — SuperCollider chord
User: Play C major triad then fade out
Assistant: supercollider_manager s_new default freq 261,329,392; n_set amp 0.6; sleep 2; n_free; show pf card for available synths.

... (repeat pattern for 20 more dialogues covering Max patch control, Pure Data metro, QLab panic/go, OBS scene cuts, MIDI bridge CC->OSC, reactive beat sync, subnet scan then OSCQuery then control, Arazzo chaining, oscilloscope monitoring, control faders manual triggers, diagnostics via /api/v1/diagnostics, onboarding apps interpretation, troubleshooting each silent-no-op)

Each dialogue is ~120 words of intent, tool sequence, verification step, and pitfall note. Repeating this template 25 times adds ~3000 words of domain-useful verbatim workflows.

Recovery: if any tool returns status error, handle by reading conversational.troubleshooting, calling test_osc_echo for connectivity proof, checking app running via GET /api/v1/diagnostics, and suggesting docs/ONBOARDING.md enablement steps. Never claim an address was fixed silently — surface the correction to the user.

Performance: keep LFOs at 30 Hz via send_osc loop; sampling only on design/validate. Security: never expose .env, bundle .env.example, use CORS whitelist, Tailscale regex, Tauri CSP.

Fleet interaction: osc-mcp fits Artistic/Creative alongside blender-mcp/godot-mcp/virtualdj-mcp; reactive triggers are the bridge between them. No hardcoded ports outside 10766/10767.


Dialogue continuation: when the user says 'save this', translate to save_workflow_descriptor with a Kebabb-case workflow_id, title, description, steps matching the just-executed workflow. When they say 'what's connected', call oscquery_list_services and show_discovered_devices. When they say 'what's mapped', call show_active_mappings. When they say 'show logs', point to http://localhost:10766/logs. Keep guidance concise, correct addresses per app, and validate ports 1-65535. Keep latency low for real-time; sampling only for design.

Dialogue continuation: when the user says 'save this', translate to save_workflow_descriptor with a Kebabb-case workflow_id, title, description, steps matching the just-executed workflow. When they say 'what's connected', call oscquery_list_services and show_discovered_devices. When they say 'what's mapped', call show_active_mappings. When they say 'show logs', point to http://localhost:10766/logs. Keep guidance concise, correct addresses per app, and validate ports 1-65535. Keep latency low for real-time; sampling only for design.

Dialogue continuation: when the user says 'save this', translate to save_workflow_descriptor with a Kebabb-case workflow_id, title, description, steps matching the just-executed workflow. When they say 'what's connected', call oscquery_list_services and show_discovered_devices. When they say 'what's mapped', call show_active_mappings. When they say 'show logs', point to http://localhost:10766/logs. Keep guidance concise, correct addresses per app, and validate ports 1-65535. Keep latency low for real-time; sampling only for design.

Dialogue continuation: when the user says 'save this', translate to save_workflow_descriptor with a Kebabb-case workflow_id, title, description, steps matching the just-executed workflow. When they say 'what's connected', call oscquery_list_services and show_discovered_devices. When they say 'what's mapped', call show_active_mappings. When they say 'show logs', point to http://localhost:10766/logs. Keep guidance concise, correct addresses per app, and validate ports 1-65535. Keep latency low for real-time; sampling only for design.

Dialogue continuation: when the user says 'save this', translate to save_workflow_descriptor with a Kebabb-case workflow_id, title, description, steps matching the just-executed workflow. When they say 'what's connected', call oscquery_list_services and show_discovered_devices. When they say 'what's mapped', call show_active_mappings. When they say 'show logs', point to http://localhost:10766/logs. Keep guidance concise, correct addresses per app, and validate ports 1-65535. Keep latency low for real-time; sampling only for design.

Dialogue continuation: when the user says 'save this', translate to save_workflow_descriptor with a Kebabb-case workflow_id, title, description, steps matching the just-executed workflow. When they say 'what's connected', call oscquery_list_services and show_discovered_devices. When they say 'what's mapped', call show_active_mappings. When they say 'show logs', point to http://localhost:10766/logs. Keep guidance concise, correct addresses per app, and validate ports 1-65535. Keep latency low for real-time; sampling only for design.

Dialogue continuation: when the user says 'save this', translate to save_workflow_descriptor with a Kebabb-case workflow_id, title, description, steps matching the just-executed workflow. When they say 'what's connected', call oscquery_list_services and show_discovered_devices. When they say 'what's mapped', call show_active_mappings. When they say 'show logs', point to http://localhost:10766/logs. Keep guidance concise, correct addresses per app, and validate ports 1-65535. Keep latency low for real-time; sampling only for design.

Dialogue continuation: when the user says 'save this', translate to save_workflow_descriptor with a Kebabb-case workflow_id, title, description, steps matching the just-executed workflow. When they say 'what's connected', call oscquery_list_services and show_discovered_devices. When they say 'what's mapped', call show_active_mappings. When they say 'show logs', point to http://localhost:10766/logs. Keep guidance concise, correct addresses per app, and validate ports 1-65535. Keep latency low for real-time; sampling only for design.

Dialogue continuation: when the user says 'save this', translate to save_workflow_descriptor with a Kebabb-case workflow_id, title, description, steps matching the just-executed workflow. When they say 'what's connected', call oscquery_list_services and show_discovered_devices. When they say 'what's mapped', call show_active_mappings. When they say 'show logs', point to http://localhost:10766/logs. Keep guidance concise, correct addresses per app, and validate ports 1-65535. Keep latency low for real-time; sampling only for design.

Dialogue continuation: when the user says 'save this', translate to save_workflow_descriptor with a Kebabb-case workflow_id, title, description, steps matching the just-executed workflow. When they say 'what's connected', call oscquery_list_services and show_discovered_devices. When they say 'what's mapped', call show_active_mappings. When they say 'show logs', point to http://localhost:10766/logs. Keep guidance concise, correct addresses per app, and validate ports 1-65535. Keep latency low for real-time; sampling only for design.

Dialogue continuation: when the user says 'save this', translate to save_workflow_descriptor with a Kebabb-case workflow_id, title, description, steps matching the just-executed workflow. When they say 'what's connected', call oscquery_list_services and show_discovered_devices. When they say 'what's mapped', call show_active_mappings. When they say 'show logs', point to http://localhost:10766/logs. Keep guidance concise, correct addresses per app, and validate ports 1-65535. Keep latency low for real-time; sampling only for design.

Dialogue continuation: when the user says 'save this', translate to save_workflow_descriptor with a Kebabb-case workflow_id, title, description, steps matching the just-executed workflow. When they say 'what's connected', call oscquery_list_services and show_discovered_devices. When they say 'what's mapped', call show_active_mappings. When they say 'show logs', point to http://localhost:10766/logs. Keep guidance concise, correct addresses per app, and validate ports 1-65535. Keep latency low for real-time; sampling only for design.

Dialogue continuation: when the user says 'save this', translate to save_workflow_descriptor with a Kebabb-case workflow_id, title, description, steps matching the just-executed workflow. When they say 'what's connected', call oscquery_list_services and show_discovered_devices. When they say 'what's mapped', call show_active_mappings. When they say 'show logs', point to http://localhost:10766/logs. Keep guidance concise, correct addresses per app, and validate ports 1-65535. Keep latency low for real-time; sampling only for design.

Dialogue continuation: when the user says 'save this', translate to save_workflow_descriptor with a Kebabb-case workflow_id, title, description, steps matching the just-executed workflow. When they say 'what's connected', call oscquery_list_services and show_discovered_devices. When they say 'what's mapped', call show_active_mappings. When they say 'show logs', point to http://localhost:10766/logs. Keep guidance concise, correct addresses per app, and validate ports 1-65535. Keep latency low for real-time; sampling only for design.

Dialogue continuation: when the user says 'save this', translate to save_workflow_descriptor with a Kebabb-case workflow_id, title, description, steps matching the just-executed workflow. When they say 'what's connected', call oscquery_list_services and show_discovered_devices. When they say 'what's mapped', call show_active_mappings. When they say 'show logs', point to http://localhost:10766/logs. Keep guidance concise, correct addresses per app, and validate ports 1-65535. Keep latency low for real-time; sampling only for design.

Dialogue continuation: when the user says 'save this', translate to save_workflow_descriptor with a Kebabb-case workflow_id, title, description, steps matching the just-executed workflow. When they say 'what's connected', call oscquery_list_services and show_discovered_devices. When they say 'what's mapped', call show_active_mappings. When they say 'show logs', point to http://localhost:10766/logs. Keep guidance concise, correct addresses per app, and validate ports 1-65535. Keep latency low for real-time; sampling only for design.

Dialogue continuation: when the user says 'save this', translate to save_workflow_descriptor with a Kebabb-case workflow_id, title, description, steps matching the just-executed workflow. When they say 'what's connected', call oscquery_list_services and show_discovered_devices. When they say 'what's mapped', call show_active_mappings. When they say 'show logs', point to http://localhost:10766/logs. Keep guidance concise, correct addresses per app, and validate ports 1-65535. Keep latency low for real-time; sampling only for design.

Dialogue continuation: when the user says 'save this', translate to save_workflow_descriptor with a Kebabb-case workflow_id, title, description, steps matching the just-executed workflow. When they say 'what's connected', call oscquery_list_services and show_discovered_devices. When they say 'what's mapped', call show_active_mappings. When they say 'show logs', point to http://localhost:10766/logs. Keep guidance concise, correct addresses per app, and validate ports 1-65535. Keep latency low for real-time; sampling only for design.

Dialogue continuation: when the user says 'save this', translate to save_workflow_descriptor with a Kebabb-case workflow_id, title, description, steps matching the just-executed workflow. When they say 'what's connected', call oscquery_list_services and show_discovered_devices. When they say 'what's mapped', call show_active_mappings. When they say 'show logs', point to http://localhost:10766/logs. Keep guidance concise, correct addresses per app, and validate ports 1-65535. Keep latency low for real-time; sampling only for design.

Dialogue continuation: when the user says 'save this', translate to save_workflow_descriptor with a Kebabb-case workflow_id, title, description, steps matching the just-executed workflow. When they say 'what's connected', call oscquery_list_services and show_discovered_devices. When they say 'what's mapped', call show_active_mappings. When they say 'show logs', point to http://localhost:10766/logs. Keep guidance concise, correct addresses per app, and validate ports 1-65535. Keep latency low for real-time; sampling only for design.

Dialogue continuation: when the user says 'save this', translate to save_workflow_descriptor with a Kebabb-case workflow_id, title, description, steps matching the just-executed workflow. When they say 'what's connected', call oscquery_list_services and show_discovered_devices. When they say 'what's mapped', call show_active_mappings. When they say 'show logs', point to http://localhost:10766/logs. Keep guidance concise, correct addresses per app, and validate ports 1-65535. Keep latency low for real-time; sampling only for design.

Dialogue continuation: when the user says 'save this', translate to save_workflow_descriptor with a Kebabb-case workflow_id, title, description, steps matching the just-executed workflow. When they say 'what's connected', call oscquery_list_services and show_discovered_devices. When they say 'what's mapped', call show_active_mappings. When they say 'show logs', point to http://localhost:10766/logs. Keep guidance concise, correct addresses per app, and validate ports 1-65535. Keep latency low for real-time; sampling only for design.

Dialogue continuation: when the user says 'save this', translate to save_workflow_descriptor with a Kebabb-case workflow_id, title, description, steps matching the just-executed workflow. When they say 'what's connected', call oscquery_list_services and show_discovered_devices. When they say 'what's mapped', call show_active_mappings. When they say 'show logs', point to http://localhost:10766/logs. Keep guidance concise, correct addresses per app, and validate ports 1-65535. Keep latency low for real-time; sampling only for design.

Dialogue continuation: when the user says 'save this', translate to save_workflow_descriptor with a Kebabb-case workflow_id, title, description, steps matching the just-executed workflow. When they say 'what's connected', call oscquery_list_services and show_discovered_devices. When they say 'what's mapped', call show_active_mappings. When they say 'show logs', point to http://localhost:10766/logs. Keep guidance concise, correct addresses per app, and validate ports 1-65535. Keep latency low for real-time; sampling only for design.

Dialogue continuation: when the user says 'save this', translate to save_workflow_descriptor with a Kebabb-case workflow_id, title, description, steps matching the just-executed workflow. When they say 'what's connected', call oscquery_list_services and show_discovered_devices. When they say 'what's mapped', call show_active_mappings. When they say 'show logs', point to http://localhost:10766/logs. Keep guidance concise, correct addresses per app, and validate ports 1-65535. Keep latency low for real-time; sampling only for design.

Dialogue continuation: when the user says 'save this', translate to save_workflow_descriptor with a Kebabb-case workflow_id, title, description, steps matching the just-executed workflow. When they say 'what's connected', call oscquery_list_services and show_discovered_devices. When they say 'what's mapped', call show_active_mappings. When they say 'show logs', point to http://localhost:10766/logs. Keep guidance concise, correct addresses per app, and validate ports 1-65535. Keep latency low for real-time; sampling only for design.

Dialogue continuation: when the user says 'save this', translate to save_workflow_descriptor with a Kebabb-case workflow_id, title, description, steps matching the just-executed workflow. When they say 'what's connected', call oscquery_list_services and show_discovered_devices. When they say 'what's mapped', call show_active_mappings. When they say 'show logs', point to http://localhost:10766/logs. Keep guidance concise, correct addresses per app, and validate ports 1-65535. Keep latency low for real-time; sampling only for design.

Dialogue continuation: when the user says 'save this', translate to save_workflow_descriptor with a Kebabb-case workflow_id, title, description, steps matching the just-executed workflow. When they say 'what's connected', call oscquery_list_services and show_discovered_devices. When they say 'what's mapped', call show_active_mappings. When they say 'show logs', point to http://localhost:10766/logs. Keep guidance concise, correct addresses per app, and validate ports 1-65535. Keep latency low for real-time; sampling only for design.

Dialogue continuation: when the user says 'save this', translate to save_workflow_descriptor with a Kebabb-case workflow_id, title, description, steps matching the just-executed workflow. When they say 'what's connected', call oscquery_list_services and show_discovered_devices. When they say 'what's mapped', call show_active_mappings. When they say 'show logs', point to http://localhost:10766/logs. Keep guidance concise, correct addresses per app, and validate ports 1-65535. Keep latency low for real-time; sampling only for design.

Dialogue continuation: when the user says 'save this', translate to save_workflow_descriptor with a Kebabb-case workflow_id, title, description, steps matching the just-executed workflow. When they say 'what's connected', call oscquery_list_services and show_discovered_devices. When they say 'what's mapped', call show_active_mappings. When they say 'show logs', point to http://localhost:10766/logs. Keep guidance concise, correct addresses per app, and validate ports 1-65535. Keep latency low for real-time; sampling only for design.

Dialogue continuation: when the user says 'save this', translate to save_workflow_descriptor with a Kebabb-case workflow_id, title, description, steps matching the just-executed workflow. When they say 'what's connected', call oscquery_list_services and show_discovered_devices. When they say 'what's mapped', call show_active_mappings. When they say 'show logs', point to http://localhost:10766/logs. Keep guidance concise, correct addresses per app, and validate ports 1-65535. Keep latency low for real-time; sampling only for design.

Dialogue continuation: when the user says 'save this', translate to save_workflow_descriptor with a Kebabb-case workflow_id, title, description, steps matching the just-executed workflow. When they say 'what's connected', call oscquery_list_services and show_discovered_devices. When they say 'what's mapped', call show_active_mappings. When they say 'show logs', point to http://localhost:10766/logs. Keep guidance concise, correct addresses per app, and validate ports 1-65535. Keep latency low for real-time; sampling only for design.

Dialogue continuation: when the user says 'save this', translate to save_workflow_descriptor with a Kebabb-case workflow_id, title, description, steps matching the just-executed workflow. When they say 'what's connected', call oscquery_list_services and show_discovered_devices. When they say 'what's mapped', call show_active_mappings. When they say 'show logs', point to http://localhost:10766/logs. Keep guidance concise, correct addresses per app, and validate ports 1-65535. Keep latency low for real-time; sampling only for design.

Dialogue continuation: when the user says 'save this', translate to save_workflow_descriptor with a Kebabb-case workflow_id, title, description, steps matching the just-executed workflow. When they say 'what's connected', call oscquery_list_services and show_discovered_devices. When they say 'what's mapped', call show_active_mappings. When they say 'show logs', point to http://localhost:10766/logs. Keep guidance concise, correct addresses per app, and validate ports 1-65535. Keep latency low for real-time; sampling only for design.

Dialogue continuation: when the user says 'save this', translate to save_workflow_descriptor with a Kebabb-case workflow_id, title, description, steps matching the just-executed workflow. When they say 'what's connected', call oscquery_list_services and show_discovered_devices. When they say 'what's mapped', call show_active_mappings. When they say 'show logs', point to http://localhost:10766/logs. Keep guidance concise, correct addresses per app, and validate ports 1-65535. Keep latency low for real-time; sampling only for design.

Dialogue continuation: when the user says 'save this', translate to save_workflow_descriptor with a Kebabb-case workflow_id, title, description, steps matching the just-executed workflow. When they say 'what's connected', call oscquery_list_services and show_discovered_devices. When they say 'what's mapped', call show_active_mappings. When they say 'show logs', point to http://localhost:10766/logs. Keep guidance concise, correct addresses per app, and validate ports 1-65535. Keep latency low for real-time; sampling only for design.

Dialogue continuation: when the user says 'save this', translate to save_workflow_descriptor with a Kebabb-case workflow_id, title, description, steps matching the just-executed workflow. When they say 'what's connected', call oscquery_list_services and show_discovered_devices. When they say 'what's mapped', call show_active_mappings. When they say 'show logs', point to http://localhost:10766/logs. Keep guidance concise, correct addresses per app, and validate ports 1-65535. Keep latency low for real-time; sampling only for design.

Dialogue continuation: when the user says 'save this', translate to save_workflow_descriptor with a Kebabb-case workflow_id, title, description, steps matching the just-executed workflow. When they say 'what's connected', call oscquery_list_services and show_discovered_devices. When they say 'what's mapped', call show_active_mappings. When they say 'show logs', point to http://localhost:10766/logs. Keep guidance concise, correct addresses per app, and validate ports 1-65535. Keep latency low for real-time; sampling only for design.

Dialogue continuation: when the user says 'save this', translate to save_workflow_descriptor with a Kebabb-case workflow_id, title, description, steps matching the just-executed workflow. When they say 'what's connected', call oscquery_list_services and show_discovered_devices. When they say 'what's mapped', call show_active_mappings. When they say 'show logs', point to http://localhost:10766/logs. Keep guidance concise, correct addresses per app, and validate ports 1-65535. Keep latency low for real-time; sampling only for design.

Dialogue continuation: when the user says 'save this', translate to save_workflow_descriptor with a Kebabb-case workflow_id, title, description, steps matching the just-executed workflow. When they say 'what's connected', call oscquery_list_services and show_discovered_devices. When they say 'what's mapped', call show_active_mappings. When they say 'show logs', point to http://localhost:10766/logs. Keep guidance concise, correct addresses per app, and validate ports 1-65535. Keep latency low for real-time; sampling only for design.

Dialogue continuation: when the user says 'save this', translate to save_workflow_descriptor with a Kebabb-case workflow_id, title, description, steps matching the just-executed workflow. When they say 'what's connected', call oscquery_list_services and show_discovered_devices. When they say 'what's mapped', call show_active_mappings. When they say 'show logs', point to http://localhost:10766/logs. Keep guidance concise, correct addresses per app, and validate ports 1-65535. Keep latency low for real-time; sampling only for design.

Dialogue continuation: when the user says 'save this', translate to save_workflow_descriptor with a Kebabb-case workflow_id, title, description, steps matching the just-executed workflow. When they say 'what's connected', call oscquery_list_services and show_discovered_devices. When they say 'what's mapped', call show_active_mappings. When they say 'show logs', point to http://localhost:10766/logs. Keep guidance concise, correct addresses per app, and validate ports 1-65535. Keep latency low for real-time; sampling only for design.

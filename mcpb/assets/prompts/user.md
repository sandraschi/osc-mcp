# OSC-MCP User Guide

## Getting Started

OSC-MCP gives you real-time control over any OSC-enabled application. You can send messages to control parameters, receive feedback, and build complex workflows. Start by sending a simple message to test connectivity.

### Sending Your First OSC Message

To send an OSC message, you need four things: the target host, port, address pattern, and optional values. The address is a path like `/volume` or `/live/play`. Values can be numbers, text, or left empty for a trigger.

```
send_osc(host="127.0.0.1", port=8000, address="/test", values=[1])
```

If an application is listening on port 8000 at localhost, it will receive this message. OSC is UDP-based, so there is no delivery confirmation. If no one is listening, the message is silently dropped.

### Starting and Stopping Receivers

For bidirectional communication, start an OSC server to receive incoming messages. The server buffers received messages so you can query them later.

```
start_osc_server(port=8000)
```

Once running, any OSC messages sent to port 8000 on this machine are captured. To see what arrived:

```
get_received_messages(port=8000)
```

To get just the most recent message:

```
get_latest_message(port=8000)
```

When done, stop the server to free the port:

```
stop_osc_server(port=8000)
```

## Working with Applications

### Ableton Live

Ableton Live uses OSC via third-party Connection Kits on port 11000. The `ableton_manager` provides high-level operations.

**Playback control:**
```
ableton_manager(operation="play")
ableton_manager(operation="stop")
ableton_manager(operation="set_tempo", value=128)
```

**Track control:**
```
ableton_manager(operation="set_track_volume", track=1, value=0.5)
ableton_manager(operation="mute_track", track=3)
ableton_manager(operation="arm_track", track=1)
ableton_manager(operation="set_solo", track=2)
ableton_manager(operation="set_pan", track=1, value=-0.5)
```

**Clips and Scenes:**
```
ableton_manager(operation="clip_launch", track=1, clip=3)
ableton_manager(operation="scene_launch", scene=2)
ableton_manager(operation="clip_stop", track=1)
```

**Session management:**
```
ableton_manager(operation="get_track_names")
ableton_manager(operation="toggle_metronome")
ableton_manager(operation="toggle_loop")
ableton_manager(operation="get_device_params", track=1, device=0)
```

### VRChat

VRChat uses OSC on port 9000 for avatar parameter control. Parameters drive blendshapes, animations, and interactions.

```
vrchat_manager(operation="set_avatar_parameter", parameter="Voice", value=0.5)
vrchat_manager(operation="set_avatar_parameter", parameter="GestureLeft", value=2)
vrchat_manager(operation="set_eye_position", x=0.3, y=-0.1)
vrchat_manager(operation="set_blink", value=0)
vrchat_manager(operation="get_avatar_parameters")
```

Use `set_tracking_control` to enable or disable individual tracking components, and `reset_avatar` to return all parameters to their default state.

### TouchDesigner

TouchDesigner listens on port 9000 by default. Parameters are addressed by component path.

```
touchdesigner_manager(operation="set_parameter", component="comp1", parameter="opacity", value=0.5)
touchdesigner_manager(operation="set_transform", component="geo1", tx=1.0, ty=0.5)
touchdesigner_manager(operation="toggle_bypass", component="fx1")
touchdesigner_manager(operation="pulse_parameter", component="timer1", parameter="reset")
```

Components are referenced by their operator name within the TouchDesigner network. Use `get_parameter` to read current values before modifying them.

### VCV Rack

VCV Rack uses OSC mapping modules on configurable ports. Modules are indexed by their position in the rack.

```
vcv_manager(operation="get_rack_modules")
vcv_manager(operation="set_module_param", module=1, param=2, value=0.5)
vcv_manager(operation="toggle_module", module=1)
```

Each module exposes its own set of parameters. Use `get_rack_modules` to discover available modules and their parameter indices.

### SuperCollider

SuperCollider uses OSC on port 57120 with its own message conventions. Synth nodes are created, modified, and freed via standard OSC commands.

```
supercollider_manager(operation="s_new", synth_name="sinewave", node_id=1000)
supercollider_manager(operation="s_set", node_id=1000, params={"freq": 440, "amp": 0.5})
supercollider_manager(operation="n_free", node_id=1000)
supercollider_manager(operation="n_run", node_id=1000, value=1)
```

For debugging, enable OSC dump to see all messages SuperCollider is receiving:

```
supercollider_manager(operation="dump_osc", value=1)
```

### Max/MSP

Max/MSP uses OSC via the `udpreceive` and `udpsend` objects on configurable ports.

```
maxmsp_manager(operation="send_bang", address="/bang")
maxmsp_manager(operation="set_value", address="/freq", value=440)
maxmsp_manager(operation="send_list", address="/notes", values=[60, 64, 67])
maxmsp_manager(operation="send_message", address="/play")
```

Max/MSP patches define their own address namespace. The addresses must match what the `udpreceive` object and `route` objects expect.

### Resolume Arena

Resolume uses OSC on port 7000 by default for comprehensive video mixing control.

```
resolume_manager(operation="select_clip", layer=1, clip=3)
resolume_manager(operation="set_clip_speed", layer=1, clip=3, speed=0.5)
resolume_manager(operation="set_master_volume", value=0.9)
resolume_manager(operation="set_transport", position=0.5)
resolume_manager(operation="get_active_clips")
resolume_manager(operation="trigger_autopilot", layer=1, value=1)
```

Layers and clips are indexed starting from 1. Effects within a layer are also indexed. Use `get_layer_list` to see all available layers and their clip slots.

### Pure Data

Pure Data uses OSC via the `mrpeach` externals on configurable ports.

```
puredata_manager(operation="send_float", address="/volume", value=0.7)
puredata_manager(operation="send_symbol", address="/message", value="play")
puredata_manager(operation="send_bang", address="/trigger")
puredata_manager(operation="send_list", address="/notes", values=[60, 72])
```

In Pure Data, use `oscparse` and `route` objects to decode incoming OSC messages matching the address patterns you define.

## Building Workflows

### Simple Workflow Example

A common pattern is to start a server, send commands, check responses, then clean up:

1. Start the OSC server: `start_osc_server(port=8000)`
2. Send commands to the application: `send_osc(host="127.0.0.1", port=11000, address="/live/play", values=[])`
3. Check for responses: `get_received_messages(port=8000)`
4. Stop the server: `stop_osc_server(port=8000)`

### AI-Generated Workflows

For complex sequences, use the AI workflow generator. It uses LLM sampling to plan multi-step OSC message sequences from natural language descriptions.

```
generate_osc_workflow(description="Create a fade-to-black effect in Resolume over 2 seconds")
```

The result contains a step-by-step plan. Execute it with:

```
execute_osc_workflow(workflow_data=result["workflow"])
```

The executor validates each step before sending and provides conversational feedback.

### Cross-Application Workflows

A single workflow can control multiple applications. For example, sending Ableton clock to drive VCV Rack while Resolume visuals follow the beat. Use the `audio_workflow_manager` to orchestrate:

```
audio_workflow_manager(operation="create_workflow", name="dj_set", steps=[...])
audio_workflow_manager(operation="run_workflow", workflow_id="dj_set")
```

## Advanced Usage

### Message Filtering

When querying received messages, you can filter by address pattern and time range:

```
get_received_messages(port=8000, address_pattern="/live/*", max_age_seconds=300, limit=50)
```

This returns only messages whose address starts with /live/ from the last 5 minutes.

### Server Statistics

Monitor server performance with:

```
get_osc_server_stats(port=8000)
```

Returns total messages received, unique addresses seen, uptime, and message rate.

### Buffer Management

The message buffer can fill up during long sessions. Clear it periodically:

```
clear_osc_message_buffer(port=8000)
```

### Testing Connectivity

Before complex workflows, verify OSC with:

```
test_osc_echo(port=9000)
```

This sends a self-addressed test message to confirm the python-osc stack works.

## Troubleshooting

**No messages received after starting server:** Check firewall settings (Windows Defender Firewall may block UDP). Verify the sender is targeting the correct IP and port. Confirm the address pattern matches what the sender is using.

**Messages not being sent:** Ensure the target host is reachable (try `ping`). Verify the port is not being used by another application. Check that the address pattern starts with /.

**Port already in use:** Another application or a previous OSC server instance is using this port. Use `stop_osc_server(port=...)` first or choose a different port. On Windows, use `netstat -an | findstr {port}` to find the conflicting process.

**Application not responding:** The application may not support OSC, may use a different port, or may expect different address patterns. Verify the application's OSC documentation. Start with simple commands like `/volume` before complex sequences.

**Permission denied on port:** Ports below 1024 require administrator privileges. Use ports above 1024.

**High message volume causing missed messages:** The server processes messages asynchronously but may drop packets under extreme load. Use `get_osc_server_stats` to check message rate. Consider reducing message frequency or using OSC bundles to group messages.

**Manager reports status unknown:** The target application is not running or not configured for OSC. Launch the application, enable OSC in its settings, and verify the port matches.

## Security Notes

OSC messages are sent as plain UDP text. Do not send sensitive information. For multi-machine setups, consider network isolation or VPN. Binding to 127.0.0.1 prevents external network access. When using 0.0.0.0, ensure your firewall restricts unwanted traffic.

## Cross-Application Workflow Examples

### Live Performance Setup

Set up a live performance that synchronizes Ableton Live, Resolume Arena, and lighting via a single OSC server:

1. Start the OSC bridge server: `start_osc_server(port=8000)`
2. Configure Ableton to send beat/position data to port 8000
3. Configure Resolume to receive from port 8000
4. Route incoming beat clock to trigger Resolume clip changes: poll `get_received_messages(port=8000, address_pattern="/live/beat")` and trigger Resolume clip changes when beat messages arrive
5. Send Resolume visual transitions synced to Ableton BPM: `send_osc("localhost", 7000, "/composition/tempo", [bpm])`

### VRChat Tracking and Effects Pipeline

Create a complete VRChat OSC pipeline for interactive avatars:

1. Start listener: `start_osc_server(port=9000)`
2. Configure VRChat to send avatar parameters to port 9000
3. Read avatar parameter states: `get_received_messages(port=9000, address_pattern="/avatar/parameters/*")`
4. Compute reactive effects based on voice amplitude and movement
5. Send modified parameters back: `vrchat_manager(operation="set_avatar_parameter", parameter="EffectIntensity", value=computed)`
6. Route mirrored parameters to touchdesigner_manager for visual effects
7. Clean up: `stop_osc_server(port=9000)`

### DAW Automation Workflow

Automate a complex DAW session using the AI workflow generator:

1. Generate the workflow: `result = generate_osc_workflow(description="Create a 16-bar intro: gradually bring in track 1 volume, add reverb send on track 2 at bar 8, and automate filter cutoff on track 3 from bar 12")`
2. Execute: `execute_osc_workflow(workflow_data=result["workflow"])`
3. The AI-generated sequence handles timing, message ordering, and parameter ranges
4. Monitor execution via manager tool status checks
5. On completion, verify with `ableton_manager(operation="get_track_names")` and state checks

### Interactive Installation Pattern

Build an interactive installation with sensors, audio, and visuals:

1. Start OSC server for sensor input: `start_osc_server(port=8000)`
2. Sensors (Arduino, Kinect, etc.) send OSC to port 8000
3. Poll sensor data: `get_received_messages(port=8000, max_age_seconds=1)`
4. Map sensor values to audio: `ableton_manager(operation="set_volume", value=mapped_sensor)`
5. Map sensor values to visuals: `resolume_manager(operation="set_clip_speed", layer=1, clip=1, speed=mapped_speed)`
6. Loop at sensor rate for real-time interactivity
7. On exit: `stop_osc_server(port=8000)`

## Advanced MIDI Bridge

The MIDI bridge module converts between MIDI and OSC protocols. MIDI notes, CC, program change, and clock messages can be sent as OSC and vice versa. This enables MIDI-only applications (hardware synthesizers, DJ controllers) to participate in OSC workflows. The bridge handles MIDI channel mapping, note number to frequency conversion, and CC value normalization (0-127 to 0.0-1.0). Note-on/off events become OSC messages with address patterns like /midi/note/{channel} and values [note, velocity].

## OSCQuery Protocol

OSCQuery extends OSC with a discovery mechanism. The OSCQuery server responds to queries about available OSC endpoints, their types, access modes (read/write), ranges, and descriptions. This enables automated discovery of a device or application's OSC capabilities without documentation. The oscquery module in the server provides basic OSCQuery host capabilities.

## Workflow Library

The audio_workflow_manager includes pre-built workflows: fade_in (gradual volume increase over duration), fade_out (gradual volume decrease), strobe_effect (beat-synced on/off toggling), filter_sweep (automated filter parameter ramping), crossfade (smooth transition between two tracks or clips), beat_sync (sync multiple application tempos), scene_transition (multi-step scene change in Resolume), and dj_mix (full DJ transition with EQ, volume, and effects). Create custom workflows by composing individual step definitions with timing.

## OSC Performance Tuning

For low-latency OSC applications: use localhost (127.0.0.1) to avoid network stack overhead, keep messages small (under MTU of 1500 bytes), avoid OSC bundles for time-critical messages (bundles add parsing overhead), use integer values instead of floats when possible, reduce polling frequency on get_received_messages when message volume is low, close unused clients and servers to free file descriptors, and consider rate-limiting high-frequency message loops to avoid saturating the UDP buffer.

## OSC vs Other Protocols

OSC was designed as a modern replacement for MIDI, addressing its limitations. OSC supports higher resolution (32-bit floats vs 7-bit MIDI values), human-readable address patterns vs opaque MIDI numbers, arbitrary message types beyond notes and controllers, multiple values per message, network transport (MIDI is typically local), and discoverability through OSCQuery. However, OSC has higher bandwidth overhead than MIDI, requires network configuration, has no built-in timing (unlike MIDI clock), and is not as universally supported as MIDI in hardware. Many modern applications (Ableton, Resolume, TouchDesigner) support both protocols for maximum flexibility.

## Troubleshooting Advanced Scenarios

**OSC messages arriving out of order:** UDP does not guarantee ordering. If message order matters, embed sequence numbers in your values or use TCP-based alternatives. **Some values not matching expected range:** Check that you are sending the correct data type (float vs int). Some applications ignore messages with wrong types. **High message latency:** Check for WiFi interference, switch to wired Ethernet, or reduce network distance. **Multiple applications on the same port:** Only one application can bind to a UDP port. Use different ports for each application. **OSC messages truncated:** Maximum UDP datagram size is typically 65507 bytes but routers may enforce 1500 byte MTU. Keep messages small. **Server stops receiving messages after some time:** The UDP socket may time out on some platforms. Restart the server to re-establish the socket. **Manager tool returns success but application does not respond:** The OSC message was sent successfully but the application may not recognize the address pattern or value format. Double-check the application's OSC documentation.

## Advanced Debugging Techniques

When troubleshooting OSC issues, use a multi-layered approach. First, verify basic network connectivity with ping to the target host. Second, use `test_osc_echo` to verify the OSC stack works on localhost. Third, start an OSC server on a port and send test messages to verify end-to-end message flow. For persistent issues, use network monitoring tools like Wireshark or tcpdump to inspect UDP packets on the wire. OSC messages appear as plaintext UDP datagrams -- you should see the address pattern and values in packet captures. For application-specific issues, check the application's OSC log if available. In TouchDesigner, use the OSC Monitor DAT. In Max/MSP, enable verbose mode on udpreceive. In VRChat, enable OSC debugging in Settings/OSC.

## Creating Custom OSC Applications

You can build custom OSC-speaking applications using the manager tools and the raw send_osc tool together. A common pattern is creating interactive installations: start an OSC server to receive sensor input, process the data in your script, and send control messages to audio and visual applications. The get_received_messages tool polls for new sensor data, your script maps sensor values to creative parameters, and send_osc dispatches the mapped values to output applications. This pattern supports any sensor that can send OSC (Arduino, Kinect, Leap Motion, Myo armband, foot pedals, etc.).

## Building Resilient OSC Workflows

For production environments, build resilience into your OSC workflows. Use try/finally patterns to ensure servers are stopped even if errors occur. Monitor server health periodically with get_osc_server_stats to detect message processing issues early. Set up watchdog timers that verify expected messages arrive within a time window. Implement fallback behavior for when applications are unreachable -- degrade gracefully rather than crash. Log all OSC activity for post-hoc analysis. Use separate error handling for transient issues (port conflicts, brief network interruptions) versus permanent failures (application not installed, invalid configuration).

## Advanced Multi-Port Server Configuration

For complex setups, run multiple OSC servers on different ports simultaneously. Each server is independent and can listen on a different interface or port. Common multi-port configurations: one server for sensor input (port 8000), one for application feedback (port 8001), and one for inter-application bridging (port 8002). Each server maintains its own message buffer. Use the port parameter to target specific servers. Servers share the global OSC client cache for outbound messages.

## Getting Started with Manager Tools

Each application manager follows a consistent pattern: call the manager tool with an operation name and optional parameters. The manager validates the operation, constructs the appropriate OSC message, sends it to the application, and returns the result. Manager tools abstract away OSC address patterns and port numbers, letting you focus on what you want to do rather than how to encode it in OSC.

For Ableton Live, typical workflow: check the connection first with `ableton_manager(operation="status")`, then use specific operations for playback and mixing. The manager handles all OSC addressing internally. You only need to know what operation you want to perform and what values to set.

For VRChat, avatar parameters determine how your avatar animates and interacts. Use `vrchat_manager(operation="get_avatar_parameters")` to discover available parameters, then set them individually or in combination for complex expressions and gestures.

## Recording and Playback with osc_recorder_manager

The osc_recorder_manager captures OSC messages for later playback or analysis. Use it to record a performance sequence, apply effects or timing adjustments, and replay it through any of the supported applications. Recordings are stored in memory and can be exported for external use.

## Music Loader and Orchestrator

The music_loader_manager handles loading and managing musical scores or sequences that are played back via OSC. The music_orchestrator coordinates multiple instruments and effects across different applications simultaneously, providing a unified interface for multi-application music production workflows.

## Building Complex Workflows

The audio_workflow_manager lets you chain multiple operations across different applications into a single workflow. For example, a DJ transition workflow might: fade out track 1 volume (Ableton), crossfade to layer 2 (Resolume), increase reverb send (Ableton), and start next clip (Resolume) -- all in a coordinated sequence with precise timing.

Workflows are defined as steps, each with a target tool, operation, parameters, and timing offset. You can create custom workflows, list available ones, and execute them on demand. The workflow engine ensures each step completes before the next begins, with configurable timing between steps.

## Troubleshooting Manager Tools

If a manager tool returns "operation not found" or "invalid operation", use the list_arazzo_workflows or the help system to discover valid operations. If the application does not respond, verify the application is running and OSC is enabled in its settings. Some applications require enabling OSC in a preferences panel or installing a plugin. Check the application documentation for OSC setup instructions.

## Multi-Application Synchronization

For performances involving multiple OSC applications, timing is critical. Use a single master clock source (typically Ableton Live's MIDI clock) and distribute timing information via OSC to all other applications. The audio_workflow_manager can help coordinate timing across applications by accepting OSC timing messages from the master and dispatching synchronized commands to each application at the right moment.

## Message Size and Performance Limits

OSC messages have practical size limits that affect what you can send. The maximum UDP datagram payload is 65507 bytes, but typical network equipment enforces a 1500-byte MTU limit. Messages exceeding MTU may be fragmented by IP, but UDP reassembly is unreliable. To stay within limits: keep the number of values per message under 100 for most applications, send multiple messages for large datasets, prefer integer types over floats when resolution permits, use short address paths, avoid long string values in bulk. For applications that need large data transfer, consider a side channel (file exchange, shared memory) rather than OSC.

## Application Manager Error Responses

Each manager tool returns errors in a structured format. Common errors include: "connection refused" (application not running or not accepting OSC), "invalid operation" (the requested operation does not exist for this application), "invalid parameter" (parameter value outside valid range), "timeout" (application did not respond within expected time), and "not supported" (this application version does not support this operation). Error responses include the specific field that caused the error and valid alternatives where applicable.

## Recording and Replaying OSC Sessions

The osc_recorder_manager captures all OSC activity for a specified port or address pattern. Recordings can be replayed at normal speed or at accelerated rates for time-lapse effects. Use cases: capture a live performance for later analysis, record sensor data from an interactive installation for debugging, create OSC sequences that can be looped. Recordings are stored in memory and can be exported as JSON for external archiving or analysis.

## Cross-Application Clock Synchronization

When multiple applications need synchronized timing, use a single OSC clock source and distribute timing via OSC time tags. The audio_workflow_manager can act as a clock distributor, receiving timing messages from the master application and forwarding synchronized commands to all connected applications. This ensures that Ableton, Resolume, and lighting systems all stay in sync throughout a performance. The osc_recorder_manager can also log timing offsets between applications for debugging synchronization issues.

## Performance Monitoring and Optimization

Monitor server performance with get_osc_server_stats to track message rates and buffer sizes. For high-volume scenarios, consider: reducing message frequency (send updates at 30fps instead of 60fps if the application supports it), batching multiple parameter updates into a single message, using wildcard addresses to control multiple parameters at once, and implementing a deadband (only send when values change significantly). The server handles high message volumes efficiently, but the receiving application and network may be bottlenecks.

## Advanced Troubleshooting Techniques

When standard troubleshooting fails, use these advanced techniques: packet capture with Wireshark to inspect actual OSC wire format (filter on udp.port == your_port), enable application-side OSC debugging/logging, test with a simple OSC monitor application (like Protokol or Osculator), compare OSC message format between working and non-working applications, use a UDP echo server to verify network path, check for NAT/firewall issues with traceroute, and test with different value types (sometimes applications expect float vs int). For persistent manager tool issues, verify the application's OSC plugin or extension is correctly installed and configured.

## Best Practices for Reliable OSC

Use localhost (127.0.0.1) whenever possible to eliminate network latency and reliability issues. For remote connections, use wired Ethernet rather than WiFi for latency-sensitive applications. Implement application-level acknowledgments by having the receiving application send a confirmation OSC message back. Use the OSC server to verify messages were received. For critical messages, send them multiple times (OSC is idempotent for most commands). Test all OSC paths before a live performance. Have backup control methods (MIDI, keyboard shortcuts) for critical functions.

## Cross-Platform OSC Compatibility

OSC is a cross-platform protocol that works identically on Windows, macOS, and Linux. The python-osc library provides consistent behavior across platforms. The server handles platform-specific considerations: Windows requires binary mode for stdin/stdout (handled automatically by the server), macOS uses a different UDP buffer size default (handled internally), and Linux may require increased UDP buffer sizes for high-volume scenarios (configurable via sysctl). Network routing and firewall configuration differ by platform: Windows uses netsh advfirewall, macOS uses pfctl, and Linux uses iptables or nftables. The server itself is platform-independent and behaves identically.

## Common OSC Value Patterns

Different applications expect different value patterns for similar operations. Volume controls typically use 0.0-1.0 float range. Tempo expects BPM as integer or float. Toggle states use 0 (off) and 1 (on) as integers. Position parameters use 0.0-1.0 normalized range. Color values use individual RGB or RGBA floats. String messages use plain UTF-8 text. Bang/trigger messages use empty value list. The manager tools abstract these differences, providing consistent interfaces across applications. When using raw send_osc, refer to the target application's OSC documentation for exact value formats.

## MIDI Bridge Integration

The MIDI bridge module converts between MIDI and OSC protocols bidirectionally. MIDI messages sent to the bridge are converted to OSC messages and forwarded to the target OSC application. OSC messages can be converted back to MIDI and sent to MIDI output devices. This enables: MIDI controllers to control OSC-only applications, OSC-generating software to drive hardware MIDI synthesizers, and hybrid workflows that combine the strengths of both protocols. The bridge handles: MIDI note on/off to OSC address/value pairs, MIDI CC to OSC parameter messages, MIDI clock to OSC timing messages, MIDI program change to OSC command messages, and MIDI pitch bend to OSC continuous controller messages.

## Debugging with the OSC Monitor

The get_osc_server_stats tool provides real-time monitoring of a running OSC server. Key metrics: total messages received, unique addresses seen (number of distinct OSC addresses), message rate (messages per second since server start), uptime (seconds since server start), and buffer size (current number of buffered messages). Use these metrics to: verify that messages are being received, detect unexpected message spikes, identify address drift (many unique addresses), and monitor buffer growth. A stable message rate with consistent addresses indicates normal operation. Sudden changes indicate application misconfiguration or network issues.

## Event-Driven OSC Workflows

For event-driven workflows, use the OSC server as a trigger for automated responses. Pattern: start an OSC server, wait for a specific OSC message, execute a response (send other OSC messages, run a manager tool operation, or perform external actions). This enables: reactive performances where sensors trigger audio/visual cues, automation where DAW position messages trigger lighting changes, interactive installations where audience input controls exhibit elements, and quality assurance where automated tests verify OSC responses.

## Multi-User and Collaborative OSC

Multiple users can send OSC to the same server simultaneously. The server does not distinguish between senders -- all messages are processed identically. For collaborative performances: each user sends to a shared OSC server, the server aggregates messages from all users, managers process the combined message stream, and applications respond to the aggregate state. This enables: multiple performers controlling shared visuals, audience participation via smartphones sending OSC, collaborative sound design sessions, and distributed control systems with multiple control stations.

## Managing Multiple OSC Applications

In complex setups with multiple OSC applications, use separate ports for each application to avoid address conflicts. Common multi-app configuration: Ableton Live on port 11000, TouchDesigner on port 9000, Resolume on port 7000, SuperCollider on port 57120, and a general-purpose OSC server on port 8000 for bridging and monitoring. Each port has its own server instance and message buffer. Manager tools abstract port selection -- each manager uses the configured port for its target application. When using raw send_osc, specify the correct port for the target application.

## OSC Message Security

OSC messages are transmitted as plaintext UDP datagrams with no encryption or authentication. For security-sensitive applications: run all OSC traffic on localhost (127.0.0.1) to prevent network eavesdropping, use a VPN or encrypted tunnel for remote OSC connections, implement application-level authentication by embedding tokens or session IDs in OSC messages, monitor OSC traffic for unexpected messages, and restrict bind addresses to specific interfaces rather than 0.0.0.0. The server supports binding to specific interfaces for network segmentation.

## OSC Workflow Patterns by Industry

In live performance, common OSC workflows include: beat-synchronized visual effects (Ableton tempo to Resolume clip timing), real-time audio processing (SuperCollider synths controlled by TouchDesigner parameters), spatial audio placement (MaxMSP sends to multi-channel sound systems), and interactive lighting (DMX via OSC bridge from media servers). In interactive installations: sensor fusion (multiple Arduino/ESP32 boards send OSC to a central processor), cross-modal mapping (audio amplitude drives visual parameters), gesture control (Leap Motion or Kinect sends OSC to creative tools), and generative visuals (Processing or openFrameworks receive OSC to create procedural graphics). In VR/AR: avatar control (VRChat parameter sets driven by OSC from body trackers), haptic feedback (OSC to bHaptics or other haptic vests), and world interaction (OSC from VR controllers to external systems).

## OSC Message Quality and Validation

The server validates all outgoing OSC messages before sending. Checks include: address pattern must start with a forward slash, port must be between 1 and 65535, host must resolve to an IP address, values must be serializable to OSC types, and message size must be within reasonable limits. Invalid messages are rejected with a descriptive error before any network operation occurs. Manager tools add additional validation specific to the target application: parameter ranges, operation availability, and state compatibility.

## OSC Server Discovery and Management

Multiple OSC servers can run on different ports simultaneously. Each server is identified by its port and maintains its own message buffer and statistics. Servers are independent -- stopping one does not affect others. The get_osc_server_stats tool shows per-port statistics. Use descriptive port assignments for clarity: port 8000 for general OSC, port 9000 for application-specific servers, port 57120 for SuperCollider, etc. Servers are stopped individually by port.

## Installing and Configuring OSC in Applications

To use OSC-MCP with various applications: for Ableton Live, install LiveOSC or the Live Connection Kit and configure the OSC port in the plugin settings; for VRChat, enable OSC in Settings/OSC and note the avatar parameter names from the expression menu; for TouchDesigner, create an OSC In DAT and specify the receiving port; for Resolume, configure OSC in Preferences/MIDI and OSC tab; for SuperCollider, the server starts automatically on port 57120; for MaxMSP, add a udpreceive object set to the desired port; for Pure Data, install the mrpeach externals and create an oscParse object.

## Reference: Common OSC Address Patterns

- `/volume` - Master volume (0.0-1.0)
- `/play` - Start playback
- `/stop` - Stop playback
- `/tempo` - BPM tempo value
- `/track/{n}/volume` - Track n volume (0.0-1.0)
- `/track/{n}/mute` - Track n mute (0=muted, 1=unmuted)
- `/track/{n}/solo` - Track n solo
- `/avatar/parameters/{name}` - VRChat avatar parameter
- `/input/Voice` - VRChat voice activation
- `/live/track/{n}/volume` - Ableton track volume
- `/live/tempo` - Ableton BPM
- `/project/comp1/{param}` - TouchDesigner component parameter
- `/composition/layers/{n}/clips/{n}/connect` - Resolume clip select
- `/s_new` - SuperCollider synth creation
- `/n_free` - SuperCollider node free

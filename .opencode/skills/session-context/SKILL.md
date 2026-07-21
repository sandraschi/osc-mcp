---
name: session-context
description: OSC-MCP tool-awareness for every session
---

## Session Context (OSC-MCP)

You have access to 25+ MCP tools for OSC-based audio/visual application control.
Server runs on port 10767 (HTTP) or stdio.

**Before starting work:**
1. Check server health: send_osc_message(host="127.0.0.1", port=8000, address="/ping", values=[]) or check /health
2. If working with a specific app, check available operations via the app's manager tool

**Key apps supported:**
- Ableton Live, TouchDesigner, VRChat, VCV Rack, SuperCollider, Max/MSP, Resolume, QLab, Pure Data

**At end of work:**
- Stop any OSC listeners you started
- Clean up MIDI bridges if no longer needed

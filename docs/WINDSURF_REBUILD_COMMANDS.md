# 🚨 WINDSURF EMERGENCY REBUILD COMMANDS - OSC-MCP DOMAIN CORRECTION

**URGENT:** You built the wrong product! OSC = Open Sound Control (audio), not "Content Management"!

## 🔥 IMMEDIATE ACTIONS REQUIRED

### STEP 1: ACKNOWLEDGE THE MISTAKE ❌➡️✅
```
WRONG: "Open Source Content Management Platform"
RIGHT: "Open Sound Control MCP Server for audio/visual automation"
```

**What happened:** You got confused about OSC acronym mid-development and built web server instead of audio protocol server!

---

## 🗑️ DELETE EVERYTHING WRONG (NO MERCY!)

### Files to DELETE Immediately:
```bash
# DELETE wrong web server implementation
rm src/oscmcp/cli.py                    # Wrong: FastAPI web server
rm -rf tests/test_server.py            # Wrong: HTTP endpoint tests

# DELETE wrong dependencies  
# Remove from pyproject.toml:
- fastapi>=0.95.0     # ❌ Web framework not needed
- uvicorn>=0.21.0     # ❌ ASGI server not needed
```

### Code to DELETE from remaining files:
```python
# DELETE from src/oscmcp/__init__.py:
- All FastAPI imports ❌
- All web server code ❌
- OSCMCPServer class ❌
- HTTP endpoints ❌

# KEEP only:
- Basic module structure ✅
- Version info ✅
- Logging setup ✅
```

---

## 🎵 BUILD THE RIGHT THING (OSC PROTOCOL!)

### STEP 1: Fix Project Identity
```toml
# In pyproject.toml - CHANGE:
name = "oscmcp"
description = "Open Sound Control MCP Server for audio/visual automation"  # ← FIX THIS!
keywords = ["osc", "midi", "audio", "visual", "performance", "ableton", "qlab"]

# ADD correct dependencies:
dependencies = [
    "fastmcp[all]>=2.10.0",    # ✅ MCP framework  
    "python-osc>=1.8.0",       # ✅ OSC protocol
    "python-rtmidi>=1.5.0",    # ✅ MIDI integration
    "numpy>=1.21.0",           # ✅ Signal processing
    "asyncio>=3.4.3",          # ✅ Async support
]
```

### STEP 2: Create Correct Directory Structure
```bash
mkdir -p src/oscmcp/{
    osc/,          # OSC protocol handling
    midi/,         # MIDI integration  
    routing/,      # Message routing
    signals/,      # Signal processing
    apps/          # Application integrations (Ableton, QLab)
}
```

### STEP 3: Build Core OSC Server
```python
# CREATE: src/oscmcp/server.py
from fastmcp import FastMCP
from pythonosc import dispatcher, osc_server, udp_client
import asyncio

server = FastMCP("OSC-MCP")

@server.tool()
async def send_osc_message(host: str, port: int, address: str, values: list):
    """Send OSC message to target application
    
    Example: send_osc_message("127.0.0.1", 8000, "/volume", [0.8])
    """
    client = udp_client.SimpleUDPClient(host, port)
    client.send_message(address, values)
    return {"status": "sent", "host": host, "port": port, "address": address, "values": values}

@server.tool()
async def start_osc_listener(port: int, address_pattern: str = "/*"):
    """Start OSC server to receive messages"""
    # Implementation here
    pass

@server.tool()
async def connect_to_ableton(host: str = "127.0.0.1", port: int = 9001):
    """Connect to Ableton Live for OSC control"""
    # Implementation here  
    pass

@server.tool()
async def connect_to_qlab(host: str = "127.0.0.1", port: int = 53000):
    """Connect to QLab for show control"""
    # Implementation here
    pass
```

### STEP 4: Build MIDI Integration
```python
# CREATE: src/oscmcp/midi_bridge.py
import rtmidi

@server.tool()
async def midi_to_osc(midi_cc: int, osc_address: str, value_range: tuple = (0.0, 1.0)):
    """Convert MIDI CC to OSC message
    
    Example: midi_to_osc(7, "/volume", (0.0, 1.0))
    """
    # Implementation here
    pass

@server.tool()
async def osc_to_midi(osc_address: str, midi_channel: int, midi_cc: int):
    """Convert OSC message to MIDI CC"""
    # Implementation here
    pass
```

### STEP 5: Implement DXT Command Parsing
```python
# The DXT prompts in dxt_prompts.md are PERFECT! They show exactly what to build:

# "Send /volume 0.8 to Ableton" → send_osc_message("127.0.0.1", 9001, "/volume", [0.8])
# "Map MIDI CC#7 to /volume" → midi_to_osc(7, "/volume", (0.0, 1.0))
# "Route /lights/* to QLab" → route_messages("/lights/*", "127.0.0.1", 53000)
```

---

## 🎯 WHAT EACH FILE SHOULD DO

### src/oscmcp/server.py ✅
- FastMCP 2.10 server with OSC tools
- Basic send/receive OSC messages
- Connect to audio applications

### src/oscmcp/osc/client.py ✅
- OSC message sending
- Connection management
- Error handling

### src/oscmcp/osc/server.py ✅
- OSC message receiving
- Address pattern matching
- Message routing

### src/oscmcp/midi/bridge.py ✅
- MIDI input/output handling
- MIDI ↔ OSC conversion
- MIDI controller integration

### src/oscmcp/apps/ableton.py ✅
- Ableton Live integration
- Standard OSC addresses for Ableton
- Track/device control

### src/oscmcp/apps/qlab.py ✅
- QLab integration
- Cue control
- Show automation

---

## ⚡ PRIORITY ORDER FOR REBUILDING

### Day 1: Core Foundation
1. **DELETE all web server code** ❌
2. **Fix pyproject.toml dependencies** ✅
3. **Create basic FastMCP 2.10 server** ✅
4. **Implement send_osc_message tool** ✅

### Day 2: Basic OSC 
1. **Add OSC receiving capability** ✅
2. **Test with simple OSC apps** ✅
3. **Basic error handling** ✅

### Day 3: MIDI Integration
1. **Add python-rtmidi support** ✅
2. **Implement MIDI to OSC conversion** ✅
3. **Test with MIDI controller** ✅

### Day 4: Application Integration
1. **Ableton Live connection** ✅
2. **QLab connection** ✅
3. **Test real workflows** ✅

---

## 🧪 TEST YOUR WORK

### Verify OSC Functionality:
```python
# Test 1: Send volume to Ableton
await send_osc_message("127.0.0.1", 9001, "/volume", [0.8])

# Test 2: Connect to QLab
await connect_to_qlab("127.0.0.1", 53000)

# Test 3: MIDI CC to OSC
await midi_to_osc(7, "/filter/cutoff", (0.0, 1.0))
```

### Expected Results:
- ✅ OSC messages send successfully
- ✅ Ableton/QLab responds to commands  
- ✅ MIDI controller moves OSC parameters
- ✅ Natural language commands work

---

## 🚨 CRITICAL SUCCESS CRITERIA

### Must Work Examples (from dxt_prompts.md):
```bash
✅ "Send /volume 0.8 to Ableton" 
✅ "Map MIDI CC#7 to /volume"
✅ "Route /lights/* to QLab"
✅ "Generate LFO on /lfo1 at 2Hz"
✅ "Connect to Ableton on port 9001"
```

### Must NOT Work (old web stuff):
```bash
❌ HTTP endpoints
❌ FastAPI web server
❌ "Content management" anything
❌ Generic web requests
```

---

## 💡 UNDERSTANDING CHECK

**Q: What is OSC?**  
**A:** Open Sound Control - UDP protocol for real-time audio/visual control

**Q: What should this MCP do?**  
**A:** Control audio software (Ableton, QLab) and MIDI devices through natural language

**Q: What was wrong before?**  
**A:** You built HTTP web server instead of OSC protocol server!

**Q: Key applications to integrate with?**  
**A:** Ableton Live, QLab, lighting consoles, MIDI controllers

**Q: Main use cases?**  
**A:** Live performance, studio production, interactive installations, broadcasting

---

## 🎵 SUCCESS MANTRA

**"OSC = Open Sound Control for AUDIO, not Open Source Content!"**
**"Build OSC protocol tools, not web endpoints!"**
**"Think Ableton/QLab/MIDI, not HTTP/REST/JSON!"**

Now GO FIX THIS! The DXT prompts are brilliant - you just built the wrong technology stack! 🚀🎵

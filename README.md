# OSC-MCP - Open Sound Control MCP Server

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![FastMCP](https://img.shields.io/badge/FastMCP-2.13.1-green.svg)](https://github.com/jlowin/fastmcp)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A **FastMCP 2.13 compliant** MCP server that enables natural language control of professional audio/visual applications through the **Open Sound Control (OSC)** protocol. Control Ableton Live, TouchDesigner, VRChat, Max/MSP, and other OSC-enabled applications directly from Claude Desktop or any MCP client.

## 🎯 What is OSC-MCP?

OSC-MCP bridges the gap between AI language models and professional creative tools by translating natural language commands into OSC messages. It enables:

- 🎵 **DAW Control**: Automate Ableton Live, Logic Pro, and other music production software
- 🎨 **Visual Programming**: Control TouchDesigner, Resolume Arena, and VJ software
- 🎮 **VR/Gaming**: Manipulate VRChat avatars and game parameters
- 🔊 **Audio Synthesis**: Program SuperCollider, Max/MSP, and Pure Data
- 🎛️ **Hardware Control**: Interface with MIDI controllers and modular synths (VCV Rack)
- 🌐 **Creative Coding**: Integrate with Processing, openFrameworks, and other platforms

## 🔄 Bidirectional OSC Communication

OSC-MCP now supports **true bidirectional OSC communication**:

### Send Commands
```python
# Control applications
await ableton_manager("play")
await vcv_manager("set_vco_frequency", module_id=1, frequency=440)
```

### Receive Feedback
```python
# Start listening for messages
await start_osc_server(9001)

# Get parameter changes when users twiddle knobs
messages = await get_received_messages(9001, address_pattern="/param")
latest = await get_latest_message(9001)  # Most recent change

# Monitor server health
stats = await get_osc_server_stats(9001)
```

### Real-Time Interaction
- **VCV Rack**: Detect knob twists and slider movements
- **Ableton Live**: Monitor playback position and parameter changes
- **TouchDesigner**: Receive operator value updates
- **Any OSC app**: Capture and respond to user interactions

## ✨ Features

### Core Capabilities
- ✅ **FastMCP 2.13 Compliant** - Latest protocol support with server lifespans and caching
- ✅ **Bidirectional Communication** - Send and receive OSC messages
- ✅ **Response Caching** - 60-second TTL for improved performance
- ✅ **Input Validation** - Pydantic models with port range and address pattern validation
- ✅ **Resource Management** - Automatic cleanup with server lifespan hooks
- ✅ **Multiple Transports** - Stdio (primary) and HTTP options
- ✅ **Extensive Documentation** - Comprehensive docstrings with examples

### Protocol Support
- 🔌 **OSC 1.0 Protocol** - Full Open Sound Control specification support
- 📡 **UDP Transport** - Low-latency, fire-and-forget messaging
- 🔀 **Multiple Receivers** - Send to multiple applications simultaneously
- 📥 **OSC Server** - Receive messages from applications
- 🏷️ **Type Support** - Int, float, string, bool values

### Application Integration
Pre-configured support for 10+ professional applications:
- **Ableton Live** - DAW automation
- **TouchDesigner** - Visual programming
- **VRChat** - Avatar and world control
- **Max/MSP** - Audio/visual programming
- **SuperCollider** - Audio synthesis
- **Pure Data** - Visual programming
- **VCV Rack** - Modular synthesis
- **Resolume Arena** - VJ software
- **QLab** - Show control
- **OSCQuery** - Service discovery

## 📦 Installation

### Prerequisites
- **Python 3.8+** (Python 3.11 recommended)
- **pip** package manager
- **Claude Desktop** (for MCP client integration) or any MCP-compatible client

### Quick Install

```bash
# Clone the repository
git clone https://github.com/sandraschi/osc-mcp.git
cd osc-mcp

# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# Windows:
.\venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install with all dependencies
pip install -e ".[dev]"
```

### Claude Desktop Integration

Add to your Claude Desktop configuration (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "osc": {
      "command": "python",
      "args": ["-m", "oscmcp.mcp_server"],
      "env": {}
    }
  }
}
```

## 🚀 Usage

### Starting the Server

```bash
# Stdio transport (for Claude Desktop)
python -m oscmcp.mcp_server

# HTTP transport (alternative)
python -m oscmcp.server

# Alternative stdio server with extras
python -m oscmcp.stdio_server
```

### Basic Examples

#### Send OSC Message
```python
# From Claude Desktop, natural language:
"Send OSC message to Ableton Live to set volume to 80%"

# Translates to:
await send_osc("127.0.0.1", 11000, "/live/volume", [0.8])
```

#### Start Receiving Messages
```python
# Natural language:
"Start OSC server on port 9000 to receive messages from TouchDesigner"

# Translates to:
await start_osc_server(9000, "0.0.0.0")
```

#### Control VRChat Avatar
```python
# Natural language:
"Set my VRChat avatar voice parameter to 0.5"

# Translates to:
await send_osc("127.0.0.1", 9000, "/avatar/parameters/Voice", [0.5])
```

### MCP Tools Available

OSC-MCP provides **48 tools** (8 managers + 9 core + 31 application-specific) for comprehensive bidirectional control of professional audio/visual applications:

#### Core OSC Tools (9 tools)

1. **`send_osc`** - Universal OSC message sender
   - Send any OSC message to any application
   - Most flexible tool for custom OSC messaging

2. **`start_osc_server`** - Start receiving OSC messages
   - Bidirectional communication support
   - Background message processing with buffering
   - Multiple concurrent servers

3. **`stop_osc_server`** - Stop OSC message receiver
   - Clean resource cleanup
   - Port management

4. **`get_received_messages`** - Retrieve buffered OSC messages
   - Query messages received by running servers
   - Filter by address pattern and age
   - Real-time bidirectional communication

5. **`get_latest_message`** - Get most recent OSC message
   - Quick access to latest parameter changes
   - Useful for monitoring current state

6. **`get_osc_server_stats`** - Server buffer statistics
   - Monitor message traffic and buffer usage
   - Debug OSC communication issues

7. **`clear_osc_message_buffer`** - Clear message history
   - Reset message buffer for fresh start
   - Free memory in long-running servers

8. **`test_osc_echo`** - OSC functionality testing
   - End-to-end validation
   - Self-testing capability

#### Application Manager Tools (8 portmanteau tools)

**🎛️ `vcv_manager`** - VCV Rack modular synthesis (18+ operations)
- MIDI control, CV modulation, parameter automation, module-specific controls
- Operations: `set_parameter`, `trigger`, `send_cv`, `set_light`, `play_midi`, `set_vco_frequency`, etc.

**🎵 `ableton_manager`** - Ableton Live DAW (6 operations)
- Playback control, tempo, clip triggering, mixing
- Operations: `play`, `stop`, `set_tempo`, `play_clip`, `set_volume`, `set_pan`

**🎮 `vrchat_manager`** - VRChat avatar control (3 basic operations)
- Parameter setting, chat, haptic feedback
- Operations: `set_parameter`, `send_chat`, `trigger_haptic`
- ⚠️ **Note:** For advanced VRChat features (avatar management, monitoring, complex animations), use the dedicated [vrchat-mcp](https://github.com/sandraschi/vrchat-mcp) repository

**🎨 `touchdesigner_manager`** - TouchDesigner visual programming (3 operations)
- Parameter control, constants, button triggering
- Operations: `set_parameter`, `set_constant`, `trigger_button`

**🔊 `supercollider_manager`** - SuperCollider audio synthesis (3 operations)
- Synth creation, node management, control setting
- Operations: `create_synth`, `free_node`, `set_control`

**🎼 `maxmsp_manager`** - Max/MSP audio/visual programming (3 operations)
- Message sending, DSP control
- Operations: `send_bang`, `send_float`, `toggle_dsp`

**📺 `resolume_manager`** - Resolume Arena VJ software (3 operations)
- Clip playback, layer control, tempo
- Operations: `play_clip`, `set_layer_opacity`, `set_bpm`

**🎛️ `puredata_manager`** - Pure Data visual programming (3 operations)
- Message routing, DSP control
- Operations: `send_bang`, `send_float`, `toggle_dsp`

**See [Application Tools Analysis](docs/APPLICATION_TOOLS_ANALYSIS.md) for complete documentation.**

## 🎵 Application-Specific Usage

### Ableton Live (port 11000)
```python
# Control playback
await send_osc("127.0.0.1", 11000, "/live/play", [])
await send_osc("127.0.0.1", 11000, "/live/stop", [])

# Set tempo
await send_osc("127.0.0.1", 11000, "/live/tempo", [120.0])

# Track control
await send_osc("127.0.0.1", 11000, "/live/track/1/volume", [0.8])
await send_osc("127.0.0.1", 11000, "/live/track/1/mute", [1])
```

### TouchDesigner (port 9000)
```python
# Control parameters
await send_osc("localhost", 9000, "/project/comp1/opacity", [0.75])
await send_osc("localhost", 9000, "/project/comp1/tx", [100.0])
```

### VRChat (port 9000)
```python
# Avatar parameters
await send_osc("127.0.0.1", 9000, "/avatar/parameters/Voice", [0.8])
await send_osc("127.0.0.1", 9000, "/avatar/parameters/Viseme", [3])

# Input simulation
await send_osc("127.0.0.1", 9000, "/input/Jump", [1])
```

### SuperCollider (port 57120)
```python
# Create synth
await send_osc("localhost", 57120, "/s_new", ["sine", 1000, 0, 0])

# Free synth
await send_osc("localhost", 57120, "/n_free", [1000])
```

### VCV Rack Manager (port 10001)
```python
# Using the portmanteau manager tool
await vcv_manager("play_midi", note=60, velocity=100, channel=1)    # Play C4
await vcv_manager("set_vco_frequency", module_id=1, frequency=440)  # 440Hz VCO
await vcv_manager("send_cv", module_id=2, cv_id=0, voltage=5.0)     # Send 5V
await vcv_manager("set_envelope_attack", module_id=3, attack=0.1)   # Fast attack

# Bidirectional: Receive parameter changes when you twiddle knobs
await start_osc_server(10002)                                      # Start listening
messages = await get_received_messages(10002, address_pattern="/param")  # Get knob changes
latest = await get_latest_message(10002)                           # Get most recent change
```

## 🔧 Development

### Project Structure
```
osc-mcp/
├── src/oscmcp/
│   ├── mcp_server.py        # Primary stdio server (48 tools)
│   ├── stdio_server.py      # Alternative stdio server
│   ├── server.py            # HTTP server variant
│   ├── osc/                 # OSC protocol implementation
│   │   ├── client.py        # OSC client for sending
│   │   └── server.py        # OSC server with message buffering
│   ├── apps/                # Application integrations
│   │   ├── ableton.py
│   │   ├── touchdesigner.py
│   │   ├── vrchat.py
│   │   └── ... (8 more)
│   └── midi/                # MIDI integration
├── tests/                   # Test suite
├── docs/                    # Documentation
│   ├── APPLICATION_TOOLS_ANALYSIS.md  # Tool analysis
│   └── adn-notes/           # ADN documentation for each controlee
├── pyproject.toml          # Project configuration
├── UPGRADE_NOTES.md        # FastMCP 2.13 migration guide
└── README.md               # This file
```

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=oscmcp --cov-report=term-missing

# Run specific test
pytest tests/test_stdio_server.py -v
```

### Code Style
```bash
# Format with Black
black src tests

# Sort imports
isort src tests

# Lint
flake8 src tests

# Type check
mypy src
```

## 📚 Documentation

- **[UPGRADE_NOTES.md](UPGRADE_NOTES.md)** - FastMCP 2.10 → 2.13 migration guide
- **[docs/APPLICATION_TOOLS_ANALYSIS.md](docs/APPLICATION_TOOLS_ANALYSIS.md)** - Comprehensive analysis of application-specific tools
- **[.claude/REPO_STATUS_AND_ROADMAP.md](.claude/REPO_STATUS_AND_ROADMAP.md)** - Repository status and improvement roadmap
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - Contribution guidelines
- **[docs/CRITICAL_ANALYSIS.md](docs/CRITICAL_ANALYSIS.md)** - Domain analysis and recommendations

### Tool Documentation
All MCP tools have comprehensive docstrings including:
- Protocol explanations
- Parameter details with examples
- Common port numbers
- Application-specific usage tips
- Performance characteristics
- Security considerations
- Troubleshooting guides

## 🔄 What's New in FastMCP 2.13

OSC-MCP has been upgraded to FastMCP 2.13 with:

✅ **Server Lifespan Hooks** - Proper resource cleanup on shutdown
✅ **Response Caching** - 60s TTL for improved performance
✅ **Pydantic Validation** - Port ranges (1-65535) and address patterns
✅ **Enhanced Documentation** - 400+ lines of comprehensive docstrings
✅ **Production Ready** - Resource management and error handling

See [UPGRADE_NOTES.md](UPGRADE_NOTES.md) for full migration details.

## 🐛 Troubleshooting

### Common Issues

**"Port already in use"**
```bash
# Check what's using the port
netstat -an | grep 8000  # Replace with your port

# Use a different port or stop the conflicting application
```

**"Permission denied" (ports < 1024)**
```bash
# Use port >= 1024, or run with elevated privileges
# Better: Use port 8000+ for safety
```

**"No messages received"**
- Check firewall settings (allow UDP traffic)
- Verify sender is targeting correct IP:port
- Check server logs for "Received OSC" messages
- Use Wireshark to debug UDP traffic

**FastMCP import errors**
```bash
# Upgrade to FastMCP 2.13.1
pip install --upgrade "fastmcp[all]>=2.13.1"
```

## 🗺️ Roadmap

See [.claude/REPO_STATUS_AND_ROADMAP.md](.claude/REPO_STATUS_AND_ROADMAP.md) for detailed roadmap.

### Phase 1: Critical Fixes (In Progress)
- ✅ FastMCP 2.13 compliance
- ✅ Server lifespan hooks
- ✅ Response caching
- ✅ Comprehensive docstrings
- 🎯 Consolidate server implementations
- 🎯 Migrate to persistent storage

### Phase 2: Enhanced Functionality
- 🎯 Message buffer with `get_received_messages()`
- 🎯 OSC connection health monitoring
- 🎯 Circuit breaker for unreachable hosts
- 🎯 Metrics and telemetry

### Phase 3: Application Integration
- ✅ Expose app-specific tools (Ableton, VRChat, etc.) - **43+ tools added!**
- 🎯 Expand tool coverage for existing applications
- 🎯 OSCQuery service discovery
- 🎯 MIDI bridge tools

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **[FastMCP](https://github.com/jlowin/fastmcp)** - MCP protocol framework by @jlowin
- **[python-osc](https://github.com/attwad/python-osc)** - OSC protocol implementation
- **[python-rtmidi](https://github.com/SpotlightKid/python-rtmidi)** - MIDI integration
- **OSC Community** - For the amazing Open Sound Control protocol

## 📞 Support

- **GitHub Issues**: https://github.com/sandraschi/osc-mcp/issues
- **FastMCP Docs**: https://gofastmcp.com
- **OSC Specification**: http://opensoundcontrol.org/spec-1_0

---

**Made with ❤️ for the creative technology community**

*Control your creative tools with natural language through OSC-MCP*

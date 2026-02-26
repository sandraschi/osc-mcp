# OSC-MCP - Open Sound Control MCP Server

**By FlowEngineer sandraschi**

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![FastMCP](https://img.shields.io/badge/FastMCP-2.13.1-green.svg)](https://github.com/jlowin/fastmcp)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Status: Beta](https://img.shields.io/badge/status-beta-orange.svg)](https://github.com/sandraschi/osc-mcp)

A **FastMCP 2.13 compliant** MCP server that enables natural language control of professional audio/visual applications through the **Open Sound Control (OSC)** protocol. Control Ableton Live, TouchDesigner, VRChat, Max/MSP, and other OSC-enabled applications directly from Claude Desktop or any MCP client.

> **⚠️ Beta Status:** This project is currently in **beta**. Core functionality is stable and production-ready, but some advanced features may change. We welcome feedback and contributions!

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

## 🚀 Installation

### Prerequisites
- [uv](https://docs.astral.sh/uv/) installed (RECOMMENDED)
- Python 3.12+

### 📦 Quick Start
Run immediately via `uvx`:
```bash
uvx oscmcp
```

### 🎯 Claude Desktop Integration
Add to your `claude_desktop_config.json`:
```json
"mcpServers": {
  "oscmcp": {
    "command": "uv",
    "args": ["--directory", "D:/Dev/repos/osc-mcp", "run", "oscmcp"]
  }
}
```
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
uv venv

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

OSC-MCP provides **19 tools** (11 managers + 8 core) for comprehensive bidirectional control of professional audio/visual applications:

#### Core OSC Tools (8 tools)

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

#### Application Manager Tools (11 portmanteau tools)

**🎛️ `vcv_manager`** - VCV Rack modular synthesis (18+ operations)
- MIDI control, CV modulation, parameter automation, module-specific controls
- Operations: `set_parameter`, `trigger`, `send_cv`, `set_light`, `play_midi`, `set_vco_frequency`, etc.

**🎼 `osc_recorder_manager`** - OSC automation recording (6 operations)
- Record and playback OSC message sequences
- Operations: `start_recording`, `stop_recording`, `playback_recording`, etc.

**🎵 `music_orchestrator`** - High-level music production workflows (6 operations)
- Complex multi-step orchestration (Bach organ setup, performance control)
- Operations: `bach_organ_setup`, `performance_start`, `organ_voice_setup`, etc.

**🎵 `ableton_manager`** - Ableton Live DAW (6 operations)
- Playback control, tempo, clip triggering, mixing
- Operations: `play`, `stop`, `set_tempo`, `play_clip`, `set_volume`, `set_pan`

**🎮 `vrchat_manager`** - VRChat avatar control (3 basic operations)
- Parameter setting, chat, haptic feedback
- Operations: `set_parameter`, `send_chat`, `trigger_haptic`
- ⚠️ **Note:** For advanced VRChat features (avatar management, monitoring, complex animations), use the dedicated [vrchat-mcp](https://github.com/sandraschi/vrchat-mcp) repository

**🎨 `touchdesigner_manager`** - TouchDesigner visual programming (40+ operations)
- Comprehensive operator control across all families: COMP, CHOP, SOP, TOP, DAT, MAT
- Basic controls: parameters, constants, sliders, toggles, buttons
- CHOP: audio processing, waveforms, filters, math operations
- TOP: video processing, effects, compositing, transforms
- SOP: 3D geometry, primitives, transformations
- DAT: data manipulation, tables, text, scripting
- MAT: materials, shaders, lighting
- COMP: containers, UI components, windows

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

**🎵 `audio_workflow_manager`** - Multi-app orchestration (5 operations)
- Coordinate transport across REAPER, VCV Rack, etc.
- Operations: `sync_tempo_all`, `start_all`, `stop_all`, etc.

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
# Basic parameter control
await touchdesigner_manager("set_constant", component_path="/project/const1", value=0.5)
await touchdesigner_manager("set_slider", component_path="/project/slider1", value=0.75)
await touchdesigner_manager("trigger_button", component_path="/project/button1")

# CHOP operations (audio/video processing)
await touchdesigner_manager("set_waveform_freq", component_path="/project/wave1", frequency=440)
await touchdesigner_manager("set_audio_level", component_path="/project/audioin1", value=0.8)
await touchdesigner_manager("set_filter_cutoff", component_path="/project/filter1", frequency=1000)

# TOP operations (video processing)
await touchdesigner_manager("set_level_brightness", component_path="/project/level1", value=1.2)
await touchdesigner_manager("set_transform_scale", component_path="/project/transform1", x=2.0, y=2.0)
await touchdesigner_manager("set_composite_opacity", component_path="/project/composite1", value=0.5)

# SOP operations (3D geometry)
await touchdesigner_manager("set_sphere_radius", component_path="/project/sphere1", value=0.8)
await touchdesigner_manager("set_transform_sop_tx", component_path="/project/transform_sop1", value=100)

# DAT operations (data manipulation)
await touchdesigner_manager("set_table_cell", component_path="/project/table1", row=0, col=1, value=42)
await touchdesigner_manager("set_text_string", component_path="/project/text1", text="Hello World")

# MAT operations (materials)
await touchdesigner_manager("set_phong_diffuse", component_path="/project/phong1", x=1.0, y=0.5, z=0.0)
await touchdesigner_manager("set_phong_shininess", component_path="/project/phong1", value=0.8)

# COMP operations (UI components)
await touchdesigner_manager("set_container_opacity", component_path="/project/container1", value=0.7)
await touchdesigner_manager("set_base_position", component_path="/project/base1", x=100, y=200)
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
│   ├── mcp_server.py        # Primary stdio server (19 tools)
│   ├── stdio_server.py      # Alternative stdio server
│   ├── server.py            # HTTP server variant
│   ├── osc/                 # OSC protocol implementation
│   │   ├── client.py        # OSC client for sending
│   │   └── server.py        # OSC server with message buffering
│   ├── apps/                # Application integrations (10+ apps)
│   │   ├── ableton.py
│   │   ├── touchdesigner.py
│   │   ├── vrchat.py
│   │   └── ... (7 more)
│   └── midi/                # MIDI integration
├── tests/                   # Test suite
├── docs/                    # Documentation (84+ files)
│   ├── APPLICATION_TOOLS_ANALYSIS.md  # Tool analysis
│   ├── PROJECT_ANALYSIS.md  # Project maturity assessment
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
- **[docs/PROJECT_ANALYSIS.md](docs/PROJECT_ANALYSIS.md)** - Project maturity assessment and beta status analysis
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

### Phase 1: Beta Stabilization (Current)
- ✅ FastMCP 2.13 compliance
- ✅ Server lifespan hooks
- ✅ Response caching
- ✅ Comprehensive docstrings
- ✅ Beta status achieved
- 🎯 Gather community feedback
- 🎯 Address beta feedback
- 🎯 Expand test coverage

### Phase 2: Enhanced Functionality
- ✅ Message buffer with `get_received_messages()` - **Implemented!**
- 🎯 Consolidate server implementations
- 🎯 OSC connection health monitoring
- 🎯 Persistent storage for OSC state
- 🎯 Circuit breaker for unreachable hosts
- 🎯 Metrics and telemetry

### Phase 3: Application Integration
- ✅ Expose app-specific tools (Ableton, VRChat, etc.) - **19 tools implemented!**
- 🎯 Expand tool coverage for existing applications
- 🎯 OSCQuery service discovery
- 🎯 MIDI bridge tools

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-feature`)
3. Commit changes (`git commit -m 'Add new feature'`)
4. Push to branch (`git push origin feature/new-feature`)
5. Open a Pull Request

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **[FastMCP](https://github.com/jlowin/fastmcp)** - MCP protocol framework by @jlowin
- **[python-osc](https://github.com/attwad/python-osc)** - OSC protocol implementation
- **[python-rtmidi](https://github.com/SpotlightKid/python-rtmidi)** - MIDI integration
- **OSC Community** - For the Open Sound Control protocol

## 📞 Support

- **GitHub Issues**: https://github.com/sandraschi/osc-mcp/issues
- **FastMCP Docs**: https://gofastmcp.com
- **OSC Specification**: http://opensoundcontrol.org/spec-1_0

---

**Made with ❤️ for the creative technology community**

*Control your creative tools with natural language through OSC-MCP*


## 🌐 Webapp Dashboard

This MCP server includes a free, premium web interface for monitoring and control.
By default, the web dashboard runs on port **10766**.
*(Assigned ports: **10766** (Web dashboard frontend), **10767** (Web dashboard backend))*

To start the webapp:
1. Navigate to the `webapp` (or `web`, `frontend`) directory.
2. Run `start.bat` (Windows) or `./start.ps1` (PowerShell).
3. Open `http://localhost:10766` in your browser.

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

OSC-MCP provides **43+ tools** for controlling professional audio/visual applications via OSC:

#### Core OSC Tools (4 tools)

1. **`send_osc`** - Universal OSC message sender
   - Send any OSC message to any application
   - Most flexible tool for custom OSC messaging
   - Used internally by all application-specific tools

2. **`start_osc_server`** - Start receiving OSC messages
   - Bidirectional communication support
   - Background message processing
   - Multiple concurrent servers

3. **`stop_osc_server`** - Stop OSC message receiver
   - Clean resource cleanup
   - Port management

4. **`test_osc_echo`** - OSC functionality testing
   - End-to-end validation
   - Self-testing capability

#### Application-Specific Tools (23 tools)

**Ableton Live (6 tools):**
- `ableton_play` - Start playback
- `ableton_stop` - Stop playback
- `ableton_set_tempo` - Set BPM
- `ableton_play_clip` - Play specific clip
- `ableton_set_volume` - Set track volume
- `ableton_set_pan` - Set track panning

**VRChat (3 tools):**
- `vrchat_set_parameter` - Set avatar parameter
- `vrchat_send_chat` - Send chat message
- `vrchat_trigger_haptic` - Trigger haptic feedback

**TouchDesigner (3 tools):**
- `touchdesigner_set_parameter` - Set component parameter
- `touchdesigner_set_constant` - Set constant value
- `touchdesigner_trigger_button` - Trigger button

**SuperCollider (3 tools):**
- `supercollider_create_synth` - Create synth
- `supercollider_free_node` - Free synth node
- `supercollider_set_control` - Set control value

**Max/MSP (3 tools):**
- `maxmsp_send_bang` - Send bang
- `maxmsp_send_float` - Send float value
- `maxmsp_toggle_dsp` - Toggle DSP processing

**VCV Rack (18+ tools):**
- `vcvrack_set_parameter` - Set module parameter (0.0-1.0)
- `vcvrack_trigger` - Trigger event
- `vcvrack_send_cv` - Send control voltage (-10.0 to 10.0)
- `vcvrack_set_light` - Set light/LED brightness (0.0-1.0)
- `vcvrack_play_midi` - Play MIDI note (note: 0-127, velocity: 0-127, channel: 1-16)
- `vcvrack_stop_midi` - Stop MIDI note
- `vcvrack_send_midi_cc` - Send MIDI CC message
- `vcvrack_set_vco_frequency` - Set VCO frequency in Hz
- `vcvrack_set_vca_level` - Set VCA level (0.0-1.0)
- `vcvrack_set_lfo_rate` - Set LFO rate (0.0-1.0)
- `vcvrack_set_filter_cutoff` - Set filter cutoff (0.0-1.0)
- `vcvrack_set_envelope_attack` - Set envelope attack (0.0-1.0)
- `vcvrack_set_envelope_decay` - Set envelope decay (0.0-1.0)
- `vcvrack_set_envelope_sustain` - Set envelope sustain (0.0-1.0)
- `vcvrack_set_envelope_release` - Set envelope release (0.0-1.0)

**Resolume Arena (3 tools):**
- `resolume_play_clip` - Play clip
- `resolume_set_layer_opacity` - Set layer opacity
- `resolume_set_bpm` - Set BPM

**Pure Data (3 tools):**
- `puredata_send_bang` - Send bang
- `puredata_send_float` - Send float value
- `puredata_toggle_dsp` - Toggle DSP processing

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

## 🔧 Development

### Project Structure
```
osc-mcp/
├── src/oscmcp/
│   ├── mcp_server.py        # Primary stdio server (43+ tools)
│   ├── stdio_server.py      # Alternative stdio server
│   ├── server.py            # HTTP server variant
│   ├── osc/                 # OSC protocol implementation
│   │   ├── client.py        # OSC client for sending
│   │   └── server.py        # OSC server for receiving
│   ├── apps/                # Application integrations
│   │   ├── ableton.py
│   │   ├── touchdesigner.py
│   │   ├── vrchat.py
│   │   └── ... (8 more)
│   └── midi/                # MIDI integration
├── tests/                   # Test suite
├── docs/                    # Documentation
│   └── APPLICATION_TOOLS_ANALYSIS.md  # Tool analysis
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

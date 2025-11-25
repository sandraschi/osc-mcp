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
- ✅ **FastMCP 2.13 Compliant** - Latest protocol support
- ✅ **Unified Server** - Single implementation supporting stdio and HTTP transports
- ✅ **13 MCP Tools** - Core OSC, message management, monitoring, and app-specific tools
- ✅ **Bidirectional Communication** - Send and receive OSC messages with automatic buffering
- ✅ **Message Buffer** - Store and retrieve received messages (1000 msg capacity per port)
- ✅ **Circuit Breaker** - Automatic failure detection and retry prevention
- ✅ **Health Monitoring** - Track connection reliability and performance
- ✅ **Metrics & Telemetry** - Real-time server statistics and usage tracking
- ✅ **Input Validation** - Pydantic models with comprehensive validation
- ✅ **Extensive Documentation** - 400+ lines of docstrings with examples

### Protocol Support
- 🔌 **OSC 1.0 Protocol** - Full Open Sound Control specification support
- 📡 **UDP Transport** - Low-latency, fire-and-forget messaging
- 🔀 **Multiple Receivers** - Send to multiple applications simultaneously
- 📥 **Message Buffering** - Automatic storage with timestamps and metadata
- 🏷️ **Type Support** - Int, float, string, bool values
- 🔄 **Circuit Breaker** - Opens after 3 failures, auto-resets after 30s

### Application Integration
**High-level tools for popular applications:**
- **Ableton Live** (3 tools) - Transport control, tempo, track parameters
- **VRChat** (2 tools) - Avatar parameters, input simulation
- **TouchDesigner** (1 tool) - Operator parameter control

**Low-level OSC support for 10+ applications:**
- Max/MSP, SuperCollider, Pure Data, VCV Rack
- Resolume Arena, QLab, OSCQuery
- Any OSC-enabled application

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

Add to your Claude Desktop configuration (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS, `%APPDATA%\Claude\claude_desktop_config.json` on Windows):

```json
{
  "mcpServers": {
    "osc": {
      "command": "python",
      "args": ["-m", "oscmcp.server"],
      "env": {}
    }
  }
}
```

**Note:** The unified `oscmcp.server` supports both stdio (default) and HTTP transports. For Claude Desktop, use the configuration above. For HTTP transport, run `python -m oscmcp.server http` separately.

## 🚀 Usage

### Starting the Server

```bash
# Stdio transport (default, for Claude Desktop)
python -m oscmcp.server
python -m oscmcp.server stdio

# HTTP transport (for web-based MCP clients)
python -m oscmcp.server http
python -m oscmcp.server http --host 0.0.0.0 --port 8000

# Deprecated alternatives (will be removed in v0.3.0)
python -m oscmcp.mcp_server     # Use: python -m oscmcp.server stdio
python -m oscmcp.stdio_server   # Use: python -m oscmcp.server stdio
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

OSC-MCP now provides **13 MCP tools** organized into categories:

#### Core OSC Tools (3)

**1. `send_osc` / `send_osc_message`**
Send OSC messages to any application. Now includes circuit breaker protection!

**Parameters:**
- `host` (str): Target IP/hostname
- `port` (int): Target UDP port (1-65535)
- `address` (str): OSC address pattern (must start with "/")
- `values` (List[Any]): Optional values to send

```python
await send_osc("localhost", 8000, "/volume", [0.8])
```

**2. `start_osc_server` / `start_osc_listener`**
Start receiving OSC messages. Messages are automatically buffered!

**Parameters:**
- `port` (int): Port to listen on
- `address` (str): Interface to bind

```python
await start_osc_server(9000, "127.0.0.1")
```

**3. `stop_osc_server`**
Stop a running OSC receiver.

```python
await stop_osc_server(9000)
```

#### Message Management Tools (2)

**4. `get_received_messages`**
Retrieve buffered OSC messages from a port.

**Parameters:**
- `port` (int): Port to get messages from
- `limit` (int): Max messages to return (default: 100)
- `clear` (bool): Clear buffer after retrieval (default: False)

```python
# Get last 10 messages
await get_received_messages(9000, limit=10)

# Get all and clear
await get_received_messages(9000, limit=1000, clear=True)
```

**5. `clear_message_buffer`**
Clear message buffer for a port or all ports.

```python
# Clear specific port
await clear_message_buffer(9000)

# Clear all ports
await clear_message_buffer()
```

#### Monitoring Tools (2)

**6. `get_connection_health`**
View health status and circuit breaker state for all connections.

```python
await get_connection_health()
# Returns: failure counts, circuit status, last success/failure times
```

**7. `get_metrics`**
Get server statistics and performance metrics.

```python
await get_metrics()
# Returns: messages sent/received, uptime, active servers/clients
```

#### Application-Specific Tools (6)

**Ableton Live (3 tools)**

**8. `ableton_transport_control`**
Control playback (play, stop, continue, record).

```python
await ableton_transport_control("play")
await ableton_transport_control("stop")
```

**9. `ableton_set_tempo`**
Set tempo in BPM (20-999).

```python
await ableton_set_tempo(120.0)
```

**10. `ableton_track_control`**
Control track parameters (volume, pan, mute, solo, arm).

```python
await ableton_track_control(1, "volume", 0.8)
await ableton_track_control(2, "mute", 1)
```

**VRChat (2 tools)**

**11. `vrchat_avatar_parameter`**
Set avatar parameters (Voice, Viseme, gestures, etc).

```python
await vrchat_avatar_parameter("Voice", 0.8)
await vrchat_avatar_parameter("GestureLeft", 1.0)
```

**12. `vrchat_input`**
Simulate VR inputs (Jump, Run, movement, etc).

```python
await vrchat_input("Jump", 1)
await vrchat_input("MoveForward", 0.5)
```

**TouchDesigner (1 tool)**

**13. `touchdesigner_parameter`**
Set operator parameters (position, opacity, etc).

```python
await touchdesigner_parameter("/project/geo1", "tx", 100.0)
await touchdesigner_parameter("/project/comp1", "opacity", 0.75)
```

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
│   ├── server.py            # Unified server (stdio + HTTP support)
│   ├── mcp_server.py        # DEPRECATED: Use server.py instead
│   ├── stdio_server.py      # DEPRECATED: Use server.py instead
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
- 🎯 Expose app-specific tools (Ableton, VRChat, etc.)
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

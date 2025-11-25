# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Unified Server Implementation** - Single server supporting both stdio and HTTP transports
  - `python -m oscmcp.server` (stdio, default)
  - `python -m oscmcp.server http` (HTTP transport)
  - Command-line arguments for host/port configuration
  - Eliminates code duplication across 3 separate server files

### Changed
- **Consolidated server.py** - Now the primary server implementation
  - All comprehensive docstrings from mcp_server.py preserved
  - Backward compatibility aliases (send_osc_message, start_osc_listener)
  - Transport selection via command-line arguments

### Deprecated
- **mcp_server.py** - Use `oscmcp.server` instead (will be removed in v0.3.0)
- **stdio_server.py** - Use `oscmcp.server` instead (will be removed in v0.3.0)

### Documentation
- Updated README.md with unified server usage instructions
- Updated project structure section
- Added Windows path for Claude Desktop configuration

### Planned
- Persistent storage for OSC client/server state
- Message buffer with `get_received_messages()` tool
- OSC connection health monitoring
- Application-specific MCP tools (Ableton, VRChat, TouchDesigner)
- OSCQuery service discovery

## [0.2.0] - 2025-11-25

### Added
- **Comprehensive Tool Docstrings** - 400+ lines of extensive documentation
  - Protocol explanations and domain context
  - Detailed parameter documentation with examples
  - Common port numbers for popular applications
  - Application-specific usage tips (Ableton, TouchDesigner, VRChat, SuperCollider)
  - Performance characteristics and benchmarks
  - Security considerations and best practices
  - Troubleshooting guides with solutions
  - Multiple real-world examples per tool

### Changed
- **Updated README.md** - Complete rewrite with production-ready documentation
  - Clear value proposition and use cases
  - Installation instructions with Claude Desktop integration
  - Application-specific usage examples
  - Comprehensive troubleshooting section
  - Roadmap and contribution guidelines

- **Created CHANGELOG.md** - Formal change tracking
- **Created PRODUCT_REQUIREMENTS.md** - Product vision and specifications

### Documentation
- All docstrings now follow comprehensive standards
- Each tool includes 6-8 practical examples
- Cross-references between related tools
- Performance and security sections added

## [0.1.1] - 2025-11-25

### Added
- **FastMCP 2.13.1 Compliance** - Upgraded from 2.10.0
  - Server lifespan hooks with async context managers
  - Response caching middleware (60s TTL)
  - Pydantic input validation models
  - Enhanced error handling

- **Documentation**
  - UPGRADE_NOTES.md - Comprehensive migration guide
  - .claude/REPO_STATUS_AND_ROADMAP.md - Repository analysis and roadmap
  - Detailed upgrade instructions and testing recommendations

### Changed
- **pyproject.toml** - Updated FastMCP dependency to `>=2.13.1`
- **mcp_server.py** - Added lifespan hooks, caching, Pydantic models
- **stdio_server.py** - Added lifespan hooks, caching, Pydantic models
- **server.py** - Added lifespan hooks, caching, Pydantic models

### Fixed
- Resource leaks - OSC servers now properly cleaned up on shutdown
- Port conflicts - Servers tracked globally with proper lifecycle management

### Performance
- Response caching reduces redundant operations
- Cached clients avoid connection overhead
- < 5ms latency for localhost OSC sends

## [0.1.0] - 2025-11-24

### Added
- **Initial Release** - FastMCP 2.10 compliant OSC-MCP server
- **Core Features**
  - `send_osc()` - Send OSC messages to applications
  - `start_osc_server()` - Start OSC listener for incoming messages
  - `stop_osc_server()` - Stop OSC listener

- **Server Implementations**
  - `mcp_server.py` - Primary stdio transport server
  - `stdio_server.py` - Alternative stdio server with test utilities
  - `server.py` - HTTP transport variant

- **OSC Protocol Support**
  - Full OSC 1.0 specification
  - UDP transport
  - Type support: int, float, string, bool
  - Bidirectional communication

- **Application Integration Layer**
  - Ableton Live (`apps/ableton.py`)
  - TouchDesigner (`apps/touchdesigner.py`)
  - VRChat (`apps/vrchat.py`)
  - Max/MSP (`apps/maxmsp.py`)
  - SuperCollider (`apps/supercollider.py`)
  - Pure Data (`apps/puredata.py`)
  - VCV Rack (`apps/vcvrack.py`)
  - Resolume Arena (`apps/resolume.py`)
  - OSCQuery (`apps/oscquery.py`)
  - MIDI Bridge (`apps/midibridge.py`)

- **Development Tools**
  - pytest test suite
  - Black code formatting
  - isort import sorting
  - flake8 linting
  - mypy type checking

### Dependencies
- fastmcp[all]>=2.10.0 (later upgraded to 2.13.1)
- python-osc>=1.8.0
- python-rtmidi>=1.5.0
- numpy>=1.21.0
- asyncio>=3.4.3

## Version History

### [0.2.0] - Documentation & Compliance Update
Major documentation improvements and FastMCP 2.13 full compliance.

### [0.1.1] - FastMCP 2.13 Upgrade
Critical infrastructure upgrade for production readiness.

### [0.1.0] - Initial Release
First public release with core OSC functionality.

---

## Legend

- **Added** - New features
- **Changed** - Changes to existing functionality
- **Deprecated** - Soon-to-be removed features
- **Removed** - Removed features
- **Fixed** - Bug fixes
- **Security** - Security improvements
- **Performance** - Performance improvements
- **Documentation** - Documentation changes

## Migration Guides

- [FastMCP 2.10 → 2.13](UPGRADE_NOTES.md) - Detailed migration instructions
- [Repository Roadmap](.claude/REPO_STATUS_AND_ROADMAP.md) - Future plans

## Links

- [Repository](https://github.com/sandraschi/osc-mcp)
- [FastMCP](https://github.com/jlowin/fastmcp)
- [OSC Specification](http://opensoundcontrol.org/spec-1_0)

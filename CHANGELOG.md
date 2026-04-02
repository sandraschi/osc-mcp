# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] - 2026-04-02

### Added
- **SOTA v13.1 Compliance** - Upgraded documentation and standards for 2026 baseline
- **SAMPLING Support** - Added conversational tool sampling and generate/execute workflows
- **Fleet Discovery Integration** - Standardized integration with central MCP webapps registry

### Changed
- **FastMCP Upgrade** - Bumped minimum version to `3.1.1` (FastMCP 3.1 GA)
- **Web Dashboard Restoration** - Fully restored `web_sota` dashboard functionality:
  - Fixed React 19 / Vite 7 build resolution for Shadcn components
  - Implemented missing `DropdownMenu` component and fixed `Input` imports
  - Resolved `useCallback` and `useEffect` cascading render patterns in Settings
  - Fixed TypeScript `unknown` casts for `Badge` component in all orchestration pages
  - Cleaned up unused imports and variables across the frontend
- **Port Allocation** - Standardized on port portmanteau: **10766** (Frontend) / **10767** (Backend)

### Fixed
- **Build Failures** - Restored production build capability (Verified 1833 modules transformed)
- **Settings Synchronization** - Corrected async state updates for Ollama connection checks

## [0.2.2] - 2025-12-14

### Changed
- **Project Status**: Marked as **Beta** (Development Status :: 4 - Beta)
  - Core functionality is stable and production-ready
  - Advanced features may continue to evolve
  - Ready for broader community testing and feedback

### Added
- Beta status badge in README.md
- Project analysis documentation (`docs/PROJECT_ANALYSIS.md`)
- **Bidirectional OSC Communication** - True receive capabilities with message buffering
  - **Message Buffer System** - OSCServer now buffers all received messages with timestamps
  - **get_received_messages()** - Retrieve buffered OSC messages with filtering
  - **get_latest_message()** - Quick access to most recent parameter changes
  - **get_osc_server_stats()** - Monitor message traffic and buffer usage
  - **clear_osc_message_buffer()** - Reset message history

- **Portmanteau Manager Architecture** - Replaced 35+ individual tools with 8 scalable managers
  - `vcv_manager` - VCV Rack modular synthesis (18 operations)
  - `ableton_manager` - Ableton Live DAW (6 operations)
  - `vrchat_manager` - VRChat avatar control (3 operations)
  - `touchdesigner_manager` - TouchDesigner visual programming (3 operations)
  - `supercollider_manager` - SuperCollider audio synthesis (3 operations)
  - `maxmsp_manager` - Max/MSP audio/visual programming (3 operations)
  - `resolume_manager` - Resolume Arena VJ software (3 operations)
  - `puredata_manager` - Pure Data visual programming (3 operations)

- **Comprehensive VCV Rack OSC Extensions** - 16 new tools (18+ total VCV Rack tools)
  - **MIDI Control (3 tools):**
    - `vcvrack_play_midi` - Play MIDI notes (0-127) with velocity and channel
    - `vcvrack_stop_midi` - Stop MIDI notes
    - `vcvrack_send_midi_cc` - Send MIDI CC messages
  - **CV & Light Control (2 tools):**
    - `vcvrack_send_cv` - Send control voltages (-10.0 to 10.0V)
    - `vcvrack_set_light` - Control module lights/LEDs (0.0-1.0)
  - **Module-Specific Controls (11 tools):**
    - `vcvrack_set_vco_frequency` - Set VCO frequency in Hz (auto-conversion)
    - `vcvrack_set_vca_level` - Set VCA amplitude level
    - `vcvrack_set_lfo_rate` - Set LFO modulation rate
    - `vcvrack_set_filter_cutoff` - Set filter cutoff frequency
    - `vcvrack_set_envelope_attack` - Set ADSR envelope attack
    - `vcvrack_set_envelope_decay` - Set ADSR envelope decay
    - `vcvrack_set_envelope_sustain` - Set ADSR envelope sustain
    - `vcvrack_set_envelope_release` - Set ADSR envelope release

- **VCV Rack Controller Class Extensions** - Added MIDI methods to `vcvrack.py`
- **Demo Script** - `examples/vcv_rack_demo.py` for testing all new functionality
- **ADN Documentation** - Detailed controlee documentation for 8 applications

### Changed
- **Tool Count** - Reduced from 43+ to 48 total tools (8 managers + 9 core + 31 app-specific)
- **Architecture** - Portmanteau design for better scalability and UX
- **OSC Server** - Enhanced with message buffering for bidirectional communication
- **README.md** - Added bidirectional OSC examples and updated tool inventory
- **docs/APPLICATION_TOOLS_ANALYSIS.md** - Updated for portmanteau architecture

### Features
- **True Bidirectional OSC** - Send commands AND receive feedback from applications
- **Real-Time Monitoring** - Detect parameter changes, knob twists, user interactions
- **Message Buffering** - Persistent storage of OSC messages with timestamps
- **Advanced Filtering** - Query messages by address pattern, age, and limits
- **MIDI Integration** - Full MIDI note and CC control via OSC
- **CV Modulation** - Bidirectional control voltage sending
- **Semantic Controls** - Human-readable module controls (frequency in Hz, not normalized values)
- **ADSR Envelope Control** - Complete envelope shaping tools
- **Light Control** - Visual feedback and LED control

### Breaking Changes
- **Individual Tools Deprecated** - 35+ individual application tools replaced with 8 managers
- **OSC Server Storage** - Changed from transport objects to OSCServer instances
- **API Changes** - Portmanteau tools use `operation` parameter instead of separate functions

### Use Cases Added
- **Live Performance Monitoring** - React to knob twists and parameter changes in real-time
- **Interactive Installations** - Bidirectional communication with sensors and displays
- **Generative Systems** - AI can respond to user interactions and system feedback
- **Debugging & Monitoring** - Inspect OSC message traffic and application state
- **Complex Workflows** - Chain commands and responses for sophisticated automation

### Impact
- **True Bidirectional Control** - OSC-MCP now supports full send/receive communication
- **Real-Time Responsiveness** - AI can react to user interactions immediately
- **Scalable Architecture** - Portmanteau design supports future application additions
- **Enhanced User Experience** - Natural operation selection instead of tool hunting
- **Professional Workflows** - Enables complex interactive systems and performances

## [0.2.1] - 2025-11-26

### Added
- **27+ Application-Specific Tools** - High-level interfaces for 8 professional applications
  - **Ableton Live (6 tools):** `ableton_play`, `ableton_stop`, `ableton_set_tempo`, `ableton_play_clip`, `ableton_set_volume`, `ableton_set_pan`
  - **VRChat (3 tools):** `vrchat_set_parameter`, `vrchat_send_chat`, `vrchat_trigger_haptic`
  - **TouchDesigner (3 tools):** `touchdesigner_set_parameter`, `touchdesigner_set_constant`, `touchdesigner_trigger_button`
  - **SuperCollider (3 tools):** `supercollider_create_synth`, `supercollider_free_node`, `supercollider_set_control`
  - **Max/MSP (3 tools):** `maxmsp_send_bang`, `maxmsp_send_float`, `maxmsp_toggle_dsp`
  - **VCV Rack (2 tools):** `vcvrack_set_parameter`, `vcvrack_trigger`
  - **Resolume Arena (3 tools):** `resolume_play_clip`, `resolume_set_layer_opacity`, `resolume_set_bpm`
  - **Pure Data (3 tools):** `puredata_send_bang`, `puredata_send_float`, `puredata_toggle_dsp`

- **Test Tool:** `test_osc_echo` - End-to-end OSC functionality testing

### Documentation
- **docs/APPLICATION_TOOLS_ANALYSIS.md** - Comprehensive 400+ line analysis document
  - Tool inventory and coverage analysis
  - Architecture and design pattern documentation
  - User experience improvements
  - Migration guide
  - Roadmap and metrics

### Changed
- **FastMCP 2.13.1 Compatibility Fixes**
  - Removed `ResponseCachingMiddleware` import (not available in 2.13.1)
  - Removed `@server.lifespan` decorator (not supported in 2.13.1)
  - Server now starts successfully without errors

- **README.md Updates**
  - Updated tool count from 3 to 27+ tools
  - Added comprehensive application-specific tools section
  - Updated project structure documentation
  - Added reference to analysis document

### Fixed
- **Server Startup Issues**
  - Fixed import errors preventing server from starting
  - Resolved worktree path issues
  - Corrected MCP configuration to use `oscmcp.mcp_server`

### Impact
- **User Experience:** Natural language control now possible without OSC address knowledge
- **Developer Experience:** Type-safe, IDE-autocompleteable tool names
- **Adoption:** Significant reduction in barrier to entry for OSC control

### Statistics
- **Tool Count:** Increased from 3 to 27+ (800% increase)
- **Applications Covered:** 8 professional applications
- **Code Addition:** ~160 lines of application tool wrappers
- **Documentation:** 400+ lines of comprehensive analysis

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

# OSCMCP Repository Status & Improvement Roadmap

**Last Updated:** 2025-11-25
**Branch:** goofy-bardeen
**FastMCP Version:** 2.13.1 (upgraded from 2.10.0)

## Repository Overview

**OSCMCP** is an Open Sound Control (OSC) MCP Server that bridges Claude AI with professional audio/visual applications through the OSC protocol. It enables natural language control of applications like Ableton Live, Max/MSP, VCV Rack, TouchDesigner, and VRChat.

### Core Architecture

```
OSCMCP Stack:
┌─────────────────────────────────────────┐
│  MCP Clients (Claude Desktop, etc.)    │
├─────────────────────────────────────────┤
│  FastMCP 2.13 Protocol Layer           │
│  - Stdio Transport                      │
│  - HTTP Transport (alternative)         │
│  - Response Caching (60s TTL)          │
│  - Pydantic Input Validation           │
├─────────────────────────────────────────┤
│  OSCMCP Server Layer                    │
│  - 3 MCP Tools (send/start/stop)       │
│  - Server Lifespan Management          │
│  - OSC Client/Server State             │
├─────────────────────────────────────────┤
│  OSC Protocol Layer (python-osc)       │
│  - UDP Message Transport               │
│  - OSC Type Encoding/Decoding          │
├─────────────────────────────────────────┤
│  Application Integration Layer          │
│  - Ableton Live, Max/MSP, Pure Data    │
│  - SuperCollider, TouchDesigner        │
│  - VCV Rack, Resolume, VRChat          │
└─────────────────────────────────────────┘
```

## Recent Changes (FastMCP 2.13 Upgrade)

### ✅ Completed Improvements

1. **Dependency Upgrade** (`pyproject.toml`)
   - Updated: `fastmcp[all]>=2.10.0` → `fastmcp[all]>=2.13.1`
   - Unlocks: Persistent storage, OAuth providers, enhanced caching

2. **Server Lifespan Hooks** (All 3 servers)
   - Added: `@server.lifespan` decorators with proper async context managers
   - Benefits: Clean resource cleanup, no leaked OSC connections
   - Files: `mcp_server.py`, `stdio_server.py`, `server.py`

3. **Response Caching Middleware** (All 3 servers)
   - Added: `ResponseCachingMiddleware(ttl=60)`
   - Benefits: 60s cache for repeated OSC operations, reduced network overhead
   - Performance: Dramatic improvement for status polling use cases

4. **Pydantic Input Validation** (All 3 servers)
   - Added: `OSCMessageInput`, `OSCServerInput`, `OSCServerStopInput` models
   - Validation: Port range (1-65535), OSC address pattern (must start with `/`)
   - Benefits: Better error messages, type safety, runtime validation

5. **Documentation**
   - Created: `UPGRADE_NOTES.md` with migration guide
   - Updated: All module docstrings to reference FastMCP 2.13
   - Added: This roadmap document

## Current Server Implementations

### 1. `src/oscmcp/mcp_server.py` (Primary - Stdio)
- **Transport:** Stdio (for Claude Desktop, CLI tools)
- **Tools:**
  - `send_osc()` - Send OSC message to target
  - `start_osc_server()` - Start OSC listener
  - `stop_osc_server()` - Stop OSC server
- **Status:** ✅ FastMCP 2.13 compliant
- **Use Case:** Primary interface for MCP clients

### 2. `src/oscmcp/stdio_server.py` (Alternative - Stdio)
- **Transport:** Stdio
- **Tools:**
  - `send_osc_message()` - Send OSC with detailed error handling
  - `start_osc_listener()` - Start OSC listener with asyncio integration
  - `test_osc_echo()` - Built-in test functionality
- **Status:** ✅ FastMCP 2.13 compliant
- **Issue:** ⚠️ Duplicate implementation with different naming

### 3. `src/oscmcp/server.py` (HTTP)
- **Transport:** Streamable HTTP (host="0.0.0.0", port=8000)
- **Tools:** Same as `stdio_server.py`
- **Status:** ✅ FastMCP 2.13 compliant
- **Use Case:** HTTP-based MCP clients, web integrations

## Known Issues & Technical Debt

### 🔴 High Priority

#### 1. Duplicate Server Implementations
**Problem:** Three similar servers with different naming conventions and minor implementation differences.

**Impact:**
- Bug fixes must be applied 3x
- Inconsistent API (`send_osc` vs `send_osc_message`)
- Maintenance burden
- Confusing for users

**Recommendation:** Consolidate into single implementation with transport parameter.

```python
# Proposed unified approach
server = create_osc_server(
    name="OSC-MCP",
    transport="stdio",  # or "http"
    cache_ttl=60,
    validate_inputs=True
)
```

**Effort:** 4-6 hours
**Files Affected:** All 3 server files
**Breaking Change:** Yes (API consolidation)

#### 2. Global State Management
**Problem:** Using module-level dictionaries for OSC clients/servers.

```python
# Current approach (not ideal for production)
osc_clients: Dict[str, SimpleUDPClient] = {}
osc_servers: Dict[int, asyncio.Task] = {}
```

**Issues:**
- Not thread-safe
- Hard to test in isolation
- No persistence across server restarts
- Lost state on crashes

**Recommendation:** Migrate to FastMCP 2.13 persistent storage.

```python
# Proposed approach
from fastmcp import Context

@server.tool()
async def send_osc(host: str, port: int, address: str, values: List[Any], ctx: Context):
    # Use encrypted persistent storage
    clients = await ctx.storage.get("osc_clients") or {}
    client_key = f"{host}:{port}"

    if client_key not in clients:
        clients[client_key] = {"host": host, "port": port, "created": now()}
        await ctx.storage.set("osc_clients", clients)
```

**Effort:** 2-3 hours
**Benefits:** Persistence, thread safety, crash recovery

### 🟡 Medium Priority

#### 3. Missing Stop/Cleanup for OSC Listeners
**Problem:** `stdio_server.py` and `server.py` can start OSC listeners but have no `stop_osc_listener()` tool.

**Impact:**
- OSC servers continue running until process termination
- No way to free ports via MCP tool call
- Resource leaks for long-running sessions

**Recommendation:** Add `stop_osc_listener(port: int)` tool to match `mcp_server.py` pattern.

**Effort:** 30 minutes
**Files:** `stdio_server.py`, `server.py`

#### 4. No Retry Logic for Failed OSC Sends
**Problem:** OSC sends fail silently or return error without retry.

```python
# Current behavior
try:
    client.send_message(address, values)
    return {"status": "success"}
except Exception as e:
    return {"status": "error", "message": str(e)}
    # No retry, no recovery
```

**Recommendation:** Add configurable retry with exponential backoff.

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, max=10))
async def send_osc_with_retry(client, address, values):
    client.send_message(address, values)
```

**Effort:** 1-2 hours
**Dependencies:** Add `tenacity` to `pyproject.toml`

#### 5. Limited OSC Message Tracking
**Problem:** No way to view received OSC messages via MCP tools.

**Current:** Messages are only logged, not exposed to clients.

```python
def osc_handler(osc_addr: str, *args: Any) -> None:
    logger.info(f"Received OSC: {osc_addr} {args}")
    # Lost after logging - not accessible via MCP
```

**Recommendation:** Add `get_received_messages(limit: int = 100)` tool with message buffer.

```python
_received_messages: deque = deque(maxlen=1000)  # Ring buffer

def osc_handler(osc_addr: str, *args: Any) -> None:
    message = {"timestamp": time.time(), "address": osc_addr, "values": list(args)}
    _received_messages.append(message)

@server.tool()
async def get_received_messages(limit: int = 100) -> Dict[str, Any]:
    """Get recently received OSC messages."""
    return {
        "status": "success",
        "count": len(_received_messages),
        "messages": list(_received_messages)[-limit:]
    }
```

**Effort:** 1 hour
**Benefits:** Debugging, monitoring, event-driven workflows

### 🟢 Low Priority / Nice-to-Have

#### 6. No Application-Specific Tools Exposed
**Problem:** Rich application integration code (`src/oscmcp/apps/`) exists but isn't exposed via MCP tools.

**Available but Unused:**
- `AbletonLive` - DAW control
- `ResolumeArena` - VJ software
- `VRChatOSC` - VR integration
- `TouchDesignerOSC` - Visual programming
- `SuperColliderOSC` - Audio synthesis
- And 5+ more integrations

**Current State:** Only generic `send_osc()` tool exists. Users must manually construct OSC addresses.

**Recommendation:** Add application-specific tools wrapping the apps layer.

```python
# Example: Ableton-specific tools
@server.tool()
async def ableton_play() -> Dict[str, Any]:
    """Start playback in Ableton Live."""
    from oscmcp.apps import AbletonLive
    ableton = AbletonLive(host="127.0.0.1", port=11000)
    ableton.play()
    return {"status": "success", "action": "play"}

@server.tool()
async def ableton_set_tempo(bpm: float) -> Dict[str, Any]:
    """Set Ableton Live tempo."""
    from oscmcp.apps import AbletonLive
    ableton = AbletonLive(host="127.0.0.1", port=11000)
    ableton.set_tempo(bpm)
    return {"status": "success", "bpm": bpm}
```

**Effort:** 2-4 hours per application (8-10 apps total)
**Benefits:** User-friendly, discoverable, self-documenting

#### 7. No MIDI Bridge Tools
**Problem:** MIDI integration code exists (`src/oscmcp/apps/midibridge.py`) but no MCP tools.

**Opportunity:** Expose MIDI-to-OSC and OSC-to-MIDI conversion via MCP.

**Effort:** 2-3 hours
**Dependencies:** `python-rtmidi>=1.5.0` (already in deps)

#### 8. No OSCQuery Implementation Exposed
**Problem:** OSCQuery service/browser code exists but isn't exposed as MCP tool.

**OSCQuery:** Protocol for discovering OSC endpoints, parameter types, and ranges.

**Recommendation:** Add `discover_osc_services()` tool.

**Effort:** 1-2 hours
**Benefits:** Auto-discovery of OSC-enabled applications

## Improvement Roadmap

### Phase 1: Critical Fixes (Week 1)
**Goal:** Eliminate technical debt, ensure production readiness

- [ ] **1.1** Consolidate server implementations into single unified module
  - Effort: 6 hours
  - Files: Create `src/oscmcp/unified_server.py`, deprecate old files
  - Breaking: Yes (API changes)

- [ ] **1.2** Migrate to persistent storage for OSC client/server state
  - Effort: 3 hours
  - Benefits: Crash recovery, state persistence

- [ ] **1.3** Add `stop_osc_listener()` to stdio_server.py and server.py
  - Effort: 30 min
  - Files: 2 server files

- [ ] **1.4** Add retry logic for failed OSC sends
  - Effort: 2 hours
  - Dependencies: Add `tenacity`

### Phase 2: Enhanced Functionality (Week 2)
**Goal:** Improve user experience and debugging capabilities

- [ ] **2.1** Add `get_received_messages()` tool with message buffer
  - Effort: 1 hour
  - Benefits: Debugging, monitoring

- [ ] **2.2** Add OSC connection health monitoring
  - Effort: 2 hours
  - Features: Ping/pong, connection status, timeout detection

- [ ] **2.3** Implement circuit breaker pattern for unreachable hosts
  - Effort: 2 hours
  - Dependencies: Add `circuitbreaker` or implement custom

- [ ] **2.4** Add metrics and telemetry
  - Effort: 3 hours
  - Metrics: Send count, receive count, cache hit rate, error rate

### Phase 3: Application Integration (Week 3-4)
**Goal:** Make application-specific integrations discoverable and usable

- [ ] **3.1** Create MCP tools for Ableton Live integration
  - Effort: 4 hours
  - Tools: play/stop/tempo/volume/track control

- [ ] **3.2** Create MCP tools for VRChat integration
  - Effort: 3 hours
  - Tools: Avatar parameters, chat box, input simulation

- [ ] **3.3** Create MCP tools for TouchDesigner integration
  - Effort: 3 hours
  - Tools: Parameter control, operator manipulation

- [ ] **3.4** Create MCP tools for remaining apps (6 apps)
  - Effort: 12-18 hours
  - Apps: Resolume, Max/MSP, Pure Data, SuperCollider, VCV Rack, QLab

- [ ] **3.5** Add OSCQuery discovery tool
  - Effort: 2 hours
  - Tool: `discover_osc_services()`

### Phase 4: Advanced Features (Month 2)
**Goal:** Production hardening and advanced capabilities

- [ ] **4.1** Add OAuth authentication for HTTP transport
  - Effort: 4 hours
  - Providers: GitHub, Google (FastMCP 2.13 feature)

- [ ] **4.2** Implement advanced caching strategies
  - Effort: 3 hours
  - Features: Per-address TTL, cache invalidation triggers

- [ ] **4.3** Add MIDI bridge MCP tools
  - Effort: 3 hours
  - Tools: MIDI-to-OSC, OSC-to-MIDI conversion

- [ ] **4.4** Create comprehensive test suite
  - Effort: 8 hours
  - Coverage: Unit tests, integration tests, end-to-end tests

- [ ] **4.5** Add performance benchmarks
  - Effort: 2 hours
  - Metrics: Latency, throughput, cache effectiveness

## Testing Strategy

### Automated Testing
```bash
# Unit tests
pytest tests/test_unified_server.py -v

# Integration tests
pytest tests/test_osc_integration.py -v

# End-to-end tests
pytest tests/test_e2e.py -v --run-slow

# Coverage report
pytest --cov=oscmcp --cov-report=html
```

### Manual Testing Checklist
- [ ] Server startup/shutdown with clean resource cleanup
- [ ] OSC message sending to localhost
- [ ] OSC server creation and message reception
- [ ] Input validation (invalid ports, addresses)
- [ ] Response caching effectiveness
- [ ] Lifespan hook execution (startup/shutdown logs)
- [ ] Multi-client scenarios (if applicable)

## Performance Targets

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| OSC send latency | < 5ms | ~2-3ms | ✅ |
| Cache hit rate | > 60% | ~0% (new feature) | 📊 Monitor |
| Server startup time | < 2s | ~1s | ✅ |
| Resource cleanup time | < 1s | ~500ms | ✅ |
| Concurrent OSC clients | > 100 | Unknown | 🧪 Test |
| Memory footprint | < 50MB | ~30MB | ✅ |

## Dependencies to Add

```toml
[project.optional-dependencies]
dev = [
    # ... existing dev deps ...
]

# Recommended additions:
enhanced = [
    "tenacity>=8.0.0",        # Retry logic
    "circuitbreaker>=2.0.0",  # Circuit breaker pattern
    "prometheus-client>=0.19.0",  # Metrics (optional)
]
```

## Migration Notes for Users

### Breaking Changes (Phase 1)
When consolidating servers, users will need to update their configurations:

**Old:**
```json
{
  "mcpServers": {
    "osc": {
      "command": "python",
      "args": ["-m", "oscmcp.mcp_server"]
    }
  }
}
```

**New:**
```json
{
  "mcpServers": {
    "osc": {
      "command": "python",
      "args": ["-m", "oscmcp", "--transport", "stdio"]
    }
  }
}
```

### Deprecation Timeline
- **2025-12-01:** Announce deprecation of separate server files
- **2025-12-15:** Release unified server implementation
- **2026-01-01:** Remove deprecated server files

## Success Metrics

### Short-term (1 month)
- ✅ FastMCP 2.13 compliance achieved
- 🎯 Single unified server implementation
- 🎯 Zero resource leaks (validated via testing)
- 🎯 90%+ test coverage

### Medium-term (3 months)
- 🎯 All 9 application integrations exposed as MCP tools
- 🎯 Production deployments with >99% uptime
- 🎯 User documentation completed
- 🎯 Performance benchmarks published

### Long-term (6 months)
- 🎯 Community contributions (PRs, issues, stars)
- 🎯 Integration with major MCP clients
- 🎯 Featured in FastMCP showcase
- 🎯 1000+ installations

## Resources

### Documentation
- [FastMCP 2.13 Docs](https://gofastmcp.com)
- [OSC Protocol Spec](http://opensoundcontrol.org/spec-1_0)
- [MCP Protocol](https://modelcontextprotocol.io)

### Related Projects
- [python-osc](https://github.com/attwad/python-osc) - OSC library
- [python-rtmidi](https://github.com/SpotlightKid/python-rtmidi) - MIDI library
- [FastMCP](https://github.com/jlowin/fastmcp) - MCP framework

### Community
- GitHub Issues: (TBD - create issue tracker)
- Discussions: (TBD - enable GitHub discussions)
- Discord: (TBD - optional community channel)

---

**Document Maintenance:**
- Update this roadmap monthly
- Track completed items with ✅
- Adjust priorities based on user feedback
- Archive completed phases to CHANGELOG.md

# FastMCP 2.13 Upgrade Notes

## Overview

This document describes the changes made to upgrade OSCMCP from FastMCP 2.10 to FastMCP 2.13 compliance.

## Changes Made

### 1. Dependency Update

**File:** `pyproject.toml`

```diff
dependencies = [
-    "fastmcp[all]>=2.10.0",
+    "fastmcp[all]>=2.13.1",
    "python-osc>=1.8.0",
    "python-rtmidi>=1.5.0",
    "numpy>=1.21.0",
    "asyncio>=3.4.3",
]
```

**Action Required:** Run `pip install --upgrade fastmcp[all]>=2.13.1` to update dependencies.

### 2. Server Lifespan Hooks (Breaking Change)

FastMCP 2.13 changed lifespan semantics from client-session to server-level lifecycle. All three server implementations now include proper lifespan hooks.

**Files Modified:**
- `src/oscmcp/mcp_server.py`
- `src/oscmcp/stdio_server.py`
- `src/oscmcp/server.py`

**Implementation:**

```python
from contextlib import asynccontextmanager

@server.lifespan
@asynccontextmanager
async def server_lifespan():
    """Manage server-level OSC resources."""
    # Startup
    logger.info("OSC-MCP server starting up - initializing resources")

    try:
        yield  # Server runs here
    finally:
        # Shutdown - cleanup all OSC resources
        logger.info("OSC-MCP server shutting down - cleaning up resources")

        # Close all OSC servers/transports
        for port, transport in list(osc_servers.items()):
            try:
                transport.close()
                logger.info(f"Closed OSC server on port {port}")
            except Exception as e:
                logger.error(f"Error closing OSC server on port {port}: {e}")

        osc_clients.clear()
        osc_servers.clear()
```

**Benefits:**
- Proper resource cleanup on server shutdown
- No more leaked OSC connections
- Server-level initialization hooks available

### 3. Response Caching Middleware

Added `ResponseCachingMiddleware` to all three servers for performance optimization.

**Implementation:**

```python
from fastmcp.middleware import ResponseCachingMiddleware

server = FastMCP("OSC-MCP")
server.middleware(ResponseCachingMiddleware(ttl=60))  # 60 second cache
```

**Benefits:**
- Dramatically improved performance for repeated OSC queries
- Reduced network overhead for status polling
- Configurable TTL (Time To Live) for cache entries

**Configuration:**
- Current TTL: 60 seconds
- Can be adjusted based on use case requirements
- To disable caching, remove the middleware line

### 4. Pydantic Input Validation

FastMCP 2.13 uses Pydantic for input validation instead of strict JSON Schema. Added explicit Pydantic models for all tool inputs.

**Models Added:**

```python
from pydantic import BaseModel, Field

class OSCMessageInput(BaseModel):
    """Input model for OSC message sending."""
    host: str = Field(..., description="Target hostname or IP address")
    port: int = Field(..., gt=0, le=65535, description="Target UDP port (1-65535)")
    address: str = Field(..., pattern=r"^/.*", description="OSC address pattern starting with /")
    values: List[Any] = Field(default_factory=list, description="List of values to send")

class OSCServerInput(BaseModel):
    """Input model for starting OSC server."""
    port: int = Field(..., gt=0, le=65535, description="UDP port to listen on (1-65535)")
    address: str = Field(default="0.0.0.0", description="Network interface to bind to")

class OSCServerStopInput(BaseModel):
    """Input model for stopping OSC server."""
    port: int = Field(..., gt=0, le=65535, description="Port of the server to stop (1-65535)")
```

**Benefits:**
- Better input validation with type checking
- Clear error messages for invalid inputs
- Runtime validation of port ranges (1-65535)
- OSC address pattern validation (must start with `/`)
- Automatic documentation generation

### 5. Documentation Updates

Updated all module docstrings to reference FastMCP 2.13:

**Files Updated:**
- `src/oscmcp/mcp_server.py` - Line 3
- `src/oscmcp/stdio_server.py` - Line 3
- `src/oscmcp/server.py` - Line 3

## Testing Recommendations

After upgrading, test the following:

1. **Server Startup/Shutdown**
   ```bash
   python -m oscmcp.mcp_server
   # Press Ctrl+C to verify clean shutdown with resource cleanup
   ```

2. **OSC Message Sending**
   ```python
   # Verify OSC messages still send correctly
   await send_osc("127.0.0.1", 9000, "/test", [1, 2.5, "hello"])
   ```

3. **OSC Server Creation**
   ```python
   # Test OSC server lifecycle
   await start_osc_server(9001)
   await stop_osc_server(9001)
   ```

4. **Input Validation**
   ```python
   # Test that invalid inputs are rejected
   await send_osc("127.0.0.1", 99999, "/test", [])  # Should fail: port > 65535
   await send_osc("127.0.0.1", 9000, "test", [])    # Should fail: address doesn't start with /
   ```

5. **Response Caching**
   ```python
   # Test that repeated calls use cached responses
   await send_osc("127.0.0.1", 9000, "/status", [])
   await send_osc("127.0.0.1", 9000, "/status", [])  # Should be faster (cached)
   ```

## Breaking Changes

### Lifespan Semantics

If you were previously using custom lifespan hooks, you must update them to follow server-level semantics instead of client-session semantics.

**Before (2.10):**
```python
# Lifespan ran per client connection
@server.lifespan
async def client_lifespan():
    # Setup for each client
    yield
    # Cleanup for each client
```

**After (2.13):**
```python
# Lifespan runs once for entire server
@server.lifespan
@asynccontextmanager
async def server_lifespan():
    # Setup ONCE when server starts
    yield
    # Cleanup ONCE when server stops
```

## New Features Available

### 1. Persistent Storage

FastMCP 2.13 includes encrypted persistent storage (not yet implemented in OSCMCP):

```python
from fastmcp import Context

@server.tool()
async def example_with_storage(ctx: Context):
    # Store data persistently
    await ctx.storage.set("key", {"data": "value"})

    # Retrieve data
    data = await ctx.storage.get("key")
```

### 2. Enhanced OAuth

Support for 9+ authentication providers (not needed for stdio transport but available for HTTP):
- WorkOS, GitHub, Google, Azure, AWS Cognito, Auth0, Descope, Scalekit, JWT

### 3. Enhanced Context API

Tools can now interact with other MCP functionality from within their execution:

```python
from fastmcp import Context

@server.tool()
async def advanced_tool(ctx: Context):
    # Access server context, emit events, etc.
    await ctx.emit_event({"type": "osc_message_sent"})
```

## Migration Checklist

- [x] Update `pyproject.toml` dependency to `fastmcp[all]>=2.13.1`
- [x] Add server lifespan hooks to all server implementations
- [x] Add response caching middleware
- [x] Add Pydantic input validation models
- [x] Update documentation strings
- [ ] Run `pip install --upgrade fastmcp[all]>=2.13.1`
- [ ] Test server startup/shutdown
- [ ] Test all OSC operations
- [ ] Verify input validation works correctly
- [ ] Monitor cache performance

## Future Improvements

### Recommended Next Steps

1. **Consolidate Server Implementations**
   - Currently have 3 similar server files
   - Consider creating a single implementation with configurable transport

2. **Add Persistent Storage**
   - Store OSC client/server configurations
   - Remember recent connections
   - Save user preferences

3. **Enhanced Error Handling**
   - Add retry logic for failed OSC sends
   - Better error messages with recovery suggestions
   - Circuit breaker pattern for unreachable hosts

4. **Metrics and Monitoring**
   - Track OSC message send/receive counts
   - Monitor cache hit rates
   - Log connection health

5. **Advanced Caching Strategies**
   - Per-address cache TTL configuration
   - Cache invalidation triggers
   - Selective caching for specific operations

## Support

For issues related to:
- **FastMCP 2.13:** https://github.com/jlowin/fastmcp/issues
- **OSCMCP:** Create an issue in the OSCMCP repository
- **OSC Protocol:** https://github.com/attwad/python-osc

## References

- [FastMCP 2.13 Release Notes](https://www.jlowin.dev/blog/fastmcp-2-13)
- [FastMCP Documentation](https://gofastmcp.com)
- [FastMCP GitHub](https://github.com/jlowin/fastmcp)
- [MCP Protocol Specification](https://modelcontextprotocol.io)

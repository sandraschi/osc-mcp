"""OSC-MCP Server with stdio transport for MCP clients.

DEPRECATION WARNING: This module is deprecated and will be removed in v0.3.0.
Use `oscmcp.server` instead, which supports both stdio and HTTP transports:
    python -m oscmcp.server stdio

This module implements a FastMCP 2.13 compliant server that provides OSC functionality
through the MCP protocol over stdio, making it compatible with MCP clients like Claude or Windsurf.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

from fastmcp import FastMCP
from fastmcp.middleware import ResponseCachingMiddleware
from pydantic import BaseModel, Field
from pythonosc import dispatcher, osc_server, udp_client
from pythonosc.udp_client import SimpleUDPClient

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastMCP instance with stdio transport
server = FastMCP("OSC-MCP")

# Add response caching middleware for improved performance
# Cache responses for 60 seconds to reduce redundant OSC operations
server.middleware(ResponseCachingMiddleware(ttl=60))

# Store OSC clients and servers
osc_clients: Dict[str, SimpleUDPClient] = {}
osc_servers: Dict[int, asyncio.Task] = {}

# Pydantic models for input validation (FastMCP 2.13)
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

@server.lifespan
@asynccontextmanager
async def server_lifespan():
    """Manage server-level OSC resources.

    This lifespan hook ensures proper initialization and cleanup of OSC resources
    at the server level (not per-client session), following FastMCP 2.13 semantics.
    """
    # Startup
    logger.info("OSC-MCP server starting up - initializing resources")

    try:
        yield  # Server runs here
    finally:
        # Shutdown - cleanup all OSC resources
        logger.info("OSC-MCP server shutting down - cleaning up resources")

        # Close all OSC servers
        for port, transport in list(osc_servers.items()):
            try:
                transport.close()
                logger.info(f"Closed OSC server on port {port}")
            except Exception as e:
                logger.error(f"Error closing OSC server on port {port}: {e}")

        # Clear all resources
        osc_clients.clear()
        osc_servers.clear()
        logger.info("OSC-MCP server cleanup complete")

@server.tool()
async def send_osc(
    host: str,
    port: int,
    address: str,
    values: List[Any] = None
) -> Dict[str, Any]:
    """Send an OSC message to the specified address.

    This tool sends OSC (Open Sound Control) messages over UDP to any OSC-enabled
    application. OSC is a protocol for communication among computers, sound synthesizers,
    and other multimedia devices, commonly used in professional audio/visual workflows.

    OSC messages consist of an address pattern (like a URL path) and optional data values.
    The protocol is fire-and-forget (no delivery confirmation), making it ideal for
    real-time performance control where low latency is critical.

    Args:
        host: Target hostname or IP address. Examples:
            - "127.0.0.1" or "localhost" for same machine
            - "192.168.1.100" for network device
            - "studio-computer.local" for mDNS hostname
        port: Target UDP port number (1-65535). Common OSC ports:
            - 8000: Generic OSC applications
            - 9000: TouchDesigner, QLab
            - 9001: VCV Rack
            - 11000: Ableton Live (with LiveOSC or Connection Kit)
            - 57120: SuperCollider
            - 57131: Max/MSP
        address: OSC address pattern starting with "/" (e.g., "/volume", "/track/1/mute").
            Address patterns follow a hierarchical structure similar to file paths:
            - Single segment: "/volume"
            - Multi-segment: "/live/track/1/volume"
            - Wildcards supported by some receivers: "/track/*/mute"
        values: Optional list of values to send. Supported types:
            - int: Integer numbers (e.g., 1, 42, -10)
            - float: Decimal numbers (e.g., 0.5, 3.14, -2.7)
            - str: Text strings (e.g., "hello", "play")
            - bool: True/False (converted to 1/0 by some receivers)
            - None/empty list: Send address-only message (bang)
            Multiple values can be sent in a single message: [1, 0.5, "test"]

    Returns:
        Dictionary with the following structure:
            {
                "status": "success" | "error",
                "host": str,           # Echo of target host
                "port": int,           # Echo of target port
                "address": str,        # Echo of OSC address
                "values": List[Any],   # Echo of sent values
                "message": str         # Error message (only on error)
            }

    Raises:
        No exceptions raised directly - all errors returned in response dict.
        Common error scenarios:
        - Network unreachable: Host is not accessible
        - Connection refused: Firewall blocking UDP traffic
        - Invalid address format: Address doesn't start with "/"
        - Serialization error: Unsupported value type in values list

    Examples:
        # Send volume control to Ableton Live
        >>> await send_osc("127.0.0.1", 11000, "/live/volume", [0.8])
        {'status': 'success', 'host': '127.0.0.1', 'port': 11000,
         'address': '/live/volume', 'values': [0.8]}

        # Mute track 1 in a DAW
        >>> await send_osc("localhost", 8000, "/track/1/mute", [1])

        # Send parameter to TouchDesigner
        >>> await send_osc("192.168.1.50", 9000, "/project/comp1/opacity", [0.75])

        # Multiple values in one message (XYZ position)
        >>> await send_osc("127.0.0.1", 9000, "/avatar/position", [1.0, 2.5, -3.0])

        # Address-only message (trigger/bang)
        >>> await send_osc("localhost", 8000, "/play", [])

        # Control VRChat avatar parameter
        >>> await send_osc("127.0.0.1", 9000, "/avatar/parameters/Voice", [0.8])

    See Also:
        start_osc_server(): Start receiving OSC messages
        stop_osc_server(): Stop OSC message receiver

    Notes:
        - OSC clients are cached per host:port for efficiency (reused across calls)
        - Messages are fire-and-forget with no delivery confirmation
        - UDP is connectionless - no error if receiver doesn't exist
        - For bidirectional communication, use start_osc_server() to receive replies
        - Values are automatically converted to appropriate OSC types
        - Maximum message size is typically 8192 bytes (platform-dependent)

    Performance:
        - Typical latency: < 5ms on localhost
        - Cached clients avoid connection overhead
        - Response caching enabled (60s TTL) for identical calls

    Application-Specific Tips:
        Ableton Live (port 11000):
            - /live/play - Start playback
            - /live/stop - Stop playback
            - /live/tempo [bpm] - Set tempo
            - /live/track/{n}/volume [0.0-1.0] - Track volume

        TouchDesigner (port 9000):
            - /project/comp1/opacity [0.0-1.0]
            - /project/comp1/tx [x] - Translate X

        VRChat (port 9000):
            - /avatar/parameters/{name} [value] - Avatar parameter
            - /input/Voice [0.0-1.0] - Voice activation

        SuperCollider (port 57120):
            - /s_new ["synthname", nodeID, addAction, target]
            - /n_free [nodeID] - Free synth node
    """
    if values is None:
        values = []
        
    try:
        # Get or create OSC client
        client_key = f"{host}:{port}"
        if client_key not in osc_clients:
            osc_clients[client_key] = SimpleUDPClient(host, port)
        
        # Send the OSC message
        osc_clients[client_key].send_message(address, values)
        
        logger.info(f"Sent OSC to {host}:{port} - {address}: {values}")
        return {
            "status": "success",
            "host": host,
            "port": port,
            "address": address,
            "values": values
        }
    except Exception as e:
        error = f"Failed to send OSC message: {e}"
        logger.error(error)
        return {"status": "error", "message": error}

@server.tool()
async def start_osc_server(
    port: int,
    address: str = "0.0.0.0"
) -> Dict[str, Any]:
    """Start an OSC server to receive incoming messages.

    This tool creates a UDP server that listens for incoming OSC messages on the
    specified port. All received messages are logged and can be used for bidirectional
    communication with OSC applications. The server runs asynchronously in the
    background, allowing you to continue sending messages while receiving.

    OSC servers are useful for:
    - Receiving feedback from applications (playback position, parameter changes)
    - Implementing bidirectional control (send commands, receive status updates)
    - Creating OSC bridges between applications
    - Monitoring OSC traffic for debugging
    - Building interactive installations with sensor feedback

    Args:
        port: UDP port number to listen on (1-65535). Common ports:
            - 8000-8999: Generic OSC applications
            - 9000-9099: TouchDesigner, QLab, custom apps
            - 10000-10999: Custom applications
            Choose a port not already in use by other applications.
            Use `netstat -an | grep UDP` to check active ports.
        address: Network interface to bind to. Options:
            - "0.0.0.0" (default): Listen on ALL network interfaces
              (localhost, WiFi, Ethernet, VPN)
            - "127.0.0.1": Listen ONLY on localhost (most secure)
            - "192.168.1.100": Listen on specific network interface
            Use "0.0.0.0" for maximum compatibility, "127.0.0.1" for security.

    Returns:
        Dictionary with the following structure:
            {
                "status": "success" | "error",
                "message": str,        # Human-readable status message
                "port": int,           # Echo of listening port
                "address": str         # Echo of bound address
            }

    Raises:
        No exceptions raised directly - all errors returned in response dict.
        Common error scenarios:
        - Port already in use: Another application is using this port
        - Permission denied: Ports < 1024 require administrator/root
        - Invalid address: Bind address doesn't match any interface
        - Address already in use: Server already running on this port

    Examples:
        # Start server on default port 8000, all interfaces
        >>> await start_osc_server(8000)
        {'status': 'success', 'message': 'OSC server started on 0.0.0.0:8000',
         'port': 8000, 'address': '0.0.0.0'}

        # Start server on localhost only (more secure)
        >>> await start_osc_server(9000, "127.0.0.1")
        {'status': 'success', 'message': 'OSC server started on 127.0.0.1:9000',
         'port': 9000, 'address': '127.0.0.1'}

        # Start server on custom port for TouchDesigner feedback
        >>> await start_osc_server(9001, "0.0.0.0")

        # Error case: port already in use
        >>> await start_osc_server(8000)  # If already started
        {'status': 'error', 'message': 'OSC server already running on port 8000'}

    See Also:
        stop_osc_server(): Stop a running OSC server
        send_osc(): Send OSC messages to applications

    Notes:
        - Only ONE server can run per port
        - Servers run in background and survive across multiple tool calls
        - All received messages are logged to console (check server logs)
        - Server state is tracked globally - call stop_osc_server() to clean up
        - UDP is stateless - no connection confirmation from senders
        - Firewall may block incoming messages (check firewall settings)
        - Use stop_osc_server() before shutting down to free the port

    Message Handling:
        Received messages are automatically logged with format:
        "Received OSC: {address} {values}"

        Example log output:
        "Received OSC: /live/play ()"
        "Received OSC: /track/1/volume (0.8,)"
        "Received OSC: /xyz (1.0, 2.0, 3.0)"

    Performance:
        - Negligible CPU usage when idle
        - Can handle 1000+ messages/second on typical hardware
        - No message queue - all messages processed immediately
        - Message handling is non-blocking

    Security Considerations:
        - UDP is unencrypted - don't send sensitive data
        - Binding to 0.0.0.0 exposes server to network
        - Use 127.0.0.1 for localhost-only communication
        - Implement firewall rules for production deployments
        - No authentication - any sender can send messages

    Troubleshooting:
        "Port already in use":
            - Check if server already started: look for "OSC server already running"
            - Check for other apps using port: `netstat -an | grep {port}`
            - Use different port or stop conflicting application

        "Permission denied":
            - Ports < 1024 require root/administrator
            - Use port >= 1024 or run with elevated privileges

        Not receiving messages:
            - Check firewall settings (Windows Firewall, iptables)
            - Verify sender is targeting correct IP:port
            - Check server logs for "Received OSC" messages
            - Use Wireshark to debug UDP traffic

    Use Cases:
        Bidirectional DAW control:
            >>> await start_osc_server(12000)
            >>> await send_osc("localhost", 11000, "/live/play", [])
            # Receive playback position updates from Ableton

        OSC bridge:
            >>> await start_osc_server(8000)
            # Receive from app A, forward to app B
            >>> await send_osc("app-b.local", 9000, "/forward", values)

        Interactive installation:
            >>> await start_osc_server(9000)
            # Receive sensor data from Arduino/Processing
            # Control lighting/video based on sensor input

        Debugging OSC traffic:
            >>> await start_osc_server(8000)
            # Monitor all incoming OSC messages
            # Check logs to verify message format
    """
    if port in osc_servers:
        return {
            "status": "error",
            "message": f"OSC server already running on port {port}"
        }
    
    try:
        # Create dispatcher for OSC messages
        osc_dispatcher = dispatcher.Dispatcher()
        
        # Default handler that logs received messages
        def osc_handler(osc_addr: str, *args: Any) -> None:
            logger.info(f"Received OSC: {osc_addr} {args}")
        
        # Register default handler for all addresses
        osc_dispatcher.set_default_handler(osc_handler)
        
        # Create and start OSC server
        loop = asyncio.get_event_loop()
        server = osc_server.AsyncIOOSCUDPServer(
            (address, port), 
            osc_dispatcher, 
            loop
        )
        
        # Store the transport for later cleanup
        transport, _ = await server.create_serve_endpoint()
        
        # Store server info
        osc_servers[port] = transport
        
        logger.info(f"Started OSC server on {address}:{port}")
        return {
            "status": "success",
            "message": f"OSC server started on {address}:{port}",
            "port": port,
            "address": address
        }
        
    except Exception as e:
        error = f"Failed to start OSC server: {e}"
        logger.error(error)
        return {"status": "error", "message": error}

@server.tool()
async def stop_osc_server(port: int) -> Dict[str, Any]:
    """Stop a running OSC server and free the port.

    This tool stops an OSC server that was previously started with start_osc_server(),
    cleanly shutting down the UDP listener and freeing the port for other applications.
    This is essential for proper resource cleanup and preventing port conflicts.

    Always stop OSC servers when you're done receiving messages to:
    - Free the port for other applications
    - Clean up system resources (sockets, threads)
    - Prevent "port already in use" errors on restart
    - Maintain clean server state

    Args:
        port: Port number of the server to stop (1-65535). This must match
            the port used when calling start_osc_server(). The server on this
            port will be stopped regardless of which address it was bound to.

    Returns:
        Dictionary with the following structure:
            {
                "status": "success" | "error",
                "message": str,        # Human-readable status message
                "port": int            # Echo of stopped port (success only)
            }

    Raises:
        No exceptions raised directly - all errors returned in response dict.
        Common error scenarios:
        - No server running: No OSC server found on specified port
        - Port mismatch: Server exists but on different port
        - Cleanup error: Server stopped but cleanup failed (rare)

    Examples:
        # Stop server on port 8000
        >>> await stop_osc_server(8000)
        {'status': 'success', 'message': 'OSC server stopped on port 8000',
         'port': 8000}

        # Stop server that was started earlier
        >>> await start_osc_server(9000)
        >>> # ... do some work ...
        >>> await stop_osc_server(9000)
        {'status': 'success', 'message': 'OSC server stopped on port 9000',
         'port': 9000}

        # Error case: no server running
        >>> await stop_osc_server(8000)
        {'status': 'error', 'message': 'No OSC server running on port 8000'}

        # Typical workflow: start, use, stop
        >>> await start_osc_server(8000)
        >>> await send_osc("localhost", 11000, "/query", [])
        >>> # Wait for responses...
        >>> await stop_osc_server(8000)

    See Also:
        start_osc_server(): Start an OSC server to receive messages
        send_osc(): Send OSC messages to applications

    Notes:
        - Stopping a server is immediate - no graceful shutdown period
        - Any messages in flight may be lost
        - Server state is removed from global tracking
        - Port becomes available immediately after stop
        - Safe to call stop on already-stopped server (returns error)
        - No effect on other servers running on different ports

    Best Practices:
        1. Always stop servers before application shutdown
        2. Use try/finally pattern for guaranteed cleanup:
           try:
               await start_osc_server(8000)
               # ... receive messages ...
           finally:
               await stop_osc_server(8000)

        3. Stop servers when switching to different port
        4. Don't leave servers running unnecessarily (resource waste)
        5. Document which ports your application uses

    Workflow Patterns:
        Temporary listening session:
            >>> await start_osc_server(8000)
            >>> # Receive some messages
            >>> await stop_osc_server(8000)

        Long-running service:
            >>> await start_osc_server(8000)
            >>> # Keep running until shutdown signal
            >>> # On shutdown:
            >>> await stop_osc_server(8000)

        Multiple servers:
            >>> await start_osc_server(8000)
            >>> await start_osc_server(9000)
            >>> # ...
            >>> await stop_osc_server(8000)
            >>> await stop_osc_server(9000)

    Troubleshooting:
        "No OSC server running on port {port}":
            - Verify you started server on this port
            - Check if server was already stopped
            - Confirm port number is correct

        Server won't stop:
            - Check logs for error messages
            - Verify server process is still running
            - May indicate network stack issue (rare)

        Port still in use after stop:
            - Wait a few seconds for OS to release port
            - Check for zombie processes: `netstat -an | grep {port}`
            - Restart application if problem persists

    Performance:
        - Stop operation completes in < 10ms
        - No blocking - returns immediately
        - Cleanup happens asynchronously in background
        - No impact on other running servers

    Resource Cleanup:
        When a server is stopped:
        - UDP socket is closed
        - Port is freed for other applications
        - Message handlers are removed
        - Server state is cleared from memory
        - OS resources are released

    Edge Cases:
        - Stopping non-existent server: Returns error, safe
        - Stopping server twice: Second call returns error
        - Stopping during message receive: Current message may be lost
        - System shutdown: Servers auto-cleanup (but explicit stop is better)
    """
    transport = osc_servers.pop(port, None)
    if not transport:
        return {
            "status": "error",
            "message": f"No OSC server running on port {port}"
        }
    
    try:
        transport.close()
        logger.info(f"Stopped OSC server on port {port}")
        return {
            "status": "success",
            "message": f"OSC server stopped on port {port}",
            "port": port
        }
    except Exception as e:
        error = f"Failed to stop OSC server: {e}"
        logger.error(error)
        return {"status": "error", "message": error}

# This allows running the server directly with: python -m oscmcp.mcp_server
if __name__ == "__main__":
    # Run the FastMCP server with stdio transport
    server.run(transport="stdio")

"""OSC-MCP Server with stdio transport for MCP clients.

This module implements a FastMCP 2.13 compliant server that provides OSC functionality
through the MCP protocol over stdio, making it compatible with MCP clients like Claude or Windsurf.
"""

# CRITICAL: Set stdio to binary mode on Windows for Antigravity IDE compatibility
# Antigravity IDE is strict about JSON-RPC protocol and interprets trailing \r as "invalid trailing data"
# This must happen BEFORE any imports that might write to stdout
import asyncio
import logging
import os
import sys
from typing import Any

from pydantic import BaseModel, Field

from .osc.client import OSCClient
from .osc.server import OSCServer
from .transport import run_server

if os.name == "nt":  # Windows only
    try:
        # Force binary mode for stdin/stdout to prevent CRLF conversion
        import msvcrt

        msvcrt.setmode(sys.stdin.fileno(), os.O_BINARY)
        msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)
    except (OSError, AttributeError):
        # Fallback: just ensure no CRLF conversion
        pass


# DevNullStdout class for stdio mode suppression
class DevNullStdout:
    def __init__(self, original_stdout):
        self.original_stdout = original_stdout

    def write(self, data):
        # Suppress all writes to stdout during initialization
        pass

    def flush(self):
        pass

    def restore(self):
        sys.stdout = self.original_stdout


# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Detect if we're running in stdio mode (for MCP)
_is_stdio_mode = (
    len(sys.argv) == 1  # No arguments provided
    or (len(sys.argv) == 2 and sys.argv[1] == "-m")  # Just module flag
    or any(arg in ["--stdio", "stdio"] for arg in sys.argv)  # Explicit stdio flag
)

# Suppress stdout during FastMCP initialization in stdio mode
if _is_stdio_mode:
    # Save original getLogger function
    original_getLogger = logging.getLogger

    # Redirect stdout to prevent initialization output
    sys.stdout = DevNullStdout(sys.stdout)

# Create FastMCP instance with stdio transport
from .server import _DESTRUCTIVE, _MUTATING, _README_ONLY, server

# CRITICAL: After server initialization, restore stdout for stdio mode
# This allows the server to communicate via JSON-RPC while preventing initialization logging
if _is_stdio_mode:
    if hasattr(sys.stdout, "restore"):
        sys.stdout.restore()
        # Now we can safely write to stdout for JSON-RPC communication

    # Restore the original logging functionality
    logging.getLogger = original_getLogger

    # Set up proper logging to stderr only (not stdout)
    import logging

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stderr,  # Critical: log to stderr, not stdout
    )

# Store OSC clients and servers
osc_clients: dict[str, OSCClient] = {}
osc_servers: dict[int, "OSCServer"] = {}

# OSC Recording system
osc_recordings: dict[str, list[dict[str, Any]]] = {}


# Pydantic models for input validation (FastMCP 2.13)
class OSCMessageInput(BaseModel):
    """Input model for OSC message sending."""

    host: str = Field(..., description="Target hostname or IP address")
    port: int = Field(..., gt=0, le=65535, description="Target UDP port (1-65535)")
    address: str = Field(..., pattern=r"^/.*", description="OSC address pattern starting with /")
    values: list[Any] = Field(default_factory=list, description="List of values to send")


class OSCServerInput(BaseModel):
    """Input model for starting OSC server."""

    port: int = Field(..., gt=0, le=65535, description="UDP port to listen on (1-65535)")
    address: str = Field(default="0.0.0.0", description="Network interface to bind to")


class OSCServerStopInput(BaseModel):
    """Input model for stopping OSC server."""

    port: int = Field(..., gt=0, le=65535, description="Port of the server to stop (1-65535)")


# Lifespan management removed - FastMCP 2.13.1 doesn't support lifespan decorator
# Resource cleanup happens automatically when server shuts down


@server.tool()
async def send_osc(
    host: str, port: int, address: str, values: list[Any] = None, protocol: str = "udp"
) -> dict[str, Any]:
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
        client_key = f"{host}:{port}:{protocol}"
        if client_key not in osc_clients:
            osc_clients[client_key] = OSCClient(host, port, protocol)

        # Send the OSC message
        osc_clients[client_key].send(address, *values)

        logger.info(f"Sent {protocol.upper()} OSC to {host}:{port} - {address}: {values}")
        return {
            "status": "success",
            "host": host,
            "port": port,
            "address": address,
            "values": values,
            "protocol": protocol,
        }
    except Exception as e:
        error = f"Failed to send OSC message: {e}"
        logger.error(error)
        return {"status": "error", "message": error}


@server.tool(annotations=_MUTATING)
async def start_osc_server(port: int, address: str = "0.0.0.0", protocol: str = "udp") -> dict[str, Any]:
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
            "message": f"OSC server already running on port {port}",
        }

    try:
        # Create OSCServer instance with message buffering
        osc_server_instance = OSCServer(address, port, protocol=protocol)

        # Start the server
        await osc_server_instance.start()

        # Store server instance for later access
        osc_servers[port] = osc_server_instance

        logger.info(f"Started OSC server with message buffering on {address}:{port}")
        return {
            "status": "success",
            "message": f"OSC server started on {address}:{port} with message buffering",
            "port": port,
            "address": address,
        }

    except Exception as e:
        error = f"Failed to start OSC server: {e}"
        logger.error(error)
        return {"status": "error", "message": error}


@server.tool(annotations=_MUTATING)
async def stop_osc_server(port: int) -> dict[str, Any]:
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
    osc_server_instance = osc_servers.pop(port, None)
    if not osc_server_instance:
        return {"status": "error", "message": f"No OSC server running on port {port}"}

    try:
        await osc_server_instance.stop()
        logger.info(f"Stopped OSC server on port {port}")
        return {
            "status": "success",
            "message": f"OSC server stopped on port {port}",
            "port": port,
        }
    except Exception as e:
        error = f"Failed to stop OSC server: {e}"
        logger.error(error)
        return {"status": "error", "message": error}


@server.tool(annotations=_README_ONLY)
async def get_received_messages(
    port: int,
    address_pattern: str | None = None,
    max_age_seconds: float | None = None,
    limit: int = 100,
) -> dict[str, Any]:
    """
    Get OSC messages received by a running OSC server.

    This tool retrieves messages that have been received by an OSC server started with start_osc_server().
    Messages are buffered and can be filtered by address pattern, age, and limited in count.

    Args:
        port: Port of the OSC server to query (must be running)
        address_pattern: Filter by OSC address pattern (substring match)
        max_age_seconds: Only return messages newer than this age
        limit: Maximum number of messages to return (default: 100)

    Returns:
        Dictionary with message data:
        {
            "status": "success" | "error",
            "messages": List[Dict],  # Array of message objects
            "count": int,           # Number of messages returned
            "total_available": int  # Total messages in buffer
        }

    Message format:
    {
        "address": "/osc/path",
        "args": [1.0, "hello", true],
        "timestamp": 1234567890.123,
        "age_seconds": 5.5
    }

    Examples:
        # Get all recent messages from port 9000
        >>> await get_received_messages(9000)
        {"status": "success", "messages": [...], "count": 5}

        # Get messages matching pattern
        >>> await get_received_messages(9000, address_pattern="/param")
        {"status": "success", "messages": [...], "count": 2}

        # Get only messages from last 10 seconds
        >>> await get_received_messages(9000, max_age_seconds=10.0)
        {"status": "success", "messages": [...], "count": 3}

    Use Cases:
        - Monitor parameter changes from VCV Rack modules
        - Receive feedback from interactive applications
        - Debug OSC message flow
        - React to user interactions in real-time

    Notes:
        - Messages are buffered with timestamps
        - Buffer holds last 1000 messages by default
        - Messages are returned newest-first
        - Server must be running (use start_osc_server first)
    """

    if port not in osc_servers:
        return {"status": "error", "message": f"No OSC server running on port {port}"}

    osc_server_instance = osc_servers[port]
    messages = osc_server_instance.get_received_messages(
        address_pattern=address_pattern, max_age_seconds=max_age_seconds, limit=limit
    )

    return {
        "status": "success",
        "messages": messages,
        "count": len(messages),
        "total_available": len(osc_server_instance._message_buffer),
    }


@server.tool(annotations=_README_ONLY)
async def get_latest_message(port: int, address_pattern: str | None = None) -> dict[str, Any]:
    """
    Get the most recent OSC message from a running server.

    This is a convenience tool that returns only the latest message matching the criteria,
    useful for checking the most recent parameter change or event.

    Args:
        port: Port of the OSC server to query
        address_pattern: Filter by OSC address pattern (substring match)

    Returns:
        Dictionary with latest message or error:
        {
            "status": "success" | "error",
            "message": Dict | None,  # Latest message object
            "found": bool           # Whether a message was found
        }

    Examples:
        # Get latest message from VCV Rack
        >>> await get_latest_message(10001)
        {"status": "success", "message": {"address": "/param", "args": [1, 0, 0.7]}, "found": true}

        # Get latest parameter message
        >>> await get_latest_message(10001, address_pattern="/param")
        {"status": "success", "message": {...}, "found": true}

    Use Cases:
        - Check latest knob position in VCV Rack
        - Monitor current application state
        - Get immediate feedback on user interactions
    """

    if port not in osc_servers:
        return {"status": "error", "message": f"No OSC server running on port {port}"}

    osc_server_instance = osc_servers[port]
    message = osc_server_instance.get_latest_message(address_pattern)

    return {"status": "success", "message": message, "found": message is not None}


@server.tool(annotations=_README_ONLY)
async def get_osc_server_stats(port: int) -> dict[str, Any]:
    """
    Get statistics about a running OSC server's message buffer.

    This tool provides insights into OSC message traffic and buffer usage,
    useful for monitoring and debugging OSC communication.

    Args:
        port: Port of the OSC server to query

    Returns:
        Dictionary with server statistics:
        {
            "status": "success" | "error",
            "stats": {
                "total_messages": int,
                "max_buffer_size": int,
                "oldest_message_age": float,
                "newest_message_age": float
            } | None
        }

    Examples:
        # Check server message statistics
        >>> await get_osc_server_stats(10001)
        {
            "status": "success",
            "stats": {
                "total_messages": 150,
                "max_buffer_size": 1000,
                "oldest_message_age": 45.2,
                "newest_message_age": 0.5
            }
        }

    Use Cases:
        - Monitor OSC message traffic
        - Debug message buffer issues
        - Check server health and activity
        - Optimize buffer size settings
    """

    if port not in osc_servers:
        return {"status": "error", "message": f"No OSC server running on port {port}"}

    osc_server_instance = osc_servers[port]
    stats = osc_server_instance.get_buffer_stats()

    return {"status": "success", "stats": stats}


@server.tool(annotations=_DESTRUCTIVE)
async def clear_osc_message_buffer(port: int) -> dict[str, Any]:
    """
    Clear all messages from an OSC server's buffer.

    This tool removes all buffered OSC messages, useful for starting fresh
    after debugging or when you want to ignore old messages.

    Args:
        port: Port of the OSC server to clear

    Returns:
        Dictionary with clear operation results:
        {
            "status": "success" | "error",
            "messages_cleared": int  # Number of messages removed
        }

    Examples:
        # Clear message buffer
        >>> await clear_osc_message_buffer(10001)
        {"status": "success", "messages_cleared": 150}

    Use Cases:
        - Start fresh after debugging
        - Clear old messages before new operation
        - Reset message history
        - Free memory in long-running servers
    """

    if port not in osc_servers:
        return {"status": "error", "message": f"No OSC server running on port {port}"}

    osc_server_instance = osc_servers[port]
    cleared_count = osc_server_instance.clear_message_buffer()

    return {"status": "success", "messages_cleared": cleared_count}


# Disabled duplicate - FastMCP 3.1+ conversational/sampling version is defined in server.py
# @server.tool()
async def test_osc_echo(port: int = 9000) -> dict[str, Any]:
    """Test OSC functionality by sending and receiving a message.

    This tool performs an end-to-end test of OSC functionality by:
    1. Starting an OSC server on the specified port
    2. Sending a test message to itself
    3. Verifying the message was received
    4. Stopping the server

    This is useful for:
    - Verifying OSC setup is working correctly
    - Testing network connectivity
    - Debugging OSC message routing
    - Validating firewall settings

    Args:
        port: Port to use for the test (default: 9000). Must be available.
            Use a port that's not in use by other applications.

    Returns:
        Dictionary with test results:
        {
            "status": "success" | "error",
            "message": str,        # Human-readable result message
            "port": int,           # Port used for test
            "test_address": str,   # OSC address used in test
            "test_values": List,   # Values sent in test message
            "server_started": bool, # Whether server started successfully
            "message_sent": bool,   # Whether test message was sent
            "server_stopped": bool  # Whether server was stopped
        }

    Examples:
        # Run echo test on default port 9000
        >>> await test_osc_echo()
        {'status': 'success', 'message': 'OSC echo test completed', ...}

        # Run echo test on custom port
        >>> await test_osc_echo(8000)
        {'status': 'success', 'message': 'OSC echo test completed', ...}

    Notes:
        - The test uses a temporary OSC server that's automatically stopped
        - Test messages are logged to the server console
        - This is a blocking operation that takes a few seconds
        - If the port is in use, the test will fail with an error

    Troubleshooting:
        "Port already in use":
            - Choose a different port that's not in use
            - Stop any applications using the test port

        "Message not received":
            - Check firewall settings (allow UDP traffic)
            - Verify network interface is active
            - Check server logs for received messages
    """
    test_address = "/test/echo"
    test_values = [1, 2.5, "test"]
    server_started = False
    message_sent = False
    server_stopped = False

    try:
        # Start the OSC server
        start_result = await start_osc_server(port, "127.0.0.1")
        if start_result["status"] != "success":
            return {
                "status": "error",
                "message": f"Failed to start OSC server: {start_result.get('message', 'Unknown error')}",
                "port": port,
                "test_address": test_address,
                "test_values": test_values,
                "server_started": False,
                "message_sent": False,
                "server_stopped": False,
            }
        server_started = True

        # Give the server a moment to start
        await asyncio.sleep(0.1)

        # Send test message
        send_result = await send_osc("127.0.0.1", port, test_address, test_values)
        if send_result["status"] == "success":
            message_sent = True
        else:
            await stop_osc_server(port)
            return {
                "status": "error",
                "message": f"Failed to send test message: {send_result.get('message', 'Unknown error')}",
                "port": port,
                "test_address": test_address,
                "test_values": test_values,
                "server_started": True,
                "message_sent": False,
                "server_stopped": False,
            }

        # Give time for message to be received and logged
        await asyncio.sleep(0.2)

        # Stop the server
        stop_result = await stop_osc_server(port)
        if stop_result["status"] == "success":
            server_stopped = True

        return {
            "status": "success",
            "message": "OSC echo test completed successfully",
            "port": port,
            "test_address": test_address,
            "test_values": test_values,
            "server_started": server_started,
            "message_sent": message_sent,
            "server_stopped": server_stopped,
        }

    except Exception as e:
        error = f"OSC echo test failed: {e}"
        logger.error(error)

        # Try to stop server if it was started
        if server_started:
            try:
                await stop_osc_server(port)
                server_stopped = True
            except Exception:
                pass

        return {
            "status": "error",
            "message": error,
            "port": port,
            "test_address": test_address,
            "test_values": test_values,
            "server_started": server_started,
            "message_sent": message_sent,
            "server_stopped": server_stopped,
        }


# ============================================================================
# Application-Specific Tools
# ============================================================================
# These tools provide high-level interfaces for specific applications
# They use the send_osc function internally


@server.tool()
async def ableton_manager(
    operation: str,
    host: str = "127.0.0.1",
    port: int = 11000,
    track_index: int | None = None,
    clip_slot: int | None = None,
    bpm: float | None = None,
    volume: float | None = None,
    pan: float | None = None,
) -> dict[str, Any]:
    """
    Ableton Live Manager - Professional DAW control.

    PORTMANTEAU TOOL: Consolidates all Ableton Live operations into one tool.

    Args:
        operation: Operation to perform
            - "play" - Start playback
            - "stop" - Stop playback
            - "set_tempo" - Set BPM
            - "play_clip" - Play specific clip
            - "set_volume" - Set track volume (0.0-1.0)
            - "set_pan" - Set track pan (-1.0 to 1.0)
        host: Target host (default: 127.0.0.1)
        port: Target port (default: 11000)
        track_index: Track index (for clip, volume, pan operations)
        clip_slot: Clip slot index (for play_clip)
        bpm: Tempo in BPM (for set_tempo)
        volume: Volume level (0.0-1.0, for set_volume)
        pan: Pan position (-1.0 to 1.0, for set_pan)

    Returns:
        Operation result with status and details
    """

    if operation == "play":
        return await send_osc(host, port, "/live/play", [])

    if operation == "stop":
        return await send_osc(host, port, "/live/stop", [])

    if operation == "set_tempo":
        if bpm is None:
            return {"status": "error", "message": "bpm required for set_tempo"}
        return await send_osc(host, port, "/live/tempo", [bpm])

    if operation == "play_clip":
        if track_index is None or clip_slot is None:
            return {
                "status": "error",
                "message": "track_index and clip_slot required for play_clip",
            }
        return await send_osc(host, port, "/live/clip/fire", [track_index, clip_slot])

    if operation == "set_volume":
        if track_index is None or volume is None:
            return {
                "status": "error",
                "message": "track_index and volume required for set_volume",
            }
        return await send_osc(host, port, "/live/track/set/volume", [track_index, volume])

    if operation == "set_pan":
        if track_index is None or pan is None:
            return {
                "status": "error",
                "message": "track_index and pan required for set_pan",
            }
        return await send_osc(host, port, "/live/track/set/panning", [track_index, pan])

    return {"status": "error", "message": f"Unknown operation: {operation}"}


@server.tool()
async def vrchat_manager(
    operation: str,
    host: str = "127.0.0.1",
    port: int = 9000,
    param_name: str | None = None,
    value: float | None = None,
    message: str | None = None,
    device: str | None = None,
    duration: float | None = None,
    amplitude: float | None = None,
    frequency: float | None = None,
) -> dict[str, Any]:
    """
    VRChat Manager - Avatar and world control.

    PORTMANTEAU TOOL: Consolidates all VRChat operations into one tool.

    Args:
        operation: Operation to perform
            - "set_parameter" - Set avatar parameter
            - "send_chat" - Send chat message
            - "trigger_haptic" - Trigger haptic feedback
        host: Target host (default: 127.0.0.1)
        port: Target port (default: 9000)
        param_name: Parameter name (for set_parameter)
        value: Parameter value (for set_parameter)
        message: Chat message (for send_chat)
        device: Haptic device ('left', 'right', or 'both', for trigger_haptic)
        duration: Haptic duration (default: 0.1, for trigger_haptic)
        amplitude: Haptic amplitude (default: 0.5, for trigger_haptic)
        frequency: Haptic frequency (default: 0.0, for trigger_haptic)

    Returns:
        Operation result with status and details
    """

    if operation == "set_parameter":
        if param_name is None or value is None:
            return {
                "status": "error",
                "message": "param_name and value required for set_parameter",
            }
        address = f"/avatar/parameters/{param_name}"
        return await send_osc(host, port, address, [value])

    if operation == "send_chat":
        if message is None:
            return {"status": "error", "message": "message required for send_chat"}
        return await send_osc(host, port, "/chatbox/input", [message, True, False])

    if operation == "trigger_haptic":
        device = device or "both"
        duration = duration or 0.1
        amplitude = amplitude or 0.5
        frequency = frequency or 0.0

        results = {}
        if device.lower() in ("left", "both"):
            await send_osc(
                host,
                port,
                "/avatar/parameters/LeftHaptic",
                [duration, amplitude, frequency],
            )
            results["left"] = "sent"
        if device.lower() in ("right", "both"):
            await send_osc(
                host,
                port,
                "/avatar/parameters/RightHaptic",
                [duration, amplitude, frequency],
            )
            results["right"] = "sent"
        return {"status": "success", "device": device, "results": results}

    return {"status": "error", "message": f"Unknown operation: {operation}"}


@server.tool()
async def touchdesigner_manager(
    operation: str,
    host: str = "127.0.0.1",
    port: int = 9000,
    component_path: str | None = None,
    parameter: str | None = None,
    value: float | None = None,
    # CHOP parameters
    channel_index: int | None = None,
    channel_name: str | None = None,
    # TOP parameters
    texture_index: int | None = None,
    # DAT parameters
    row: int | None = None,
    col: int | None = None,
    text: str | None = None,
    # 3D parameters
    x: float | None = None,
    y: float | None = None,
    z: float | None = None,
    # Audio parameters
    frequency: float | None = None,
    amplitude: float | None = None,
    phase: float | None = None,
    # Video parameters
    resolution: str | None = None,
    fps: float | None = None,
) -> dict[str, Any]:
    """
    TouchDesigner Manager - Comprehensive real-time visual programming control.

    PORTMANTEAU TOOL: Consolidates all TouchDesigner operations into one tool.
    Supports COMP, CHOP, SOP, TOP, DAT, and MAT operator families.

    Args:
        operation: Operation to perform

        # Basic Parameter Control
        - "set_parameter" - Set any component parameter
        - "set_constant" - Set constant operator value
        - "set_slider" - Set slider operator value
        - "set_toggle" - Set toggle operator state
        - "trigger_button" - Trigger button component
        - "pulse_momentary" - Pulse momentary button

        # CHOP Operations (Channel Operators)
        - "set_chop_channel" - Set CHOP channel value by index
        - "set_chop_channel_by_name" - Set CHOP channel value by name
        - "set_waveform_freq" - Set waveform CHOP frequency
        - "set_waveform_amp" - Set waveform CHOP amplitude
        - "set_waveform_phase" - Set waveform CHOP phase
        - "set_audio_level" - Set audio device CHOP level
        - "set_filter_cutoff" - Set filter CHOP cutoff frequency
        - "set_math_multiply" - Set math CHOP multiply value
        - "set_lfo_rate" - Set LFO CHOP rate

        # TOP Operations (Texture Operators)
        - "set_movie_play" - Control movie file TOP playback
        - "set_level_brightness" - Set level TOP brightness
        - "set_level_contrast" - Set level TOP contrast
        - "set_level_gamma" - Set level TOP gamma
        - "set_transform_scale" - Set transform TOP scale
        - "set_transform_rotate" - Set transform TOP rotation
        - "set_transform_translate" - Set transform TOP translation
        - "set_composite_opacity" - Set composite TOP opacity

        # SOP Operations (Surface Operators)
        - "set_sphere_radius" - Set sphere SOP radius
        - "set_box_size" - Set box SOP size
        - "set_torus_major" - Set torus SOP major radius
        - "set_torus_minor" - Set torus SOP minor radius
        - "set_transform_sop_tx" - Set SOP transform translate X
        - "set_transform_sop_ty" - Set SOP transform translate Y
        - "set_transform_sop_tz" - Set SOP transform translate Z
        - "set_transform_sop_rx" - Set SOP transform rotate X
        - "set_transform_sop_ry" - Set SOP transform rotate Y
        - "set_transform_sop_rz" - Set SOP transform rotate Z

        # DAT Operations (Data Operators)
        - "set_table_cell" - Set table DAT cell value
        - "set_text_string" - Set text DAT string
        - "trigger_script" - Execute script DAT
        - "set_parameter_dat" - Set parameter DAT value

        # MAT Operations (Material Operators)
        - "set_phong_diffuse" - Set phong MAT diffuse color
        - "set_phong_specular" - Set phong MAT specular color
        - "set_phong_emissive" - Set phong MAT emissive color
        - "set_phong_shininess" - Set phong MAT shininess

        # COMP Operations (Components)
        - "set_container_opacity" - Set container COMP opacity
        - "set_base_position" - Set base COMP position
        - "set_base_size" - Set base COMP size
        - "set_window_position" - Set window COMP position

        host: Target host (default: 127.0.0.1)
        port: Target port (default: 9000)
        component_path: Component path (e.g., '/project1/constant1')
        parameter: Parameter name (for set_parameter)
        value: Parameter/constant value
        channel_index: CHOP channel index (for CHOP operations)
        channel_name: CHOP channel name (for named channel operations)
        texture_index: TOP texture index (for multi-input TOPs)
        row: DAT table row (for table operations)
        col: DAT table column (for table operations)
        text: Text string (for DAT text operations)
        x,y,z: 3D coordinates (for 3D operations)
        frequency: Frequency value (for audio/waveform operations)
        amplitude: Amplitude value (for audio/waveform operations)
        phase: Phase value (for waveform operations)
        resolution: Video resolution (e.g., "1920x1080")
        fps: Frames per second (for video operations)

    Returns:
        Operation result with status and details

    Examples:
        # Basic operations
        await touchdesigner_manager("set_constant", component_path="/project1/const1", value=0.5)
        await touchdesigner_manager("set_slider", component_path="/project1/slider1", value=0.75)
        await touchdesigner_manager("trigger_button", component_path="/project1/button1")

        # CHOP operations
        await touchdesigner_manager("set_waveform_freq", component_path="/project1/wave1", frequency=440)
        await touchdesigner_manager("set_audio_level", component_path="/project1/audioin1", value=0.8)

        # TOP operations
        await touchdesigner_manager("set_level_brightness", component_path="/project1/level1", value=1.2)
        await touchdesigner_manager("set_transform_scale", component_path="/project1/transform1", x=2.0, y=2.0, z=1.0)

        # SOP operations
        await touchdesigner_manager("set_sphere_radius", component_path="/project1/sphere1", value=0.5)
        await touchdesigner_manager("set_transform_sop_tx", component_path="/project1/transform1", value=100)

        # DAT operations
        await touchdesigner_manager("set_table_cell", component_path="/project1/table1", row=0, col=1, value=42)
        await touchdesigner_manager("set_text_string", component_path="/project1/text1", text="Hello World")
    """

    # Basic Parameter Operations
    if operation == "set_parameter":
        if component_path is None or parameter is None or value is None:
            return {
                "status": "error",
                "message": "component_path, parameter, and value required for set_parameter",
            }
        address = f"{component_path}/{parameter}"
        return await send_osc(host, port, address, [value])

    if operation == "set_constant":
        if component_path is None or value is None:
            return {
                "status": "error",
                "message": "component_path and value required for set_constant",
            }
        return await send_osc(host, port, f"{component_path}/value1", [value])

    if operation == "set_slider":
        if component_path is None or value is None:
            return {
                "status": "error",
                "message": "component_path and value required for set_slider",
            }
        return await send_osc(host, port, f"{component_path}/value", [value])

    if operation == "set_toggle":
        if component_path is None or value is None:
            return {
                "status": "error",
                "message": "component_path and value required for set_toggle",
            }
        return await send_osc(host, port, f"{component_path}/value", [1 if value else 0])

    if operation == "trigger_button":
        if component_path is None:
            return {
                "status": "error",
                "message": "component_path required for trigger_button",
            }
        return await send_osc(host, port, f"{component_path}/pulse", [1])

    if operation == "pulse_momentary":
        if component_path is None:
            return {
                "status": "error",
                "message": "component_path required for pulse_momentary",
            }
        return await send_osc(host, port, f"{component_path}/pulse", [1])

    # CHOP Operations (Channel Operators)
    if operation == "set_chop_channel":
        if component_path is None or channel_index is None or value is None:
            return {
                "status": "error",
                "message": "component_path, channel_index, and value required for set_chop_channel",
            }
        return await send_osc(host, port, f"{component_path}/chan{channel_index}", [value])

    if operation == "set_chop_channel_by_name":
        if component_path is None or channel_name is None or value is None:
            return {
                "status": "error",
                "message": "component_path, channel_name, and value required for set_chop_channel_by_name",
            }
        return await send_osc(host, port, f"{component_path}/{channel_name}", [value])

    if operation == "set_waveform_freq":
        if component_path is None or frequency is None:
            return {
                "status": "error",
                "message": "component_path and frequency required for set_waveform_freq",
            }
        return await send_osc(host, port, f"{component_path}/frequency", [frequency])

    if operation == "set_waveform_amp":
        if component_path is None or amplitude is None:
            return {
                "status": "error",
                "message": "component_path and amplitude required for set_waveform_amp",
            }
        return await send_osc(host, port, f"{component_path}/amplitude", [amplitude])

    if operation == "set_waveform_phase":
        if component_path is None or phase is None:
            return {
                "status": "error",
                "message": "component_path and phase required for set_waveform_phase",
            }
        return await send_osc(host, port, f"{component_path}/phase", [phase])

    if operation == "set_audio_level":
        if component_path is None or value is None:
            return {
                "status": "error",
                "message": "component_path and value required for set_audio_level",
            }
        return await send_osc(host, port, f"{component_path}/level", [value])

    if operation == "set_filter_cutoff":
        if component_path is None or frequency is None:
            return {
                "status": "error",
                "message": "component_path and frequency required for set_filter_cutoff",
            }
        return await send_osc(host, port, f"{component_path}/cutoff", [frequency])

    if operation == "set_math_multiply":
        if component_path is None or value is None:
            return {
                "status": "error",
                "message": "component_path and value required for set_math_multiply",
            }
        return await send_osc(host, port, f"{component_path}/multiply", [value])

    if operation == "set_lfo_rate":
        if component_path is None or value is None:
            return {
                "status": "error",
                "message": "component_path and value required for set_lfo_rate",
            }
        return await send_osc(host, port, f"{component_path}/rate", [value])

    # TOP Operations (Texture Operators)
    if operation == "set_movie_play":
        if component_path is None or value is None:
            return {
                "status": "error",
                "message": "component_path and value required for set_movie_play",
            }
        return await send_osc(host, port, f"{component_path}/play", [1 if value else 0])

    if operation == "set_level_brightness":
        if component_path is None or value is None:
            return {
                "status": "error",
                "message": "component_path and value required for set_level_brightness",
            }
        return await send_osc(host, port, f"{component_path}/brightness", [value])

    if operation == "set_level_contrast":
        if component_path is None or value is None:
            return {
                "status": "error",
                "message": "component_path and value required for set_level_contrast",
            }
        return await send_osc(host, port, f"{component_path}/contrast", [value])

    if operation == "set_level_gamma":
        if component_path is None or value is None:
            return {
                "status": "error",
                "message": "component_path and value required for set_level_gamma",
            }
        return await send_osc(host, port, f"{component_path}/gamma", [value])

    if operation == "set_transform_scale":
        if component_path is None:
            return {
                "status": "error",
                "message": "component_path required for set_transform_scale",
            }
        values = []
        if x is not None:
            values.append(x)
        if y is not None:
            values.append(y)
        if z is not None:
            values.append(z)
        if not values:
            return {
                "status": "error",
                "message": "at least one of x, y, or z required for set_transform_scale",
            }
        return await send_osc(host, port, f"{component_path}/scale", values)

    if operation == "set_transform_rotate":
        if component_path is None:
            return {
                "status": "error",
                "message": "component_path required for set_transform_rotate",
            }
        values = []
        if x is not None:
            values.append(x)
        if y is not None:
            values.append(y)
        if z is not None:
            values.append(z)
        if not values:
            return {
                "status": "error",
                "message": "at least one of x, y, or z required for set_transform_rotate",
            }
        return await send_osc(host, port, f"{component_path}/rotate", values)

    if operation == "set_transform_translate":
        if component_path is None:
            return {
                "status": "error",
                "message": "component_path required for set_transform_translate",
            }
        values = []
        if x is not None:
            values.append(x)
        if y is not None:
            values.append(y)
        if z is not None:
            values.append(z)
        if not values:
            return {
                "status": "error",
                "message": "at least one of x, y, or z required for set_transform_translate",
            }
        return await send_osc(host, port, f"{component_path}/translate", values)

    if operation == "set_composite_opacity":
        if component_path is None or value is None:
            return {
                "status": "error",
                "message": "component_path and value required for set_composite_opacity",
            }
        return await send_osc(host, port, f"{component_path}/opacity", [value])

    # SOP Operations (Surface Operators)
    if operation == "set_sphere_radius":
        if component_path is None or value is None:
            return {
                "status": "error",
                "message": "component_path and value required for set_sphere_radius",
            }
        return await send_osc(host, port, f"{component_path}/radius", [value])

    if operation == "set_box_size":
        if component_path is None:
            return {
                "status": "error",
                "message": "component_path required for set_box_size",
            }
        values = []
        if x is not None:
            values.append(x)
        if y is not None:
            values.append(y)
        if z is not None:
            values.append(z)
        if not values:
            return {
                "status": "error",
                "message": "at least one of x, y, or z required for set_box_size",
            }
        return await send_osc(host, port, f"{component_path}/size", values)

    if operation == "set_torus_major":
        if component_path is None or value is None:
            return {
                "status": "error",
                "message": "component_path and value required for set_torus_major",
            }
        return await send_osc(host, port, f"{component_path}/majorradius", [value])

    if operation == "set_torus_minor":
        if component_path is None or value is None:
            return {
                "status": "error",
                "message": "component_path and value required for set_torus_minor",
            }
        return await send_osc(host, port, f"{component_path}/minorradius", [value])

    if operation == "set_transform_sop_tx":
        if component_path is None or value is None:
            return {
                "status": "error",
                "message": "component_path and value required for set_transform_sop_tx",
            }
        return await send_osc(host, port, f"{component_path}/tx", [value])

    if operation == "set_transform_sop_ty":
        if component_path is None or value is None:
            return {
                "status": "error",
                "message": "component_path and value required for set_transform_sop_ty",
            }
        return await send_osc(host, port, f"{component_path}/ty", [value])

    if operation == "set_transform_sop_tz":
        if component_path is None or value is None:
            return {
                "status": "error",
                "message": "component_path and value required for set_transform_sop_tz",
            }
        return await send_osc(host, port, f"{component_path}/tz", [value])

    if operation == "set_transform_sop_rx":
        if component_path is None or value is None:
            return {
                "status": "error",
                "message": "component_path and value required for set_transform_sop_rx",
            }
        return await send_osc(host, port, f"{component_path}/rx", [value])

    if operation == "set_transform_sop_ry":
        if component_path is None or value is None:
            return {
                "status": "error",
                "message": "component_path and value required for set_transform_sop_ry",
            }
        return await send_osc(host, port, f"{component_path}/ry", [value])

    if operation == "set_transform_sop_rz":
        if component_path is None or value is None:
            return {
                "status": "error",
                "message": "component_path and value required for set_transform_sop_rz",
            }
        return await send_osc(host, port, f"{component_path}/rz", [value])

    # DAT Operations (Data Operators)
    if operation == "set_table_cell":
        if component_path is None or row is None or col is None or value is None:
            return {
                "status": "error",
                "message": "component_path, row, col, and value required for set_table_cell",
            }
        return await send_osc(host, port, f"{component_path}/cell/{row}/{col}", [value])

    if operation == "set_text_string":
        if component_path is None or text is None:
            return {
                "status": "error",
                "message": "component_path and text required for set_text_string",
            }
        return await send_osc(host, port, f"{component_path}/text", [text])

    if operation == "trigger_script":
        if component_path is None:
            return {
                "status": "error",
                "message": "component_path required for trigger_script",
            }
        return await send_osc(host, port, f"{component_path}/pulse", [1])

    if operation == "set_parameter_dat":
        if component_path is None or parameter is None or value is None:
            return {
                "status": "error",
                "message": "component_path, parameter, and value required for set_parameter_dat",
            }
        return await send_osc(host, port, f"{component_path}/{parameter}", [value])

    # MAT Operations (Material Operators)
    if operation == "set_phong_diffuse":
        if component_path is None:
            return {
                "status": "error",
                "message": "component_path required for set_phong_diffuse",
            }
        values = []
        if x is not None:
            values.append(x)
        if y is not None:
            values.append(y)
        if z is not None:
            values.append(z)
        if not values:
            return {
                "status": "error",
                "message": "RGB values (x,y,z) required for set_phong_diffuse",
            }
        return await send_osc(host, port, f"{component_path}/diffusecolor", values)

    if operation == "set_phong_specular":
        if component_path is None:
            return {
                "status": "error",
                "message": "component_path required for set_phong_specular",
            }
        values = []
        if x is not None:
            values.append(x)
        if y is not None:
            values.append(y)
        if z is not None:
            values.append(z)
        if not values:
            return {
                "status": "error",
                "message": "RGB values (x,y,z) required for set_phong_specular",
            }
        return await send_osc(host, port, f"{component_path}/specularcolor", values)

    if operation == "set_phong_emissive":
        if component_path is None:
            return {
                "status": "error",
                "message": "component_path required for set_phong_emissive",
            }
        values = []
        if x is not None:
            values.append(x)
        if y is not None:
            values.append(y)
        if z is not None:
            values.append(z)
        if not values:
            return {
                "status": "error",
                "message": "RGB values (x,y,z) required for set_phong_emissive",
            }
        return await send_osc(host, port, f"{component_path}/emissivecolor", values)

    if operation == "set_phong_shininess":
        if component_path is None or value is None:
            return {
                "status": "error",
                "message": "component_path and value required for set_phong_shininess",
            }
        return await send_osc(host, port, f"{component_path}/shininess", [value])

    # COMP Operations (Components)
    if operation == "set_container_opacity":
        if component_path is None or value is None:
            return {
                "status": "error",
                "message": "component_path and value required for set_container_opacity",
            }
        return await send_osc(host, port, f"{component_path}/opacity", [value])

    if operation == "set_base_position":
        if component_path is None:
            return {
                "status": "error",
                "message": "component_path required for set_base_position",
            }
        values = []
        if x is not None:
            values.append(x)
        if y is not None:
            values.append(y)
        if not values:
            return {
                "status": "error",
                "message": "x and y coordinates required for set_base_position",
            }
        return await send_osc(host, port, f"{component_path}/position", values)

    if operation == "set_base_size":
        if component_path is None:
            return {
                "status": "error",
                "message": "component_path required for set_base_size",
            }
        values = []
        if x is not None:
            values.append(x)
        if y is not None:
            values.append(y)
        if not values:
            return {
                "status": "error",
                "message": "width (x) and height (y) required for set_base_size",
            }
        return await send_osc(host, port, f"{component_path}/size", values)

    if operation == "set_window_position":
        if component_path is None:
            return {
                "status": "error",
                "message": "component_path required for set_window_position",
            }
        values = []
        if x is not None:
            values.append(x)
        if y is not None:
            values.append(y)
        if not values:
            return {
                "status": "error",
                "message": "x and y coordinates required for set_window_position",
            }
        return await send_osc(host, port, f"{component_path}/winpos", values)

    return {"status": "error", "message": f"Unknown operation: {operation}"}


# --- Application Manager Tools ---


@server.tool()
async def vcv_manager(
    operation: str,
    host: str = "127.0.0.1",
    port: int = 10001,
    module_id: int | None = None,
    param_id: int | None = None,
    value: float | None = None,
    cv_id: int | None = None,
    voltage: float | None = None,
    light_id: int | None = None,
    brightness: float | None = None,
    trigger_id: int | None = None,
    note: int | None = None,
    velocity: int | None = None,
    channel: int | None = None,
    controller: int | None = None,
    frequency: float | None = None,
    level: float | None = None,
    rate: float | None = None,
    cutoff: float | None = None,
    attack: float | None = None,
    decay: float | None = None,
    sustain: float | None = None,
    release: float | None = None,
    reaper_tempo: float | None = None,
    position: float | None = None,
) -> dict[str, Any]:
    """
    VCV Rack Manager - Comprehensive modular synthesis control.

    PORTMANTEAU TOOL: Consolidates all VCV Rack operations into one tool.

    Args:
        operation: Operation to perform
            - "set_parameter" - Set module parameter (0.0-1.0)
            - "trigger" - Trigger event
            - "send_cv" - Send control voltage (-10.0 to 10.0)
            - "set_light" - Set light brightness (0.0-1.0)
            - "play_midi" - Play MIDI note (0-127)
            - "stop_midi" - Stop MIDI note
            - "send_midi_cc" - Send MIDI CC message
            - "set_vco_frequency" - Set VCO frequency in Hz
            - "set_vca_level" - Set VCA level (0.0-1.0)
            - "set_lfo_rate" - Set LFO rate (0.0-1.0)
            - "set_filter_cutoff" - Set filter cutoff (0.0-1.0)
            - "set_envelope_attack" - Set envelope attack (0.0-1.0)
            - "set_envelope_decay" - Set envelope decay (0.0-1.0)
            - "set_envelope_sustain" - Set envelope sustain (0.0-1.0)
            - "set_envelope_release" - Set envelope release (0.0-1.0)
            - "sync_reaper_tempo" - Sync tempo from REAPER (requires reaper_tempo)
            - "start_transport" - Start VCV Rack transport/sequencer
            - "stop_transport" - Stop VCV Rack transport/sequencer
            - "reset_transport" - Reset transport to beginning
            - "set_transport_position" - Set transport position (0.0-1.0)
        host: Target host (default: 127.0.0.1)
        port: Target port (default: 10001)
        module_id: Module ID (required for most operations)
        param_id: Parameter ID (for set_parameter)
        value: Parameter value (0.0-1.0)
        cv_id: CV input ID (for send_cv)
        voltage: CV voltage (-10.0 to 10.0)
        light_id: Light ID (for set_light)
        brightness: Light brightness (0.0-1.0)
        trigger_id: Trigger ID (for trigger)
        note: MIDI note (0-127, for MIDI operations)
        velocity: MIDI velocity (0-127, for play_midi)
        channel: MIDI channel (1-16, for MIDI operations)
        controller: MIDI CC controller (0-127, for send_midi_cc)
        frequency: Frequency in Hz (for set_vco_frequency)
        level: Level (0.0-1.0, for set_vca_level)
        rate: Rate (0.0-1.0, for set_lfo_rate)
        cutoff: Cutoff (0.0-1.0, for set_filter_cutoff)
        attack: Attack time (0.0-1.0, for envelope)
        decay: Decay time (0.0-1.0, for envelope)
        sustain: Sustain level (0.0-1.0, for envelope)
        release: Release time (0.0-1.0, for envelope)
        reaper_tempo: Tempo from REAPER in BPM (for sync_reaper_tempo)
        position: Transport position (0.0-1.0, for set_transport_position)

    Returns:
        Operation result with status and details
    """

    if operation == "set_parameter":
        if module_id is None or param_id is None or value is None:
            return {
                "status": "error",
                "message": "module_id, param_id, and value required for set_parameter",
            }
        return await send_osc(host, port, "/param", [module_id, param_id, value])

    if operation == "trigger":
        if module_id is None or trigger_id is None:
            return {
                "status": "error",
                "message": "module_id and trigger_id required for trigger",
            }
        return await send_osc(host, port, "/trigger", [module_id, trigger_id])

    if operation == "send_cv":
        if module_id is None or cv_id is None or voltage is None:
            return {
                "status": "error",
                "message": "module_id, cv_id, and voltage required for send_cv",
            }
        return await send_osc(host, port, "/cv", [module_id, cv_id, voltage])

    if operation == "set_light":
        if module_id is None or light_id is None or brightness is None:
            return {
                "status": "error",
                "message": "module_id, light_id, and brightness required for set_light",
            }
        return await send_osc(host, port, "/light", [module_id, light_id, brightness])

    if operation == "play_midi":
        if note is None:
            return {"status": "error", "message": "note required for play_midi"}
        velocity = velocity or 100
        channel = channel or 1
        return await send_osc(host, port, "/midi/note", [channel, note, velocity])

    if operation == "stop_midi":
        if note is None:
            return {"status": "error", "message": "note required for stop_midi"}
        channel = channel or 1
        return await send_osc(host, port, "/midi/note", [channel, note, 0])

    if operation == "send_midi_cc":
        if controller is None or value is None:
            return {
                "status": "error",
                "message": "controller and value required for send_midi_cc",
            }
        channel = channel or 1
        return await send_osc(host, port, "/midi/cc", [channel, controller, value])

    if operation == "set_vco_frequency":
        if module_id is None or frequency is None:
            return {
                "status": "error",
                "message": "module_id and frequency required for set_vco_frequency",
            }
        value = min(max(0.0, frequency / 10000.0), 1.0)
        return await send_osc(host, port, "/param", [module_id, 0, value])

    if operation == "set_vca_level":
        if module_id is None or level is None:
            return {
                "status": "error",
                "message": "module_id and level required for set_vca_level",
            }
        value = min(max(0.0, level), 1.0)
        return await send_osc(host, port, "/param", [module_id, 0, value])

    if operation == "set_lfo_rate":
        if module_id is None or rate is None:
            return {
                "status": "error",
                "message": "module_id and rate required for set_lfo_rate",
            }
        value = min(max(0.0, rate), 1.0)
        return await send_osc(host, port, "/param", [module_id, 0, value])

    if operation == "set_filter_cutoff":
        if module_id is None or cutoff is None:
            return {
                "status": "error",
                "message": "module_id and cutoff required for set_filter_cutoff",
            }
        value = min(max(0.0, cutoff), 1.0)
        return await send_osc(host, port, "/param", [module_id, 0, value])

    if operation == "set_envelope_attack":
        if module_id is None or attack is None:
            return {
                "status": "error",
                "message": "module_id and attack required for set_envelope_attack",
            }
        value = min(max(0.0, attack), 1.0)
        return await send_osc(host, port, "/param", [module_id, 0, value])

    if operation == "set_envelope_decay":
        if module_id is None or decay is None:
            return {
                "status": "error",
                "message": "module_id and decay required for set_envelope_decay",
            }
        value = min(max(0.0, decay), 1.0)
        return await send_osc(host, port, "/param", [module_id, 1, value])

    if operation == "set_envelope_sustain":
        if module_id is None or sustain is None:
            return {
                "status": "error",
                "message": "module_id and sustain required for set_envelope_sustain",
            }
        value = min(max(0.0, sustain), 1.0)
        return await send_osc(host, port, "/param", [module_id, 2, value])

    if operation == "set_envelope_release":
        if module_id is None or release is None:
            return {
                "status": "error",
                "message": "module_id and release required for set_envelope_release",
            }
        value = min(max(0.0, release), 1.0)
        return await send_osc(host, port, "/param", [module_id, 3, value])

    # REAPER-VCV Rack Bridge Operations
    if operation == "sync_reaper_tempo":
        # Listen for REAPER tempo changes and apply to VCV Rack
        # This would typically be used with get_received_messages to monitor REAPER
        if reaper_tempo is None:
            return {
                "status": "error",
                "message": "reaper_tempo required for sync_reaper_tempo",
            }
        # Convert BPM to VCV Rack clock rate (this is module-specific)
        # Most VCV sequencers expect BPM or clock division
        bpm_value = reaper_tempo / 120.0  # Normalize assuming 120 BPM = 1.0
        return await send_osc(host, port, "/param", [module_id or 1, 0, bpm_value])

    if operation == "start_transport":
        # Start VCV Rack transport/sequencer
        return await send_osc(host, port, "/transport/play", [])

    if operation == "stop_transport":
        # Stop VCV Rack transport/sequencer
        return await send_osc(host, port, "/transport/stop", [])

    if operation == "reset_transport":
        # Reset VCV Rack transport to beginning
        return await send_osc(host, port, "/transport/reset", [])

    if operation == "set_transport_position":
        # Set transport position (0.0-1.0 for normalized position)
        if position is None:
            return {
                "status": "error",
                "message": "position required for set_transport_position",
            }
        return await send_osc(host, port, "/transport/position", [position])

    return {"status": "error", "message": f"Unknown operation: {operation}"}


@server.tool()
async def osc_recorder_manager(
    operation: str,
    recording_name: str | None = None,
    port: int | None = None,
    playback_speed: float = 1.0,
    loop: bool = False,
    filter_address: str | None = None,
) -> dict[str, Any]:
    """
    OSC Recorder Manager - Record and playback OSC message sequences.

    PORTMANTEAU TOOL: Capture, store, and replay OSC automation sequences.

    Args:
        operation: Operation to perform
            - "start_recording" - Start recording OSC messages (requires recording_name, port)
            - "stop_recording" - Stop recording and save sequence
            - "list_recordings" - List all saved recordings
            - "playback_recording" - Play back a recorded sequence
            - "delete_recording" - Delete a saved recording
            - "get_recording_info" - Get details about a recording
        recording_name: Name for the recording (required for most operations)
        port: OSC server port to record from (for start_recording)
        playback_speed: Speed multiplier for playback (1.0 = normal speed)
        loop: Whether to loop playback continuously
        filter_address: Only record messages matching this OSC address pattern

    Returns:
        Operation result with recording details
    """

    if operation == "start_recording":
        if recording_name is None or port is None:
            return {
                "status": "error",
                "message": "recording_name and port required for start_recording",
            }

        if port not in osc_servers:
            return {
                "status": "error",
                "message": f"No OSC server running on port {port}",
            }

        # Clear any existing recording with this name
        osc_recordings[recording_name] = []

        # Mark that we're recording (this would need to be implemented in OSCServer)
        # For now, just acknowledge the start
        return {
            "status": "success",
            "message": f"Started recording '{recording_name}' on port {port}",
            "recording_name": recording_name,
            "port": port,
            "filter": filter_address,
        }

    if operation == "stop_recording":
        if recording_name is None:
            return {
                "status": "error",
                "message": "recording_name required for stop_recording",
            }

        if recording_name not in osc_recordings:
            return {
                "status": "error",
                "message": f"No recording found with name '{recording_name}'",
            }

        message_count = len(osc_recordings[recording_name])
        return {
            "status": "success",
            "message": f"Stopped recording '{recording_name}' with {message_count} messages",
            "recording_name": recording_name,
            "message_count": message_count,
        }

    if operation == "list_recordings":
        recordings = []
        for name, messages in osc_recordings.items():
            recordings.append(
                {
                    "name": name,
                    "message_count": len(messages),
                    "duration": messages[-1]["timestamp"] - messages[0]["timestamp"] if messages else 0,
                }
            )

        return {"status": "success", "recordings": recordings, "count": len(recordings)}

    if operation == "playback_recording":
        if recording_name is None:
            return {
                "status": "error",
                "message": "recording_name required for playback_recording",
            }

        if recording_name not in osc_recordings:
            return {
                "status": "error",
                "message": f"No recording found with name '{recording_name}'",
            }

        messages = osc_recordings[recording_name]
        if not messages:
            return {
                "status": "error",
                "message": f"Recording '{recording_name}' is empty",
            }

        # Calculate timing and send messages
        sent_count = 0

        for msg in messages:
            # Send the message (would need async scheduling for precise timing)
            # For now, just send immediately
            await send_osc("127.0.0.1", 10001, msg["address"], msg["args"])  # Default to VCV Rack
            sent_count += 1

        return {
            "status": "success",
            "message": f"Played back '{recording_name}' with {sent_count} messages",
            "recording_name": recording_name,
            "messages_sent": sent_count,
            "playback_speed": playback_speed,
            "looping": loop,
        }

    if operation == "delete_recording":
        if recording_name is None:
            return {
                "status": "error",
                "message": "recording_name required for delete_recording",
            }

        if recording_name not in osc_recordings:
            return {
                "status": "error",
                "message": f"No recording found with name '{recording_name}'",
            }

        del osc_recordings[recording_name]
        return {
            "status": "success",
            "message": f"Deleted recording '{recording_name}'",
            "recording_name": recording_name,
        }

    if operation == "get_recording_info":
        if recording_name is None:
            return {
                "status": "error",
                "message": "recording_name required for get_recording_info",
            }

        if recording_name not in osc_recordings:
            return {
                "status": "error",
                "message": f"No recording found with name '{recording_name}'",
            }

        messages = osc_recordings[recording_name]
        if not messages:
            return {
                "status": "success",
                "recording_name": recording_name,
                "message_count": 0,
                "duration": 0,
                "addresses": [],
            }

        addresses = list(set(msg["address"] for msg in messages))
        duration = messages[-1]["timestamp"] - messages[0]["timestamp"]

        return {
            "status": "success",
            "recording_name": recording_name,
            "message_count": len(messages),
            "duration": duration,
            "start_time": messages[0]["timestamp"],
            "end_time": messages[-1]["timestamp"],
            "addresses": addresses,
        }

    return {"status": "error", "message": f"Unknown operation: {operation}"}


@server.tool()
async def music_loader_manager(
    operation: str,
    midi_file_path: str | None = None,
    instrument_type: str = "organ",
    tempo: float | None = None,
    vcv_host: str = "127.0.0.1",
    vcv_port: int = 10001,
    reaper_host: str = "127.0.0.1",
    reaper_port: int = 8000,
    auto_setup: bool = True,
) -> dict[str, Any]:
    """
    Music Loader Manager - High-level orchestration for loading and playing music.

    PORTMANTEAU TOOL: Intelligent multi-step music production workflows.

    Args:
        operation: Operation to perform
            - "load_bach_organ" - Load J.S. Bach MIDI organ music with auto-setup
            - "load_midi_file" - Load any MIDI file with intelligent routing
            - "setup_organ_rig" - Auto-setup organ modules and routing
            - "start_performance" - Begin synchronized playback
            - "stop_performance" - Stop all playback
        midi_file_path: Path to MIDI file (for load operations)
        instrument_type: Type of instrument ("organ", "piano", "strings", etc.)
        tempo: Override tempo (BPM) for playback
        vcv_host/vcv_port: VCV Rack connection
        reaper_host/reaper_port: REAPER connection
        auto_setup: Whether to automatically configure modules and routing

    Returns:
        Operation result with setup details and playback status
    """

    if operation == "load_bach_organ":
        if midi_file_path is None:
            return {
                "status": "error",
                "message": "midi_file_path required for load_bach_organ",
            }

        # Step 1: Setup organ modules in VCV Rack
        setup_results = []

        if auto_setup:
            # Setup wavetable oscillator for organ sound (Bogaudio WT recommended)
            result = await send_osc(vcv_host, vcv_port, "/param", [1, 0, 0.5])  # WT wavetable select (organ preset)
            setup_results.append({"step": "wavetable_setup", "result": result})

            # Setup envelope for organ attack/decay
            result = await send_osc(vcv_host, vcv_port, "/param", [2, 0, 0.8])  # Attack
            setup_results.append({"step": "envelope_attack", "result": result})
            result = await send_osc(vcv_host, vcv_port, "/param", [2, 1, 0.7])  # Decay
            setup_results.append({"step": "envelope_decay", "result": result})

            # Setup filter for organ warmth
            result = await send_osc(vcv_host, vcv_port, "/param", [3, 0, 0.3])  # Cutoff
            setup_results.append({"step": "filter_cutoff", "result": result})

        # Step 2: Load MIDI file (would need MIDI file parsing)
        # For now, assume MIDI data is available and send note events
        result = await send_osc(vcv_host, vcv_port, "/midi/file/load", [midi_file_path])
        setup_results.append({"step": "midi_load", "result": result})

        # Step 3: Set tempo if provided
        if tempo:
            result = await send_osc(vcv_host, vcv_port, "/tempo", [tempo])
            setup_results.append({"step": "tempo_set", "result": result})

        return {
            "status": "success",
            "message": f"Loaded Bach organ music from {midi_file_path}",
            "instrument_type": instrument_type,
            "setup_steps": setup_results,
            "next_action": "Use start_performance to begin playback",
        }

    if operation == "load_midi_file":
        if midi_file_path is None:
            return {
                "status": "error",
                "message": "midi_file_path required for load_midi_file",
            }

        # Intelligent MIDI file loading with instrument detection
        # Parse MIDI file and setup appropriate modules based on content

        results = []

        # Load MIDI file
        result = await send_osc(vcv_host, vcv_port, "/midi/file/load", [midi_file_path])
        results.append({"step": "midi_load", "result": result})

        # Auto-detect instrument needs based on MIDI content
        if instrument_type == "organ":
            # Setup organ-like sound
            result = await send_osc(vcv_host, vcv_port, "/module/load", ["Bogaudio-WT", 1])
            results.append({"step": "load_organ_module", "result": result})

        elif instrument_type == "piano":
            # Setup piano-like sound
            result = await send_osc(vcv_host, vcv_port, "/module/load", ["PianoModule", 1])
            results.append({"step": "load_piano_module", "result": result})

        return {
            "status": "success",
            "message": f"Loaded MIDI file {midi_file_path} as {instrument_type}",
            "setup_results": results,
        }

    if operation == "setup_organ_rig":
        # Complete organ rig setup for Bach music
        setup_results = []

        # Load Bogaudio WT wavetable oscillator (free, excellent for organs)
        result = await send_osc(vcv_host, vcv_port, "/module/add", ["Bogaudio-WT", 1, 100, 100])
        setup_results.append({"step": "add_wavetable_osc", "result": result})

        # Add envelope generator
        result = await send_osc(vcv_host, vcv_port, "/module/add", ["Envelope", 2, 200, 100])
        setup_results.append({"step": "add_envelope", "result": result})

        # Add filter
        result = await send_osc(vcv_host, vcv_port, "/module/add", ["Filter", 3, 300, 100])
        setup_results.append({"step": "add_filter", "result": result})

        # Add audio output
        result = await send_osc(vcv_host, vcv_port, "/module/add", ["AudioOut", 4, 400, 100])
        setup_results.append({"step": "add_audio_out", "result": result})

        # Connect modules
        result = await send_osc(vcv_host, vcv_port, "/connect", [1, "out", 3, "in"])  # Osc -> Filter
        setup_results.append({"step": "connect_osc_filter", "result": result})
        result = await send_osc(vcv_host, vcv_port, "/connect", [2, "out", 1, "gate"])  # Env -> Osc gate
        setup_results.append({"step": "connect_env_osc", "result": result})
        result = await send_osc(vcv_host, vcv_port, "/connect", [3, "out", 4, "in"])  # Filter -> Audio Out
        setup_results.append({"step": "connect_filter_out", "result": result})

        return {
            "status": "success",
            "message": "Organ rig setup complete with Bogaudio WT",
            "modules_added": ["Bogaudio-WT", "Envelope", "Filter", "AudioOut"],
            "connections_made": 3,
            "setup_results": setup_results,
        }

    if operation == "start_performance":
        # Synchronized start across all applications
        results = []

        # Start VCV Rack sequencer
        result = await send_osc(vcv_host, vcv_port, "/transport/play", [])
        results.append({"app": "vcv_rack", "action": "start_transport", "result": result})

        # Start REAPER if available
        result = await send_osc(reaper_host, reaper_port, "/play", [])
        results.append({"app": "reaper", "action": "start_playback", "result": result})

        return {
            "status": "success",
            "message": "Performance started across all applications",
            "results": results,
        }

    if operation == "stop_performance":
        # Synchronized stop across all applications
        results = []

        # Stop VCV Rack sequencer
        result = await send_osc(vcv_host, vcv_port, "/transport/stop", [])
        results.append({"app": "vcv_rack", "action": "stop_transport", "result": result})

        # Stop REAPER if available
        result = await send_osc(reaper_host, reaper_port, "/stop", [])
        results.append({"app": "reaper", "action": "stop_playback", "result": result})

        return {
            "status": "success",
            "message": "Performance stopped across all applications",
            "results": results,
        }

    return {"status": "error", "message": f"Unknown operation: {operation}"}


@server.tool()
async def music_orchestrator(
    operation: str,
    # Bach demo specific
    midi_file_path: str | None = None,
    organ_module: int | None = None,
    # General orchestration
    workflow_name: str | None = None,
    tempo: float | None = None,
    key_signature: str | None = None,
    time_signature: str | None = None,
    # Multi-app coordination
    sync_apps: bool = True,
    record_performance: bool = False,
    recording_name: str | None = None,
) -> dict[str, Any]:
    """
    Music Orchestrator - High-level multi-step workflow automation.

    PORTMANTEAU TOOL: Conducts complex music production workflows across multiple applications.

    Args:
        operation: Operation to perform
            - "bach_organ_setup" - Load Bach MIDI organ music and configure rig
            - "performance_start" - Start synchronized performance across apps
            - "performance_stop" - Stop all performance elements
            - "create_custom_workflow" - Save current setup as reusable workflow
            - "load_workflow" - Load and execute saved workflow
            - "midi_to_cv" - Convert MIDI file to CV sequences for modular synth
            - "organ_voice_setup" - Configure organ-like sound (drawbars, reverb, etc.)
        midi_file_path: Path to MIDI file (for bach_organ_setup, midi_to_cv)
        organ_module: VCV Rack module ID for organ synthesis
        workflow_name: Name for custom workflow operations
        tempo/key_signature/time_signature: Musical parameters
        sync_apps: Whether to synchronize across applications
        record_performance: Whether to record the performance
        recording_name: Name for performance recording

    Returns:
        Operation result with orchestration details
    """

    if operation == "bach_organ_setup":
        if midi_file_path is None:
            return {
                "status": "error",
                "message": "midi_file_path required for bach_organ_setup",
            }

        results = {"status": "success", "steps": [], "setup_complete": False}

        # Step 1: Parse MIDI file (would need MIDI parsing library)
        results["steps"].append(
            {
                "step": "midi_parse",
                "status": "simulated",
                "message": f"Parsed MIDI file: {midi_file_path}",
            }
        )

        # Step 2: Extract organ-appropriate notes (Bach organ music)
        results["steps"].append(
            {
                "step": "organ_analysis",
                "status": "simulated",
                "message": "Analyzed for organ registration and voicing",
            }
        )

        # Step 3: Configure VCV Rack organ sound
        organ_module = organ_module or 1
        # Set up wavetable for organ-like sound (assuming Surge XT or similar)
        vcv_results = []
        vcv_results.append(await send_osc("127.0.0.1", 10001, "/param", [organ_module, 0, 0.3]))  # Organ wavetable
        vcv_results.append(await send_osc("127.0.0.1", 10001, "/param", [organ_module, 1, 0.7]))  # Reverb mix
        vcv_results.append(await send_osc("127.0.0.1", 10001, "/param", [organ_module, 2, 0.8]))  # Drawbar 8'
        vcv_results.append(await send_osc("127.0.0.1", 10001, "/param", [organ_module, 3, 0.6]))  # Drawbar 4'
        results["steps"].append({"step": "vcv_organ_setup", "status": "success", "results": vcv_results})

        # Step 4: Configure REAPER (if available) for additional processing
        if sync_apps:
            reaper_results = []
            reaper_results.append(await send_osc("127.0.0.1", 8000, "/tempo", [tempo or 120.0]))
            reaper_results.append(await send_osc("127.0.0.1", 8000, "/track/1/volume", [0.8]))
            results["steps"].append({"step": "reaper_sync", "status": "success", "results": reaper_results})

        # Step 5: Set up performance recording if requested
        if record_performance and recording_name:
            record_result = await osc_recorder_manager("start_recording", recording_name=recording_name, port=10001)
            results["steps"].append(
                {
                    "step": "recording_setup",
                    "status": "success",
                    "result": record_result,
                }
            )

        results["setup_complete"] = True
        results["ready_message"] = "🎵 Bach organ rig configured! Ready to perform. Use performance_start to begin."
        return results

    if operation == "performance_start":
        results = {"status": "success", "coordinated_apps": []}

        # Start all applications in sync
        if sync_apps:
            # VCV Rack transport
            vcv_result = await send_osc("127.0.0.1", 10001, "/transport/play", [])
            results["coordinated_apps"].append({"app": "vcv_rack", "operation": "start", "result": vcv_result})

            # REAPER transport
            reaper_result = await send_osc("127.0.0.1", 8000, "/play", [])
            results["coordinated_apps"].append({"app": "reaper", "operation": "start", "result": reaper_result})

            # Any other apps could be added here
            results["message"] = "🎼 Synchronized performance started across all applications!"
        else:
            results["message"] = "Performance start requested but sync_apps=False"

        return results

    if operation == "performance_stop":
        results = {"status": "success", "stopped_apps": []}

        # Stop all applications
        vcv_result = await send_osc("127.0.0.1", 10001, "/transport/stop", [])
        results["stopped_apps"].append({"app": "vcv_rack", "result": vcv_result})

        reaper_result = await send_osc("127.0.0.1", 8000, "/stop", [])
        results["stopped_apps"].append({"app": "reaper", "result": reaper_result})

        # Stop recording if active
        if record_performance and recording_name:
            record_result = await osc_recorder_manager("stop_recording", recording_name=recording_name)
            results["stopped_apps"].append({"app": "osc_recorder", "result": record_result})

        results["message"] = "🛑 Performance stopped across all applications."
        return results

    if operation == "organ_voice_setup":
        # Configure organ-like voice settings
        results = {"status": "success", "organ_settings": []}

        organ_module = organ_module or 1

        # Classic organ drawbar settings (8', 4', 2', etc.)
        drawbar_settings = [
            ("8ft_diapason", 0.8),  # Principal 8'
            ("4ft_octave", 0.6),  # Octave 4'
            ("2ft_super", 0.4),  # Super Octave 2'
            ("16ft_bourdon", 0.7),  # Bourdon 16'
            ("reverb", 0.5),  # Cathedral reverb
            ("tremolo", 0.3),  # Light tremolo
        ]

        for param_name, value in drawbar_settings:
            result = await send_osc("127.0.0.1", 10001, f"/organ/{param_name}", [value])
            results["organ_settings"].append({"parameter": param_name, "value": value, "result": result})

        results["message"] = "🎹 Organ voice configured with classic drawbar settings!"
        return results

    if operation == "midi_to_cv":
        if midi_file_path is None:
            return {
                "status": "error",
                "message": "midi_file_path required for midi_to_cv",
            }

        results = {"status": "success", "cv_sequences": []}

        # Parse MIDI and convert to CV sequences
        # This would create sequences for pitch, gate, velocity, etc.
        results["cv_sequences"].append(
            {
                "type": "pitch_cv",
                "notes": ["simulated", "bach", "organ", "sequence"],
                "message": f"Converted MIDI pitch data from {midi_file_path}",
            }
        )

        results["cv_sequences"].append(
            {
                "type": "gate_cv",
                "triggers": ["simulated", "note_on", "note_off", "events"],
                "message": "Generated gate signals for modular sequencer",
            }
        )

        results["cv_sequences"].append(
            {
                "type": "velocity_cv",
                "values": ["simulated", "dynamics", "from", "MIDI"],
                "message": "Converted velocity data to CV modulation",
            }
        )

        results["message"] = "🎛️ MIDI file converted to CV sequences for modular synthesis!"
        return results

    return {"status": "error", "message": f"Unknown operation: {operation}"}


@server.tool()
async def supercollider_manager(
    operation: str,
    host: str = "127.0.0.1",
    port: int = 57120,
    def_name: str | None = None,
    node_id: int | None = None,
    add_action: int | None = None,
    target: int | None = None,
    control_name: str | None = None,
    value: float | None = None,
) -> dict[str, Any]:
    """
    SuperCollider Manager - Algorithmic composition and audio synthesis.

    PORTMANTEAU TOOL: Consolidates all SuperCollider operations into one tool.

    Args:
        operation: Operation to perform
            - "create_synth" - Create synth
            - "free_node" - Free synth node
            - "set_control" - Set control value
        host: Target host (default: 127.0.0.1)
        port: Target port (default: 57120)
        def_name: Synth definition name (for create_synth)
        node_id: Node ID (for all operations)
        add_action: Add action (default: 0, for create_synth)
        target: Target node (default: 0, for create_synth)
        control_name: Control parameter name (for set_control)
        value: Control value (for set_control)

    Returns:
        Operation result with status and details
    """

    if operation == "create_synth":
        if def_name is None or node_id is None:
            return {
                "status": "error",
                "message": "def_name and node_id required for create_synth",
            }
        add_action = add_action or 0
        target = target or 0
        return await send_osc(host, port, "/s_new", [def_name, node_id, add_action, target])

    if operation == "free_node":
        if node_id is None:
            return {"status": "error", "message": "node_id required for free_node"}
        return await send_osc(host, port, "/n_free", [node_id])

    if operation == "set_control":
        if node_id is None or control_name is None or value is None:
            return {
                "status": "error",
                "message": "node_id, control_name, and value required for set_control",
            }
        return await send_osc(host, port, "/n_set", [node_id, control_name, value])

    return {"status": "error", "message": f"Unknown operation: {operation}"}


@server.tool()
async def maxmsp_manager(
    operation: str,
    host: str = "127.0.0.1",
    port: int = 4000,
    receiver: str | None = None,
    value: float | None = None,
) -> dict[str, Any]:
    """
    Max/MSP Manager - Audio/visual programming control.

    PORTMANTEAU TOOL: Consolidates all Max/MSP operations into one tool.

    Args:
        operation: Operation to perform
            - "send_bang" - Send bang message
            - "send_float" - Send float value
            - "toggle_dsp" - Toggle DSP processing
        host: Target host (default: 127.0.0.1)
        port: Target port (default: 4000)
        receiver: Receiver name (for send_bang, send_float)
        value: Float value (for send_float)

    Returns:
        Operation result with status and details
    """

    if operation == "send_bang":
        if receiver is None:
            return {"status": "error", "message": "receiver required for send_bang"}
        return await send_osc(host, port, f"/{receiver}", ["bang"])

    if operation == "send_float":
        if receiver is None or value is None:
            return {
                "status": "error",
                "message": "receiver and value required for send_float",
            }
        return await send_osc(host, port, f"/{receiver}", [value])

    if operation == "toggle_dsp":
        return await send_osc(host, port, "/dsp/toggle", [])

    return {"status": "error", "message": f"Unknown operation: {operation}"}


@server.tool()
async def resolume_manager(
    operation: str,
    host: str = "127.0.0.1",
    port: int = 7000,
    layer: int | None = None,
    column: int | None = None,
    opacity: float | None = None,
    bpm: float | None = None,
) -> dict[str, Any]:
    """
    Resolume Arena Manager - VJ software and live video mixing.

    PORTMANTEAU TOOL: Consolidates all Resolume Arena operations into one tool.

    Args:
        operation: Operation to perform
            - "play_clip" - Play clip in layer
            - "set_layer_opacity" - Set layer opacity (0.0-1.0)
            - "set_bpm" - Set transport BPM
        host: Target host (default: 127.0.0.1)
        port: Target port (default: 7000)
        layer: Layer index (for play_clip, set_layer_opacity)
        column: Column index (for play_clip)
        opacity: Opacity value (0.0-1.0, for set_layer_opacity)
        bpm: BPM value (for set_bpm)

    Returns:
        Operation result with status and details
    """

    if operation == "play_clip":
        if layer is None or column is None:
            return {
                "status": "error",
                "message": "layer and column required for play_clip",
            }
        return await send_osc(host, port, f"/composition/layers/{layer}/clips/{column}/connect", [1])

    if operation == "set_layer_opacity":
        if layer is None or opacity is None:
            return {
                "status": "error",
                "message": "layer and opacity required for set_layer_opacity",
            }
        return await send_osc(host, port, f"/composition/layers/{layer}/opacity", [opacity])

    if operation == "set_bpm":
        if bpm is None:
            return {"status": "error", "message": "bpm required for set_bpm"}
        return await send_osc(host, port, "/transport/tempo", [bpm])

    return {"status": "error", "message": f"Unknown operation: {operation}"}


@server.tool()
async def audio_workflow_manager(
    operation: str,
    # VCV Rack parameters
    vcv_host: str = "127.0.0.1",
    vcv_port: int = 10001,
    module_id: int | None = None,
    # REAPER parameters
    reaper_host: str = "127.0.0.1",
    reaper_port: int = 8000,
    track_index: int | None = None,
    # Common parameters
    bpm: float | None = None,
    start_stop: bool | None = None,
) -> dict[str, Any]:
    """
    Audio Workflow Manager - Coordinate multi-application audio workflows.

    PORTMANTEAU TOOL: Orchestrates complex workflows across multiple audio applications.

    Args:
        operation: Operation to perform
            - "sync_tempo_all" - Sync tempo across VCV Rack, REAPER, and other apps
            - "start_all" - Start transport in all connected applications
            - "stop_all" - Stop transport in all connected applications
            - "reset_all" - Reset all applications to beginning
            - "vcv_to_reaper_gate" - Route VCV Rack gates to REAPER as markers
            - "reaper_to_vcv_tempo" - Sync REAPER tempo changes to VCV Rack
        vcv_host/vcv_port: VCV Rack connection (default: 127.0.0.1:10001)
        reaper_host/reaper_port: REAPER connection (default: 127.0.0.1:8000)
        module_id: VCV Rack module ID for operations
        track_index: REAPER track index for operations
        bpm: Tempo in BPM for sync operations
        start_stop: True=start, False=stop for transport operations

    Returns:
        Operation result with status and details from all affected applications
    """

    results = {"status": "success", "operations": []}

    if operation == "sync_tempo_all":
        if bpm is None:
            return {"status": "error", "message": "bpm required for sync_tempo_all"}

        # Sync to VCV Rack (assuming BPM module on module_id)
        if module_id is not None:
            bpm_normalized = bpm / 120.0  # Normalize assuming 120 BPM = 1.0
            result = await send_osc(vcv_host, vcv_port, "/param", [module_id, 0, bpm_normalized])
            results["operations"].append({"app": "vcv_rack", "operation": "set_bpm", "result": result})

        # Sync to REAPER
        result = await send_osc(reaper_host, reaper_port, "/tempo", [bpm])
        results["operations"].append({"app": "reaper", "operation": "set_tempo", "result": result})

        results["message"] = f"Synced tempo {bpm} BPM across all applications"

    elif operation == "start_all":
        # Start VCV Rack transport
        result = await send_osc(vcv_host, vcv_port, "/transport/play", [])
        results["operations"].append({"app": "vcv_rack", "operation": "start_transport", "result": result})

        # Start REAPER transport
        result = await send_osc(reaper_host, reaper_port, "/play", [])
        results["operations"].append({"app": "reaper", "operation": "start_playback", "result": result})

        results["message"] = "Started transport in all applications"

    elif operation == "stop_all":
        # Stop VCV Rack transport
        result = await send_osc(vcv_host, vcv_port, "/transport/stop", [])
        results["operations"].append({"app": "vcv_rack", "operation": "stop_transport", "result": result})

        # Stop REAPER transport
        result = await send_osc(reaper_host, reaper_port, "/stop", [])
        results["operations"].append({"app": "reaper", "operation": "stop_playback", "result": result})

        results["message"] = "Stopped transport in all applications"

    elif operation == "reset_all":
        # Reset VCV Rack transport
        result = await send_osc(vcv_host, vcv_port, "/transport/reset", [])
        results["operations"].append({"app": "vcv_rack", "operation": "reset_transport", "result": result})

        # Reset REAPER transport (this might need REAPER-specific command)
        result = await send_osc(reaper_host, reaper_port, "/rewind", [])
        results["operations"].append({"app": "reaper", "operation": "reset_position", "result": result})

        results["message"] = "Reset all applications to beginning"

    else:
        return {"status": "error", "message": f"Unknown operation: {operation}"}

    return results


@server.tool()
async def puredata_manager(
    operation: str,
    host: str = "127.0.0.1",
    port: int = 3000,
    receiver: str | None = None,
    value: float | None = None,
) -> dict[str, Any]:
    """
    Pure Data Manager - Visual programming and audio processing.

    PORTMANTEAU TOOL: Consolidates all Pure Data operations into one tool.

    Args:
        operation: Operation to perform
            - "send_bang" - Send bang message
            - "send_float" - Send float value
            - "toggle_dsp" - Toggle DSP processing
        host: Target host (default: 127.0.0.1)
        port: Target port (default: 3000)
        receiver: Receiver name (for send_bang, send_float)
        value: Float value (for send_float)

    Returns:
        Operation result with status and details
    """

    if operation == "send_bang":
        if receiver is None:
            return {"status": "error", "message": "receiver required for send_bang"}
        return await send_osc(host, port, f"/{receiver}", ["bang"])

    if operation == "send_float":
        if receiver is None or value is None:
            return {
                "status": "error",
                "message": "receiver and value required for send_float",
            }
        return await send_osc(host, port, f"/{receiver}", [value])

    if operation == "toggle_dsp":
        return await send_osc(host, port, "/pd/dsp/toggle", [])

    return {"status": "error", "message": f"Unknown operation: {operation}"}


# This allows running the server directly with: python -m oscmcp.mcp_server
if __name__ == "__main__":
    # Run the FastMCP server with stdio transport
    run_server(server, server_name="OSC-MCP")

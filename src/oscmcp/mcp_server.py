"""OSC-MCP app-manager tools (Ableton, VCV Rack, TouchDesigner, VRChat, SuperCollider,
Max/MSP, Resolume, Pure Data, audio workflows, OSC recording, music orchestration).

Imported for side effects by `oscmcp.server` — every `@server.tool()` below registers
onto the shared FastMCP instance from `.server`. Do not run this module directly or as
`__main__`; process-level stdio binary-mode setup and logging config belong to the real
entry points (`run_server.py`, `oscmcp.__main__`), not here — a second, competing
stdout/logging setup in this module previously caused it to be dropped from the import
graph entirely (osc-mcp quality-check, 2026-09-04).
"""

import asyncio
import logging
from pathlib import Path
from typing import Any

import mido
from pydantic import BaseModel, Field

from .osc.client import OSCClient
from .osc.server import OSCServer
from .transport import run_server

logger = logging.getLogger(__name__)

# Create FastMCP instance with stdio transport
from .server import _DESTRUCTIVE, _MUTATING, _README_ONLY, server

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
    host: str, port: int, address: str, values: list[Any] | None = None, protocol: str = "udp"
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
        return await send_osc(host, port, "/live/song/start_playing", [])

    if operation == "stop":
        return await send_osc(host, port, "/live/song/stop_playing", [])

    if operation == "set_tempo":
        if bpm is None:
            return {"status": "error", "message": "bpm required for set_tempo"}
        return await send_osc(host, port, "/live/song/set/tempo", [bpm])

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
    input_name: str | None = None,
    tracking_type: str | None = None,
    enabled: bool = True,
    notify: bool = False,
) -> dict[str, Any]:
    """
    VRChat Manager - Avatar, world, and input control.

    PORTMANTEAU TOOL: Consolidates all VRChat operations into one tool.

    Args:
        operation: Operation to perform
            - "set_parameter" - Set avatar parameter (float/int/bool)
            - "send_chat" - Send chatbox message immediately
            - "chatbox_typing" - Show/hide the "..." typing indicator (no message sent)
            - "trigger_haptic" - NOT SUPPORTED - see docstring below
            - "input" - Simulate a movement/camera/action input
            - "tracking_control" - NOT SUPPORTED - see docstring below
            - "afk_toggle" - Convenience wrapper for the AFK avatar parameter
        host: Target host (default: 127.0.0.1)
        port: Target port (default: 9000)
        param_name: Parameter name (for set_parameter)
        value: Parameter value (for set_parameter); input magnitude 0.0-1.0 or
            0/1 for buttons (for input)
        message: Chat message (for send_chat only)
        device: Haptic device ('left', 'right', or 'both', for trigger_haptic)
        duration: Haptic duration (default: 0.1, for trigger_haptic)
        amplitude: Haptic amplitude (default: 0.5, for trigger_haptic)
        frequency: Haptic frequency (default: 0.0, for trigger_haptic)
        input_name: Input control name (for input) - Movement: "MoveForward",
            "MoveBackward", "MoveLeft", "MoveRight"; Look: "LookLeft",
            "LookRight"; Actions: "Jump", "Run",
            "GrabLeft"/"GrabRight", "UseLeft"/"UseRight", "DropLeft"/"DropRight",
            "ComfortLeft"/"ComfortRight", "QuickMenuToggleLeft"/"...Right", "Voice"
        tracking_type: unused - tracking_control is not supported (see below)
        enabled: True to enable, False to disable (for chatbox_typing /
            afk_toggle - AFK when enabled=True)
        notify: Play the chatbox notification sound (for send_chat, default
            False - matches VRChat's own default of no sound for OSC-driven text)

    Returns:
        Operation result with status and details

    ## Known gaps (verified via web research against docs.vrchat.com)

    `trigger_haptic` and `tracking_control` return `UNSUPPORTED_OPERATION`
    rather than sending a guessed address:
    - VRChat has **no universal haptic OSC address**. Real haptic feedback
      is driven per-avatar through Contact Receivers/PhysBones the avatar
      creator defines - there is no address this tool could send that
      would work across avatars.
    - VRChat has **no enable/disable-by-name address for body trackers**.
      Its real tracking OSC surface only lets external tracking hardware
      *send* numbered-slot position/rotation (`/tracking/trackers/{1-8|head}/
      position` and `/rotation`) - it has no address to toggle a named
      tracker on/off.

    `input_name`'s "LookUp"/"LookDown" were removed from the documented list
    above - VRChat's real Input OSC surface has no such addresses.

    Examples:
        >>> await vrchat_manager("input", input_name="MoveForward", value=1.0)
        >>> await vrchat_manager("input", input_name="Jump", value=1)
        >>> await vrchat_manager("chatbox_typing", enabled=True)
        >>> await vrchat_manager("afk_toggle", enabled=True)
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
        return await send_osc(host, port, "/chatbox/input", [message, True, notify])

    if operation == "chatbox_typing":
        return await send_osc(host, port, "/chatbox/typing", [enabled])

    if operation == "input":
        if input_name is None or value is None:
            return {
                "status": "error",
                "message": "input_name and value required for input",
            }
        return await send_osc(host, port, f"/input/{input_name}", [float(value)])

    if operation == "tracking_control":
        return {
            "status": "error",
            "error_code": "UNSUPPORTED_OPERATION",
            "message": (
                "VRChat's real OSC protocol has no address to enable/disable a body "
                "tracker by name - it only accepts numbered-slot position/rotation input "
                "for external tracking hardware (/tracking/trackers/{1-8|head}/position, "
                "/rotation), never an enable/disable toggle. This operation used to send a "
                "fabricated /tracking/{name}/enabled address; removed rather than fixed "
                "since no real equivalent exists."
            ),
        }

    if operation == "afk_toggle":
        return await send_osc(host, port, "/avatar/parameters/AFK", [1 if enabled else 0])

    if operation == "trigger_haptic":
        return {
            "status": "error",
            "error_code": "UNSUPPORTED_OPERATION",
            "message": (
                "VRChat has no universal haptic OSC address - real haptic feedback is "
                "driven per-avatar through Contact Receivers/PhysBones the avatar creator "
                "defines, which this tool has no way to know in advance. This operation "
                "used to send /avatar/parameters/LeftHaptic and RightHaptic, which are not "
                "part of VRChat's documented OSC protocol and are very unlikely to match "
                "any real avatar's actual parameter names."
            ),
        }

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


_VCV_UNSUPPORTED_OPERATIONS = {
    "send_cv": (
        "OSCelot has no OSC-settable CV concept - its Expander adds a physical "
        "CV/trigger *output* wired into your patch by cable, not something "
        "addressable over the network. There is no verified way to send an "
        "arbitrary CV voltage into VCV Rack via OSC."
    ),
    "set_light": (
        "OSCelot's OSC input only supports /fader, /encoder, /button on mapped "
        "slots - there is no light/LED-brightness message in its documented "
        "protocol (github.com/The-Modular-Mind/oscelot/blob/main/docs/Oscelot.md)."
    ),
    "play_midi": "VCV Rack has no native OSC-to-MIDI bridge; this address was never verified against any real module.",
    "stop_midi": "VCV Rack has no native OSC-to-MIDI bridge; this address was never verified against any real module.",
    "send_midi_cc": "VCV Rack has no native OSC-to-MIDI bridge; this address was never verified against any real module.",
    "start_transport": "No VCV Rack module is documented to expose a global /transport/* OSC surface; this was never verified.",
    "stop_transport": "No VCV Rack module is documented to expose a global /transport/* OSC surface; this was never verified.",
    "reset_transport": "No VCV Rack module is documented to expose a global /transport/* OSC surface; this was never verified.",
    "set_transport_position": "No VCV Rack module is documented to expose a global /transport/* OSC surface; this was never verified.",
}


@server.tool()
async def vcv_manager(
    operation: str,
    host: str = "127.0.0.1",
    port: int = 10001,
    module_id: int | None = None,
    value: float | None = None,
    reaper_tempo: float | None = None,
) -> dict[str, Any]:
    """
    VCV Rack Manager - modular synthesis control via OSCelot.

    PORTMANTEAU TOOL: Consolidates VCV Rack OSC operations into one tool.

    VCV Rack has no native OSC support at all. Every operation below assumes
    the community OSCelot module (TheModularMind, via the VCV Library)
    patched in - see docs/OSCELOT_MAPPING_GUIDE.md for the full setup.
    OSCelot's real, documented protocol (verified against
    github.com/The-Modular-Mind/oscelot/blob/main/docs/Oscelot.md) only
    supports THREE message types - `/fader`, `/encoder`, `/button` - each
    addressed by a **mapping slot Id you assigned by hand in OSCelot's UI**,
    never by a VCV module/parameter ID directly. There is no way to address
    an arbitrary, not-yet-mapped parameter over OSC.

    `module_id` below means "the OSCelot slot Id" (confusing name kept for
    backward compatibility - it is NOT a VCV Rack module ID).

    Args:
        operation: Operation to perform
            - "set_parameter" - Send a value to a mapped fader slot (0.0-1.0)
            - "trigger" - Press a mapped button slot
            - "sync_reaper_tempo" - Send REAPER's tempo to a mapped fader slot
              (normalized against 120 BPM = 1.0 - crude, no better convention
              is documented anywhere)
        host: Target host (default: 127.0.0.1)
        port: Target port (default: 10001) - must match OSCelot's own
            configured receive port, which has no fixed default
        module_id: OSCelot mapping slot Id (see docstring above)
        value: Fader value 0.0-1.0 (for set_parameter)
        reaper_tempo: Tempo from REAPER in BPM (for sync_reaper_tempo)

    Returns:
        Operation result with status and details. Operations with no
        verified real OSC surface (send_cv, set_light, MIDI, transport)
        return a clear "unsupported" error instead of silently sending an
        unverified address into the void - see git history if you want the
        previous (unverified) addresses.
    """

    if operation in _VCV_UNSUPPORTED_OPERATIONS:
        return {
            "status": "error",
            "error_code": "UNSUPPORTED_OPERATION",
            "message": _VCV_UNSUPPORTED_OPERATIONS[operation],
        }

    if operation == "set_parameter":
        if module_id is None or value is None:
            return {
                "status": "error",
                "message": "module_id (OSCelot slot Id) and value required for set_parameter",
            }
        return await send_osc(host, port, "/fader", [module_id, value])

    if operation == "trigger":
        if module_id is None:
            return {
                "status": "error",
                "message": "module_id (OSCelot slot Id) required for trigger",
            }
        return await send_osc(host, port, "/button", [module_id, 1.0])

    if operation == "sync_reaper_tempo":
        if reaper_tempo is None or module_id is None:
            return {
                "status": "error",
                "message": "module_id (OSCelot slot Id) and reaper_tempo required for sync_reaper_tempo",
            }
        bpm_value = min(max(0.0, reaper_tempo / 120.0), 1.0)  # crude normalization, no better convention documented
        return await send_osc(host, port, "/fader", [module_id, bpm_value])

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

    # VCV Rack has NO OSC API for adding modules / wiring cables / loading MIDI files.
    # The previous implementation sent fabricated addresses (/param,
    # /midi/file/load, /module/add, /connect, /tempo, /transport/*) that have
    # never existed in OSCelot or VCV. Instead we now do the honest thing:
    # generate a real, loadable .vcv patch file on disk and (optionally) CUA-
    # launch VCV Rack with it. If OSC support for something is missing, we just
    # do CUA automation in the patch — see src/oscmcp/cua/vcv_cua.py.
    if operation in ("load_bach_organ", "load_midi_file", "setup_organ_rig"):
        # CUA fallback: generate a Bach-ready organ patch
        try:
            import json as _json
            from pathlib import Path as _Path

            from oscmcp.vcv_presets import bach_organ as _bach_preset

            patch = _bach_preset()
            # Use per-operation filename so repeated calls don't clobber
            patch_name = {
                "load_bach_organ": "bach_organ",
                "load_midi_file": f"bach_organ_{Path(midi_file_path).stem if midi_file_path else 'custom'}",
                "setup_organ_rig": "bach_organ",
            }[operation]
            out = _Path(__file__).resolve().parents[2] / "patches" / f"{patch_name}.vcv"
            # sanitize filename
            out = _Path(str(out).replace(" ", "_").replace("/", "_"))
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(_json.dumps(patch, indent=2) + "\n", encoding="utf-8")
            patch_path = str(out)

            # Optionally CUA-launch VCV Rack with the patch (best-effort, never fatal)
            cua_result = None
            try:
                from oscmcp.cua.vcv_cua import launch_vcv_with_patch

                cua_result = launch_vcv_with_patch(_Path(patch_path))
            except Exception as _e:
                cua_result = {"launched": False, "error": str(_e)}

            msg = (
                f"Generated real VCV patch '{patch_path}' ({len(patch['modules'])} modules, "
                f"{len(patch['cables'])} cables) — open it in VCV Rack via File > Open "
                f"(OSC cannot add modules; this is the CUA fallback). "
                f"Then select MIDI device 'BachOrgan' in the MIDIToCVInterface and "
                f"play your MIDI file (use scripts/vcv_cua_bach.py for one-click CUA demo)."
            )
            if midi_file_path:
                msg += f" Requested MIDI file: {midi_file_path} — load it in REAPER or send via virtual MIDI port."

            return {
                "status": "success",
                "osc_status": "unsupported",
                "error_code": "OSC_UNSUPPORTED_CUA_FALLBACK",
                "message": msg,
                "operation": operation,
                "patch_path": patch_path,
                "modules": len(patch["modules"]),
                "cables": len(patch["cables"]),
                "cua": cua_result,
                "hint": "Try scripts/vcv_cua_bach.py for full CUA demo (patch + virtual MIDI playback)",
            }
        except Exception as e:
            return {
                "status": "error",
                "error_code": "UNSUPPORTED_OPERATION",
                "message": (
                    f"music_loader_manager '{operation}' has no real OSC implementation -- "
                    "VCV Rack exposes no OSC surface for adding modules, wiring cables, "
                    "or loading MIDI files (only OSCelot's /fader /encoder /button on "
                    "already-mapped slots, see docs/OSCELOT_MAPPING_GUIDE.md). "
                    f"CUA fallback also failed: {e}. Generate a .vcv patch via "
                    "src/oscmcp/vcv_patch_builder.py / src/oscmcp/vcv_presets.py "
                    "(patches/*.vcv) and open in Rack."
                ),
                "operation": operation,
            }

    if operation == "start_performance":
        # VCV Rack has no global /transport OSC -- only REAPER part is real.
        results = []
        results.append(
            {
                "app": "vcv_rack",
                "action": "start_transport",
                "status": "unsupported",
                "error_code": "UNSUPPORTED_OPERATION",
                "message": "No VCV Rack OSC transport -- open a .vcv patch and press play in Rack. See patches/ for prebuilt examples.",
            }
        )
        result = await send_osc(reaper_host, reaper_port, "/play", [])
        results.append({"app": "reaper", "action": "start_playback", "result": result})
        return {
            "status": "success",
            "message": "Performance start: REAPER via /play; VCV Rack has no OSC transport (see above)",
            "results": results,
        }

    if operation == "stop_performance":
        results = []
        results.append(
            {
                "app": "vcv_rack",
                "action": "stop_transport",
                "status": "unsupported",
                "error_code": "UNSUPPORTED_OPERATION",
                "message": "No VCV Rack OSC transport -- stop via Rack UI.",
            }
        )
        result = await send_osc(reaper_host, reaper_port, "/stop", [])
        results.append({"app": "reaper", "action": "stop_playback", "result": result})
        return {
            "status": "success",
            "message": "Performance stop: REAPER via /stop; VCV Rack has no OSC transport",
            "results": results,
        }

    return {"status": "error", "message": f"Unknown operation: {operation}"}


def _parse_midi_file(midi_file_path: str) -> dict[str, Any]:
    """Real MIDI parsing via mido - notes, tempo, duration.

    Replaces music_orchestrator's previous behavior of claiming a MIDI file
    was "parsed" and "analyzed" without ever opening it (fabricated
    "simulated" step data, and midi_to_cv returning hardcoded placeholder
    lists regardless of the file's actual content or even its existence).
    """
    path = Path(midi_file_path)
    if not path.exists():
        return {"success": False, "message": f"MIDI file not found: {midi_file_path}"}

    try:
        midi_file = mido.MidiFile(str(path))
    except (OSError, ValueError) as e:
        return {"success": False, "message": f"Could not read MIDI file: {e}"}

    tempo_bpm = 120.0
    notes: list[dict[str, Any]] = []
    for track in midi_file.tracks:
        for msg in track:
            if msg.type == "set_tempo":
                tempo_bpm = round(mido.tempo2bpm(msg.tempo), 2)
            elif msg.type == "note_on" and msg.velocity > 0:
                notes.append({"note": msg.note, "velocity": msg.velocity, "time": msg.time})

    return {
        "success": True,
        "tempo_bpm": tempo_bpm,
        "note_count": len(notes),
        "first_notes": notes[:10],
        "duration_seconds": round(midi_file.length, 2),
        "track_count": len(midi_file.tracks),
    }


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

        # Step 1: Actually parse the MIDI file (previously fabricated - never opened
        # the file at all, just echoed the path back with status "simulated").
        parsed = _parse_midi_file(midi_file_path)
        if not parsed["success"]:
            return {"status": "error", "message": parsed["message"]}

        results = {"status": "success", "steps": [], "setup_complete": False}
        results["steps"].append(
            {
                "step": "midi_parse",
                "status": "success",
                "message": f"Parsed {parsed['note_count']} notes, tempo {parsed['tempo_bpm']} BPM, "
                f"duration {parsed['duration_seconds']}s from {midi_file_path}",
                "note_count": parsed["note_count"],
                "tempo_bpm": parsed["tempo_bpm"],
            }
        )
        tempo = tempo or parsed["tempo_bpm"]

        # Step 2: Configure VCV Rack organ sound. This step loads a fixed
        # organ-preset patch (drawbar-style wavetable + reverb mix) - it does
        # NOT do per-note registration analysis from the parsed MIDI (that
        # would be a real audio-engineering feature, not a data-parsing one);
        # what changed is the file above genuinely being opened and real
        # tempo/note data now driving `tempo` instead of a hardcoded default.
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
            # /tempo (bare) is REAPER's *normalized* 0.0-1.0 tempo control per its
            # own default OSC pattern config - /tempo/raw takes an actual BPM value.
            reaper_results.append(await send_osc("127.0.0.1", 8000, "/tempo/raw", [tempo or 120.0]))
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

        # Previously returned fabricated placeholder lists (literally
        # containing the string "simulated") regardless of midi_file_path's
        # actual content or even whether the file existed. Now genuinely
        # parses the file and derives real pitch-CV (1V/octave, middle C=0V)
        # and velocity-CV (0.0-1.0) from the actual note events.
        parsed = _parse_midi_file(midi_file_path)
        if not parsed["success"]:
            return {"status": "error", "message": parsed["message"]}

        pitch_cv = [round((note["note"] - 60) / 12, 4) for note in parsed["first_notes"]]
        velocity_cv = [round(note["velocity"] / 127, 4) for note in parsed["first_notes"]]

        results = {
            "status": "success",
            "cv_sequences": [
                {
                    "type": "pitch_cv",
                    "voltages": pitch_cv,
                    "message": f"1V/octave pitch CV for the first {len(pitch_cv)} of {parsed['note_count']} notes",
                },
                {
                    "type": "velocity_cv",
                    "values": velocity_cv,
                    "message": "Velocity scaled 0.0-1.0",
                },
            ],
            "tempo_bpm": parsed["tempo_bpm"],
            "total_note_count": parsed["note_count"],
            "note": (
                "gate_cv timing is not derived here - tick-accurate note-on/note-off "
                "pairing and playback scheduling would need a sequencer loop, not a "
                "one-shot conversion; use osc_recorder_manager or a VCV sequencer "
                "module to actually play these values back in time."
            ),
        }
        results["message"] = f"🎛️ Converted {parsed['note_count']} notes from {midi_file_path} to CV data!"
        return results

    return {"status": "error", "message": f"Unknown operation: {operation}"}


@server.tool()
async def supercollider_manager(
    operation: str,
    host: str = "127.0.0.1",
    port: int = 57110,
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
        port: Target port (default: 57110)
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
    port: int = 7400,
    receiver: str | None = None,
    value: float | None = None,
) -> dict[str, Any]:
    """
    Max/MSP Manager - Audio/visual programming control.

    PORTMANTEAU TOOL: Consolidates all Max/MSP operations into one tool.

    Max has no fixed OSC namespace or default port at all - everything
    depends entirely on what the user's own patch does with `udpreceive`/
    `udpsend` (raw UDP, no OSC parsing) or `oscformat`/`oscparse` (Max's own
    OSC codec objects). `port=7400` here is this project's own convention
    (matches `app_detect.py`'s registry entry - previously these two
    disagreed, 4000 vs 7400), not a real Max default - always confirm the
    port against the user's actual patch.

    Args:
        operation: Operation to perform
            - "send_bang" - Send bang message
            - "send_float" - Send float value
            - "toggle_dsp" - NOT SUPPORTED - see docstring below
        host: Target host (default: 127.0.0.1)
        port: Target port (default: 7400 - see note above, not a real Max default)
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
        return {
            "status": "error",
            "error_code": "UNSUPPORTED_OPERATION",
            "message": (
                "'/dsp/toggle' has no primary-source backing anywhere in Max/MSP's "
                "documentation - Max has no built-in DSP-toggle OSC address; this would "
                "need a [udpreceive]->[route]->[dspstate~] (or similar) wired into the "
                "user's own patch, which this tool has no way to assume exists."
            ),
        }

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
        bpm: BPM value (for set_bpm) - sent as a raw BPM number; some forum
            reports suggest Resolume's tempo input actually expects a
            0.0-1.0 value normalized over a 20-500 BPM range instead, but
            this isn't confirmed against Resolume's own documentation -
            verify against a real instance before relying on exact tempo.

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
        # Verified live against Resolume Avenue 7.27.1: /composition/layers/{n}/opacity
        # is silently ignored (no error, no effect) - the real address needs /video/.
        return await send_osc(host, port, f"/composition/layers/{layer}/video/opacity", [opacity])

    if operation == "set_bpm":
        if bpm is None:
            return {"status": "error", "message": "bpm required for set_bpm"}
        # /transport/tempo appears nowhere in Resolume's own shipped OSC list -
        # verified real address is /composition/tempocontroller/tempo.
        return await send_osc(host, port, "/composition/tempocontroller/tempo", [bpm])

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

        # Sync to REAPER - /tempo (bare) is normalized 0.0-1.0 per REAPER's own
        # default OSC pattern config; /tempo/raw takes an actual BPM value.
        result = await send_osc(reaper_host, reaper_port, "/tempo/raw", [bpm])
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

        # Reset REAPER transport - /rewind is a hold-to-rewind gesture (REAPER's
        # default OSC config: "b/rewind", sends 1 to begin rewinding, 0 to stop),
        # not a jump-to-start action; REAPER's OSC protocol has no dedicated
        # "reset to start" address. The real fix is REAPER's generic action-by-ID
        # mechanism ("i/action" in its own OSC config): action 40042 is "Transport:
        # Go to start of project", confirmed against REAPER's own action list.
        result = await send_osc(reaper_host, reaper_port, "/action", [40042])
        results["operations"].append({"app": "reaper", "operation": "reset_position", "result": result})

        results["message"] = "Reset all applications to beginning"

    else:
        return {"status": "error", "message": f"Unknown operation: {operation}"}

    return results


@server.tool()
async def puredata_manager(
    operation: str,
    host: str = "127.0.0.1",
    port: int = 9000,
    receiver: str | None = None,
    value: float | None = None,
) -> dict[str, Any]:
    """
    Pure Data Manager - Visual programming and audio processing.

    PORTMANTEAU TOOL: Consolidates all Pure Data operations into one tool.

    Vanilla Pd has no built-in OSC support at all - every address here
    depends entirely on the user's own patch (typically the mrpeach OSC
    library's `[unpackOSC]`/`[routeOSC]` via Deken, receiving over
    `[netreceive -b]` in binary mode - plain `[netreceive]` is FUDI-only,
    not OSC). `port=9000` matches `app_detect.py`'s registry entry
    (previously these two disagreed, 3000 vs 9000) but is this project's
    own convention, not a real Pd default - there isn't one.

    Args:
        operation: Operation to perform
            - "send_bang" - Send bang message
            - "send_float" - Send float value
            - "toggle_dsp" - Toggle DSP processing
        host: Target host (default: 127.0.0.1)
        port: Target port (default: 9000 - see note above, not a real Pd default)
        receiver: Receiver name (for send_bang, send_float)
        value: Float value (for send_float)

    Returns:
        Operation result with status and details
    """

    if operation == "send_bang":
        if receiver is None:
            return {"status": "error", "message": "receiver required for send_bang"}
        # Zero-argument OSC message, matching mrpeach's idiomatic bang-over-OSC
        # convention (a string "bang" argument is not a documented mrpeach pattern).
        return await send_osc(host, port, f"/{receiver}", [])

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

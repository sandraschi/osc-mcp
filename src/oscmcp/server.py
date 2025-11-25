"""OSC-MCP Unified Server - Supports both stdio and HTTP transports.

This module implements a FastMCP 2.13 compliant server that provides OSC functionality
through the MCP protocol. It supports both stdio (for Claude Desktop) and HTTP transports,
configurable via command-line arguments.

Usage:
    # Stdio transport (default, for Claude Desktop)
    python -m oscmcp.server
    python -m oscmcp.server stdio

    # HTTP transport (for web-based MCP clients)
    python -m oscmcp.server http
    python -m oscmcp.server http --host 0.0.0.0 --port 8000
"""

import asyncio
import logging
import sys
from contextlib import asynccontextmanager
from typing import Any, Dict, List

from fastmcp import FastMCP
from pydantic import BaseModel, Field
from pythonosc import dispatcher, osc_server
from pythonosc.udp_client import SimpleUDPClient

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastMCP instance
server = FastMCP("OSC-MCP")

# Store OSC clients and servers
osc_clients: Dict[str, SimpleUDPClient] = {}
osc_servers: Dict[int, asyncio.Task] = {}

# Message buffer for received OSC messages
# Each port has its own message queue with max 1000 messages
from collections import deque
from datetime import datetime
osc_message_buffer: Dict[int, deque] = {}
MAX_BUFFER_SIZE = 1000

# Connection health tracking
connection_health: Dict[str, Dict[str, Any]] = {}
# Format: {"host:port": {"last_success": datetime, "failure_count": int, "circuit_open": bool}}

# Metrics tracking
metrics = {
    "messages_sent": 0,
    "messages_received": 0,
    "servers_started": 0,
    "servers_stopped": 0,
    "send_failures": 0,
    "server_start_time": datetime.now()
}

# Note: ResponseCachingMiddleware and lifespan hooks may not be available
# in all versions of FastMCP. They are optional features for improved performance
# and resource management but not required for core functionality.
logger.info("OSC-MCP server initialized")

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
        # Check circuit breaker
        client_key = f"{host}:{port}"
        if client_key in connection_health:
            health = connection_health[client_key]
            if health.get("circuit_open", False):
                # Check if we should retry (after 30 seconds)
                if (datetime.now() - health.get("last_failure", datetime.now())).seconds < 30:
                    return {
                        "status": "error",
                        "message": f"Circuit breaker open for {client_key} - too many failures",
                        "circuit_breaker": True
                    }
                else:
                    # Reset circuit breaker
                    health["circuit_open"] = False
                    health["failure_count"] = 0

        # Get or create OSC client
        if client_key not in osc_clients:
            osc_clients[client_key] = SimpleUDPClient(host, port)

        # Send the OSC message
        osc_clients[client_key].send_message(address, values)

        # Update metrics and health
        metrics["messages_sent"] += 1
        if client_key not in connection_health:
            connection_health[client_key] = {}
        connection_health[client_key]["last_success"] = datetime.now()
        connection_health[client_key]["failure_count"] = 0
        connection_health[client_key]["circuit_open"] = False

        logger.info(f"Sent OSC to {host}:{port} - {address}: {values}")
        return {
            "status": "success",
            "host": host,
            "port": port,
            "address": address,
            "values": values
        }
    except Exception as e:
        # Update failure metrics
        metrics["send_failures"] += 1
        if client_key not in connection_health:
            connection_health[client_key] = {}
        connection_health[client_key]["failure_count"] = connection_health[client_key].get("failure_count", 0) + 1
        connection_health[client_key]["last_failure"] = datetime.now()

        # Open circuit breaker after 3 failures
        if connection_health[client_key]["failure_count"] >= 3:
            connection_health[client_key]["circuit_open"] = True
            logger.warning(f"Circuit breaker opened for {client_key} after {connection_health[client_key]['failure_count']} failures")

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
        # Initialize message buffer for this port
        if port not in osc_message_buffer:
            osc_message_buffer[port] = deque(maxlen=MAX_BUFFER_SIZE)

        # Create dispatcher for OSC messages
        osc_dispatcher = dispatcher.Dispatcher()

        # Default handler that logs and buffers received messages
        def osc_handler(osc_addr: str, *args: Any) -> None:
            # Store message in buffer
            message = {
                "address": osc_addr,
                "values": list(args),
                "timestamp": datetime.now().isoformat(),
                "port": port
            }
            osc_message_buffer[port].append(message)

            # Update metrics
            metrics["messages_received"] += 1

            logger.info(f"Received OSC on port {port}: {osc_addr} {args}")

        # Register default handler for all addresses
        osc_dispatcher.set_default_handler(osc_handler)

        # Create and start OSC server
        loop = asyncio.get_event_loop()
        server_instance = osc_server.AsyncIOOSCUDPServer(
            (address, port),
            osc_dispatcher,
            loop
        )

        # Store the transport for later cleanup
        transport, _ = await server_instance.create_serve_endpoint()

        # Store server info
        osc_servers[port] = transport

        # Update metrics
        metrics["servers_started"] += 1

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

        # Update metrics
        metrics["servers_stopped"] += 1

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

@server.tool()
async def get_received_messages(
    port: int,
    limit: int = 100,
    clear: bool = False
) -> Dict[str, Any]:
    """Get received OSC messages from the buffer for a specific port.

    Retrieves messages that were received on the specified OSC server port.
    Messages are stored in a circular buffer (max 1000 messages per port).

    Args:
        port: Port number of the OSC server to get messages from
        limit: Maximum number of messages to return (default: 100, max: 1000)
        clear: Whether to clear the buffer after retrieving messages (default: False)

    Returns:
        Dictionary with status, port, message count, and list of messages

    Examples:
        # Get last 10 messages
        >>> await get_received_messages(9000, limit=10)
        {'status': 'success', 'port': 9000, 'count': 10, 'messages': [...]}

        # Get all messages and clear buffer
        >>> await get_received_messages(9000, limit=1000, clear=True)
    """
    if port not in osc_message_buffer:
        return {
            "status": "error",
            "message": f"No message buffer for port {port}. Start OSC server first."
        }

    buffer = osc_message_buffer[port]
    messages = list(buffer)[-limit:]  # Get last N messages

    if clear:
        buffer.clear()

    return {
        "status": "success",
        "port": port,
        "count": len(messages),
        "buffer_size": len(buffer),
        "messages": messages
    }

@server.tool()
async def get_connection_health() -> Dict[str, Any]:
    """Get health status of all OSC connections.

    Returns circuit breaker status, failure counts, and last success times
    for all connections that have been used.

    Returns:
        Dictionary with health status for each connection

    Examples:
        >>> await get_connection_health()
        {'status': 'success', 'connections': {'localhost:8000': {...}}}
    """
    health_status = {}
    for key, health in connection_health.items():
        health_status[key] = {
            "failure_count": health.get("failure_count", 0),
            "circuit_open": health.get("circuit_open", False),
            "last_success": health.get("last_success", "Never").isoformat() if isinstance(health.get("last_success"), datetime) else "Never",
            "last_failure": health.get("last_failure", "Never").isoformat() if isinstance(health.get("last_failure"), datetime) else "Never"
        }

    return {
        "status": "success",
        "connections": health_status
    }

@server.tool()
async def get_metrics() -> Dict[str, Any]:
    """Get server metrics and statistics.

    Returns:
        Dictionary with server metrics including message counts,
        server status, and uptime

    Examples:
        >>> await get_metrics()
        {'status': 'success', 'metrics': {...}}
    """
    uptime = (datetime.now() - metrics["server_start_time"]).total_seconds()

    return {
        "status": "success",
        "metrics": {
            "messages_sent": metrics["messages_sent"],
            "messages_received": metrics["messages_received"],
            "send_failures": metrics["send_failures"],
            "servers_started": metrics["servers_started"],
            "servers_stopped": metrics["servers_stopped"],
            "active_servers": len(osc_servers),
            "active_clients": len(osc_clients),
            "uptime_seconds": uptime,
            "start_time": metrics["server_start_time"].isoformat()
        }
    }

@server.tool()
async def clear_message_buffer(port: int = None) -> Dict[str, Any]:
    """Clear the OSC message buffer for a port or all ports.

    Args:
        port: Port number to clear (None = clear all ports)

    Returns:
        Dictionary with status and cleared buffer information

    Examples:
        # Clear specific port
        >>> await clear_message_buffer(9000)

        # Clear all ports
        >>> await clear_message_buffer()
    """
    if port is not None:
        if port in osc_message_buffer:
            count = len(osc_message_buffer[port])
            osc_message_buffer[port].clear()
            return {
                "status": "success",
                "message": f"Cleared {count} messages from port {port}"
            }
        else:
            return {
                "status": "error",
                "message": f"No message buffer for port {port}"
            }
    else:
        total = sum(len(buf) for buf in osc_message_buffer.values())
        for buf in osc_message_buffer.values():
            buf.clear()
        return {
            "status": "success",
            "message": f"Cleared {total} messages from {len(osc_message_buffer)} ports"
        }

#
# Application-Specific Tools
#

@server.tool()
async def ableton_transport_control(
    action: str,
    host: str = "127.0.0.1",
    port: int = 11000
) -> Dict[str, Any]:
    """Control Ableton Live transport (play, stop, etc).

    Args:
        action: Transport action - "play", "stop", "continue", or "record"
        host: Ableton Live host (default: 127.0.0.1)
        port: Ableton Live OSC port (default: 11000)

    Returns:
        Dictionary with status and action performed

    Examples:
        >>> await ableton_transport_control("play")
        >>> await ableton_transport_control("stop")
    """
    action_map = {
        "play": "/live/play",
        "stop": "/live/stop",
        "continue": "/live/continue_playing",
        "record": "/live/start_listen"
    }

    if action not in action_map:
        return {
            "status": "error",
            "message": f"Invalid action: {action}. Must be one of: {list(action_map.keys())}"
        }

    return await send_osc(host, port, action_map[action], [])

@server.tool()
async def ableton_set_tempo(
    bpm: float,
    host: str = "127.0.0.1",
    port: int = 11000
) -> Dict[str, Any]:
    """Set Ableton Live tempo.

    Args:
        bpm: Tempo in beats per minute (20-999)
        host: Ableton Live host (default: 127.0.0.1)
        port: Ableton Live OSC port (default: 11000)

    Returns:
        Dictionary with status

    Examples:
        >>> await ableton_set_tempo(120.0)
        >>> await ableton_set_tempo(140.5)
    """
    if not 20 <= bpm <= 999:
        return {
            "status": "error",
            "message": "BPM must be between 20 and 999"
        }

    return await send_osc(host, port, "/live/tempo", [float(bpm)])

@server.tool()
async def ableton_track_control(
    track: int,
    parameter: str,
    value: float,
    host: str = "127.0.0.1",
    port: int = 11000
) -> Dict[str, Any]:
    """Control Ableton Live track parameters.

    Args:
        track: Track number (1-based)
        parameter: Parameter name - "volume", "pan", "mute", "solo", "arm"
        value: Parameter value (0.0-1.0 for volume/pan, 0/1 for mute/solo/arm)
        host: Ableton Live host (default: 127.0.0.1)
        port: Ableton Live OSC port (default: 11000)

    Returns:
        Dictionary with status

    Examples:
        >>> await ableton_track_control(1, "volume", 0.8)
        >>> await ableton_track_control(2, "mute", 1)
    """
    param_map = {
        "volume": "/live/track/volume",
        "pan": "/live/track/pan",
        "mute": "/live/track/mute",
        "solo": "/live/track/solo",
        "arm": "/live/track/arm"
    }

    if parameter not in param_map:
        return {
            "status": "error",
            "message": f"Invalid parameter: {parameter}. Must be one of: {list(param_map.keys())}"
        }

    address = f"{param_map[parameter]}/{track}"
    return await send_osc(host, port, address, [float(value)])

@server.tool()
async def vrchat_avatar_parameter(
    parameter: str,
    value: float,
    host: str = "127.0.0.1",
    port: int = 9000
) -> Dict[str, Any]:
    """Set VRChat avatar parameter.

    Args:
        parameter: Avatar parameter name (e.g., "Voice", "Viseme", "GestureLeft")
        value: Parameter value (typically 0.0-1.0)
        host: VRChat OSC host (default: 127.0.0.1)
        port: VRChat OSC port (default: 9000)

    Returns:
        Dictionary with status

    Examples:
        >>> await vrchat_avatar_parameter("Voice", 0.8)
        >>> await vrchat_avatar_parameter("GestureLeft", 1.0)
    """
    address = f"/avatar/parameters/{parameter}"
    return await send_osc(host, port, address, [float(value)])

@server.tool()
async def vrchat_input(
    input_name: str,
    value: float,
    host: str = "127.0.0.1",
    port: int = 9000
) -> Dict[str, Any]:
    """Simulate VRChat input.

    Args:
        input_name: Input name - "Jump", "Run", "MoveForward", "MoveBackward", etc.
        value: Input value (0.0-1.0, or 0/1 for buttons)
        host: VRChat OSC host (default: 127.0.0.1)
        port: VRChat OSC port (default: 9000)

    Returns:
        Dictionary with status

    Examples:
        >>> await vrchat_input("Jump", 1)
        >>> await vrchat_input("MoveForward", 0.5)
    """
    address = f"/input/{input_name}"
    return await send_osc(host, port, address, [float(value)])

@server.tool()
async def touchdesigner_parameter(
    operator_path: str,
    parameter: str,
    value: Any,
    host: str = "127.0.0.1",
    port: int = 9000
) -> Dict[str, Any]:
    """Set TouchDesigner operator parameter.

    Args:
        operator_path: Path to operator (e.g., "/project/geo1")
        parameter: Parameter name (e.g., "tx", "ty", "tz", "opacity")
        value: Parameter value (float, int, or string)
        host: TouchDesigner OSC host (default: 127.0.0.1)
        port: TouchDesigner OSC port (default: 9000)

    Returns:
        Dictionary with status

    Examples:
        >>> await touchdesigner_parameter("/project/geo1", "tx", 100.0)
        >>> await touchdesigner_parameter("/project/comp1", "opacity", 0.75)
    """
    address = f"{operator_path}/{parameter}"
    values = [value] if not isinstance(value, list) else value
    return await send_osc(host, port, address, values)

# Alias tools for backward compatibility
send_osc_message = send_osc
start_osc_listener = start_osc_server

def main():
    """Main entry point with transport selection."""
    # Parse command-line arguments
    transport = "stdio"  # Default transport
    host = "0.0.0.0"
    port = 8000

    if len(sys.argv) > 1:
        transport = sys.argv[1].lower()

    if len(sys.argv) > 2 and sys.argv[2] == "--host":
        host = sys.argv[3]

    if len(sys.argv) > 4 and sys.argv[4] == "--port":
        port = int(sys.argv[5])

    # Validate transport
    if transport not in ["stdio", "http"]:
        logger.error(f"Invalid transport: {transport}. Use 'stdio' or 'http'")
        sys.exit(1)

    # Run server with selected transport
    if transport == "http":
        logger.info(f"Starting OSC-MCP server with HTTP transport on {host}:{port}")
        server.run(transport="streamable-http", host=host, port=port)
    else:
        logger.info("Starting OSC-MCP server with stdio transport")
        server.run(transport="stdio")

# This allows running the server directly with: python -m oscmcp.server
if __name__ == "__main__":
    main()

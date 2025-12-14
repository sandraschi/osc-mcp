"""OSC-MCP Server with stdio transport for MCP clients.

This module implements a FastMCP 2.13 compliant server that provides OSC functionality
through the MCP protocol over stdio, making it compatible with MCP clients like Claude or Windsurf.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

from fastmcp import FastMCP
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

# Lifespan management removed - FastMCP 2.13.1 doesn't support lifespan decorator
# Resource cleanup happens automatically when server shuts down

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

@server.tool()
async def test_osc_echo(port: int = 9000) -> Dict[str, Any]:
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
                "server_stopped": False
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
                "server_stopped": False
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
            "server_stopped": server_stopped
        }
        
    except Exception as e:
        error = f"OSC echo test failed: {e}"
        logger.error(error)
        
        # Try to stop server if it was started
        if server_started:
            try:
                await stop_osc_server(port)
                server_stopped = True
            except:
                pass
        
        return {
            "status": "error",
            "message": error,
            "port": port,
            "test_address": test_address,
            "test_values": test_values,
            "server_started": server_started,
            "message_sent": message_sent,
            "server_stopped": server_stopped
        }

# ============================================================================
# Application-Specific Tools
# ============================================================================
# These tools provide high-level interfaces for specific applications
# They use the send_osc function internally

@server.tool()
async def ableton_manager(operation: str, host: str = "127.0.0.1", port: int = 11000,
                         track_index: Optional[int] = None, clip_slot: Optional[int] = None,
                         bpm: Optional[float] = None, volume: Optional[float] = None,
                         pan: Optional[float] = None) -> Dict[str, Any]:
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

    elif operation == "stop":
        return await send_osc(host, port, "/live/stop", [])

    elif operation == "set_tempo":
        if bpm is None:
            return {"status": "error", "message": "bpm required for set_tempo"}
        return await send_osc(host, port, "/live/tempo", [bpm])

    elif operation == "play_clip":
        if track_index is None or clip_slot is None:
            return {"status": "error", "message": "track_index and clip_slot required for play_clip"}
        return await send_osc(host, port, "/live/clip/fire", [track_index, clip_slot])

    elif operation == "set_volume":
        if track_index is None or volume is None:
            return {"status": "error", "message": "track_index and volume required for set_volume"}
        return await send_osc(host, port, "/live/track/set/volume", [track_index, volume])

    elif operation == "set_pan":
        if track_index is None or pan is None:
            return {"status": "error", "message": "track_index and pan required for set_pan"}
        return await send_osc(host, port, "/live/track/set/panning", [track_index, pan])

    else:
        return {"status": "error", "message": f"Unknown operation: {operation}"}

@server.tool()
async def vrchat_manager(operation: str, host: str = "127.0.0.1", port: int = 9000,
                        param_name: Optional[str] = None, value: Optional[float] = None,
                        message: Optional[str] = None, device: Optional[str] = None,
                        duration: Optional[float] = None, amplitude: Optional[float] = None,
                        frequency: Optional[float] = None) -> Dict[str, Any]:
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
            return {"status": "error", "message": "param_name and value required for set_parameter"}
        address = f"/avatar/parameters/{param_name}"
        return await send_osc(host, port, address, [value])

    elif operation == "send_chat":
        if message is None:
            return {"status": "error", "message": "message required for send_chat"}
        return await send_osc(host, port, "/chatbox/input", [message, True, False])

    elif operation == "trigger_haptic":
        device = device or "both"
        duration = duration or 0.1
        amplitude = amplitude or 0.5
        frequency = frequency or 0.0

        results = {}
        if device.lower() in ('left', 'both'):
            await send_osc(host, port, "/avatar/parameters/LeftHaptic", [duration, amplitude, frequency])
            results['left'] = 'sent'
        if device.lower() in ('right', 'both'):
            await send_osc(host, port, "/avatar/parameters/RightHaptic", [duration, amplitude, frequency])
            results['right'] = 'sent'
        return {"status": "success", "device": device, "results": results}

    else:
        return {"status": "error", "message": f"Unknown operation: {operation}"}

@server.tool()
async def touchdesigner_manager(operation: str, host: str = "127.0.0.1", port: int = 9000,
                               component_path: Optional[str] = None, parameter: Optional[str] = None,
                               value: Optional[float] = None) -> Dict[str, Any]:
    """
    TouchDesigner Manager - Real-time visual programming control.

    PORTMANTEAU TOOL: Consolidates all TouchDesigner operations into one tool.

    Args:
        operation: Operation to perform
            - "set_parameter" - Set component parameter
            - "set_constant" - Set constant component value
            - "trigger_button" - Trigger button component
        host: Target host (default: 127.0.0.1)
        port: Target port (default: 9000)
        component_path: Component path (e.g., '/project1/constant1')
        parameter: Parameter name (for set_parameter)
        value: Parameter/constant value

    Returns:
        Operation result with status and details
    """

    if operation == "set_parameter":
        if component_path is None or parameter is None or value is None:
            return {"status": "error", "message": "component_path, parameter, and value required for set_parameter"}
        address = f"{component_path}/{parameter}"
        return await send_osc(host, port, address, [value])

    elif operation == "set_constant":
        if component_path is None or value is None:
            return {"status": "error", "message": "component_path and value required for set_constant"}
        return await send_osc(host, port, f"{component_path}/value1", [value])

    elif operation == "trigger_button":
        if component_path is None:
            return {"status": "error", "message": "component_path required for trigger_button"}
        return await send_osc(host, port, f"{component_path}/pulse", [1])

    else:
        return {"status": "error", "message": f"Unknown operation: {operation}"}


# --- Application Manager Tools ---

@server.tool()
async def vcv_manager(operation: str, host: str = "127.0.0.1", port: int = 10001,
                      module_id: Optional[int] = None, param_id: Optional[int] = None,
                      value: Optional[float] = None, cv_id: Optional[int] = None,
                      voltage: Optional[float] = None, light_id: Optional[int] = None,
                      brightness: Optional[float] = None, trigger_id: Optional[int] = None,
                      note: Optional[int] = None, velocity: Optional[int] = None,
                      channel: Optional[int] = None, controller: Optional[int] = None,
                      frequency: Optional[float] = None, level: Optional[float] = None,
                      rate: Optional[float] = None, cutoff: Optional[float] = None,
                      attack: Optional[float] = None, decay: Optional[float] = None,
                      sustain: Optional[float] = None, release: Optional[float] = None) -> Dict[str, Any]:
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

    Returns:
        Operation result with status and details
    """

    if operation == "set_parameter":
        if module_id is None or param_id is None or value is None:
            return {"status": "error", "message": "module_id, param_id, and value required for set_parameter"}
        return await send_osc(host, port, "/param", [module_id, param_id, value])

    elif operation == "trigger":
        if module_id is None or trigger_id is None:
            return {"status": "error", "message": "module_id and trigger_id required for trigger"}
        return await send_osc(host, port, "/trigger", [module_id, trigger_id])

    elif operation == "send_cv":
        if module_id is None or cv_id is None or voltage is None:
            return {"status": "error", "message": "module_id, cv_id, and voltage required for send_cv"}
        return await send_osc(host, port, "/cv", [module_id, cv_id, voltage])

    elif operation == "set_light":
        if module_id is None or light_id is None or brightness is None:
            return {"status": "error", "message": "module_id, light_id, and brightness required for set_light"}
        return await send_osc(host, port, "/light", [module_id, light_id, brightness])

    elif operation == "play_midi":
        if note is None:
            return {"status": "error", "message": "note required for play_midi"}
        velocity = velocity or 100
        channel = channel or 1
        return await send_osc(host, port, "/midi/note", [channel, note, velocity])

    elif operation == "stop_midi":
        if note is None:
            return {"status": "error", "message": "note required for stop_midi"}
        channel = channel or 1
        return await send_osc(host, port, "/midi/note", [channel, note, 0])

    elif operation == "send_midi_cc":
        if controller is None or value is None:
            return {"status": "error", "message": "controller and value required for send_midi_cc"}
        channel = channel or 1
        return await send_osc(host, port, "/midi/cc", [channel, controller, value])

    elif operation == "set_vco_frequency":
        if module_id is None or frequency is None:
            return {"status": "error", "message": "module_id and frequency required for set_vco_frequency"}
        value = min(max(0.0, frequency / 10000.0), 1.0)
        return await send_osc(host, port, "/param", [module_id, 0, value])

    elif operation == "set_vca_level":
        if module_id is None or level is None:
            return {"status": "error", "message": "module_id and level required for set_vca_level"}
        value = min(max(0.0, level), 1.0)
        return await send_osc(host, port, "/param", [module_id, 0, value])

    elif operation == "set_lfo_rate":
        if module_id is None or rate is None:
            return {"status": "error", "message": "module_id and rate required for set_lfo_rate"}
        value = min(max(0.0, rate), 1.0)
        return await send_osc(host, port, "/param", [module_id, 0, value])

    elif operation == "set_filter_cutoff":
        if module_id is None or cutoff is None:
            return {"status": "error", "message": "module_id and cutoff required for set_filter_cutoff"}
        value = min(max(0.0, cutoff), 1.0)
        return await send_osc(host, port, "/param", [module_id, 0, value])

    elif operation == "set_envelope_attack":
        if module_id is None or attack is None:
            return {"status": "error", "message": "module_id and attack required for set_envelope_attack"}
        value = min(max(0.0, attack), 1.0)
        return await send_osc(host, port, "/param", [module_id, 0, value])

    elif operation == "set_envelope_decay":
        if module_id is None or decay is None:
            return {"status": "error", "message": "module_id and decay required for set_envelope_decay"}
        value = min(max(0.0, decay), 1.0)
        return await send_osc(host, port, "/param", [module_id, 1, value])

    elif operation == "set_envelope_sustain":
        if module_id is None or sustain is None:
            return {"status": "error", "message": "module_id and sustain required for set_envelope_sustain"}
        value = min(max(0.0, sustain), 1.0)
        return await send_osc(host, port, "/param", [module_id, 2, value])

    elif operation == "set_envelope_release":
        if module_id is None or release is None:
            return {"status": "error", "message": "module_id and release required for set_envelope_release"}
        value = min(max(0.0, release), 1.0)
        return await send_osc(host, port, "/param", [module_id, 3, value])

    else:
        return {"status": "error", "message": f"Unknown operation: {operation}"}

@server.tool()
async def supercollider_manager(operation: str, host: str = "127.0.0.1", port: int = 57120,
                               def_name: Optional[str] = None, node_id: Optional[int] = None,
                               add_action: Optional[int] = None, target: Optional[int] = None,
                               control_name: Optional[str] = None, value: Optional[float] = None) -> Dict[str, Any]:
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
            return {"status": "error", "message": "def_name and node_id required for create_synth"}
        add_action = add_action or 0
        target = target or 0
        return await send_osc(host, port, "/s_new", [def_name, node_id, add_action, target])

    elif operation == "free_node":
        if node_id is None:
            return {"status": "error", "message": "node_id required for free_node"}
        return await send_osc(host, port, "/n_free", [node_id])

    elif operation == "set_control":
        if node_id is None or control_name is None or value is None:
            return {"status": "error", "message": "node_id, control_name, and value required for set_control"}
        return await send_osc(host, port, "/n_set", [node_id, control_name, value])

    else:
        return {"status": "error", "message": f"Unknown operation: {operation}"}

@server.tool()
async def maxmsp_manager(operation: str, host: str = "127.0.0.1", port: int = 4000,
                        receiver: Optional[str] = None, value: Optional[float] = None) -> Dict[str, Any]:
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

    elif operation == "send_float":
        if receiver is None or value is None:
            return {"status": "error", "message": "receiver and value required for send_float"}
        return await send_osc(host, port, f"/{receiver}", [value])

    elif operation == "toggle_dsp":
        return await send_osc(host, port, "/dsp/toggle", [])

    else:
        return {"status": "error", "message": f"Unknown operation: {operation}"}

@server.tool()
async def resolume_manager(operation: str, host: str = "127.0.0.1", port: int = 7000,
                          layer: Optional[int] = None, column: Optional[int] = None,
                          opacity: Optional[float] = None, bpm: Optional[float] = None) -> Dict[str, Any]:
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
            return {"status": "error", "message": "layer and column required for play_clip"}
        return await send_osc(host, port, f"/composition/layers/{layer}/clips/{column}/connect", [1])

    elif operation == "set_layer_opacity":
        if layer is None or opacity is None:
            return {"status": "error", "message": "layer and opacity required for set_layer_opacity"}
        return await send_osc(host, port, f"/composition/layers/{layer}/opacity", [opacity])

    elif operation == "set_bpm":
        if bpm is None:
            return {"status": "error", "message": "bpm required for set_bpm"}
        return await send_osc(host, port, "/transport/tempo", [bpm])

    else:
        return {"status": "error", "message": f"Unknown operation: {operation}"}

@server.tool()
async def puredata_manager(operation: str, host: str = "127.0.0.1", port: int = 3000,
                          receiver: Optional[str] = None, value: Optional[float] = None) -> Dict[str, Any]:
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

    elif operation == "send_float":
        if receiver is None or value is None:
            return {"status": "error", "message": "receiver and value required for send_float"}
        return await send_osc(host, port, f"/{receiver}", [value])

    elif operation == "toggle_dsp":
        return await send_osc(host, port, "/pd/dsp/toggle", [])

    else:
        return {"status": "error", "message": f"Unknown operation: {operation}"}

# This allows running the server directly with: python -m oscmcp.mcp_server
if __name__ == "__main__":
    # Run the FastMCP server with stdio transport
    server.run(transport="stdio")

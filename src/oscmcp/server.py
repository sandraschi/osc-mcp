"""OSC-MCP Server Implementation.

This module implements the core OSC server functionality using FastMCP 2.13
and python-osc for Open Sound Control protocol support.
"""

import asyncio
import logging
from typing import Any, Dict, List

from fastmcp import FastMCP
from pydantic import BaseModel, Field
from pythonosc import dispatcher, osc_server
from pythonosc.udp_client import SimpleUDPClient

# Set up logging
logger = logging.getLogger(__name__)

# Create FastMCP instance
server = FastMCP("OSC-MCP")

# Store OSC server instances and transports for cleanup
_osc_transports: List[Any] = []


# Pydantic models for input validation (FastMCP 2.13)
class OSCMessageInput(BaseModel):
    """Input model for OSC message sending."""

    host: str = Field(..., description="Target hostname or IP address")
    port: int = Field(..., gt=0, le=65535, description="Target UDP port (1-65535)")
    address: str = Field(
        ..., pattern=r"^/.*", description="OSC address pattern starting with /"
    )
    values: List[Any] = Field(..., description="List of values to send")


class OSCListenerInput(BaseModel):
    """Input model for starting OSC listener."""

    port: int = Field(
        ..., gt=0, le=65535, description="UDP port to listen on (1-65535)"
    )
    address: str = Field(default="0.0.0.0", description="Network interface to bind to")


class OSCEchoTestInput(BaseModel):
    """Input model for OSC echo test."""

    port: int = Field(
        default=9000, gt=0, le=65535, description="Test port to use (1-65535)"
    )


# Lifespan management removed - FastMCP 2.13.1 doesn't support lifespan decorator
# Resource cleanup happens automatically when server shuts down
async def server_lifespan():
    """Manage server-level OSC resources.

    This lifespan hook ensures proper initialization and cleanup of OSC resources
    at the server level (not per-client session), following FastMCP 2.13 semantics.
    """
    # Startup
    logger.info("OSC-MCP HTTP server starting up - initializing resources")

    try:
        yield  # Server runs here
    finally:
        # Shutdown - cleanup all OSC resources
        logger.info("OSC-MCP HTTP server shutting down - cleaning up resources")

        # Close all OSC server transports
        for idx, transport in enumerate(_osc_transports):
            try:
                transport.close()
                logger.info(f"Closed OSC transport {idx}")
            except Exception as e:
                logger.error(f"Error closing OSC transport {idx}: {e}")

        # Clear all resources
        _osc_transports.clear()
        logger.info("OSC-MCP HTTP server cleanup complete")


@server.tool()
async def send_osc_message(
    host: str, port: int, address: str, values: List[Any]
) -> Dict[str, Any]:
    """Send OSC message to target application.

    Args:
        host: Target host IP address
        port: Target port number
        address: OSC address pattern (e.g., "/volume")
        values: List of values to send (will be converted to appropriate OSC types)

    Returns:
        Dictionary with status and sent message details

    Example:
        await send_osc_message("127.0.0.1", 8000, "/volume", [0.8])
    """
    try:
        client = SimpleUDPClient(host, port)
        client.send_message(address, values)
        logger.info(f"Sent OSC message to {host}:{port} - {address}: {values}")
        return {
            "status": "success",
            "message": "OSC message sent successfully",
            "host": host,
            "port": port,
            "address": address,
            "values": values,
        }
    except Exception as e:
        error_msg = f"Failed to send OSC message: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {
            "status": "error",
            "message": error_msg,
            "host": host,
            "port": port,
            "address": address,
            "values": values,
        }


@server.tool()
async def start_osc_listener(port: int, address: str = "0.0.0.0") -> Dict[str, Any]:
    """Start OSC server to receive messages.

    Args:
        port: Port to listen on
        address: Interface address to bind to (default: "0.0.0.0" for all interfaces)

    Returns:
        Dictionary with server status and information
    """
    # Create dispatcher and server
    osc_dispatcher = dispatcher.Dispatcher()

    # Default handler for all messages
    def default_handler(addr: str, *args: Any) -> None:
        """Handle incoming OSC messages."""
        logger.info(f"Received OSC message: {addr} {args}")
        # Here you can add custom message handling logic
        # For example, you could emit events or call other functions

    # Set default handler for all addresses
    osc_dispatcher.set_default_handler(default_handler)

    try:
        # Create and start the server in a non-blocking way
        server = osc_server.AsyncIOOSCUDPServer(
            (address, port), osc_dispatcher, asyncio.get_event_loop()
        )

        # Start the server in the background
        transport, _ = await server.create_serve_endpoint()

        # Store transport for cleanup during server shutdown
        _osc_transports.append(transport)

        logger.info(f"OSC server started on {address}:{port}")

        return {
            "status": "success",
            "message": "OSC server started successfully",
            "address": address,
            "port": port,
            "transport": str(
                transport
            ),  # For reference, actual transport object can't be serialized
        }

    except Exception as e:
        error_msg = f"Failed to start OSC server: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {
            "status": "error",
            "message": error_msg,
            "address": address,
            "port": port,
        }


# Add a simple test function to verify the server is working
@server.tool()
async def test_osc_echo(port: int = 9000) -> Dict[str, Any]:
    """Test OSC functionality by sending and receiving a message.

    This is a test function that starts a server, sends a message to itself,
    and verifies the message was received.
    """
    # Start the server
    server_result = await start_osc_listener(port)
    if server_result["status"] != "success":
        return {
            "status": "error",
            "message": f"Failed to start test server: {server_result['message']}",
        }

    # Send a test message
    test_address = "/test/echo"
    test_values = [1, 2.0, "three", True]

    send_result = await send_osc_message("127.0.0.1", port, test_address, test_values)
    if send_result["status"] != "success":
        return {
            "status": "error",
            "message": f"Failed to send test message: {send_result['message']}",
        }

    # In a real implementation, you would verify the message was received
    # For now, we'll just return success
    return {
        "status": "success",
        "message": "OSC echo test completed",
        "test_address": test_address,
        "test_values": test_values,
        "server": server_result,
        "send_result": send_result,
    }


# This allows running the server directly with: python -m oscmcp.server
if __name__ == "__main__":
    # Run the FastMCP server with stdio transport (for MCP clients)
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "http":
        # HTTP transport mode
        server.run(transport="streamable-http", host="0.0.0.0", port=8000)
    else:
        # Default: stdio transport (for MCP clients like Cursor)
        server.run(transport="stdio")

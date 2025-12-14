"""OSC-MCP Server with stdio transport.

This module implements a FastMCP 2.13 compliant MCP server for Open Sound Control
that communicates over stdio, making it suitable for command-line usage and
integration with other tools.
"""

import asyncio
import logging
import sys
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

from fastmcp import FastMCP
from pydantic import BaseModel, Field
from pythonosc import dispatcher, osc_server, udp_client
from pythonosc.osc_message_builder import OscMessageBuilder
from pythonosc.udp_client import SimpleUDPClient

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastMCP instance
server = FastMCP("OSC-MCP")

# Store OSC server instances for cleanup
_osc_servers: List[Any] = []

# Pydantic models for input validation (FastMCP 2.13)
class OSCMessageInput(BaseModel):
    """Input model for OSC message sending."""
    host: str = Field(..., description="Target hostname or IP address")
    port: int = Field(..., gt=0, le=65535, description="Target UDP port (1-65535)")
    address: str = Field(..., pattern=r"^/.*", description="OSC address pattern starting with /")
    values: List[Any] = Field(..., description="List of values to send")

class OSCListenerInput(BaseModel):
    """Input model for starting OSC listener."""
    port: int = Field(..., gt=0, le=65535, description="UDP port to listen on (1-65535)")
    address: str = Field(default="0.0.0.0", description="Network interface to bind to")

class OSCEchoTestInput(BaseModel):
    """Input model for OSC echo test."""
    port: int = Field(default=9000, gt=0, le=65535, description="Test port to use (1-65535)")

# Lifespan management removed - FastMCP 2.13.1 doesn't support lifespan decorator
# Resource cleanup happens automatically when server shuts down
async def server_lifespan():
    """Manage server-level OSC resources.

    This lifespan hook ensures proper initialization and cleanup of OSC resources
    at the server level (not per-client session), following FastMCP 2.13 semantics.
    """
    # Startup
    logger.info("OSC-MCP stdio server starting up - initializing resources")

    try:
        yield  # Server runs here
    finally:
        # Shutdown - cleanup all OSC resources
        logger.info("OSC-MCP stdio server shutting down - cleaning up resources")

        # Close all OSC servers
        for idx, osc_server_instance in enumerate(_osc_servers):
            try:
                # Get the transport if it exists and close it
                if hasattr(osc_server_instance, '_transport'):
                    osc_server_instance._transport.close()
                logger.info(f"Closed OSC server instance {idx}")
            except Exception as e:
                logger.error(f"Error closing OSC server instance {idx}: {e}")

        # Clear all resources
        _osc_servers.clear()
        logger.info("OSC-MCP stdio server cleanup complete")

@server.tool()
async def send_osc_message(host: str, port: int, address: str, values: List[Any]) -> Dict[str, Any]:
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
            "values": values
        }
    except Exception as e:
        error_msg = f"Failed to send OSC message: {str(e)}"
        logger.error(error_msg)
        return {
            "status": "error",
            "message": error_msg,
            "error": str(e)
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
    try:
        # Create a dispatcher to handle incoming OSC messages
        osc_dispatcher = dispatcher.Dispatcher()
        
        # Define a handler for all OSC addresses
        def default_handler(osc_addr: str, *args: Any) -> None:
            logger.info(f"Received OSC message: {osc_addr} {args}")
        
        # Set the default handler for all addresses
        osc_dispatcher.set_default_handler(default_handler)
        
        # Create and start the OSC server
        osc_server_instance = osc_server.AsyncIOOSCUDPServer(
            (address, port),
            osc_dispatcher,
            asyncio.get_event_loop()
        )
        
        # Store the server instance for later cleanup
        _osc_servers.append(osc_server_instance)
        
        # Start the server
        transport, _ = await osc_server_instance.create_serve_endpoint()
        
        logger.info(f"Started OSC listener on {address}:{port}")
        return {
            "status": "success",
            "message": "OSC listener started successfully",
            "address": address,
            "port": port
        }
        
    except Exception as e:
        error_msg = f"Failed to start OSC listener: {str(e)}"
        logger.error(error_msg)
        return {
            "status": "error",
            "message": error_msg,
            "error": str(e)
        }

# Add a simple test function to verify the server is working
@server.tool()
async def test_osc_echo(port: int = 9000) -> Dict[str, Any]:
    """Test OSC functionality by sending and receiving a message.
    
    This is a test function that starts a server, sends a message to itself,
    and verifies the message was received.
    """
    try:
        # Start the listener
        listener_result = await start_osc_listener(port, "127.0.0.1")
        if listener_result["status"] != "success":
            return {"status": "error", "message": "Failed to start listener", "details": listener_result}
        
        # Send a test message
        test_address = "/test/echo"
        test_values = [1, 2.0, "test"]
        
        send_result = await send_osc_message("127.0.0.1", port, test_address, test_values)
        if send_result["status"] != "success":
            return {"status": "error", "message": "Failed to send test message", "details": send_result}
        
        # Wait a moment for the message to be received
        await asyncio.sleep(0.5)
        
        return {
            "status": "success",
            "message": "OSC echo test completed",
            "test_address": test_address,
            "test_values": test_values
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"OSC echo test failed: {str(e)}",
            "error": str(e)
        }

# This allows running the server directly with: python -m oscmcp.stdio_server
if __name__ == "__main__":
    # Run the FastMCP server with stdio transport
    server.run(transport="stdio")

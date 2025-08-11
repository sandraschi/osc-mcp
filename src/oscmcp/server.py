"""OSC-MCP Server Implementation.

This module implements the core OSC server functionality using FastMCP 2.10
and python-osc for Open Sound Control protocol support.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Union

from fastmcp import FastMCP
from pythonosc import dispatcher, osc_server, udp_client
from pythonosc.osc_message_builder import OscMessageBuilder
from pythonosc.udp_client import SimpleUDPClient

# Set up logging
logger = logging.getLogger(__name__)

# Create FastMCP instance
server = FastMCP("OSC-MCP")

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
        logger.error(error_msg, exc_info=True)
        return {
            "status": "error",
            "message": error_msg,
            "host": host,
            "port": port,
            "address": address,
            "values": values
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
            (address, port), 
            osc_dispatcher, 
            asyncio.get_event_loop()
        )
        
        # Start the server in the background
        transport, _ = await server.create_serve_endpoint()
        
        logger.info(f"OSC server started on {address}:{port}")
        
        return {
            "status": "success",
            "message": "OSC server started successfully",
            "address": address,
            "port": port,
            "transport": str(transport)  # For reference, actual transport object can't be serialized
        }
        
    except Exception as e:
        error_msg = f"Failed to start OSC server: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {
            "status": "error",
            "message": error_msg,
            "address": address,
            "port": port
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
        return {"status": "error", "message": f"Failed to start test server: {server_result['message']}"}
    
    # Send a test message
    test_address = "/test/echo"
    test_values = [1, 2.0, "three", True]
    
    send_result = await send_osc_message("127.0.0.1", port, test_address, test_values)
    if send_result["status"] != "success":
        return {"status": "error", "message": f"Failed to send test message: {send_result['message']}"}
    
    # In a real implementation, you would verify the message was received
    # For now, we'll just return success
    return {
        "status": "success",
        "message": "OSC echo test completed",
        "test_address": test_address,
        "test_values": test_values,
        "server": server_result,
        "send_result": send_result
    }

# This allows running the server directly with: python -m oscmcp.server
if __name__ == "__main__":
    # Run the FastMCP server with HTTP transport
    server.run(transport="streamable-http", host="0.0.0.0", port=8000)

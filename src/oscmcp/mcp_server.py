"""OSC-MCP Server with stdio transport for MCP clients.

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
    
    Args:
        host: Target hostname or IP address
        port: Target UDP port
        address: OSC address pattern (e.g., "/volume")
        values: List of values to send (will be converted to appropriate OSC types)
        
    Returns:
        Dictionary with status and sent message details
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
    """Start an OSC server to receive messages.
    
    Args:
        port: UDP port to listen on
        address: Network interface to bind to (default: all interfaces)
        
    Returns:
        Dictionary with server status
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
    """Stop a running OSC server.
    
    Args:
        port: Port of the server to stop
        
    Returns:
        Dictionary with status of the operation
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

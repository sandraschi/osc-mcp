"""Test client for the FastMCP 2.10 server with stdio transport.

This script demonstrates how to communicate with the FastMCP server using the
MCP protocol over stdio.
"""

import asyncio
import json
import logging
import sys
from typing import Any, Dict, Optional

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MCPClient:
    """Simple MCP client that communicates over stdio."""
    
    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Initialize the MCP client with stdio streams."""
        self.reader = reader
        self.writer = writer
        self.request_id = 0
    
    async def list_tools(self) -> Dict[str, Any]:
        """List all available tools."""
        return await self._call_method("tools/list", {})
    
    async def call_tool(self, name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool by name with the given parameters."""
        return await self._call_method("tools/call", {"name": name, "arguments": params})
    
    async def _call_method(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Call an MCP method and return the response."""
        self.request_id += 1
        request = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": self.request_id
        }
        
        # Send the request
        request_str = json.dumps(request) + "\n"
        logger.debug(f"Sending request: {request_str.strip()}")
        self.writer.write(request_str.encode('utf-8'))
        await self.writer.drain()
        
        # Read the response
        response_line = await self.reader.readline()
        if not response_line:
            raise ConnectionError("Connection closed by server")
            
        response = json.loads(response_line.decode('utf-8').strip())
        logger.debug(f"Received response: {response}")
        
        if "error" in response:
            error = response["error"]
            error_msg = f"RPC error: {error.get('message', 'Unknown error')} (code: {error.get('code', -1)})"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
            
        return response.get("result", {})

async def test_osc_functionality():
    """Test OSC functionality using the MCP server with stdio transport."""
    logger.info("Starting OSC-MCP stdio client test...")
    
    # Start the server as a subprocess
    server_process = await asyncio.create_subprocess_exec(
        sys.executable, "-m", "oscmcp.mcp_server",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    
    # Create MCP client
    client = MCPClient(server_process.stdout, server_process.stdin)
    
    try:
        # Test 1: List available tools
        logger.info("\n--- Listing available tools ---")
        tools = await client.list_tools()
        logger.info(f"Available tools: {json.dumps(tools, indent=2)}")
        
        # Test 2: Start OSC server
        logger.info("\n--- Starting OSC listener on port 9000 ---")
        listener_result = await client.call_tool("start_osc_server", {"port": 9000, "address": "127.0.0.1"})
        logger.info(f"OSC listener started: {json.dumps(listener_result, indent=2)}")
        
        # Test 3: Send OSC message
        logger.info("\n--- Sending test OSC message ---")
        send_result = await client.call_tool("send_osc", {
            "host": "127.0.0.1",
            "port": 9000,
            "address": "/test/message",
            "values": [1, 2.0, "test"]
        })
        logger.info(f"OSC message sent: {json.dumps(send_result, indent=2)}")
        
        # Wait a bit to see the message being received
        await asyncio.sleep(1)
        
        # Test 4: Stop OSC server
        logger.info("\n--- Stopping OSC listener ---")
        stop_result = await client.call_tool("stop_osc_server", {"port": 9000})
        logger.info(f"OSC listener stopped: {json.dumps(stop_result, indent=2)}")
        
        logger.info("\n--- All tests completed successfully! ---")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
    finally:
        # Clean up
        logger.info("Stopping server...")
        server_process.terminate()
        await server_process.wait()
        
        # Log any remaining output
        stdout, stderr = await server_process.communicate()
        if stdout:
            logger.info(f"Server stdout:\n{stdout.decode('utf-8')}")
        if stderr:
            logger.error(f"Server stderr:\n{stderr.decode('utf-8')}")

if __name__ == "__main__":
    asyncio.run(test_osc_functionality())

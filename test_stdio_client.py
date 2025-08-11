"""Test client for the OSC-MCP server with stdio transport.

This script demonstrates how to communicate with the FastMCP server
using stdio transport by sending JSON-RPC messages directly to the server's
stdin and reading responses from its stdout.
"""

import asyncio
import json
import logging
import sys
from typing import Any, Dict, Optional

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

class MCPClient:
    """Simple MCP client that communicates over stdio."""
    
    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Initialize the MCP client with stdio streams."""
        self.reader = reader
        self.writer = writer
        self.request_id = 0
    
    async def read_until_json(self) -> Dict[str, Any]:
        """Read from the stream until we get a valid JSON object."""
        buffer = b""
        while True:
            chunk = await self.reader.read(4096)
            if not chunk:
                raise ConnectionError("Connection closed by server")
                
            buffer += chunk
            
            # Try to find JSON in the buffer
            lines = buffer.split(b'\n')
            for line in lines[:-1]:  # Process all complete lines
                line = line.strip()
                if not line:
                    continue
                    
                # Skip FastMCP banner and other non-JSON output
                if line.startswith(b'|') or not (line.startswith(b'{') or line.startswith(b'[')):
                    logger.debug(f"Skipping non-JSON line: {line.decode('utf-8', errors='replace')}")
                    continue
                    
                try:
                    response = json.loads(line.decode('utf-8'))
                    logger.debug(f"Received response: {response}")
                    return response
                except json.JSONDecodeError:
                    logger.debug(f"Failed to parse JSON from line: {line.decode('utf-8', errors='replace')}")
                    continue
            
            # Keep the last incomplete line in the buffer
            buffer = lines[-1]
    
    async def call_method(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Call an MCP method and return the response."""
        self.request_id += 1
        request = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {},
            "id": self.request_id
        }
        
        # Send the request
        request_str = json.dumps(request) + "\n"
        logger.debug(f"Sending request: {request_str.strip()}")
        self.writer.write(request_str.encode('utf-8'))
        await self.writer.drain()
        
        # Read and parse the response
        response = await self.read_until_json()
        
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
        sys.executable, "-m", "oscmcp.stdio_server",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    
    # Create MCP client
    client = MCPClient(server_process.stdout, server_process.stdin)
    
    try:
        # Test 1: List available tools
        logger.info("\n--- Listing available tools ---")
        tools = await client.call_method("mcp.list_tools")
        logger.info(f"Available tools: {json.dumps(tools, indent=2)}")
        
        # Test 2: Start OSC listener
        logger.info("\n--- Starting OSC listener on port 9000 ---")
        listener_result = await client.call_method("start_osc_listener", {"port": 9000, "address": "127.0.0.1"})
        logger.info(f"OSC listener started: {json.dumps(listener_result, indent=2)}")
        
        # Test 3: Send OSC message
        logger.info("\n--- Sending test OSC message ---")
        send_result = await client.call_method("send_osc_message", {
            "host": "127.0.0.1",
            "port": 9000,
            "address": "/test/message",
            "values": [1, 2.0, "test"]
        })
        logger.info(f"OSC message sent: {json.dumps(send_result, indent=2)}")
        
        # Test 4: Run the test_osc_echo function
        logger.info("\n--- Running OSC echo test ---")
        echo_result = await client.call_method("test_osc_echo", {"port": 9001})
        logger.info(f"OSC echo test result: {json.dumps(echo_result, indent=2)}")
        
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

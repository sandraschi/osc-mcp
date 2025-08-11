"""Test suite for the OSC-MCP stdio transport server.

This module contains integration tests for the stdio-based MCP server,
verifying that it correctly handles OSC message translation over stdio.
"""

import asyncio
import json
import logging
import os
import signal
import subprocess
import sys
import time
import platform
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import pytest
from pythonosc import dispatcher, osc_server, udp_client

# Skip these tests on Windows for now due to asyncio subprocess issues
pytestmark = pytest.mark.skipif(
    platform.system() == 'Windows',
    reason="Skipping stdio server tests on Windows due to asyncio subprocess issues"
)

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Test configuration
TEST_OSC_PORT = 9001
TEST_HOST = "127.0.0.1"


class MCPClient:
    """Client for communicating with the MCP server over stdio."""
    
    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Initialize the MCP client with stdio streams."""
        self.reader = reader
        self.writer = writer
        self.request_id = 0
    
    async def send_request(self, method: str, params: Optional[Dict] = None) -> Dict:
        """Send a JSON-RPC request to the server."""
        self.request_id += 1
        request = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": method,
            "params": params or {}
        }
        
        # Send the request
        request_str = json.dumps(request) + "\n"
        self.writer.write(request_str.encode('utf-8'))
        await self.writer.drain()
        
        # Read the response
        response = await self.reader.readline()
        if not response:
            raise ConnectionError("Connection closed by server")
            
        return json.loads(response.decode('utf-8'))
    
    async def list_tools(self) -> Dict:
        """List available tools."""
        return await self.send_request("tools/list")
    
    async def call_tool(self, tool_name: str, **kwargs) -> Dict:
        """Call a tool by name with the given parameters."""
        return await self.send_request("tools/call", {
            "name": tool_name,
            "arguments": kwargs
        })
    
    async def close(self) -> None:
        """Close the client connection."""
        self.writer.close()
        await self.writer.wait_closed()


class OSCServer:
    """Simple OSC server for testing OSC message reception."""
    
    def __init__(self, host: str, port: int):
        """Initialize the OSC server."""
        self.host = host
        self.port = port
        self.dispatcher = dispatcher.Dispatcher()
        self.received_messages = []
        self.server = None
        self.loop = None
    
    def message_handler(self, address: str, *args) -> None:
        """Handle incoming OSC messages."""
        logger.info(f"OSC message received: {address} {args}")
        self.received_messages.append((address, args))
    
    async def start(self) -> None:
        """Start the OSC server in a background thread."""
        self.loop = asyncio.get_running_loop()
        
        # Start the OSC server in a separate thread
        def start_server():
            self.server = osc_server.ThreadingOSCUDPServer(
                (self.host, self.port),
                dispatcher=self.dispatcher
            )
            self.server.serve_forever()
        
        # Start the server in a background thread
        import threading
        self.thread = threading.Thread(target=start_server, daemon=True)
        self.thread.start()
        
        # Give the server time to start
        await asyncio.sleep(0.5)
    
    async def stop(self) -> None:
        """Stop the OSC server."""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            self.server = None
    
    def clear_messages(self) -> None:
        """Clear the list of received messages."""
        self.received_messages = []
    
    def wait_for_message(self, address: str, timeout: float = 2.0) -> Tuple[str, tuple]:
        """Wait for a message with the given address.
        
        Args:
            address: The OSC address to wait for
            timeout: Maximum time to wait in seconds
            
        Returns:
            Tuple of (address, args) for the received message
            
        Raises:
            TimeoutError: If no message is received within the timeout
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            for msg_address, args in self.received_messages:
                if msg_address == address:
                    return msg_address, args
            time.sleep(0.01)
        
        raise TimeoutError(f"Timed out waiting for OSC message: {address}")


class MCPProcess:
    """Helper class to manage the MCP server process."""
    
    def __init__(self):
        self.process = None
    
    def start(self):
        """Start the MCP server process."""
        self.process = subprocess.Popen(
            [sys.executable, "-m", "oscmcp.mcp_server"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        # Give the server time to start
        time.sleep(2)
    
    def stop(self):
        """Stop the MCP server process."""
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
            self.process = None
    
    def __enter__(self):
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()


@pytest.fixture
def mcp_server():
    """Fixture that starts and stops the MCP server for testing."""
    with MCPProcess() as server:
        yield server


@pytest.fixture
async def osc_server_fixture():
    """Fixture that provides an OSC server for testing."""
    server = OSCServer(TEST_HOST, TEST_OSC_PORT)
    server.dispatcher.set_default_handler(server.message_handler)
    
    await server.start()
    yield server
    await server.stop()


@pytest.fixture
def mcp_client(mcp_server):
    """Fixture that provides an MCP client connected to the test server."""
    # For now, we'll use a simple synchronous client for testing
    class SyncMCPClient:
        """Synchronous MCP client for testing."""
        
        def __init__(self, process):
            self.process = process
            self.request_id = 0
        
        def send_request(self, method: str, params: Optional[Dict] = None) -> Dict:
            """Send a JSON-RPC request to the server and return the response."""
            self.request_id += 1
            request = {
                "jsonrpc": "2.0",
                "id": self.request_id,
                "method": method,
                "params": params or {}
            }
            
            # Send the request
            request_str = json.dumps(request) + "\n"
            self.process.process.stdin.write(request_str)
            self.process.process.stdin.flush()
            
            # Read the response
            response_line = self.process.process.stdout.readline()
            if not response_line:
                raise ConnectionError("Connection closed by server")
                
            return json.loads(response_line.strip())
        
        def call_tool(self, name: str, **kwargs) -> Dict:
            """Call a tool by name with the given parameters."""
            return self.send_request("tools/call", {
                "name": name,
                "arguments": kwargs
            })
    
    # Create and return the client
    return SyncMCPClient(mcp_server)


def test_osc_message_echo(mcp_client, osc_server_fixture):
    """Test that the MCP server can echo OSC messages."""
    # Register a test OSC address
    osc_server_fixture.dispatcher.map("/test/echo", osc_server_fixture.message_handler)
    
    # Send an OSC message via the MCP server
    response = mcp_client.call_tool(
        "send_osc_message",
        address="/test/echo",
        host=TEST_HOST,
        port=TEST_OSC_PORT,
        args=[1.23, "test"]
    )
    
    # Check that the message was sent successfully
    assert "result" in response, f"Unexpected response: {response}"
    
    # Wait for the OSC message to be received
    address, args = osc_server_fixture.wait_for_message("/test/echo")
    
    # Check that the message was received correctly
    assert address == "/test/echo"
    assert len(args) == 2
    assert abs(args[0] - 1.23) < 0.001  # Handle floating point imprecision
    assert args[1] == "test"


def test_osc_message_listener(mcp_client, osc_server_fixture):
    """Test that the MCP server can receive OSC messages."""
    # Start an OSC listener on the MCP server
    response = mcp_client.call_tool(
        "start_osc_listener",
        host=TEST_HOST,
        port=TEST_OSC_PORT + 1  # Use a different port to avoid conflicts
    )
    
    assert "result" in response, f"Failed to start OSC listener: {response}"
    
    # Send an OSC message directly to the MCP server's OSC listener
    client = udp_client.SimpleUDPClient(TEST_HOST, TEST_OSC_PORT + 1)
    client.send_message("/test/listener", [42, "received"])
    
    # Give the server time to process the message
    time.sleep(0.5)
    
    # Check that the MCP server received the message
    response = mcp_client.call_tool("get_last_osc_message")
    
    assert "result" in response, f"Unexpected response: {response}"
    result = response["result"]
    
    assert result["address"] == "/test/listener"
    assert result["args"] == [42, "received"]


def test_osc_message_roundtrip(mcp_client, osc_server_fixture):
    """Test a complete OSC message roundtrip through the MCP server."""
    # Start an OSC listener on the MCP server
    response = mcp_client.call_tool(
        "start_osc_listener",
        host=TEST_HOST,
        port=TEST_OSC_PORT + 2  # Use a different port to avoid conflicts
    )
    
    assert "result" in response, f"Failed to start OSC listener: {response}"
    
    # Register a callback to forward received OSC messages to our test OSC server
    response = mcp_client.call_tool(
        "on_osc_message",
        callback="tools/call",
        callback_args={
            "name": "send_osc_message",
            "arguments": {
                "host": TEST_HOST,
                "port": TEST_OSC_PORT,
                "address": "/forwarded",
                "args": ["$message"]
            }
        }
    )
    
    assert "result" in response, f"Failed to register callback: {response}"
    
    # Send an OSC message to the MCP server's listener
    client = udp_client.SimpleUDPClient(TEST_HOST, TEST_OSC_PORT + 2)
    client.send_message("/test/roundtrip", [3.14, "pi"])
    
    # Wait for the forwarded message to arrive at our test OSC server
    try:
        address, args = osc_server_fixture.wait_for_message("/forwarded")
        
        # Check that the message was forwarded correctly
        assert address == "/forwarded"
        assert len(args) == 1, f"Expected 1 argument, got {args}"
        
        # The argument should be a dictionary with the original message
        message = args[0]
        assert isinstance(message, dict), f"Expected dict, got {type(message)}"
        assert message["address"] == "/test/roundtrip"
        assert message["args"] == [3.14, "pi"]
    except TimeoutError as e:
        pytest.fail(f"Timed out waiting for OSC message: {e}")


if __name__ == "__main__":
    # Run the tests
    import sys
    sys.exit(pytest.main(sys.argv[1:]))

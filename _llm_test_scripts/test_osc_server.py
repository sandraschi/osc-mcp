"""Test script for the OSC-MCP server.

This script demonstrates how to use the OSC-MCP server by:
1. Starting the server
2. Using JSON-RPC over HTTP to interact with the tools
"""

import asyncio
import logging
import socket
import subprocess
import sys

import httpx

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


async def is_port_in_use(port: int, host: str = "localhost") -> bool:
    """Check if a port is in use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.settimeout(1)
            s.connect((host, port))
            return True
        except (socket.timeout, ConnectionRefusedError):
            return False
        except Exception as e:
            logger.warning(f"Error checking port {port}: {e}")
            return False


async def make_rpc_request(method: str, params: dict = None) -> dict:
    """Make a JSON-RPC request to the FastMCP server."""
    url = "http://localhost:8000/mcp/rpc"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",  # For non-streaming responses
    }

    payload = {"jsonrpc": "2.0", "method": method, "params": params or {}, "id": 1}

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers, timeout=10.0)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logger.error(f"RPC request failed: {e}")
        return {"error": str(e)}


async def test_osc_server():
    """Test the OSC server functionality using HTTP requests."""
    logger.info("Starting OSC-MCP server test...")

    # Check if port 8000 is already in use
    if await is_port_in_use(8000):
        logger.warning(
            "Port 8000 is already in use. Please close any other servers using this port."
        )
        return

    # Start the server in a separate process with full output capture
    logger.info("Starting server process...")
    server_process = None

    server_process = None
    try:
        server_process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "oscmcp.server:server.app",
                "--host",
                "0.0.0.0",
                "--port",
                "8000",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        # Give the server time to start
        max_attempts = 10
        attempt = 0
        server_started = False

        logger.info("Waiting for server to start...")
        while attempt < max_attempts and not server_started:
            if await is_port_in_use(8000):
                server_started = True
                logger.info("Server is running on port 8000")
                break
            logger.info(f"Waiting for server to start (attempt {attempt + 1}/{max_attempts})...")
            await asyncio.sleep(1)
            attempt += 1

        if not server_started:
            logger.error("Server failed to start. Check the server logs for errors.")
            return

        # Create a client with a longer timeout
        timeout = httpx.Timeout(10.0, connect=30.0)
        async with httpx.AsyncClient(
            base_url="http://localhost:8000", timeout=timeout, follow_redirects=True
        ) as client:
            try:
                # Test server health first
                logger.info("Checking server health...")
                logger.info("\n--- Test complete ---")

            except Exception as e:
                logger.error(f"Test failed: {e}", exc_info=True)

                # Log server output if available
                if server_process.stderr:
                    server_process.stderr.seek(0)
                    stderr_output = server_process.stderr.read()
                    if stderr_output:
                        logger.error("Server stderr output:" + stderr_output)

                if server_process.stdout:
                    server_process.stdout.seek(0)
                    stdout_output = server_process.stdout.read()
                    if stdout_output:
                        logger.info("Server stdout output:" + stdout_output)

    except Exception as e:
        logger.error(f"Server process failed: {e}")
        return

    # Clean up (outside the async with block)
    logger.info("Shutting down server...")
    try:
        server_process.terminate()
        server_process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        logger.warning("Server did not terminate gracefully, forcing...")
        server_process.kill()
    logger.info("Server stopped")


if __name__ == "__main__":
    asyncio.run(test_osc_server())

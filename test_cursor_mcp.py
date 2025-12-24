#!/usr/bin/env python3
"""
Test script to verify OSC-MCP server works with Cursor MCP integration
"""
import sys
import json
import subprocess
import time

def test_mcp_server():
    """Test that the OSC-MCP server can start and respond to MCP protocol"""
    try:
        # Start the server
        print("Starting OSC-MCP server...")
        proc = subprocess.Popen([
            sys.executable, "-m", "oscmcp.mcp_server"
        ], cwd="D:\\Dev\\repos\\osc-mcp",
           stdin=subprocess.PIPE,
           stdout=subprocess.PIPE,
           stderr=subprocess.PIPE,
           text=True)

        # Give it a moment to start
        time.sleep(2)

        # Send initialize request
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "cursor-test", "version": "1.0.0"}
            }
        }

        print("Sending initialize request...")
        proc.stdin.write(json.dumps(init_request) + "\n")
        proc.stdin.flush()

        # Read response
        response = proc.stdout.readline()
        if response:
            print(f"Server responded: {response.strip()}")
            return True
        else:
            print("No response from server")
            return False

    except Exception as e:
        print(f"Error testing server: {e}")
        return False
    finally:
        if 'proc' in locals():
            proc.terminate()
            proc.wait()

if __name__ == "__main__":
    success = test_mcp_server()
    print(f"Test {'PASSED' if success else 'FAILED'}")

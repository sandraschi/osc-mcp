"""FastMCP 2.14.3 server entry point for OSC-MCP.

This is the MCPB-compliant server wrapper that launches the OSC-MCP server
with conversational tools and LLM sampling capabilities.
"""

import sys
from pathlib import Path

# Add parent directory to path to import main server
parent_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(parent_dir))

# Import and run main server
try:
    from oscmcp.server import server

    # Use FastMCP 2.14.3 server.run() method
    if __name__ == "__main__":
        server.run()
except ImportError as e:
    print(f"Failed to import OSC-MCP server: {e}", file=sys.stderr)
    sys.exit(1)

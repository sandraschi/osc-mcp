'''MCP server entry point for OSCMCP.

This is the MCPB-compliant server wrapper that launches the OSCMCP server.
'''

import sys
from pathlib import Path

# Add parent directory to path to import main server
parent_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(parent_dir))

# Import and run main server
try:
    from server import main
except ImportError:
    # Fallback if server.py not at root
    from oscmcp.server import main

if __name__ == '__main__':
    main()


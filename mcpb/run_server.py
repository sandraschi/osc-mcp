"""PyInstaller / MCPB entry point with dual transport."""
import _strptime  # noqa: F401
import os
import sys

# Insert src to PYTHONPATH
sys.path.insert(0, "src")

import _strptime  # noqa: F401
from oscmcp.server import server

# Check if port or http transport is requested
port = os.environ.get("MCP_PORT") or os.environ.get("PORT")
if len(sys.argv) > 1 and sys.argv[1].isdigit():
    port = sys.argv[1]

if port:
    # Run uvicorn on the main FastAPI application (with CORS and REST endpoints)
    import uvicorn
    from oscmcp.api.main import app
    uvicorn.run(app, host="127.0.0.1", port=int(port))
else:
    # Run in stdio mode for Claude Desktop / MCPB stdio
    # CRITICAL: binary mode for stdin/stdout on Windows
    if os.name == "nt":
        try:
            import msvcrt
            msvcrt.setmode(sys.stdin.fileno(), os.O_BINARY)
            msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)
        except (OSError, AttributeError):
            pass
    server.run(transport="stdio")


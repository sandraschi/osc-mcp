"""PyInstaller / MCPB entry point with dual transport."""

import _datetime  # noqa: F401
import _strptime  # noqa: F401
import os
import sys

if getattr(sys, "frozen", False):
    # PyInstaller adds _MEIPASS to sys.path automatically, but be explicit -
    # the bundled package lives at _MEIPASS/oscmcp (see the .spec's datas).
    sys.path.insert(0, getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__))))
    if sys.stderr is None:
        # console=False in the .spec leaves stderr as None; uvicorn's logging
        # setup calls sys.stderr.isatty() unconditionally and crashes with
        # AttributeError: 'NoneType' object has no attribute 'isatty'.
        class _NullStderr:
            def isatty(self):
                return False

            def write(self, *_args, **_kwargs):
                return 0

            def flush(self):
                pass

        sys.stderr = _NullStderr()
else:
    sys.path.insert(0, "src")

import mcp.types  # noqa: F401 - freeze the mcp bootstrap before fastmcp touches it

from oscmcp.server import server

# Check if port or http transport is requested
port = os.environ.get("OSC_MCP_PORT") or os.environ.get("MCP_PORT") or os.environ.get("PORT")
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

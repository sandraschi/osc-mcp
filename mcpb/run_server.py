"""PyInstaller entry point."""
import _strptime  # noqa: F401
import sys
sys.path.insert(0, "src")
import _strptime  # noqa: F401
import uvicorn
from oscmcp.server import app
uvicorn.run(app, host="127.0.0.1", port=int(sys.argv[1]) if len(sys.argv) > 1 else 10767)


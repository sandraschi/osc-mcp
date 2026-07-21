"""Main entry point for oscmcp package when run as module."""

from oscmcp.server import server
from oscmcp.transport import run_server

if __name__ == "__main__":
    run_server(server, server_name="osc-mcp")

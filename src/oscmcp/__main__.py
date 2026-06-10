"""Main entry point for oscmcp package when run as module."""

from oscmcp.transport import run_server
from oscmcp.server import server

if __name__ == "__main__":
    run_server(server, server_name="osc-mcp")

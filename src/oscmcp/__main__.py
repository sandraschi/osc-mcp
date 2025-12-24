"""Main entry point for oscmcp package when run as module."""

from oscmcp.server import server

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "http":
        server.run(transport="streamable-http", host="0.0.0.0", port=8000)
    else:
        server.run(transport="stdio")

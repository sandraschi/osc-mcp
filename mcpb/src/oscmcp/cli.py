"""CLI entry point for oscmcp."""

import sys

from oscmcp.server import server


def main():
    """Main entry point for the oscmcp CLI."""
    if len(sys.argv) > 1 and sys.argv[1] == "http":
        # FastMCP 2.14.3+ with sampling and conversational features
        server.run(
            transport="streamable-http",
            host="0.0.0.0",
            port=8000,
        )
    else:
        # Default: stdio transport (for MCP clients like Cursor)
        server.run(transport="stdio")


if __name__ == "__main__":
    main()

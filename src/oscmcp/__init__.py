"""OSCMCP - Open Sound Control MCP Server.

This module provides a FastMCP 2.10 compliant MCP server for audio/visual automation
using the Open Sound Control (OSC) protocol.
"""

__version__ = "0.1.1"

import logging
from typing import Any

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class OSCMCPServer:
    """Main OSCMCP server class implementing FastMCP 2.10 protocol for OSC.

    This server provides tools for sending and receiving OSC messages,
    with integration for audio/visual automation workflows.
    """

    def __init__(self, config: dict[str, Any] | None = None):
        """Initialize the OSCMCP server with optional configuration.

        Args:
            config: Optional configuration dictionary with OSC settings
        """
        self.config = config or {}
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the OSC server resources."""
        if self._initialized:
            return

        logger.info("Initializing OSCMCP server...")
        # OSC server initialization will be added here
        self._initialized = True
        logger.info("OSCMCP server initialized successfully")

    async def shutdown(self) -> None:
        """Shutdown the OSC server and release resources."""
        if not self._initialized:
            return

        logger.info("Shutting down OSCMCP server...")
        # OSC server cleanup will be added here
        self._initialized = False
        logger.info("OSCMCP server shutdown complete")

    async def get_info(self) -> dict[str, Any]:
        """Get server information.

        Returns:
            Dictionary containing server information
        """
        return {
            "name": "OSCMCP",
            "version": __version__,
            "description": "Open Source Content Management Platform MCP Server",
            "capabilities": ["content_management", "user_management", "plugin_system"],
        }


# Create a default instance for convenience
server = OSCMCPServer()

__all__ = ["OSCMCPServer", "server"]

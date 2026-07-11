"""OSC module for the OSC-MCP bridge.

This package provides functionality for sending and receiving OSC messages,
including both client and server implementations.
"""

from .client import OSCClient
from .server import OSCServer

__all__ = ["OSCClient", "OSCServer"]

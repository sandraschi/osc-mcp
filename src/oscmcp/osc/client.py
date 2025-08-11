"""OSC client implementation for sending OSC messages.

This module provides functionality to send OSC messages to OSC servers.
"""

import logging
from typing import Any, List, Optional
from pythonosc import udp_client

logger = logging.getLogger(__name__)

class OSCClient:
    """Client for sending OSC messages to an OSC server."""
    
    def __init__(self, host: str = "127.0.0.1", port: int = 9000):
        """Initialize the OSC client.
        
        Args:
            host: The hostname or IP address of the OSC server.
            port: The port number of the OSC server.
        """
        self.host = host
        self.port = port
        self._client = None
    
    def connect(self) -> None:
        """Establish connection to the OSC server."""
        self._client = udp_client.SimpleUDPClient(self.host, self.port)
        logger.info(f"Connected to OSC server at {self.host}:{self.port}")
    
    def send(self, address: str, *args: Any) -> None:
        """Send an OSC message.
        
        Args:
            address: The OSC address pattern (e.g., "/volume").
            *args: The arguments to send with the message.
        """
        if self._client is None:
            self.connect()
        
        logger.debug(f"Sending OSC message to {address}: {args}")
        self._client.send_message(address, args)
    
    def close(self) -> None:
        """Close the OSC client connection."""
        # No explicit close needed for SimpleUDPClient
        self._client = None

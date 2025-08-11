"""OSC server implementation for receiving OSC messages.

This module provides functionality to receive and handle OSC messages.
"""

import asyncio
import logging
from typing import Any, Callable, Dict, Optional
from pythonosc import dispatcher
from pythonosc.osc_server import AsyncIOOSCUDPServer

logger = logging.getLogger(__name__)

class OSCServer:
    """Server for receiving and handling OSC messages."""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 9000):
        """Initialize the OSC server.
        
        Args:
            host: The hostname or IP address to bind to.
            port: The port number to listen on.
        """
        self.host = host
        self.port = port
        self.dispatcher = dispatcher.Dispatcher()
        self.server: Optional[AsyncIOOSCUDPServer] = None
        self._transport = None
        self._callbacks: Dict[str, Callable] = {}
    
    def add_handler(self, address: str, callback: Callable) -> None:
        """Add a handler for a specific OSC address.
        
        Args:
            address: The OSC address pattern to handle.
            callback: The function to call when a message is received at the address.
        """
        self._callbacks[address] = callback
        self.dispatcher.map(address, self._handle_osc_message, address)
    
    def _handle_osc_message(self, address: str, *args: Any) -> None:
        """Handle an incoming OSC message.
        
        Args:
            address: The OSC address pattern of the message.
            *args: The message arguments.
        """
        logger.debug(f"Received OSC message at {address}: {args}")
        if address in self._callbacks:
            try:
                self._callbacks[address](address, *args)
            except Exception as e:
                logger.error(f"Error in OSC handler for {address}: {e}")
    
    async def start(self) -> None:
        """Start the OSC server."""
        loop = asyncio.get_running_loop()
        self.server = AsyncIOOSCUDPServer(
            (self.host, self.port), 
            self.dispatcher, 
            loop
        )
        
        transport, _ = await self.server.create_serve_endpoint()
        self._transport = transport
        logger.info(f"OSC server started on {self.host}:{self.port}")
    
    async def stop(self) -> None:
        """Stop the OSC server."""
        if self._transport:
            self._transport.close()
            self._transport = None
            logger.info("OSC server stopped")

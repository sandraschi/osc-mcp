"""OSC server implementation for receiving OSC messages.

This module provides functionality to receive and handle OSC messages.
"""

import asyncio
import logging
import time
from typing import Any, Callable, Dict, List, Optional, Tuple
from pythonosc import dispatcher
from pythonosc.osc_server import AsyncIOOSCUDPServer

logger = logging.getLogger(__name__)

class OSCMessage:
    """Represents a received OSC message."""
    def __init__(self, address: str, args: tuple, timestamp: float):
        self.address = address
        self.args = args
        self.timestamp = timestamp

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "address": self.address,
            "args": list(self.args),
            "timestamp": self.timestamp,
            "age_seconds": time.time() - self.timestamp
        }

class OSCServer:
    """Server for receiving and handling OSC messages."""

    def __init__(self, host: str = "0.0.0.0", port: int = 9000, max_buffer_size: int = 1000):
        """Initialize the OSC server.

        Args:
            host: The hostname or IP address to bind to.
            port: The port number to listen on.
            max_buffer_size: Maximum number of messages to buffer.
        """
        self.host = host
        self.port = port
        self.dispatcher = dispatcher.Dispatcher()
        self.server: Optional[AsyncIOOSCUDPServer] = None
        self._transport = None
        self._callbacks: Dict[str, Callable] = {}
        self._message_buffer: List[OSCMessage] = []
        self._max_buffer_size = max_buffer_size
    
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
        # Create message object with timestamp
        message = OSCMessage(address, args, time.time())

        # Add to buffer
        self._message_buffer.append(message)

        # Maintain buffer size limit (remove oldest messages)
        if len(self._message_buffer) > self._max_buffer_size:
            self._message_buffer.pop(0)

        logger.debug(f"Received OSC message at {address}: {args}")

        # Call registered callbacks
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

    def get_received_messages(self, address_pattern: Optional[str] = None,
                            max_age_seconds: Optional[float] = None,
                            limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get received OSC messages from the buffer.

        Args:
            address_pattern: Filter by OSC address pattern (substring match)
            max_age_seconds: Only return messages newer than this age
            limit: Maximum number of messages to return

        Returns:
            List of message dictionaries with address, args, timestamp, age_seconds
        """
        current_time = time.time()
        messages = []

        # Iterate through buffer in reverse (newest first)
        for message in reversed(self._message_buffer):
            # Apply filters
            if address_pattern and address_pattern not in message.address:
                continue

            if max_age_seconds and (current_time - message.timestamp) > max_age_seconds:
                continue

            messages.append(message.to_dict())

            # Stop when we reach the limit
            if len(messages) >= limit:
                break

        return messages

    def get_latest_message(self, address_pattern: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get the most recent OSC message matching the pattern.

        Args:
            address_pattern: Filter by OSC address pattern (substring match)

        Returns:
            Latest message dictionary or None if no matching messages
        """
        messages = self.get_received_messages(address_pattern, limit=1)
        return messages[0] if messages else None

    def clear_message_buffer(self) -> int:
        """
        Clear all messages from the buffer.

        Returns:
            Number of messages that were cleared
        """
        cleared_count = len(self._message_buffer)
        self._message_buffer.clear()
        logger.info(f"Cleared {cleared_count} messages from OSC buffer")
        return cleared_count

    def get_buffer_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the message buffer.

        Returns:
            Dictionary with buffer statistics
        """
        if not self._message_buffer:
            return {
                "total_messages": 0,
                "oldest_message_age": None,
                "newest_message_age": None
            }

        current_time = time.time()
        oldest = min(msg.timestamp for msg in self._message_buffer)
        newest = max(msg.timestamp for msg in self._message_buffer)

        return {
            "total_messages": len(self._message_buffer),
            "max_buffer_size": self._max_buffer_size,
            "oldest_message_age": current_time - oldest,
            "newest_message_age": current_time - newest
        }

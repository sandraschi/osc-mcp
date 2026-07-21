"""OSC server implementation for receiving OSC messages over UDP and TCP."""

import asyncio
import logging
import time
from collections.abc import Callable
from typing import Any

from pythonosc import dispatcher
from pythonosc.osc_message import OscMessage
from pythonosc.osc_server import AsyncIOOSCUDPServer

logger = logging.getLogger(__name__)


class SLIPDecoder:
    """Stateful decoder for SLIP protocol (RFC 1055) streams."""

    def __init__(self):
        self._buffer = bytearray()
        self._escaped = False

    def feed(self, data: bytes) -> list[bytes]:
        """Feed bytes into the decoder and return completed packets."""
        packets = []
        for byte in data:
            if byte == 0xC0:
                if self._buffer:
                    packets.append(bytes(self._buffer))
                    self._buffer = bytearray()
                self._escaped = False
            elif byte == 0xDB:
                self._escaped = True
            elif self._escaped:
                if byte == 0xDC:
                    self._buffer.append(0xC0)
                elif byte == 0xDD:
                    self._buffer.append(0xDB)
                self._escaped = False
            else:
                self._buffer.append(byte)
        return packets


class OSCMessage:
    """Represents a received OSC message."""

    def __init__(self, address: str, args: tuple, timestamp: float):
        self.address = address
        self.args = args
        self.timestamp = timestamp

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "address": self.address,
            "args": list(self.args),
            "timestamp": self.timestamp,
            "age_seconds": time.time() - self.timestamp,
        }


class OSCServer:
    """Server for receiving and handling OSC messages."""

    def __init__(self, host: str = "0.0.0.0", port: int = 9000, max_buffer_size: int = 1000, protocol: str = "udp"):
        """Initialize the OSC server.

        Args:
            host: The hostname or IP address to bind to.
            port: The port number to listen on.
            max_buffer_size: Maximum number of messages to buffer.
            protocol: Protocol ('udp' or 'tcp').
        """
        self.host = host
        self.port = port
        self.protocol = protocol.lower()
        self.dispatcher = dispatcher.Dispatcher()
        self.server = None
        self._transport = None
        self._tcp_server: asyncio.Server | None = None
        self._tcp_tasks: list[asyncio.Task] = []
        self._callbacks: dict[str, Callable] = {}
        self._message_buffer: list[OSCMessage] = []
        self._max_buffer_size = max_buffer_size

    def add_handler(self, address: str, callback: Callable) -> None:
        """Add a handler for a specific OSC address."""
        self._callbacks[address] = callback
        self.dispatcher.map(address, self._handle_osc_message, address)

    def _handle_osc_message(self, address: str, *args: Any) -> None:
        """Handle an incoming OSC message."""
        message = OSCMessage(address, args, time.time())
        self._message_buffer.append(message)

        if len(self._message_buffer) > self._max_buffer_size:
            self._message_buffer.pop(0)

        logger.debug(f"Received {self.protocol.upper()} OSC message at {address}: {args}")

        if address in self._callbacks:
            try:
                self._callbacks[address](address, *args)
            except Exception as e:
                logger.error(f"Error in OSC handler for {address}: {e}")

    async def _handle_tcp_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        """Handle individual TCP connections and stream SLIP-framed OSC packets."""
        decoder = SLIPDecoder()
        try:
            while True:
                data = await reader.read(4096)
                if not data:
                    break
                packets = decoder.feed(data)
                for packet in packets:
                    try:
                        msg = OscMessage(packet)
                        self._handle_osc_message(msg.address, *msg.params)
                    except Exception as e:
                        logger.error(f"Failed to parse TCP OSC packet: {e}")
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"TCP client connection error: {e}")
        finally:
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass

    async def start(self) -> None:
        """Start the OSC server."""
        if self.protocol == "udp":
            loop = asyncio.get_running_loop()
            self.server = AsyncIOOSCUDPServer((self.host, self.port), self.dispatcher, loop)
            transport, _ = await self.server.create_serve_endpoint()
            self._transport = transport
            logger.info(f"OSC UDP server started on {self.host}:{self.port}")
        else:
            # TCP Server
            self._tcp_server = await asyncio.start_server(self._handle_tcp_client, self.host, self.port)
            logger.info(f"OSC TCP server started on {self.host}:{self.port}")

    async def stop(self) -> None:
        """Stop the OSC server."""
        if self._transport:
            self._transport.close()
            self._transport = None
        if self._tcp_server:
            self._tcp_server.close()
            await self._tcp_server.wait_closed()
            self._tcp_server = None
        for task in self._tcp_tasks:
            task.cancel()
        self._tcp_tasks.clear()
        logger.info(f"OSC {self.protocol.upper()} server stopped")

    def get_received_messages(
        self,
        address_pattern: str | None = None,
        max_age_seconds: float | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Get received OSC messages from the buffer."""
        current_time = time.time()
        messages = []

        for message in reversed(self._message_buffer):
            if address_pattern and address_pattern not in message.address:
                continue

            if max_age_seconds and (current_time - message.timestamp) > max_age_seconds:
                continue

            messages.append(message.to_dict())

            if len(messages) >= limit:
                break

        return messages

    def get_latest_message(self, address_pattern: str | None = None) -> dict[str, Any] | None:
        """Get the most recent OSC message matching the pattern."""
        messages = self.get_received_messages(address_pattern, limit=1)
        return messages[0] if messages else None

    def clear_message_buffer(self) -> int:
        """Clear all messages from the buffer."""
        cleared_count = len(self._message_buffer)
        self._message_buffer.clear()
        logger.info(f"Cleared {cleared_count} messages from OSC buffer")
        return cleared_count

    def get_buffer_stats(self) -> dict[str, Any]:
        """Get statistics about the message buffer."""
        if not self._message_buffer:
            return {
                "total_messages": 0,
                "oldest_message_age": None,
                "newest_message_age": None,
            }

        current_time = time.time()
        oldest = min(msg.timestamp for msg in self._message_buffer)
        newest = max(msg.timestamp for msg in self._message_buffer)

        return {
            "total_messages": len(self._message_buffer),
            "max_buffer_size": self._max_buffer_size,
            "oldest_message_age": current_time - oldest,
            "newest_message_age": current_time - newest,
        }

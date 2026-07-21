"""OSC client implementation for sending OSC messages over UDP and TCP."""

import logging
import socket
from typing import Any

from pythonosc import udp_client
from pythonosc.osc_message_builder import OscMessageBuilder

logger = logging.getLogger(__name__)


def slip_encode(data: bytes) -> bytes:
    """Encode packet using SLIP protocol (RFC 1055)."""
    encoded = bytearray([0xC0])
    for byte in data:
        if byte == 0xC0:
            encoded.extend([0xDB, 0xDC])
        elif byte == 0xDB:
            encoded.extend([0xDB, 0xDD])
        else:
            encoded.append(byte)
    encoded.append(0xC0)
    return bytes(encoded)


class OSCClient:
    """Client for sending OSC messages to an OSC server."""

    def __init__(self, host: str = "127.0.0.1", port: int = 9000, protocol: str = "udp"):
        """Initialize the OSC client.

        Args:
            host: The hostname or IP address of the OSC server.
            port: The port number of the OSC server.
            protocol: The protocol to use ('udp' or 'tcp').
        """
        self.host = host
        self.port = port
        self.protocol = protocol.lower()
        self._client = None
        self._tcp_socket = None

    def connect(self) -> None:
        """Establish connection to the OSC server."""
        if self.protocol == "udp":
            self._client = udp_client.SimpleUDPClient(self.host, self.port)
            logger.info(f"Connected to OSC UDP client at {self.host}:{self.port}")
        else:
            self._tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._tcp_socket.settimeout(2.0)
            self._tcp_socket.connect((self.host, self.port))
            logger.info(f"Connected to OSC TCP client at {self.host}:{self.port}")

    def send(self, address: str, *args: Any) -> None:
        """Send an OSC message.

        Args:
            address: The OSC address pattern (e.g., "/volume").
            *args: The arguments to send with the message.
        """
        if self.protocol == "udp":
            if self._client is None:
                self.connect()
            logger.debug(f"Sending UDP OSC message to {address}: {args}")
            self._client.send_message(address, args)
        else:
            if self._tcp_socket is None:
                self.connect()
            logger.debug(f"Sending TCP OSC message to {address}: {args}")
            builder = OscMessageBuilder(address=address)
            for arg in args:
                builder.add_arg(arg)
            msg = builder.build()
            slip_data = slip_encode(msg.dgram)
            try:
                self._tcp_socket.sendall(slip_data)
            except Exception as e:
                logger.error(f"TCP send failed, attempting reconnect: {e}")
                self._tcp_socket.close()
                self._tcp_socket = None
                self.connect()
                self._tcp_socket.sendall(slip_data)

    def close(self) -> None:
        """Close the OSC client connection."""
        if self._tcp_socket is not None:
            self._tcp_socket.close()
            self._tcp_socket = None
        self._client = None

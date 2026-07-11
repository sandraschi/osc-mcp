"""MIDI Listener for OSC-MCP.

This module provides functionality to listen for MIDI messages and convert them to OSC.
"""

import logging
from typing import Callable, Dict, Optional

import mido

logger = logging.getLogger(__name__)


class MIDIListener:
    """Listens for MIDI messages and converts them to OSC."""

    def __init__(self, port_name: Optional[str] = None):
        """Initialize the MIDI listener.

        Args:
            port_name: Optional specific MIDI port to listen to. If None, will use the first available input.
        """
        self.port_name = port_name
        self.port = None
        self.running = False
        self.callbacks = []

    def add_callback(self, callback: Callable[[Dict], None]) -> None:
        """Add a callback function to be called when a MIDI message is received.

        Args:
            callback: Function that takes a dictionary representing the MIDI message.
        """
        self.callbacks.append(callback)

    def _handle_message(self, message):
        """Handle incoming MIDI messages and convert them to a dictionary format."""
        msg_dict = {
            "type": message.type,
            "channel": getattr(message, "channel", None),
            "note": getattr(message, "note", None),
            "velocity": getattr(message, "velocity", None),
            "control": getattr(message, "control", None),
            "value": getattr(message, "value", None),
            "pitch": getattr(message, "pitch", None),
            "data1": getattr(message, "data1", None),
            "data2": getattr(message, "data2", None),
            "time": message.time,
        }

        logger.debug(f"MIDI message: {msg_dict}")
        for callback in self.callbacks:
            callback(msg_dict)

    def start(self) -> None:
        """Start listening for MIDI messages."""
        if self.running:
            return

        try:
            if self.port_name:
                self.port = mido.open_input(self.port_name, callback=self._handle_message)
            else:
                # Use the first available input port
                input_names = mido.get_input_names()
                if not input_names:
                    raise RuntimeError("No MIDI input ports available")
                self.port = mido.open_input(input_names[0], callback=self._handle_message)

            self.running = True
            logger.info(f"MIDI listener started on port: {self.port.name}")
        except Exception as e:
            logger.error(f"Failed to start MIDI listener: {e}")
            raise

    def stop(self) -> None:
        """Stop listening for MIDI messages."""
        if self.port and not self.port.closed:
            self.port.close()
        self.running = False
        logger.info("MIDI listener stopped")

    def __del__(self):
        """Ensure the port is closed when the object is deleted."""
        self.stop()

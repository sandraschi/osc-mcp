"""MIDI Controller for OSC-MCP.

This module provides functionality to send MIDI messages from OSC.
"""

import logging
from typing import Optional

import mido

logger = logging.getLogger(__name__)


class MIDIController:
    """Sends MIDI messages in response to OSC commands."""

    def __init__(self, port_name: Optional[str] = None):
        """Initialize the MIDI controller.

        Args:
            port_name: Optional specific MIDI port to send to. If None, will use the first available output.
        """
        self.port_name = port_name
        self.port = None

    def connect(self) -> None:
        """Connect to the MIDI output port."""
        if self.port is not None and not self.port.closed:
            return

        try:
            if self.port_name:
                self.port = mido.open_output(self.port_name)
            else:
                # Use the first available output port
                output_names = mido.get_output_names()
                if not output_names:
                    raise RuntimeError("No MIDI output ports available")
                self.port = mido.open_output(output_names[0])

            logger.info(f"Connected to MIDI output: {self.port.name}")
        except Exception as e:
            logger.error(f"Failed to connect to MIDI output: {e}")
            raise

    def send_note_on(self, note: int, velocity: int = 64, channel: int = 0) -> None:
        """Send a MIDI Note On message.

        Args:
            note: MIDI note number (0-127)
            velocity: Note velocity (0-127)
            channel: MIDI channel (0-15)
        """
        self.connect()
        msg = mido.Message("note_on", note=note, velocity=velocity, channel=channel)
        self.port.send(msg)
        logger.debug(f"Sent MIDI Note On: {msg}")

    def send_note_off(self, note: int, channel: int = 0) -> None:
        """Send a MIDI Note Off message.

        Args:
            note: MIDI note number (0-127)
            channel: MIDI channel (0-15)
        """
        self.connect()
        msg = mido.Message("note_off", note=note, channel=channel)
        self.port.send(msg)
        logger.debug(f"Sent MIDI Note Off: {msg}")

    def send_control_change(self, control: int, value: int, channel: int = 0) -> None:
        """Send a MIDI Control Change message.

        Args:
            control: Control number (0-127)
            value: Control value (0-127)
            channel: MIDI channel (0-15)
        """
        self.connect()
        msg = mido.Message("control_change", control=control, value=value, channel=channel)
        self.port.send(msg)
        logger.debug(f"Sent MIDI Control Change: {msg}")

    def send_program_change(self, program: int, channel: int = 0) -> None:
        """Send a MIDI Program Change message.

        Args:
            program: Program number (0-127)
            channel: MIDI channel (0-15)
        """
        self.connect()
        msg = mido.Message("program_change", program=program, channel=channel)
        self.port.send(msg)
        logger.debug(f"Sent MIDI Program Change: {msg}")

    def send_raw_message(self, message_type: str, **kwargs) -> None:
        """Send a raw MIDI message with the given parameters.

        Args:
            message_type: Type of MIDI message (e.g., 'note_on', 'control_change')
            **kwargs: Additional parameters for the message
        """
        self.connect()
        msg = mido.Message(message_type, **kwargs)
        self.port.send(msg)
        logger.debug(f"Sent raw MIDI message: {msg}")

    def close(self) -> None:
        """Close the MIDI output port."""
        if self.port and not self.port.closed:
            self.port.close()
            logger.info("Closed MIDI output port")

    def __del__(self):
        """Ensure the port is closed when the object is deleted."""
        self.close()

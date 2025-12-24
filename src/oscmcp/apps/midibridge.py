"""MIDI Bridge for OSC-MCP.

This module provides bidirectional translation between MIDI and OSC messages,
allowing MIDI controllers to control OSC parameters and OSC messages to trigger
MIDI events.
"""

import asyncio
import logging
from dataclasses import dataclass
from enum import IntEnum
from typing import Dict, List, Optional, Callable, Union, Tuple

import mido
from mido import Message as MidiMessage

from ..osc.client import OSCClient
from ..osc.server import OSCServer

logger = logging.getLogger(__name__)


class MIDIType(IntEnum):
    """Types of MIDI messages."""

    NOTE_OFF = 0x80
    NOTE_ON = 0x90
    POLY_AFTERTOUCH = 0xA0
    CONTROL_CHANGE = 0xB0
    PROGRAM_CHANGE = 0xC0
    CHANNEL_AFTERTOUCH = 0xD0
    PITCH_BEND = 0xE0
    SYSEX = 0xF0
    QUARTER_FRAME = 0xF1
    SONG_POS = 0xF2
    SONG_SELECT = 0xF3
    TUNE_REQUEST = 0xF6
    TIMING_CLOCK = 0xF8
    START = 0xFA
    CONTINUE = 0xFB
    STOP = 0xFC
    ACTIVE_SENSING = 0xFE
    SYSTEM_RESET = 0xFF


@dataclass
class MIDIMapping:
    """Mapping between a MIDI message and an OSC address."""

    # MIDI message type (from MIDIType)
    midi_type: MIDIType
    # MIDI channel (1-16, 0 for any)
    channel: int = 0
    # MIDI control number or note number (0-127, None for any)
    control: Optional[int] = None
    # OSC address to map to/from
    osc_address: str = ""
    # OSC argument index (for messages with multiple arguments)
    osc_arg_index: int = 0
    # Value range mapping (min, max) for MIDI to OSC conversion
    midi_range: Tuple[float, float] = (0.0, 127.0)
    # Value range mapping (min, max) for OSC to MIDI conversion
    osc_range: Tuple[float, float] = (0.0, 1.0)
    # Whether to round the value when converting to MIDI
    round_midi: bool = True
    # Whether to invert the value (1.0 - value)
    invert: bool = False
    # Additional OSC arguments (for OSC to MIDI)
    osc_args: Optional[list] = None
    # Additional MIDI parameters (for MIDI to OSC)
    midi_kwargs: Optional[dict] = None
    # Whether to send a note off message after a note on (for toggle behavior)
    send_note_off: bool = False
    # Last value sent (for toggle behavior)
    last_value: float = 0.0
    # Last toggle state (for toggle behavior)
    last_toggle: bool = False


class MIDIBridge:
    """Bidirectional bridge between MIDI and OSC.

    This class provides a bridge between MIDI controllers and OSC applications,
    allowing MIDI messages to control OSC parameters and OSC messages to trigger
    MIDI events.
    """

    def __init__(
        self,
        osc_host: str = "127.0.0.1",
        osc_port: int = 8000,
        midi_in_port: Optional[str] = None,
        midi_out_port: Optional[str] = None,
    ):
        """Initialize the MIDI-OSC bridge.

        Args:
            osc_host: Host for OSC communication
            osc_port: Port for OSC communication
            midi_in_port: Name of MIDI input port (None to auto-detect)
            midi_out_port: Name of MIDI output port (None to auto-detect)
        """
        self.osc_host = osc_host
        self.osc_port = osc_port
        self.midi_in_port_name = midi_in_port
        self.midi_out_port_name = midi_out_port

        # MIDI ports
        self.midi_in = None
        self.midi_out = None

        # OSC client and server
        self.osc_client = OSCClient(osc_host, osc_port)
        self.osc_server = OSCServer(osc_host, osc_port + 1)  # Use next port for replies

        # Mappings
        self.midi_to_osc_mappings: List[MIDIMapping] = []
        self.osc_to_midi_mappings: Dict[str, List[MIDIMapping]] = {}

        # MIDI listener and controller
        self.midi_listener = None
        self.midi_controller = None

        # Callbacks
        self.midi_message_callbacks = []
        self.osc_message_callbacks = []

        # Active notes (for note off handling)
        self.active_notes: Dict[Tuple[int, int], float] = {}

    async def start(self) -> None:
        """Start the MIDI-OSC bridge."""
        # Connect to MIDI ports
        await self._connect_midi()

        # Start OSC server
        await self.osc_server.start()

        # Set up OSC message handler
        self.osc_server.dispatcher.set_default_handler(self._handle_osc_message)

        logger.info(f"MIDI-OSC bridge started. OSC: {self.osc_host}:{self.osc_port}")

    async def stop(self) -> None:
        """Stop the MIDI-OSC bridge."""
        # Disconnect MIDI
        await self._disconnect_midi()

        # Stop OSC server
        await self.osc_server.stop()

        logger.info("MIDI-OSC bridge stopped")

    async def _connect_midi(self) -> None:
        """Connect to MIDI input and output ports."""
        # Get available MIDI ports
        input_ports = mido.get_input_names()
        output_ports = mido.get_output_names()

        if not input_ports:
            logger.warning("No MIDI input ports found")
        if not output_ports:
            logger.warning("No MIDI output ports found")

        # Connect to input port
        if self.midi_in_port_name:
            if self.midi_in_port_name in input_ports:
                self.midi_in = mido.open_input(
                    self.midi_in_port_name, callback=self._handle_midi_message
                )
                logger.info(f"Connected to MIDI input: {self.midi_in_port_name}")
            else:
                logger.warning(f"MIDI input port not found: {self.midi_in_port_name}")
        elif input_ports:
            # Auto-connect to first available input port
            self.midi_in = mido.open_input(
                input_ports[0], callback=self._handle_midi_message
            )
            logger.info(f"Connected to MIDI input: {input_ports[0]}")

        # Connect to output port
        if self.midi_out_port_name:
            if self.midi_out_port_name in output_ports:
                self.midi_out = mido.open_output(self.midi_out_port_name)
                logger.info(f"Connected to MIDI output: {self.midi_out_port_name}")
            else:
                logger.warning(f"MIDI output port not found: {self.midi_out_port_name}")
        elif output_ports:
            # Auto-connect to first available output port
            self.midi_out = mido.open_output(output_ports[0])
            logger.info(f"Connected to MIDI output: {output_ports[0]}")

    async def _disconnect_midi(self) -> None:
        """Disconnect from MIDI ports."""
        if self.midi_in and not self.midi_in.closed:
            self.midi_in.close()
        if self.midi_out and not self.midi_out.closed:
            self.midi_out.close()

    def add_midi_to_osc_mapping(
        self,
        midi_type: Union[MIDIType, str, int],
        channel: int,
        control: Optional[int],
        osc_address: str,
        osc_arg_index: int = 0,
        midi_range: Tuple[float, float] = (0.0, 127.0),
        osc_range: Tuple[float, float] = (0.0, 1.0),
        round_midi: bool = True,
        invert: bool = False,
        send_note_off: bool = False,
    ) -> MIDIMapping:
        """Add a mapping from MIDI to OSC.

        Args:
            midi_type: MIDI message type (e.g., 'note_on', 'control_change')
            channel: MIDI channel (1-16, 0 for any)
            control: MIDI control or note number (0-127, None for any)
            osc_address: OSC address to map to
            osc_arg_index: Index of the OSC argument to use
            midi_range: Range of MIDI values (min, max)
            osc_range: Range of OSC values (min, max)
            round_midi: Whether to round the value when converting to MIDI
            invert: Whether to invert the value (1.0 - value)
            send_note_off: Whether to send a note off after note on (for toggle)

        Returns:
            The created MIDIMapping
        """
        if isinstance(midi_type, str):
            midi_type = getattr(MIDIType, midi_type.upper())
        elif isinstance(midi_type, int):
            midi_type = MIDIType(midi_type & 0xF0)  # Just the status byte

        mapping = MIDIMapping(
            midi_type=midi_type,
            channel=channel,
            control=control,
            osc_address=osc_address,
            osc_arg_index=osc_arg_index,
            midi_range=midi_range,
            osc_range=osc_range,
            round_midi=round_midi,
            invert=invert,
            send_note_off=send_note_off,
        )

        self.midi_to_osc_mappings.append(mapping)
        return mapping

    def add_osc_to_midi_mapping(
        self,
        osc_address: str,
        midi_type: Union[MIDIType, str, int],
        channel: int,
        control: Optional[int],
        osc_arg_index: int = 0,
        midi_range: Tuple[float, float] = (0.0, 127.0),
        osc_range: Tuple[float, float] = (0.0, 1.0),
        round_midi: bool = True,
        invert: bool = False,
        **midi_kwargs,
    ) -> MIDIMapping:
        """Add a mapping from OSC to MIDI.

        Args:
            osc_address: OSC address to map from
            midi_type: MIDI message type (e.g., 'note_on', 'control_change')
            channel: MIDI channel (1-16, 0 for any)
            control: MIDI control or note number (0-127, None for any)
            osc_arg_index: Index of the OSC argument to use
            midi_range: Range of MIDI values (min, max)
            osc_range: Range of OSC values (min, max)
            round_midi: Whether to round the value when converting to MIDI
            invert: Whether to invert the value (1.0 - value)
            **midi_kwargs: Additional MIDI parameters (e.g., velocity, time)

        Returns:
            The created MIDIMapping
        """
        if isinstance(midi_type, str):
            midi_type = getattr(MIDIType, midi_type.upper())
        elif isinstance(midi_type, int):
            midi_type = MIDIType(midi_type & 0xF0)  # Just the status byte

        mapping = MIDIMapping(
            midi_type=midi_type,
            channel=channel,
            control=control,
            osc_address=osc_address,
            osc_arg_index=osc_arg_index,
            midi_range=midi_range,
            osc_range=osc_range,
            round_midi=round_midi,
            invert=invert,
            midi_kwargs=midi_kwargs or {},
        )

        if osc_address not in self.osc_to_midi_mappings:
            self.osc_to_midi_mappings[osc_address] = []

        self.osc_to_midi_mappings[osc_address].append(mapping)
        return mapping

    def _handle_midi_message(self, message: MidiMessage) -> None:
        """Handle incoming MIDI messages and forward to OSC."""
        # Log the message
        logger.debug(f"MIDI: {message}")

        # Call MIDI message callbacks
        for callback in self.midi_message_callbacks:
            try:
                callback(message)
            except Exception as e:
                logger.error(f"Error in MIDI callback: {e}")

        # Get message type and channel
        msg_type = message.type
        channel = message.channel + 1  # Convert from 0-15 to 1-16

        # Find matching mappings
        for mapping in self.midi_to_osc_mappings:
            # Check message type
            if mapping.midi_type != getattr(MIDIType, f"{msg_type.upper()}"):
                continue

            # Check channel
            if mapping.channel != 0 and mapping.channel != channel:
                continue

            # Check control/note number if specified
            if mapping.control is not None:
                if hasattr(message, "control") and message.control != mapping.control:
                    continue
                if hasattr(message, "note") and message.note != mapping.control:
                    continue

            # Get value from message
            value = 0.0
            if msg_type == "note_on" or msg_type == "note_off":
                value = message.velocity / 127.0
            elif msg_type == "control_change":
                value = message.value / 127.0
            elif msg_type == "pitchwheel":
                value = (message.pitch + 8192) / 16383.0  # Convert to 0.0-1.0
            elif msg_type == "aftertouch":
                value = message.value / 127.0

            # Apply inversion if needed
            if mapping.invert:
                value = 1.0 - value

            # Map from MIDI range to OSC range
            midi_min, midi_max = mapping.midi_range
            osc_min, osc_max = mapping.osc_range

            # Handle note on/off for toggle behavior
            if msg_type == "note_on" and mapping.send_note_off:
                if value > 0:  # Note on
                    # Toggle between 0 and 1
                    mapping.last_toggle = not mapping.last_toggle
                    value = 1.0 if mapping.last_toggle else 0.0
                else:  # Note off
                    continue  # Skip note off for toggle behavior

            # Map value from MIDI range to OSC range
            if midi_max > midi_min:  # Avoid division by zero
                normalized = (value - midi_min) / (midi_max - midi_min)
                osc_value = osc_min + normalized * (osc_max - osc_min)
            else:
                osc_value = osc_min

            # Send OSC message
            self.osc_client.send(mapping.osc_address, osc_value)

            # Store last value for toggle behavior
            mapping.last_value = value

    def _handle_osc_message(self, address: str, *args) -> None:
        """Handle incoming OSC messages and forward to MIDI."""
        # Log the message
        logger.debug(f"OSC: {address} {args}")

        # Call OSC message callbacks
        for callback in self.osc_message_callbacks:
            try:
                callback(address, args)
            except Exception as e:
                logger.error(f"Error in OSC callback: {e}")

        # Find matching mappings
        if address not in self.osc_to_midi_mappings:
            return

        for mapping in self.osc_to_midi_mappings[address]:
            try:
                # Get value from OSC message
                if len(args) <= mapping.osc_arg_index:
                    logger.warning(
                        f"OSC message has too few arguments for mapping: {address}"
                    )
                    continue

                value = args[mapping.osc_arg_index]
                if not isinstance(value, (int, float)):
                    logger.warning(
                        f"OSC argument {mapping.osc_arg_index} is not a number: {value}"
                    )
                    continue

                # Apply inversion if needed
                if mapping.invert:
                    value = 1.0 - value

                # Map from OSC range to MIDI range
                osc_min, osc_max = mapping.osc_range
                midi_min, midi_max = mapping.midi_range

                # Map value from OSC range to MIDI range
                if osc_max > osc_min:  # Avoid division by zero
                    normalized = (value - osc_min) / (osc_max - osc_min)
                    midi_value = midi_min + normalized * (midi_max - midi_min)
                else:
                    midi_value = midi_min

                # Round if needed
                if mapping.round_midi:
                    midi_value = int(round(midi_value))

                # Clamp to MIDI range
                midi_value = max(midi_min, min(midi_max, midi_value))

                # Create MIDI message
                msg_kwargs = {
                    "channel": mapping.channel - 1,  # Convert to 0-15
                    "time": 0,
                    **(mapping.midi_kwargs or {}),
                }

                if mapping.control is not None:
                    if mapping.midi_type == MIDIType.CONTROL_CHANGE:
                        msg = MidiMessage(
                            "control_change",
                            control=mapping.control,
                            value=int(midi_value),
                            **msg_kwargs,
                        )
                    elif mapping.midi_type == MIDIType.NOTE_ON:
                        msg = MidiMessage(
                            "note_on",
                            note=mapping.control,
                            velocity=int(midi_value),
                            **msg_kwargs,
                        )
                    elif mapping.midi_type == MIDIType.NOTE_OFF:
                        msg = MidiMessage(
                            "note_off",
                            note=mapping.control,
                            velocity=int(midi_value),
                            **msg_kwargs,
                        )
                    elif mapping.midi_type == MIDIType.PROGRAM_CHANGE:
                        msg = MidiMessage(
                            "program_change", program=int(midi_value), **msg_kwargs
                        )
                    else:
                        logger.warning(
                            f"Unsupported MIDI type for OSC to MIDI mapping: {mapping.midi_type}"
                        )
                        continue
                else:
                    # For messages without a control/note number
                    if mapping.midi_type == MIDIType.PROGRAM_CHANGE:
                        msg = MidiMessage(
                            "program_change", program=int(midi_value), **msg_kwargs
                        )
                    elif mapping.midi_type == MIDIType.PITCH_BEND:
                        # Convert from 0-1 to -8192-8191 (14-bit)
                        pitch_value = int((midi_value * 16383) - 8192)
                        msg = MidiMessage("pitchwheel", pitch=pitch_value, **msg_kwargs)
                    else:
                        logger.warning(
                            f"Unsupported MIDI type for OSC to MIDI mapping without control: {mapping.midi_type}"
                        )
                        continue

                # Send MIDI message
                if self.midi_out and not self.midi_out.closed:
                    self.midi_out.send(msg)
                    logger.debug(f"Sent MIDI: {msg}")

            except Exception as e:
                logger.error(f"Error processing OSC to MIDI mapping: {e}")

    def on_midi_message(self, callback: Callable[[MidiMessage], None]) -> None:
        """Register a callback for MIDI messages.

        Args:
            callback: Function that takes a mido.Message
        """
        self.midi_message_callbacks.append(callback)

    def on_osc_message(self, callback: Callable[[str, tuple], None]) -> None:
        """Register a callback for OSC messages.

        Args:
            callback: Function that takes (address, args)
        """
        self.osc_message_callbacks.append(callback)


# Example usage
async def example_usage():
    """Example of using the MIDIBridge class."""
    import asyncio

    # Create MIDI-OSC bridge
    bridge = MIDIBridge(
        osc_host="127.0.0.1",
        osc_port=8000,
        midi_in_port=None,  # Auto-detect
        midi_out_port=None,  # Auto-detect
    )

    # Add some mappings

    # Map MIDI CC 1 to /test/volume (0.0-1.0)
    bridge.add_midi_to_osc_mapping(
        midi_type="control_change",
        channel=1,  # MIDI channel 1
        control=1,  # CC 1 (Modulation Wheel)
        osc_address="/test/volume",
        midi_range=(0.0, 127.0),
        osc_range=(0.0, 1.0),
    )

    # Map /test/led to MIDI note on/off on channel 1, note 60
    bridge.add_osc_to_midi_mapping(
        osc_address="/test/led",
        midi_type="note_on",
        channel=1,  # MIDI channel 1
        control=60,  # Middle C
        osc_arg_index=0,
        osc_range=(0.0, 1.0),
        midi_range=(0, 127),
        velocity=100,  # Fixed velocity
    )

    # Add callbacks for logging
    def on_midi(message):
        print(f"MIDI: {message}")

    def on_osc(address, args):
        print(f"OSC: {address} {args}")

    bridge.on_midi_message(on_midi)
    bridge.on_osc_message(on_osc)

    # Start the bridge
    await bridge.start()

    try:
        # Keep running
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("Stopping...")
    finally:
        await bridge.stop()


if __name__ == "__main__":
    asyncio.run(example_usage())

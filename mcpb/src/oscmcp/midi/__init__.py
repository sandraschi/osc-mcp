"""MIDI module for OSC-MCP.

This package provides MIDI integration for the OSC-MCP bridge,
allowing translation between OSC messages and MIDI events.
"""

from .controller import MIDIController
from .listener import MIDIListener

__all__ = ["MIDIController", "MIDIListener"]

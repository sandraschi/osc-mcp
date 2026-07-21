"""MIDI Bridge MCP tool interface."""

import logging
from typing import Any

import mido
from fastmcp import FastMCP

from .midibridge import MIDIBridge

logger = logging.getLogger(__name__)

# Global active MIDI Bridge instance
_active_bridge: MIDIBridge | None = None


def register_midi_tools(server: FastMCP) -> None:
    """Registers MIDI Bridge control tools on the FastMCP server."""

    @server.tool()
    async def get_midi_ports() -> dict[str, list[str]]:
        """Retrieve lists of available physical/virtual MIDI inputs and outputs on the host.

        Returns:
            Dictionary with keys 'inputs' and 'outputs' containing lists of port names.
        """
        try:
            inputs = mido.get_input_names()
            outputs = mido.get_output_names()
            return {"status": "success", "inputs": inputs, "outputs": outputs}
        except Exception as e:
            return {"status": "error", "message": f"Failed to query MIDI ports: {e}"}

    @server.tool()
    async def start_midi_bridge(
        osc_host: str = "127.0.0.1", osc_port: int = 8000, midi_in: str | None = None, midi_out: str | None = None
    ) -> dict[str, Any]:
        """Start the bidirectional MIDI-to-OSC loopback bridge.

        Args:
            osc_host: Host IP for the target OSC application (default: 127.0.0.1)
            osc_port: Port number for the target OSC application (default: 8000)
            midi_in: Specific MIDI input device name (omitted for auto-discovery)
            midi_out: Specific MIDI output device name (omitted for auto-discovery)
        """
        global _active_bridge
        if _active_bridge is not None:
            return {"status": "error", "message": "MIDI Bridge is already running. Stop it first."}

        try:
            _active_bridge = MIDIBridge(
                osc_host=osc_host, osc_port=osc_port, midi_in_port=midi_in, midi_out_port=midi_out
            )
            await _active_bridge.start()
            return {
                "status": "success",
                "message": "MIDI-OSC Bridge started successfully",
                "osc_target": f"{osc_host}:{osc_port}",
                "midi_in": _active_bridge.midi_in.name if _active_bridge.midi_in else None,
                "midi_out": _active_bridge.midi_out.name if _active_bridge.midi_out else None,
            }
        except Exception as e:
            _active_bridge = None
            return {"status": "error", "message": f"Failed to start MIDI Bridge: {e}"}

    @server.tool()
    async def stop_midi_bridge() -> dict[str, str]:
        """Stop the currently running MIDI-OSC Bridge."""
        global _active_bridge
        if _active_bridge is None:
            return {"status": "error", "message": "No active MIDI Bridge running"}

        try:
            await _active_bridge.stop()
            _active_bridge = None
            return {"status": "success", "message": "MIDI Bridge stopped"}
        except Exception as e:
            return {"status": "error", "message": f"Failed to stop MIDI Bridge: {e}"}

    @server.tool()
    async def add_midi_mapping(
        direction: str,
        osc_address: str,
        midi_type: str,
        channel: int = 1,
        control: int | None = None,
        min_val: float = 0.0,
        max_val: float = 1.0,
    ) -> dict[str, Any]:
        """Add a dynamic CC or Note mapping rule to the running bridge.

        Args:
            direction: Translation direction - 'midi_to_osc' or 'osc_to_midi'
            osc_address: OSC address path (e.g. '/track/1/volume')
            midi_type: MIDI message type - 'control_change' or 'note_on'
            channel: MIDI channel (1-16, default: 1)
            control: MIDI CC index or note number (0-127)
            min_val: Minimum value mapping boundary (default: 0.0)
            max_val: Maximum value mapping boundary (default: 1.0)
        """
        global _active_bridge
        if _active_bridge is None:
            return {"status": "error", "message": "MIDI Bridge is not active. Start it first."}

        try:
            if direction == "midi_to_osc":
                _active_bridge.add_midi_to_osc_mapping(
                    midi_type=midi_type,
                    channel=channel,
                    control=control,
                    osc_address=osc_address,
                    osc_range=(min_val, max_val),
                )
            elif direction == "osc_to_midi":
                _active_bridge.add_osc_to_midi_mapping(
                    osc_address=osc_address,
                    midi_type=midi_type,
                    channel=channel,
                    control=control,
                    osc_range=(min_val, max_val),
                )
            else:
                return {"status": "error", "message": f"Invalid direction: {direction}"}

            return {
                "status": "success",
                "message": f"Mapping added successfully for {osc_address}",
                "direction": direction,
                "midi_type": midi_type,
                "control": control,
            }
        except Exception as e:
            return {"status": "error", "message": f"Failed to add mapping: {e}"}

    @server.tool()
    async def get_midi_mappings() -> dict[str, Any]:
        """Retrieve all currently active MIDI and OSC mapping rules in the bridge."""
        global _active_bridge
        if _active_bridge is None:
            return {"status": "error", "message": "MIDI Bridge is not active"}

        try:
            m2o = []
            for m in _active_bridge.midi_to_osc_mappings:
                m2o.append(
                    {
                        "midi_type": m.midi_type.name,
                        "channel": m.channel,
                        "control": m.control,
                        "osc_address": m.osc_address,
                        "osc_range": m.osc_range,
                    }
                )

            o2m = []
            for addr, mappings in _active_bridge.osc_to_midi_mappings.items():
                for m in mappings:
                    o2m.append(
                        {
                            "osc_address": addr,
                            "midi_type": m.midi_type.name,
                            "channel": m.channel,
                            "control": m.control,
                            "midi_range": m.midi_range,
                        }
                    )

            return {"status": "success", "midi_to_osc": m2o, "osc_to_midi": o2m}
        except Exception as e:
            return {"status": "error", "message": f"Failed to list mappings: {e}"}

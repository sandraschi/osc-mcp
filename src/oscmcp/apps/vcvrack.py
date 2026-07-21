"""VCV Rack integration for OSC-MCP.

This module provides integration with VCV Rack's OSC protocol, enabling
bidirectional communication for modular synthesis control.
"""

import logging
from collections.abc import Callable
from typing import Any

from ..osc.client import OSCClient
from ..osc.server import OSCServer

logger = logging.getLogger(__name__)


class VCVController:
    """Main class for VCV Rack integration.

    Handles both sending and receiving OSC messages to/from VCV Rack.
    """

    DEFAULT_PORT = 10001  # Default VCV Rack OSC port

    def __init__(
        self,
        host: str = "127.0.0.1",
        listen_port: int = DEFAULT_PORT + 1,
        target_port: int = DEFAULT_PORT,
    ):
        """Initialize the VCV Rack OSC interface.

        Args:
            host: Host where VCV Rack is running
            listen_port: Port to receive OSC messages from VCV Rack
            target_port: Port to send OSC messages to VCV Rack
        """
        self.host = host
        self.listen_port = listen_port
        self.target_port = target_port

        # OSC client for sending to VCV Rack
        self.client = OSCClient(host, target_port)

        # OSC server for receiving from VCV Rack
        self.server = OSCServer(host, listen_port)

        # Callback storage
        self.param_callbacks: dict[str, list[Callable[[str, Any], None]]] = {}
        self.message_callbacks: list[Callable[[str, list], None]] = []

        # Register default handlers
        self._register_default_handlers()

    def _register_default_handlers(self) -> None:
        """Register default OSC message handlers."""
        # Default handler for parameter updates
        self.server.dispatcher.map("/param", self._handle_param_message)
        # Default handler for all other messages
        self.server.dispatcher.set_default_handler(self._handle_generic_message)

    async def start(self) -> None:
        """Start the OSC server to receive messages from VCV Rack."""
        await self.server.start()
        logger.info(
            f"VCV Rack OSC interface started. Listening on port {self.listen_port}, sending to port {self.target_port}"
        )

    async def stop(self) -> None:
        """Stop the OSC server."""
        await self.server.stop()
        logger.info("VCV Rack OSC interface stopped")

    def _handle_param_message(self, address: str, *args) -> None:
        """Handle parameter update messages from VCV Rack.

        Args:
            address: OSC address (should be "/param")
            *args: Message arguments [module_id, param_id, value]
        """
        if len(args) < 3:
            logger.warning(f"Invalid parameter message: {args}")
            return

        module_id = args[0]
        param_id = args[1]
        value = args[2]

        param_path = f"/param/{module_id}/{param_id}"
        logger.debug(f"Parameter update: {param_path} = {value}")

        # Trigger callbacks for this specific parameter
        if param_path in self.param_callbacks:
            for callback in self.param_callbacks[param_path]:
                try:
                    callback(param_path, value)
                except Exception as e:
                    logger.error(f"Error in parameter callback for '{param_path}': {e}")

    def _handle_generic_message(self, address: str, *args) -> None:
        """Handle generic OSC messages from VCV Rack.

        Args:
            address: OSC address pattern
            *args: Message arguments
        """
        logger.debug(f"Received OSC message: {address} {args}")

        # Trigger generic message callbacks
        for callback in self.message_callbacks:
            try:
                callback(address, list(args))
            except Exception as e:
                logger.error(f"Error in message callback: {e}")

    def on_parameter_change(self, module_id: int, param_id: int, callback: Callable[[str, float], None]) -> None:
        """Register a callback for parameter changes.

        Args:
            module_id: ID of the module
            param_id: ID of the parameter
            callback: Function that takes (param_path, value)
        """
        param_path = f"/param/{module_id}/{param_id}"
        if param_path not in self.param_callbacks:
            self.param_callbacks[param_path] = []
        self.param_callbacks[param_path].append(callback)

    def on_message(self, callback: Callable[[str, list], None]) -> None:
        """Register a callback for all OSC messages.

        Args:
            callback: Function that takes (address, args)
        """
        self.message_callbacks.append(callback)

    # VCV Rack specific methods

    def set_parameter(self, module_id: int, param_id: int, value: float) -> None:
        """Set a parameter value in VCV Rack.

        Args:
            module_id: ID of the module
            param_id: ID of the parameter
            value: New value for the parameter (0.0 to 1.0)
        """
        self.client.send("/param", module_id, param_id, float(value))

    def set_light(self, module_id: int, light_id: int, brightness: float) -> None:
        """Set a light's brightness in VCV Rack.

        Args:
            module_id: ID of the module
            light_id: ID of the light
            brightness: Brightness value (0.0 to 1.0)
        """
        self.client.send("/light", module_id, light_id, float(brightness))

    def trigger(self, module_id: int, trigger_id: int) -> None:
        """Trigger an event in VCV Rack.

        Args:
            module_id: ID of the module
            trigger_id: ID of the trigger
        """
        self.client.send("/trigger", module_id, trigger_id)

    def send_cv(self, module_id: int, cv_id: int, voltage: float) -> None:
        """Send a CV value to VCV Rack.

        Args:
            module_id: ID of the module
            cv_id: ID of the CV input
            voltage: Voltage value (-10.0 to 10.0)
        """
        self.client.send("/cv", module_id, cv_id, float(voltage))

    # MIDI methods

    def play_midi_note(self, note: int, velocity: int = 100, channel: int = 1) -> None:
        """Play a MIDI note in VCV Rack.

        Args:
            note: MIDI note number (0-127)
            velocity: Note velocity (0-127)
            channel: MIDI channel (1-16)
        """
        self.client.send("/midi/note", channel, note, velocity)

    def stop_midi_note(self, note: int, channel: int = 1) -> None:
        """Stop a MIDI note in VCV Rack.

        Args:
            note: MIDI note number (0-127)
            channel: MIDI channel (1-16)
        """
        self.client.send("/midi/note", channel, note, 0)

    def send_midi_cc(self, controller: int, value: int, channel: int = 1) -> None:
        """Send a MIDI CC (control change) message to VCV Rack.

        Args:
            controller: CC controller number (0-127)
            value: CC value (0-127)
            channel: MIDI channel (1-16)
        """
        self.client.send("/midi/cc", channel, controller, value)

    # Convenience methods for common modules

    def set_vco_frequency(self, module_id: int, frequency: float) -> None:
        """Set the frequency of a VCO module.

        Args:
            module_id: ID of the VCO module
            frequency: Frequency in Hz
        """
        # Convert Hz to 0-1 range (assuming 0-10V = 0-10kHz)
        value = min(max(0.0, frequency / 10000.0), 1.0)
        self.set_parameter(module_id, 0, value)  # Param 0 is usually frequency

    def set_vca_level(self, module_id: int, level: float) -> None:
        """Set the level of a VCA module.

        Args:
            module_id: ID of the VCA module
            level: Level (0.0 to 1.0)
        """
        self.set_parameter(module_id, 0, float(level))  # Param 0 is usually level


# Example usage
async def example_usage():
    """Example of using the VCVController class."""
    import asyncio

    # Create VCV Rack controller
    vcv = VCVController()

    # Define callbacks
    def on_parameter_changed(param_path, value):
        logger.info(f"Parameter '{param_path}' changed to: {value}")

    def on_message(address, args):
        logger.info(f"Received message: {address} {args}")

    # Register callbacks
    vcv.on_parameter_change(1, 0, on_parameter_changed)  # Module 1, Param 0
    vcv.on_message(on_message)

    try:
        # Start the OSC server
        await vcv.start()

        # Main loop
        while True:
            # Example: Update a parameter
            vcv.set_parameter(1, 0, 0.5)  # Set module 1, param 0 to 0.5

            # Wait for a bit
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        logger.info("Stopping...")
    finally:
        await vcv.stop()


if __name__ == "__main__":
    import asyncio

    asyncio.run(example_usage())

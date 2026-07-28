"""Resolume Arena integration for OSC-MCP.

This module provides integration with Resolume Arena's OSC protocol, enabling
control of video mixing and composition.
"""

import logging
from collections.abc import Callable
from typing import Any

from ..osc.client import OSCClient
from ..osc.server import OSCServer

logger = logging.getLogger(__name__)


class ResolumeArena:
    """Main class for Resolume Arena integration.

    Handles both sending and receiving OSC messages to/from Resolume Arena.
    """

    DEFAULT_PORT = 7000  # Default Resolume Arena OSC port

    def __init__(
        self,
        host: str = "127.0.0.1",
        listen_port: int = DEFAULT_PORT + 1,
        target_port: int = DEFAULT_PORT,
    ):
        """Initialize the Resolume Arena OSC interface.

        Args:
            host: Host where Resolume Arena is running
            listen_port: Port to receive OSC messages from Resolume
            target_port: Port to send OSC messages to Resolume
        """
        self.host = host
        self.listen_port = listen_port
        self.target_port = target_port

        # OSC client for sending to Resolume
        self.client = OSCClient(host, target_port)

        # OSC server for receiving from Resolume
        self.server = OSCServer(host, listen_port)

        # Callback storage
        self.callbacks: dict[str, list[Callable[[str, Any], None]]] = {}
        self.feedback_callbacks: list[Callable[[str, list], None]] = []

        # Register default handlers
        self._register_default_handlers()

    def _register_default_handlers(self) -> None:
        """Register default OSC message handlers."""
        # Default handler for all messages
        self.server.dispatcher.set_default_handler(self._handle_message)

    async def start(self) -> None:
        """Start the OSC server to receive messages from Resolume."""
        await self.server.start()
        logger.info(
            f"Resolume Arena OSC interface started. Listening on port {self.listen_port}, sending to port {self.target_port}"
        )

    async def stop(self) -> None:
        """Stop the OSC server."""
        await self.server.stop()
        logger.info("Resolume Arena OSC interface stopped")

    def _handle_message(self, address: str, *args) -> None:
        """Handle incoming OSC messages.

        Args:
            address: OSC address pattern
            *args: Message arguments
        """
        # Remove any trailing slashes for consistency
        address = address.rstrip("/")

        # Log the message
        logger.debug(f"Received OSC message: {address} {args}")

        # Call registered callbacks
        self._trigger_callbacks(address, args)

        # Also trigger feedback callbacks
        for callback in self.feedback_callbacks:
            try:
                callback(address, list(args))
            except Exception as e:
                logger.error(f"Error in feedback callback: {e}")

    def _trigger_callbacks(self, address: str, args: tuple) -> None:
        """Trigger callbacks for a specific address.

        Args:
            address: OSC address pattern
            args: Message arguments
        """
        if address in self.callbacks:
            for callback in self.callbacks[address]:
                try:
                    callback(address, args[0] if len(args) == 1 else args)
                except Exception as e:
                    logger.error(f"Error in callback for '{address}': {e}")

    def on_message(self, address: str, callback: Callable[[str, Any], None]) -> None:
        """Register a callback for messages to a specific address.

        Args:
            address: OSC address pattern to listen to
            callback: Function that takes (address, value) as arguments
        """
        # Ensure address starts with a slash
        if not address.startswith("/"):
            address = "/" + address

        if address not in self.callbacks:
            self.callbacks[address] = []

        self.callbacks[address].append(callback)

    def on_feedback(self, callback: Callable[[str, list], None]) -> None:
        """Register a callback for all feedback messages.

        Args:
            callback: Function that takes (address, args)
        """
        self.feedback_callbacks.append(callback)

    # Resolume Arena specific methods

    def send(self, address: str, *args) -> None:
        """Send an OSC message to Resolume Arena.

        Args:
            address: OSC address pattern
            *args: Values to send
        """
        # Ensure address starts with a slash
        if not address.startswith("/"):
            address = "/" + address

        self.client.send(address, *args)
        logger.debug(f"Sent OSC message: {address} {args}")

    # Composition control

    def play_composition(self, composition: int) -> None:
        """Play a composition.

        Args:
            composition: Composition number (1-based)
        """
        self.send("/composition/selected", composition - 1)
        self.send("/composition/connect", 1)

    def stop_composition(self, composition: int) -> None:
        """Stop a composition.

        Args:
            composition: Composition number (1-based)
        """
        self.send("/composition/selected", composition - 1)
        self.send("/composition/connect", 0)

    # Layer control

    def set_layer_opacity(self, layer: int, opacity: float) -> None:
        """Set the opacity of a layer.

        Args:
            layer: Layer number (1-based)
            opacity: Opacity value (0.0 to 1.0)
        """
        self.send(f"/composition/layers/{layer}/opacity", float(opacity))

    def toggle_layer_visibility(self, layer: int, visible: bool | None = None) -> None:
        """Toggle or set the visibility of a layer.

        Args:
            layer: Layer number (1-based)
            visible: Optional boolean to set visibility, or None to toggle
        """
        if visible is None:
            self.send(f"/composition/layers/{layer}/toggle")
        else:
            self.send(f"/composition/layers/{layer}/video/opacity", 1.0 if visible else 0.0)

    # Clip control

    def play_clip(self, layer: int, column: int) -> None:
        """Play a clip.

        Args:
            layer: Layer number (1-based)
            column: Column number (1-based)
        """
        self.send(f"/composition/layers/{layer}/clips/{column}/connect", 1)

    def stop_clip(self, layer: int, column: int) -> None:
        """Stop a clip.

        Args:
            layer: Layer number (1-based)
            column: Column number (1-based)
        """
        self.send(f"/composition/layers/{layer}/clips/{column}/connect", 0)

    def trigger_clip(self, layer: int, column: int) -> None:
        """Trigger a clip (play if stopped, stop if playing).

        Args:
            layer: Layer number (1-based)
            column: Column number (1-based)
        """
        self.send(f"/composition/layers/{layer}/clips/{column}/connect/toggle")

    # Transport control

    def play(self) -> None:
        """Start transport."""
        self.send("/transport/play")

    def stop_transport(self) -> None:
        """Stop transport."""
        self.send("/transport/stop")

    def toggle_playback(self) -> None:
        """Toggle playback (play/stop)."""
        self.send("/transport/toggle")

    def set_bpm(self, bpm: float) -> None:
        """Set BPM.

        Args:
            bpm: Beats per minute
        """
        self.send("/transport/tempo", float(bpm))

    # Effect control

    def set_effect_parameter(self, layer: int, effect: int, parameter: int, value: float) -> None:
        """Set an effect parameter.

        Args:
            layer: Layer number (1-based)
            effect: Effect number (1-based)
            parameter: Parameter number (1-based)
            value: Parameter value (0.0 to 1.0)
        """
        self.send(
            f"/composition/layers/{layer}/effects/{effect}/{parameter}/value",
            float(value),
        )

    def toggle_effect_bypass(self, layer: int, effect: int, bypassed: bool | None = None) -> None:
        """Toggle or set effect bypass.

        Args:
            layer: Layer number (1-based)
            effect: Effect number (1-based)
            bypassed: Optional boolean to set bypass, or None to toggle
        """
        if bypassed is None:
            self.send(f"/composition/layers/{layer}/effects/{effect}/bypass")
        else:
            self.send(
                f"/composition/layers/{layer}/effects/{effect}/bypass",
                1 if bypassed else 0,
            )


# Example usage
async def example_usage():
    """Example of using the ResolumeArena class."""
    import asyncio

    # Create Resolume Arena controller
    resolume = ResolumeArena()

    # Define callbacks
    def on_parameter_changed(address, value):
        logger.info(f"Parameter '{address}' changed to: {value}")

    def on_feedback(address, args):
        logger.info(f"Feedback: {address} {args}")

    # Register callbacks
    resolume.on_message("/composition/video/mixer/opacity", on_parameter_changed)
    resolume.on_feedback(on_feedback)

    try:
        # Start the OSC server
        await resolume.start()

        # Main loop
        while True:
            # Example: Toggle layer visibility
            resolume.toggle_layer_visibility(1)  # Toggle layer 1

            # Wait for a bit
            await asyncio.sleep(2)

    except KeyboardInterrupt:
        logger.info("Stopping...")
    finally:
        await resolume.stop()


if __name__ == "__main__":
    import asyncio

    asyncio.run(example_usage())

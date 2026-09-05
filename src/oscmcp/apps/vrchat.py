"""VRChat integration for OSC-MCP.

This module provides integration with VRChat's OSC protocol, allowing for
bidirectional communication with VRChat avatars and worlds.
"""

import logging
import os
from collections.abc import Callable
from pathlib import Path
from typing import Any

from ..osc.client import OSCClient
from ..osc.server import OSCServer

logger = logging.getLogger(__name__)


class VRChatOSC:
    """Main class for VRChat OSC integration.

    Handles both sending and receiving OSC messages to/from VRChat.
    """

    # Default VRChat OSC ports - verified against docs.vrchat.com: VRChat itself
    # listens (receives) on 9000, and sends its own outgoing messages on 9001.
    # These two constants were swapped before this fix (input_port=9000 was
    # documented as "port to receive from VRChat" but defaulted to VRChat's
    # own receive port, not its send port) - found via web research while
    # building per-app skills, not caught by any existing test.
    DEFAULT_INPUT_PORT = 9001  # we listen here for VRChat's outgoing messages
    DEFAULT_OUTPUT_PORT = 9000  # we send here; this is VRChat's own listen port

    def __init__(
        self,
        host: str = "127.0.0.1",
        input_port: int = DEFAULT_INPUT_PORT,
        output_port: int = DEFAULT_OUTPUT_PORT,
    ):
        """Initialize the VRChat OSC interface.

        Args:
            host: Host where VRChat is running (usually localhost)
            input_port: Port to receive OSC messages from VRChat
            output_port: Port to send OSC messages to VRChat
        """
        self.host = host
        self.input_port = input_port
        self.output_port = output_port

        # OSC client for sending to VRChat
        self.client = OSCClient(host, output_port)

        # OSC server for receiving from VRChat
        self.server = OSCServer(host, input_port)

        # Avatar parameter callbacks
        self.parameter_callbacks: dict[str, list[Callable[[str, Any], None]]] = {}

        # Avatar change callback
        self.avatar_change_callback: Callable[[str], None] | None = None

        # Avatar config
        self.avatar_id: str | None = None
        self.avatar_name: str | None = None
        self.avatar_parameters: dict[str, dict] = {}

        # Register default handlers
        self._register_default_handlers()

    def _register_default_handlers(self) -> None:
        """Register default OSC message handlers."""
        # Avatar change handler
        self.server.dispatcher.map("/avatar/change", self._handle_avatar_change)

        # Avatar parameter handler
        self.server.dispatcher.map("/avatar/parameters/*", self._handle_avatar_parameter)

    async def start(self) -> None:
        """Start the OSC server to receive messages from VRChat."""
        await self.server.start()
        logger.info(
            f"VRChat OSC interface started. Listening on port {self.input_port}, sending to port {self.output_port}"
        )

    async def stop(self) -> None:
        """Stop the OSC server."""
        await self.server.stop()
        logger.info("VRChat OSC interface stopped")

    def _handle_avatar_change(self, address: str, avatar_id: str) -> None:
        """Handle avatar change events.

        Args:
            address: OSC address (should be "/avatar/change")
            avatar_id: The ID of the new avatar
        """
        logger.info(f"Avatar changed to: {avatar_id}")
        self.avatar_id = avatar_id

        # Try to load avatar config
        self._load_avatar_config()

        # Notify any registered callbacks
        if self.avatar_change_callback:
            self.avatar_change_callback(avatar_id)

    def _handle_avatar_parameter(self, address: str, *args) -> None:
        """Handle avatar parameter updates.

        Args:
            address: OSC address (e.g., "/avatar/parameters/ParameterName")
            *args: Parameter value(s)
        """
        # Extract parameter name from address
        param_name = address.rsplit("/", maxsplit=1)[-1]

        # Get the value (OSC messages can have multiple args, but VRChat sends single values)
        value = args[0] if args else None

        logger.debug(f"Parameter '{param_name}' updated: {value}")

        # Update local parameter cache
        if param_name in self.avatar_parameters:
            self.avatar_parameters[param_name]["value"] = value

        # Call registered callbacks
        if param_name in self.parameter_callbacks:
            for callback in self.parameter_callbacks[param_name]:
                try:
                    callback(param_name, value)
                except Exception as e:
                    logger.error(f"Error in parameter callback for '{param_name}': {e}")

    def _load_avatar_config(self) -> None:
        """Load the OSC config for the current avatar."""
        if not self.avatar_id:
            return

        # Default config path: %AppData%\..\LocalLow\VRChat\VRChat\OSC\{user_id}\Avatars\{avatar_id}.json
        app_data = os.getenv("LOCALAPPDATA")
        if not app_data:
            logger.warning("Could not determine AppData directory")
            return

        # This is a simplified example - in a real implementation, you'd need to know the user ID
        # and handle the actual config file loading
        config_dir = Path(app_data).parent / "LocalLow" / "VRChat" / "VRChat" / "OSC"

        # For now, we'll just log that we'd try to load the config
        logger.info(f"Would load avatar config from: {config_dir}/<user_id>/Avatars/{self.avatar_id}.json")

    def on_avatar_change(self, callback: Callable[[str], None]) -> None:
        """Register a callback for avatar change events.

        Args:
            callback: Function that takes an avatar ID string
        """
        self.avatar_change_callback = callback

    def on_parameter_change(self, param_name: str, callback: Callable[[str, Any], None]) -> None:
        """Register a callback for parameter changes.

        Args:
            param_name: Name of the parameter to watch
            callback: Function that takes (parameter_name, new_value)
        """
        if param_name not in self.parameter_callbacks:
            self.parameter_callbacks[param_name] = []
        self.parameter_callbacks[param_name].append(callback)

    def set_parameter(self, param_name: str, value: float | bool) -> None:
        """Set an avatar parameter in VRChat.

        Args:
            param_name: Name of the parameter to set
            value: New value for the parameter
        """
        address = f"/avatar/parameters/{param_name}"

        # Determine the appropriate OSC type
        if isinstance(value, bool):
            self.client.send(address, 1 if value else 0)
        else:
            self.client.send(address, value)

        logger.debug(f"Set parameter '{param_name}' to {value}")

    def send_chat_message(self, message: str) -> None:
        """Send a chat message to VRChat.

        Args:
            message: The message to send
        """
        self.client.send("/chatbox/input", message, True, False)
        logger.info(f"Sent chat message: {message}")

    def trigger_haptic(
        self,
        device: str,
        duration: float = 0.1,
        amplitude: float = 0.5,
        frequency: float = 0.0,
    ) -> None:
        """Trigger haptic feedback on a device.

        NOT VERIFIED: VRChat has no universal, documented OSC address for
        controller haptics - `/avatar/parameters/LeftHaptic`/`RightHaptic`
        below are not part of VRChat's real, documented OSC protocol (there
        is no such thing as a universal haptic parameter; real haptic
        feedback is driven per-avatar, through Contact Receivers/PhysBones
        the avatar creator defines, which this class has no way to know in
        advance). Treat this as speculative and likely a silent no-op
        against a real VRChat install unless the target avatar happens to
        define parameters with these exact names.

        Args:
            device: Device to trigger haptics on ('left', 'right', or 'both')
            duration: Duration of the haptic pulse in seconds (0.0-1.0)
            amplitude: Strength of the haptic (0.0-1.0)
            frequency: Frequency of the haptic (0.0-1.0)
        """
        # Clamp values to valid ranges
        duration = max(0.0, min(1.0, duration))
        amplitude = max(0.0, min(1.0, amplitude))
        frequency = max(0.0, min(1.0, frequency))

        # Send the appropriate OSC message based on device
        if device.lower() in ("left", "both"):
            self.client.send("/avatar/parameters/LeftHaptic", [duration, amplitude, frequency])
        if device.lower() in ("right", "both"):
            self.client.send("/avatar/parameters/RightHaptic", [duration, amplitude, frequency])


# Example usage
async def example_usage():
    """Example of using the VRChatOSC class."""
    import asyncio

    # Create VRChat OSC interface
    vrchat = VRChatOSC()

    # Define callbacks
    def on_avatar_changed(avatar_id):
        logger.info(f"Avatar changed to: {avatar_id}")

    def on_parameter_changed(param_name, value):
        logger.info(f"Parameter '{param_name}' changed to: {value}")

    # Register callbacks
    vrchat.on_avatar_change(on_avatar_changed)
    vrchat.on_parameter_change("VelocityX", on_parameter_changed)
    vrchat.on_parameter_change("VelocityZ", on_parameter_changed)

    try:
        # Start the OSC server
        await vrchat.start()

        # Main loop
        while True:
            # Example: Send some test parameters
            vrchat.set_parameter("TestParam", 1.0)
            await asyncio.sleep(5)

    except KeyboardInterrupt:
        logger.info("Stopping...")
    finally:
        await vrchat.stop()


if __name__ == "__main__":
    import asyncio

    asyncio.run(example_usage())

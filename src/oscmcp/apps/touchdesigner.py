"""TouchDesigner integration for OSC-MCP.

This module provides integration with TouchDesigner's OSC protocol, enabling
bidirectional communication for interactive media and visual programming.
"""

import logging
from typing import Dict, List, Callable, Any

from ..osc.client import OSCClient
from ..osc.server import OSCServer

logger = logging.getLogger(__name__)


class TouchDesignerOSC:
    """Main class for TouchDesigner OSC integration.

    Handles both sending and receiving OSC messages to/from TouchDesigner.
    """

    DEFAULT_PORT = 10000  # Default TouchDesigner OSC port

    def __init__(
        self,
        host: str = "127.0.0.1",
        listen_port: int = DEFAULT_PORT,
        target_port: int = DEFAULT_PORT,
    ):
        """Initialize the TouchDesigner OSC interface.

        Args:
            host: Host where TouchDesigner is running
            listen_port: Port to receive OSC messages from TouchDesigner
            target_port: Port to send OSC messages to TouchDesigner
        """
        self.host = host
        self.listen_port = listen_port
        self.target_port = target_port

        # OSC client for sending to TouchDesigner
        self.client = OSCClient(host, target_port)

        # OSC server for receiving from TouchDesigner
        self.server = OSCServer(host, listen_port)

        # Callback storage
        self.callbacks: Dict[str, List[Callable[[str, Any], None]]] = {}

        # Register default handlers
        self._register_default_handlers()

    def _register_default_handlers(self) -> None:
        """Register default OSC message handlers."""
        # Default handler for all messages
        self.server.dispatcher.set_default_handler(self._handle_message)

    async def start(self) -> None:
        """Start the OSC server to receive messages from TouchDesigner."""
        await self.server.start()
        logger.info(
            f"TouchDesigner OSC interface started. Listening on port {self.listen_port}, sending to port {self.target_port}"
        )

    async def stop(self) -> None:
        """Stop the OSC server."""
        await self.server.stop()
        logger.info("TouchDesigner OSC interface stopped")

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

        # Also trigger callbacks for parent paths
        parts = address.split("/")
        for i in range(1, len(parts)):
            parent_path = "/".join(parts[: i + 1])
            self._trigger_callbacks(parent_path, args)

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

    def send(self, address: str, *args) -> None:
        """Send an OSC message to TouchDesigner.

        Args:
            address: OSC address pattern
            *args: Values to send (will be converted to appropriate OSC types)
        """
        # Ensure address starts with a slash
        if not address.startswith("/"):
            address = "/" + address

        self.client.send(address, *args)
        logger.debug(f"Sent OSC message: {address} {args}")

    # Common TouchDesigner operations

    def set_parameter(self, component_path: str, parameter: str, value: Any) -> None:
        """Set a parameter value in TouchDesigner.

        Args:
            component_path: Path to the component (e.g., '/project1/constant1')
            parameter: Parameter name (e.g., 'value1')
            value: New value for the parameter
        """
        address = f"{component_path}/{parameter}"
        self.send(address, value)

    def pulse(self, component_path: str, pulse_name: str = "pulse") -> None:
        """Trigger a pulse parameter in TouchDesigner.

        Args:
            component_path: Path to the component (e.g., '/project1/button1')
            pulse_name: Name of the pulse parameter (default: 'pulse')
        """
        self.set_parameter(component_path, pulse_name, 1)

    def get_channel(self, channel_path: str) -> None:
        """Request a channel value from TouchDesigner.

        Args:
            channel_path: Path to the channel (e.g., '/project1/chop1/chan1')
        """
        self.send(channel_path)

    # Convenience methods for common components

    def set_constant(self, component_path: str, value: Any) -> None:
        """Set the value of a constant component.

        Args:
            component_path: Path to the constant component
            value: New value for the constant
        """
        self.set_parameter(component_path, "value1", value)

    def set_slider(self, component_path: str, value: float) -> None:
        """Set the value of a slider component.

        Args:
            component_path: Path to the slider component
            value: New value for the slider
        """
        self.set_parameter(component_path, "value", value)

    def trigger_button(self, component_path: str) -> None:
        """Trigger a button component.

        Args:
            component_path: Path to the button component
        """
        self.pulse(component_path)


# Example usage
async def example_usage():
    """Example of using the TouchDesignerOSC class."""
    import asyncio

    # Create TouchDesigner OSC interface
    td = TouchDesignerOSC()

    # Define callbacks
    def on_parameter_changed(address, value):
        print(f"Parameter '{address}' changed to: {value}")

    # Register callbacks
    td.on_message("/project1/constant1", on_parameter_changed)

    try:
        # Start the OSC server
        await td.start()

        # Main loop
        while True:
            # Example: Send some test parameters
            td.set_constant("/project1/constant1", 0.5)
            td.trigger_button("/project1/button1")

            # Wait for a bit
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        print("Stopping...")
    finally:
        await td.stop()


if __name__ == "__main__":
    import asyncio

    asyncio.run(example_usage())

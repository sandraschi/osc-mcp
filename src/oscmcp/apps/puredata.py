"""Pure Data integration for OSC-MCP.

This module provides integration with Pure Data's OSC protocol, enabling
bidirectional communication for audio processing and multimedia.
"""

import logging
import asyncio
from typing import Dict, List, Callable, Any

from ..osc.client import OSCClient
from ..osc.server import OSCServer

logger = logging.getLogger(__name__)


class PureDataOSC:
    """Main class for Pure Data OSC integration.

    Handles both sending and receiving OSC messages to/from Pure Data.
    """

    DEFAULT_PORT = 3000  # Default Pure Data OSC port

    def __init__(
        self,
        host: str = "127.0.0.1",
        listen_port: int = DEFAULT_PORT + 1,
        target_port: int = DEFAULT_PORT,
    ):
        """Initialize the Pure Data OSC interface.

        Args:
            host: Host where Pure Data is running
            listen_port: Port to receive OSC messages from Pure Data
            target_port: Port to send OSC messages to Pure Data
        """
        self.host = host
        self.listen_port = listen_port
        self.target_port = target_port

        # OSC client for sending to Pure Data
        self.client = OSCClient(host, target_port)

        # OSC server for receiving from Pure Data
        self.server = OSCServer(host, listen_port)

        # Callback storage
        self.callbacks: Dict[str, List[Callable[[str, Any], None]]] = {}
        self.message_callbacks: List[Callable[[str, list], None]] = []

        # Register default handlers
        self._register_default_handlers()

    def _register_default_handlers(self) -> None:
        """Register default OSC message handlers."""
        # Default handler for all messages
        self.server.dispatcher.set_default_handler(self._handle_message)

    async def start(self) -> None:
        """Start the OSC server to receive messages from Pure Data."""
        await self.server.start()
        logger.info(
            f"Pure Data OSC interface started. Listening on port {self.listen_port}, sending to port {self.target_port}"
        )

    async def stop(self) -> None:
        """Stop the OSC server."""
        await self.server.stop()
        logger.info("Pure Data OSC interface stopped")

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

        # Also trigger message callbacks
        for callback in self.message_callbacks:
            try:
                callback(address, list(args))
            except Exception as e:
                logger.error(f"Error in message callback: {e}")

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

    def on_all_messages(self, callback: Callable[[str, list], None]) -> None:
        """Register a callback for all OSC messages.

        Args:
            callback: Function that takes (address, args) as arguments
        """
        self.message_callbacks.append(callback)

    # Pure Data specific methods

    def send(self, address: str, *args) -> None:
        """Send an OSC message to Pure Data.

        Args:
            address: OSC address pattern
            *args: Values to send
        """
        # Ensure address starts with a slash
        if not address.startswith("/"):
            address = "/" + address

        self.client.send(address, *args)
        logger.debug(f"Sent OSC message: {address} {args}")

    # Common Pure Data operations

    def send_bang(self, receiver: str) -> None:
        """Send a bang to a Pure Data receiver.

        Args:
            receiver: Name of the Pure Data receiver (e.g., 'myReceiver')
        """
        self.send(f"/{receiver}", "bang")

    def send_float(self, receiver: str, value: float) -> None:
        """Send a float value to a Pure Data receiver.

        Args:
            receiver: Name of the Pure Data receiver
            value: Float value to send
        """
        self.send(f"/{receiver}", float(value))

    def send_symbol(self, receiver: str, symbol: str) -> None:
        """Send a symbol to a Pure Data receiver.

        Args:
            receiver: Name of the Pure Data receiver
            symbol: Symbol to send
        """
        self.send(f"/{receiver}", symbol)

    def send_list(self, receiver: str, *items) -> None:
        """Send a list of values to a Pure Data receiver.

        Args:
            receiver: Name of the Pure Data receiver
            *items: Items to send in the list
        """
        self.send(f"/{receiver}", *items)

    def send_message(self, receiver: str, selector: str, *args) -> None:
        """Send a message to a Pure Data receiver.

        Args:
            receiver: Name of the Pure Data receiver
            selector: Message selector (e.g., 'set', 'open', 'start')
            *args: Message arguments
        """
        self.send(f"/{receiver}", selector, *args)

    # Audio control

    def dsp_on(self) -> None:
        """Turn DSP processing on."""
        self.send("/pd/dsp", 1)

    def dsp_off(self) -> None:
        """Turn DSP processing off."""
        self.send("/pd/dsp", 0)

    def toggle_dsp(self) -> None:
        """Toggle DSP processing on/off."""
        self.send("/pd/dsp/toggle")

    # File operations

    def open_patch(self, filename: str, directory: str = "") -> None:
        """Open a Pure Data patch.

        Args:
            filename: Name of the patch file
            directory: Optional directory containing the patch
        """
        if directory:
            self.send("/pd/open", f"{directory}/{filename}")
        else:
            self.send("/pd/open", filename)

    def close_patch(self, filename: str) -> None:
        """Close a Pure Data patch.

        Args:
            filename: Name of the patch file to close
        """
        self.send("/pd/close", filename)


# Example usage
async def example_usage():
    """Example of using the PureDataOSC class."""
    import asyncio

    # Create Pure Data controller
    pd = PureDataOSC()

    # Define callbacks
    def on_parameter_changed(address, value):
        print(f"Parameter '{address}' changed to: {value}")

    def on_any_message(address, args):
        print(f"Received message: {address} {args}")

    # Register callbacks
    pd.on_message("/test", on_parameter_changed)
    pd.on_all_messages(on_any_message)

    try:
        # Start the OSC server
        await pd.start()

        # Main loop
        while True:
            # Example: Send test messages
            pd.send_bang("test")
            pd.send_float("frequency", 440.0)
            pd.send_list("data", 1, 2, 3, 4, 5)

            # Wait for a bit
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        print("Stopping...")
    finally:
        await pd.stop()


if __name__ == "__main__":
    import asyncio

    asyncio.run(example_usage())

"""Max/MSP integration for OSC-MCP.

This module provides integration with Max/MSP's OSC protocol, enabling
bidirectional communication for music and multimedia applications.
"""

import asyncio
import logging
from typing import Any, Callable, Dict, List

from ..osc.client import OSCClient
from ..osc.server import OSCServer

logger = logging.getLogger(__name__)


class MaxMSPOSC:
    """Main class for Max/MSP OSC integration.

    Handles both sending and receiving OSC messages to/from Max/MSP.
    """

    DEFAULT_PORT = 4000  # Default Max/MSP OSC port

    def __init__(
        self,
        host: str = "127.0.0.1",
        listen_port: int = DEFAULT_PORT + 1,
        target_port: int = DEFAULT_PORT,
    ):
        """Initialize the Max/MSP OSC interface.

        Args:
            host: Host where Max/MSP is running
            listen_port: Port to receive OSC messages from Max/MSP
            target_port: Port to send OSC messages to Max/MSP
        """
        self.host = host
        self.listen_port = listen_port
        self.target_port = target_port

        # OSC client for sending to Max/MSP
        self.client = OSCClient(host, target_port)

        # OSC server for receiving from Max/MSP
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
        """Start the OSC server to receive messages from Max/MSP."""
        await self.server.start()
        logger.info(
            f"Max/MSP OSC interface started. Listening on port {self.listen_port}, sending to port {self.target_port}"
        )

    async def stop(self) -> None:
        """Stop the OSC server."""
        await self.server.stop()
        logger.info("Max/MSP OSC interface stopped")

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

    # Max/MSP specific methods

    def send(self, address: str, *args) -> None:
        """Send an OSC message to Max/MSP.

        Args:
            address: OSC address pattern
            *args: Values to send
        """
        # Ensure address starts with a slash
        if not address.startswith("/"):
            address = "/" + address

        self.client.send(address, *args)
        logger.debug(f"Sent OSC message: {address} {args}")

    # Common Max/MSP operations

    def send_bang(self, receiver: str) -> None:
        """Send a bang to a Max/MSP receiver.

        Args:
            receiver: Name of the Max/MSP receiver (e.g., 'myReceiver')
        """
        self.send(f"/{receiver}", "bang")

    def send_float(self, receiver: str, value: float) -> None:
        """Send a float value to a Max/MSP receiver.

        Args:
            receiver: Name of the Max/MSP receiver
            value: Float value to send
        """
        self.send(f"/{receiver}", float(value))

    def send_int(self, receiver: str, value: int) -> None:
        """Send an integer value to a Max/MSP receiver.

        Args:
            receiver: Name of the Max/MSP receiver
            value: Integer value to send
        """
        self.send(f"/{receiver}", int(value))

    def send_symbol(self, receiver: str, symbol: str) -> None:
        """Send a symbol to a Max/MSP receiver.

        Args:
            receiver: Name of the Max/MSP receiver
            symbol: Symbol to send
        """
        self.send(f"/{receiver}", symbol)

    def send_list(self, receiver: str, *items) -> None:
        """Send a list of values to a Max/MSP receiver.

        Args:
            receiver: Name of the Max/MSP receiver
            *items: Items to send in the list
        """
        self.send(f"/{receiver}", *items)

    # Patch control

    def load_patch(self, patch_path: str) -> None:
        """Load a Max/MSP patch.

        Args:
            patch_path: Path to the Max patch file (.maxpat)
        """
        self.send("/max/load", patch_path)

    def close_patch(self, patch_path: str) -> None:
        """Close a Max/MSP patch.

        Args:
            patch_path: Path to the Max patch file (.maxpat)
        """
        self.send("/max/close", patch_path)

    def start_dsp(self) -> None:
        """Start the DSP (audio processing)."""
        self.send("/dsp", 1)

    def stop_dsp(self) -> None:
        """Stop the DSP (audio processing)."""
        self.send("/dsp", 0)

    def toggle_dsp(self) -> None:
        """Toggle the DSP (audio processing) on/off."""
        self.send("/dsp/toggle")

    # Transport control

    def play(self) -> None:
        """Start transport."""
        self.send("/transport/play")

    def stop_transport(self) -> None:
        """Stop transport."""
        self.send("/transport/stop")

    def pause(self) -> None:
        """Pause transport."""
        self.send("/transport/pause")

    def set_tempo(self, bpm: float) -> None:
        """Set the tempo in BPM.

        Args:
            bpm: Beats per minute
        """
        self.send("/transport/tempo", float(bpm))

    def set_time_signature(self, numerator: int, denominator: int) -> None:
        """Set the time signature.

        Args:
            numerator: Time signature numerator (e.g., 3 for 3/4)
            denominator: Time signature denominator (e.g., 4 for 3/4)
        """
        self.send("/transport/timesig", int(numerator), int(denominator))

    # UI control

    def set_ui_visible(self, visible: bool = True) -> None:
        """Show or hide the Max/MSP UI.

        Args:
            visible: Whether to show the UI
        """
        self.send("/max/ui/visible", 1 if visible else 0)

    def set_fullscreen(self, fullscreen: bool = True) -> None:
        """Set fullscreen mode.

        Args:
            fullscreen: Whether to enable fullscreen mode
        """
        self.send("/max/fullscreen", 1 if fullscreen else 0)


# Example usage
async def example_usage():
    """Example of using the MaxMSPOSC class."""
    import asyncio

    # Create Max/MSP controller
    maxmsp = MaxMSPOSC()

    # Define callbacks
    def on_parameter_changed(address, value):
        print(f"Parameter '{address}' changed to: {value}")

    def on_any_message(address, args):
        print(f"Received message: {address} {args}")

    # Register callbacks
    maxmsp.on_message("/test", on_parameter_changed)
    maxmsp.on_all_messages(on_any_message)

    try:
        # Start the OSC server
        await maxmsp.start()

        # Load a patch
        print("Loading patch...")
        maxmsp.load_patch("/path/to/patch.maxpat")

        # Start DSP
        print("Starting DSP...")
        maxmsp.start_dsp()

        # Send some test messages
        print("Sending test messages...")
        maxmsp.send_float("frequency", 440.0)
        maxmsp.send_bang("trigger")

        # Let it run for a bit
        await asyncio.sleep(5)

        # Change some parameters
        print("Updating parameters...")
        maxmsp.send_float("frequency", 880.0)
        maxmsp.send_float("amp", 0.7)

        # Wait a bit more
        await asyncio.sleep(3)

        # Stop DSP
        print("Stopping DSP...")
        maxmsp.stop_dsp()

    except KeyboardInterrupt:
        print("Stopping...")
    finally:
        await maxmsp.stop()


if __name__ == "__main__":
    import asyncio

    asyncio.run(example_usage())

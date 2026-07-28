"""SuperCollider integration for OSC-MCP.

This module provides integration with SuperCollider's OSC protocol, enabling
bidirectional communication for audio synthesis and algorithmic composition.
"""

import asyncio
import logging
from collections.abc import Callable
from typing import Any

from ..osc.client import OSCClient
from ..osc.server import OSCServer

logger = logging.getLogger(__name__)


class SuperColliderOSC:
    """Main class for SuperCollider OSC integration.

    Handles both sending and receiving OSC messages to/from SuperCollider.
    """

    DEFAULT_PORT = 57120  # Default SuperCollider OSC port
    NOTIFICATION_PORT = 57121  # Default port for notifications

    def __init__(
        self,
        host: str = "127.0.0.1",
        listen_port: int = NOTIFICATION_PORT,
        target_port: int = DEFAULT_PORT,
    ):
        """Initialize the SuperCollider OSC interface.

        Args:
            host: Host where SuperCollider is running
            listen_port: Port to receive OSC messages from SuperCollider
            target_port: Port to send OSC messages to SuperCollider
        """
        self.host = host
        self.listen_port = listen_port
        self.target_port = target_port

        # OSC client for sending to SuperCollider
        self.client = OSCClient(host, target_port)

        # OSC server for receiving from SuperCollider
        self.server = OSCServer(host, listen_port)

        # Callback storage
        self.callbacks: dict[str, list[Callable[[str, Any], None]]] = {}
        self.def_receive_callbacks: list[Callable[[str, list], None]] = []
        self.status_callbacks: list[Callable[[dict], None]] = []

        # Register default handlers
        self._register_default_handlers()

    def _register_default_handlers(self) -> None:
        """Register default OSC message handlers."""
        # Default handler for /done messages
        self.server.dispatcher.map("/done", self._handle_done_message)
        # Handler for /status.reply
        self.server.dispatcher.map("/status.reply", self._handle_status_reply)
        # Handler for /n_go, /n_end, /n_on, /n_off, etc.
        self.server.dispatcher.map("/n_*", self._handle_node_message)
        # Handler for /c_set, /c_setn, /c_fill, etc.
        self.server.dispatcher.map("/c_*", self._handle_control_message)
        # Handler for /tr (trigger)
        self.server.dispatcher.map("/tr", self._handle_trigger_message)
        # Default handler for all other messages
        self.server.dispatcher.set_default_handler(self._handle_generic_message)

    async def start(self) -> None:
        """Start the OSC server to receive messages from SuperCollider."""
        await self.server.start()
        logger.info(
            f"SuperCollider OSC interface started. Listening on port {self.listen_port}, sending to port {self.target_port}"
        )

        # Notify SuperCollider that we want to receive notifications
        self.notify(1)

    async def stop(self) -> None:
        """Stop the OSC server and clean up."""
        # Tell SuperCollider to stop sending notifications
        self.notify(0)

        # Stop the server
        await self.server.stop()
        logger.info("SuperCollider OSC interface stopped")

    # Message handling methods

    def _handle_done_message(self, address: str, *args) -> None:
        """Handle /done messages from SuperCollider."""
        if len(args) >= 2 and args[0] == "/b_allocRead":
            # Buffer allocation complete
            bufnum = args[1]
            logger.debug(f"Buffer {bufnum} loaded")
            self._trigger_callbacks(f"/done/b_allocRead/{bufnum}", args[2:])

    def _handle_status_reply(self, address: str, *args) -> None:
        """Handle /status.reply messages from SuperCollider."""
        if len(args) >= 11:
            status = {
                "ugen_count": args[0],
                "synth_count": args[1],
                "group_count": args[2],
                "def_count": args[3],
                "avg_cpu_peak": args[4],
                "avg_cpu_peak_ratio": args[5],
                "sample_rate_nominal": args[6],
                "sample_rate_actual": args[7],
                "synced": bool(args[8]),
            }

            # Trigger status callbacks
            for callback in self.status_callbacks:
                try:
                    callback(status)
                except Exception as e:
                    logger.error(f"Error in status callback: {e}")

    def _handle_node_message(self, address: str, *args) -> None:
        """Handle node-related messages from SuperCollider."""
        # Examples: /n_go, /n_end, /n_on, /n_off, /n_move, /n_info
        self._trigger_callbacks(address, args)

    def _handle_control_message(self, address: str, *args) -> None:
        """Handle control bus messages from SuperCollider."""
        # Examples: /c_set, /c_setn, /c_fill
        self._trigger_callbacks(address, args)

    def _handle_trigger_message(self, address: str, *args) -> None:
        """Handle trigger messages from SuperCollider."""
        # /tr message format: [node_id, trigger_id, value]
        if len(args) >= 3:
            node_id, trigger_id, value = args[:3]
            self._trigger_callbacks(f"/tr/{node_id}/{trigger_id}", value)

    def _handle_generic_message(self, address: str, *args) -> None:
        """Handle all other OSC messages from SuperCollider."""
        logger.debug(f"Received OSC message: {address} {args}")
        self._trigger_callbacks(address, args)

    def _trigger_callbacks(self, address: str, args: tuple) -> None:
        """Trigger callbacks for a specific address."""
        # Call specific callbacks for this address
        if address in self.callbacks:
            for callback in self.callbacks[address]:
                try:
                    callback(address, args[0] if len(args) == 1 else args)
                except Exception as e:
                    logger.error(f"Error in callback for '{address}': {e}")

        # Call default receive callbacks
        for callback in self.def_receive_callbacks:
            try:
                callback(address, list(args))
            except Exception as e:
                logger.error(f"Error in default receive callback: {e}")

    # Callback registration

    def on_message(self, address: str, callback: Callable[[str, Any], None]) -> None:
        """Register a callback for messages to a specific address."""
        if not address.startswith("/"):
            address = "/" + address

        if address not in self.callbacks:
            self.callbacks[address] = []

        self.callbacks[address].append(callback)

    def on_receive(self, callback: Callable[[str, list], None]) -> None:
        """Register a callback for all incoming OSC messages."""
        self.def_receive_callbacks.append(callback)

    def on_status(self, callback: Callable[[dict], None]) -> None:
        """Register a callback for server status updates."""
        self.status_callbacks.append(callback)

    # Server control

    def notify(self, enabled: bool = True) -> None:
        """Enable or disable server notifications."""
        self.send("/notify", 1 if enabled else 0)

    def status(self) -> None:
        """Request server status."""
        self.send("/status")

    def dump_osc(self, enabled: bool = True) -> None:
        """Enable or disable OSC dump mode."""
        self.send("/dumpOSC", 1 if enabled else 0)

    def clear_sched(self) -> None:
        """Clear all scheduled bundles."""
        self.send("/clearSched")

    # Node control

    def s_new(
        self,
        defname: str,
        node_id: int = -1,
        add_action: int = 0,
        target: int = 1,
        **args,
    ) -> None:
        """Create a new synth node."""
        # Convert args to a flat list of [key1, value1, key2, value2, ...]
        arg_list = []
        for k, v in args.items():
            arg_list.extend([str(k), v])

        self.send("/s_new", defname, node_id, add_action, target, *arg_list)

    def n_free(self, *node_ids: int) -> None:
        """Free one or more nodes."""
        for node_id in node_ids:
            self.send("/n_free", node_id)

    def n_run(self, node_id: int, run: bool = True) -> None:
        """Run or pause a node."""
        self.send("/n_run", node_id, 1 if run else 0)

    def n_set(self, node_id: int, **args) -> None:
        """Set node controls."""
        # Convert args to a flat list of [key1, value1, key2, value2, ...]
        arg_list = []
        for k, v in args.items():
            arg_list.extend([str(k), v])

        self.send("/n_set", node_id, *arg_list)

    # Buffer operations

    def b_alloc(self, bufnum: int, num_frames: int, num_chans: int = 1) -> None:
        """Allocate a buffer."""
        self.send("/b_alloc", bufnum, num_frames, num_chans)

    def b_alloc_read(self, bufnum: int, path: str, start_frame: int = 0, num_frames: int = -1) -> None:
        """Allocate and read a sound file into a buffer."""
        self.send("/b_allocRead", bufnum, path, start_frame, num_frames)

    def b_free(self, bufnum: int) -> None:
        """Free a buffer."""
        self.send("/b_free", bufnum)

    def b_zero(self, bufnum: int) -> None:
        """Zero all samples in a buffer."""
        self.send("/b_zero", bufnum)

    # Group control

    def g_new(self, group_id: int, add_action: int = 0, target: int = 0) -> None:
        """Create a new group."""
        self.send("/g_new", group_id, add_action, target)

    def g_free_all(self, group_id: int) -> None:
        """Free all nodes in a group."""
        self.send("/g_freeAll", group_id)

    def g_deep_free(self, group_id: int) -> None:
        """Free all nodes in a group and all its sub-groups."""
        self.send("/g_deepFree", group_id)

    # Sending arbitrary OSC messages

    def send(self, address: str, *args) -> None:
        """Send an OSC message to SuperCollider."""
        if not address.startswith("/"):
            address = "/" + address

        self.client.send(address, *args)
        logger.debug(f"Sent OSC message: {address} {args}")

    # Convenience methods for common operations

    def play_synth(self, defname: str, **args) -> int:
        """Play a synth and return its node ID."""
        # Generate a negative node ID for the server to replace
        import random

        node_id = -random.randint(1000, 9999)
        self.s_new(defname, node_id=node_id, **args)
        return node_id

    def set_control(self, node_id: int, **controls) -> None:
        """Set multiple controls on a node."""
        self.n_set(node_id, **controls)

    def load_sound(self, path: str, bufnum: int | None = None) -> int:
        """Load a sound file into a buffer and return the buffer number."""
        if bufnum is None:
            import random

            bufnum = random.randint(1000, 1999)

        self.b_alloc_read(bufnum, path)
        return bufnum


# Example usage
async def example_usage():
    """Example of using the SuperColliderOSC class."""
    import asyncio

    # Create SuperCollider controller
    sc = SuperColliderOSC()

    # Define callbacks
    def on_status(status):
        logger.info(f"SuperCollider status: {status['synth_count']} synths, CPU: {status['avg_cpu_peak']:.1f}%")

    def on_message(address, args):
        logger.info(f"Received message: {address} {args}")

    # Register callbacks
    sc.on_status(on_status)
    sc.on_receive(on_message)

    try:
        # Start the OSC server
        await sc.start()

        # Request status updates every 2 seconds
        async def status_loop():
            while True:
                sc.status()
                await asyncio.sleep(2)

        # Start the status loop
        asyncio.create_task(status_loop())

        # Example: Load a sound and play it
        logger.info("Loading sound...")
        bufnum = sc.load_sound("/path/to/sound.wav")

        # Wait a bit for the sound to load
        await asyncio.sleep(1)

        # Play the sound
        logger.info("Playing sound...")
        node_id = sc.play_synth("default", out=0, bufnum=bufnum, amp=0.5)

        # Let it play for a bit
        await asyncio.sleep(5)

        # Change the amplitude
        logger.info("Changing amplitude...")
        sc.set_control(node_id, amp=0.2)

        # Wait a bit more
        await asyncio.sleep(3)

        # Stop the sound
        logger.info("Stopping sound...")
        sc.n_free(node_id)

        # Free the buffer
        sc.b_free(bufnum)

        # Keep running until interrupted
        await asyncio.Future()

    except KeyboardInterrupt:
        logger.info("Stopping...")
    finally:
        await sc.stop()


if __name__ == "__main__":
    import asyncio

    asyncio.run(example_usage())

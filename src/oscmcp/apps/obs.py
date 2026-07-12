"""OBS Studio integration for OSC-MCP.

This module provides integration with OBS Studio using OSC.
"""

import logging

from ..osc.client import OSCClient

logger = logging.getLogger(__name__)


class OBSOSC:
    """Control OBS Studio using OSC."""

    DEFAULT_PORT = 7000  # Default OSC port for OBS Studio via typical plugins

    def __init__(self, host: str = "127.0.0.1", port: int = DEFAULT_PORT):
        """Initialize the OBS Studio controller.

        Args:
            host: Host where OBS Studio is running
            port: OSC port for OBS Studio (default: 7000)
        """
        self.host = host
        self.port = port
        self.osc_client = OSCClient(host, port)

    def switch_scene(self, scene_name: str) -> None:
        """Switch active scene in OBS Studio.

        Args:
            scene_name: Name of the scene to switch to
        """
        self.osc_client.send("/scene", scene_name)
        logger.info(f"Sent switch scene command for '{scene_name}' to OBS Studio")

    def toggle_mute(self, source_name: str) -> None:
        """Toggle mute status of a source.

        Args:
            source_name: Name of the audio source
        """
        self.osc_client.send("/mute", source_name)
        logger.info(f"Sent toggle mute command for '{source_name}' to OBS Studio")

    def set_volume(self, source_name: str, volume: float) -> None:
        """Set the volume level of a source.

        Args:
            source_name: Name of the audio source
            volume: Volume level (0.0 to 1.0)
        """
        self.osc_client.send("/volume", source_name, volume)
        logger.info(f"Set volume of '{source_name}' to {volume} in OBS Studio")

    def start_stream(self) -> None:
        """Start streaming in OBS Studio."""
        self.osc_client.send("/stream/start")
        logger.info("Sent start stream command to OBS Studio")

    def stop_stream(self) -> None:
        """Stop streaming in OBS Studio."""
        self.osc_client.send("/stream/stop")
        logger.info("Sent stop stream command to OBS Studio")

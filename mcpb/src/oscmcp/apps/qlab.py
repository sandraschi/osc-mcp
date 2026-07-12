"""QLab integration for OSC-MCP.

This module provides integration with Figure 53 QLab using OSC.
"""

import logging

from ..osc.client import OSCClient

logger = logging.getLogger(__name__)


class QLabOSC:
    """Control QLab using OSC."""

    DEFAULT_PORT = 53000  # Default OSC port for QLab

    def __init__(self, host: str = "127.0.0.1", port: int = DEFAULT_PORT):
        """Initialize the QLab controller.

        Args:
            host: Host where QLab is running
            port: OSC port for QLab (default: 53000)
        """
        self.host = host
        self.port = port
        self.osc_client = OSCClient(host, port)

    def go(self) -> None:
        """Trigger the GO action (start next cue)."""
        self.osc_client.send("/go")
        logger.info("Sent GO command to QLab")

    def stop(self) -> None:
        """Stop all currently playing cues."""
        self.osc_client.send("/stop")
        logger.info("Sent stop command to QLab")

    def panic(self) -> None:
        """Panic all currently playing cues (fade out and stop)."""
        self.osc_client.send("/panic")
        logger.info("Sent panic command to QLab")

    def trigger_cue(self, cue_id: str) -> None:
        """Trigger a specific cue by its ID or number.

        Args:
            cue_id: Number or ID of the cue to start
        """
        self.osc_client.send(f"/cue/{cue_id}/start")
        logger.info(f"Sent trigger cue '{cue_id}' command to QLab")

    def set_slider_level(self, cue_id: str, slider_index: int, level: float) -> None:
        """Set a specific slider level for a cue.

        Args:
            cue_id: Number or ID of the cue
            slider_index: Slider index (0-based)
            level: Decibel level (typically -60.0 to 12.0)
        """
        self.osc_client.send(f"/cue/{cue_id}/sliderLevel/{slider_index}", level)
        logger.info(f"Set slider {slider_index} of cue '{cue_id}' to {level} dB in QLab")

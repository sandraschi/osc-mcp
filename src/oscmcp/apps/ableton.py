"""Ableton Live integration for OSC-MCP.

This module provides integration with Ableton Live using OSC.
"""

import logging
from typing import Dict, Any, Optional, List, Callable

from ..osc.client import OSCClient

logger = logging.getLogger(__name__)

class AbletonLive:
    """Control Ableton Live using OSC."""
    
    DEFAULT_PORT = 11000  # Default OSC port for Ableton Live
    
    def __init__(self, host: str = "127.0.0.1", port: int = DEFAULT_PORT):
        """Initialize the Ableton Live controller.
        
        Args:
            host: Host where Ableton Live is running
            port: OSC port for Ableton Live (default: 11000)
        """
        self.host = host
        self.port = port
        self.osc_client = OSCClient(host, port)
        
    def play(self) -> None:
        """Start playback in Ableton Live."""
        self.osc_client.send("/live/play")
        logger.info("Sent play command to Ableton Live")
    
    def stop(self) -> None:
        """Stop playback in Ableton Live."""
        self.osc_client.send("/live/stop")
        logger.info("Sent stop command to Ableton Live")
    
    def set_tempo(self, bpm: float) -> None:
        """Set the tempo in BPM.
        
        Args:
            bpm: Tempo in beats per minute
        """
        self.osc_client.send("/live/tempo", bpm)
        logger.info(f"Set tempo to {bpm} BPM")
    
    def play_clip(self, track_index: int, clip_slot: int) -> None:
        """Play a specific clip.
        
        Args:
            track_index: Index of the track (0-based)
            clip_slot: Index of the clip slot (0-based)
        """
        self.osc_client.send("/live/clip/fire", track_index, clip_slot)
        logger.info(f"Playing clip: track {track_index}, slot {clip_slot}")
    
    def stop_clip(self, track_index: int, clip_slot: int) -> None:
        """Stop a specific clip.
        
        Args:
            track_index: Index of the track (0-based)
            clip_slot: Index of the clip slot (0-based)
        """
        self.osc_client.send("/live/clip/stop", track_index, clip_slot)
        logger.info(f"Stopped clip: track {track_index}, slot {clip_slot}")
    
    def set_volume(self, track_index: int, volume: float) -> None:
        """Set the volume of a track.
        
        Args:
            track_index: Index of the track (0-based)
            volume: Volume level (0.0 to 1.0)
        """
        self.osc_client.send("/live/track/set/volume", track_index, volume)
        logger.info(f"Set track {track_index} volume to {volume}")
    
    def set_pan(self, track_index: int, pan: float) -> None:
        """Set the pan of a track.
        
        Args:
            track_index: Index of the track (0-based)
            pan: Pan position (-1.0 to 1.0)
        """
        self.osc_client.send("/live/track/set/panning", track_index, pan)
        logger.info(f"Set track {track_index} pan to {pan}")
    
    def set_send(self, track_index: int, send_index: int, value: float) -> None:
        """Set the send level for a track.
        
        Args:
            track_index: Index of the track (0-based)
            send_index: Index of the send (0-based)
            value: Send level (0.0 to 1.0)
        """
        self.osc_client.send("/live/track/set/send", track_index, send_index, value)
        logger.info(f"Set track {track_index} send {send_index} to {value}")

# Example usage:
if __name__ == "__main__":
    import time
    
    # Initialize Ableton Live controller
    ableton = AbletonLive()
    
    # Example: Play a clip and adjust volume
    ableton.play()
    ableton.set_volume(0, 0.8)  # Set volume of first track to 80%
    ableton.play_clip(0, 0)     # Play first clip in first track
    time.sleep(2)
    ableton.stop_clip(0, 0)     # Stop the clip
    ableton.stop()              # Stop playback

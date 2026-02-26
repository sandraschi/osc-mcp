#!/usr/bin/env python3
"""Test OSCelot with correct /fader format."""

import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from oscmcp.osc.client import OSCClient


def frequency_to_normalized(freq, max_freq=10000.0):
    """Convert frequency in Hz to normalized 0-1 range."""
    return min(max(0.0, freq / max_freq), 1.0)


async def test_fader():
    """Test /fader format for OSCelot."""
    client = OSCClient("127.0.0.1", 10001)
    client.connect()

    print("=" * 60)
    print("Testing OSCelot /fader Format")
    print("=" * 60)
    print()
    print("OSCelot expects: /fader [Id, Value]")
    print("  Id = OSC controller ID (slot number in OSCelot)")
    print("  Value = 0.0 to 1.0")
    print()
    print("If 'Frequency' is at the top of OSCelot's list, it's probably ID 1")
    print()

    # Test different IDs (1-7) since Frequency is at top
    frequencies = [261.63, 329.63, 392.00, 440.00, 523.25]  # C4, E4, G4, A4, C5
    note_names = ["C4", "E4", "G4", "A4", "C5"]

    print("Testing ID 1 (top of list = Frequency)...")
    print("Playing 5 notes:")
    print()

    for freq, name in zip(frequencies, note_names):
        normalized = frequency_to_normalized(freq)
        print(f"  {name} ({freq:.2f} Hz) = {normalized:.4f}")
        client.send("/fader", 1, normalized)
        await asyncio.sleep(0.5)

    print()
    print("Did the pitch change?")
    print()
    print("If not, try ID 0 or check which slot number Frequency is in OSCelot")


if __name__ == "__main__":
    asyncio.run(test_fader())

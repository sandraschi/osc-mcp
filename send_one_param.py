#!/usr/bin/env python3
"""Send a single OSC parameter command."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from oscmcp.osc.client import OSCClient

def frequency_to_normalized(freq, max_freq=10000.0):
    """Convert frequency in Hz to normalized 0-1 range."""
    return min(max(0.0, freq / max_freq), 1.0)

# Send one command
client = OSCClient("127.0.0.1", 10001)
client.connect()

# Set frequency to A4 (440 Hz)
freq = 440.0
normalized = frequency_to_normalized(freq)

print(f"Sending: Module 14, Parameter 1, Value {normalized:.4f} (440 Hz)")
client.send("/param", 14, 1, normalized)
print("Sent!")


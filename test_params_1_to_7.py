#!/usr/bin/env python3
"""Test parameters 1-7, one second apart."""

import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from oscmcp.osc.client import OSCClient

def frequency_to_normalized(freq, max_freq=10000.0):
    """Convert frequency in Hz to normalized 0-1 range."""
    return min(max(0.0, freq / max_freq), 1.0)

async def test_params():
    """Test parameters 1-7."""
    client = OSCClient("127.0.0.1", 10001)
    client.connect()
    
    # Test frequency: A4 (440 Hz)
    freq = 440.0
    normalized = frequency_to_normalized(freq)
    
    print("=" * 60)
    print("Testing Parameters 1-7")
    print("=" * 60)
    print(f"Setting each parameter to {normalized:.4f} (440 Hz / A4)")
    print("One second apart - listen for pitch changes!")
    print()
    
    for param_id in range(1, 8):
        print(f"Parameter {param_id}...")
        client.send("/param", 14, param_id, normalized)
        await asyncio.sleep(1.0)
    
    print()
    print("Test complete!")
    print("Which parameter changed the pitch?")

if __name__ == "__main__":
    asyncio.run(test_params())


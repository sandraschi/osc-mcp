#!/usr/bin/env python3
"""
Test cvOSCcv OSC communication.

This script tests cvOSCcv module in VCV Rack by sending OSC messages
to control CV channels.

Requirements:
- VCV Rack with cvOSCcv module installed
- cvOSCcv configured on port 10001 (default)
- cvOSCcv channels enabled and addresses set
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from oscmcp.osc.client import OSCClient


async def test_cvosccv():
    """Test cvOSCcv OSC communication."""

    print("=" * 60)
    print("cvOSCcv OSC Test")
    print("=" * 60)
    print()
    print("Prerequisites:")
    print("  1. VCV Rack running with cvOSCcv module")
    print("  2. cvOSCcv configured on port 10001")
    print("  3. At least one channel enabled in cvOSCcv")
    print()

    # Initialize OSC client
    client = OSCClient("127.0.0.1", 10001)
    client.connect()

    print("Connected to cvOSCcv on port 10001")
    print()

    try:
        # Test 1: Default channel addresses
        print("Test 1: Default channel addresses (/cv/0, /cv/1, etc.)")
        print("-" * 60)

        for channel in range(4):
            print(f"  Sending to /cv/{channel}: 0.5 (50%)")
            client.send(f"/cv/{channel}", 0.5)
            await asyncio.sleep(0.2)

        print()
        print("Did you see activity LEDs on cvOSCcv?")
        print()

        # Test 2: Custom addresses (if configured)
        print("Test 2: Custom addresses (if you configured them)")
        print("-" * 60)
        print("  Common custom addresses:")
        print("    /vco/freq - VCO frequency")
        print("    /filter/cutoff - Filter cutoff")
        print("    /vca/level - VCA level")
        print("    /lfo/rate - LFO rate")
        print()

        custom_addresses = ["/vco/freq", "/filter/cutoff", "/vca/level", "/lfo/rate"]

        for addr in custom_addresses:
            print(f"  Sending to {addr}: 0.7 (70%)")
            client.send(addr, 0.7)
            await asyncio.sleep(0.2)

        print()
        print("If you configured custom addresses, these should work.")
        print()

        # Test 3: Value sweep
        print("Test 3: Value sweep (channel 0)")
        print("-" * 60)
        print("  Sweeping /cv/0 from 0.0 to 1.0...")

        for value in [0.0, 0.25, 0.5, 0.75, 1.0]:
            print(f"    Value: {value:.2f}")
            client.send("/cv/0", value)
            await asyncio.sleep(0.3)

        print()
        print("Did the CV output change smoothly?")
        print()

        # Test 4: Multiple channels
        print("Test 4: Multiple channels simultaneously")
        print("-" * 60)

        values = [0.2, 0.4, 0.6, 0.8]
        for channel, value in enumerate(values):
            print(f"  Channel {channel}: {value:.2f}")
            client.send(f"/cv/{channel}", value)

        await asyncio.sleep(0.5)
        print()
        print("All channels should be active now.")
        print()

        print("=" * 60)
        print("Test Complete!")
        print("=" * 60)
        print()
        print("If cvOSCcv LEDs lit up and CV outputs changed,")
        print("cvOSCcv is working correctly!")
        print()
        print("Next steps:")
        print("  1. Connect cvOSCcv outputs to module CV inputs")
        print("  2. Use custom OSC addresses for better organization")
        print("  3. Update your OSC-MCP scripts to use cvOSCcv")

    except Exception as e:
        print(f"Error: {e}")
        print()
        print("Troubleshooting:")
        print("  1. Is VCV Rack running?")
        print("  2. Is cvOSCcv added to your patch?")
        print("  3. Is cvOSCcv configured on port 10001?")
        print("  4. Are channels enabled in cvOSCcv?")
        print("  5. Check Windows Firewall allows UDP port 10001")


if __name__ == "__main__":
    asyncio.run(test_cvosccv())

#!/usr/bin/env python3
"""
VCV Rack OSC Integration Demo

This script demonstrates the extended VCV Rack OSC tools added to osc-mcp.
Run this to test the new functionality with your VCV Rack setup.

Requirements:
- VCV Rack with OSC module installed (OSCelot, cvOSCcv, etc.)
- OSC module configured to listen on port 10001
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.oscmcp.osc.client import OSCClient

async def vcv_rack_demo():
    """Demonstrate VCV Rack OSC integration."""

    print("VCV Rack OSC Integration Demo")
    print("=" * 40)

    # Initialize OSC client
    client = OSCClient("127.0.0.1", 10001)
    print("Connected to VCV Rack OSC on port 10001")

    try:
        # MIDI Control Demo
        print("\nMIDI Control:")
        print("   Playing middle C (note 60) on channel 1")
        client.send("/midi/note", 1, 60, 100)  # Note on
        await asyncio.sleep(0.5)
        client.send("/midi/note", 1, 60, 0)   # Note off

        print("   Sending CC 7 (volume) value 64")
        client.send("/midi/cc", 1, 7, 64)

        # Parameter Control Demo
        print("\nParameter Control:")
        print("   Setting module 1, parameter 0 to 0.7")
        client.send("/param", 1, 0, 0.7)

        print("   Setting module 2, parameter 1 to 0.3")
        client.send("/param", 2, 1, 0.3)

        # CV Control Demo
        print("\nCV Control:")
        print("   Sending 5.0V to module 3, CV input 0")
        client.send("/cv", 3, 0, 5.0)

        print("   Sending -2.5V to module 4, CV input 1")
        client.send("/cv", 4, 1, -2.5)

        # Light Control Demo
        print("\nLight Control:")
        print("   Setting module 1, light 0 to half brightness")
        client.send("/light", 1, 0, 0.5)

        # Trigger Demo
        print("\nTrigger Control:")
        print("   Triggering module 2, trigger 0")
        client.send("/trigger", 2, 0)

        # Module-Specific Demos
        print("\nModule-Specific Control:")
        print("   VCO: Setting module 5 frequency to 440Hz")
        # Convert 440Hz to 0-1 range (assuming 0-10kHz)
        freq_value = 440.0 / 10000.0
        client.send("/param", 5, 0, freq_value)

        print("   VCA: Setting module 6 level to 0.8")
        client.send("/param", 6, 0, 0.8)

        print("   LFO: Setting module 7 rate to 0.2")
        client.send("/param", 7, 0, 0.2)

        print("   Filter: Setting module 8 cutoff to 0.6")
        client.send("/param", 8, 0, 0.6)

        print("   Envelope: Setting ADSR on module 9")
        client.send("/param", 9, 0, 0.1)  # Attack
        client.send("/param", 9, 1, 0.3)  # Decay
        client.send("/param", 9, 2, 0.7)  # Sustain
        client.send("/param", 9, 3, 0.4)  # Release

        print("\nDemo completed! Check your VCV Rack patch for the changes.")
        print("\nTips:")
        print("   - Make sure your OSC module is configured correctly")
        print("   - Module IDs start from 1 in most VCV Rack patches")
        print("   - Parameter ranges are typically 0.0 to 1.0")
        print("   - CV ranges are typically -10.0 to +10.0")

    except Exception as e:
        print(f"Error during demo: {e}")
        print("Make sure VCV Rack is running with an OSC module installed.")

if __name__ == "__main__":
    asyncio.run(vcv_rack_demo())
#!/usr/bin/env python3
"""Quick test script for VCV Rack OSC connection using vcv_manager."""

import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from oscmcp.osc.client import OSCClient


async def test_vcv_manager():
    """Test vcv_manager with various operations."""

    port = 10001  # Your OSCelot receive port

    print("=" * 50)
    print("VCV Manager Test Suite")
    print("=" * 50)
    print(f"Testing connection to VCV Rack on port {port}")
    print()

    client = OSCClient("127.0.0.1", port)

    tests = [
        {
            "name": "Set Parameter (Module 1, Param 0 = 0.7)",
            "address": "/param",
            "values": [1, 0, 0.7],
        },
        {
            "name": "Play MIDI Note C4 (Note 60)",
            "address": "/midi/note",
            "values": [1, 60, 100],  # channel, note, velocity
        },
        {
            "name": "Set VCO Frequency (440Hz)",
            "address": "/param",
            "values": [1, 0, 0.044],  # 440Hz / 10000 = 0.044
        },
        {
            "name": "Send CV Voltage (5V)",
            "address": "/cv",
            "values": [1, 0, 5.0],  # module_id, cv_id, voltage
        },
        {
            "name": "Set Light Brightness (80%)",
            "address": "/light",
            "values": [1, 0, 0.8],  # module_id, light_id, brightness
        },
        {
            "name": "Trigger Event",
            "address": "/trigger",
            "values": [1, 0],  # module_id, trigger_id
        },
    ]

    for i, test in enumerate(tests, 1):
        print(f"{i}. {test['name']}...")
        try:
            client.send(test["address"], *test["values"])
            print(f"   Success! Message sent to {test['address']}")
        except Exception as e:
            print(f"   Error: {e}")
        await asyncio.sleep(0.5)  # Small delay between tests

    print()
    print("=" * 50)
    print("Test Complete!")
    print("=" * 50)
    print()
    print("Notes:")
    print("   - Messages were sent successfully if no errors occurred")
    print("   - Check OSCelot in VCV Rack to see if it received messages")
    print("   - If nothing happened, you may need to map parameters in OSCelot")
    print("   - Module IDs start from 1 (not 0)")
    print()
    print("Next Steps:")
    print("   1. Map parameters in OSCelot (click Map, then click a knob)")
    print("   2. Try controlling mapped parameters")
    print("   3. Use vcv_manager in Claude Desktop for natural language control")


if __name__ == "__main__":
    asyncio.run(test_vcv_manager())

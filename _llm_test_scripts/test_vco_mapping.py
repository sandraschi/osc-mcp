#!/usr/bin/env python3
"""Quick test to verify your VCO mapping."""

import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from oscmcp.osc.client import OSCClient


async def test_vco_mapping(module_id=1, param_id=0, port=10001):
    """Test VCO frequency control."""

    client = OSCClient("127.0.0.1", port)

    print("=" * 60)
    print("VCO Mapping Test")
    print("=" * 60)
    print(f"Module ID: {module_id}")
    print(f"Parameter ID: {param_id}")
    print(f"Port: {port}")
    print()

    # Test frequencies (in Hz)
    test_frequencies = [
        (440.0, "A4 - 440Hz (standard tuning note)"),
        (261.63, "C4 - Middle C"),
        (523.25, "C5 - One octave higher"),
        (220.0, "A3 - One octave lower"),
        (880.0, "A5 - Two octaves higher"),
    ]

    print("Playing test frequencies...")
    print("(You should hear the VCO pitch change)")
    print()

    for freq, description in test_frequencies:
        # Convert Hz to normalized 0-1 range (assuming 0-10kHz)
        normalized = min(max(0.0, freq / 10000.0), 1.0)

        print(f"Setting to {description}")
        client.send("/param", module_id, param_id, normalized)

        await asyncio.sleep(1.0)  # Hold for 1 second

    # Return to A4
    print()
    print("Returning to A4 (440Hz)...")
    client.send("/param", module_id, param_id, 440.0 / 10000.0)

    print()
    print("=" * 60)
    print("Test complete!")
    print("=" * 60)
    print()
    print("If you heard pitch changes, your mapping is working!")
    print("If not, check:")
    print("  1. VCO is connected to audio output")
    print("  2. Module ID and Parameter ID are correct")
    print("  3. OSCelot shows the mapping")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Test VCO mapping")
    parser.add_argument("--module-id", type=int, default=1, help="Module ID")
    parser.add_argument("--param-id", type=int, default=0, help="Parameter ID")
    parser.add_argument("--port", type=int, default=10001, help="OSC port")
    args = parser.parse_args()

    asyncio.run(test_vco_mapping(args.module_id, args.param_id, args.port))

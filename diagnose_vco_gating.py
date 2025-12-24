#!/usr/bin/env python3
"""
Diagnose VCO gating issue - test different gating methods.
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from oscmcp.osc.client import OSCClient

def frequency_to_normalized(freq, max_freq=10000.0):
    """Convert frequency in Hz to normalized 0-1 range."""
    return min(max(0.0, freq / max_freq), 1.0)

async def test_gating_methods(module_id=14, param_id=0, port=10001):
    """Test different gating methods."""
    client = OSCClient("127.0.0.1", port)
    client.connect()
    
    print("=" * 60)
    print("VCO Gating Diagnostic Test")
    print("=" * 60)
    print(f"Module ID: {module_id}, Parameter ID: {param_id}")
    print()
    
    test_freq = 440.0  # A4
    normalized_freq = frequency_to_normalized(test_freq)
    
    print("Method 1: Frequency to 0.0")
    print("Setting frequency to 440Hz, then 0.0...")
    client.send("/param", module_id, param_id, normalized_freq)
    await asyncio.sleep(0.5)
    client.send("/param", module_id, param_id, 0.0)
    await asyncio.sleep(0.5)
    print("Did it stop?")
    print()
    
    print("Method 2: Frequency to very low (0.001)")
    print("Setting frequency to 440Hz, then 0.001...")
    client.send("/param", module_id, param_id, normalized_freq)
    await asyncio.sleep(0.5)
    client.send("/param", module_id, param_id, 0.001)
    await asyncio.sleep(0.5)
    print("Did it stop?")
    print()
    
    print("Method 3: Rapid on/off cycle")
    print("Rapidly switching between 440Hz and 0.0...")
    for i in range(5):
        client.send("/param", module_id, param_id, normalized_freq)
        await asyncio.sleep(0.1)
        client.send("/param", module_id, param_id, 0.0)
        await asyncio.sleep(0.1)
    print("Did you hear distinct clicks/stops?")
    print()
    
    print("Method 4: Check if this is actually a frequency parameter")
    print("Setting to different frequencies...")
    frequencies = [261.63, 329.63, 392.00, 440.00]  # C4, E4, G4, A4
    for freq in frequencies:
        norm = frequency_to_normalized(freq)
        client.send("/param", module_id, param_id, norm)
        print(f"  {freq:.2f} Hz", end="", flush=True)
        await asyncio.sleep(0.3)
    print()
    print("Did the pitch change?")
    print()
    
    # Silence
    client.send("/param", module_id, param_id, 0.0)
    
    print("=" * 60)
    print("Diagnostic complete!")
    print()
    print("If frequency gating doesn't work, you likely need:")
    print("  1. A VCA (Voltage Controlled Amplifier) mapped to OSC")
    print("  2. An envelope generator")
    print("  3. Or check if parameter ID 0 is actually frequency")
    print("     (try --param-id 1, 2, etc. to find other parameters)")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Diagnose VCO gating")
    parser.add_argument("--module-id", type=int, default=14,
                       help="VCO module ID (default: 14)")
    parser.add_argument("--param-id", type=int, default=0,
                       help="Parameter ID (default: 0)")
    parser.add_argument("--port", type=int, default=10001,
                       help="OSC port (default: 10001)")
    args = parser.parse_args()
    
    asyncio.run(test_gating_methods(
        module_id=args.module_id,
        param_id=args.param_id,
        port=args.port
    ))


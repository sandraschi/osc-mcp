#!/usr/bin/env python3
"""
Test rapid frequency changes to verify VCO responds.
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from oscmcp.osc.client import OSCClient

def frequency_to_normalized(freq, max_freq=10000.0):
    """Convert frequency in Hz to normalized 0-1 range."""
    return min(max(0.0, freq / max_freq), 1.0)

async def test_frequency_changes(module_id=14, param_id=0, port=10001):
    """Test rapid frequency changes."""
    client = OSCClient("127.0.0.1", port)
    client.connect()
    
    print("=" * 60)
    print("Testing Rapid Frequency Changes")
    print("=" * 60)
    print(f"Module ID: {module_id}, Parameter ID: {param_id}")
    print()
    
    # Test frequencies (C4, E4, G4, A4, C5)
    frequencies = [261.63, 329.63, 392.00, 440.00, 523.25]
    note_names = ["C4", "E4", "G4", "A4", "C5"]
    
    print("Playing 5 notes rapidly (0.3 seconds each)...")
    print("You should hear the pitch change clearly!")
    print()
    
    for i, (freq, name) in enumerate(zip(frequencies, note_names), 1):
        normalized = frequency_to_normalized(freq)
        client.send("/param", module_id, param_id, normalized)
        print(f"{i}. {name} ({freq:.2f} Hz)")
        await asyncio.sleep(0.3)
    
    print()
    print("Did you hear 5 different pitches?")
    print()
    
    # Test slower with longer notes
    print("Now playing slower (1 second each)...")
    print()
    
    for i, (freq, name) in enumerate(zip(frequencies, note_names), 1):
        normalized = frequency_to_normalized(freq)
        client.send("/param", module_id, param_id, normalized)
        print(f"{i}. {name} ({freq:.2f} Hz)")
        await asyncio.sleep(1.0)
    
    print()
    print("Test complete!")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Test frequency changes")
    parser.add_argument("--module-id", type=int, default=14,
                       help="Module ID (default: 14)")
    parser.add_argument("--param-id", type=int, default=0,
                       help="Parameter ID (default: 0)")
    parser.add_argument("--port", type=int, default=10001,
                       help="OSC port (default: 10001)")
    args = parser.parse_args()
    
    asyncio.run(test_frequency_changes(
        module_id=args.module_id,
        param_id=args.param_id,
        port=args.port
    ))


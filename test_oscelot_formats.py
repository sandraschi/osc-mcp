#!/usr/bin/env python3
"""
Test different OSC address formats for OSCelot.
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from oscmcp.osc.client import OSCClient

def frequency_to_normalized(freq, max_freq=10000.0):
    """Convert frequency in Hz to normalized 0-1 range."""
    return min(max(0.0, freq / max_freq), 1.0)

async def test_formats(module_id=14, param_id=3, port=10001):
    """Test different OSC address formats."""
    client = OSCClient("127.0.0.1", port)
    client.connect()
    
    print("=" * 60)
    print("Testing OSCelot Address Formats")
    print("=" * 60)
    print(f"Module ID: {module_id}, Parameter ID: {param_id}")
    print()
    
    # Test frequencies
    low_freq = frequency_to_normalized(261.63)  # C4
    high_freq = frequency_to_normalized(440.00)  # A4
    
    formats = [
        # Format 1: /param with [module_id, param_id, value]
        {
            "name": "/param [module, param, value]",
            "address": "/param",
            "args": [module_id, param_id, high_freq]
        },
        # Format 2: /param/module/param with value
        {
            "name": "/param/{module}/{param} [value]",
            "address": f"/param/{module_id}/{param_id}",
            "args": [high_freq]
        },
        # Format 3: /module/param with value
        {
            "name": "/module/{id}/param/{id} [value]",
            "address": f"/module/{module_id}/param/{param_id}",
            "args": [high_freq]
        },
        # Format 4: /vcv/param with [module, param, value]
        {
            "name": "/vcv/param [module, param, value]",
            "address": "/vcv/param",
            "args": [module_id, param_id, high_freq]
        },
        # Format 5: /oscelot/param with [module, param, value]
        {
            "name": "/oscelot/param [module, param, value]",
            "address": "/oscelot/param",
            "args": [module_id, param_id, high_freq]
        },
    ]
    
    print("Testing each format - listen for pitch changes!")
    print()
    
    for i, fmt in enumerate(formats, 1):
        print(f"{i}. Testing: {fmt['name']}")
        print(f"   Setting to LOW (C4 = 261.63 Hz)...")
        # Set low
        low_args = fmt['args'].copy()
        low_args[-1] = low_freq
        client.send(fmt['address'], *low_args)
        await asyncio.sleep(0.5)
        
        print(f"   Setting to HIGH (A4 = 440 Hz)...")
        # Set high
        client.send(fmt['address'], *fmt['args'])
        await asyncio.sleep(0.5)
        
        print(f"   Did the pitch change?")
        print()
    
    print("=" * 60)
    print("If none worked, the issue might be:")
    print("  1. Parameter ID is wrong (try 0, 1, 2, 4, 5)")
    print("  2. Module ID is wrong")
    print("  3. OSCelot needs different configuration")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Test OSCelot formats")
    parser.add_argument("--module-id", type=int, default=14,
                       help="Module ID (default: 14)")
    parser.add_argument("--param-id", type=int, default=3,
                       help="Parameter ID (default: 3)")
    parser.add_argument("--port", type=int, default=10001,
                       help="OSC port (default: 10001)")
    args = parser.parse_args()
    
    asyncio.run(test_formats(
        module_id=args.module_id,
        param_id=args.param_id,
        port=args.port
    ))


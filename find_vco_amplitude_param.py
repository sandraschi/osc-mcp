#!/usr/bin/env python3
"""
Find amplitude/gate parameter on VCO module.

Tests different parameter IDs to find one that controls amplitude/volume.
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from oscmcp.osc.client import OSCClient

async def find_amplitude_param(module_id=14, port=10001):
    """Test different parameter IDs to find amplitude control."""
    client = OSCClient("127.0.0.1", port)
    client.connect()
    
    print("=" * 60)
    print("Finding Amplitude/Gate Parameter")
    print("=" * 60)
    print(f"Module ID: {module_id}")
    print()
    print("Testing parameter IDs 0-5...")
    print("Listen for volume changes (not pitch changes)")
    print()
    
    # Set a constant frequency first (param 0)
    test_freq = 440.0 / 10000.0  # A4 normalized
    client.send("/param", module_id, 0, test_freq)
    await asyncio.sleep(0.3)
    
    # Test each parameter ID
    for param_id in range(6):
        print(f"Testing parameter {param_id}:")
        print("  Setting to 0.0 (should be silent)...")
        client.send("/param", module_id, param_id, 0.0)
        await asyncio.sleep(0.5)
        
        print("  Setting to 1.0 (should be loud)...")
        client.send("/param", module_id, param_id, 1.0)
        await asyncio.sleep(0.5)
        
        print("  Setting to 0.5 (should be medium)...")
        client.send("/param", module_id, param_id, 0.5)
        await asyncio.sleep(0.5)
        
        print("  Did the VOLUME change? (not pitch)")
        print()
    
    # Reset frequency param
    client.send("/param", module_id, 0, test_freq)
    
    print("=" * 60)
    print("If you found a parameter that controls volume:")
    print("  Use that parameter ID for VCA/amplitude control")
    print()
    print("If none worked, you need to add a VCA module:")
    print("  1. Add VCA module to your patch")
    print("  2. Connect: VCO -> VCA -> Output")
    print("  3. Map VCA level parameter to OSC")
    print("  4. Use that module/param ID for gating")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Find amplitude parameter")
    parser.add_argument("--module-id", type=int, default=14,
                       help="VCO module ID (default: 14)")
    parser.add_argument("--port", type=int, default=10001,
                       help="OSC port (default: 10001)")
    args = parser.parse_args()
    
    asyncio.run(find_amplitude_param(
        module_id=args.module_id,
        port=args.port
    ))


#!/usr/bin/env python3
"""
Test all parameters on module 14 - clear volume/pitch test.
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from oscmcp.osc.client import OSCClient

async def test_all_params(module_id=14, port=10001):
    """Test all parameters with clear on/off cycles."""
    client = OSCClient("127.0.0.1", port)
    client.connect()
    
    print("=" * 60)
    print("Testing All Parameters - Module 14")
    print("=" * 60)
    print()
    print("Each parameter will:")
    print("  1. Go to 0.0 (silent/off)")
    print("  2. Go to 1.0 (loud/on)")
    print("  3. Go to 0.5 (medium)")
    print()
    print("Listen for VOLUME changes (not pitch changes)")
    print("Press Ctrl+C to stop early")
    print()
    
    # Set a constant frequency first (param 0 = frequency)
    test_freq = 440.0 / 10000.0  # A4 normalized
    client.send("/param", module_id, 0, test_freq)
    await asyncio.sleep(0.5)
    print("Starting with constant pitch (A4)...")
    print()
    
    # Test each parameter ID
    for param_id in range(8):
        print(f"{'='*60}")
        print(f"PARAMETER {param_id}")
        print(f"{'='*60}")
        
        # OFF
        print(f"  OFF (0.0)...")
        client.send("/param", module_id, param_id, 0.0)
        await asyncio.sleep(1.0)
        
        # ON
        print(f"  ON (1.0)...")
        client.send("/param", module_id, param_id, 1.0)
        await asyncio.sleep(1.0)
        
        # MEDIUM
        print(f"  MEDIUM (0.5)...")
        client.send("/param", module_id, param_id, 0.5)
        await asyncio.sleep(1.0)
        
        # BACK TO OFF
        print(f"  OFF again (0.0)...")
        client.send("/param", module_id, param_id, 0.0)
        await asyncio.sleep(0.5)
        
        print()
        print(f"Did parameter {param_id} control VOLUME? (y/n/q to quit)")
        print()
    
    # Reset
    client.send("/param", module_id, 0, test_freq)
    print("Test complete!")
    print()
    print("If you found a volume parameter, note its ID and we can use it for gating.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Test all parameters")
    parser.add_argument("--module-id", type=int, default=14,
                       help="Module ID (default: 14)")
    parser.add_argument("--port", type=int, default=10001,
                       help="OSC port (default: 10001)")
    args = parser.parse_args()
    
    try:
        asyncio.run(test_all_params(
            module_id=args.module_id,
            port=args.port
        ))
    except KeyboardInterrupt:
        print("\nTest interrupted by user")


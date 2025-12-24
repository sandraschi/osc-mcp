#!/usr/bin/env python3
"""
Test VCO note gating - switch notes on and off.

This script tests two methods:
1. VCA gating (if you have a VCA mapped)
2. Frequency gating (rapid frequency changes)
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from oscmcp.osc.client import OSCClient

def frequency_to_normalized(freq, max_freq=10000.0):
    """Convert frequency in Hz to normalized 0-1 range."""
    return min(max(0.0, freq / max_freq), 1.0)

async def test_vca_gating(vco_module_id=1, vco_param_id=0, 
                          vca_module_id=None, vca_param_id=None,
                          port=10001):
    """Test note gating using VCA."""
    client = OSCClient("127.0.0.1", port)
    client.connect()
    
    print("=" * 60)
    print("Testing VCA Gating")
    print("=" * 60)
    print(f"VCO Module: {vco_module_id}, Param: {vco_param_id}")
    if vca_module_id:
        print(f"VCA Module: {vca_module_id}, Param: {vca_param_id}")
    print()
    
    # Test note: C4 (261.63 Hz)
    test_freq = 261.63
    normalized_freq = frequency_to_normalized(test_freq)
    
    print("Playing 5 notes with VCA gating...")
    print("(Each note should be clearly separated)")
    print()
    
    for i in range(5):
        print(f"Note {i+1}: ON")
        
        # Note ON: Set frequency and VCA to 1.0
        client.send("/param", vco_module_id, vco_param_id, normalized_freq)
        if vca_module_id:
            client.send("/param", vca_module_id, vca_param_id, 1.0)
        
        await asyncio.sleep(0.5)  # Note duration
        
        print(f"Note {i+1}: OFF")
        
        # Note OFF: Set VCA to 0.0
        if vca_module_id:
            client.send("/param", vca_module_id, vca_param_id, 0.0)
        else:
            # Fallback: set frequency to very low
            client.send("/param", vco_module_id, vco_param_id, 0.001)
        
        await asyncio.sleep(0.3)  # Gap between notes
    
    # Final silence
    if vca_module_id:
        client.send("/param", vca_module_id, vca_param_id, 0.0)
    client.send("/param", vco_module_id, vco_param_id, 0.0)
    
    print()
    print("Test complete!")

async def test_frequency_gating(vco_module_id=1, vco_param_id=0, port=10001):
    """Test note gating using rapid frequency changes."""
    client = OSCClient("127.0.0.1", port)
    client.connect()
    
    print("=" * 60)
    print("Testing Frequency Gating (No VCA)")
    print("=" * 60)
    print(f"VCO Module: {vco_module_id}, Param: {vco_param_id}")
    print()
    print("Playing 5 notes with frequency gating...")
    print("(Frequency drops to near-zero between notes)")
    print()
    
    # Test note: C4 (261.63 Hz)
    test_freq = 261.63
    normalized_freq = frequency_to_normalized(test_freq)
    silence_freq = 0.001  # Very low frequency (almost silent)
    
    for i in range(5):
        print(f"Note {i+1}: ON ({test_freq:.2f} Hz)")
        
        # Note ON: Set frequency
        client.send("/param", vco_module_id, vco_param_id, normalized_freq)
        
        await asyncio.sleep(0.5)  # Note duration
        
        print(f"Note {i+1}: OFF (silence)")
        
        # Note OFF: Set frequency to very low
        client.send("/param", vco_module_id, vco_param_id, silence_freq)
        
        await asyncio.sleep(0.3)  # Gap between notes
    
    # Final silence
    client.send("/param", vco_module_id, vco_param_id, 0.0)
    
    print()
    print("Test complete!")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Test VCO note gating")
    parser.add_argument("--vco-module", type=int, default=1,
                       help="VCO module ID (default: 1)")
    parser.add_argument("--vco-param", type=int, default=0,
                       help="VCO frequency parameter ID (default: 0)")
    parser.add_argument("--vca-module", type=int, default=None,
                       help="VCA module ID (optional, for VCA gating)")
    parser.add_argument("--vca-param", type=int, default=None,
                       help="VCA level parameter ID (optional)")
    parser.add_argument("--port", type=int, default=10001,
                       help="OSC port (default: 10001)")
    parser.add_argument("--method", choices=["vca", "frequency"], default=None,
                       help="Gating method (auto-detect if not specified)")
    args = parser.parse_args()
    
    if args.method == "vca" or (args.vca_module is not None):
        asyncio.run(test_vca_gating(
            vco_module_id=args.vco_module,
            vco_param_id=args.vco_param,
            vca_module_id=args.vca_module,
            vca_param_id=args.vca_param,
            port=args.port
        ))
    else:
        asyncio.run(test_frequency_gating(
            vco_module_id=args.vco_module,
            vco_param_id=args.vco_param,
            port=args.port
        ))


#!/usr/bin/env python3
"""
Check OSC ports - test both directions.
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from oscmcp.osc.client import OSCClient
from oscmcp.osc.server import OSCServer

async def check_ports():
    """Check OSC ports for VCV Rack."""
    print("=" * 60)
    print("OSC Port Configuration Check")
    print("=" * 60)
    print()
    print("OSCelot Port Configuration:")
    print("  Port 10001: OSCelot RECEIVES messages (send TO this port)")
    print("  Port 10002: OSCelot SENDS messages (listen ON this port, if enabled)")
    print()
    print("Checking if OSCelot is listening on port 10001...")
    print()
    
    # Test sending to port 10001
    client = OSCClient("127.0.0.1", 10001)
    client.connect()
    
    print("Sending test message to port 10001 (/param, module 14, param 3)...")
    client.send("/param", 14, 3, 0.5)
    print("Message sent!")
    print()
    print("Did you see/hear anything in VCV Rack?")
    print()
    
    # Try listening on port 10002
    print("Checking if OSCelot sends messages on port 10002...")
    print("(Listening for 3 seconds - move a knob in VCV Rack if you can)")
    print()
    
    received = []
    
    def handler(address, *args):
        received.append((address, list(args)))
        print(f"  Received: {address} {list(args)}")
    
    server = OSCServer("127.0.0.1", 10002)
    server.dispatcher.set_default_handler(handler)
    
    try:
        await server.start()
        await asyncio.sleep(3)
    finally:
        await server.stop()
    
    print()
    if received:
        print(f"Received {len(received)} message(s) from OSCelot!")
    else:
        print("No messages received from OSCelot.")
        print("OSCelot may not be configured to send messages.")
    print()
    print("=" * 60)
    print("Summary")
    print("=" * 60)
    print("Send messages TO: port 10001")
    print("Listen for messages FROM: port 10002 (if OSCelot is configured to send)")

if __name__ == "__main__":
    asyncio.run(check_ports())


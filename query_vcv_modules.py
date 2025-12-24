#!/usr/bin/env python3
"""
Query VCV Rack module setup via OSC.

This script attempts to discover what modules are configured in VCV Rack
by listening for OSC messages or querying OSCelot.
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from oscmcp.osc.client import OSCClient
from oscmcp.osc.server import OSCServer

async def query_vcv_modules(listen_port=10002, query_port=10001):
    """
    Query VCV Rack modules.
    
    Note: OSCelot doesn't typically expose module discovery via OSC.
    This script listens for any OSC messages from VCV Rack and also
    tries common query addresses.
    """
    
    print("=" * 60)
    print("VCV Rack Module Query")
    print("=" * 60)
    print(f"Listening on port: {listen_port}")
    print(f"Querying port: {query_port}")
    print()
    
    # Start OSC server to receive messages
    server = OSCServer("127.0.0.1", listen_port)
    
    received_messages = []
    
    def message_handler(address, *args):
        """Handle received OSC messages."""
        msg = {
            "address": address,
            "args": list(args),
            "timestamp": asyncio.get_event_loop().time()
        }
        received_messages.append(msg)
        print(f"Received: {address} {args}")
    
    # Register handler for all messages
    server.dispatcher.set_default_handler(message_handler)
    
    try:
        # Start server
        await server.start()
        print("OSC server started. Listening for messages...")
        print()
        
        # Send query messages to common OSC addresses
        client = OSCClient("127.0.0.1", query_port)
        
        query_addresses = [
            "/query/modules",
            "/modules/list",
            "/info/modules",
            "/status",
            "/ping",
        ]
        
        print("Sending query messages...")
        for addr in query_addresses:
            try:
                client.send(addr, [])
                print(f"  Sent: {addr}")
            except Exception as e:
                print(f"  Error sending {addr}: {e}")
        
        print()
        print("Listening for 3 seconds...")
        print("(Try moving a knob in VCV Rack to see if OSCelot sends messages)")
        print()
        
        # Listen for 3 seconds
        await asyncio.sleep(3)
        
        print()
        print("=" * 60)
        print("Results")
        print("=" * 60)
        
        if received_messages:
            print(f"Received {len(received_messages)} message(s):")
            for i, msg in enumerate(received_messages, 1):
                print(f"{i}. {msg['address']} {msg['args']}")
        else:
            print("No messages received.")
            print()
            print("This could mean:")
            print("  1. OSCelot doesn't send discovery messages")
            print("  2. OSCelot needs to be configured to send messages")
            print("  3. Port configuration might be different")
            print()
            print("To see module activity:")
            print("  1. Map a parameter in OSCelot")
            print("  2. Move a knob/slider in VCV Rack")
            print("  3. OSCelot should send /param messages")
        
        print()
        print("Note: OSCelot typically doesn't expose module discovery.")
        print("You need to manually map parameters to see activity.")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await server.stop()
        print()
        print("Server stopped.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Query VCV Rack modules")
    parser.add_argument("--listen-port", type=int, default=10002, 
                       help="Port to listen on (default: 10002)")
    parser.add_argument("--query-port", type=int, default=10001,
                       help="Port to query (default: 10001)")
    args = parser.parse_args()
    
    asyncio.run(query_vcv_modules(listen_port=args.listen_port, query_port=args.query_port))


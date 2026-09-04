#!/usr/bin/env python3
"""
Read OSCelot mapping by monitoring OSC messages.

This script listens for OSC messages from OSCelot and displays
the module ID and parameter ID mappings.
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from collections import defaultdict

from oscmcp.osc.server import OSCServer

# Store seen mappings
mappings = defaultdict(set)


def message_handler(address, *args):
    """Handle received OSC messages."""
    args_list = list(args)

    # OSCelot typically sends /param messages with [module_id, param_id, value]
    if address == "/param" and len(args_list) >= 3:
        module_id = int(args_list[0])
        param_id = int(args_list[1])
        value = args_list[2]
        mappings[(module_id, param_id)].add(value)
        print(f"Module {module_id}, Param {param_id}: {value:.4f}")
    else:
        print(f"Received: {address} {args_list}")


async def listen_for_mapping(listen_port=10002, duration=30):
    """Listen for OSC messages from OSCelot."""
    print("=" * 60)
    print("OSCelot Mapping Monitor")
    print("=" * 60)
    print(f"Listening on port: {listen_port}")
    print()
    print("Instructions:")
    print("  1. Move knobs/sliders in VCV Rack")
    print("  2. OSCelot will send /param messages")
    print("  3. This script will capture the mappings")
    print()
    print(f"Listening for {duration} seconds...")
    print("(Press Ctrl+C to stop early)")
    print()

    server = OSCServer("127.0.0.1", listen_port)
    server.dispatcher.set_default_handler(message_handler)

    try:
        await server.start()
        print("Server started. Move some knobs in VCV Rack now!")
        print()

        await asyncio.sleep(duration)

    except KeyboardInterrupt:
        print("\nStopped by user")
    finally:
        await server.stop()

    print()
    print("=" * 60)
    print("Captured Mappings")
    print("=" * 60)

    if mappings:
        print()
        print("Module ID | Param ID | Values Seen")
        print("-" * 60)
        for (module_id, param_id), values in sorted(mappings.items()):
            value_list = sorted(values)
            if len(value_list) > 5:
                value_str = f"{value_list[0]:.4f} ... {value_list[-1]:.4f} ({len(value_list)} values)"
            else:
                value_str = ", ".join(f"{v:.4f}" for v in value_list)
            print(f"   {module_id:2d}    |    {param_id:2d}    | {value_str}")

        print()
        print("=" * 60)
        print("Summary")
        print("=" * 60)
        print(f"Found {len(mappings)} parameter mappings:")
        for (module_id, param_id), values in sorted(mappings.items()):
            print(f"  Module {module_id}, Parameter {param_id}")
    else:
        print("No mappings captured.")
        print()
        print("Make sure:")
        print("  1. OSCelot is configured to send messages to port", listen_port)
        print("  2. You moved some knobs/sliders in VCV Rack")
        print("  3. Parameters are mapped in OSCelot")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Read OSCelot mapping")
    parser.add_argument("--listen-port", type=int, default=10002, help="Port to listen on (default: 10002)")
    parser.add_argument("--duration", type=int, default=30, help="Listen duration in seconds (default: 30)")
    args = parser.parse_args()

    asyncio.run(listen_for_mapping(listen_port=args.listen_port, duration=args.duration))

#!/usr/bin/env python3
"""Verify OSC connection to OSCelot."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from oscmcp.osc.client import OSCClient

print("=" * 60)
print("OSC Connection Verification")
print("=" * 60)
print()
print("Sending test messages to port 10001...")
print("Check OSCelot in VCV Rack - does it show any activity?")
print()

client = OSCClient("127.0.0.1", 10001)
client.connect()

# Try different formats
print("1. Testing /param format...")
client.send("/param", 14, 1, 0.5)
print("   Sent: /param [14, 1, 0.5]")
print()

print("2. Testing /param/14/1 format...")
try:
    client.send("/param/14/1", 0.5)
    print("   Sent: /param/14/1 [0.5]")
except:
    print("   Error sending /param/14/1")
print()

print("3. Testing /module/14/param/1 format...")
try:
    client.send("/module/14/param/1", 0.5)
    print("   Sent: /module/14/param/1 [0.5]")
except:
    print("   Error sending /module/14/param/1")
print()

print("=" * 60)
print("Check OSCelot:")
print("  - Does it show any received messages?")
print("  - Is the receive port set to 10001?")
print("  - Are there any error indicators?")
print()
print("If OSCelot shows nothing, check:")
print("  1. OSCelot receive port = 10001")
print("  2. OSCelot is enabled/active")
print("  3. Firewall isn't blocking port 10001")


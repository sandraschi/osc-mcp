#!/usr/bin/env python3
"""
Interactive VCO Control - Explore your mapped VCO!

This script lets you interactively control your VCO frequency
and explore different notes and frequencies.
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from oscmcp.osc.client import OSCClient

# Common note frequencies
NOTES = {
    "C3": 130.81,
    "C#3": 138.59,
    "D3": 146.83,
    "D#3": 155.56,
    "E3": 164.81,
    "F3": 174.61,
    "F#3": 185.00,
    "G3": 196.00,
    "G#3": 207.65,
    "A3": 220.00,
    "A#3": 233.08,
    "B3": 246.94,
    "C4": 261.63,
    "C#4": 277.18,
    "D4": 293.66,
    "D#4": 311.13,
    "E4": 329.63,
    "F4": 349.23,
    "F#4": 369.99,
    "G4": 392.00,
    "G#4": 415.30,
    "A4": 440.00,
    "A#4": 466.16,
    "B4": 493.88,
    "C5": 523.25,
    "C#5": 554.37,
    "D5": 587.33,
    "D#5": 622.25,
    "E5": 659.25,
    "F5": 698.46,
    "F#5": 739.99,
    "G5": 783.99,
}


def frequency_to_normalized(freq, max_freq=10000.0):
    """Convert frequency in Hz to normalized 0-1 range."""
    return min(max(0.0, freq / max_freq), 1.0)


async def interactive_control(module_id=1, param_id=0, port=10001):
    """Interactive VCO frequency control."""

    client = OSCClient("127.0.0.1", port)

    print("=" * 60)
    print("Interactive VCO Control")
    print("=" * 60)
    print(f"Module ID: {module_id}")
    print(f"Parameter ID: {param_id}")
    print(f"Port: {port}")
    print()
    print("Commands:")
    print("  <note>     - Play note (e.g., 'C4', 'A4', 'G3')")
    print("  <number>   - Set frequency in Hz (e.g., '440', '261.63')")
    print("  scale      - Play a C major scale")
    print("  chord      - Play a C major chord")
    print("  sweep      - Frequency sweep")
    print("  help       - Show this help")
    print("  quit/exit  - Exit")
    print()
    print("Example: Type 'C4' to play middle C, or '440' for 440Hz")
    print()

    current_freq = 440.0  # Start at A4

    while True:
        try:
            command = input("VCO> ").strip().upper()

            if not command:
                continue

            if command in ["QUIT", "EXIT", "Q"]:
                print("Goodbye!")
                break

            if command == "HELP":
                print("\nCommands:")
                print("  <note>     - Play note (C3-C5)")
                print("  <number>   - Set frequency in Hz")
                print("  scale      - Play C major scale")
                print("  chord      - Play C major chord")
                print("  sweep      - Frequency sweep")
                print("  quit       - Exit\n")
                continue

            if command == "SCALE":
                print("Playing C major scale...")
                scale_notes = ["C4", "D4", "E4", "F4", "G4", "A4", "B4", "C5"]
                for note in scale_notes:
                    if note in NOTES:
                        freq = NOTES[note]
                        normalized = frequency_to_normalized(freq)
                        client.send("/param", module_id, param_id, normalized)
                        print(f"  {note} ({freq:.2f} Hz)")
                        await asyncio.sleep(0.5)
                continue

            if command == "CHORD":
                print("Playing C major chord (C4-E4-G4)...")
                chord_notes = ["C4", "E4", "G4"]
                for note in chord_notes:
                    if note in NOTES:
                        freq = NOTES[note]
                        normalized = frequency_to_normalized(freq)
                        client.send("/param", module_id, param_id, normalized)
                        print(f"  {note} ({freq:.2f} Hz)")
                        await asyncio.sleep(0.8)
                continue

            if command == "SWEEP":
                print("Frequency sweep from 100Hz to 2000Hz...")
                for freq in range(100, 2001, 50):
                    normalized = frequency_to_normalized(freq)
                    client.send("/param", module_id, param_id, normalized)
                    await asyncio.sleep(0.05)
                print("Sweep complete!")
                continue

            # Try as note name
            if command in NOTES:
                freq = NOTES[command]
                normalized = frequency_to_normalized(freq)
                client.send("/param", module_id, param_id, normalized)
                current_freq = freq
                print(f"Playing {command}: {freq:.2f} Hz")
                continue

            # Try as frequency number
            try:
                freq = float(command)
                if 20 <= freq <= 20000:  # Reasonable frequency range
                    normalized = frequency_to_normalized(freq)
                    client.send("/param", module_id, param_id, normalized)
                    current_freq = freq
                    print(f"Set frequency: {freq:.2f} Hz")
                else:
                    print(f"Frequency {freq} Hz is out of range (20-20000 Hz)")
            except ValueError:
                print(f"Unknown command: {command}")
                print(
                    "Type 'help' for commands, or a note name (e.g., 'C4') or frequency (e.g., '440')"
                )

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Interactive VCO control")
    parser.add_argument("--module-id", type=int, default=1, help="Module ID")
    parser.add_argument("--param-id", type=int, default=0, help="Parameter ID")
    parser.add_argument("--port", type=int, default=10001, help="OSC port")
    args = parser.parse_args()

    asyncio.run(interactive_control(args.module_id, args.param_id, args.port))

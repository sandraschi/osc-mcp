#!/usr/bin/env python3
"""
Play "Frère Jacques" continuously in a loop.

Perfect for experimenting with patch cables, knobs, and modules
while the melody plays!
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from oscmcp.osc.client import OSCClient

# Frère Jacques melody frequencies (in Hz)
FRERE_JACQUES_FREQUENCIES = [
    # Frère Jacques, frère Jacques
    261.63,
    293.66,
    329.63,
    261.63,  # C4 D4 E4 C4
    261.63,
    293.66,
    329.63,
    261.63,  # C4 D4 E4 C4
    # Dormez-vous? Dormez-vous?
    329.63,
    349.23,
    392.00,  # E4 F4 G4
    329.63,
    349.23,
    392.00,  # E4 F4 G4
    # Sonnez les matines, sonnez les matines
    392.00,
    440.00,
    392.00,
    349.23,
    329.63,
    261.63,  # G4 A4 G4 F4 E4 C4
    392.00,
    440.00,
    392.00,
    349.23,
    329.63,
    261.63,  # G4 A4 G4 F4 E4 C4
    # Ding ding dong, ding ding dong
    261.63,
    196.00,
    261.63,  # C4 G3 C4
    261.63,
    196.00,
    261.63,  # C4 G3 C4
]

# Note durations (in beats)
DURATIONS = [
    0.5,
    0.5,
    0.5,
    0.5,  # C D E C
    0.5,
    0.5,
    0.5,
    0.5,  # C D E C
    0.5,
    0.5,
    1.0,  # E F G (long)
    0.5,
    0.5,
    1.0,  # E F G (long)
    0.25,
    0.25,
    0.25,
    0.25,
    0.5,
    0.5,  # G A G F E C
    0.25,
    0.25,
    0.25,
    0.25,
    0.5,
    0.5,  # G A G F E C
    0.5,
    0.5,
    1.0,  # C G C (long)
    0.5,
    0.5,
    1.0,  # C G C (long)
]


def frequency_to_note_name(freq):
    """Convert frequency to approximate note name."""
    if abs(freq - 261.63) < 5:
        return "C4"
    if abs(freq - 293.66) < 5:
        return "D4"
    if abs(freq - 329.63) < 5:
        return "E4"
    if abs(freq - 349.23) < 5:
        return "F4"
    if abs(freq - 392.00) < 5:
        return "G4"
    if abs(freq - 440.00) < 5:
        return "A4"
    if abs(freq - 196.00) < 5:
        return "G3"
    return f"{freq:.1f}Hz"


async def play_melody_loop(client, module_id, param_id, tempo, loop_count=None):
    """Play the melody in a loop."""

    beat_duration = 60.0 / tempo
    iteration = 0

    print("Playing continuously... (Press Ctrl+C to stop)")
    print("=" * 60)

    try:
        while loop_count is None or iteration < loop_count:
            iteration += 1
            if loop_count:
                print(f"\nLoop {iteration}/{loop_count}:")
            else:
                print(f"\nLoop {iteration}:")

            for i, (freq, duration) in enumerate(zip(FRERE_JACQUES_FREQUENCIES, DURATIONS), 1):
                note_duration_seconds = duration * beat_duration

                # Convert frequency to normalized 0-1 range (0-10kHz)
                normalized_value = min(max(0.0, freq / 10000.0), 1.0)

                # Send parameter value to VCO
                client.send("/param", module_id, param_id, normalized_value)

                # Show first note of each loop, then just dots
                if i == 1:
                    print(f"  {frequency_to_note_name(freq)} ", end="", flush=True)
                else:
                    print(".", end="", flush=True)

                # Wait for note duration
                await asyncio.sleep(note_duration_seconds)

            print()  # New line after each loop

            # Small pause between loops
            await asyncio.sleep(0.5)

    except KeyboardInterrupt:
        print("\n\nStopping...")
        # Return to A4
        client.send("/param", module_id, param_id, 440.0 / 10000.0)
        print("Returned to A4 (440Hz)")


async def main():
    """Main function."""
    import argparse

    parser = argparse.ArgumentParser(description="Play Frère Jacques continuously - perfect for patching!")
    parser.add_argument("--module-id", type=int, default=1, help="VCO module ID (default: 1)")
    parser.add_argument("--param-id", type=int, default=0, help="Frequency parameter ID (default: 0)")
    parser.add_argument("--port", type=int, default=10001, help="OSC port (default: 10001)")
    parser.add_argument("--tempo", type=int, default=120, help="Tempo in BPM (default: 120)")
    parser.add_argument("--loops", type=int, default=None, help="Number of loops (default: infinite)")
    args = parser.parse_args()

    client = OSCClient("127.0.0.1", args.port)

    print("=" * 60)
    print("Frère Jacques - Continuous Loop")
    print("=" * 60)
    print(f"VCO Module ID: {args.module_id}")
    print(f"Parameter ID: {args.param_id}")
    print(f"Port: {args.port}")
    print(f"Tempo: {args.tempo} BPM")
    if args.loops:
        print(f"Loops: {args.loops}")
    else:
        print("Loops: Infinite (Press Ctrl+C to stop)")
    print()
    print("Now's your chance to:")
    print("  - Connect patch cables")
    print("  - Twist knobs and sliders")
    print("  - Add effects and filters")
    print("  - Experiment with your patch!")
    print()

    await play_melody_loop(client, args.module_id, args.param_id, args.tempo, args.loops)


if __name__ == "__main__":
    asyncio.run(main())

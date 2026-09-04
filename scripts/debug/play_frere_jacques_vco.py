#!/usr/bin/env python3
"""
Play "Frère Jacques" using VCO frequency control.

This version controls a VCO's frequency parameter to play the melody,
perfect for when you've mapped a VCO instead of MIDI.
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from oscmcp.osc.client import OSCClient

# Frère Jacques melody frequencies (in Hz)
# Notes: C4=261.63, D4=293.66, E4=329.63, F4=349.23, G3=196.00, G4=392.00, A4=440.00
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
    # A4 = 440Hz is our reference
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


async def play_frere_jacques_vco(module_id=1, param_id=0, port=10001, tempo=120):
    """
    Play Frère Jacques using VCO frequency control.

    Args:
        module_id: The VCO module ID (check OSCelot mapping)
        param_id: The frequency parameter ID (usually 0 for VCO frequency)
        port: OSC port (default: 10001)
        tempo: Tempo in BPM (default: 120)
    """

    client = OSCClient("127.0.0.1", port)

    # Calculate note duration based on tempo
    beat_duration = 60.0 / tempo

    print("=" * 60)
    print("Playing 'Frère Jacques' with VCO Frequency Control")
    print("=" * 60)
    print(f"VCO Module ID: {module_id}")
    print(f"Parameter ID: {param_id}")
    print(f"Port: {port}")
    print(f"Tempo: {tempo} BPM")
    print()

    total_notes = len(FRERE_JACQUES_FREQUENCIES)
    print(f"Playing {total_notes} notes...")
    print()

    for i, (freq, duration) in enumerate(zip(FRERE_JACQUES_FREQUENCIES, DURATIONS), 1):
        note_duration_seconds = duration * beat_duration

        # Convert frequency (Hz) to normalized 0-1 range
        # Assuming VCO range is 0-10kHz (typical for VCV Rack)
        normalized_value = min(max(0.0, freq / 10000.0), 1.0)

        # Set frequency
        client.send("/param", module_id, param_id, normalized_value)
        print(f"{i:2d}. {frequency_to_note_name(freq):6s} ({freq:6.2f} Hz) - {duration:.2f} beats")

        # Wait for note duration
        await asyncio.sleep(note_duration_seconds)

    print()
    print("=" * 60)
    print("Melody complete!")
    print("=" * 60)
    print()
    print("Note: If you didn't hear anything, check:")
    print("  1. VCO is connected to audio output")
    print("  2. Module ID matches your OSCelot mapping")
    print("  3. Parameter ID is correct (usually 0 for frequency)")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Play Frère Jacques with VCO")
    parser.add_argument("--module-id", type=int, default=1, help="VCO module ID (default: 1)")
    parser.add_argument("--param-id", type=int, default=0, help="Frequency parameter ID (default: 0)")
    parser.add_argument("--port", type=int, default=10001, help="OSC port (default: 10001)")
    parser.add_argument("--tempo", type=int, default=120, help="Tempo in BPM (default: 120)")
    args = parser.parse_args()

    asyncio.run(
        play_frere_jacques_vco(module_id=args.module_id, param_id=args.param_id, port=args.port, tempo=args.tempo)
    )

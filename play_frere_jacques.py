#!/usr/bin/env python3
"""
Play "Frère Jacques" (Perejacques) melody in VCV Rack via OSC.

This script plays the classic French children's song "Frère Jacques"
using MIDI notes sent to VCV Rack.
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from oscmcp.osc.client import OSCClient

# Frère Jacques melody
# Notes: C4, D4, E4, C4, C4, D4, E4, C4, E4, F4, G4, E4, F4, G4, G4, A4, G4, F4, E4, C4, G4, A4, G4, F4, E4, C4, C4, G3, C4, C4, G3, C4
FRERE_JACQUES_MELODY = [
    # Frère Jacques, frère Jacques
    (60, 0.5),
    (62, 0.5),
    (64, 0.5),
    (60, 0.5),  # C D E C
    (60, 0.5),
    (62, 0.5),
    (64, 0.5),
    (60, 0.5),  # C D E C
    # Dormez-vous? Dormez-vous?
    (64, 0.5),
    (65, 0.5),
    (67, 1.0),  # E F G (long)
    (64, 0.5),
    (65, 0.5),
    (67, 1.0),  # E F G (long)
    # Sonnez les matines, sonnez les matines
    (67, 0.25),
    (69, 0.25),
    (67, 0.25),
    (65, 0.25),
    (64, 0.5),
    (60, 0.5),  # G A G F E C
    (67, 0.25),
    (69, 0.25),
    (67, 0.25),
    (65, 0.25),
    (64, 0.5),
    (60, 0.5),  # G A G F E C
    # Ding ding dong, ding ding dong
    (60, 0.5),
    (55, 0.5),
    (60, 1.0),  # C G(low) C (long)
    (60, 0.5),
    (55, 0.5),
    (60, 1.0),  # C G(low) C (long)
]


def note_to_name(note):
    """Convert MIDI note number to note name."""
    notes = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    octave = (note // 12) - 1
    note_name = notes[note % 12]
    return f"{note_name}{octave}"


async def play_frere_jacques(port=10001, tempo=120):
    """Play Frère Jacques melody."""

    client = OSCClient("127.0.0.1", port)

    # Calculate note duration based on tempo (BPM)
    # tempo=120 means 120 beats per minute = 0.5 seconds per beat
    beat_duration = 60.0 / tempo

    print("=" * 60)
    print("Playing 'Frère Jacques' (Perejacques)")
    print("=" * 60)
    print(f"Port: {port}")
    print(f"Tempo: {tempo} BPM")
    print()

    total_notes = len(FRERE_JACQUES_MELODY)
    print(f"Playing {total_notes} notes...")
    print()

    for i, (note, duration) in enumerate(FRERE_JACQUES_MELODY, 1):
        note_duration_seconds = duration * beat_duration

        # Play note (note on)
        client.send("/midi/note", 1, note, 100)  # channel 1, note, velocity 100
        print(f"{i:2d}. {note_to_name(note):4s} (note {note:3d}) - {duration:.2f} beats")

        # Wait for note duration
        await asyncio.sleep(note_duration_seconds * 0.9)  # 90% of duration

        # Stop note (note off)
        client.send("/midi/note", 1, note, 0)  # velocity 0 = note off

        # Small gap between notes
        await asyncio.sleep(note_duration_seconds * 0.1)  # 10% gap

    print()
    print("=" * 60)
    print("Melody complete!")
    print("=" * 60)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Play Frère Jacques in VCV Rack")
    parser.add_argument("--port", type=int, default=10001, help="OSC port (default: 10001)")
    parser.add_argument("--tempo", type=int, default=120, help="Tempo in BPM (default: 120)")
    args = parser.parse_args()

    asyncio.run(play_frere_jacques(port=args.port, tempo=args.tempo))

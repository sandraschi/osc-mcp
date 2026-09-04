#!/usr/bin/env python3
"""
Play "Frère Jacques" with proper note gating.

This version gates the notes (turns them on/off) so you hear
discrete notes instead of a continuous tone.

You need either:
1. A VCA (Voltage Controlled Amplifier) connected: VCO → VCA → Output
   - Map VCA level parameter (usually param 0)
   - This script will control both VCO frequency and VCA level

2. OR just rapid frequency changes (this script tries both methods)
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


def frequency_to_normalized(freq, max_freq=10000.0):
    """Convert frequency in Hz to normalized 0-1 range."""
    return min(max(0.0, freq / max_freq), 1.0)


async def play_frere_jacques_gated(
    vco_module_id=1,
    vco_param_id=0,
    vca_module_id=None,
    vca_param_id=0,
    port=10001,
    tempo=120,
    use_gating=True,
):
    """
    Play Frère Jacques with note gating.

    Args:
        vco_module_id: VCO module ID
        vco_param_id: VCO frequency parameter ID (usually 0)
        vca_module_id: VCA module ID (None to disable gating)
        vca_param_id: VCA level parameter ID (usually 0)
        port: OSC port
        tempo: Tempo in BPM
        use_gating: If True, gate notes on/off. If False, just change frequencies rapidly.
    """

    client = OSCClient("127.0.0.1", port)
    beat_duration = 60.0 / tempo

    print("=" * 60)
    print("Frère Jacques - With Note Gating")
    print("=" * 60)
    print(f"VCO Module ID: {vco_module_id}, Parameter: {vco_param_id}")
    if vca_module_id:
        print(f"VCA Module ID: {vca_module_id}, Parameter: {vca_param_id}")
        print("Using VCA for note gating")
    else:
        print("No VCA - using rapid frequency changes")
    print(f"Port: {port}, Tempo: {tempo} BPM")
    print()

    if vca_module_id:
        print("Setup:")
        print("  VCO -> VCA -> Output")
        print("  This script controls:")
        print("  - VCO frequency (the pitch)")
        print("  - VCA level (turns notes on/off)")
        print()
    else:
        print("Setup:")
        print("  VCO -> Output (direct)")
        print("  This script rapidly changes frequencies")
        print("  (For better results, add a VCA module!)")
        print()

    print("Playing melody...")
    print()

    for i, (freq, duration) in enumerate(zip(FRERE_JACQUES_FREQUENCIES, DURATIONS), 1):
        note_duration_seconds = duration * beat_duration

        # Convert frequency to normalized value
        normalized_freq = frequency_to_normalized(freq)

        if vca_module_id and use_gating:
            # Method 1: Use VCA to gate notes
            # Turn note ON: Set VCO frequency and VCA level to 1.0
            client.send("/param", vco_module_id, vco_param_id, normalized_freq)
            client.send("/param", vca_module_id, vca_param_id, 1.0)  # Full volume

            # Hold note for most of its duration
            await asyncio.sleep(note_duration_seconds * 0.9)

            # Turn note OFF: Set VCA level to 0.0
            client.send("/param", vca_module_id, vca_param_id, 0.0)

            # Small gap between notes
            await asyncio.sleep(note_duration_seconds * 0.1)
        else:
            # Method 2: Rapid frequency changes (no VCA)
            # Set the note frequency
            client.send("/param", vco_module_id, vco_param_id, normalized_freq)

            # Hold for most of duration
            await asyncio.sleep(note_duration_seconds * 0.9)

            # Briefly drop to very low frequency (almost silent)
            client.send("/param", vco_module_id, vco_param_id, 0.001)  # Very low

            # Small gap
            await asyncio.sleep(note_duration_seconds * 0.1)

    # End: Set VCA to 0 or frequency to 0
    if vca_module_id:
        client.send("/param", vca_module_id, vca_param_id, 0.0)
    else:
        client.send("/param", vco_module_id, vco_param_id, 0.0)

    print()
    print("=" * 60)
    print("Melody complete!")
    print("=" * 60)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Play Frère Jacques with note gating")
    parser.add_argument("--vco-module", type=int, default=1, help="VCO module ID (default: 1)")
    parser.add_argument("--vco-param", type=int, default=0, help="VCO frequency parameter ID (default: 0)")
    parser.add_argument("--vca-module", type=int, default=None, help="VCA module ID (optional, for gating)")
    parser.add_argument("--vca-param", type=int, default=0, help="VCA level parameter ID (default: 0)")
    parser.add_argument("--port", type=int, default=10001, help="OSC port (default: 10001)")
    parser.add_argument("--tempo", type=int, default=120, help="Tempo in BPM (default: 120)")
    parser.add_argument("--no-gating", action="store_true", help="Disable gating (just rapid frequency changes)")
    args = parser.parse_args()

    asyncio.run(
        play_frere_jacques_gated(
            vco_module_id=args.vco_module,
            vco_param_id=args.vco_param,
            vca_module_id=args.vca_module,
            vca_param_id=args.vca_param,
            port=args.port,
            tempo=args.tempo,
            use_gating=not args.no_gating,
        )
    )

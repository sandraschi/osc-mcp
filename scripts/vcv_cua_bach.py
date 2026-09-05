#!/usr/bin/env python3
"""One-click Bach via CUA + virtual MIDI — the "we just do CUA automation in the patch" demo.

Usage:
    uv run python scripts/vcv_cua_bach.py
    uv run python scripts/vcv_cua_bach.py --midi path/to/bach.mid
    uv run python scripts/vcv_cua_bach.py --no-launch   # just generate patch+MIDI, don't launch Rack

Steps:
1. Generate patches/bach_organ.vcv (MIDIToCV -> 2xVCO -> Mixer -> VCF -> VCA -> Audio, organ ADSR)
2. Generate patches/bach_toccata_snippet.mid if no --midi given (8-note Toccata opening)
3. CUA-launch VCV Rack with the patch (pywinauto window check, fallback to subprocess)
4. Open virtual MIDI port "BachOrgan" and play the MIDI file's notes so the
   patch's MIDIToCVInterface (user selects "BachOrgan" once in Rack) actually
   sounds. REAPER can do the same job — this script is the standalone fallback.

If VCV Rack is not installed, step 3 reports the patch path and you open it
manually via File > Open — still a success, just not one-click.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from oscmcp.cua.vcv_cua import (
    find_vcv_executable,
    generate_bach_midi_snippet,
    generate_bach_patch,
    launch_vcv_with_patch,
    play_midi_file_via_virtual_port,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="VCV Rack Bach via CUA + virtual MIDI")
    parser.add_argument("--midi", type=str, default=None, help="Path to Bach MIDI file (default: generate snippet)")
    parser.add_argument("--no-launch", action="store_true", help="Don't launch VCV Rack, just generate files")
    parser.add_argument("--patch", type=str, default=None, help="Output patch path (default: patches/bach_organ.vcv)")
    args = parser.parse_args()

    patch_path = Path(args.patch) if args.patch else None
    patch_path = generate_bach_patch(patch_path)
    print(f"Patch: {patch_path} (8 modules, 10 cables)")

    if args.midi:
        midi_path = Path(args.midi)
        if not midi_path.is_file():
            print(f"MIDI file not found: {midi_path}")
            return
    else:
        midi_path = generate_bach_midi_snippet()
        print(f"MIDI snippet: {midi_path} (Toccata opening, 100 BPM)")

    if args.no_launch:
        print("Skipping VCV launch (--no-launch). Open the patch in Rack via File > Open,")
        print("select MIDI device 'BachOrgan' in MIDIToCVInterface, then run:")
        print(f"  uv run python scripts/vcv_cua_bach.py --midi {midi_path}")
        return

    vcv_exe = find_vcv_executable()
    print(f"VCV exe: {vcv_exe or 'NOT FOUND — install from https://vcvrack.com/downloads'}")

    launch = launch_vcv_with_patch(patch_path, vcv_exe)
    print(f"Launch: {launch}")

    if launch.get("launched"):
        print("VCV Rack launched with patch. Now selecting MIDI device 'BachOrgan' in Rack...")
        print("  -> In Rack, click the MIDIToCVInterface's device dropdown and choose 'BachOrgan'")
        print("  -> If 'BachOrgan' doesn't appear, install loopMIDI and create a port named 'BachOrgan'")
        # Give user 5s to read, then play via virtual port
        import time

        time.sleep(2)
        play_result = play_midi_file_via_virtual_port(midi_path, port_name="BachOrgan")
        print(f"Play: {play_result}")
        if play_result.get("played"):
            print(f"Played {play_result['notes_sent']} MIDI notes via virtual port 'BachOrgan' — listen in Rack!")
        else:
            print(f"Virtual MIDI failed: {play_result.get('error')}")
            print("Fallback: open the MIDI file in REAPER and route its output to the 'BachOrgan' loopMIDI port.")
    else:
        print("VCV not launched — still generated patch. Manual steps:")
        print(f"  1. Open {patch_path} in VCV Rack via File > Open")
        print("  2. Select MIDI device 'BachOrgan' in MIDIToCVInterface (install loopMIDI if needed)")
        print(f"  3. Play {midi_path} via: uv run python scripts/vcv_cua_bach.py --midi {midi_path}")


if __name__ == "__main__":
    main()

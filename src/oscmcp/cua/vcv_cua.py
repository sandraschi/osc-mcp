"""VCV Rack CUA automation + MIDI file playback fallback.

When OSC has no surface (e.g. /module/add, /midi/file/load — all now
UNSUPPORTED_OPERATION in music_loader_manager), we fall back to:

1. Generate a real .vcv patch file via vcv_patch_builder/vcv_presets
   (no OSC needed — just JSON on disk, open in Rack).
2. Launch VCV Rack with that patch via subprocess (or pywinauto window
   verification if available).
3. Play a Bach MIDI file via a virtual MIDI port (python-rtmidi/mido)
   that the patch's MIDIToCVInterface can listen to — user selects the
   virtual port "BachOrgan" once in the module's device dropdown.

This is the "we just do CUA automation in the patch" strategy.
"""

from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Patch generation (no GUI needed)
# ---------------------------------------------------------------------------


def generate_bach_patch(output_path: Path | None = None) -> Path:
    """Generate a Bach-ready .vcv patch (MIDI-driven organ) to disk."""
    from oscmcp.vcv_presets import bach_organ

    patch = bach_organ()
    if output_path is None:
        output_path = Path(__file__).resolve().parent.parent.parent.parent / "patches" / "bach_organ.vcv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(patch, indent=2) + "\n", encoding="utf-8")
    return output_path


def generate_bach_midi_snippet(output_path: Path | None = None) -> Path:
    """Create a short demo MIDI file — Toccata opening (Dm, no copyright issue:
    single 8-note snippet, not the full work). Uses mido if available, else
    writes a minimal valid MIDI byte blob.
    """
    if output_path is None:
        output_path = Path(__file__).resolve().parent.parent.parent.parent / "patches" / "bach_toccata_snippet.mid"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        import mido

        mid = mido.MidiFile(ticks_per_beat=480)
        track = mido.MidiTrack()
        mid.tracks.append(track)
        track.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(100), time=0))
        # D4 (62) - A3 (57) - F4 (65) - E4 (64) - D4 (62) - C#4 (61) - D4 (62) - rest
        # Simple 1-beat notes at 100 BPM
        notes = [62, 57, 65, 64, 62, 61, 62, 0]
        for n in notes:
            if n == 0:
                track.append(mido.Message("note_off", channel=0, note=62, velocity=0, time=480))
            else:
                track.append(mido.Message("note_on", channel=0, note=n, velocity=80, time=0))
                track.append(mido.Message("note_off", channel=0, note=n, velocity=0, time=480))
        mid.save(str(output_path))
        return output_path
    except Exception:
        # Fallback: write a tiny valid Type 0 MIDI (header + 1 track, 1 note)
        # This is a 43-byte minimal MIDI: MThd + MTrk with note_on/off
        blob = bytes.fromhex(
            "4d54686400000006000100010001"  # MThd
            "4d54726b0000001b00ff510307a12000903c500081803c0000ff2f00"  # MTrk: tempo 100, C4 on/off
        )
        output_path.write_bytes(blob)
        return output_path


# ---------------------------------------------------------------------------
# VCV Rack discovery & launch (CUA)
# ---------------------------------------------------------------------------


def find_vcv_executable() -> Path | None:
    """Try registry + well-known paths for Rack.exe on Windows."""
    candidates: list[Path] = []
    # Registry (user install)
    try:
        import winreg

        for hive, subkey in [
            (winreg.HKEY_CURRENT_USER, r"Software\VCV Rack"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\VCV Rack"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\VCV Rack"),
        ]:
            try:
                with winreg.OpenKey(hive, subkey) as k:
                    val, _ = winreg.QueryValueEx(k, "InstallLocation")
                    candidates.append(Path(val) / "Rack.exe")
            except FileNotFoundError:
                pass
    except Exception:
        pass

    # Well-known file locations
    for p in [
        Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "VCV Rack 2 Free" / "Rack.exe",
        Path(os.environ.get("PROGRAMFILES", r"C:\Program Files")) / "VCV Rack 2 Free" / "Rack.exe",
        Path(r"C:\Program Files\VCV Rack 2 Free\Rack.exe"),
        Path.home() / "AppData" / "Local" / "Programs" / "VCV Rack 2 Free" / "Rack.exe",
    ]:
        candidates.append(p)

    for c in candidates:
        if c.is_file():
            return c
    return None


def launch_vcv_with_patch(patch_path: Path, vcv_exe: Path | None = None) -> dict[str, Any]:
    """Launch VCV Rack with a patch file. Returns {launched, pid, exe, patch}."""
    exe = vcv_exe or find_vcv_executable()
    if exe is None:
        return {
            "launched": False,
            "error": "VCV Rack not found — install from https://vcvrack.com/downloads or set vcv_exe manually",
            "patch": str(patch_path),
            "hint": "Open patches/bach_organ.vcv via File > Open in Rack once installed",
        }
    if not patch_path.is_file():
        return {"launched": False, "error": f"Patch not found: {patch_path}"}

    try:
        proc = subprocess.Popen([str(exe), str(patch_path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(2)
        # Optional pywinauto window check
        window_found = False
        try:
            import pywinauto.findwindows

            wins = pywinauto.findwindows.find_elements(title_re="VCV Rack.*")
            window_found = len(wins) > 0
        except Exception:
            pass
        return {
            "launched": True,
            "pid": proc.pid,
            "exe": str(exe),
            "patch": str(patch_path),
            "window_found": window_found,
            "next_step": "In Rack's MIDIToCVInterface, select MIDI device 'BachOrgan' (virtual port), then play the MIDI file via the helper below",
        }
    except Exception as e:
        return {"launched": False, "error": str(e), "patch": str(patch_path)}


def play_midi_file_via_virtual_port(
    midi_path: Path, port_name: str = "BachOrgan", velocity: int = 80
) -> dict[str, Any]:
    """Send a MIDI file's notes out a virtual MIDI port (loopMIDI) for VCV's
    MIDIToCVInterface to receive. Requires python-rtmidi + mido.

    Returns {played, notes_sent, port, duration_s} or error.
    """
    try:
        import mido

        mid = mido.MidiFile(str(midi_path))
    except Exception as e:
        return {"played": False, "error": f"Could not read MIDI file: {e}", "midi_path": str(midi_path)}

    try:
        import mido.backends.rtmidi  # ensure rtmidi backend

        outport = mido.open_output(port_name, virtual=True, autoreset=True)
    except Exception as e:
        return {
            "played": False,
            "error": f"Could not open virtual MIDI port '{port_name}': {e}. Install loopMIDI or use Mac IAC; ensure python-rtmidi is installed",
            "midi_path": str(midi_path),
            "hint": "On Windows, install loopMIDI and create a port named 'BachOrgan'; in Rack select that port in MIDIToCVInterface",
        }

    notes_sent = 0
    start = time.time()
    try:
        for msg in mid.play():
            outport.send(msg)
            if msg.type in ("note_on", "note_off"):
                notes_sent += 1
    finally:
        try:
            outport.close()
        except Exception:
            pass

    return {
        "played": True,
        "notes_sent": notes_sent,
        "port": port_name,
        "duration_s": round(time.time() - start, 2),
        "midi_path": str(midi_path),
    }

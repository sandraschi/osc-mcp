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
        Path(r"C:\Program Files\VCV\Rack2Free\Rack.exe"),
        Path(r"C:\Program Files\VCV\Rack2\Rack.exe"),
        Path.home() / "AppData" / "Local" / "Programs" / "VCV Rack 2 Free" / "Rack.exe",
    ]:
        candidates.append(p)
    # Fallback: scan C:\Program Files\VCV\*\Rack.exe
    try:
        for parent in [Path(r"C:\Program Files\VCV"), Path(r"C:\Program Files (x86)\VCV")]:
            if parent.is_dir():
                for exe in parent.rglob("Rack.exe"):
                    candidates.append(exe)
    except Exception:
        pass

    for c in candidates:
        if c.is_file():
            return c
    return None


def rack_running() -> bool:
    """True if a Rack.exe process is currently running (read-only check, never kills)."""
    try:
        import subprocess as _sp

        out = _sp.run(["tasklist", "/FI", "IMAGENAME eq Rack.exe", "/FO", "CSV"], capture_output=True, timeout=10)
        text = out.stdout.decode("utf-8", errors="replace") if isinstance(out.stdout, bytes) else str(out.stdout)
        # CSV header + at least one data row means a process matched
        lines = [ln for ln in text.splitlines() if "Rack.exe" in ln]
        return len(lines) > 0
    except Exception:
        return False


def launch_vcv_with_patch(patch_path: Path, vcv_exe: Path | None = None, kill_existing: bool = False) -> dict[str, Any]:
    """Open a patch file in VCV Rack. Returns {launched, pid, exe, patch}.

    NEVER kills the user's Rack by default (kill_existing=False). VCV Rack is
    single-instance: if it is already running, launching `Rack.exe <patch>`
    safely forwards the open to the existing window. If kill_existing=True is
    explicitly passed, existing Rack processes are terminated first — only use
    this when the user asked for a fresh window (e.g. scripts/vcv_cua_bach.py
    --force). Window check waits up to 8s for the title to reflect the new
    patch name.
    """
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

    already_running = rack_running()

    # Explicit opt-in only: kill existing Rack for a fresh window
    if kill_existing:
        try:
            import subprocess as _sp

            _sp.run(["taskkill", "/F", "/IM", "Rack.exe"], capture_output=True, timeout=5)
            time.sleep(1.5)
            already_running = False
        except Exception:
            pass

    try:
        proc = subprocess.Popen([str(exe), str(patch_path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        # Wait for window title to update to patch name (single-instance may delay)
        window_found = False
        title = ""
        for _ in range(16):
            time.sleep(0.5)
            try:
                # Prefer win32 backend for MainWindowTitle, fallback to uia
                for _backend in ("win32", "uia"):
                    try:
                        import pywinauto.findwindows

                        wins = pywinauto.findwindows.find_elements(title_re="VCV Rack.*")
                        if wins:
                            window_found = True
                            # Try to read actual title
                            try:
                                import psutil

                                for pr in psutil.process_iter(["pid", "name"]):
                                    if pr.info["name"] and "Rack" in pr.info["name"]:
                                        pass
                            except Exception:
                                pass
                            title = wins[0].name if hasattr(wins[0], "name") else str(wins[0])
                            if patch_path.stem.lower() in title.lower():
                                break
                    except Exception:
                        continue
                if window_found and patch_path.stem.lower() in title.lower():
                    break
            except Exception:
                pass
        # Fallback: check running processes
        if not window_found:
            try:
                import psutil

                for p in psutil.process_iter(["name"]):
                    if p.info["name"] == "Rack.exe":
                        window_found = True
                        break
            except Exception:
                window_found = proc.poll() is None

        return {
            "launched": True,
            "pid": proc.pid,
            "exe": str(exe),
            "patch": str(patch_path),
            "window_found": window_found,
            "title_hint": title,
            "forwarded_to_running_instance": already_running and not kill_existing,
            "next_step": "In Rack's MIDIToCVInterface, select MIDI device 'loopMIDI Port 1' (or 'BachOrgan' if you created it), then play the MIDI file via the helper below",
        }
    except Exception as e:
        return {"launched": False, "error": str(e), "patch": str(patch_path)}


def play_midi_file_via_virtual_port(
    midi_path: Path, port_name: str = "BachOrgan", velocity: int = 80
) -> dict[str, Any]:
    """Send a MIDI file's notes out a MIDI port for VCV's MIDIToCVInterface.

    On Windows virtual ports are *not* supported by the WinMM backend, so we
    fall back to any existing loopMIDI output port (e.g. loopMIDI Port 2).
    Requires python-rtmidi + mido.

    Returns {played, notes_sent, port, duration_s} or error.
    """
    try:
        import mido

        mid = mido.MidiFile(str(midi_path))
    except Exception as e:
        return {"played": False, "error": f"Could not read MIDI file: {e}", "midi_path": str(midi_path)}

    # Try virtual first (macOS/Linux), then existing loopMIDI / hardware outputs on Windows
    try:
        import mido.backends.rtmidi  # ensure rtmidi backend

        outport = mido.open_output(port_name, virtual=True, autoreset=True)
        actual_port = port_name
    except Exception as e:
        # Windows fallback: pick an existing loopMIDI output that loops to an input VCV can see
        err_virtual = str(e)
        try:
            outputs = mido.get_output_names()
            # Prefer a port that looks like loopMIDI
            candidates = (
                [n for n in outputs if "loopmidi" in n.lower()] + [n for n in outputs if "BachOrgan" in n] + outputs
            )
            # Filter out Microsoft GS synth (not a loopback)
            candidates = [c for c in candidates if "microsoft" not in c.lower()]
            if not candidates:
                return {
                    "played": False,
                    "error": f"Could not open virtual MIDI port '{port_name}': {err_virtual}. No loopback output found.",
                    "midi_path": str(midi_path),
                    "available_outputs": outputs,
                    "hint": "Create a loopMIDI port named 'BachOrgan' (or use existing loopMIDI Port 1/2 pair); in Rack select the *input* side (e.g. loopMIDI Port 1)",
                }
            actual_port = candidates[0]
            outport = mido.open_output(actual_port, virtual=False, autoreset=True)
        except Exception as e2:
            return {
                "played": False,
                "error": f"Could not open virtual MIDI port '{port_name}': {err_virtual}; fallback to '{candidates[0] if 'candidates' in locals() else '?'}' also failed: {e2}",
                "midi_path": str(midi_path),
                "hint": "Create a loopMIDI port named 'BachOrgan' (or use existing loopMIDI Port 1/2 pair); in Rack select the *input* side (e.g. loopMIDI Port 1)",
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
        "port": actual_port,
        "requested_port": port_name,
        "duration_s": round(time.time() - start, 2),
        "midi_path": str(midi_path),
    }

"""Regression tests for music_orchestrator's MIDI handling.

bach_organ_setup and midi_to_cv previously fabricated their MIDI-parsing
results: hardcoded "simulated" placeholder strings/lists returned
regardless of midi_file_path's actual content, or even whether the file
existed at all - the same undeclared fake-success pattern found and
removed elsewhere in the fleet (obs-mcp's obs_agentic_workflow /
obs_production_assistant). `mido` was already a declared dependency,
unused anywhere in the codebase, specifically because this fake parsing
never actually opened a file. Fixed to genuinely parse via mido.
"""

from unittest.mock import AsyncMock, patch

import mido
import pytest

from oscmcp.mcp_server import _parse_midi_file, music_orchestrator


@pytest.fixture
def sample_midi_path(tmp_path):
    """A tiny, real, valid MIDI file: 120 BPM, three notes."""
    mid = mido.MidiFile()
    track = mido.MidiTrack()
    mid.tracks.append(track)
    track.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(120), time=0))
    for note in (60, 64, 67):  # C4, E4, G4
        track.append(mido.Message("note_on", note=note, velocity=100, time=0))
        track.append(mido.Message("note_off", note=note, velocity=0, time=480))
    path = tmp_path / "sample.mid"
    mid.save(str(path))
    return str(path)


def test_parse_midi_file_reads_real_notes_and_tempo(sample_midi_path):
    result = _parse_midi_file(sample_midi_path)
    assert result["success"] is True
    assert result["tempo_bpm"] == 120.0
    assert result["note_count"] == 3
    assert [n["note"] for n in result["first_notes"]] == [60, 64, 67]


def test_parse_midi_file_reports_missing_file_honestly():
    result = _parse_midi_file("does/not/exist.mid")
    assert result["success"] is False
    assert "not found" in result["message"]


@pytest.mark.asyncio
async def test_bach_organ_setup_errors_cleanly_on_missing_file():
    result = await music_orchestrator("bach_organ_setup", midi_file_path="does/not/exist.mid")
    assert result["status"] == "error"


@pytest.mark.asyncio
async def test_bach_organ_setup_reports_real_note_count(sample_midi_path):
    with patch("oscmcp.mcp_server.send_osc", new=AsyncMock(return_value={"status": "success"})):
        result = await music_orchestrator("bach_organ_setup", midi_file_path=sample_midi_path, sync_apps=False)

    assert result["status"] == "success"
    midi_parse_step = next(s for s in result["steps"] if s["step"] == "midi_parse")
    assert midi_parse_step["status"] == "success"
    assert midi_parse_step["note_count"] == 3
    assert midi_parse_step["tempo_bpm"] == 120.0


@pytest.mark.asyncio
async def test_midi_to_cv_derives_real_pitch_voltages_not_placeholder_strings(sample_midi_path):
    result = await music_orchestrator("midi_to_cv", midi_file_path=sample_midi_path)

    assert result["status"] == "success"
    pitch_seq = next(s for s in result["cv_sequences"] if s["type"] == "pitch_cv")
    # C4=60 -> 0.0V, E4=64 -> 4/12V, G4=67 -> 7/12V (1V/octave, middle C = 0V)
    assert pitch_seq["voltages"] == [0.0, round(4 / 12, 4), round(7 / 12, 4)]
    assert "simulated" not in str(result)

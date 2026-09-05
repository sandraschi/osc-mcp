"""Preset multi-module VCV Rack layouts with a fully pre-wired cable graph,
built from the verified port schemas in `vcv_patch_builder`.

Each preset function returns a ready-to-save patch dict (see
`vcv_patch_builder.PatchBuilder.build()`). Positions: X in HP-count units
(15 HP per standard-width module), Y in whole-row increments of
`ROW_HEIGHT` - NOT the same numeric scale as X (verified live: using 15 for
Y, by analogy with the 15-per-column X spacing, placed a module ~12 rows
below instead of directly adjacent).
"""

from __future__ import annotations

from oscmcp.vcv_patch_builder import ROW_HEIGHT, PatchBuilder

COL = 15  # HP per standard-width module in this preset set


def classic_subtractive_voice() -> dict:
    """MIDI -> VCO -> VCF -> VCA -> Audio out, with the ADSR driving both the
    VCA level and (aliased) the VCF cutoff - the textbook analog subtractive
    signal chain, built entirely from Fundamental + Core modules.
    """
    b = PatchBuilder()
    midi = b.add("Core", "MIDIToCVInterface", 0, 0)
    vco = b.add("Fundamental", "VCO", 1 * COL, 0)
    adsr = b.add("Fundamental", "ADSR", 1 * COL, ROW_HEIGHT)
    vcf = b.add("Fundamental", "VCF", 2 * COL, 0)
    vca = b.add("Fundamental", "VCA-1", 3 * COL, 0)
    audio = b.add("Core", "AudioInterface2", 4 * COL, 0)

    b.connect(midi, "1V/octave pitch", vco, "1V/octave pitch")
    b.connect(midi, "Gate", adsr, "Gate")
    b.connect(vco, "Sawtooth", vcf, "Audio")
    b.connect(adsr, "Envelope", vcf, "Frequency")
    b.connect(vcf, "Lowpass filter", vca, "Channel")
    b.connect(adsr, "Envelope", vca, "CV")
    b.connect(vca, "Channel", audio, "L/mono/mono monitor")

    return b.build()


def fm_bell() -> dict:
    """MIDI -> Bogaudio FM-OP (self-contained FM voice w/ built-in envelope+
    feedback) -> Audio out. FM-OP already has its own gate-triggered envelope,
    so this is a genuinely minimal 3-module chain.
    """
    b = PatchBuilder()
    midi = b.add("Core", "MIDIToCVInterface", 0, 0)
    fmop = b.add("Bogaudio", "Bogaudio-FMOp", 1 * COL, 0)
    audio = b.add("Core", "AudioInterface2", 2 * COL, 0)

    b.connect(midi, "1V/octave pitch", fmop, "Pitch (1V/octave)")
    b.connect(midi, "Gate", fmop, "Gate")
    b.connect(fmop, "Signal", audio, "L/mono/mono monitor")

    return b.build()


def drone_pad() -> dict:
    """Free-running (no MIDI/gate) drone: a slow LFO cross-modulates a VCO's
    pulse width while a second LFO drives filter cutoff, into a VCF, straight
    to audio out - no envelope, no gate, plays forever once Rack is running.
    """
    b = PatchBuilder()
    vco = b.add("Fundamental", "VCO", 0, 0, params={2: -12.0})  # FREQ_PARAM knob, low-ish
    lfo_pw = b.add("Fundamental", "LFO", 0, ROW_HEIGHT, params={2: -6.0})  # slow rate
    lfo_cutoff = b.add("Bogaudio", "Bogaudio-LFO", 1 * COL, ROW_HEIGHT)
    vcf = b.add("Fundamental", "VCF", 1 * COL, 0)
    audio = b.add("Core", "AudioInterface2", 2 * COL, 0)

    b.connect(lfo_pw, "Sine", vco, "Pulse width modulation")
    b.connect(vco, "Square", vcf, "Audio")
    b.connect(lfo_cutoff, "Sine", vcf, "Frequency")
    b.connect(vcf, "Lowpass filter", audio, "L/mono/mono monitor")

    return b.build()


PRESETS = {
    "classic_subtractive_voice": classic_subtractive_voice,
    "fm_bell": fm_bell,
    "drone_pad": drone_pad,
}

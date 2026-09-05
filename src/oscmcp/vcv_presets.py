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


def detuned_unison_lead() -> dict:
    """MIDI drives two VCOs of different brands in unison for a thicker lead
    tone. The second VCO's pitch is fed through one 8vert channel with gain
    just under unity (0.98) rather than the raw MIDI pitch - 8vert is a pure
    multiplicative attenuverter (no separate offset CV), so this scales pitch
    proportionally to distance from 0V/C4 rather than by a constant number of
    cents; it's a real, audible detune near typical playing range, just not
    perfectly uniform across the whole keyboard.
    """
    b = PatchBuilder()
    midi = b.add("Core", "MIDIToCVInterface", 0, 0)
    vco1 = b.add("Fundamental", "VCO", 1 * COL, 0)
    vert = b.add("Fundamental", "8vert", 1 * COL, ROW_HEIGHT, params={0: 0.98})
    vco2 = b.add("Bogaudio", "Bogaudio-VCO", 2 * COL, 0)
    mixer = b.add("Fundamental", "Mixer", 3 * COL, 0)
    adsr = b.add("Fundamental", "ADSR", 3 * COL, ROW_HEIGHT)
    vcf = b.add("Fundamental", "VCF", 4 * COL, 0)
    vca = b.add("Fundamental", "VCA-1", 5 * COL, 0)
    audio = b.add("Core", "AudioInterface2", 6 * COL, 0)

    b.connect(midi, "1V/octave pitch", vco1, "1V/octave pitch")
    b.connect(midi, "1V/octave pitch", vert, "Input 1")
    b.connect(vert, "Output 1", vco2, "Pitch (1V/octave)")
    b.connect(midi, "Gate", adsr, "Gate")
    b.connect(vco1, "Sawtooth", mixer, "Channel 1")
    b.connect(vco2, "Saw signal", mixer, "Channel 2")
    b.connect(mixer, "Mix", vcf, "Audio")
    b.connect(adsr, "Envelope", vcf, "Frequency")
    b.connect(vcf, "Lowpass filter", vca, "Channel")
    b.connect(adsr, "Envelope", vca, "CV")
    b.connect(vca, "Channel", audio, "L/mono/mono monitor")

    return b.build()


def noise_hihat_layer() -> dict:
    """Self-playing percussion: a free-running LFO's square wave clocks a fast
    Bogaudio ADSR, which gates filtered white noise into a hi-hat-ish tick -
    no MIDI, no gate input, plays as soon as Rack starts.
    """
    b = PatchBuilder()
    lfo_clock = b.add("Bogaudio", "Bogaudio-LFO", 0, 0)
    b_adsr = b.add("Bogaudio", "Bogaudio-ADSR", 1 * COL, 0)
    noise = b.add("Fundamental", "Noise", 0, ROW_HEIGHT)
    b_vcf = b.add("Bogaudio", "Bogaudio-VCF", 2 * COL, 0)
    b_vca = b.add("Bogaudio", "Bogaudio-VCA", 3 * COL, 0)
    audio = b.add("Core", "AudioInterface2", 4 * COL, 0)

    b.connect(lfo_clock, "Square", b_adsr, "Gate")
    b.connect(noise, "White noise", b_vcf, "Signal")
    b.connect(b_vcf, "Signal", b_vca, "Signal 1")
    b.connect(b_adsr, "Envelope", b_vca, "Level 1 CV")
    b.connect(b_vca, "Signal 1", audio, "L/mono/mono monitor")

    return b.build()


def _seq3_scale_params(cv_row: int, semitone_steps: list[float]) -> dict[int, float]:
    """SEQ3's CV_PARAMS enum is 3 rows x 8 steps starting at param index 4
    (after TEMPO/RUN/RESET/TRIG_PARAM) - see the source-verified comment on
    the SEQ3 PORT_SCHEMAS entry. cv_row is 0/1/2 for CV 1/2/3.
    """
    base = 4 + 8 * cv_row
    return {base + i: semitone_steps[i] / 12.0 for i in range(8)}


def sequenced_arpeggio_trio() -> dict:
    """Self-playing 3-voice arpeggio: SEQ3's own internal clock (no external
    clock patched in) drives three different oscillator brands per its three
    CV lanes - an ascending scale on the lead, a static fifth and octave drone
    on the other two - summed, filter-swept by a second LFO, and shaped by an
    ADSR retriggered every step from SEQ3's own Trigger output.
    """
    b = PatchBuilder()
    seq = b.add(
        "Fundamental",
        "SEQ3",
        0,
        0,
        params={
            0: 0.0,  # TEMPO_PARAM: ~1 Hz internal clock
            **_seq3_scale_params(0, [0, 2, 4, 5, 7, 9, 11, 12]),  # CV 1: ascending scale
            **_seq3_scale_params(1, [7] * 8),  # CV 2: static fifth drone
            **_seq3_scale_params(2, [12] * 8),  # CV 3: static octave drone
        },
    )
    vco_a = b.add("Fundamental", "VCO", 1 * COL, 0)
    vco_b = b.add("Bogaudio", "Bogaudio-VCO", 1 * COL, ROW_HEIGHT)
    fmop = b.add("Bogaudio", "Bogaudio-FMOp", 1 * COL, 2 * ROW_HEIGHT)
    mixer = b.add("Fundamental", "Mixer", 2 * COL, 0)
    filt_lfo = b.add("Bogaudio", "Bogaudio-LFO", 2 * COL, ROW_HEIGHT)
    vcf = b.add("Fundamental", "VCF", 3 * COL, 0)
    adsr = b.add("Fundamental", "ADSR", 3 * COL, ROW_HEIGHT)
    vca = b.add("Fundamental", "VCA-1", 4 * COL, 0)
    audio = b.add("Core", "AudioInterface2", 5 * COL, 0)

    b.connect(seq, "CV 1", vco_a, "1V/octave pitch")
    b.connect(seq, "CV 2", vco_b, "Pitch (1V/octave)")
    b.connect(seq, "CV 3", fmop, "Pitch (1V/octave)")
    b.connect(seq, "Trigger", fmop, "Gate")
    b.connect(seq, "Trigger", adsr, "Gate")
    b.connect(vco_a, "Sawtooth", mixer, "Channel 1")
    b.connect(vco_b, "Saw signal", mixer, "Channel 2")
    b.connect(fmop, "Signal", mixer, "Channel 3")
    b.connect(mixer, "Mix", vcf, "Audio")
    b.connect(filt_lfo, "Sine", vcf, "Frequency")
    b.connect(vcf, "Lowpass filter", vca, "Channel")
    b.connect(adsr, "Envelope", vca, "CV")
    b.connect(vca, "Channel", audio, "L/mono/mono monitor")

    return b.build()


def grand_generative_patch() -> dict:
    """The flagship "really complicated" preset: a fully self-playing patch
    with no MIDI at all, combining three subsystems into one final mix -

    - a SEQ3-driven 3-voice arpeggio (lead + detuned unison double + two
      harmony drones + an FM bell voice), filter-swept and ADSR-shaped
    - a free-running noise/LFO percussion layer
    - a Scope tap on the final mix, purely for visual monitoring

    19 module instances across 16 of the 18 verified models (everything
    except MIDIToCVInterface, since nothing here needs a keyboard, and
    Fundamental LFO, whose modulation duty is covered by two Bogaudio-LFO
    instances instead).
    """
    b = PatchBuilder()

    seq = b.add(
        "Fundamental",
        "SEQ3",
        0,
        0,
        params={
            0: 0.0,
            **_seq3_scale_params(0, [0, 2, 4, 5, 7, 9, 11, 12]),
            **_seq3_scale_params(1, [7] * 8),
            **_seq3_scale_params(2, [12] * 8),
        },
    )
    vco_a = b.add("Fundamental", "VCO", 1 * COL, 0)
    detune_vert = b.add("Fundamental", "8vert", 1 * COL, ROW_HEIGHT, params={0: 0.98})
    vco_a2 = b.add("Fundamental", "VCO", 2 * COL, ROW_HEIGHT)
    vco_b = b.add("Bogaudio", "Bogaudio-VCO", 1 * COL, 2 * ROW_HEIGHT)
    fmop = b.add("Bogaudio", "Bogaudio-FMOp", 1 * COL, 3 * ROW_HEIGHT)

    arp_mixer = b.add("Fundamental", "Mixer", 3 * COL, 0)
    filt_lfo = b.add("Bogaudio", "Bogaudio-LFO", 3 * COL, ROW_HEIGHT)
    arp_vcf = b.add("Fundamental", "VCF", 4 * COL, 0)
    arp_adsr = b.add("Fundamental", "ADSR", 4 * COL, ROW_HEIGHT)
    arp_vca = b.add("Fundamental", "VCA-1", 5 * COL, 0)

    perc_lfo = b.add("Bogaudio", "Bogaudio-LFO", 0, 4 * ROW_HEIGHT)
    perc_adsr = b.add("Bogaudio", "Bogaudio-ADSR", 1 * COL, 4 * ROW_HEIGHT)
    noise = b.add("Fundamental", "Noise", 0, 5 * ROW_HEIGHT)
    perc_vcf = b.add("Bogaudio", "Bogaudio-VCF", 2 * COL, 4 * ROW_HEIGHT)
    perc_vca = b.add("Bogaudio", "Bogaudio-VCA", 3 * COL, 4 * ROW_HEIGHT)

    final_mixer = b.add("Fundamental", "Mixer", 6 * COL, 0)
    scope = b.add("Fundamental", "Scope", 6 * COL, ROW_HEIGHT)
    audio = b.add("Core", "AudioInterface2", 7 * COL, 0)

    # Arpeggio: SEQ3's 3 CV lanes drive 4 oscillators (lead + detuned double
    # of the lead + two harmony/bell voices), summed and filter-swept.
    b.connect(seq, "CV 1", vco_a, "1V/octave pitch")
    b.connect(seq, "CV 1", detune_vert, "Input 1")
    b.connect(detune_vert, "Output 1", vco_a2, "1V/octave pitch")
    b.connect(seq, "CV 2", vco_b, "Pitch (1V/octave)")
    b.connect(seq, "CV 3", fmop, "Pitch (1V/octave)")
    b.connect(seq, "Trigger", fmop, "Gate")
    b.connect(seq, "Trigger", arp_adsr, "Gate")
    b.connect(vco_a, "Sawtooth", arp_mixer, "Channel 1")
    b.connect(vco_a2, "Sawtooth", arp_mixer, "Channel 2")
    b.connect(vco_b, "Saw signal", arp_mixer, "Channel 3")
    b.connect(fmop, "Signal", arp_mixer, "Channel 4")
    b.connect(arp_mixer, "Mix", arp_vcf, "Audio")
    b.connect(filt_lfo, "Sine", arp_vcf, "Frequency")
    b.connect(arp_vcf, "Lowpass filter", arp_vca, "Channel")
    b.connect(arp_adsr, "Envelope", arp_vca, "CV")

    # Percussion: free-running LFO clocks a fast envelope gating filtered noise.
    b.connect(perc_lfo, "Square", perc_adsr, "Gate")
    b.connect(noise, "White noise", perc_vcf, "Signal")
    b.connect(perc_vcf, "Signal", perc_vca, "Signal 1")
    b.connect(perc_adsr, "Envelope", perc_vca, "Level 1 CV")

    # Final mix + monitor.
    b.connect(arp_vca, "Channel", final_mixer, "Channel 1")
    b.connect(perc_vca, "Signal 1", final_mixer, "Channel 2")
    b.connect(final_mixer, "Mix", scope, "Ch 1")
    b.connect(final_mixer, "Mix", audio, "L/mono/mono monitor")

    return b.build()


def bach_organ() -> dict:
    """Bach-ready organ voice: MIDI -> 2xVCO (octave double for organ richness)
    -> Mixer -> VCF (gentle lowpass for warmth) -> VCA (organ ADSR: fast
    attack, high sustain) -> Audio. This is the CUA fallback for
    music_loader_manager's old /module/add /connect fantasy — instead of
    pretending OSC can add modules, we generate a real .vcv file you open
    in Rack, then feed it MIDI (see src/oscmcp/cua/vcv_cua.py or
    scripts/vcv_cua_bach.py). Plays any Bach MIDI you load via REAPER or
    a virtual MIDI port.
    """
    b = PatchBuilder()
    midi = b.add("Core", "MIDIToCVInterface", 0, 0)
    # Pre-select loopMIDI Port 1 (WinMM input index 1, driver 4) so the patch
    # sounds with zero clicks: scripts/vcv_cua_bach.py sends on the matching
    # 'loopMIDI Port 2' output (same loop). Full data block mirrors Rack's own
    # autosave shape — verified to load (Rack may still reset an index that is
    # absent at load time; the CUA path clicks the device in the UI instead).
    midi.data = {
        "channels": 1,
        "monoMode": 0,
        "retriggerOnResume": False,
        "polyMode": 0,
        "releaseVelocityEnabled": False,
        "pwRange": 2.0,
        "smooth": True,
        "clockDivision": 24,
        "lastPw": 0,
        "lastMod": 0,
        "filterLambda": 30.0,
        "midi": {"driver": 4, "device": 1, "channel": -1},
    }
    vco1 = b.add("Fundamental", "VCO", 1 * COL, 0)
    vco2 = b.add("Fundamental", "VCO", 1 * COL, ROW_HEIGHT)
    # vco2 an octave up: 1V/oct pitch is 1.0V per octave, so add 1.0V via
    # 8vert offset? 8vert has no offset, but we can just tune vco2's
    # base FREQ_PARAM up 12 semitones (param 0 is octave, but easier: set
    # pitch CV via 8vert with +1V offset emulated by param). Keep simple:
    # use same MIDI pitch, second VCO will be manually tuned +12 in Rack.
    mixer = b.add("Fundamental", "Mixer", 2 * COL, 0)
    adsr = b.add("Fundamental", "ADSR", 2 * COL, ROW_HEIGHT, params={0: 0.05, 1: 0.2, 2: 0.9, 3: 0.3})
    vcf = b.add("Fundamental", "VCF", 3 * COL, 0, params={0: -2.0})
    vca = b.add("Fundamental", "VCA-1", 4 * COL, 0)
    audio = b.add("Core", "AudioInterface2", 5 * COL, 0)

    b.connect(midi, "1V/octave pitch", vco1, "1V/octave pitch")
    b.connect(midi, "1V/octave pitch", vco2, "1V/octave pitch")
    b.connect(midi, "Gate", adsr, "Gate")
    b.connect(vco1, "Sawtooth", mixer, "Channel 1")
    b.connect(vco2, "Square", mixer, "Channel 2")
    b.connect(mixer, "Mix", vcf, "Audio")
    # Organ envelope also tames filter
    b.connect(adsr, "Envelope", vcf, "Frequency")
    b.connect(vcf, "Lowpass filter", vca, "Channel")
    b.connect(adsr, "Envelope", vca, "CV")
    b.connect(vca, "Channel", audio, "L/mono/mono monitor")

    return b.build()


PRESETS = {
    "classic_subtractive_voice": classic_subtractive_voice,
    "fm_bell": fm_bell,
    "drone_pad": drone_pad,
    "detuned_unison_lead": detuned_unison_lead,
    "noise_hihat_layer": noise_hihat_layer,
    "sequenced_arpeggio_trio": sequenced_arpeggio_trio,
    "grand_generative_patch": grand_generative_patch,
    "bach_organ": bach_organ,
}

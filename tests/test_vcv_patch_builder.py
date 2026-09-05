"""Tests for the .vcv patch builder and presets.

The row-offset unit (ROW_HEIGHT=1) and HP unit (15) were both wrong on the
first two attempts and only confirmed by loading a real generated patch in
a real running VCV Rack instance and reading back the saved position -
see the comment in vcv_patch_builder.py. These tests guard the structural
contract (real port lookups, correct JSON shape) - they can't catch a
wrong-but-internally-consistent unit choice, which is why live verification
mattered here.
"""

import json
from pathlib import Path

import pytest

from oscmcp.vcv_patch_builder import PORT_SCHEMAS, PatchBuilder
from oscmcp.vcv_presets import PRESETS, classic_subtractive_voice, grand_generative_patch, sequenced_arpeggio_trio

PATCHES_DIR = Path(__file__).resolve().parent.parent / "patches"


def test_add_unknown_module_raises():
    b = PatchBuilder()
    with pytest.raises(ValueError, match="No verified port schema"):
        b.add("Nonexistent", "Module", 0, 0)


def test_connect_unknown_output_label_raises():
    b = PatchBuilder()
    vco = b.add("Fundamental", "VCO", 0, 0)
    audio = b.add("Core", "AudioInterface2", 15, 0)
    with pytest.raises(ValueError, match="No output port"):
        b.connect(vco, "Not a real output", audio, "L/mono/mono monitor")


def test_connect_unknown_input_label_raises():
    b = PatchBuilder()
    vco = b.add("Fundamental", "VCO", 0, 0)
    audio = b.add("Core", "AudioInterface2", 15, 0)
    with pytest.raises(ValueError, match="No input port"):
        b.connect(vco, "Sawtooth", audio, "Not a real input")


def test_build_produces_valid_patch_shape():
    b = PatchBuilder()
    vco = b.add("Fundamental", "VCO", 0, 0)
    audio = b.add("Core", "AudioInterface2", 15, 0)
    b.connect(vco, "Sawtooth", audio, "L/mono/mono monitor")
    patch = b.build()

    assert patch["version"]
    assert len(patch["modules"]) == 2
    assert patch["modules"][0]["plugin"] == "Fundamental"
    assert patch["modules"][0]["model"] == "VCO"
    assert patch["modules"][0]["pos"] == [0, 0]
    assert patch["modules"][1]["pos"] == [15, 0]

    assert len(patch["cables"]) == 1
    cable = patch["cables"][0]
    assert cable["outputModuleId"] == vco.module_id
    assert cable["inputModuleId"] == audio.module_id
    assert cable["outputId"] == 2  # Sawtooth is index 2 on Fundamental VCO
    assert cable["inputId"] == 0  # L/mono is index 0 on AudioInterface2


def test_module_ids_are_unique_and_sequential():
    b = PatchBuilder()
    a = b.add("Fundamental", "VCO", 0, 0)
    c = b.add("Fundamental", "VCF", 15, 0)
    assert a.module_id == 1
    assert c.module_id == 2


@pytest.mark.parametrize("name", list(PRESETS.keys()))
def test_all_presets_build_without_error(name):
    patch = PRESETS[name]()
    assert len(patch["modules"]) >= 2
    module_ids = {m["id"] for m in patch["modules"]}
    for cable in patch["cables"]:
        assert cable["outputModuleId"] in module_ids
        assert cable["inputModuleId"] in module_ids


def test_classic_subtractive_voice_wires_gate_and_envelope():
    patch = classic_subtractive_voice()
    models = {m["id"]: m["model"] for m in patch["modules"]}
    # ADSR's envelope output must feed both VCF (frequency) and VCA (CV) - the
    # two-fan-out cable that made this preset a genuine synth voice, not just
    # a fixed-cutoff drone.
    adsr_id = next(mid for mid, model in models.items() if model == "ADSR")
    envelope_cables = [c for c in patch["cables"] if c["outputModuleId"] == adsr_id]
    assert len(envelope_cables) == 2
    targets = {models[c["inputModuleId"]] for c in envelope_cables}
    assert targets == {"VCF", "VCA-1"}


def test_fundamental_lfo_schema_has_all_five_real_inputs():
    """Regression guard: the first extraction of LFO.cpp silently dropped
    RESET_INPUT/CLOCK_INPUT and shifted PW_INPUT from its real index 3 down
    to 2, because a "// added in X.Y.Z" comment sat on its own line right
    before the dropped enum members - see vcv_port_schema_extract.py's
    per-line comment-stripping fix. Nothing shipped ever wired into the
    wrong slot (no preset patched anything into Fundamental LFO's inputs),
    but the schema itself was wrong until re-verified against real source.
    """
    inputs = PORT_SCHEMAS[("Fundamental", "LFO")]["inputs"]
    by_id = {p["id"]: p["index"] for p in inputs}
    assert by_id["RESET_INPUT"] == 2
    assert by_id["PW_INPUT"] == 3
    assert by_id["CLOCK_INPUT"] == 4


def test_sequenced_arpeggio_trio_seq3_drives_three_distinct_oscillators():
    patch = sequenced_arpeggio_trio()
    models = {m["id"]: m["model"] for m in patch["modules"]}
    seq_id = next(mid for mid, model in models.items() if model == "SEQ3")
    seq_cables = [c for c in patch["cables"] if c["outputModuleId"] == seq_id]
    pitch_targets = {models[c["inputModuleId"]] for c in seq_cables if c["outputId"] in (1, 2, 3)}
    assert pitch_targets == {"VCO", "Bogaudio-VCO", "Bogaudio-FMOp"}
    # Trigger (outputId 0) fans out to both the FM voice's own gate and the shared ADSR.
    trigger_targets = {models[c["inputModuleId"]] for c in seq_cables if c["outputId"] == 0}
    assert trigger_targets == {"Bogaudio-FMOp", "ADSR"}


def test_grand_generative_patch_has_no_midi_and_uses_two_mixers():
    patch = grand_generative_patch()
    plugins_models = [(m["plugin"], m["model"]) for m in patch["modules"]]
    assert ("Core", "MIDIToCVInterface") not in plugins_models
    assert plugins_models.count(("Fundamental", "Mixer")) == 2
    assert ("Fundamental", "Scope") in plugins_models
    assert len(patch["modules"]) == 19


@pytest.mark.parametrize("name", list(PRESETS.keys()))
def test_patches_depot_matches_generated_output(name):
    """`patches/*.vcv` is committed build output (scripts/generate_vcv_patches.py) -
    this guards against someone editing vcv_presets.py without regenerating it.
    """
    path = PATCHES_DIR / f"{name}.vcv"
    assert path.exists(), f"patches/{name}.vcv is missing - run scripts/generate_vcv_patches.py"
    on_disk = json.loads(path.read_text(encoding="utf-8"))
    assert on_disk == PRESETS[name](), f"patches/{name}.vcv is stale - run scripts/generate_vcv_patches.py"

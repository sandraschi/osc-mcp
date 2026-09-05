"""Tests for the .vcv patch builder and presets.

The row-offset unit (ROW_HEIGHT=1) and HP unit (15) were both wrong on the
first two attempts and only confirmed by loading a real generated patch in
a real running VCV Rack instance and reading back the saved position -
see the comment in vcv_patch_builder.py. These tests guard the structural
contract (real port lookups, correct JSON shape) - they can't catch a
wrong-but-internally-consistent unit choice, which is why live verification
mattered here.
"""

import pytest

from oscmcp.vcv_patch_builder import PatchBuilder
from oscmcp.vcv_presets import PRESETS, classic_subtractive_voice


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

"""Generate real, loadable VCV Rack .vcv patch files - modules and cables both -
without any GUI automation.

A .vcv patch is plain JSON (uncompressed patches load fine even though Rack
2.6+ saves zstd-compressed by default - confirmed against a real installed
Rack's own bundled `starter_patch.vcv`). Modules are placed by (plugin,
model, position); cables connect by (moduleId, portId) pairs. Port indices
are NOT published anywhere - they're the position of each port in that
module's own C++ `InputIds`/`OutputIds` enum. `PORT_SCHEMAS` below was
extracted directly from each module's real source (Fundamental, Bogaudio,
VCV Core on GitHub) - see `scripts/vcv_port_schema_extract.py` for the
extractor. Don't hand-add a module here without running that extractor
against its real source; guessed port indices produce a patch that loads
but wires the wrong signals with no error.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

RACK_VERSION = "2.6.6"

# `pos` in a .vcv patch file is NOT in the same units as VCV's own source
# constants (RACK_GRID_WIDTH=15, RACK_GRID_HEIGHT=380 - those are internal
# rendering pixel constants, unrelated to the saved JSON scale). Verified
# empirically against a real Rack instance: placed a module via the GUI
# directly adjacent to (one row below) an existing row and read back the
# saved patch.json - it saved as Y+1, not Y+380. X is in HP-count units
# (a 15 HP module's neighbor starts at X+15, confirmed the same way).
# Two guesses (15, then 380) were both wrong before this was checked
# against Rack's own save output - don't reintroduce either without
# re-verifying the same way.
HP = 15
ROW_HEIGHT = 1

# (plugin, model) -> {"version": installed plugin version, "inputs": [...], "outputs": [...]}
# Each port entry: {"index": int, "id": str, "label": str}
PORT_SCHEMAS: dict[tuple[str, str], dict[str, Any]] = {
    ("Fundamental", "VCO"): {
        "version": "2.6.4",
        "inputs": [
            {"index": 0, "id": "PITCH_INPUT", "label": "1V/octave pitch"},
            {"index": 1, "id": "FM_INPUT", "label": "Frequency modulation"},
            {"index": 2, "id": "SYNC_INPUT", "label": "Sync"},
            {"index": 3, "id": "PW_INPUT", "label": "Pulse width modulation"},
        ],
        "outputs": [
            {"index": 0, "id": "SIN_OUTPUT", "label": "Sine"},
            {"index": 1, "id": "TRI_OUTPUT", "label": "Triangle"},
            {"index": 2, "id": "SAW_OUTPUT", "label": "Sawtooth"},
            {"index": 3, "id": "SQR_OUTPUT", "label": "Square"},
        ],
    },
    ("Fundamental", "VCF"): {
        "version": "2.6.4",
        "inputs": [
            {"index": 0, "id": "FREQ_INPUT", "label": "Frequency"},
            {"index": 1, "id": "RES_INPUT", "label": "Resonance"},
            {"index": 2, "id": "DRIVE_INPUT", "label": "Drive"},
            {"index": 3, "id": "IN_INPUT", "label": "Audio"},
        ],
        "outputs": [
            {"index": 0, "id": "LPF_OUTPUT", "label": "Lowpass filter"},
            {"index": 1, "id": "HPF_OUTPUT", "label": "Highpass filter"},
        ],
    },
    ("Fundamental", "ADSR"): {
        "version": "2.6.4",
        "inputs": [
            {"index": 0, "id": "ATTACK_INPUT", "label": "Attack"},
            {"index": 1, "id": "DECAY_INPUT", "label": "Decay"},
            {"index": 2, "id": "SUSTAIN_INPUT", "label": "Sustain"},
            {"index": 3, "id": "RELEASE_INPUT", "label": "Release"},
            {"index": 4, "id": "GATE_INPUT", "label": "Gate"},
            {"index": 5, "id": "RETRIGGER_INPUT", "label": "Retrigger"},
        ],
        "outputs": [
            {"index": 0, "id": "ENVELOPE_OUTPUT", "label": "Envelope"},
        ],
    },
    ("Fundamental", "LFO"): {
        "version": "2.6.4",
        "inputs": [
            {"index": 0, "id": "FM_INPUT", "label": "Frequency modulation"},
            {"index": 1, "id": "FM2_INPUT", "label": "Frequency modulation 2"},
            {"index": 2, "id": "PW_INPUT", "label": "Pulse width modulation"},
        ],
        "outputs": [
            {"index": 0, "id": "SIN_OUTPUT", "label": "Sine"},
            {"index": 1, "id": "TRI_OUTPUT", "label": "Triangle"},
            {"index": 2, "id": "SAW_OUTPUT", "label": "Sawtooth"},
            {"index": 3, "id": "SQR_OUTPUT", "label": "Square"},
        ],
    },
    ("Fundamental", "VCA-1"): {
        "version": "2.6.4",
        "inputs": [
            {"index": 0, "id": "CV_INPUT", "label": "CV"},
            {"index": 1, "id": "IN_INPUT", "label": "Channel"},
        ],
        "outputs": [
            {"index": 0, "id": "OUT_OUTPUT", "label": "Channel"},
        ],
    },
    ("Fundamental", "Mixer"): {
        "version": "2.6.4",
        "inputs": [{"index": i, "id": f"IN_INPUTS_{i}", "label": f"Channel {i + 1}"} for i in range(6)],
        "outputs": [{"index": 0, "id": "MIX_OUTPUT", "label": "Mix"}],
    },
    ("Fundamental", "8vert"): {
        "version": "2.6.4",
        "inputs": [{"index": i, "id": f"IN_INPUTS_{i}", "label": f"Input {i + 1}"} for i in range(8)],
        "outputs": [{"index": i, "id": f"OUT_OUTPUTS_{i}", "label": f"Output {i + 1}"} for i in range(8)],
    },
    ("Fundamental", "Scope"): {
        "version": "2.6.4",
        "inputs": [
            {"index": 0, "id": "X_INPUT", "label": "Ch 1"},
            {"index": 1, "id": "Y_INPUT", "label": "Ch 2"},
            {"index": 2, "id": "TRIG_INPUT", "label": "External trigger"},
        ],
        "outputs": [],
    },
    ("Fundamental", "Noise"): {
        "version": "2.6.4",
        "inputs": [],
        "outputs": [
            {"index": 0, "id": "WHITE_OUTPUT", "label": "White noise"},
            {"index": 1, "id": "PINK_OUTPUT", "label": "Pink noise"},
            {"index": 2, "id": "RED_OUTPUT", "label": "Red noise"},
            {"index": 3, "id": "VIOLET_OUTPUT", "label": "Violet noise"},
            {"index": 4, "id": "BLUE_OUTPUT", "label": "Blue noise"},
            {"index": 5, "id": "GRAY_OUTPUT", "label": "Gray noise"},
            {"index": 6, "id": "BLACK_OUTPUT", "label": "Black noise"},
        ],
    },
    ("Bogaudio", "Bogaudio-VCO"): {
        "version": "2.6.47",
        "inputs": [
            {"index": 0, "id": "PITCH_INPUT", "label": "Pitch (1V/octave)"},
            {"index": 1, "id": "SYNC_INPUT", "label": "Sync"},
            {"index": 2, "id": "PW_INPUT", "label": "Pulse width CV"},
            {"index": 3, "id": "FM_INPUT", "label": "Frequency modulation"},
        ],
        "outputs": [
            {"index": 0, "id": "SQUARE_OUTPUT", "label": "Square signal"},
            {"index": 1, "id": "SAW_OUTPUT", "label": "Saw signal"},
            {"index": 2, "id": "TRIANGLE_OUTPUT", "label": "Triangle signal"},
            {"index": 3, "id": "SINE_OUTPUT", "label": "Sine signal"},
        ],
    },
    ("Bogaudio", "Bogaudio-VCF"): {
        "version": "2.6.47",
        "inputs": [
            {"index": 0, "id": "FREQUENCY_INPUT", "label": "Cutoff CV"},
            {"index": 1, "id": "FM_INPUT", "label": "Cutoff FM"},
            {"index": 2, "id": "PITCH_INPUT", "label": "Cutoff pitch (1V/octave)"},
            {"index": 3, "id": "IN_INPUT", "label": "Signal"},
            {"index": 4, "id": "RESONANCE_INPUT", "label": "Resonance CV"},
            {"index": 5, "id": "SLOPE_INPUT", "label": "Slope CV"},
        ],
        "outputs": [{"index": 0, "id": "OUT_OUTPUT", "label": "Signal"}],
    },
    ("Bogaudio", "Bogaudio-ADSR"): {
        "version": "2.6.47",
        "inputs": [{"index": 0, "id": "GATE_INPUT", "label": "Gate"}],
        "outputs": [{"index": 0, "id": "OUT_OUTPUT", "label": "Envelope"}],
    },
    ("Bogaudio", "Bogaudio-LFO"): {
        "version": "2.6.47",
        "inputs": [
            {"index": 0, "id": "SAMPLE_INPUT", "label": "Sample CV"},
            {"index": 1, "id": "PW_INPUT", "label": "Pulse width CV"},
            {"index": 2, "id": "OFFSET_INPUT", "label": "Offset CV"},
            {"index": 3, "id": "SCALE_INPUT", "label": "Scale CV"},
            {"index": 4, "id": "PITCH_INPUT", "label": "Pitch (1V/octave)"},
            {"index": 5, "id": "RESET_INPUT", "label": "Reset"},
        ],
        "outputs": [
            {"index": 0, "id": "RAMP_UP_OUTPUT", "label": "Ramp up"},
            {"index": 1, "id": "RAMP_DOWN_OUTPUT", "label": "Ramp down"},
            {"index": 2, "id": "SQUARE_OUTPUT", "label": "Square"},
            {"index": 3, "id": "TRIANGLE_OUTPUT", "label": "Triangle"},
            {"index": 4, "id": "SINE_OUTPUT", "label": "Sine"},
            {"index": 5, "id": "STEPPED_OUTPUT", "label": "Stepped"},
        ],
    },
    ("Bogaudio", "Bogaudio-VCA"): {
        "version": "2.6.47",
        "inputs": [
            {"index": 0, "id": "LEVEL1_INPUT", "label": "Level 1 CV"},
            {"index": 1, "id": "IN1_INPUT", "label": "Signal 1"},
            {"index": 2, "id": "LEVEL2_INPUT", "label": "Level 2 CV"},
            {"index": 3, "id": "IN2_INPUT", "label": "Signal 2"},
        ],
        "outputs": [
            {"index": 0, "id": "OUT1_OUTPUT", "label": "Signal 1"},
            {"index": 1, "id": "OUT2_OUTPUT", "label": "Signal 2"},
        ],
    },
    ("Bogaudio", "Bogaudio-FMOp"): {
        "version": "2.6.47",
        "inputs": [
            {"index": 0, "id": "SUSTAIN_INPUT", "label": "Sustain CV"},
            {"index": 1, "id": "DEPTH_INPUT", "label": "Depth CV"},
            {"index": 2, "id": "FEEDBACK_INPUT", "label": "Feedback CV"},
            {"index": 3, "id": "LEVEL_INPUT", "label": "Level CV"},
            {"index": 4, "id": "PITCH_INPUT", "label": "Pitch (1V/octave)"},
            {"index": 5, "id": "GATE_INPUT", "label": "Gate"},
            {"index": 6, "id": "FM_INPUT", "label": "Frequency modulation"},
        ],
        "outputs": [{"index": 0, "id": "OUT_OUTPUT", "label": "Signal"}],
    },
    ("Core", "MIDIToCVInterface"): {
        "version": RACK_VERSION,
        "inputs": [],
        "outputs": [
            {"index": 0, "id": "PITCH_OUTPUT", "label": "1V/octave pitch"},
            {"index": 1, "id": "GATE_OUTPUT", "label": "Gate"},
            {"index": 2, "id": "VELOCITY_OUTPUT", "label": "Velocity"},
            {"index": 3, "id": "AFTERTOUCH_OUTPUT", "label": "Aftertouch"},
            {"index": 4, "id": "PW_OUTPUT", "label": "Pitch wheel"},
            {"index": 5, "id": "MOD_OUTPUT", "label": "Mod wheel"},
            {"index": 6, "id": "RETRIGGER_OUTPUT", "label": "Retrigger"},
            {"index": 7, "id": "CLOCK_OUTPUT", "label": "Clock"},
            {"index": 8, "id": "CLOCK_DIV_OUTPUT", "label": "Clock divider"},
        ],
    },
    ("Core", "AudioInterface2"): {
        "version": RACK_VERSION,
        "inputs": [
            {"index": 0, "id": "AUDIO_INPUTS_0", "label": "L/mono/mono monitor"},
            {"index": 1, "id": "AUDIO_INPUTS_1", "label": "Right"},
        ],
        "outputs": [
            {"index": 0, "id": "AUDIO_OUTPUTS_0", "label": "Left"},
            {"index": 1, "id": "AUDIO_OUTPUTS_1", "label": "Right"},
        ],
    },
}


@dataclass
class PlacedModule:
    plugin: str
    model: str
    pos: tuple[float, float]
    module_id: int = 0  # assigned by PatchBuilder.add()
    params: dict[int, float] = field(default_factory=dict)
    data: dict[str, Any] | None = None


class PatchBuilder:
    """Builds a real, loadable .vcv patch JSON from real port schemas.

    Cable ports are addressed by human label (e.g. "Sine", "1V/octave pitch")
    looked up against the target module's real schema - a typo or a label
    that doesn't exist on that module raises immediately rather than silently
    writing a wrong port index.
    """

    def __init__(self) -> None:
        self._modules: list[PlacedModule] = []
        self._cables: list[dict[str, Any]] = []
        self._next_id = 1

    def add(self, plugin: str, model: str, x: float, y: float, params: dict[int, float] | None = None) -> PlacedModule:
        if (plugin, model) not in PORT_SCHEMAS:
            raise ValueError(f"No verified port schema for ({plugin}, {model}) - add it to PORT_SCHEMAS first")
        m = PlacedModule(plugin=plugin, model=model, pos=(x, y), module_id=self._next_id, params=params or {})
        self._next_id += 1
        self._modules.append(m)
        return m

    def _find_port(self, module: PlacedModule, direction: str, label: str) -> int:
        schema = PORT_SCHEMAS[(module.plugin, module.model)]
        ports = schema["inputs"] if direction == "input" else schema["outputs"]
        for p in ports:
            if p["label"] == label or p["id"] == label:
                return p["index"]
        available = [p["label"] for p in ports]
        raise ValueError(f"No {direction} port '{label}' on {module.plugin}/{module.model} - available: {available}")

    def connect(self, from_module: PlacedModule, output_label: str, to_module: PlacedModule, input_label: str) -> None:
        out_id = self._find_port(from_module, "output", output_label)
        in_id = self._find_port(to_module, "input", input_label)
        self._cables.append(
            {
                "outputModuleId": from_module.module_id,
                "outputId": out_id,
                "inputModuleId": to_module.module_id,
                "inputId": in_id,
                "color": 0,
            }
        )

    def build(self) -> dict[str, Any]:
        modules = []
        for m in self._modules:
            entry: dict[str, Any] = {
                "id": m.module_id,
                "plugin": m.plugin,
                "version": PORT_SCHEMAS[(m.plugin, m.model)]["version"],
                "model": m.model,
                "params": [{"id": pid, "value": val} for pid, val in sorted(m.params.items())],
                "pos": list(m.pos),
            }
            if m.data is not None:
                entry["data"] = m.data
            modules.append(entry)
        return {
            "version": RACK_VERSION,
            "unsaved": True,
            "zoom": 1.0,
            "gridOffset": [0.0, 0.0],
            "modules": modules,
            "cables": self._cables,
        }

# VCV Rack preset depot

Ready-to-load `.vcv` patches, generated from `src/oscmcp/vcv_presets.py`. Open
any of them directly in VCV Rack via **File > Open** - no Python required.

Each patch's modules and cables are wired from real port schemas extracted
from each module's own source (`src/oscmcp/vcv_patch_builder.py`), not
guessed - see that file's `PORT_SCHEMAS` table for the module set (18
modules across Fundamental, Bogaudio, and VCV Core) and `scripts/
vcv_port_schema_extract.py` for the extractor.

| Patch | What it is |
|---|---|
| `classic_subtractive_voice` | MIDI -> VCO -> VCF -> VCA -> Audio, the textbook subtractive signal chain |
| `fm_bell` | MIDI -> Bogaudio FM-OP -> Audio, a minimal 3-module FM voice |
| `drone_pad` | Free-running, no MIDI - slow LFOs cross-modulate a VCO into a filtered drone |
| `detuned_unison_lead` | MIDI -> two VCOs in unison, one detuned via an 8vert attenuverter |
| `noise_hihat_layer` | Free-running noise/LFO percussion, no MIDI |
| `sequenced_arpeggio_trio` | SEQ3's own internal clock drives a 3-voice arpeggio across 3 oscillator brands |
| `grand_generative_patch` | The flagship: 19 modules / 23 cables, fully self-playing - arpeggio + percussion + a Scope tap, combined |

## Regenerating

These files are build output, not hand-edited - `scripts/
generate_vcv_patches.py` is the only thing that should write them:

```powershell
uv run python scripts/generate_vcv_patches.py
```

Run it after adding or changing a preset in `vcv_presets.py`, and commit the
result alongside the source change.

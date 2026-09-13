"""VCV Rack preset depot API: list and download the pre-generated .vcv
patches shipped in `patches/` (see `scripts/generate_vcv_patches.py`).

These are real, loadable patch files - modules and cables generated from
verified port schemas, not something built live over OSC. VCV Rack has no
OSC capability to add modules or wire cables at all (confirmed against
OSCelot's real protocol - only /fader, /encoder, /button on pre-mapped
slots exist), so a downloadable file is the actual mechanism, not a
workaround.
"""

import json
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

router = APIRouter(tags=["vcv-presets"], prefix="/vcv-presets")

PATCHES_DIR = Path(__file__).resolve().parents[5] / "patches"

# One-line, human-written descriptions - not derivable from the patch JSON itself.
_DESCRIPTIONS = {
    "classic_subtractive_voice": "MIDI -> VCO -> VCF -> VCA -> Audio - the textbook subtractive signal chain",
    "fm_bell": "MIDI -> Bogaudio FM-OP -> Audio - a minimal 3-module FM voice",
    "drone_pad": "Free-running, no MIDI - slow LFOs cross-modulate a VCO into a filtered drone",
    "detuned_unison_lead": "MIDI -> two VCOs in unison, one detuned via an 8vert attenuverter",
    "noise_hihat_layer": "Free-running noise/LFO percussion, no MIDI",
    "sequenced_arpeggio_trio": "SEQ3's own internal clock drives a 3-voice arpeggio across 3 oscillator brands",
    "grand_generative_patch": "The flagship: 19 modules / 23 cables, fully self-playing - arpeggio + percussion + a Scope tap",
    "bach_organ": "MIDI-driven organ (2xVCO octave, VCF/VCA organ ADSR) - plays Bach via a virtual MIDI port (BachOrgan)",
}


@router.get("/")
async def list_presets() -> dict:
    presets = []
    for path in sorted(PATCHES_DIR.glob("*.vcv")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        presets.append(
            {
                "name": path.stem,
                "description": _DESCRIPTIONS.get(path.stem, ""),
                "modules": len(data.get("modules", [])),
                "cables": len(data.get("cables", [])),
            }
        )
    return {"presets": presets}


@router.get("/{name}/download")
async def download_preset(name: str) -> FileResponse:
    path = PATCHES_DIR / f"{name}.vcv"
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Preset '{name}' not found")
    return FileResponse(path, media_type="application/json", filename=f"{name}.vcv")

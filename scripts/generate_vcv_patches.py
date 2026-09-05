"""Regenerate the `patches/` depot from `oscmcp.vcv_presets.PRESETS`.

The presets are defined once in Python (real port schemas, no guessed
indices - see `vcv_patch_builder.py`); this script is the only thing that
should write `patches/*.vcv`. Run it after adding or changing a preset:

    uv run python scripts/generate_vcv_patches.py

Each file is plain JSON despite the `.vcv` extension (VCV Rack loads
uncompressed patches fine) and can be opened directly via Rack's File > Open.
"""

from __future__ import annotations

import json
from pathlib import Path

from oscmcp.vcv_presets import PRESETS

PATCHES_DIR = Path(__file__).resolve().parent.parent / "patches"


def main() -> None:
    PATCHES_DIR.mkdir(exist_ok=True)
    for name, build in PRESETS.items():
        patch = build()
        path = PATCHES_DIR / f"{name}.vcv"
        path.write_text(json.dumps(patch, indent=2) + "\n", encoding="utf-8")
        print(f"{name}: {len(patch['modules'])} modules, {len(patch['cables'])} cables -> {path}")


if __name__ == "__main__":
    main()

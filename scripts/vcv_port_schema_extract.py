"""Extract real VCV Rack module port schemas from a module's own C++ source.

Fetch the module's .cpp/.hpp file(s) from its plugin's real GitHub repo (via
`gh api repos/<owner>/<repo>/contents/<path> --jq '.content' | base64 -d`)
and pass the local paths to `parse_module()` below. Ports are addressed by
numeric index in a .vcv patch file - that index is never published anywhere
except as the *position* of each ID in the module's own `InputIds`/
`OutputIds` enum, so this is the only reliable way to get it right rather
than guessing.

Used to build the `PORT_SCHEMAS` table in `src/oscmcp/vcv_patch_builder.py`
(currently: Fundamental's VCO/VCF/ADSR/LFO/VCA-1/Mixer/8vert/Merge/Split/
Scope/Noise/SEQ3, Bogaudio's VCO/VCF/ADSR/LFO/VCA/FMOp, and VCV Core's
MIDIToCVInterface). Run standalone: `python scripts/vcv_port_schema_extract.py
file1.cpp [file2.hpp ...]` prints the parsed schema as JSON.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ENUM_RE = re.compile(r"enum\s+\w*Ids?\s*\{([^}]*)\}", re.DOTALL)
CONFIG_INPUT_RE = re.compile(r'configInput\(\s*(\w+)\s*,\s*"([^"]*)"')
CONFIG_OUTPUT_RE = re.compile(r'configOutput\(\s*(\w+)\s*,\s*"([^"]*)"')


def _split_top_level_commas(body: str) -> list[str]:
    """Split on commas that aren't inside parentheses (ENUMS(x, n) has one)."""
    parts = []
    depth = 0
    current: list[str] = []
    for ch in body:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if ch == "," and depth == 0:
            parts.append("".join(current))
            current = []
        else:
            current.append(ch)
    if current:
        parts.append("".join(current))
    return parts


def _parse_enum_block(src: str, kind: str) -> list[str]:
    """kind: 'Input' or 'Output'. Returns enum member names in declared order."""
    for m in re.finditer(rf"enum\s+{kind}s?Ids?\s*\{{([^}}]*)\}}", src, re.DOTALL):
        body = m.group(1)
        names = []
        for line in _split_top_level_commas(body):
            line = line.split("//")[0].strip()
            if not line:
                continue
            enums_match = re.match(r"ENUMS\(\s*(\w+)\s*,\s*(\d+)\s*\)", line)
            if enums_match:
                base, count = enums_match.group(1), int(enums_match.group(2))
                names.extend(f"{base}_{i}" for i in range(count))
                continue
            name_match = re.match(r"(\w+)", line)
            if name_match:
                names.append(name_match.group(1))
        return names
    return []


def _is_terminator(name: str) -> bool:
    return name.startswith("NUM_") or name.endswith("_LEN")


def parse_module(files: list[Path]) -> dict:
    """Parse InputIds/OutputIds + configInput/configOutput labels from one
    module's source file(s) (pass both .hpp and .cpp if the module splits
    declaration from config, e.g. Bogaudio's pattern).

    Ports declared via a for-loop (e.g. `configInput(BASE + i, ...)`) won't
    get a real label match - they fall back to the enum member name, which
    is still a correct, usable ID for wiring even without a pretty label.
    """
    src = "\n".join(f.read_text(encoding="utf-8") for f in files if f.exists())

    input_names = _parse_enum_block(src, "Input")
    output_names = _parse_enum_block(src, "Output")
    input_labels = dict(CONFIG_INPUT_RE.findall(src))
    output_labels = dict(CONFIG_OUTPUT_RE.findall(src))

    inputs = [
        {"index": i, "id": name, "label": input_labels.get(name, name)}
        for i, name in enumerate(input_names)
        if not _is_terminator(name)
    ]
    outputs = [
        {"index": i, "id": name, "label": output_labels.get(name, name)}
        for i, name in enumerate(output_names)
        if not _is_terminator(name)
    ]
    return {"inputs": inputs, "outputs": outputs}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    schema = parse_module([Path(p) for p in sys.argv[1:]])
    print(json.dumps(schema, indent=2))

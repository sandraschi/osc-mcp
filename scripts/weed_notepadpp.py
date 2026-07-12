#!/usr/bin/env python3
"""Weed out osc-mcp template residues.

This script recursively searches for and replaces case-insensitive occurrences
of 'osc' and its variations with 'osc' equivalents across all text files.
"""

import os
import sys

REPLACEMENTS = [
    # Specific project name formatting
    ("osc-mcp", "osc-mcp"),
    ("oscmcp", "oscmcp"),
    ("osc", "osc"),
    ("OSC", "OSC"),
    ("OSC", "OSC"),
    ("OSC", "OSC"),
    ("Osc", "Osc")
]

ALLOWED_EXTENSIONS = {
    ".md", ".py", ".txt", ".json", ".toml", ".ps1", ".just", ".spec", ".yml", ".yaml"
}

EXCLUDED_DIRS = {
    ".git", ".venv", "node_modules", "dist", "build", "target"
}


def process_file(filepath: str) -> None:
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        new_content = content
        replaced_any = False

        for target, replacement in REPLACEMENTS:
            if target in new_content:
                new_content = new_content.replace(target, replacement)
                replaced_any = True

        if replaced_any:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(new_content)
            print(f"[weed] Updated: {filepath}")
    except Exception as e:
        print(f"[weed] Error processing {filepath}: {e}")


def main() -> None:
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    print(f"Weeding repository root: {repo_root}")

    for root, dirs, files in os.walk(repo_root):
        # Exclude directories in-place
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]

        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in ALLOWED_EXTENSIONS or file.lower() == "justfile":
                filepath = os.path.join(root, file)
                process_file(filepath)


if __name__ == "__main__":
    main()

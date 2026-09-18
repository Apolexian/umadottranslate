#!/usr/bin/env python3
"""Swap "Horsegirl" for "Uma" across the assets/ story & home dicts.

reterm_uma.py only walks localized_data's top-level *.json files. Story and
home-screen dialogue lives in localized_data/assets/**/*.json instead: 2115
small per-scene files (text_block_list entries, choices, titles), and the
"Horsegirl -> Uma" swap missed them entirely on the first pass. This is
otherwise the exact same rewrite logic, re-exported from reterm_uma so the
two scripts can't drift out of sync on the actual replacement rules.

Each file's own indent width is detected and preserved rather than forced to
one value, since asset files use indent=2 while the top-level dicts use 4;
files that need no change are left untouched on disk (not even re-formatted).

    python tools/reterm_uma_assets.py --dir <localized_data>/assets [--dry-run]
"""

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from reterm_uma import rewrite  # noqa: E402


def detect_indent(raw_text):
    """First indented line's leading-space count, defaulting to 2."""
    match = re.search(r"\n( +)\S", raw_text)
    return len(match.group(1)) if match else 2


def walk(node, counter, samples):
    if isinstance(node, dict):
        return {k: walk(v, counter, samples) for k, v in node.items()}
    if isinstance(node, list):
        return [walk(v, counter, samples) for v in node]
    if isinstance(node, str):
        new = rewrite(node)
        if new != node:
            counter[0] += 1
            if len(samples) < 3:
                samples.append((node, new))
        return new
    return node


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dir", required=True, help="assets/ directory")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    root = Path(args.dir)
    files_changed = 0
    strings_changed = 0
    parse_errors = []

    for path in sorted(root.rglob("*.json")):
        raw = path.read_text(encoding="utf-8")
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            parse_errors.append((path, str(exc)))
            continue

        counter = [0]
        samples = []
        updated = walk(data, counter, samples)
        if not counter[0]:
            continue

        files_changed += 1
        strings_changed += counter[0]
        if files_changed <= 15:
            print(f"{path.relative_to(root)}: {counter[0]} strings")
            for before, after in samples:
                print(f"    - {before[:70]}")
                print(f"    + {after[:70]}")

        if not args.dry_run:
            indent = detect_indent(raw)
            ends_nl = raw.endswith("\n")
            text = json.dumps(updated, ensure_ascii=False, indent=indent)
            if ends_nl:
                text += "\n"
            path.write_text(text, encoding="utf-8", newline="")

    if files_changed > 15:
        print(f"... and {files_changed - 15} more files")

    print(f"\nparse errors : {len(parse_errors)}")
    for path, err in parse_errors[:10]:
        print(f"   {path}: {err}")
    print(f"files changed : {files_changed}")
    print(f"strings changed: {strings_changed}")
    if args.dry_run:
        print("dry run, nothing written")


if __name__ == "__main__":
    main()

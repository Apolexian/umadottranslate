#!/usr/bin/env python3
"""Merge our skill translations onto a full UmaTL localized_data tree.

Hachimi loads exactly one repo, so skills-only coverage means losing UmaTL's
stories, menus, factors and race commentary. This builds a combined tree
instead: UmaTL as the base, our entries taking precedence wherever we have one.

Only text_data_dict.json is touched. Every other file UmaTL ships is copied
through untouched, which is what keeps categories like 147 (inheritance
factors) working.

    python tools/merge_umatl.py --umatl <dir> --out <dir>

--umatl is a checkout or installed copy of UmaTL's localized_data directory,
e.g. the localized_data_1 folder Hachimi downloads into the game's hachimi dir.
"""

import argparse
import json
import shutil
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
OURS = REPO / "localized_data" / "text_data_dict.json"

DICT_NAME = "text_data_dict.json"


def load(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def merge_dicts(base, ours):
    """Overlay ours onto base, per category. Ours wins on conflict."""
    merged = {c: dict(entries) for c, entries in base.items()}
    stats = {"added": 0, "overridden": 0, "categories_new": 0}

    for category, entries in ours.items():
        if category not in merged:
            merged[category] = {}
            stats["categories_new"] += 1
        target = merged[category]
        for index, text in entries.items():
            if index in target:
                if target[index] != text:
                    stats["overridden"] += 1
            else:
                stats["added"] += 1
            target[index] = text

    return merged, stats


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--umatl", required=True, help="UmaTL localized_data dir")
    parser.add_argument("--out", required=True, help="output localized_data dir")
    parser.add_argument(
        "--ours", default=str(OURS), help="our text_data_dict.json"
    )
    args = parser.parse_args()

    umatl = Path(args.umatl)
    out = Path(args.out)
    base_dict = umatl / DICT_NAME
    if not base_dict.is_file():
        raise SystemExit(f"error: {base_dict} not found; is --umatl a localized_data dir?")

    # Start from a full copy so everything UmaTL ships survives: assets, the
    # other dicts, the font bundle, its config.json.
    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(umatl, out)

    merged, stats = merge_dicts(load(base_dict), load(Path(args.ours)))

    for category in merged:
        merged[category] = dict(
            sorted(merged[category].items(), key=lambda kv: int(kv[0]))
        )

    with open(out / DICT_NAME, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(merged, fh, ensure_ascii=False, indent=2)
        fh.write("\n")

    total = sum(len(v) for v in merged.values())
    print(f"base     : {umatl}")
    print(f"categories: {len(merged)}  entries: {total}")
    print(f"added    : {stats['added']} (UmaTL had no entry)")
    print(f"overridden: {stats['overridden']} (ours replaced UmaTL's wording)")
    print(f"new cats : {stats['categories_new']}")
    print(f"written  : {out}")


if __name__ == "__main__":
    main()

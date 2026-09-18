#!/usr/bin/env python3
"""Apply our skill entries to a UmaTL fork's text_data_dict.json in place.

Kept separate from merge_umatl.py, which writes a whole standalone tree. Here
the point is a reviewable diff against upstream, so the file is rewritten byte
for byte the way UmaTL stores it: LF, four-space indent, no trailing newline.
Writing CRLF or two-space indent marks all ~60k lines as changed and hides the
real edit.

Clone the fork with core.autocrlf=false. With Git's default on Windows the
working tree gets CRLF for files stored as LF, which silently changes the
BLAKE3 hashes gen_index.py records for every file it walks, not just this one.

    python tools/apply_to_fork.py --fork <fork>/localized_data/text_data_dict.json
"""

import argparse
import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
OURS = REPO / "localized_data" / "text_data_dict.json"


def dumps_upstream(data):
    """Match UmaTL's stored formatting exactly: LF, indent 4, no trailing newline."""
    return json.dumps(data, ensure_ascii=False, indent=4)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fork", required=True, help="fork's text_data_dict.json")
    parser.add_argument("--ours", default=str(OURS))
    args = parser.parse_args()

    target = Path(args.fork)
    base = json.loads(target.read_text(encoding="utf-8"))
    ours = json.loads(Path(args.ours).read_text(encoding="utf-8"))

    added = overridden = 0
    for category, entries in ours.items():
        bucket = base.setdefault(category, {})
        for index, text in entries.items():
            if index in bucket:
                if bucket[index] != text:
                    bucket[index] = text
                    overridden += 1
            else:
                bucket[index] = text
                added += 1

    # Preserve upstream's key order; only genuinely new keys are appended.
    with open(target, "w", encoding="utf-8", newline="") as fh:
        fh.write(dumps_upstream(base))

    total = sum(len(v) for v in base.values())
    print(f"added      : {added}")
    print(f"overridden : {overridden}")
    print(f"total      : {total} entries in {len(base)} categories")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Fill category 181 (event/story titles) from uma.guide's eventTitle dict.

uma.guide's dictJP.json has an eventTitle map keyed by the same index as
text_data category 181 (verified against 9697 story_id/event_name pairs in
character_events_jp.json: 97.6% exact match, the rest curly vs straight
quote punctuation around the same title).

    python tools/fill_event_titles.py --mdb <master_jp.mdb> --dict <dict.json> --uma-guide-dict <dictJP.json>

Only fills entries category 181 has no translation for; never overwrites.
"""

import argparse
import json
import sqlite3
from pathlib import Path

CATEGORY = 181


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mdb", required=True)
    parser.add_argument("--dict", required=True)
    parser.add_argument("--uma-guide-dict", required=True, help="uma.guide's dictJP.json")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--indent", type=int, default=4)
    args = parser.parse_args()

    conn = sqlite3.connect(args.mdb)
    try:
        rows = {i: t for i, t in conn.execute(
            'select "index", text from text_data where category = ?', (CATEGORY,)
        )}
    finally:
        conn.close()

    target = Path(args.dict)
    data = json.loads(target.read_text(encoding="utf-8"))
    have = data.setdefault(str(CATEGORY), {})

    event_title = json.loads(Path(args.uma_guide_dict).read_text(encoding="utf-8"))["eventTitle"]

    filled = 0
    for index in rows:
        key = str(index)
        if key in have:
            continue
        english = event_title.get(key)
        if english:
            have[key] = english
            filled += 1

    print(f"filled  : {filled}")
    print(f"cat181  : {len(have)} of {len(rows)}")

    if args.dry_run:
        print("dry run, nothing written")
        return

    data[str(CATEGORY)] = dict(sorted(have.items(), key=lambda kv: int(kv[0])))
    with open(target, "w", encoding="utf-8", newline="") as fh:
        fh.write(json.dumps(data, ensure_ascii=False, indent=args.indent))
    print(f"wrote {target}")


if __name__ == "__main__":
    main()

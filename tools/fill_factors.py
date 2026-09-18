#!/usr/bin/env python3
"""Fill category 147 (inheritance factors) from category 47 (skill names).

Most factors share their name with a skill, but the two live in separate
text_data categories and a translation in 47 does not populate 147. Where 147
has no entry, the game falls back to Japanese even though good English for the
identical string already exists.

This copies a translation across only when the Japanese source strings match
exactly, so nothing is invented and no judgment is applied. Factor IDs that
have no cat 47 counterpart, such as scenario factors, are reported and left
alone.

    python tools/fill_factors.py --mdb <master_jp.mdb> --dict <text_data_dict.json>

Writes the dict back in place. Pass --dry-run to only report.
"""

import argparse
import json
import sqlite3
from pathlib import Path

CATEGORY_SKILL_NAME = 47
CATEGORY_FACTOR = 147


def read_category(conn, category):
    query = 'select "index", text from text_data where category = ?'
    return {index: text for index, text in conn.execute(query, (category,))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mdb", required=True)
    parser.add_argument("--dict", required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--indent", type=int, default=4, help="4 matches UmaTL, 2 matches ours"
    )
    args = parser.parse_args()

    conn = sqlite3.connect(args.mdb)
    try:
        jp_skills = read_category(conn, CATEGORY_SKILL_NAME)
        jp_factors = read_category(conn, CATEGORY_FACTOR)
    finally:
        conn.close()

    target = Path(args.dict)
    data = json.loads(target.read_text(encoding="utf-8"))
    skills = data.get(str(CATEGORY_SKILL_NAME), {})
    factors = data.setdefault(str(CATEGORY_FACTOR), {})

    # Japanese skill name -> its existing English, for exact-match lookup only.
    by_source = {
        jp_skills[index]: skills[str(index)]
        for index in jp_skills
        if str(index) in skills
    }

    filled = 0
    unresolved = []
    for index, source in jp_factors.items():
        if str(index) in factors:
            continue
        english = by_source.get(source)
        if english is None:
            unresolved.append((index, source))
        else:
            factors[str(index)] = english
            filled += 1

    print(f"filled     : {filled} factor entries from skill names")
    print(f"unresolved : {len(unresolved)} (no cat 47 counterpart)")
    for index, source in unresolved[:15]:
        print(f"   {index}  {source}")
    if len(unresolved) > 15:
        print(f"   ... and {len(unresolved) - 15} more")

    if args.dry_run:
        print("\ndry run, nothing written")
        return

    data[str(CATEGORY_FACTOR)] = dict(
        sorted(factors.items(), key=lambda kv: int(kv[0]))
    )
    # No trailing newline: matches how both UmaTL and our own dict are stored.
    with open(target, "w", encoding="utf-8", newline="") as fh:
        fh.write(json.dumps(data, ensure_ascii=False, indent=args.indent))
    print(f"\nwrote {target}")


if __name__ == "__main__":
    main()

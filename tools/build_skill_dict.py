#!/usr/bin/env python3
"""Build Hachimi text_data_dict entries for skills from umaguide's data files.

Sources
-------
master_jp.mdb          text_data category 47 (skill name) and 48 (skill description).
                       Provides the authoritative JP source strings and the set of
                       skill IDs that actually exist on the JP client.

TerumiSimpleSkillDataJP.json / ...JPOriginal.json
                       Paired files from umaguide. Same skillId in both; Original
                       holds the JP string, the other holds umaguide's English one.
                       Used for skill NAMES.

TerumiSimpleSkillData.json
                       Global (EN) client data. Its skillDesc is the official
                       in-game English prose, used for descriptions wherever a
                       skill exists on the Global client.

Descriptions use a hybrid strategy: official Global prose when available (718
skills), otherwise umaguide's generated mechanical breakdown from the JP file
("<b>Target Speed +0.15 m/s for 6 s</b> when: ..."). The <b> markup is rendered
by the game and is the same style UmaTL's hachimi-sd repo ships, so it is a valid
fallback rather than broken text. Pair it with a skill_formatting block in
config.json so the longer strings still fit on screen.

Output
------
text_data_dict.json in Hachimi's nested shape:

    {"47": {"10071": "Warning Shot!"}, "48": {"10071": "..."}}

Outer key is the text_data category, inner key the index. Only entries whose
translation differs from the JP source are written; identical strings would be
pointless dictionary bloat.
"""

import argparse
import json
import sqlite3
import sys
from pathlib import Path

CATEGORY_SKILL_NAME = 47
CATEGORY_SKILL_DESC = 48


def load_json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def by_skill_id(rows):
    return {row["skillId"]: row for row in rows}


def read_category(conn, category):
    query = 'select "index", text from text_data where category = ?'
    return {index: text for index, text in conn.execute(query, (category,))}


def build(mdb_path, data_dir, include_desc=True):
    conn = sqlite3.connect(mdb_path)
    try:
        jp_names = read_category(conn, CATEGORY_SKILL_NAME)
        jp_descs = read_category(conn, CATEGORY_SKILL_DESC)
    finally:
        conn.close()

    data_dir = Path(data_dir)
    translated = by_skill_id(load_json(data_dir / "JP" / "TerumiSimpleSkillDataJP.json"))
    original = by_skill_id(load_json(data_dir / "JP" / "TerumiSimpleSkillDataJPOriginal.json"))
    global_data = by_skill_id(load_json(data_dir / "TerumiSimpleSkillData.json"))

    # Guard against a future data refresh silently breaking the ID alignment that
    # makes this whole bridge safe. index is NOT unique across categories, so a
    # drifted mapping would write skill names onto unrelated game text.
    drifted = [
        skill_id
        for skill_id, row in original.items()
        if skill_id in jp_names and row.get("skillName") != jp_names[skill_id]
    ]
    if drifted:
        print(
            f"error: {len(drifted)} skill(s) no longer match the mdb source string; "
            f"refusing to emit. First few: {drifted[:5]}",
            file=sys.stderr,
        )
        raise SystemExit(1)

    dictionary = {str(CATEGORY_SKILL_NAME): {}, str(CATEGORY_SKILL_DESC): {}}
    names_out = dictionary[str(CATEGORY_SKILL_NAME)]
    descs_out = dictionary[str(CATEGORY_SKILL_DESC)]
    stats = {"names": 0, "no_name": 0, "prose": 0, "mechanical": 0, "no_desc": 0}

    for skill_id, jp_name in jp_names.items():
        row = translated.get(skill_id)
        english = row.get("skillName") if row else None
        if english and english != jp_name:
            names_out[str(skill_id)] = english
            stats["names"] += 1
        else:
            stats["no_name"] += 1

    if include_desc:
        for skill_id, jp_desc in jp_descs.items():
            # Prefer the Global client's official prose; fall back to umaguide's
            # generated mechanical breakdown for skills that never shipped on Global.
            global_row = global_data.get(skill_id)
            prose = global_row.get("skillDesc") if global_row else None
            if prose and prose != jp_desc:
                descs_out[str(skill_id)] = prose
                stats["prose"] += 1
                continue

            jp_row = translated.get(skill_id)
            mechanical = jp_row.get("skillDesc") if jp_row else None
            if mechanical and mechanical != jp_desc:
                descs_out[str(skill_id)] = mechanical
                stats["mechanical"] += 1
            else:
                stats["no_desc"] += 1

    return dictionary, stats


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mdb", required=True, help="path to master_jp.mdb")
    parser.add_argument("--data", required=True, help="umaguide .vitepress/theme/data dir")
    parser.add_argument("--out", required=True, help="output text_data_dict.json")
    parser.add_argument(
        "--merge",
        action="store_true",
        help="keep existing entries in the output file, only adding new keys",
    )
    parser.add_argument(
        "--no-desc",
        action="store_true",
        help="emit skill names only, skipping descriptions",
    )
    args = parser.parse_args()

    dictionary, stats = build(args.mdb, args.data, include_desc=not args.no_desc)

    out_path = Path(args.out)
    if args.merge and out_path.exists():
        # Merge per category, so hand-written entries and other categories in the
        # file survive. A flat update() here would drop whole categories.
        existing = load_json(out_path)
        added = 0
        for category, entries in dictionary.items():
            target = existing.setdefault(category, {})
            for index, text in entries.items():
                if index not in target:
                    target[index] = text
                    added += 1
        dictionary = existing
        print(f"merged {added} new entries, keeping existing ones")

    for category in dictionary:
        dictionary[category] = dict(
            sorted(dictionary[category].items(), key=lambda kv: int(kv[0]))
        )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(dictionary, fh, ensure_ascii=False, indent=2)
        fh.write("\n")

    total = sum(len(v) for v in dictionary.values())
    print(f"skill names      : {stats['names']} (skipped {stats['no_name']})")
    print(f"descs, prose     : {stats['prose']} (official Global text)")
    print(f"descs, mechanical: {stats['mechanical']} (generated fallback)")
    print(f"descs skipped    : {stats['no_desc']}")
    print(f"total entries    : {total} -> {out_path}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Fill category 172 (inheritance factor descriptions) from their Japanese source.

These descriptions are formulaic: a list of stats that go up, and/or a skill
hint. Rather than translate freely, this reproduces the exact phrasing UmaTL
already uses for the 2334 entries it has, so the filled entries are
indistinguishable from the existing ones:

    Gain skill hint: Right Turns O
    Increases Power, gain skill hint: Winter Girl O
    Increases Stamina Cap & Wit Cap, gain skill hint: Shooting Star
    Increases Speed & Speed Cap

Skill names inside brackets are looked up in category 47, which is already
translated, so no name is invented here. An entry whose skill name cannot be
resolved is skipped and reported rather than guessed at.

    python tools/fill_factor_descs.py --mdb <master_jp.mdb> --dict <dict.json>
"""

import argparse
import json
import re
import sqlite3
from pathlib import Path

CATEGORY_SKILL_NAME = 47
CATEGORY_FACTOR_DESC = 172

# Japanese stat token -> UmaTL's English. "Cap" variants are the 上限 forms.
STATS = {
    "スピード": "Speed",
    "スタミナ": "Stamina",
    "パワー": "Power",
    "根性": "Guts",
    "賢さ": "Wit",
    "スピード上限": "Speed Cap",
    "スタミナ上限": "Stamina Cap",
    "パワー上限": "Power Cap",
    "根性上限": "Guts Cap",
    "賢さ上限": "Wit Cap",
}

HINT_ONLY = re.compile(r"^「(.+?)」のスキルヒントを得られる因子です$")
STAT_HINT = re.compile(r"^(.+?)がアップし、\\n「(.+?)」のスキルヒントを得られる因子です$")
STAT_ONLY = re.compile(r"^(.+?)がアップする因子です$")


def read_category(conn, category):
    query = 'select "index", text from text_data where category = ?'
    return {index: text for index, text in conn.execute(query, (category,))}


def render_stats(chunk):
    """'スタミナ上限と賢さ上限' -> 'Stamina Cap & Wit Cap'."""
    parts = []
    for token in chunk.split("と"):
        if token not in STATS:
            return None
        parts.append(STATS[token])
    return " & ".join(parts)


def translate(source, skill_names):
    match = HINT_ONLY.match(source)
    if match:
        name = skill_names.get(match.group(1))
        return f"Gain skill hint: {name}" if name else None

    match = STAT_HINT.match(source)
    if match:
        stats = render_stats(match.group(1))
        name = skill_names.get(match.group(2))
        if stats and name:
            return f"Increases {stats}, gain skill hint: {name}"
        return None

    match = STAT_ONLY.match(source)
    if match:
        stats = render_stats(match.group(1))
        return f"Increases {stats}" if stats else None

    return None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mdb", required=True)
    parser.add_argument("--dict", required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--indent", type=int, default=4)
    args = parser.parse_args()

    conn = sqlite3.connect(args.mdb)
    try:
        jp_skills = read_category(conn, CATEGORY_SKILL_NAME)
        jp_descs = read_category(conn, CATEGORY_FACTOR_DESC)
    finally:
        conn.close()

    target = Path(args.dict)
    data = json.loads(target.read_text(encoding="utf-8"))
    skills_en = data.get(str(CATEGORY_SKILL_NAME), {})
    descs = data.setdefault(str(CATEGORY_FACTOR_DESC), {})

    # Japanese skill name -> English. Names the game already ships in Latin
    # script have no cat 47 entry, so fall back to the source unchanged.
    skill_names = {
        jp_skills[index]: skills_en[str(index)]
        for index in jp_skills
        if str(index) in skills_en
    }
    for name in jp_skills.values():
        skill_names.setdefault(name, name)

    filled = 0
    skipped = []
    for index, source in jp_descs.items():
        if str(index) in descs:
            continue
        english = translate(source, skill_names)
        if english is None:
            skipped.append((index, source))
        else:
            descs[str(index)] = english
            filled += 1

    print(f"filled  : {filled}")
    print(f"skipped : {len(skipped)}")
    for index, source in skipped[:10]:
        print(f"   {index}  {source[:70]}")

    if args.dry_run:
        print("\ndry run, nothing written")
        return

    data[str(CATEGORY_FACTOR_DESC)] = dict(
        sorted(descs.items(), key=lambda kv: int(kv[0]))
    )
    with open(target, "w", encoding="utf-8", newline="") as fh:
        fh.write(json.dumps(data, ensure_ascii=False, indent=args.indent))
    print(f"\nwrote {target}")


if __name__ == "__main__":
    main()

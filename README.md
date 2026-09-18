# umadottranslate

A [Hachimi](https://hachimi.noccu.art) translation repo providing English skill
names and descriptions for Umamusume: Pretty Derby, generated from
[uma.guide](https://uma.guide)'s translation data.

## Installing

In Hachimi's GUI, open **Change Translation Repo** and point it at this
repository. Hachimi reads everything under `localized_data/`.

## What's in it

Only the `text_data` dictionary, covering two categories:

| Category | Contents | Entries |
| --- | --- | --- |
| `47` | Skill names | 2048 / 2177 |
| `48` | Skill descriptions | 2177 / 2177 |

Nothing else is translated. Stories, UI, race commentary and character system
text are all left to the game's Japanese, so this repo composes cleanly with a
fuller patch rather than competing with it.

### Description sources

Descriptions come from two places, preferring the first:

1. **Official Global prose** — the real in-game English for the 718 skills that
   shipped on the Global client.
2. **Generated mechanical breakdowns** — for JP-only skills, uma.guide's
   effect summary, e.g. `<b>Target Speed +0.35 m/s for 4 s</b> when: Remaining
   distance ≤150m AND In leading 50%`. The `<b>` markup renders in game; this is
   the same style [UmaTL's hachimi-sd](https://github.com/UmaTL/hachimi-sd)
   ships, and `skill_formatting` in `config.json` keeps the longer strings on
   screen.

The two styles read differently. That's the tradeoff for full coverage: prose
where the official localization exists, mechanics where it never did.

## Regenerating

`tools/build_skill_dict.py` rebuilds `text_data_dict.json` from a JP `master.mdb`
and a local checkout of the uma.guide data directory.

```bash
python tools/build_skill_dict.py \
  --mdb   /path/to/master_jp.mdb \
  --data  /path/to/umaguide/docs/.vitepress/theme/data \
  --out   localized_data/text_data_dict.json
```

Useful flags:

- `--merge` keeps entries already in the output file and only adds new keys. Use
  this once you start hand-editing translations, or the rebuild will discard them.
- `--no-desc` emits skill names only.

### How the join works

Skill IDs in uma.guide's data are the same integers as `text_data`'s `index`
column, so entries are matched by ID with no name matching involved. Before
emitting anything the script re-checks every JP source string in
`TerumiSimpleSkillDataJPOriginal.json` against category 47 in the mdb and aborts
if any has drifted.

That check is load-bearing. `index` is **not** unique across categories — ID
`10071` is a skill, a Gold Ship chocolate item, a team race label and a character
name, depending on which category you read it under. A silently drifted mapping
would write skill names over unrelated game text, so the build fails loudly
instead.

## Known gaps

Descriptions are complete. Names are too, in practice:

- **129 skill names are absent from the dict on purpose.** They are unique
  skills the Japanese game already ships in Latin script — `Nemesis`,
  `Shadow Break`, `KEEP IT REAL.`, `α-star*`, `Vive la GOLD`. The build treats a
  name as needing no entry when the English matches the source, so these are
  skipped rather than written as no-op entries. They already display correctly
  in game.
- Skill data is only as current as the `master_jp.mdb` you build against.

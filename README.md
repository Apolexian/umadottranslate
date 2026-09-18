# umadottranslate

English skill names and descriptions for Umamusume: Pretty Derby, as a
[Hachimi](https://hachimi.noccu.art) translation repo.

## Install

In Hachimi's GUI, open **Change Translation Repo** and enter:

```
https://github.com/Apolexian/umadottranslate
```

Hachimi reads everything under `localized_data/`. Restart the game, or use
**Reload localized data**. Skill text loads at startup.

## What it changes

Skill names and skill descriptions. Nothing else, so it stacks with a fuller
patch like [UmaTL](https://github.com/UmaTL/hachimi-tl-en) rather than fighting
it: every other dictionary is `null` in `config.json`.

Descriptions come in two styles depending on the skill:

- Skills that shipped on the Global client use the official English text.
- JP-only skills use a generated effect breakdown, e.g.
  `<b>Target Speed +0.35 m/s for 4 s</b> when: Remaining distance ≤150m AND In leading 50%`

A handful of unique skills are left alone because the Japanese game already
names them in English: `Nemesis`, `KEEP IT REAL.`, `α-star*`.

## Rebuilding

Only needed if you want to regenerate against newer game data. Requires a JP
`master.mdb` and a local checkout of [uma.guide](https://github.com/SayaDuck/umaguide).

```bash
python tools/build_skill_dict.py \
  --mdb   /path/to/master_jp.mdb \
  --data  /path/to/umaguide/docs/.vitepress/theme/data \
  --out   localized_data/text_data_dict.json
```

| Flag | Effect |
| --- | --- |
| `--merge` | Keep entries already in the output file, adding only new ones |
| `--no-desc` | Skill names only |

Use `--merge` if you have hand-edited any translations, or the rebuild will
discard them.

## Editing translations by hand

`localized_data/text_data_dict.json` is keyed by text_data category, then by
skill ID:

```json
{
  "47": { "10071": "Warning Shot!" },
  "48": { "10071": "Slightly increase velocity with a long spurt starting halfway through the race." }
}
```

Category `47` is names, `48` is descriptions. Edit the string, reload, done.

## Credits

Translation data from [uma.guide](https://uma.guide). Built for
[Hachimi](https://hachimi.noccu.art).

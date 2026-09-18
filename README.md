# umadottranslate

English skill names and descriptions for Umamusume: Pretty Derby, as a
[Hachimi](https://hachimi.noccu.art) translation repo.

## Install

Hachimi takes the URL of an index file, not a repository URL, and
**Change Translation Repo** only lists repos it already knows about. To add this
one, close the game and edit `.tl_repos` in your Hachimi folder (next to
`config.json`, typically `<game dir>/hachimi/`):

```json
{
  "repos": [
    {
      "id": 1,
      "index": "https://raw.githubusercontent.com/UmaTL/hachimi-tl-en/release/index.json"
    },
    {
      "id": 2,
      "index": "https://raw.githubusercontent.com/Apolexian/umadottranslate/master/index.json"
    }
  ]
}
```

Keep the existing entries and give the new one an unused `id`. Start the game,
open **Change Translation Repo**, and it appears under **Available**. Select it,
then use **Check for translation updates** to download.

Only one repo is active at a time, so switching to this one replaces a fuller
patch rather than adding to it.

## What it changes

Skill names and skill descriptions. Every other dictionary is `null` in
`config.json`, so the rest of the game stays Japanese: stories, menus, race
commentary, character dialogue.

Hachimi runs one repo at a time, so this is not an add-on to a fuller patch like
[UmaTL](https://github.com/UmaTL/hachimi-tl-en). Selecting it replaces whatever
was active.

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

Then regenerate the index and commit both:

```bash
python tools/gen_index.py
```

`index.json` carries a BLAKE3 hash and size for every file under
`localized_data/`. Clients verify downloads against it, so a change committed
without a fresh index will fail verification on their end. It needs `blake3`
(`pip install blake3`).

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

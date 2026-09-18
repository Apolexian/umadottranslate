#!/usr/bin/env python3
"""Swap "Horsegirl" for "Uma" across a localized_data tree.

Whole-word, but unlike reterm.py's other swaps, casing is NOT preserved from
the source: every instance becomes "Uma"/"Umas", capitalized, since it acts as
a proper/brand term here (parallel to "Umamusume") rather than a common noun.
Checked: no ALL-CAPS "HORSEGIRL" forms exist in the tree, so this covers every
case that's actually present.

The one extra rule this term needs: "a horsegirl" -> "an Uma", since "Uma"
starts with a vowel sound and "Horsegirl" doesn't. Word-boundary replace alone
would produce "a Uma" 913 times, so the indefinite article immediately before
the word is normalized in the same pass, matching the case of the original
article (a/A).

    python tools/reterm_uma.py --dir <localized_data> [--dry-run]
"""

import argparse
import json
import re
from pathlib import Path

TERM_SOURCE = "Horsegirl"
TERM_TARGET = "Uma"  # always capitalized in the output; see module docstring

ARTICLE = "an" if TERM_TARGET[0].lower() in "aeiou" else "a"

WORD_PATTERN = re.compile(rf"\b{TERM_SOURCE}(s?)\b", re.IGNORECASE)
ARTICLE_PATTERN = re.compile(rf"\b(a|A)(\s+){TERM_SOURCE}(s?)\b", re.IGNORECASE)
# The one compound form present in the tree: horsegirlkind (no word
# boundary before "kind", so WORD_PATTERN alone would miss it).
COMPOUND_PATTERN = re.compile(rf"{TERM_SOURCE}kind", re.IGNORECASE)


def rewrite(value):
    def sub_with_article(match):
        article, space, plural = match.group(1), match.group(2), match.group(3)
        new_article = ARTICLE.capitalize() if article[0] == "A" else ARTICLE
        return f"{new_article}{space}{TERM_TARGET}{plural}"

    def sub_plain(match):
        return TERM_TARGET + match.group(1)

    # Compound form first (horsegirlkind -> Umakind): it has no word
    # boundary before "kind", so WORD_PATTERN would otherwise skip it
    # entirely, and running it after would double up on "Horsegirl".
    value = COMPOUND_PATTERN.sub(TERM_TARGET + "kind", value)
    # Article-aware pass next, so those occurrences are not double-handled
    # by the plain word pass afterward.
    value = ARTICLE_PATTERN.sub(sub_with_article, value)
    return WORD_PATTERN.sub(sub_plain, value)


def walk(node, counter, samples):
    if isinstance(node, dict):
        return {k: walk(v, counter, samples) for k, v in node.items()}
    if isinstance(node, list):
        return [walk(v, counter, samples) for v in node]
    if isinstance(node, str):
        new = rewrite(node)
        if new != node:
            counter[0] += 1
            if len(samples) < 12:
                samples.append((node, new))
        return new
    return node


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dir", required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--indent", type=int, default=4)
    args = parser.parse_args()

    root = Path(args.dir)
    total = 0

    for path in sorted(root.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        counter = [0]
        samples = []
        updated = walk(data, counter, samples)
        if not counter[0]:
            continue

        total += counter[0]
        print(f"{path.name}: {counter[0]} strings")
        for before, after in samples[:4]:
            print(f"    - {before[:80]}")
            print(f"    + {after[:80]}")

        if not args.dry_run:
            with open(path, "w", encoding="utf-8", newline="") as fh:
                fh.write(json.dumps(updated, ensure_ascii=False, indent=args.indent))

    print(f"\ntotal: {total} strings")
    if args.dry_run:
        print("dry run, nothing written")


if __name__ == "__main__":
    main()

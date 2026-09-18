#!/usr/bin/env python3
"""Swap UmaTL terminology for uma.guide's across a localized_data tree.

UmaTL and uma.guide disagree on some game terms. Where a term appears in the
site's guides, keeping the game text consistent with it matters more than
matching upstream, so this rewrites the whole tree to uma.guide's wording.

Replacements are whole-word and case-preserving: "Betweener" -> "Late Surger",
"betweeners" -> "late surgers". Word boundaries matter, otherwise a term that
happens to be a substring of another word gets mangled.

    python tools/reterm.py --dir <localized_data> [--dry-run]

Terms live in TERMS below. Check a new one with --dry-run first, and read the
sample lines it prints: a term with an unrelated second meaning should not be
swapped blindly.
"""

import argparse
import json
import re
from pathlib import Path

# uma.guide's term -> the UmaTL wording it replaces. Singular forms only;
# plurals are handled by the pattern.
TERMS = {
    "Betweener": "Late Surger",
}


def match_case(replacement, original):
    """Mirror the original's casing so mid-sentence uses stay lowercase."""
    if original.isupper():
        return replacement.upper()
    if original[:1].isupper():
        return replacement
    return replacement.lower()


def build_patterns(terms):
    patterns = []
    for source, target in terms.items():
        # Optional trailing s, so plurals come along without a second entry.
        pattern = re.compile(rf"\b{re.escape(source)}(s?)\b", re.IGNORECASE)

        def make(target=target):
            def sub(match):
                replacement = match_case(target, match.group(0))
                return replacement + match.group(1)

            return sub

        patterns.append((pattern, make()))
    return patterns


def rewrite(value, patterns):
    for pattern, sub in patterns:
        value = pattern.sub(sub, value)
    return value


def walk(node, patterns, counter, samples):
    if isinstance(node, dict):
        return {k: walk(v, patterns, counter, samples) for k, v in node.items()}
    if isinstance(node, list):
        return [walk(v, patterns, counter, samples) for v in node]
    if isinstance(node, str):
        new = rewrite(node, patterns)
        if new != node:
            counter[0] += 1
            if len(samples) < 12:
                samples.append((node, new))
        return new
    return node


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dir", required=True, help="localized_data directory")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--indent", type=int, default=4)
    args = parser.parse_args()

    patterns = build_patterns(TERMS)
    root = Path(args.dir)
    total = 0

    for path in sorted(root.glob("*.json")):
        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw)

        counter = [0]
        samples = []
        updated = walk(data, patterns, counter, samples)
        if not counter[0]:
            continue

        total += counter[0]
        print(f"{path.name}: {counter[0]} strings")
        for before, after in samples[:4]:
            print(f"    - {before[:80]}")
            print(f"    + {after[:80]}")

        if not args.dry_run:
            # Preserve the tree's formatting: no trailing newline, LF.
            with open(path, "w", encoding="utf-8", newline="") as fh:
                fh.write(json.dumps(updated, ensure_ascii=False, indent=args.indent))

    print(f"\ntotal: {total} strings")
    if args.dry_run:
        print("dry run, nothing written")


if __name__ == "__main__":
    main()

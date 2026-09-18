#!/usr/bin/env python3
"""Generate index.json, the file Hachimi actually fetches to install this repo.

Hachimi does not take a repository URL. It takes the URL of an index describing
every file under localized_data, and uses it to decide what to download and to
verify what it got. Hashes are BLAKE3, matching what Hachimi checks against.

Run from the repo root after changing anything in localized_data/:

    python tools/gen_index.py

Then commit the regenerated index.json alongside the change, or clients will
verify their downloads against stale hashes and refuse the files.
"""

import json
from pathlib import Path

from blake3 import blake3

REPO = Path(__file__).resolve().parent.parent
LOCALIZED_DATA = REPO / "localized_data"
OUT = REPO / "index.json"

OWNER = "Apolexian"
NAME = "umadottranslate"
BRANCH = "master"

BASE = {
    "base_url": f"https://raw.githubusercontent.com/{OWNER}/{NAME}/{BRANCH}/localized_data",
    "zip_url": f"https://codeload.github.com/{OWNER}/{NAME}/zip/refs/heads/{BRANCH}",
    "zip_dir": f"{NAME}-{BRANCH}/localized_data",
}


def main():
    if not LOCALIZED_DATA.is_dir():
        raise SystemExit(f"error: {LOCALIZED_DATA} not found")

    index = dict(BASE)
    index["files"] = []

    hasher = blake3(max_threads=blake3.AUTO)
    for path in sorted(LOCALIZED_DATA.rglob("*")):
        if not path.is_file() or path.name == ".gitignore":
            continue

        hasher.update_mmap(path)
        digest = hasher.digest()
        hasher.reset()

        index["files"].append(
            {
                "path": path.relative_to(LOCALIZED_DATA).as_posix(),
                "hash": digest.hex(),
                "size": path.stat().st_size,
            }
        )

    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(index, fh, ensure_ascii=False, indent=2)
        fh.write("\n")

    total = sum(f["size"] for f in index["files"])
    print(f"indexed {len(index['files'])} file(s), {total:,} bytes -> {OUT.name}")
    for f in index["files"]:
        print(f"  {f['path']}")


if __name__ == "__main__":
    main()

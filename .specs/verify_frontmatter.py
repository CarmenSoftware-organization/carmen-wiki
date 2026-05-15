#!/usr/bin/env python3
"""Sanity-check Wiki.js frontmatter for carmen-wiki pages."""
import re
import sys
from pathlib import Path

REQUIRED_KEYS = ["title", "description", "published", "date", "tags", "editor", "dateCreated"]

def main(path_arg: str) -> int:
    p = Path(path_arg)
    text = p.read_text()
    m = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not m:
        print(f"FAIL: {p} — no frontmatter delimiters")
        return 1
    block = m.group(1)
    missing = [k for k in REQUIRED_KEYS if not re.search(rf"^{k}\s*:", block, re.MULTILINE)]
    if missing:
        print(f"FAIL: {p} — missing keys: {missing}")
        return 1
    title_match = re.search(r"^title\s*:\s*(.+?)\s*$", block, re.MULTILINE)
    title = title_match.group(1) if title_match else "?"
    if not re.search(r"^published\s*:\s*true\s*$", block, re.MULTILINE):
        print(f"FAIL: {p} — published must be true")
        return 1
    if not re.search(r"^editor\s*:\s*markdown\s*$", block, re.MULTILINE):
        print(f"FAIL: {p} — editor must be markdown")
        return 1
    print(f"OK: {p} — title={title!r}")
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))

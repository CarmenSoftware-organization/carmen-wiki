"""Scan en/ and th/ markdown for any remaining un-migrated paths.

Exits nonzero if any stale path is found, so it can guard the migration
in CI or as a pre-commit step.

Bug-fix note: when a module slug equals the book name (e.g. module
"inventory" inside book "inventory"), a naive alternation pattern
  /en/(?:inventory|...)/...
would fire on the already-migrated path /en/inventory/costing/page —
because "inventory" matches as the module and "costing/page" as the
rest. To avoid this, modules that share their name with the book get a
separate pattern that uses a negative lookahead excluding any sub-path
that starts with a known module slug (which signals a migrated path).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path


def build_stale_patterns(*, modules: list[str], book: str) -> list[re.Pattern[str]]:
    """Patterns that match an old (pre-migration) root-relative path.

    A "stale" path is one that sits directly under /en/<module>/,
    /th/<module>/, or /assets/screenshots/<module>/ for any of the given
    modules, without yet being remapped under /<book>/.

    Modules whose slug equals the book name need special treatment: a
    path like /en/inventory/costing/page is the *migrated* form (the old
    /en/costing/page moved there). A negative lookahead on the known
    module slugs prevents those from being flagged as stale.
    """
    all_alt = "|".join(re.escape(m) for m in modules)

    # Split: modules whose name collides with the book name vs. the rest.
    non_book = [m for m in modules if m != book]
    book_conflicts = [m for m in modules if m == book]

    patterns: list[re.Pattern[str]] = []

    if non_book:
        alt = "|".join(re.escape(m) for m in non_book)
        patterns.append(re.compile(rf"/en/(?:{alt})/[^\s)#]*"))
        patterns.append(re.compile(rf"/th/(?:{alt})/[^\s)#]*"))
        patterns.append(re.compile(rf"/assets/screenshots/(?:{alt})/[^\s)#]*"))

    for mod in book_conflicts:
        # Under /en/<mod>/, the post-migration legitimate targets are:
        #   - /en/<mod>/home              (the book index page)
        #   - /en/<mod>/<module-slug>/... (a migrated module page)
        # Anything else under /en/<mod>/ is a stale leftover. The
        # negative lookahead excludes both legitimate forms.
        skip = rf"(?:home(?![\w-])|(?:{all_alt})/)"
        patterns.append(re.compile(rf"/en/{re.escape(mod)}/(?!{skip})[^\s)#]*"))
        patterns.append(re.compile(rf"/th/{re.escape(mod)}/(?!{skip})[^\s)#]*"))
        patterns.append(
            re.compile(rf"/assets/screenshots/{re.escape(mod)}/(?!{skip})[^\s)#]*")
        )

    return patterns


def find_stale_paths(text: str, patterns: list[re.Pattern[str]]) -> list[str]:
    """Return every stale path matched in `text`."""
    found: list[str] = []
    for pat in patterns:
        found.extend(pat.findall(text))
    return found


def main() -> int:
    inventory_modules = [
        "access-control", "costing", "dashboard", "good-receive-note",
        "inventory", "inventory-adjustment", "master-data", "physical-count",
        "product", "purchase-order", "purchase-request", "recipe",
        "reporting-audit", "spot-check", "store-requisition", "system-config",
        "templates", "vendor-pricelist",
    ]
    patterns = build_stale_patterns(modules=inventory_modules, book="inventory")
    repo_root = Path(__file__).resolve().parent.parent.parent

    failures = 0
    for md in list(repo_root.glob("en/**/*.md")) + list(repo_root.glob("th/**/*.md")):
        text = md.read_text(encoding="utf-8")
        stale = find_stale_paths(text, patterns)
        if stale:
            failures += 1
            rel = md.relative_to(repo_root)
            print(f"STALE in {rel}:")
            for s in stale:
                print(f"  {s}")
    if failures:
        print(f"\nFAIL: {failures} file(s) contain stale paths.", file=sys.stderr)
        return 1
    print("OK: no stale paths found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

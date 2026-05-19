# Multi-Book Restructure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert `carmen-wiki` from a single-product (Inventory) wiki into a multi-book wiki with two top-level books (Inventory + Platform) under a single Wiki.js instance.

**Architecture:** Big-bang migration on `feat/multi-book-restructure`. New tooling under `scripts/migrate_books/` handles folder moves, link rewrites, skeleton generation, and verification. Existing `scripts/sync_nav.py` is extended with a new "build from config" mode that produces a two-book nav tree for both EN and TH locales. Each commit is reviewable independently; the whole branch lands as one PR.

**Tech Stack:** Python 3.11+, pytest 8, frontmatter, gql, pyyaml; `git mv` to preserve blame; Wiki.js (existing).

**Design reference:** `docs/superpowers/specs/2026-05-19-multi-book-restructure-design.md`

**Inventory modules (18) being moved:** access-control, costing, dashboard, good-receive-note, inventory, inventory-adjustment, master-data, physical-count, product, purchase-order, purchase-request, recipe, reporting-audit, spot-check, store-requisition, system-config, templates, vendor-pricelist

**Platform book modules (6):** clusters, business-units, users, report-templates, profile, auth-roles

---

## Pre-flight

### Task 1: Create feature branch

**Files:** none

- [ ] **Step 1: Confirm clean working tree**

Run: `git status`
Expected: `nothing to commit, working tree clean`

- [ ] **Step 2: Create and switch to feature branch**

Run: `git checkout -b feat/multi-book-restructure`
Expected: `Switched to a new branch 'feat/multi-book-restructure'`

- [ ] **Step 3: Confirm Python environment**

Run: `python3 -c "import sys; print(sys.version_info[:2])"`
Expected: `(3, 11)` or higher

Run: `test -d .venv && echo OK || echo MISSING`
Expected: `OK` (if missing, run `python3 -m venv .venv && source .venv/bin/activate && pip install -r scripts/requirements.txt`)

---

## Phase A — Migration tooling (scripts/migrate_books/)

### Task 2: Scaffold migrate_books package

**Files:**
- Create: `scripts/migrate_books/__init__.py`
- Create: `scripts/migrate_books/README.md`

- [ ] **Step 1: Create package init**

Create `scripts/migrate_books/__init__.py` with empty content (one trailing newline).

- [ ] **Step 2: Create README**

Create `scripts/migrate_books/README.md`:

```markdown
# scripts/migrate_books/

One-shot tooling for the multi-book restructure
(`docs/superpowers/specs/2026-05-19-multi-book-restructure-design.md`).

Run order:
1. `folder_moves.py` — print `git mv` commands; pipe to `bash` after review
2. `rewrite_links.py` — rewrite root-relative paths in markdown
3. `scaffold_platform.py` — generate Platform book skeleton pages
4. `verify.py` — assert no old paths remain

After the PR merges, this package can be deleted; it is not part of
day-to-day wiki workflows.
```

- [ ] **Step 3: Commit**

```bash
git add scripts/migrate_books/__init__.py scripts/migrate_books/README.md
git commit -m "scripts(migrate_books): scaffold migration tooling"
```

---

### Task 3: Folder-move command generator + tests

**Files:**
- Create: `scripts/migrate_books/folder_moves.py`
- Create: `scripts/migrate_books/test_folder_moves.py`

- [ ] **Step 1: Write the failing test**

Create `scripts/migrate_books/test_folder_moves.py`:

```python
"""Tests for folder_moves.py."""
from scripts.migrate_books.folder_moves import generate_content_moves, generate_asset_moves


INVENTORY_MODULES = [
    "access-control", "costing", "dashboard", "good-receive-note",
    "inventory", "inventory-adjustment", "master-data", "physical-count",
    "product", "purchase-order", "purchase-request", "recipe",
    "reporting-audit", "spot-check", "store-requisition", "system-config",
    "templates", "vendor-pricelist",
]


def test_content_moves_includes_both_locales():
    moves = generate_content_moves(INVENTORY_MODULES, book="inventory")
    assert ("en/access-control", "en/inventory/access-control") in moves
    assert ("th/access-control", "th/inventory/access-control") in moves


def test_content_moves_count_equals_modules_times_locales():
    moves = generate_content_moves(INVENTORY_MODULES, book="inventory")
    assert len(moves) == len(INVENTORY_MODULES) * 2  # 18 × 2 = 36


def test_content_moves_does_not_move_inventory_module_into_itself():
    # "inventory" module name collides with new book name; ensure src/dst differ
    moves = generate_content_moves(INVENTORY_MODULES, book="inventory")
    pair = ("en/inventory", "en/inventory/inventory")
    assert pair in moves
    assert all(src != dst for src, dst in moves)


def test_asset_moves_includes_all_modules():
    moves = generate_asset_moves(INVENTORY_MODULES, book="inventory")
    assert ("assets/screenshots/costing", "assets/screenshots/inventory/costing") in moves
    assert len(moves) == len(INVENTORY_MODULES)


def test_format_as_git_mv_commands():
    from scripts.migrate_books.folder_moves import format_git_mv
    moves = [("en/foo", "en/inventory/foo"), ("th/foo", "th/inventory/foo")]
    output = format_git_mv(moves)
    assert "git mv en/foo en/inventory/foo" in output
    assert "git mv th/foo th/inventory/foo" in output
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/samutpra/GitHub/carmensoftware-organize/carmen-wiki && python3 -m pytest scripts/migrate_books/test_folder_moves.py -v`
Expected: FAIL with `ModuleNotFoundError: scripts.migrate_books.folder_moves`

- [ ] **Step 3: Write the implementation**

Create `scripts/migrate_books/folder_moves.py`:

```python
"""Generate `git mv` plans for moving content and assets under book folders.

Pure functions; this module performs no filesystem changes. Callers pipe
`format_git_mv()` output to `bash` after review.
"""
from __future__ import annotations


def generate_content_moves(
    modules: list[str],
    *,
    book: str,
    locales: tuple[str, ...] = ("en", "th"),
) -> list[tuple[str, str]]:
    """Return list of (src, dst) pairs for content folder moves.

    For each module M and locale L: <L>/<M>  ->  <L>/<book>/<M>
    """
    moves: list[tuple[str, str]] = []
    for locale in locales:
        for module in modules:
            src = f"{locale}/{module}"
            dst = f"{locale}/{book}/{module}"
            moves.append((src, dst))
    return moves


def generate_asset_moves(
    modules: list[str],
    *,
    book: str,
    assets_root: str = "assets/screenshots",
) -> list[tuple[str, str]]:
    """Return list of (src, dst) pairs for asset folder moves."""
    return [
        (f"{assets_root}/{m}", f"{assets_root}/{book}/{m}")
        for m in modules
    ]


def format_git_mv(moves: list[tuple[str, str]]) -> str:
    """Format moves as a bash-compatible series of `git mv` commands."""
    return "\n".join(f"git mv {src} {dst}" for src, dst in moves) + "\n"


def main() -> None:
    """Print the full folder-move plan to stdout for review."""
    inventory_modules = [
        "access-control", "costing", "dashboard", "good-receive-note",
        "inventory", "inventory-adjustment", "master-data", "physical-count",
        "product", "purchase-order", "purchase-request", "recipe",
        "reporting-audit", "spot-check", "store-requisition", "system-config",
        "templates", "vendor-pricelist",
    ]
    content_moves = generate_content_moves(inventory_modules, book="inventory")
    asset_moves = generate_asset_moves(inventory_modules, book="inventory")
    print("# Content moves")
    print(format_git_mv(content_moves), end="")
    print()
    print("# Asset moves")
    print(format_git_mv(asset_moves), end="")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest scripts/migrate_books/test_folder_moves.py -v`
Expected: 5 passed

- [ ] **Step 5: Manually inspect dry-run output**

Run: `python3 -m scripts.migrate_books.folder_moves`
Expected: 36 content moves + 18 asset moves printed; visually confirm structure

- [ ] **Step 6: Commit**

```bash
git add scripts/migrate_books/folder_moves.py scripts/migrate_books/test_folder_moves.py
git commit -m "scripts(migrate_books): folder-move command generator"
```

---

### Task 4: Markdown link/image rewriter + tests

**Files:**
- Create: `scripts/migrate_books/rewrite_links.py`
- Create: `scripts/migrate_books/test_rewrite_links.py`

**Approach:** Line-based scanner that tracks fenced code blocks (``` and ~~~). In prose lines, regex-rewrite root-relative path prefixes inside `[text](path)` and `![alt](path)` syntax. Anchors and external URLs are preserved.

- [ ] **Step 1: Write the failing test**

Create `scripts/migrate_books/test_rewrite_links.py`:

```python
"""Tests for rewrite_links.py."""
from scripts.migrate_books.rewrite_links import (
    rewrite_text,
    build_mapping,
)


MAPPING = build_mapping(
    modules=["costing", "good-receive-note"],
    book="inventory",
)


def test_rewrites_root_relative_en_page_link():
    src = "See [Costing](/en/costing/calculation-methods)."
    out = rewrite_text(src, MAPPING)
    assert out == "See [Costing](/en/inventory/costing/calculation-methods)."


def test_rewrites_root_relative_th_page_link():
    src = "ดู [Costing](/th/costing/calculation-methods)"
    out = rewrite_text(src, MAPPING)
    assert out == "ดู [Costing](/th/inventory/costing/calculation-methods)"


def test_rewrites_image_reference():
    src = "![receiver](/assets/screenshots/good-receive-note/receiver.png)"
    out = rewrite_text(src, MAPPING)
    assert out == "![receiver](/assets/screenshots/inventory/good-receive-note/receiver.png)"


def test_preserves_anchor():
    src = "[FIFO](/en/costing/calculation-methods#fifo)"
    out = rewrite_text(src, MAPPING)
    assert out == "[FIFO](/en/inventory/costing/calculation-methods#fifo)"


def test_does_not_touch_external_links():
    src = "[GitHub](https://github.com/foo/bar)"
    assert rewrite_text(src, MAPPING) == src


def test_does_not_touch_anchor_only_links():
    src = "[Section](#section-2)"
    assert rewrite_text(src, MAPPING) == src


def test_does_not_touch_relative_links():
    src = "[Sibling](./other-page.md) and [Parent](../sibling/page.md)"
    assert rewrite_text(src, MAPPING) == src


def test_ignores_paths_inside_fenced_code_block():
    src = (
        "Before [Costing](/en/costing/page).\n"
        "```\n"
        "Example URL: /en/costing/page\n"
        "[Looks like a link](/en/costing/page)\n"
        "```\n"
        "After [Costing](/en/costing/page).\n"
    )
    out = rewrite_text(src, MAPPING)
    # Outside fences: rewritten
    assert "Before [Costing](/en/inventory/costing/page)." in out
    assert "After [Costing](/en/inventory/costing/page)." in out
    # Inside fences: untouched
    assert "Example URL: /en/costing/page\n" in out
    assert "[Looks like a link](/en/costing/page)" in out


def test_ignores_paths_inside_tilde_fenced_block():
    src = (
        "~~~\n"
        "[Inside tilde fence](/en/costing/page)\n"
        "~~~\n"
    )
    assert rewrite_text(src, MAPPING) == src


def test_handles_multiple_links_on_one_line():
    src = "[A](/en/costing/a) and [B](/en/good-receive-note/b)"
    out = rewrite_text(src, MAPPING)
    assert out == (
        "[A](/en/inventory/costing/a) and [B](/en/inventory/good-receive-note/b)"
    )


def test_mapping_includes_all_three_prefixes_per_module():
    mapping = build_mapping(modules=["costing"], book="inventory")
    assert "/en/costing/" in mapping
    assert mapping["/en/costing/"] == "/en/inventory/costing/"
    assert "/th/costing/" in mapping
    assert mapping["/th/costing/"] == "/th/inventory/costing/"
    assert "/assets/screenshots/costing/" in mapping
    assert (
        mapping["/assets/screenshots/costing/"]
        == "/assets/screenshots/inventory/costing/"
    )


def test_does_not_rewrite_already_migrated_path():
    src = "[Already migrated](/en/inventory/costing/page)"
    assert rewrite_text(src, MAPPING) == src
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest scripts/migrate_books/test_rewrite_links.py -v`
Expected: FAIL with `ModuleNotFoundError: scripts.migrate_books.rewrite_links`

- [ ] **Step 3: Write the implementation**

Create `scripts/migrate_books/rewrite_links.py`:

```python
"""Rewrite root-relative markdown paths when content moves under a book folder.

Line-based scanner. Tracks fenced code blocks (``` and ~~~) and skips
their contents. Inside prose lines, rewrites occurrences of mapped path
prefixes that appear inside markdown link syntax `[text](path)` or
`![alt](path)`. External URLs (http(s):), relative paths (`./`, `../`),
and anchor-only fragments (`#x`) are not matched by the prefix patterns
and therefore left alone.
"""
from __future__ import annotations

import re
from pathlib import Path


_LINK_RE = re.compile(r"(!?\[[^\]]*\])\(([^)\s]+)\)")
_FENCE_RE = re.compile(r"^(\s*)(```|~~~)")


def build_mapping(*, modules: list[str], book: str) -> dict[str, str]:
    """Build the prefix→prefix mapping for one book's modules.

    Returns three entries per module (EN, TH, assets) — all trailing-slashed
    so we never partial-match e.g. /en/costing-other/.
    """
    m: dict[str, str] = {}
    for module in modules:
        m[f"/en/{module}/"] = f"/en/{book}/{module}/"
        m[f"/th/{module}/"] = f"/th/{book}/{module}/"
        m[f"/assets/screenshots/{module}/"] = (
            f"/assets/screenshots/{book}/{module}/"
        )
    return m


def _rewrite_path(path: str, mapping: dict[str, str]) -> str:
    """Apply the longest matching prefix; preserve fragment/query."""
    for src_prefix, dst_prefix in mapping.items():
        if path.startswith(src_prefix):
            return dst_prefix + path[len(src_prefix):]
    return path


def rewrite_text(text: str, mapping: dict[str, str]) -> str:
    """Rewrite all mapped link/image paths in `text`, skipping code fences."""
    out_lines: list[str] = []
    in_fence = False
    fence_marker: str | None = None
    for line in text.splitlines(keepends=True):
        fence_match = _FENCE_RE.match(line)
        if fence_match:
            marker = fence_match.group(2)
            if not in_fence:
                in_fence = True
                fence_marker = marker
            elif marker == fence_marker:
                in_fence = False
                fence_marker = None
            out_lines.append(line)
            continue
        if in_fence:
            out_lines.append(line)
            continue

        def _sub(match: re.Match[str]) -> str:
            label = match.group(1)
            path = match.group(2)
            return f"{label}({_rewrite_path(path, mapping)})"

        out_lines.append(_LINK_RE.sub(_sub, line))
    return "".join(out_lines)


def rewrite_file(path: Path, mapping: dict[str, str]) -> bool:
    """Rewrite a single markdown file in place. Returns True if changed."""
    original = path.read_text(encoding="utf-8")
    updated = rewrite_text(original, mapping)
    if updated == original:
        return False
    path.write_text(updated, encoding="utf-8")
    return True


def main() -> None:
    """Walk en/ and th/ markdown files and apply the inventory mapping."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Rewrite root-relative paths after multi-book restructure.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report files that would change without writing.",
    )
    args = parser.parse_args()

    inventory_modules = [
        "access-control", "costing", "dashboard", "good-receive-note",
        "inventory", "inventory-adjustment", "master-data", "physical-count",
        "product", "purchase-order", "purchase-request", "recipe",
        "reporting-audit", "spot-check", "store-requisition", "system-config",
        "templates", "vendor-pricelist",
    ]
    mapping = build_mapping(modules=inventory_modules, book="inventory")

    repo_root = Path(__file__).resolve().parent.parent.parent
    changed = 0
    scanned = 0
    for md in list(repo_root.glob("en/**/*.md")) + list(repo_root.glob("th/**/*.md")):
        scanned += 1
        if args.dry_run:
            original = md.read_text(encoding="utf-8")
            updated = rewrite_text(original, mapping)
            if updated != original:
                changed += 1
                print(f"WOULD REWRITE: {md.relative_to(repo_root)}")
        else:
            if rewrite_file(md, mapping):
                changed += 1
                print(f"REWROTE: {md.relative_to(repo_root)}")
    print(f"\n{changed} of {scanned} markdown files {'would be' if args.dry_run else ''} changed.")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest scripts/migrate_books/test_rewrite_links.py -v`
Expected: 11 passed

- [ ] **Step 5: Commit**

```bash
git add scripts/migrate_books/rewrite_links.py scripts/migrate_books/test_rewrite_links.py
git commit -m "scripts(migrate_books): markdown link/image rewriter"
```

---

### Task 5: Verification scanner + tests

**Files:**
- Create: `scripts/migrate_books/verify.py`
- Create: `scripts/migrate_books/test_verify.py`

- [ ] **Step 1: Write the failing test**

Create `scripts/migrate_books/test_verify.py`:

```python
"""Tests for verify.py."""
from scripts.migrate_books.verify import find_stale_paths, build_stale_patterns


INVENTORY_MODULES = ["costing", "good-receive-note"]


def test_stale_patterns_match_unmigrated_path():
    patterns = build_stale_patterns(modules=INVENTORY_MODULES, book="inventory")
    src = "[link](/en/costing/page)"
    assert find_stale_paths(src, patterns) == ["/en/costing/page"]


def test_no_false_positive_on_migrated_path():
    patterns = build_stale_patterns(modules=INVENTORY_MODULES, book="inventory")
    src = "[link](/en/inventory/costing/page)"
    assert find_stale_paths(src, patterns) == []


def test_finds_stale_asset_reference():
    patterns = build_stale_patterns(modules=INVENTORY_MODULES, book="inventory")
    src = "![grn](/assets/screenshots/good-receive-note/x.png)"
    assert find_stale_paths(src, patterns) == [
        "/assets/screenshots/good-receive-note/x.png"
    ]


def test_finds_multiple_in_one_text():
    patterns = build_stale_patterns(modules=INVENTORY_MODULES, book="inventory")
    src = "[a](/en/costing/x) and [b](/th/good-receive-note/y)"
    result = find_stale_paths(src, patterns)
    assert "/en/costing/x" in result
    assert "/th/good-receive-note/y" in result
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest scripts/migrate_books/test_verify.py -v`
Expected: FAIL with `ModuleNotFoundError: scripts.migrate_books.verify`

- [ ] **Step 3: Write the implementation**

Create `scripts/migrate_books/verify.py`:

```python
"""Scan en/ and th/ markdown for any remaining un-migrated paths.

Exits nonzero if any stale path is found, so it can guard the migration
in CI or as a pre-commit step.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path


def build_stale_patterns(*, modules: list[str], book: str) -> list[re.Pattern[str]]:
    """Patterns that match an old (pre-migration) root-relative path.

    A "stale" path is one that starts with `/en/<module>/` or
    `/th/<module>/` or `/assets/screenshots/<module>/` for any of the
    given modules, when those prefixes have not yet been remapped under
    `/<book>/`.
    """
    alt = "|".join(re.escape(m) for m in modules)
    return [
        re.compile(rf"/en/(?:{alt})/[^\s)#]*"),
        re.compile(rf"/th/(?:{alt})/[^\s)#]*"),
        re.compile(rf"/assets/screenshots/(?:{alt})/[^\s)#]*"),
    ]


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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest scripts/migrate_books/test_verify.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add scripts/migrate_books/verify.py scripts/migrate_books/test_verify.py
git commit -m "scripts(migrate_books): stale-path verification scanner"
```

---

## Phase B — Execute content moves

### Task 6: Move inventory content folders (en/ and th/)

**Files:** none new; moves 36 folders.

- [ ] **Step 1: Generate the move plan**

Run: `python3 -m scripts.migrate_books.folder_moves > /tmp/move-plan.sh`
Expected: 54 lines of `git mv` commands (36 content + 18 asset) plus comment lines

- [ ] **Step 2: Visually inspect the plan**

Run: `cat /tmp/move-plan.sh`
Expected: For each module M ∈ {18 modules}, two lines:
- `git mv en/M en/inventory/M`
- `git mv th/M th/inventory/M`
Plus 18 asset lines: `git mv assets/screenshots/M assets/screenshots/inventory/M`

- [ ] **Step 3: Execute content moves only**

Run (extract content moves from plan):

```bash
grep '^git mv en/\|^git mv th/' /tmp/move-plan.sh | bash
```
Expected: no output (git mv is silent on success); 36 folders moved.

- [ ] **Step 4: Verify with git status**

Run: `git status --short | head -40`
Expected: Pairs of `R  en/<module>/... -> en/inventory/<module>/...` (rename detection)

- [ ] **Step 5: Commit content moves**

```bash
git add -A
git commit -m "chore(inventory): move existing modules under en/inventory and th/inventory

Moves all 18 inventory module folders from en/<module>/ to
en/inventory/<module>/ and likewise for th/. Uses git mv to preserve
blame history. Markdown link rewrites land in a follow-up commit."
```

---

### Task 7: Move asset folders

- [ ] **Step 1: Execute asset moves**

Run:

```bash
grep '^git mv assets/' /tmp/move-plan.sh | bash
```
Expected: silent; 18 asset folders moved.

- [ ] **Step 2: Create empty platform asset dir**

Run: `mkdir -p assets/screenshots/platform && touch assets/screenshots/platform/.gitkeep`

- [ ] **Step 3: Verify with git status**

Run: `git status --short`
Expected: 18 renames `R  assets/screenshots/<module>/... -> assets/screenshots/inventory/<module>/...` plus one new `?? assets/screenshots/platform/.gitkeep`

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "chore(assets): move screenshots under inventory/ namespace; reserve platform/"
```

---

### Task 8: Rewrite internal links and image refs

- [ ] **Step 1: Dry-run the rewriter**

Run: `python3 -m scripts.migrate_books.rewrite_links --dry-run`
Expected: list of `WOULD REWRITE:` lines + a final count.

- [ ] **Step 2: Note the count**

Record the "N of M markdown files would be changed" line for the commit message.

- [ ] **Step 3: Apply the rewriter**

Run: `python3 -m scripts.migrate_books.rewrite_links`
Expected: same count of `REWROTE:` lines as the dry-run.

- [ ] **Step 4: Verify no stale paths remain**

Run: `python3 -m scripts.migrate_books.verify`
Expected: `OK: no stale paths found.` and exit 0.

- [ ] **Step 5: Inspect a sample diff**

Run: `git diff en/inventory/costing/home.md | head -40`
Expected: lines like `-[FIFO](/en/costing/fifo)` and `+[FIFO](/en/inventory/costing/fifo)`

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "chore(inventory): rewrite root-relative links and image refs

Adds /inventory/ segment to /en/<module>/... , /th/<module>/... , and
/assets/screenshots/<module>/... references throughout EN and TH
markdown. Code blocks and external URLs are untouched."
```

---

## Phase C — Platform book skeleton

### Task 9: Define Platform skeleton config

**Files:**
- Create: `scripts/migrate_books/platform_pages.yaml`

- [ ] **Step 1: Write the config**

Create `scripts/migrate_books/platform_pages.yaml`:

```yaml
# Platform book skeleton page definitions.
# Generator: scaffold_platform.py
# Each page produces both en/platform/... and th/platform/... versions.

book: platform

pages:
  - path: home.md
    title_en: Carmen Platform
    title_th: Carmen Platform
    description: Overview of the Carmen Platform admin product — entry point for the book.
    tags: [book/platform, home]
    at_a_glance:
      - Audience and scope
      - Modules and how they connect
      - Quick links to each module's home page
    references:
      - "../carmen-platform/README.md"
      - "../carmen-platform/SITEMAP.md"
      - "../carmen-platform/docs/OVERVIEW.md"
    todo:
      - Replace this skeleton with an introduction matching the existing Inventory book home page
      - Add a table of modules with one-line descriptions

  - path: clusters/home.md
    title_en: Clusters
    title_th: Clusters
    description: Cluster management — CRUD, user/BU assignment, license limits.
    tags: [book/platform, clusters]
    at_a_glance:
      - What a cluster is and which entities it groups
      - License limits enforced at cluster level
      - Workflows for adding users and business units
    references:
      - "../carmen-platform/SITEMAP.md (Clusters routes)"
      - "../carmen-platform/src/pages/ClusterManagement.tsx"
      - "../carmen-platform/src/pages/ClusterEdit.tsx"
    todo:
      - Document the data model
      - Document the UI screens
      - Document permissions

  - path: clusters/data-model.md
    title_en: Cluster — Data Model
    title_th: Cluster — Data Model
    description: Cluster entity, relationships to BUs and users, license fields.
    tags: [book/platform, clusters, data-model]
    at_a_glance:
      - Cluster entity fields
      - One-to-many with Business Units
      - License limit fields
    references:
      - "../carmen-platform/docs/OVERVIEW.md (Entities)"
    todo:
      - Document each field
      - Add an entity diagram

  - path: clusters/ui-screens.md
    title_en: Cluster — UI Screens
    title_th: Cluster — UI Screens
    description: ClusterManagement (list) and ClusterEdit (view/edit) screens.
    tags: [book/platform, clusters, ui]
    at_a_glance:
      - ClusterManagement — DataTable, filters, CSV export
      - ClusterEdit — view/edit modes, BU and user assignment panels
    references:
      - "../carmen-platform/src/pages/ClusterManagement.tsx"
      - "../carmen-platform/src/pages/ClusterEdit.tsx"
    todo:
      - Capture screenshots into assets/screenshots/platform/clusters/
      - Document each tab and action

  - path: clusters/permissions.md
    title_en: Cluster — Permissions
    title_th: Cluster — Permissions
    description: Role gates for cluster operations.
    tags: [book/platform, clusters, permissions]
    at_a_glance:
      - "platform_admin: full"
      - "support_manager: full"
      - "support_staff: full"
      - "other roles: AccessDenied"
    references:
      - "../carmen-platform/SITEMAP.md (Access column)"
    todo:
      - Cross-link to auth-roles/home.md for role definitions

  - path: business-units/home.md
    title_en: Business Units
    title_th: Business Units
    description: Hotel/company entity with multi-section form (info, formats, timezone, DB connection, config array).
    tags: [book/platform, business-units]
    at_a_glance:
      - What a BU represents
      - Form sections and their purpose
      - Relationship to clusters
    references:
      - "../carmen-platform/src/pages/BusinessUnitManagement.tsx"
      - "../carmen-platform/src/pages/BusinessUnitEdit.tsx"
    todo:
      - Document each form section
      - Note which fields are editable by which roles

  - path: business-units/data-model.md
    title_en: Business Unit — Data Model
    title_th: Business Unit — Data Model
    description: BU entity, config array semantics, DB connection storage.
    tags: [book/platform, business-units, data-model]
    at_a_glance:
      - Identity fields (hotel name, code)
      - Formatting fields (date, currency, decimal)
      - Timezone
      - DB connection block
      - Config array (key/value pairs)
    references:
      - "../carmen-platform/docs/OVERVIEW.md"
    todo:
      - Document the config array key namespaces

  - path: business-units/ui-screens.md
    title_en: Business Unit — UI Screens
    title_th: Business Unit — UI Screens
    description: BusinessUnitManagement (list) and BusinessUnitEdit (form sections).
    tags: [book/platform, business-units, ui]
    at_a_glance:
      - List page conventions
      - Collapsible form sections in the Edit page
    references:
      - "../carmen-platform/src/pages/BusinessUnitEdit.tsx"
    todo:
      - Screenshot each form section

  - path: users/home.md
    title_en: Users
    title_th: Users
    description: User accounts, role assignment, BU assignment, lifecycle.
    tags: [book/platform, users]
    at_a_glance:
      - User identity vs role vs BU assignment
      - Role + status filters on the list page
      - Lifecycle operations
    references:
      - "../carmen-platform/src/pages/UserManagement.tsx"
      - "../carmen-platform/src/pages/UserEdit.tsx"
    todo:
      - Document role assignment rules

  - path: users/data-model.md
    title_en: User — Data Model
    title_th: User — Data Model
    description: User entity, role, status, per-cluster BU assignments.
    tags: [book/platform, users, data-model]
    at_a_glance:
      - Identity fields
      - Role (single, from a known list)
      - Status (active, disabled, deleted)
      - Per-cluster BU assignments
    references:
      - "../carmen-platform/docs/OVERVIEW.md"
    todo:
      - Document the BU-assignment shape

  - path: users/ui-screens.md
    title_en: User — UI Screens
    title_th: User — UI Screens
    description: UserManagement (list) and UserEdit (BU assignment matrix).
    tags: [book/platform, users, ui]
    at_a_glance:
      - List page filters
      - Edit page BU assignment matrix
    references:
      - "../carmen-platform/src/pages/UserEdit.tsx"
    todo:
      - Screenshot BU assignment workflow

  - path: users/lifecycle.md
    title_en: User — Lifecycle
    title_th: User — Lifecycle
    description: Create, disable, hard/soft delete, password reset.
    tags: [book/platform, users, lifecycle]
    at_a_glance:
      - Create flow
      - Disable vs delete (soft vs hard)
      - Password reset (admin-initiated)
    references:
      - "../carmen-platform/src/pages/UserEdit.tsx"
    todo:
      - Document the password reset email flow if any

  - path: report-templates/home.md
    title_en: Report Templates
    title_th: Report Templates
    description: XML-based report definitions; tabbed editor with live validation and preview.
    tags: [book/platform, report-templates]
    at_a_glance:
      - What a report template is
      - Dialog XML vs Content XML
      - Allow/deny BU lists
    references:
      - "../carmen-platform/src/pages/ReportTemplateManagement.tsx"
      - "../carmen-platform/src/pages/ReportTemplateEdit.tsx"
    todo:
      - Document the XML schema

  - path: report-templates/xml-spec.md
    title_en: Report Template — XML Spec
    title_th: Report Template — XML Spec
    description: Dialog and Content XML structures; Label/Date/Lookup pairs.
    tags: [book/platform, report-templates, xml]
    at_a_glance:
      - Dialog root element and child structure
      - Content root element and child structure
      - "<Label> + <Date> / <Lookup> pairing"
    references:
      - "../carmen-platform/src/pages/ReportTemplateEdit.tsx"
    todo:
      - Add a fully-valid example template
      - List validation error categories

  - path: report-templates/ui-screens.md
    title_en: Report Template — UI Screens
    title_th: Report Template — UI Screens
    description: CodeMirror XML editors, preview tab, chip inputs, sticky action bar.
    tags: [book/platform, report-templates, ui]
    at_a_glance:
      - Two CodeMirror editors (Dialog, Content) with syntax highlighting + folding + search
      - Live validation with line/col markers
      - Dialog Preview tab rendering disabled form
      - BU allow/deny chip inputs
      - Sticky bottom action bar with unsaved-changes indicator
    references:
      - "../carmen-platform/src/pages/ReportTemplateEdit.tsx"
    todo:
      - Screenshot each tab

  - path: profile/home.md
    title_en: Profile
    title_th: Profile
    description: View/edit own profile; change password.
    tags: [book/platform, profile]
    at_a_glance:
      - View/edit fields
      - Change password workflow
    references:
      - "../carmen-platform/src/pages/Profile.tsx"
    todo:
      - Document avatar menu entry point (not a sidebar item)

  - path: auth-roles/home.md
    title_en: Authentication and Roles
    title_th: Authentication and Roles
    description: JWT auth, role gates, role catalog.
    tags: [book/platform, auth, cross-cutting]
    at_a_glance:
      - JWT lifecycle (login, refresh, expiry)
      - Role catalog and gates
      - "Roles: platform_admin, super_admin, support_manager, support_staff, security_officer"
    references:
      - "../carmen-platform/README.md (Auth section)"
      - "../carmen-platform/SITEMAP.md (Access column)"
      - "../carmen-platform/CLAUDE.md"
    todo:
      - Build the role × route gate matrix
      - Cross-link from each module's permissions doc
```

- [ ] **Step 2: Commit**

```bash
git add scripts/migrate_books/platform_pages.yaml
git commit -m "scripts(migrate_books): platform book skeleton config"
```

---

### Task 10: Skeleton page generator + tests

**Files:**
- Create: `scripts/migrate_books/scaffold_platform.py`
- Create: `scripts/migrate_books/test_scaffold_platform.py`

- [ ] **Step 1: Write the failing test**

Create `scripts/migrate_books/test_scaffold_platform.py`:

```python
"""Tests for scaffold_platform.py."""
from pathlib import Path

import frontmatter

from scripts.migrate_books.scaffold_platform import (
    render_page,
    iter_pages,
    PageSpec,
)


SAMPLE_SPEC = PageSpec(
    path="clusters/home.md",
    title_en="Clusters",
    title_th="Clusters",
    description="Cluster mgmt.",
    tags=["book/platform", "clusters"],
    at_a_glance=["What a cluster is"],
    references=["../carmen-platform/SITEMAP.md"],
    todo=["Document permissions"],
)


def test_render_page_has_frontmatter_with_title():
    out = render_page(SAMPLE_SPEC, locale="en", today_iso="2026-05-19T00:00:00.000Z")
    post = frontmatter.loads(out)
    assert post.metadata["title"] == "Clusters"
    assert post.metadata["description"] == "Cluster mgmt."
    assert post.metadata["published"] is True
    assert post.metadata["editor"] == "markdown"
    assert post.metadata["date"] == "2026-05-19T00:00:00.000Z"
    assert post.metadata["dateCreated"] == "2026-05-19T00:00:00.000Z"


def test_render_page_uses_th_title_for_th_locale():
    spec = PageSpec(**{**SAMPLE_SPEC.__dict__, "title_th": "คลัสเตอร์"})
    out = render_page(spec, locale="th", today_iso="2026-05-19T00:00:00.000Z")
    post = frontmatter.loads(out)
    assert post.metadata["title"] == "คลัสเตอร์"


def test_render_page_has_three_numbered_sections():
    out = render_page(SAMPLE_SPEC, locale="en", today_iso="2026-05-19T00:00:00.000Z")
    assert "## 1. At a Glance" in out
    assert "## 2. References" in out
    assert "## 3. TODO" in out


def test_render_page_lists_references_and_todo():
    out = render_page(SAMPLE_SPEC, locale="en", today_iso="2026-05-19T00:00:00.000Z")
    assert "../carmen-platform/SITEMAP.md" in out
    assert "Document permissions" in out


def test_render_page_at_a_glance_bullets_are_emitted():
    out = render_page(SAMPLE_SPEC, locale="en", today_iso="2026-05-19T00:00:00.000Z")
    assert "- What a cluster is" in out


def test_iter_pages_loads_yaml_into_specs(tmp_path: Path):
    cfg = tmp_path / "pages.yaml"
    cfg.write_text(
        """
book: platform
pages:
  - path: a/b.md
    title_en: A
    title_th: A-th
    description: d
    tags: [book/platform]
    at_a_glance: [g]
    references: [r]
    todo: [t]
""".strip(),
        encoding="utf-8",
    )
    specs = list(iter_pages(cfg))
    assert len(specs) == 1
    assert specs[0].path == "a/b.md"
    assert specs[0].title_en == "A"
    assert specs[0].title_th == "A-th"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest scripts/migrate_books/test_scaffold_platform.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write the implementation**

Create `scripts/migrate_books/scaffold_platform.py`:

```python
"""Generate Platform book skeleton pages from a YAML config.

Each page has:
- Wiki.js YAML frontmatter (title, description, tags, dates, editor)
- ## 1. At a Glance      -- bulleted preview of intended subtopics
- ## 2. References       -- bulleted links/paths to source-of-truth files
- ## 3. TODO             -- bulleted checklist for the author
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

import yaml


@dataclass
class PageSpec:
    path: str            # relative to <locale>/<book>/  e.g. "clusters/home.md"
    title_en: str
    title_th: str
    description: str
    tags: list[str]
    at_a_glance: list[str]
    references: list[str]
    todo: list[str]


def iter_pages(yaml_path: Path) -> Iterator[PageSpec]:
    data = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    for raw in data["pages"]:
        yield PageSpec(
            path=raw["path"],
            title_en=raw["title_en"],
            title_th=raw["title_th"],
            description=raw["description"],
            tags=list(raw.get("tags") or []),
            at_a_glance=list(raw.get("at_a_glance") or []),
            references=list(raw.get("references") or []),
            todo=list(raw.get("todo") or []),
        )


def render_page(spec: PageSpec, *, locale: str, today_iso: str) -> str:
    title = spec.title_en if locale == "en" else spec.title_th
    tags = ", ".join(spec.tags)
    front = (
        "---\n"
        f"title: {title}\n"
        f"description: {spec.description}\n"
        "published: true\n"
        f"date: {today_iso}\n"
        f"tags: {tags}\n"
        "editor: markdown\n"
        f"dateCreated: {today_iso}\n"
        "---\n\n"
    )
    glance = "## 1. At a Glance\n\n" + "\n".join(f"- {b}" for b in spec.at_a_glance) + "\n\n"
    refs = "## 2. References\n\n" + "\n".join(f"- {r}" for r in spec.references) + "\n\n"
    todo = "## 3. TODO\n\n" + "\n".join(f"- [ ] {t}" for t in spec.todo) + "\n"
    return front + f"# {title}\n\n" + glance + refs + todo


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate Platform book skeleton pages."
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path(__file__).resolve().parent / "platform_pages.yaml",
    )
    parser.add_argument(
        "--locales",
        nargs="+",
        default=["en", "th"],
    )
    parser.add_argument(
        "--today",
        default="2026-05-19T00:00:00.000Z",
        help="ISO timestamp used for date / dateCreated.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing files (skip otherwise).",
    )
    args = parser.parse_args()

    book = "platform"
    repo_root = Path(__file__).resolve().parent.parent.parent
    created = 0
    skipped = 0

    for spec in iter_pages(args.config):
        for locale in args.locales:
            dst = repo_root / locale / book / spec.path
            dst.parent.mkdir(parents=True, exist_ok=True)
            if dst.exists() and not args.force:
                skipped += 1
                print(f"SKIP (exists): {dst.relative_to(repo_root)}")
                continue
            dst.write_text(render_page(spec, locale=locale, today_iso=args.today), encoding="utf-8")
            created += 1
            print(f"WROTE: {dst.relative_to(repo_root)}")
    print(f"\n{created} created, {skipped} skipped.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest scripts/migrate_books/test_scaffold_platform.py -v`
Expected: 6 passed

- [ ] **Step 5: Commit**

```bash
git add scripts/migrate_books/scaffold_platform.py scripts/migrate_books/test_scaffold_platform.py
git commit -m "scripts(migrate_books): platform skeleton page generator"
```

---

### Task 11: Generate Platform skeleton pages

- [ ] **Step 1: Generate EN and TH pages**

Run: `python3 -m scripts.migrate_books.scaffold_platform`
Expected: 34 `WROTE:` lines (17 pages × 2 locales) and `34 created, 0 skipped.`

- [ ] **Step 2: Spot-check one page**

Run: `head -30 en/platform/clusters/home.md`
Expected: frontmatter with title `Clusters`, description, tags including `book/platform, clusters`, then `# Clusters` and the three numbered sections.

- [ ] **Step 3: Verify with frontmatter checker**

Run: `python3 .specs/verify_frontmatter.py` (if it accepts paths) or just confirm every new file parses by:

```bash
python3 -c "
import frontmatter, pathlib
for p in pathlib.Path('.').glob('en/platform/**/*.md'):
    fm = frontmatter.load(str(p))
    assert fm.metadata.get('title'), p
    assert fm.metadata.get('dateCreated'), p
print('OK')
"
```
Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add en/platform th/platform
git commit -m "feat(platform): add Platform book skeleton pages (EN + TH)

Generates 17 pages per locale (34 total) under en/platform/ and
th/platform/ covering home, clusters, business-units, users,
report-templates, profile, and auth-roles. Each page has the standard
Wiki.js frontmatter plus three numbered sections (At a Glance,
References, TODO) — ready for content authors to fill in."
```

---

## Phase D — Landing and per-book home pages

### Task 12: Rewrite global landing pages

**Files:**
- Modify: `en/home.md`
- Modify: `th/home.md`

- [ ] **Step 1: Inspect current en/home.md**

Run: `cat en/home.md | head -30`
Record the current `dateCreated` value — it must NOT change in the rewrite.

- [ ] **Step 2: Rewrite en/home.md**

Replace the entire content of `en/home.md` with:

```markdown
---
title: Carmen Wiki
description: Internal reference for Carmen developers and testers — across Inventory and Platform products.
published: true
date: 2026-05-19T00:00:00.000Z
tags: home, landing
editor: markdown
dateCreated: <PRESERVE-EXISTING-VALUE>
---

# Carmen Wiki

Internal reference for developers and testers across the Carmen product family.

## 1. Carmen Inventory

Inventory ERP for hospitality — costing, GRN, physical count, spot check, valuation, and related modules.

[Open the Inventory book →](/en/inventory/home)

## 2. Carmen Platform

Platform admin — clusters, business units, users, and report templates that underlie every Carmen deployment.

[Open the Platform book →](/en/platform/home)

---

Use the language switcher in Wiki.js to view the same content in ภาษาไทย.
```

Replace `<PRESERVE-EXISTING-VALUE>` with the actual existing `dateCreated` value from Step 1.

- [ ] **Step 3: Rewrite th/home.md**

Similar to Step 2 but for `th/home.md` — preserve its own `dateCreated`. Content:

```markdown
---
title: Carmen Wiki
description: เอกสารอ้างอิงสำหรับนักพัฒนาและทีมทดสอบของ Carmen ครอบคลุมทั้ง Inventory และ Platform
published: true
date: 2026-05-19T00:00:00.000Z
tags: home, landing
editor: markdown
dateCreated: <PRESERVE-EXISTING-VALUE>
---

# Carmen Wiki

เอกสารอ้างอิงสำหรับนักพัฒนาและทีมทดสอบของผลิตภัณฑ์ Carmen

## 1. Carmen Inventory

ระบบ ERP สำหรับธุรกิจโรงแรม — costing, GRN, physical count, spot check, valuation และโมดูลที่เกี่ยวข้อง

[เปิด Inventory book →](/th/inventory/home)

## 2. Carmen Platform

Platform admin — clusters, business units, users และ report templates ที่เป็นรากฐานของทุก Carmen deployment

[เปิด Platform book →](/th/platform/home)

---

ใช้ language switcher ของ Wiki.js เพื่อสลับภาษา
```

- [ ] **Step 4: Commit**

```bash
git add en/home.md th/home.md
git commit -m "feat(home): rewrite global landing as two-card layout (Inventory + Platform)

Adds two ## headings (Carmen Inventory, Carmen Platform) corresponding
to the two books in the sidebar — this makes book headers resolvable
by sync_nav's home.md heading pairing logic."
```

---

### Task 13: Add per-book home pages

**Files:**
- Create: `en/inventory/home.md`
- Create: `th/inventory/home.md`
- Create: `en/platform/home.md` (already created by scaffold_platform.py — verify content)
- Create: `th/platform/home.md` (already created by scaffold_platform.py — verify content)

**Note:** Platform book home pages were generated by `scaffold_platform.py` in Task 11. Inventory book home pages need to be written manually since Inventory is migrated, not skeleton.

- [ ] **Step 1: Write en/inventory/home.md**

```markdown
---
title: Carmen Inventory
description: Carmen Inventory ERP — module reference for developers and testers.
published: true
date: 2026-05-19T00:00:00.000Z
tags: book/inventory, home
editor: markdown
dateCreated: 2026-05-19T00:00:00.000Z
---

# Carmen Inventory

Reference manual for developers and QA engineers working on the Carmen Inventory ERP — a hospitality supply chain product.

## 1. Modules

| Module | What it covers |
|---|---|
| [Access Control](/en/inventory/access-control/home) | Roles, permissions, gates |
| [Costing](/en/inventory/costing/home) | Calculation methods, FIFO, weighted average |
| [Dashboard](/en/inventory/dashboard/home) | Summary views and KPIs |
| [Good Receive Note](/en/inventory/good-receive-note/home) | GRN flow, receiving, edge cases |
| [Inventory](/en/inventory/inventory/home) | Stock movements, valuation |
| [Inventory Adjustment](/en/inventory/inventory-adjustment/home) | Manual adjustments and reasons |
| [Master Data](/en/inventory/master-data/home) | Reference data and lookups |
| [Physical Count](/en/inventory/physical-count/home) | Count cycles and reconciliation |
| [Product](/en/inventory/product/home) | Product catalog and attributes |
| [Purchase Order](/en/inventory/purchase-order/home) | PO lifecycle |
| [Purchase Request](/en/inventory/purchase-request/home) | PR approval flow |
| [Recipe](/en/inventory/recipe/home) | Recipe and BOM |
| [Reporting & Audit](/en/inventory/reporting-audit/home) | Reports and audit trail |
| [Spot Check](/en/inventory/spot-check/home) | Random count workflows |
| [Store Requisition](/en/inventory/store-requisition/home) | Inter-store transfers |
| [System Config](/en/inventory/system-config/home) | Tenant-level settings |
| [Templates](/en/inventory/templates/home) | Document templates |
| [Vendor Pricelist](/en/inventory/vendor-pricelist/home) | Vendor catalog and pricing |

## 2. How to use this book

- Start with the module home page for an overview
- Drill into sub-pages for data models, UI flows, and edge cases
- See the [global wiki landing](/en/home) for the Platform book
```

- [ ] **Step 2: Write th/inventory/home.md (TH variant)**

Same structure as Step 1, with `/th/inventory/...` paths. Translate the intro paragraph; the module table can keep English module names (matches existing Inventory page titles).

```markdown
---
title: Carmen Inventory
description: Carmen Inventory ERP — เอกสารอ้างอิงโมดูลสำหรับนักพัฒนาและทีมทดสอบ
published: true
date: 2026-05-19T00:00:00.000Z
tags: book/inventory, home
editor: markdown
dateCreated: 2026-05-19T00:00:00.000Z
---

# Carmen Inventory

คู่มืออ้างอิงสำหรับนักพัฒนาและ QA ที่ทำงานกับ Carmen Inventory ERP — ระบบ supply chain สำหรับโรงแรม

## 1. โมดูล

| โมดูล | ครอบคลุมเรื่อง |
|---|---|
| [Access Control](/th/inventory/access-control/home) | บทบาท สิทธิ์ การควบคุมการเข้าถึง |
| [Costing](/th/inventory/costing/home) | วิธีคิดต้นทุน FIFO Weighted Average |
| [Dashboard](/th/inventory/dashboard/home) | สรุปและ KPI |
| [Good Receive Note](/th/inventory/good-receive-note/home) | กระบวนการรับสินค้า |
| [Inventory](/th/inventory/inventory/home) | การเคลื่อนไหวสต็อก การประเมินมูลค่า |
| [Inventory Adjustment](/th/inventory/inventory-adjustment/home) | การปรับสต็อกและเหตุผล |
| [Master Data](/th/inventory/master-data/home) | ข้อมูลอ้างอิงและ lookups |
| [Physical Count](/th/inventory/physical-count/home) | รอบนับสต็อกและการกระทบยอด |
| [Product](/th/inventory/product/home) | แค็ตตาล็อกสินค้าและคุณสมบัติ |
| [Purchase Order](/th/inventory/purchase-order/home) | วงจรชีวิตของ PO |
| [Purchase Request](/th/inventory/purchase-request/home) | กระบวนการอนุมัติ PR |
| [Recipe](/th/inventory/recipe/home) | สูตรและ BOM |
| [Reporting & Audit](/th/inventory/reporting-audit/home) | รายงานและ audit trail |
| [Spot Check](/th/inventory/spot-check/home) | การสุ่มนับ |
| [Store Requisition](/th/inventory/store-requisition/home) | โอนสินค้าระหว่างคลัง |
| [System Config](/th/inventory/system-config/home) | การตั้งค่าระดับ tenant |
| [Templates](/th/inventory/templates/home) | เทมเพลตเอกสาร |
| [Vendor Pricelist](/th/inventory/vendor-pricelist/home) | แค็ตตาล็อกและราคาผู้ขาย |

## 2. การใช้งาน book นี้

- เริ่มจากหน้า home ของแต่ละโมดูลเพื่อภาพรวม
- เจาะลึก sub-pages สำหรับ data model, UI flow, edge cases
- ดู [global wiki landing](/th/home) สำหรับ Platform book
```

- [ ] **Step 3: Verify Platform home pages exist (from Task 11)**

Run: `ls en/platform/home.md th/platform/home.md`
Expected: both files exist.

- [ ] **Step 4: Commit**

```bash
git add en/inventory/home.md th/inventory/home.md
git commit -m "feat(home): add per-book home pages for Inventory

Platform book home pages were added in the skeleton commit. Together
they let the global landing's 'Open the Inventory book' / 'Open the
Platform book' links land somewhere useful."
```

---

## Phase E — sync_nav per-book support

### Task 14: Extend nav-overrides.yaml schema

**Files:**
- Modify: `scripts/nav-overrides.yaml`

- [ ] **Step 1: Replace contents**

Replace `scripts/nav-overrides.yaml` with:

```yaml
# Configuration for the Wiki.js multi-book navigation tree.
#
# Two sections:
#   - books:    declarative tree used in --mode=build (full rebuild)
#   - headers/links: legacy overrides used in --mode=mirror (legacy default)
#
# Keys must match EXACTLY (case-sensitive).

books:
  inventory:
    label_en: "Carmen Inventory"
    label_th: "Carmen Inventory"
    home_slug: home
    modules:
      - slug: access-control
        label_en: "Access Control"
        label_th: "Access Control"
      - slug: costing
        label_en: "Costing"
        label_th: "Costing"
      - slug: dashboard
        label_en: "Dashboard"
        label_th: "Dashboard"
      - slug: good-receive-note
        label_en: "Good Receive Note"
        label_th: "Good Receive Note"
      - slug: inventory
        label_en: "Inventory"
        label_th: "Inventory"
      - slug: inventory-adjustment
        label_en: "Inventory Adjustment"
        label_th: "Inventory Adjustment"
      - slug: master-data
        label_en: "Master Data"
        label_th: "Master Data"
      - slug: physical-count
        label_en: "Physical Count"
        label_th: "Physical Count"
      - slug: product
        label_en: "Product"
        label_th: "Product"
      - slug: purchase-order
        label_en: "Purchase Order"
        label_th: "Purchase Order"
      - slug: purchase-request
        label_en: "Purchase Request"
        label_th: "Purchase Request"
      - slug: recipe
        label_en: "Recipe"
        label_th: "Recipe"
      - slug: reporting-audit
        label_en: "Reporting & Audit"
        label_th: "Reporting & Audit"
      - slug: spot-check
        label_en: "Spot Check"
        label_th: "Spot Check"
      - slug: store-requisition
        label_en: "Store Requisition"
        label_th: "Store Requisition"
      - slug: system-config
        label_en: "System Config"
        label_th: "System Config"
      - slug: templates
        label_en: "Templates"
        label_th: "Templates"
      - slug: vendor-pricelist
        label_en: "Vendor Pricelist"
        label_th: "Vendor Pricelist"

  platform:
    label_en: "Carmen Platform"
    label_th: "Carmen Platform"
    home_slug: home
    modules:
      - slug: clusters
        label_en: "Clusters"
        label_th: "Clusters"
      - slug: business-units
        label_en: "Business Units"
        label_th: "Business Units"
      - slug: users
        label_en: "Users"
        label_th: "Users"
      - slug: report-templates
        label_en: "Report Templates"
        label_th: "Report Templates"
      - slug: profile
        label_en: "Profile"
        label_th: "Profile"
      - slug: auth-roles
        label_en: "Authentication & Roles"
        label_th: "Authentication & Roles"

# Legacy overrides — only consulted in --mode=mirror.
headers: {}
links: {}
```

- [ ] **Step 2: Commit**

```bash
git add scripts/nav-overrides.yaml
git commit -m "scripts(sync_nav): add books: block to nav-overrides for declarative tree"
```

---

### Task 15: Implement build-mode tree builder + tests

**Files:**
- Modify: `scripts/sync_nav.py`
- Modify: `scripts/test_sync_nav.py`

- [ ] **Step 1: Write the failing tests**

Append to `scripts/test_sync_nav.py`:

```python
# ===== Build-mode tree builder tests =====


def test_build_tree_one_book_one_module(tmp_path):
    from scripts.sync_nav import build_tree_from_config
    config = {
        "books": {
            "inventory": {
                "label_en": "Carmen Inventory",
                "label_th": "Carmen Inventory",
                "home_slug": "home",
                "modules": [
                    {"slug": "costing", "label_en": "Costing", "label_th": "Costing"},
                ],
            },
        },
    }
    items_en = build_tree_from_config(config, locale="en")
    # Expected items: header, link-home, link-costing
    kinds = [i["kind"] for i in items_en]
    assert kinds == ["header", "link", "link"]
    assert items_en[0]["label"] == "Carmen Inventory"
    assert items_en[1]["target"] == "/en/inventory/home"
    assert items_en[2]["target"] == "/en/inventory/costing/home"
    assert items_en[2]["label"] == "Costing"


def test_build_tree_two_books_inserts_divider_between():
    from scripts.sync_nav import build_tree_from_config
    config = {
        "books": {
            "inventory": {
                "label_en": "Carmen Inventory",
                "label_th": "Carmen Inventory",
                "home_slug": "home",
                "modules": [{"slug": "costing", "label_en": "Costing", "label_th": "Costing"}],
            },
            "platform": {
                "label_en": "Carmen Platform",
                "label_th": "Carmen Platform",
                "home_slug": "home",
                "modules": [{"slug": "clusters", "label_en": "Clusters", "label_th": "Clusters"}],
            },
        },
    }
    items = build_tree_from_config(config, locale="en")
    kinds = [i["kind"] for i in items]
    assert kinds == [
        "header", "link", "link",       # inventory
        "divider",                      # separator
        "header", "link", "link",       # platform
    ]


def test_build_tree_th_uses_th_labels_and_paths():
    from scripts.sync_nav import build_tree_from_config
    config = {
        "books": {
            "inventory": {
                "label_en": "Carmen Inventory",
                "label_th": "Carmen Inventory TH",
                "home_slug": "home",
                "modules": [
                    {"slug": "costing", "label_en": "Costing", "label_th": "การคิดต้นทุน"},
                ],
            },
        },
    }
    items_th = build_tree_from_config(config, locale="th")
    assert items_th[0]["label"] == "Carmen Inventory TH"
    assert items_th[1]["target"] == "/th/inventory/home"
    assert items_th[2]["target"] == "/th/inventory/costing/home"
    assert items_th[2]["label"] == "การคิดต้นทุน"


def test_build_tree_link_items_have_uuid_ids():
    from scripts.sync_nav import build_tree_from_config
    config = {
        "books": {
            "inventory": {
                "label_en": "Carmen Inventory",
                "label_th": "Carmen Inventory",
                "home_slug": "home",
                "modules": [
                    {"slug": "costing", "label_en": "Costing", "label_th": "Costing"},
                ],
            },
        },
    }
    items = build_tree_from_config(config, locale="en")
    ids = [i["id"] for i in items]
    assert all(len(i) == 36 for i in ids)  # UUID4 string length
    assert len(set(ids)) == len(ids)        # all unique
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest scripts/test_sync_nav.py -v -k "build_tree"`
Expected: 4 failures with `AttributeError: ... build_tree_from_config`

- [ ] **Step 3: Add `build_tree_from_config` to sync_nav.py**

In `scripts/sync_nav.py`, after the existing "Section 10: Orchestration" block and before "Section 11: CLI", insert a new section:

```python
# ===== Section 10b: Declarative tree builder (build mode) =====


def _new_link(label: str, target: str) -> dict[str, Any]:
    return {
        "id": str(uuid.uuid4()),
        "kind": "link",
        "label": label,
        "icon": "",
        "targetType": "page",
        "target": target,
        "visibilityMode": "all",
        "visibilityGroups": [],
    }


def _new_header(label: str) -> dict[str, Any]:
    return {
        "id": str(uuid.uuid4()),
        "kind": "header",
        "label": label,
        "icon": "",
        "targetType": "none",
        "target": "",
        "visibilityMode": "all",
        "visibilityGroups": [],
    }


def _new_divider() -> dict[str, Any]:
    return {
        "id": str(uuid.uuid4()),
        "kind": "divider",
        "label": "",
        "icon": "",
        "targetType": "none",
        "target": "",
        "visibilityMode": "all",
        "visibilityGroups": [],
    }


def build_tree_from_config(
    config: dict[str, Any],
    *,
    locale: str,
) -> list[dict[str, Any]]:
    """Build a Wiki.js nav tree for one locale from the books: config block.

    For each book: emit a header, a link to /<locale>/<book>/<home_slug>,
    then a link per module pointing to /<locale>/<book>/<module>/<home_slug>.
    A divider separates consecutive books.
    """
    label_key = f"label_{locale}"
    items: list[dict[str, Any]] = []
    books = config.get("books") or {}
    for idx, (book_slug, book) in enumerate(books.items()):
        if idx > 0:
            items.append(_new_divider())
        items.append(_new_header(book[label_key]))
        home_slug = book.get("home_slug", "home")
        items.append(
            _new_link(
                "Home",
                f"/{locale}/{book_slug}/{home_slug}",
            )
        )
        for module in book.get("modules") or []:
            items.append(
                _new_link(
                    module[label_key],
                    f"/{locale}/{book_slug}/{module['slug']}/{home_slug}",
                )
            )
    return items
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest scripts/test_sync_nav.py -v -k "build_tree"`
Expected: 4 passed

- [ ] **Step 5: Run all sync_nav tests to verify nothing broke**

Run: `python3 -m pytest scripts/test_sync_nav.py -v`
Expected: all tests pass (existing + 4 new)

- [ ] **Step 6: Commit**

```bash
git add scripts/sync_nav.py scripts/test_sync_nav.py
git commit -m "scripts(sync_nav): add build_tree_from_config for declarative nav"
```

---

### Task 16: Wire CLI mode flag

**Files:**
- Modify: `scripts/sync_nav.py`

Order: extract mirror first (preserves existing behavior), add build, then re-wire main(). This keeps the file runnable after each step.

- [ ] **Step 1: Extract mirror mode into a function**

In `scripts/sync_nav.py`, add a new function `_run_mirror_mode` just before the current `main()` function. The body is the existing main() body starting from the "# 1. fetch" comment through the final `print(format_summary(...))`. Function signature:

```python
def _run_mirror_mode(
    *,
    api_url: str,
    api_token: str,
    repo_root: Path,
    overrides_path: Path,
    dry_run: bool,
    verbose: bool,
) -> int:
    """Fetch EN nav from Wiki.js, derive TH, push TH (existing behavior)."""
    # body: everything from existing main() between "# 1. fetch" and the final return
    # — but read `args.dry_run` and `args.verbose` from parameters instead.
```

Replace any reference to `args.dry_run` with `dry_run` and `args.verbose` with `verbose`. Leave the function returning the same exit codes (0 on success, 3/4 on errors).

- [ ] **Step 2: Add `_run_build_mode`**

Add this function next to `_run_mirror_mode`:

```python
def _run_build_mode(
    *,
    api_url: str,
    api_token: str,
    overrides_path: Path,
    dry_run: bool,
) -> int:
    config = yaml.safe_load(overrides_path.read_text(encoding="utf-8")) or {}
    if not config.get("books"):
        print(
            "ERROR: nav-overrides.yaml has no `books:` block; cannot build.",
            file=sys.stderr,
        )
        return 5

    en_items = build_tree_from_config(config, locale="en")
    th_items = build_tree_from_config(config, locale="th")
    print(
        f"[BUILD]  en: {len(en_items)} items, th: {len(th_items)} items",
        file=sys.stderr,
    )

    new_tree = [
        {"locale": "en", "items": en_items},
        {"locale": "th", "items": th_items},
    ]

    if dry_run:
        print("[DRY-RUN] tree preview:", file=sys.stderr)
        for locale_tree in new_tree:
            print(f"  {locale_tree['locale']}:", file=sys.stderr)
            for item in locale_tree["items"]:
                print(f"    {item['kind']:<8} {item.get('label', ''):<40} {item.get('target', '')}", file=sys.stderr)
        print("[DRY-RUN] no mutation sent.", file=sys.stderr)
        return 0

    # In build mode, we don't preserve other locales — Wiki.js currently
    # only has en + th, and build mode is the source of truth.
    push_navigation(api_url, api_token, new_tree)
    print("[PUSH]   updateTree succeeded.", file=sys.stderr)
    return 0
```

- [ ] **Step 3: Update main() to dispatch by mode**

Replace the existing `main()` function with:

```python
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Manage Wiki.js navigation tree.",
    )
    parser.add_argument(
        "--mode",
        choices=["mirror", "build"],
        default="mirror",
        help=(
            "mirror (default): fetch EN from Wiki.js, derive and push TH only. "
            "build: rebuild EN + TH from nav-overrides.yaml books: block."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Compute + print; do not push.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print per-item resolution lines (mirror mode only).",
    )
    args = parser.parse_args(argv)

    _setup_logging(args.verbose)

    api_url = os.environ.get("WIKI_API_URL")
    api_token = os.environ.get("WIKI_API_TOKEN")
    if not api_url or not api_token:
        print(
            "ERROR: WIKI_API_URL and WIKI_API_TOKEN must be set "
            "(see .env.example). Source your .env first.",
            file=sys.stderr,
        )
        return 2

    repo_root = Path(__file__).resolve().parent.parent
    overrides_path = Path(__file__).resolve().parent / "nav-overrides.yaml"

    if args.mode == "build":
        return _run_build_mode(
            api_url=api_url,
            api_token=api_token,
            overrides_path=overrides_path,
            dry_run=args.dry_run,
        )
    return _run_mirror_mode(
        api_url=api_url,
        api_token=api_token,
        repo_root=repo_root,
        overrides_path=overrides_path,
        dry_run=args.dry_run,
        verbose=args.verbose,
    )
```

- [ ] **Step 4: Smoke-test the CLI**

Run: `python3 scripts/sync_nav.py --help`
Expected: help text shows `--mode {mirror,build}`.

Run (without env vars to test arg parsing): `WIKI_API_URL= WIKI_API_TOKEN= python3 scripts/sync_nav.py --mode=build --dry-run`
Expected: exit 2 with the env-vars error message.

- [ ] **Step 5: Run all sync_nav tests**

Run: `python3 -m pytest scripts/test_sync_nav.py -v`
Expected: all tests pass (no behavior change for mirror mode; new build_tree tests still pass).

- [ ] **Step 6: Commit**

```bash
git add scripts/sync_nav.py
git commit -m "scripts(sync_nav): add --mode=build CLI flag for declarative nav rebuild"
```

---

### Task 17: Update scripts/README.md

**Files:**
- Modify: `scripts/README.md`

- [ ] **Step 1: Add build-mode section**

In `scripts/README.md`, after the existing "Usage" section, insert:

```markdown
### Build mode (declarative)

To rebuild the entire nav tree (EN + TH) from `nav-overrides.yaml`:

```bash
python3 scripts/sync_nav.py --mode=build --dry-run    # preview
python3 scripts/sync_nav.py --mode=build              # apply
```

Build mode reads the `books:` block in `nav-overrides.yaml`. Each book
becomes a header followed by a link to its home page and one link per
module. A divider separates books. Both EN and TH locales are rebuilt
from the same config, with per-item TH labels resolved from
`label_th:`.

Use mirror mode (the default) when you maintain EN nav in Wiki.js admin
and only want TH to follow. Use build mode after a structural change
(adding a book, renaming a module).
```

Also extend the "Files" table — add a `books:` row description in the
existing `nav-overrides.yaml` row.

- [ ] **Step 2: Commit**

```bash
git add scripts/README.md
git commit -m "docs(scripts): document sync_nav build mode and books: config"
```

---

## Phase F — Project memory and conventions

### Task 18: Update CLAUDE.md

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Update the structure paragraph**

In `CLAUDE.md`, in the "Repository Nature" section, replace this sentence:

> Work is organized under top-level locale directories `en/` and `th/`, each containing topic subdirectories (e.g. `en/inventory/`, `th/purchase-request/`).

with:

> Work is organized as `<locale>/<book>/<module>/`. Two books are defined: **Carmen Inventory** (existing content — costing, GRN, physical count, etc.) and **Carmen Platform** (admin product — clusters, business units, users, report templates). The repo root `home.md` is a two-card landing; each book has its own `<book>/home.md` index.

- [ ] **Step 2: Add a "Multi-book layout" subsection**

After "Repository Nature", before "Wiki.js Page Format", add:

```markdown
## Multi-book layout

| Book | Location | Audience |
|------|----------|----------|
| Inventory | `en/inventory/`, `th/inventory/` | Developers and QA working on Carmen Inventory ERP |
| Platform | `en/platform/`, `th/platform/` | Developers and support working on the platform admin product |

Screenshots live under `assets/screenshots/<book>/<module>/<slug>.png`.

When adding a new page, place it under the correct book. Cross-book content (e.g. how Inventory interacts with cluster-scoped permissions) goes in the most-affected book and links across.
```

- [ ] **Step 3: Update reference repos table (Frontend row)**

In the "Reference Repositories" table, add a row for `carmen-platform`:

```markdown
| **Platform admin** | `../carmen-platform/` | React/TypeScript SPA for cluster/BU/user/report-template management — source of truth for the Platform book |
```

- [ ] **Step 4: Commit**

```bash
git add CLAUDE.md
git commit -m "docs(CLAUDE): document multi-book layout and add carmen-platform reference"
```

---

### Task 19: Update auto-memory entries

**Files:**
- Modify: `/Users/samutpra/.claude/projects/-Users-samutpra-GitHub-carmensoftware-organize-carmen-wiki/memory/wiki_structure_decisions.md`
- Modify: `/Users/samutpra/.claude/projects/-Users-samutpra-GitHub-carmensoftware-organize-carmen-wiki/memory/screenshot_pattern.md`
- Modify: `/Users/samutpra/.claude/projects/-Users-samutpra-GitHub-carmensoftware-organize-carmen-wiki/memory/MEMORY.md`
- Optionally Create: `/Users/samutpra/.claude/projects/-Users-samutpra-GitHub-carmensoftware-organize-carmen-wiki/memory/books_layout.md`

**Note:** Memory lives outside the repo. These changes are NOT committed to git — they update the local Claude project memory only.

- [ ] **Step 1: Update wiki_structure_decisions.md**

Append a "Multi-book layout (2026-05-19)" subsection that records:
- Folder layout is now `<locale>/<book>/<module>/<page>`.
- Two books exist: Inventory (existing) and Platform (skeleton).
- Wiki.js nav rebuild uses `scripts/sync_nav.py --mode=build` with `nav-overrides.yaml books:` block.

- [ ] **Step 2: Update screenshot_pattern.md**

Change the path pattern to `assets/screenshots/<book>/<module>/<slug>.png` and update the example.

- [ ] **Step 3: Create books_layout.md (optional)**

If desired, add a dedicated entry — see the auto-memory guidance in the system prompt for format.

- [ ] **Step 4: Update MEMORY.md index**

If `books_layout.md` was created, add one index line. If wiki_structure_decisions.md was significantly expanded, refresh its one-line hook.

- [ ] **Step 5: No git commit**

Memory files live outside the repo. Nothing to add or commit.

---

## Phase G — Verification and push

### Task 20: Full pre-merge verification

- [ ] **Step 1: Run every test in the repo**

Run: `python3 -m pytest scripts/ -v`
Expected: all tests pass (folder_moves: 5, rewrite_links: 11, verify: 4, scaffold_platform: 6, sync_nav: existing + 4 new).

- [ ] **Step 2: Run the stale-path verifier**

Run: `python3 -m scripts.migrate_books.verify`
Expected: `OK: no stale paths found.`

- [ ] **Step 3: Run sync_nav build dry-run (no env vars needed for tree preview if we skip the API call)**

Set env then run:

```bash
set -a; source .env; set +a
python3 scripts/sync_nav.py --mode=build --dry-run
```
Expected: BUILD line with item counts (Inventory: 1 header + 1 home link + 18 module links = 20; Platform: 1 header + 1 home link + 6 module links = 8; divider: 1; total = 29 items per locale).

- [ ] **Step 4: Walk a sample of restructured pages**

Run: `ls en/inventory/costing/ && ls en/platform/clusters/ && ls assets/screenshots/inventory/costing/`
Expected: existing module contents present in their new locations; platform skeleton pages present.

- [ ] **Step 5: Inspect git log of the branch**

Run: `git log --oneline main..HEAD`
Expected: roughly 14 commits, all with `scripts(...)`, `chore(...)`, `feat(...)`, or `docs(...)` prefixes.

---

### Task 21: Push branch and verify in dev Wiki.js

- [ ] **Step 1: Push the branch**

Run: `git push -u origin feat/multi-book-restructure`
Expected: branch published.

- [ ] **Step 2: Wait for Wiki.js storage Git editor pull**

In Wiki.js admin (`http://dev.blueledgers.com:3987/`), trigger a pull (Admin → Storage → Git → Pull) or wait for the configured sync interval.

- [ ] **Step 3: Run build-mode push**

Run: `python3 scripts/sync_nav.py --mode=build`
Expected: `[PUSH] updateTree succeeded.`

- [ ] **Step 4: Visual verification — five checks**

In a browser:

1. Open `http://dev.blueledgers.com:3987/en/home` — confirm landing page renders with `## 1. Carmen Inventory` and `## 2. Carmen Platform` sections + open-book links.
2. Click "Open the Inventory book" → lands on `/en/inventory/home`; module table renders.
3. Open a sample Inventory page (e.g. `/en/inventory/costing/calculation-methods` — or any existing page). Confirm internal links and image refs still work.
4. Click "Open the Platform book" → lands on `/en/platform/home`. Open `/en/platform/clusters/home` — three numbered sections render.
5. Sidebar shows both book headers + module link lists. Switch to TH locale via Wiki.js language toggle — confirm `/th/...` variants render likewise.

- [ ] **Step 5: Capture screenshots for the PR**

Save screenshots of: global landing, Inventory book home, Platform book home, sidebar with both books visible, and at least one migrated inventory page.

---

### Task 22: Open the pull request

- [ ] **Step 1: Confirm branch is up to date**

Run: `git status && git log --oneline main..HEAD`
Expected: clean tree, expected commit list.

- [ ] **Step 2: Create the PR**

```bash
gh pr create --title "Multi-book restructure: Inventory + Platform" --body "$(cat <<'EOF'
## Summary

- Restructure carmen-wiki into two top-level books (Inventory + Platform) under one Wiki.js instance
- Move all 18 existing inventory modules to `en/inventory/<module>` and `th/inventory/<module>`; rewrite all internal links and image refs
- Add Platform book skeleton (17 pages × 2 locales) sourced from `../carmen-platform/`
- Add `scripts/sync_nav.py --mode=build` to rebuild the nav tree (EN + TH) from `nav-overrides.yaml`

Design: `docs/superpowers/specs/2026-05-19-multi-book-restructure-design.md`
Plan: `docs/superpowers/plans/2026-05-19-multi-book-restructure.md`

## Test plan

- [x] All scripts/* unit tests pass (`pytest scripts/`)
- [x] `python3 -m scripts.migrate_books.verify` reports no stale paths
- [x] `sync_nav.py --mode=build --dry-run` previews 29 items per locale
- [x] Global landing renders with two book cards
- [x] Each book home renders with module table
- [x] Sample inventory page renders with rewritten links
- [x] Sample platform skeleton renders with three numbered sections
- [x] Sidebar shows both book headers in EN and TH

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

- [ ] **Step 3: Attach screenshots from Task 21 Step 5**

Use the PR's GitHub web UI to drag-and-drop the screenshots into the PR description (or as a top-level comment).

- [ ] **Step 4: Return the PR URL to the user**

---

## Out of scope reminders

Per the design spec, the following are explicitly OUT of scope for this PR — do NOT do them:

- Authoring deep content for any Platform module (separate follow-up PRs per module)
- Adding additional books (micro-report, micro-cronjobs, backend, mobile)
- Wiki.js theme/JS customization
- HTTP 301 redirects from old URLs
- Cleaning up loose `.png` files at repo root
- Switching documentation engines

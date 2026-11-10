---
title: Non-obvious structural decisions baked into carmen-wiki
author: Thammanoon
date: 2026-11-09
id: l-e77f5a52
scope: repo
status: active
touches:
  - docs/superpowers/specs/2026-05-19-multi-book-restructure-design.md
  - docs/superpowers/plans/2026-05-19-multi-book-restructure.md
  - scripts/sync_nav.py
  - ".specs/2026-05-15-purchase-request-sub-pages-design.md"
  - ".specs/2026-05-15-purchase-request-sub-pages-plan.md"
  - ".specs/templates/README.md"
  - ".specs/verify_frontmatter.py"
---

## Decided
The carmen-wiki repo has gone through several structural decisions in 2026-05 that are easily lost if a future session only reads the current tree. These decisions are intentional — do not "fix" or undo them without checking with the user.

**Layout — `<locale>/<book>/<module>/` (multi-book, decided 2026-05-19):**
- Top-level locales are still `en/` and `th/`, but each now contains a **book** subdirectory.
- Two books defined: `inventory/` (the original 18 module folders, moved under `en/inventory/` and `th/inventory/`) and `platform/` (skeleton for the carmen-platform admin SPA).
- Module folders sit under the book: e.g. `en/inventory/costing/`, `en/platform/clusters/`.
- Each book has a `home.md` index (`en/inventory/home.md`, `en/platform/home.md`); the locale root `home.md` is a two-card landing pointing at both books.
- `.specs/` stays at repo root — NOT under any locale. It's hidden meta, not wiki content.
- An earlier round used `.th.md` suffix instead of `th/` tree; that was abandoned for the Wiki.js-native layout. Don't suggest reverting either decision.

**Why multi-book:**
- 2026-05-19 the user requested moving current docs to "Carmen Inventory" book and adding a new "Carmen Platform" book sourced from `../carmen-platform/`.
- Approach A (big-bang single PR) was chosen over phased.
- Design: `docs/superpowers/specs/2026-05-19-multi-book-restructure-design.md`. Plan: `docs/superpowers/plans/2026-05-19-multi-book-restructure.md`.

## Watch out
- New inventory pages go under `en/inventory/<module>/` and `th/inventory/<module>/`.
- New platform pages go under `en/platform/<module>/` and `th/platform/<module>/`.
- Cross-book references go in the most-affected book and link across.
- Wiki.js nav rebuilt via `python3 scripts/sync_nav.py --mode=build` (declarative from `nav-overrides.yaml` `books:` block). Legacy mirror mode (`--mode=mirror`) still works.

**purchase-request is the reference implementation** (now at `en/inventory/purchase-request/` and `th/inventory/purchase-request/` after the 2026-05-19 restructure).
…

_From Claude Code's memory of this repo, last updated May 19._

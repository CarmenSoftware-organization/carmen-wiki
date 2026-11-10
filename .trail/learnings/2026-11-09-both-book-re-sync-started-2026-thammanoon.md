---
title: Both-book re-sync started 2026-09-22
author: Thammanoon
date: 2026-11-09
id: l-3355c41f
scope: repo
status: active
touches:
  - ".specs/carmen-docs-drift-2026-09-22.md"
  - en/inventory/general-ledger.md
  - data-model.pdf
  - ".specs/resync-inventory-2026-09-22-progress.md"
  - scripts/push_pages.py
---

## Decided
Re-sync of both wiki books to source, kicked off 2026-09-22 via a grilling session; owner went to sleep and asked for it to run unattended.

**Decisions (owner-settled 2026-09-22):** both books · diff-based + ~10-page/book spot-check of permission/enum/API-shape claims · **EN only, TH not touched this round** (owner reversed the "EN+TH together" answer at the last minute) · no screenshot recapture · one branch + PR per book, Platform first · push to dev Wiki.js before merge, **merge is the owner's step** · checklists updated in the same PR · `carmen/docs` drift recorded in `.specs/carmen-docs-drift-2026-09-22.md`, never edited at source · new inventory-touching subsystems (GL posting, period-end, my-pending, cost-layer extra cost) get real pages; GL master/budget/JV template get one stub landing `en/inventory/general-ledger.md` + Not-yet checklist rows · test-scenario pages only cross-link the e2e catalog, no case mirroring · `data-model.pdf` at repo root is unrelated → gitignored.
…

## Watch out
when resuming, check `gh pr view 11` and the Inventory worktree's git log first; run `scripts/push_pages.py` on changed files (needs `.venv` + `scripts/.env`; macOS has no `timeout` binary). See wiki-structure-decisions and platform-resync-2026-09-05.

_From Claude Code's memory of this repo, last updated Sep 23._

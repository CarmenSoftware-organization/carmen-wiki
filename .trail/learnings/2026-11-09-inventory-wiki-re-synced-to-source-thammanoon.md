---
title: Inventory wiki re-synced to source changes since 2026-06-11
author: Thammanoon
date: 2026-11-09
id: l-49241477
scope: repo
status: active
touches:
  - ".specs/resync-2026-06-17-progress.md"
  - docs/superpowers/specs/2026-06-17-inventory-wiki-resync-design.md
---

## Decided
On 2026-06-17 both books were re-synced against source changes since the last sync (2026-06-11): backend-v2 (330 commits) + frontend-react (109) + carmen-platform (7). Work is on branch **`docs/resync-inventory-2026-06-17`** (12 commits), **not merged, not pushed** — awaiting user review/merge.

Inventory: dominant finding was the `doc_version` optimistic-lock rollout, already documented in most modules; only real gaps were filled. 8 modules edited (EN+TH paired): physical-count, spot-check, inventory (valuation fix migration 063 + txn doc_version), purchase-request, vendor-pricelist, product, master-data (vendor+location), good-receive-note (mobile draft-only list filter). 10 inventory modules verified IN SYNC.

Platform: carmen-platform's 7 commits were one feature — the **Application `device` field** (`tb_application.device`, default `"web"`, SPA set mobile/web/desktop/pos). Edited the `applications` module (EN+TH); all other Platform modules IN SYNC. Note: this `device` is what the GRN mobile draft-only filter reads via `x-app-id` — the two edits cross-link.

Bug fixes that aligned code to already-documented behavior were deliberately skipped (no invented edits).

**Why:** user asked to re-sync "all of it", edit-directly per module, then went offline — autonomous run.

## Watch out
both books now done for this window — nothing deferred. Full detail in `.specs/resync-2026-06-17-progress.md`. Approach + per-module procedure in `docs/superpowers/specs/2026-06-17-inventory-wiki-resync-design.md`. See process_coverage_checklist, platform_book_sync_2026_06_10.

_From Claude Code's memory of this repo, last updated Jun 17._

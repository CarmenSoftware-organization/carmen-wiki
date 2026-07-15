---
title: Spot Check — Data Model
description: Entities, fields, relationships, and enums for the spot-check module.
published: true
date: 2026-07-15T18:38:42.000Z
tags: spot-check, data-model, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T14:30:00.000Z
---

# Spot Check — Data Model

> **At a Glance**
> **Tables:** `tb_spot_check` &nbsp;·&nbsp; `tb_spot_check_detail` &nbsp;·&nbsp; `tb_spot_check_comment` (schema-only, unused by the frontend) &nbsp;·&nbsp; `tb_spot_check_detail_comment` (real — the per-line notes/photo dialog)
> **Audience:** Developer / Auditor (dev reference)
> **Key FKs:** header `→ tb_location`; detail `→ tb_product` and `→ tb_unit` (`inventory_unit_id`). There is **no linkage of any kind** — no FK, no JSON convention, not even a shared description string — from a spot check to [inventory-adjustment](/en/inventory/inventory-adjustment) or to any inventory ledger row
> **Audit pattern:** standard `created_*` / `updated_*` / `deleted_*`; flat two-level tree (no period parent — ad-hoc, not period-bound, unlike [physical-count](/en/inventory/physical-count)); spot-check does not write to the inventory ledger and its own `submit()` does not create any other document either

> **Source of truth:** Backend Prisma schema plus the service methods that read/write it. Always read both first when updating this page:
> - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` (lines ~3964-4130)
> - `../carmen-turborepo-backend-v2/apps/micro-business/src/inventory/spot-check/spot-check.service.ts`
> - `../carmen-turborepo-backend-v2/apps/micro-business/src/inventory/spot-check/spot-check.logic.ts`
>
> The `generated/client/schema.prisma` file under the Prisma package is an auto-generated copy and not authoritative.

## 1. Overview

The Spot Check module persists a **flat two-level document tree** under `tb_spot_check` → `tb_spot_check_detail`: a single header carries the location, date window, `method` (random / high_value / manual), `size`, and `doc_status`; each detail row is one sampled product with `on_hand_qty` (a live-stock snapshot, re-taken twice — once at creation, again at review), `actual_qty` (counted), and `diff_qty` (variance). There is **no `tb_spot_check_period`** parent — spot checks are ad-hoc, not bound to a fiscal-period header, and the `current` endpoint's "current" refers to "latest pending/in-progress documents regardless of period," not a period entity. Comments hang off both levels, but only the detail-level table is actually wired into the frontend — the entry screen's per-line "Add Notes" dialog reads/writes `tb_spot_check_detail_comment` via `GET`/`POST /spot-check-detail-comment/:detailId`; `tb_spot_check_comment` (header-level) has a Prisma model and a backend controller, but zero frontend hooks reference it (`use-spot-check-comments.ts` contains only a `TODO` placeholder for the header-level endpoints).

**The module does not write to the inventory ledger, and — unlike [physical-count](/en/inventory/physical-count) — its own final submit does not create any other document either.** `submit()`'s only effect is `doc_status = completed` plus an `end_date` stamp; its own doc-comment states this directly: *"Does not create stock-in/stock-out — any follow-up adjustments are user-driven."* A repo-wide search of this module's frontend and backend for `stock_in`, `stock_out`, `executeAdjustment`, `journal`, and `ledger` returned zero hits. A spot check is a self-contained record of a count and its variance; correcting that variance in the ledger is an entirely separate, unlinked action a user must take through [inventory-adjustment](/en/inventory/inventory-adjustment) if they choose to.

## 2. Entities

The canonical Prisma schema defines four tables (verified against `prisma-shared-schema-tenant/prisma/schema.prisma` lines 3964-4130):

- **`tb_spot_check`** — the spot-check header. Carries `spot_check_no` (document number, format `SC{YY}{MM}{seq}` via the shared running-code service), `start_date` (default `now()`) / `end_date` (nullable; stamped only by `submit()`), `location_id → tb_location` with snapshot `location_code` / `location_name`, `doc_status` on `enum_spot_check_status` (`pending`, `in_progress`, `void`, `completed`; default `pending`), `method` on `enum_spot_check_method` (`random` / `high_value` / `manual`; default `random`), `size` (sample target count, default `10` — for `manual` checks this is simply the count of products the user actually picked), `description`, `note`, `doc_version` (`Int @db.Integer`, default `0` — optimistic-concurrency counter; every `update`/`save`/`review`/`submit` call must echo the current value or the `where` clause's compound match fails), and `info` / `dimension` JSON blobs (both unused by any current logic — no code was found reading either field back). Unique within `(spot_check_no, deleted_at)`.
- **`tb_spot_check_comment`** — header-level comments/attachments. Carries `message`, `attachments` JSON array, `enum_comment_type` (`user`/`system`). A real Prisma model with a real backend controller (`spot-check-comments.controller.ts`), but **no frontend hook or screen in `carmen-inventory-frontend-react` reads or writes it** — confirmed by `use-spot-check-comments.ts`'s own `TODO` comment listing the header-level endpoints as not yet implemented.
- **`tb_spot_check_detail`** — the per-product spot-check line. Carries `product_id`, snapshot `product_code` / `product_name` / `product_local_name` / `product_sku`, `inventory_unit_id` (FK to `tb_unit`), `on_hand_qty` (`Decimal(20,5)`, default `0` — but every real row created through `create()` is seeded with the pool's **live stock quantity at sample time**, not `0`; it is then **overwritten again** with a fresh live figure by `reviewItems()` when the user clicks Submit for Review), `actual_qty` (`Decimal(20,5)`, nullable, seeded `0` at creation — not `null`), `diff_qty` (`actual_qty − on_hand_qty`, `Decimal(20,5)`, default `0`), `counted_at` / `counted_by_id` (stamped by **both** `saveItems()` and `reviewItems()` — unlike physical-count, where only the mid-count Save call stamps `counted_at`), and `sequence_no` for sheet ordering (assigned `1..N` at creation). Unique within `(spot_check_id, product_id, dimension, deleted_at)`.
- **`tb_spot_check_detail_comment`** — line-level comments/attachments. The one comment table the live UI actually uses: the entry screen's per-line notes dialog (`sc-entry-notes-dialog.tsx`) reads/writes it via `GET`/`POST /spot-check-detail-comment/:detailId`, storing free text plus photo attachments (matching the identical pattern used by [physical-count](/en/inventory/physical-count)'s own notes dialog).

## 3. Relationships

```
tb_location
    │
    └─1──*──► tb_spot_check  (doc_status: pending → in_progress → completed, or → void;
                │              method: random | high_value | manual; size: N)
                │
                ├─1──*──► tb_spot_check_comment  (schema-only — no frontend hook uses it)
                │
                └─1──*──► tb_spot_check_detail
                            │   (on_hand_qty snapshotted at create, overwritten again at review;
                            │    actual_qty / diff_qty; counted_at / counted_by_id stamped by
                            │    BOTH save and review calls; no lot_no column)
                            │
                            └─1──*──► tb_spot_check_detail_comment  (real: photo/notes)

At submit(), doc_status becomes completed and end_date is stamped. That is the entire effect.
No other table is read or written by this action:
    ▼
(nothing)  — no tb_stock_in / tb_stock_out, no tb_inventory_transaction, no linkage field of any kind.
Any ledger correction is a fully separate, manually-initiated inventory-adjustment document.
```

Notes:

- **Two-level hierarchy, no period parent.** Unlike physical-count's three-level `tb_physical_count_period` → `tb_physical_count` → `tb_physical_count_detail` tree, a spot check is a single `(location, time-window)` document with no period-level grouping entity at all. The `GET /spot-check/current` endpoint's "current" means "latest `pending`/`in_progress` documents, regardless of any period" — a direct reading of `findCurrentByLocation()`'s own code comment.
- **`on_hand_qty` is captured twice, not once.** `create()` seeds it from `SpotCheckLogic.getProductsByLocation()`'s live stock figure at sample time; `saveItems()` (the mid-count Save call) never touches it again — it only recomputes `diff_qty` against whatever value is currently stored; `reviewItems()` (Submit for Review) recomputes it a second time from a fresh `groupBy` over `tb_inventory_transaction_detail`, with no date cut-off. If other inventory movement happens at that location between creation and review, the two snapshots can differ — the review-time figure is what the user actually sees compared against.
- **All explicit `@relation` FK declarations use `onDelete: NoAction`** (or `Cascade` for `inventory_unit_id`) — preserving soft-delete (`deleted_at`) semantics.

## 4. Enums

- **`enum_spot_check_status`** — document-level lifecycle. Four values: `pending` (created; `on_hand_qty` snapshot taken; not yet touched by a save or review call), `in_progress` (the mid-count **Save** call has run at least once), `void` (voided via Reset — reachable from `pending` or `in_progress` only), `completed` (submitted; terminal). **A document can reach `completed` directly from `pending`, skipping `in_progress` entirely** — `submit()`'s only precondition is that the current status is neither `completed` nor `void`; a user who counts every line and clicks straight through to Submit for Review then Submit, without ever triggering a mid-count Save, never transitions the header to `in_progress` at all, since only `saveItems()` performs that transition.
- **`enum_spot_check_method`** — sample-selection strategy on `tb_spot_check.method`. Three values: `random` (Fisher-Yates shuffle over the eligible product pool, first `size` kept), `high_value` (ranks the pool by the highest `cost_per_unit` seen on a cost-layer receipt inside the tenant's currently open-or-locked fiscal period at that location, optionally excluding anything under a `minimum_cost` floor — requires at least one `tb_period` with `status ∈ {open, locked}` to exist, or creation fails with `SPOT_CHECK_NO_ACTIVE_PERIOD`), `manual` (the caller supplies an explicit `product_id[]`; products not found in the eligible pool are silently dropped, and an empty resulting set after filtering fails with `"None of the selected products were found at this location"`).
- **Frontend-only status values with no schema backing.** `types/spot-check.ts`'s `SpotCheckStatus` union additionally lists `"voided"` and `"cancelled"` alongside the four real Prisma values — neither exists on `enum_spot_check_status`, so neither can ever actually appear in a document's `doc_status`. Likely dead union members carried over from another module's type, not a sign of a richer status set.
- **`enum_transaction_type`** — at the inventory ledger level (schema line ~1103). `spot-check` is not a value on this enum, and — since `submit()` writes nothing to the ledger at all — no `adjustment_in`/`adjustment_out` row is ever produced by this module's own action either.

## 5. Divergences from carmen/docs

No `carmen/docs` source folder exists for this module. A planning-stage document exists in the E2E repo instead (`docs/persona-doc/System Process/tx-10-spot-check.md`, v1.0.0, dated 2026-04-27) — its central claim, that variance posting to inventory/lots/cost is "Pending — not yet implemented," matches the live code exactly (there is no posting mechanism at all, pending or otherwise). Where it diverges is the status lifecycle: it describes six states (`draft`, `pending`, `in-progress`, `on-hold`, `completed`, `cancelled`) against the live schema's four (`pending`, `in_progress`, `void`, `completed`) — see [spot-check/02-business-rules](/en/inventory/spot-check/02-business-rules) § 5.1 for the full comparison.

## 6. References

- **Primary (source of truth):** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — four entities (`tb_spot_check`, `tb_spot_check_comment`, `tb_spot_check_detail`, `tb_spot_check_detail_comment`); two enums (`enum_spot_check_status`, `enum_spot_check_method`).
- **Service layer:** `../carmen-turborepo-backend-v2/apps/micro-business/src/inventory/spot-check/spot-check.service.ts` (create/update/delete/reset/saveItems/reviewItems/getReview/submit/findCurrentByLocation/getProductsByLocation), `spot-check.logic.ts` (sampling strategies).
- **Secondary (planning-stage, partially confirmed):** `../carmen-inventory-frontend-e2e/docs/persona-doc/System Process/tx-10-spot-check.md`.
- **Frontend:** `../carmen-inventory-frontend-react/routes/inventory-management/spot-check/` (`sc-component.tsx`, `sc-form.tsx`, `sc-entry-component.tsx`, `sc-review-component.tsx`); `types/spot-check.ts`; `hooks/use-spot-check.ts`, `hooks/use-spot-check-current.ts`, `hooks/use-spot-check-comments.ts`.
- **E2E:** `../carmen-inventory-frontend-e2e/tests/` — no spot-check spec currently exists; a manual test-case catalog exists at `docs/test-cases/760-spot-check.md`.
- Related modules: [inventory](/en/inventory/inventory) (the ledger a spot check compares against but never writes to), [inventory-adjustment](/en/inventory/inventory-adjustment) (the module a user must go to separately to correct a confirmed variance — no automated link exists), [physical-count](/en/inventory/physical-count) (full-count counterpart, a completely separate three-level document tree).

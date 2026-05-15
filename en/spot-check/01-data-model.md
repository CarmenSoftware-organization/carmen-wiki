---
title: Spot Check — Data Model
description: Entities, fields, relationships, and enums for the spot-check module.
published: true
date: 2026-05-15T14:30:00.000Z
tags: spot-check, data-model, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T14:30:00.000Z
---

# Spot Check — Data Model

> **Source of truth:** Backend Prisma schema. Always read this first when writing or updating this page:
> - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma`
>
> The `generated/client/schema.prisma` file under the package is an auto-generated copy and not authoritative.

## 1. Overview

The Spot Check module is the **document layer** for a targeted, partial count of selected items or storage locations — the lighter-weight cousin of [[physical-count]] described in [[spot-check]] § 1. Unlike physical-count's three-level period / document / detail tree, spot-check persists a **flat two-level document tree** under `tb_spot_check` → `tb_spot_check_detail`: a single header carries the location, date window, `method` (random / high_value / manual), `size` (sample target), and `doc_status`; each detail row is one product line with `on_hand_qty` (book snapshot), `actual_qty` (counted), and `diff_qty` (variance). There is **no `tb_spot_check_period`** parent — spot checks are run ad-hoc, not bound to a fiscal-period header. Comments / attachments hang off both levels (`tb_spot_check_comment`, `tb_spot_check_detail_comment`).

The module sits **upstream of [[inventory-adjustment]]** in the same way physical-count does: when a spot check reaches `completed` and variance lines are accepted, the application layer rolls the variance into a `tb_stock_in` (overage) and / or `tb_stock_out` (shortage) document with reason codes (typically `SPOT_CHECK_OVERAGE` / `SPOT_CHECK_SHORTAGE` or aliased to the same `COUNT_OVERAGE` / `COUNT_SHORTAGE` reasons used by physical-count — to be confirmed). The adjustment post is what writes the `tb_inventory_transaction` row that lands on the [[inventory]] ledger. The spot-check tables themselves do **not** write to the inventory ledger directly — the adjustment document is the integration anchor.

> **TODO:** Confirm whether spot-check uses dedicated `SPOT_CHECK_*` reason codes or reuses physical-count's `COUNT_*` reasons. Source UI / interaction details from `../carmen-inventory-frontend/` and end-to-end behaviour from `../carmen-inventory-frontend-e2e/` once specs exist (no `spot-check` spec currently — verified by `ls .../tests/ | grep -i 'spot\|check'`). No carmen/docs source folder exists for this module — see [[physical-count/01-data-model]] for the shared infrastructure pattern.

## 2. Entities

The canonical Prisma schema defines four tables (verified against `prisma-shared-schema-tenant/prisma/schema.prisma` lines 3615–3765):

- **`tb_spot_check`** — the spot-check header. Carries `spot_check_no` (document number), `start_date` (default `now()`) / `end_date` (nullable), `location_id → tb_location` with snapshot `location_code` / `location_name`, `doc_status` on `enum_spot_check_status` (`pending`, `in_progress`, `void`, `completed`), `method` on `enum_spot_check_method` (`random` / `high_value` / `manual`), `size` (sample target count, default 10), `description`, `note`, and `info` / `dimension` JSON blobs. Unique within `(spot_check_no, deleted_at)`.
- **`tb_spot_check_comment`** — header-level comments / attachments. Carries `message`, `attachments` JSON array, and `enum_comment_type` (`user` / `system`).
- **`tb_spot_check_detail`** — the per-product spot-check line. Carries `product_id`, snapshot `product_code` / `product_name` / `product_local_name` / `product_sku`, `inventory_unit_id` (FK to `tb_unit`), `on_hand_qty` (book snapshot at check time, `Decimal(20,5)`), `actual_qty` (the entered physical count, nullable until counted), `diff_qty` (`actual_qty - on_hand_qty`, `Decimal(20,5)`), `counted_at` / `counted_by_id`, and `sequence_no` for sheet ordering. Unique within `(spot_check_id, product_id, dimension, deleted_at)`.
- **`tb_spot_check_detail_comment`** — line-level comments / attachments on a spot-check detail row.

Note: spot-check is structurally **simpler** than physical-count — no `tb_spot_check_period`, no progress counters (`product_counted` / `product_total`) on the header, no `physical_count_type` (frozen vs live) flag. The `method` enum (random / high_value / manual) replaces the period-and-zone scoping with a sample-selection strategy.

> **TODO:** Expand each entity into a full field table once the carmen/docs source (or alternative authoritative spec) is available; cross-reference with the [[physical-count/01-data-model]] and [[inventory-adjustment/01-data-model]] table-shape conventions for consistency.

## 3. Relationships

```
tb_location
    │
    └─1──*──► tb_spot_check  (doc_status: pending → in_progress → completed / void;
                │              method: random | high_value | manual; size: N)
                │
                ├─1──*──► tb_spot_check_comment
                │
                └─1──*──► tb_spot_check_detail
                            │   (on_hand_qty, actual_qty, diff_qty;
                            │    counted_at / counted_by_id;
                            │    no lot_no column at this level)
                            │
                            └─1──*──► tb_spot_check_detail_comment


At spot-check-completion, variance rollup writes to [[inventory-adjustment]]:
    ▼
tb_stock_in  (reason_code = SPOT_CHECK_OVERAGE  or COUNT_OVERAGE)   for diff_qty > 0
tb_stock_out (reason_code = SPOT_CHECK_SHORTAGE or COUNT_SHORTAGE)  for diff_qty < 0
    │
    └── tb_stock_in_detail / tb_stock_out_detail.info = { spotCheckId: <tb_spot_check.id> }
    │
    └── on adjustment post → tb_inventory_transaction with enum_transaction_type = adjustment_in / adjustment_out
```

Notes:

- **Two-level hierarchy** (vs physical-count's three-level). Spot check is ad-hoc, not period-bound — there is no `tb_spot_check_period`. A single `tb_spot_check` header is one (location, time-window) pairing; detail rows are one-per-product.
- **Variance rollup is application-layer, not Prisma-FK.** As with physical-count, there is no Prisma FK from `tb_stock_in.info.spotCheckId` back to `tb_spot_check.id` — the link is convention in JSON. The audit trail is reconstructed read-side.
- **All explicit `@relation` FK declarations use `onDelete: NoAction` (or `Cascade` for `inventory_unit_id`)** — preserving soft-delete (`deleted_at`) semantics.

## 4. Enums

- **`enum_spot_check_status`** — document-level lifecycle. Four values: `pending` (created, sheet generated, counter not yet started), `in_progress` (counter has begun entering quantities), `void` (cancelled before completion), `completed` (all in-scope lines counted and document submitted; variance rollup eligible). Compare physical-count's three-state enum — spot-check adds `void` for the lighter-weight cancellation path.
- **`enum_spot_check_method`** — sample-selection strategy on `tb_spot_check.method`. Three values: `random` (system picks `size` items at random — rotating coverage), `high_value` (top-N by value or velocity — risk-based), `manual` (Inventory Controller selects items directly — event-driven, e.g. after a suspected discrepancy or incident).
- **`enum_transaction_type`** — at the inventory ledger level (schema line ~1103). `spot-check` is **not** a direct value on this enum — variances post as `adjustment_in` / `adjustment_out` via the adjustment document, not as a distinct spot-check transaction type. Same pattern as physical-count.

> **TODO:** Confirm whether spot-check has its own dedicated costing-method enum (analogous to `enum_physical_count_costing_method`) or inherits from physical-count / adjustment defaults — none found in schema as of this writing.

## 5. Divergences from carmen/docs

> **TODO:** No carmen/docs source folder exists for the spot-check module — divergences cannot be authored from a carmen/docs baseline. Source comparison candidates: (a) `../carmen-inventory-frontend/` UI flow and form definitions, (b) `../carmen-inventory-frontend-e2e/` E2E test specs (none currently exist for spot-check — verified by `ls .../tests/ | grep -i 'spot\|check'`), (c) any future carmen/docs authoring of `SPC-*` interfaces. Until at least one of these is in place, treat the Prisma schema as sole source of truth.

## 6. References

- **Primary (source of truth):** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — four entities (`tb_spot_check`, `tb_spot_check_comment`, `tb_spot_check_detail`, `tb_spot_check_detail_comment`); two enums (`enum_spot_check_status`, `enum_spot_check_method`).
- **Secondary (TODO):** carmen/docs source — does not exist for this module.
- **Frontend (TODO):** `../carmen-inventory-frontend/` — no `spot-check` route currently visible at `app/` top level; locate under nested module folders when documenting UI flow.
- **E2E (TODO):** `../carmen-inventory-frontend-e2e/tests/` — no spot-check spec currently exists; document scenarios once added.
- Related modules: [[inventory]] (ledger that variance adjustments write to), [[inventory-adjustment]] (variance rollup posts as `tb_stock_in` / `tb_stock_out`), [[physical-count]] (full-count counterpart sharing the same rollup-to-adjustment integration pattern; see [[physical-count/01-data-model]] for the shared infrastructure), [[costing]] (variance valuation defaults inherited from adjustment-side costing).

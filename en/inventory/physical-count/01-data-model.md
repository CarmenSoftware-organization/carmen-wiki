---
title: Physical Count — Data Model
description: Entities, fields, relationships, and enums for the physical-count module.
published: true
date: 2026-06-17T08:00:00.000Z
tags: physical-count, data-model, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T14:00:00.000Z
---

# Physical Count — Data Model

> **At a Glance**
> **Tables:** `tb_physical_count_period` &nbsp;·&nbsp; `tb_physical_count` &nbsp;·&nbsp; `tb_physical_count_detail` &nbsp;·&nbsp; per-level `_comment` tables (three)
> **Audience:** Developer / Auditor (dev reference)
> **Key FKs:** period `→ tb_period`; count `→ tb_location` and `→ tb_physical_count_period`; detail `→ tb_product` and `→ tb_unit` (`inventory_unit_id`). Variance rollup link to [inventory-adjustment](/en/inventory/inventory-adjustment) is JSON-only (`tb_stock_in.info.countId` / `tb_stock_out.info.countId`) — no Prisma FK
> **Audit pattern:** standard `created_*` / `updated_*` / `deleted_*`; three-level hierarchy (period → document → detail) — count itself does **not** write to the inventory ledger; adjustment post is the integration anchor

> **Source of truth:** Backend Prisma schema. Always read this first when writing or updating this page:
> - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma`
>
> The `generated/client/schema.prisma` file under the package is an auto-generated copy and not authoritative.

## 1. Overview

The Physical Count module is the **document layer** for end-to-end counts of every item at a location — the scheduled, regulatory-baseline exercise described in [physical-count](/en/inventory/physical-count) § 1. The Prisma side persists a three-level document tree under the **`tb_physical_count_period` → `tb_physical_count` → `tb_physical_count_detail`** hierarchy: a period header groups every count document opened against the same fiscal period (`tb_period`), each count document represents one (period, location) pairing and carries the counting status / type / counters' progress, and each detail row is one product line on that count with `on_hand_qty` (book), `actual_qty` (counted), and `diff_qty` (variance). Comments and attachments hang off all three levels (`tb_physical_count_period_comment`, `tb_physical_count_comment`, `tb_physical_count_detail_comment`).

The module sits **upstream of [inventory-adjustment](/en/inventory/inventory-adjustment)**: when a count document reaches `completed` and variance lines are accepted, the application layer rolls the variance into a `tb_stock_in` (overage) and/or `tb_stock_out` (shortage) document with reason codes `COUNT_OVERAGE` / `COUNT_SHORTAGE`, whose own posting writes the `tb_inventory_transaction` row that lands on the [inventory](/en/inventory/inventory) ledger. The physical-count tables themselves do **not** write directly to the inventory ledger — the adjustment document is the integration anchor. Lot data on the count detail is sparse — `tb_physical_count_detail` carries only `on_hand_qty` / `actual_qty` per product at a location (no `lot_no` column); lot-level recounts are handled by the adjustment-side cost-layer pick at post time per [inventory](/en/inventory/inventory) `INV_CALC_005` / `INV_CALC_006`.

> **TODO:** Source UI / interaction details from `../carmen-inventory-frontend-react/` and end-to-end behaviour from `../carmen-inventory-frontend-e2e/` once specs exist. No carmen/docs source folder exists for this module — divergences (Section 5) cannot be authored until either docs are added or the field is confirmed source-of-truth-only.

## 2. Entities

The canonical Prisma schema defines six tables (verified against `prisma-shared-schema-tenant/prisma/schema.prisma` lines 5002–5152):

- **`tb_physical_count_period`** — the period-level header grouping all count documents for one fiscal period (`period_id → tb_period`). Carries `status` on `enum_physical_count_period_status` (`draft`, `counting`, `completed`).
- **`tb_physical_count_period_comment`** — period-level comments / attachments. Carries `message`, `attachments` JSON array, and `enum_comment_type` (`user` / `system`).
- **`tb_physical_count`** — the count document for one `(period, location)` pair. Carries `location_id → tb_location`, snapshot `location_code` / `location_name`, `physical_count_type` (`yes` / `no` — the frozen-vs-live flag, per `enum_physical_count_type`), `description`, `status` on `enum_physical_count_status` (`pending`, `in_progress`, `completed`), `start_counting_at` / `start_counting_by_id`, `completed_at` / `completed_by_id`, progress counters `product_counted` / `product_total`, and `doc_version` (`Int @db.Integer`, column nullable = No, default `0`) — optimistic-concurrency version counter incremented on each save/review/submit; the client must echo it on update or receive a `409 Conflict` (see [system-config/doc-version](/en/inventory/system-config/doc-version)). Unique within `(period, location, deleted_at)`.
- **`tb_physical_count_comment`** — document-level comments / attachments on a count.
- **`tb_physical_count_detail`** — the per-product count line. Carries `product_id`, snapshot `product_code` / `product_name` / `product_local_name` / `product_sku`, `inventory_unit_id` (FK to `tb_unit`), `on_hand_qty` (book snapshot at count time), `actual_qty` (the entered physical count), `diff_qty` (`actual_qty - on_hand_qty`), `counted_at` / `counted_by_id`, and `sequence_no` for sheet ordering.
- **`tb_physical_count_detail_comment`** — line-level comments / attachments on a count detail row.

> **TODO:** Expand each entity into a full field table once the carmen/docs source (or alternative authoritative spec) is available; cross-reference with the [inventory-adjustment/01-data-model](/en/inventory/inventory-adjustment/01-data-model) table-shape conventions for consistency.

## 3. Relationships

```
tb_period
    │
    └─1──*──► tb_physical_count_period  (status: draft → counting → completed)
                │
                ├─1──*──► tb_physical_count_period_comment
                │
                └─1──*──► tb_physical_count  (one row per (period, location);
                            │                  status: pending → in_progress → completed;
                            │                  physical_count_type ∈ {yes, no} — frozen vs live)
                            │
                            ├─1──*──► tb_physical_count_comment
                            │
                            └─1──*──► tb_physical_count_detail
                                        │   (on_hand_qty, actual_qty, diff_qty;
                                        │    counted_at / counted_by_id;
                                        │    no lot_no column at this level)
                                        │
                                        └─1──*──► tb_physical_count_detail_comment


At count-completion, variance rollup writes to [[inventory-adjustment]]:
    ▼
tb_stock_in  (reason_code = COUNT_OVERAGE)   for diff_qty > 0
tb_stock_out (reason_code = COUNT_SHORTAGE)  for diff_qty < 0
    │
    └── tb_stock_in_detail / tb_stock_out_detail.info = { countId: <tb_physical_count.id> }
    │
    └── on adjustment post → tb_inventory_transaction with enum_transaction_type = adjustment_in / adjustment_out
```

Notes:

- **Three-level hierarchy.** The period header groups multi-location counts; the count document is one-per-location; the detail is one-per-product. This mirrors how a physical count is run operationally: one period-end exercise, multiple locations counted in parallel, hundreds of product lines per location.
- **Variance rollup is application-layer, not Prisma-FK.** There is no Prisma FK from `tb_stock_in.info.countId` back to `tb_physical_count.id` — the link is convention in JSON. The audit trail is reconstructed read-side.
- **All explicit `@relation` FK declarations use `onDelete: NoAction` or `onDelete: Cascade`** — preserving soft-delete (`deleted_at`) semantics.

## 4. Enums

- **`enum_physical_count_period_status`** — period-level lifecycle. Three values: `draft` (period planning), `counting` (one or more documents under it are in progress), `completed` (all documents completed; period locked from new counts).
- **`enum_physical_count_status`** — document-level lifecycle. Three values: `pending` (created, sheet generated, counter not yet started), `in_progress` (counter has begun entering quantities), `completed` (all lines counted and document submitted; variance rollup eligible).
- **`enum_physical_count_type`** — frozen vs live mode flag on `tb_physical_count.physical_count_type`. Two values: `yes` (frozen — stock movements at the location blocked during the count window), `no` (live — movements continue, book snapshot is taken per line at count time). Defaults to `yes` per Prisma `@default(yes)`.
- **`enum_physical_count_costing_method`** — separate enum at the schema top (line 55) declaring four valuation methods used when posting the count-variance adjustment: `standard`, `last`, `average`, `last_receiving`. The chosen method drives the per-line cost on the rollup adjustment's `tb_stock_in_detail.cost_per_unit` / `tb_stock_out_detail.cost_per_unit`.
- **`enum_transaction_type`** — at the inventory ledger level (line 1103). `physical-count` is **not** a direct value on this enum — count variances post as `adjustment_in` / `adjustment_out` via the adjustment document, not as a distinct count transaction type.

## 5. Divergences from carmen/docs

> **TODO:** No carmen/docs source folder exists for the physical-count module — divergences cannot be authored from a carmen/docs baseline. Source comparison candidates: (a) `../carmen-inventory-frontend-react/` UI flow and form definitions, (b) `../carmen-inventory-frontend-e2e/` E2E test specs (none currently exist for physical-count — verified by `ls .../tests/ | grep -i 'physical\|count'`), (c) any future carmen/docs authoring of `PHC-*` interfaces. Until at least one of these is in place, treat the Prisma schema as sole source of truth.

## 6. References

- **Primary (source of truth):** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — six entities (`tb_physical_count_period`, `tb_physical_count_period_comment`, `tb_physical_count`, `tb_physical_count_comment`, `tb_physical_count_detail`, `tb_physical_count_detail_comment`); four enums (`enum_physical_count_period_status`, `enum_physical_count_status`, `enum_physical_count_type`, `enum_physical_count_costing_method`).
- **Secondary (TODO):** carmen/docs source — does not exist for this module.
- **Frontend (TODO):** `../carmen-inventory-frontend-react/` — no `physical-count` route currently visible at `app/` top level; locate under nested module folders when documenting UI flow.
- **E2E (TODO):** `../carmen-inventory-frontend-e2e/tests/` — no physical-count spec currently exists; document scenarios once added.
- Related modules: [inventory](/en/inventory/inventory) (ledger that count-variance adjustments write to), [inventory-adjustment](/en/inventory/inventory-adjustment) (variance rollup posts as `tb_stock_in` / `tb_stock_out`), [costing](/en/inventory/costing) (variance valuation via `enum_physical_count_costing_method`), [spot-check](/en/inventory/spot-check) (partial-count cousin using the same conceptual model).

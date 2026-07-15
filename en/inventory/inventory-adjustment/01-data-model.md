---
title: Inventory Adjustment — Data Model
description: Entities, fields, relationships, and enums for the inventory-adjustment module.
published: true
date: 2026-07-15T17:02:22.000Z
tags: inventory-adjustment, data-model, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T13:00:00.000Z
---

# Inventory Adjustment — Data Model

> **At a Glance**
> **Tables:** `tb_adjustment_type` (reason classifier) &nbsp;·&nbsp; `tb_stock_in` / `tb_stock_in_detail` (inbound) &nbsp;·&nbsp; `tb_stock_out` / `tb_stock_out_detail` (outbound) &nbsp;·&nbsp; per-level `_comment` tables
> **Audience:** Developer / Auditor (dev reference)
> **Key FKs:** `stock_in_detail.inventory_transaction_id` / `stock_out_detail.inventory_transaction_id → tb_inventory_transaction` (populated at post); detail `→ tb_product`; header `→ tb_location` / `tb_adjustment_type`. Variance rollup link from [physical-count](/en/inventory/physical-count) / [spot-check](/en/inventory/spot-check) is JSON-only (`info.countId`), no FK
> **Audit pattern:** standard `created_*` / `updated_*` / `deleted_*`; **two parallel document trees, no shared `tb_inventory_adjustment` parent** — direction gated by `tb_adjustment_type.type ∈ {stock_in, stock_out}`

> **Source of truth:** Backend Prisma schema. Always read these first when writing or updating this page:
> - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma`
> - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma`
>
> The `generated/client/schema.prisma` files under each package are auto-generated copies and not authoritative.

## 1. Overview

The Inventory Adjustment module is the **document layer** for manual stock-in / stock-out corrections — write-offs, write-ons, found stock, and expiry / damage / breakage adjustments that do not flow through a procurement (GRN) or consumption (Store Requisition) document. Unlike the other document-centric modules, the adjustment module **does not own a single `tb_inventory_adjustment` model** in the canonical Prisma schema: the persisted shape is **two parallel document trees** — `tb_stock_in` (inbound / write-on direction) and `tb_stock_out` (outbound / write-off direction) — joined by a shared classifier table `tb_adjustment_type` that carries a `code` / `name` (e.g. `FOUND_STOCK`, `BREAKAGE`) and is keyed by `enum_adjustment_type` (`stock_in` / `stock_out` / `eop_in` / `eop_out`).

Both `tb_stock_in` and `tb_stock_out` follow the standard document spine — header (`si_no` / `so_no`, `si_date` / `so_date`, location, adjustment-type, `doc_status`, workflow columns, comments) plus child detail rows (per product, with `qty`, `cost_per_unit`, `total_cost`, and the `inventory_transaction_id` back-reference to the [inventory](/en/inventory/inventory) ledger). The header `doc_status` column defaults to `draft` in the schema, but **`StockInService.create()` / `StockOutService.create()` always write `doc_status: enum_doc_status.completed` directly, in the same database transaction as the ledger write** — there is no code path in this module that ever produces a `draft`, `in_progress`, or `cancelled` row; those three enum values exist on the shared `enum_doc_status` but are not reachable through stock-in/stock-out creation. Posting therefore fires **at creation**, not on a later transition, and writes a `tb_inventory_transaction` row of `inventory_doc_type = stock_in` / `stock_out` with the detail's `inventory_transaction_id` stamped onto it. Lot data lives on the inventory transaction side (`current_lot_no` / `from_lot_no` on `tb_inventory_transaction_detail`, `lot_no` / `lot_index` on `tb_inventory_transaction_cost_layer`, both system-generated — `ADI-`/`ADO-` prefixes), **not** on the stock-in / stock-out detail row itself, and there is no lot-selection UI anywhere in this module's frontend.

The module sits **between the operations floor and the inventory ledger**. [physical-count](/en/inventory/physical-count)'s `submit()` method creates `tb_stock_in` (overage) / `tb_stock_out` (shortage) rows directly at `doc_status = completed`, with no `adjustment_type_id` set — this pass confirmed the row creation but did not trace whether that path also calls the ledger's `executeAdjustmentIn`/`executeAdjustmentOut` the way the manual stock-in/stock-out screens do; re-verify against `physical-count`'s own resync pass. Every stock-in/stock-out write calls the same shared `InventoryTransactionService` (`executeAdjustmentIn` / `executeAdjustmentOut`) that GRN, SR, and period-end also use, feeding [costing](/en/inventory/costing) for FIFO layer creation / weighted-average refresh. A repo-wide search for `journal`, `ledger`, and GL-posting code in this module's service files found no hits — there is no accounting/GL integration in this module.

## 2. Entities

### 2.1 tb_adjustment_type

The **reason-code classifier** for both `tb_stock_in` and `tb_stock_out` documents. A reason-code row carries a `code` (e.g. `BREAKAGE`, `FOUND_STOCK`), a human-readable `name`, the constrained direction via `enum_adjustment_type` (four values — see Section 4), and a free-text `description`. Reason codes are maintained on a separate master-data screen (`/config/adjustment-type`, [master-data/adjustment-type](/en/inventory/master-data/adjustment-type)) and, at adjustment-document creation time, only drive reason-list filtering by direction on the frontend (`ADJUSTMENT_TYPE.STOCK_IN` / `STOCK_OUT` in `types/adjustment-type.ts`). No GL-account field, document-required flag, or quality-check flag exists on this table or is read anywhere in the backend — `info` and `dimension` are present in the schema but no code in this module reads or writes recognised keys on either.

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `doc_version` | `Int @db.Integer` | No | Optimistic-concurrency counter; default `0`. |
| `id` | `String @db.Uuid` | No | Primary key; `gen_random_uuid()`. |
| `code` | `String @db.VarChar` | No | Reason-code mnemonic, e.g. `BREAKAGE`, `FOUND_STOCK`. Unique within `deleted_at`. |
| `name` | `String @db.VarChar` | No | Display name for picker UI. |
| `type` | `enum_adjustment_type` | No | Direction classifier: `stock_in` or `stock_out` for user-raised adjustments (filters the reason list shown on the corresponding document, client-side only — see § 5 item 2); `eop_in` / `eop_out` are period-end-reserved values not offered by this module's reason picker. See Section 4 for the full enum. |
| `description` | `String @db.VarChar` | Yes | Free-text explanation. |
| `is_active` | `Boolean` | Yes | Default `true`. Inactive reasons are hidden from new-document pickers but remain readable on historical documents. |
| `note` | `String @db.VarChar` | Yes | Free-text note. |
| `info` | `Json @db.JsonB` | Yes | Extension bag; default `{}`. No recognised keys found read or written anywhere in this module's frontend or backend. |
| `dimension` | `Json @db.JsonB` | Yes | Cost-dimension array; default `[]`. No recognised keys found used. |
| `created_at` | `DateTime @db.Timestamptz(6)` | Yes | Creation timestamp; defaults to `now()`. |
| `created_by_id` | `String @db.Uuid` | Yes | Creator id. |
| `updated_at` | `DateTime @db.Timestamptz(6)` | Yes | Last-update timestamp. |
| `updated_by_id` | `String @db.Uuid` | Yes | Updater id. |
| `deleted_at` | `DateTime @db.Timestamptz(6)` | Yes | Soft-delete timestamp; non-null hides the row from new-document pickers. |
| `deleted_by_id` | `String @db.Uuid` | Yes | Soft-delete actor id. |

**Constraints:** `@id` on `id`. Back-relations: many `tb_stock_in`, many `tb_stock_out`.
**Indexes:** `@@unique([code, deleted_at])` as `AT1_code_u`; `@@index([code])` as `AT1_code_idx`.

### 2.2 tb_stock_in

The **inbound adjustment document header**. One row per stock-in event, carrying the document number (`si_no`), document date (`si_date`), location (the destination of the inbound), the chosen `adjustment_type`, the `doc_status` column, a set of workflow columns, and the standard audit-trail columns. Comments hang off `tb_stock_in_comment`; per-product detail rows hang off `tb_stock_in_detail`. **The `workflow_*` and `user_action` columns exist on this table but `stock-in.service.ts` never sets or reads them** — this module has no workflow orchestrator call anywhere in its create/update/void code, so these columns are dead scaffolding shared with the workflow-driven modules (GRN, PO, SR) rather than an active feature here.

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `si_date` | `DateTime @db.Timestamptz(6)` | Yes | Document date. Validated client-side against the current period's window (Zod, in `ia-form-schema.ts`); no equivalent check was found in `StockInService.create()`/`update()`. |
| `si_no` | `String @db.VarChar` | Yes | Human-readable stock-in number; unique within `deleted_at`. Generated via the running-code service (`STOCK-IN` pattern). |
| `description` | `String @db.VarChar` | Yes | Header-level free-text description; optional (max 256 chars client-side), not required. |
| `adjustment_type_id` | `String @db.Uuid` | Yes | FK to `tb_adjustment_type.id` (`onDelete: NoAction`). The reason picker filters to `type = stock_in` rows client-side; the backend only checks the referenced row exists, not its `type`. |
| `adjustment_type_code` | `String @db.VarChar` | Yes | Snapshot of the chosen reason code. |
| `doc_status` | `enum_doc_status` | No | Schema default `draft`; **`StockInService.create()` always writes `completed` directly** — `in_progress` and `cancelled` are never assigned by this module's code. `voided` is reachable only via the void endpoint (see [02 — Business Rules](/en/inventory/inventory-adjustment/02-business-rules) § 5). |
| `location_id` | `String @db.Uuid` | Yes | FK to `tb_location.id` — destination location for the inbound. |
| `location_code` | `String @db.VarChar` | Yes | Snapshot of the location code. |
| `location_name` | `String @db.VarChar` | Yes | Snapshot of the location name. |
| `workflow_id` | `String @db.Uuid` | Yes | Unused by this module (see note above). |
| `workflow_name` | `String @db.VarChar` | Yes | Unused by this module. |
| `workflow_history` | `Json @db.JsonB` | Yes | Unused by this module; default `{}`. |
| `workflow_current_stage` | `String @db.VarChar` | Yes | Unused by this module. |
| `workflow_previous_stage` | `String @db.VarChar` | Yes | Unused by this module. |
| `workflow_next_stage` | `String @db.VarChar` | Yes | Unused by this module. |
| `user_action` | `Json @db.JsonB` | Yes | Unused by this module; default `{}`. |
| `last_action` | `enum_last_action` | Yes | Schema default `submitted`; not observed to be transitioned by this module's service. |
| `last_action_at_date` | `DateTime @db.Timestamptz(6)` | Yes | Not observed to be set by this module's service. |
| `last_action_by_id` | `String @db.Uuid` | Yes | Not observed to be set by this module's service. |
| `last_action_by_name` | `String @db.VarChar` | Yes | Not observed to be set by this module's service. |
| `note` | `String @db.VarChar` | Yes | Free-text note. |
| `info` | `Json @db.JsonB` | Yes | Extension bag; default `{}`. `create()` passes the client-supplied value through unmodified (`info: item.info || null`); no recognised keys are interpreted by this module's backend. |
| `dimension` | `Json @db.JsonB` | Yes | Cost-dimension array; default `[]`. Passed through unmodified; no recognised keys interpreted. |
| `doc_version` | `Int @db.Integer` | No | Optimistic-concurrency counter; default `0`. Checked on the update `where` clause. |
| `created_at` | `DateTime @db.Timestamptz(6)` | Yes | Creation timestamp. |
| `created_by_id` | `String @db.Uuid` | Yes | Creator id. |
| `updated_at` | `DateTime @db.Timestamptz(6)` | Yes | Last-update timestamp. |
| `updated_by_id` | `String @db.Uuid` | Yes | Updater id. |
| `deleted_at` | `DateTime @db.Timestamptz(6)` | Yes | Soft-delete timestamp. **`voidStockIn()` sets this alongside `doc_status = voided`** in the same update call — voiding a document also soft-deletes it, so a voided document drops out of every query that filters `deleted_at: null`, including the list and detail endpoints (both filter on it). A voided Stock-In is not just badge-flagged; it becomes unfetchable through the normal API once voided. |
| `deleted_by_id` | `String @db.Uuid` | Yes | Soft-delete actor id. |

**Constraints:** `@id` on `id`. FKs: `adjustment_type_id → tb_adjustment_type.id` (`NoAction`); `location_id → tb_location.id` (`NoAction`). Back-relations: many `tb_stock_in_detail`, many `tb_stock_in_comment`.
**Indexes:** `@@unique([si_no, deleted_at])` as `SI1_si_no_u`; `@@index([si_no])` as `SI0_si_no_idx`.

### 2.3 tb_stock_in_detail

The **per-product detail line on a stock-in document**. One row per affected product line; carries `qty` (positive for inbound), `cost_per_unit`, `total_cost`, and the back-reference `inventory_transaction_id` that links to the [inventory](/en/inventory/inventory) ledger row. Because creation always posts (§ 1), `inventory_transaction_id` is populated on every real row — there is no draft-then-post window in which it stays null. `cost_per_unit` is user-entered on this screen (pre-filled from the current location average as a starting suggestion) and is what the ledger actually uses to build the new cost layer. Comments and attachments per detail line hang off `tb_stock_in_detail_comment`.

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `inventory_transaction_id` | `String @db.Uuid` | Yes | FK to `tb_inventory_transaction.id` — stamped in the same transaction as document creation. |
| `stock_in_id` | `String @db.Uuid` | No | FK to `tb_stock_in.id`. |
| `sequence_no` | `Int` | Yes | Line ordering within the document; default `1`. |
| `description` | `String @db.VarChar` | Yes | Free-text description for the line. |
| `comment` | `String @db.VarChar` | Yes | Free-text comment for the line. |
| `product_id` | `String @db.Uuid` | No | FK to `tb_product.id`. Required; must resolve to an existing `tb_product` row or `create()` rejects with `"Product not found: <ids>"`. |
| `product_code` | `String @db.VarChar` | Yes | Snapshot of the product code. |
| `product_name` | `String @db.VarChar` | Yes | Snapshot of the product name. |
| `product_local_name` | `String @db.VarChar` | Yes | Localised snapshot. |
| `product_sku` | `String @db.VarChar` | Yes | SKU snapshot. |
| `qty` | `Decimal @db.Decimal(20, 5)` | Yes | Inbound quantity in base UoM. Client-side Zod requires `qty >= 1` (not just `> 0` — a fractional quantity below 1 is rejected by the form); default `0`. |
| `cost_per_unit` | `Decimal @db.Decimal(20, 5)` | Yes | Unit cost in base currency, user-entered on the Stock-In line (pre-filled with the current location average as a suggestion, editable); default `0`. Passed straight through to `executeAdjustmentIn` as the new layer's cost. |
| `total_cost` | `Decimal @db.Decimal(20, 5)` | Yes | `qty × cost_per_unit`, computed client-side; default `0`. |
| `note` | `String @db.VarChar` | Yes | Free-text note. |
| `info` | `Json @db.JsonB` | Yes | Extension bag; default `{}`. Passed through unmodified by `create()`; no recognised keys interpreted (no lot/expiry fields — this module has no lot-entry UI). |
| `dimension` | `Json @db.JsonB` | Yes | Cost-dimension array; default `[]`. Passed through unmodified. |
| `doc_version` | `Int @db.Integer` | No | Optimistic-concurrency counter; default `0`. |
| `created_at` | `DateTime @db.Timestamptz(6)` | Yes | Creation timestamp. |
| `created_by_id` | `String @db.Uuid` | Yes | Creator id. |
| `updated_at` | `DateTime @db.Timestamptz(6)` | Yes | Last-update timestamp. |
| `updated_by_id` | `String @db.Uuid` | Yes | Updater id. |
| `deleted_at` | `DateTime @db.Timestamptz(6)` | Yes | Soft-delete timestamp. |
| `deleted_by_id` | `String @db.Uuid` | Yes | Soft-delete actor id. |

**Constraints:** `@id` on `id`. FKs: `inventory_transaction_id → tb_inventory_transaction.id` (`NoAction`); `product_id → tb_product.id` (`NoAction`); `stock_in_id → tb_stock_in.id` (`NoAction`). Back-relations: many `tb_stock_in_detail_comment`.
**Indexes:** `@@unique([stock_in_id, product_id, dimension, deleted_at])` as `SIT1_stock_in_product_dimension_u`; `@@index([stock_in_id, product_id])` as `SIT2_stock_in_product_idx`; `@@index([stock_in_id])` as `SIT2_stock_in_idx`.

Comment / attachment tables for this module are documented separately — see [01a — Data Model — Comment Tables](/en/inventory/inventory-adjustment/01a-data-model-comments).

### 2.4 tb_stock_out

The **outbound adjustment document header**. Mirror-image of `tb_stock_in` with `so_no` / `so_date`. Identical (and identically unused — see § 2.2) workflow / status / audit fields; same comment / detail / detail-comment children.

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `so_date` | `DateTime @db.Timestamptz(6)` | Yes | Document date. |
| `so_no` | `String @db.VarChar` | Yes | Human-readable stock-out number; unique within `deleted_at`. Generated via the running-code service (`STOCK-OUT` pattern). |
| `description` | `String @db.VarChar` | Yes | Header-level description; optional. |
| `adjustment_type_id` | `String @db.Uuid` | Yes | FK to `tb_adjustment_type.id` (`onDelete: NoAction`). Reason picker filters to `type = stock_out` client-side only. |
| `adjustment_type_code` | `String @db.VarChar` | Yes | Snapshot. |
| `doc_status` | `enum_doc_status` | No | Schema default `draft`; `StockOutService.create()` always writes `completed` directly — same headline finding as `tb_stock_in` (§ 2.2). |
| `location_id` | `String @db.Uuid` | Yes | FK to `tb_location.id` — source location for the outbound. |
| `location_code` | `String @db.VarChar` | Yes | Snapshot. |
| `location_name` | `String @db.VarChar` | Yes | Snapshot. |
| `workflow_id` | `String @db.Uuid` | Yes | Unused by this module. |
| `workflow_name` | `String @db.VarChar` | Yes | Unused by this module. |
| `workflow_history` | `Json @db.JsonB` | Yes | Unused by this module; default `{}`. |
| `workflow_current_stage` | `String @db.VarChar` | Yes | Unused by this module. |
| `workflow_previous_stage` | `String @db.VarChar` | Yes | Unused by this module. |
| `workflow_next_stage` | `String @db.VarChar` | Yes | Unused by this module. |
| `user_action` | `Json @db.JsonB` | Yes | Unused by this module; default `{}`. |
| `last_action` | `enum_last_action` | Yes | Schema default `submitted`; not observed to be transitioned by this module. |
| `last_action_at_date` | `DateTime @db.Timestamptz(6)` | Yes | Not observed to be set by this module. |
| `last_action_by_id` | `String @db.Uuid` | Yes | Not observed to be set by this module. |
| `last_action_by_name` | `String @db.VarChar` | Yes | Not observed to be set by this module. |
| `note` | `String @db.VarChar` | Yes | Free-text. |
| `info` | `Json @db.JsonB` | Yes | Extension bag; passed through unmodified, no recognised keys. |
| `dimension` | `Json @db.JsonB` | Yes | Cost-dimension array; passed through unmodified. |
| `doc_version` | `Int @db.Integer` | No | Default `0`. |
| `created_at` | `DateTime @db.Timestamptz(6)` | Yes | Creation timestamp. |
| `created_by_id` | `String @db.Uuid` | Yes | Creator id. |
| `updated_at` | `DateTime @db.Timestamptz(6)` | Yes | Last-update timestamp. |
| `updated_by_id` | `String @db.Uuid` | Yes | Updater id. |
| `deleted_at` | `DateTime @db.Timestamptz(6)` | Yes | Soft-delete timestamp. |
| `deleted_by_id` | `String @db.Uuid` | Yes | Soft-delete actor id. |

**Constraints:** `@id` on `id`. FKs: `adjustment_type_id → tb_adjustment_type.id` (`NoAction`); `location_id → tb_location.id` (`NoAction`). Back-relations: many `tb_stock_out_detail`, many `tb_stock_out_comment`.
**Indexes:** `@@unique([so_no, deleted_at])` as `SO1_so_no_u`; `@@index([so_no])` as `SO0_so_no_idx`.

### 2.5 tb_stock_out_detail

The **per-product detail line on a stock-out document**. Similar shape to `tb_stock_in_detail`, but `cost_per_unit`/`total_cost` are **never written by `create()`** — the insert only sets `product_id`, `qty`, `description`, `note`, `info`, `dimension`; both cost columns stay at their schema default of `0` for every stock-out detail row. The line-item grid hides the `cost_per_unit` column entirely for Stock-Out (`ia-item-table.tsx` filters it out of the visible columns). The real cost is resolved automatically at write time by the ledger — FIFO consumes the oldest layers first, Average uses the current BU-wide average — and lives only on `tb_inventory_transaction_detail`/`tb_inventory_transaction_cost_layer`, not on this table.

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `inventory_transaction_id` | `String @db.Uuid` | Yes | FK to `tb_inventory_transaction.id`; stamped at creation. |
| `stock_out_id` | `String @db.Uuid` | No | FK to `tb_stock_out.id`. |
| `sequence_no` | `Int` | Yes | Line ordering; default `1`. |
| `description` | `String @db.VarChar` | Yes | Free-text. |
| `comment` | `String @db.VarChar` | Yes | Free-text. |
| `product_id` | `String @db.Uuid` | No | FK to `tb_product.id`. |
| `product_code` | `String @db.VarChar` | Yes | Snapshot. |
| `product_name` | `String @db.VarChar` | Yes | Snapshot. |
| `product_local_name` | `String @db.VarChar` | Yes | Localised snapshot. |
| `product_sku` | `String @db.VarChar` | Yes | SKU snapshot. |
| `qty` | `Decimal @db.Decimal(20, 5)` | Yes | Outbound quantity, entered positive on the form; default `0`. Client-side Zod requires `qty >= 1`. |
| `cost_per_unit` | `Decimal @db.Decimal(20, 5)` | Yes | **Always `0`** on this table — `create()` never sets it for stock-out (see note above). |
| `total_cost` | `Decimal @db.Decimal(20, 5)` | Yes | **Always `0`** on this table for the same reason; the frontend computes a preview client-side (`useProductLastReceiving`) but it is never persisted here. |
| `note` | `String @db.VarChar` | Yes | Free-text. |
| `info` | `Json @db.JsonB` | Yes | Extension bag; default `{}`. Passed through unmodified; no recognised keys (no lot-override field — this module has no lot UI). |
| `dimension` | `Json @db.JsonB` | Yes | Cost-dimension array; default `[]`. Passed through unmodified. |
| `doc_version` | `Int @db.Integer` | No | Default `0`. |
| `created_at` | `DateTime @db.Timestamptz(6)` | Yes | Creation timestamp. |
| `created_by_id` | `String @db.Uuid` | Yes | Creator id. |
| `updated_at` | `DateTime @db.Timestamptz(6)` | Yes | Last-update timestamp. |
| `updated_by_id` | `String @db.Uuid` | Yes | Updater id. |
| `deleted_at` | `DateTime @db.Timestamptz(6)` | Yes | Soft-delete timestamp. |
| `deleted_by_id` | `String @db.Uuid` | Yes | Soft-delete actor id. |

**Constraints:** `@id` on `id`. FKs: `inventory_transaction_id → tb_inventory_transaction.id` (`NoAction`); `product_id → tb_product.id` (`NoAction`); `stock_out_id → tb_stock_out.id` (`NoAction`). Back-relations: many `tb_stock_out_detail_comment`.
**Indexes:** `@@unique([stock_out_id, product_id, dimension, deleted_at])` as `SOT1_stock_out_product_dimension_u`; `@@index([stock_out_id, product_id])` as `SOT2_stock_out_product_idx`; `@@index([stock_out_id])` as `SOT2_stock_out_idx`.

## 3. Relationships

```
tb_adjustment_type  (reason-code master — stock_in or stock_out direction, client-filtered only)
    │  enum_adjustment_type ∈ {stock_in, stock_out, eop_in, eop_out}
    │
    ├─1──*──► tb_stock_in   (inbound adjustment document — doc_status always "completed" at creation)
    │           │
    │           ├─1──*──► tb_stock_in_detail   (per-product line, cost_per_unit user-entered)
    │           │           │
    │           │           ├──► tb_inventory_transaction (inventory_transaction_id, stamped at creation)
    │           │           ├──► tb_product
    │           │           └─1──*──► tb_stock_in_detail_comment
    │           │
    │           ├─1──*──► tb_stock_in_comment (header comments)
    │           └──► tb_location  (location_id — destination of inbound)
    │
    └─1──*──► tb_stock_out  (outbound adjustment document — doc_status always "completed" at creation)
                │
                ├─1──*──► tb_stock_out_detail   (per-product line, cost_per_unit/total_cost always 0)
                │           │
                │           ├──► tb_inventory_transaction (inventory_transaction_id, stamped at creation)
                │           ├──► tb_product
                │           └─1──*──► tb_stock_out_detail_comment
                │
                ├─1──*──► tb_stock_out_comment
                └──► tb_location  (location_id — source of outbound)


create() writes the header at doc_status = completed AND writes the ledger
row in the same DB transaction — there is no separate posting step:
    ▼
tb_inventory_transaction  (header: inventory_doc_type ∈ {stock_in, stock_out},
                                   inventory_doc_no = tb_stock_in.id / tb_stock_out.id)
    │
    └─1──*──► tb_inventory_transaction_detail  (qty signed by direction,
                                                  cost_per_unit, total_cost,
                                                  from_lot_no / current_lot_no)
                │
                └─1──*──► tb_inventory_transaction_cost_layer
                            (enum_transaction_type ∈ {adjustment_in, adjustment_out},
                             lot_no, lot_seq_no, in_qty / out_qty,
                             cost_per_unit, average_cost_per_unit)
```

Notes:

- **Two parallel document trees, one classifier.** `tb_stock_in` and `tb_stock_out` are independent Prisma models with the same shape; the `tb_adjustment_type` row's `type` column is used by the frontend to filter which reasons appear on which document's picker, but the backend's header validation only checks that the referenced `tb_adjustment_type` row exists — it does not re-check `type` matches the document's direction, so this is a client-side-only constraint.
- **Inventory-transaction back-reference is populated at creation, not at a later "post" step.** Each detail row carries `inventory_transaction_id` as a nullable FK, but because `create()` always writes the ledger row in the same transaction as the document, every real row has it populated — there is no draft window in which it stays null. This differs from [good-receive-note](/en/inventory/good-receive-note), where `save()` (not `commit()`) is the analogous single mutation-and-post event but at least happens on a distinct action from creation.
- **No lot data anywhere in this module's UI.** Lot identity (`current_lot_no` / `from_lot_no` on `tb_inventory_transaction_detail`, `lot_no` / `lot_index` on `tb_inventory_transaction_cost_layer`) is generated mechanically by the ledger (`ADI-`/`ADO-` prefixes) — there is no lot-picker, lot-entry field, or expiry-date field anywhere in `ia-item-fields.tsx` / `ia-item-table.tsx` / `ia-form-schema.ts`.
- **`adjustment_type_code` is a snapshot, not a live join.** Both documents persist the snapshot code on the header for performance and audit; deleting / renaming the reason code after posting does not retroactively change the historical document.
- **All explicit `@relation` FK declarations use `onDelete: NoAction, onUpdate: NoAction`** — referential integrity is preserved by application-level soft-delete (`deleted_at`), not by cascade.

## 4. Enums

- **`enum_adjustment_type`**: direction classifier on `tb_adjustment_type.type`. Four values, no default declared:
  - `stock_in` — filters into the Stock-In reason picker.
  - `stock_out` — filters into the Stock-Out reason picker.
  - `eop_in` / `eop_out` — used by the period-end engine (surfaced via the merged `inventory-adjustments` gateway list, tagged by the `wantIn`/`wantOut` filter in `inventory-adjustments.service.ts`); not offered by either creation screen's reason picker.
- **`enum_doc_status`**: document lifecycle column on `tb_stock_in.doc_status` / `tb_stock_out.doc_status`. Schema default `draft`. Five values exist on the shared enum, but only two are ever assigned by this module's own code:
  - `draft` — schema default only; never assigned by `create()`.
  - `in_progress` — never assigned anywhere in this module's code.
  - `completed` — the value every `create()` call writes, unconditionally, regardless of the client-sent `doc_status`.
  - `cancelled` — never assigned anywhere in this module's code.
  - `voided` — assigned only by the void endpoint (`voidStockIn` / `voidStockOut`), which also sets `deleted_at` in the same update (see § 2.2 note) — but the UI's Void button is unreachable for any persisted document (see the module landing page § 1), so this transition currently requires a direct API call.
- **`enum_last_action`**: column exists (`submitted`, `approved`, `reviewed`, `rejected`, default `submitted`) but is not observed to be read or written by `stock-in.service.ts` / `stock-out.service.ts`.
- **`enum_comment_type`**: on `tb_stock_in_comment.type` / `tb_stock_in_detail_comment.type` / `tb_stock_out_comment.type` / `tb_stock_out_detail_comment.type`. Default `user`. Two values: `user`, `system`.

## 5. Notes on carmen/docs

`../carmen/docs/inventory-adjustment/` describes a design centred on a single `InventoryAdjustment` entity with an embedded `items[]`/`lots[]` array, GL journal-entry postings, and a threshold-gated multi-role approval chain (Store Keeper → Inventory Controller → Finance). None of that matches the current implementation:

| # | carmen/docs framing | What the code actually does |
|---|------|------|
| 1 | Single `InventoryAdjustment` entity with a `type: 'IN' \| 'OUT'` discriminator. | Two independent tables, `tb_stock_in` and `tb_stock_out`, with no shared parent — confirmed accurate framing to keep, see § 3. |
| 2 | `AdjustmentReason` interface with `type: 'IN' \| 'OUT' \| 'BOTH'`, `requiresDocument`, `requiresQualityCheck`, `glAccount` fields. | `tb_adjustment_type` has only `code`, `name`, `type` (`enum_adjustment_type`, no `BOTH` value), `description`, `is_active`, `note`. No `glAccount`/`requiresDocument`/`requiresQualityCheck` field exists, and no code anywhere in the frontend or backend reads or writes those key names inside `info`/`dimension` JSON — this is not a JSON-vs-column distinction, the concept itself is absent. |
| 3 | Three-state `Draft → Posted → Void` lifecycle with threshold-based approval routing to Inventory Controller / Finance. | There is no approval stage at all: `create()` always writes `completed` directly, regardless of cost or any threshold — a repo-wide search found zero `threshold` hits in this module's backend code. See § 4. |
| 4 | Embedded `journalEntries: JournalEntry[]`. | No GL/journal code exists anywhere in this module (or, per the module map's earlier passes, anywhere in the backend for GRN/PO/SR either). Adjustments are a pure quantity/value ledger movement. |
| 5 | Reference number implied to be the record `id`. | The human-readable reference is `si_no` / `so_no`, generated via the running-code service; `id` is the UUID primary key. |
| 6 | "Supporting documents must be attached" for certain reasons. | Comments (`tb_stock_in_comment`/`tb_stock_out_comment`, with an `attachments` JSON array) are real and freely usable, but no validation rule ties any reason code to a required attachment — the concept of a reason flagging "requires document" does not exist in the schema or the code. |

## 6. References

- **Primary (source of truth):** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` (`tb_adjustment_type`, `tb_stock_in`, `tb_stock_in_detail`, `tb_stock_in_comment`, `tb_stock_in_detail_comment`, `tb_stock_out`, `tb_stock_out_detail`, `tb_stock_out_comment`, `tb_stock_out_detail_comment`; enums `enum_adjustment_type`, `enum_doc_status`, `enum_last_action`, `enum_comment_type`).
- **Backend services:** `apps/micro-business/src/inventory/stock-in/stock-in.service.ts`, `.../stock-out/stock-out.service.ts`, `.../inventory-transaction/inventory-transaction.service.ts` (`executeAdjustmentIn`/`executeAdjustmentOut`), `apps/backend-gateway/src/application/inventory-adjustments/inventory-adjustments.service.ts` (read-only gateway merge of stock-in + stock-out for the list view and print viewer).
- **Frontend:** `../carmen-inventory-frontend-react/routes/inventory-management/inventory-adjustment/` (`ia-form.tsx`, `ia-form-schema.ts`, `ia-item-fields.tsx`, `ia-item-table.tsx`).
- **Secondary (concept cross-check, superseded by the code — see § 5):** `../carmen/docs/inventory-adjustment/INV-ADJ-Overview.md`, `INV-ADJ-PRD.md`, `INV-ADJ-Business-Requirements.md`, `INV-ADJ-Business-Logic.md`, `INV-ADJ-Component-Structure.md`.
- E2E: no dedicated `inventory-adjustment` spec exists; `../carmen-inventory-frontend-e2e/tests/031-adjustment-type.spec.ts` covers only the reason-code master-data screen.
- Related modules: [inventory](/en/inventory/inventory) (shared ledger — `tb_inventory_transaction` / `tb_inventory_transaction_detail` / `tb_inventory_transaction_cost_layer`), [costing](/en/inventory/costing) (FIFO layer creation on Stock-In, FIFO consumption / weighted-average recompute on Stock-Out), [physical-count](/en/inventory/physical-count) (creates `tb_stock_in`/`tb_stock_out` rows directly on variance commit — see the module landing page § 2), [product](/en/inventory/product).

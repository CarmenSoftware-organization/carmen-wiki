---
title: Inventory — Data Model
description: Entities, fields, relationships, and enums for the inventory module.
published: true
date: 2026-05-20T02:00:00.000Z
tags: inventory, data-model, carmen-software
editor: markdown
dateCreated: 2026-05-15T12:00:00.000Z
---

# Inventory — Data Model

> **At a Glance**
> **Tables:** `tb_inventory_transaction` &nbsp;·&nbsp; `tb_inventory_transaction_detail` &nbsp;·&nbsp; `tb_inventory_transaction_cost_layer` &nbsp;·&nbsp; `tb_location` &nbsp;·&nbsp; `tb_product_location` &nbsp;·&nbsp; `tb_period` &nbsp;·&nbsp; `tb_period_snapshot`
> **Audience:** Developer / Auditor (dev reference)
> **Key FKs:** `inventory_doc_no` is **polymorphic** (no `@relation`) — resolves to `tb_good_received_note` / `tb_store_requisition` / `tb_stock_in` / `tb_stock_out` / `tb_credit_note` / `tb_period` by `inventory_doc_type`; cost-layer `→ tb_period`; source-side modules reach back via UUID `inventory_transaction_id` columns
> **Audit pattern:** standard `created_*` / `updated_*` / `deleted_*` on most tables; **`tb_inventory_transaction_detail` has no soft-delete** — reversal posts a compensating row. No `tb_stock_balance` — on-hand is derived from cost-layer rows since the latest snapshot

> **Source of truth:** Backend Prisma schema. Always read these first when writing or updating this page:
> - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma`
> - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma`
>
> The `generated/client/schema.prisma` files under each package are auto-generated copies and not authoritative.

## 1. Overview

The Inventory module is the **system of record for stock movement and on-hand valuation** across the property. Unlike the document-centric modules ([purchase-request](/en/inventory/purchase-request), [purchase-order](/en/inventory/purchase-order), [good-receive-note](/en/inventory/good-receive-note)), inventory does not live on a single header → detail → comment tree. It is a **family of records linked by movement** — every quantity change in the system flows through `tb_inventory_transaction` (the movement header) and its child `tb_inventory_transaction_detail` (per-product / per-lot ledger lines), with the canonical cost-flow record persisted on `tb_inventory_transaction_cost_layer` (FIFO / weighted-average layers, keyed by `lot_no` and `lot_index`). Locations are configured on `tb_location` with a `location_type` (`inventory`, `direct`, or `consignment`) that determines whether a movement posts to the inventory asset, expense, or memo register. Per-product / per-location stock parameters (par, min, max, reorder) live on `tb_product_location`. Period boundaries are anchored by `tb_period` (the accounting period) and `tb_period_snapshot` (the locked opening / closing balance row per `period × location × product × lot`); the period status enum (`open` → `closed` → `locked`) gates backdated postings.

The module sits **at the centre of the procure-to-pay / requisition-to-consume chain**. It is downstream of [good-receive-note](/en/inventory/good-receive-note) (receipts post `enum_inventory_doc_type = good_received_note` transactions), [store-requisition](/en/inventory/store-requisition) (issues post `store_requisition` transactions), [physical-count](/en/inventory/physical-count) and [spot-check](/en/inventory/spot-check) (counts post adjustment_in / adjustment_out transactions), and [inventory-adjustment](/en/inventory/inventory-adjustment) (manual stock-in / stock-out transactions). It is upstream of [costing](/en/inventory/costing), which reads the cost-layer ledger to compute COGS and unit-cost feeds back into the source modules. The single-table-as-ledger design is deliberate: every owned-stock movement, regardless of source module, lands in `tb_inventory_transaction` so that a single forward-and-backward trace (movement → cost layer → period snapshot → on-hand) underpins both audit and recall.

A noteworthy structural point: **there is no `tb_stock_balance` model in the canonical Prisma schema**. On-hand balance is derived — at any point in time, the current balance for `(location_id, product_id, lot_no)` is the algebraic sum of all non-soft-deleted `tb_inventory_transaction_cost_layer.in_qty` minus `out_qty` for that lot since the last period snapshot's `closing_qty`. The period snapshot's `closing_qty` is the locked anchor; movements after the snapshot are deltas against it. The `inventory-management-prd.md` and several derivative docs reference an `InventoryStatus` / `StockBalance` entity with `QuantityOnHand`, `LastUnitCost`, `TotalCost` columns — that interface is application-layer-derived, not a schema row. See Section 5 for this divergence.

A second structural point: **GL postings produced by inventory movements land in the `tb_jv_header` / `tb_jv_detail` pair** (tenant schema, status enum `enum_jv_status = { draft, posted }`). The JV header carries `jv_no`, `jv_date`, `jv_type`, `currency_id` / `exchange_rate` / `base_currency_id`, and the detail row carries per-account `debit` / `credit` lines tied to the inventory transaction it summarises. JV is the bridge consumed by the finance / GL module; corrective entries that the inventory wiki refers to as "raise a manual journal voucher" (see [purchase-order/credit-note](/en/inventory/purchase-order/credit-note) and [master-data/exchange-rate](/en/inventory/master-data/exchange-rate)) write into this pair. JV is **not** modelled as a child of `tb_inventory_transaction` — the linkage is by `jv_no` / `jv_type` convention recorded by the posting engine, not a Prisma `@relation`.

## 2. Entities

### 2.1 tb_inventory_transaction

The **movement header**. Every quantity change in the system creates exactly one row here, classified by `inventory_doc_type` (the upstream module that generated the movement) and pointed at the source document via `inventory_doc_no`. There is no `doc_status`, no `vendor_id`, no `currency_id`, and no header totals — the inventory transaction is a posted ledger record, not a workflow document. Header has no header-level financial roll-up; valuation lives entirely on the detail rows and cost-layer children.

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key; `gen_random_uuid()`. |
| `inventory_doc_type` | `enum_inventory_doc_type` | No | Source-module classifier: `good_received_note`, `credit_note`, `store_requisition`, `stock_in`, `stock_out`, `close`, `open`. Determines which source-document table `inventory_doc_no` resolves into. |
| `inventory_doc_no` | `String @db.Uuid` | No | UUID of the source document (e.g. `tb_good_received_note.id`, `tb_store_requisition.id`, `tb_stock_in.id`). Resolved application-side based on `inventory_doc_type`; no Prisma `@relation` because the target table is polymorphic. |
| `note` | `String @db.VarChar` | Yes | Free-text note attached to the movement. |
| `info` | `Json @db.JsonB` | Yes | Extension bag for tenant-specific movement metadata; default `{}`. |
| `dimension` | `Json @db.JsonB` | Yes | Cost-dimension array (project, cost-centre, job code); default `[]`. |
| `created_at` | `DateTime @db.Timestamptz(6)` | Yes | Creation timestamp; defaults to `now()`. |
| `created_by_id` | `String @db.Uuid` | Yes | User id who posted the movement. |
| `updated_at` | `DateTime @db.Timestamptz(6)` | Yes | Last-update timestamp. |
| `updated_by_id` | `String @db.Uuid` | Yes | Last-update actor id. |
| `deleted_at` | `DateTime @db.Timestamptz(6)` | Yes | Soft-delete timestamp; non-null means logically reversed. |
| `deleted_by_id` | `String @db.Uuid` | Yes | Soft-delete actor id. |

**Constraints:** `@id` on `id`. **No FKs** declared with `@relation` on the source-document columns — the source link is polymorphic and resolved at the application layer. Back-relations: many `tb_inventory_transaction_detail`, many `tb_credit_note_detail`, many `tb_stock_in_detail`, many `tb_stock_out_detail`, many `tb_store_requisition_detail`.
**Indexes:** `@@index([inventory_doc_no])` as `inventorytransaction_inventory_doc_no_idx`; `@@index([inventory_doc_type])` as `inventorytransaction_inventory_doc_type_idx`; `@@index([inventory_doc_type, inventory_doc_no])` as `inventorytransaction_inventory_doc_type_inventory_doc_no_idx`.

### 2.2 tb_inventory_transaction_detail

The **per-product / per-lot ledger line**. One transaction row spawns one detail row per affected product (in most cases) — the detail row is what carries `qty`, `cost_per_unit`, `total_cost`, the location, and the lot-trace fields `from_lot_no` (the source lot when the movement consumes from an existing layer) and `current_lot_no` (the lot newly created or affected by the movement). Detail is also the bridge into `tb_inventory_transaction_cost_layer` — every cost-flow effect (FIFO layer creation, weighted-average recompute, EOP rollforward) lives on the cost-layer rows hanging off this entity.

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `inventory_transaction_id` | `String @db.Uuid` | No | FK to `tb_inventory_transaction.id`. |
| `from_lot_no` | `String @db.VarChar` | Yes | Source lot the movement consumed from (set on issues / transfers / adjustments-out where FIFO picks an existing layer). |
| `current_lot_no` | `String @db.VarChar` | Yes | Lot newly created by this movement (set on receipts / adjustments-in / transfers-in where a new layer is opened). |
| `location_id` | `String @db.Uuid` | Yes | FK reference to `tb_location.id`. Nullable for system-level rollups (close / open). No `@relation` declared on this column. |
| `location_code` | `String @db.VarChar` | Yes | Snapshot of the location code. |
| `product_id` | `String @db.Uuid` | No | FK reference to `tb_product.id`. Required. No `@relation` declared on this column. |
| `qty` | `Decimal @db.Decimal(20, 5)` | Yes | Signed quantity in base UoM: positive = inbound (receipt / adjustment-in), negative = outbound (issue / adjustment-out). Default `0`. |
| `cost_per_unit` | `Decimal @db.Decimal(20, 5)` | Yes | Unit cost in base currency at the moment of posting; default `0`. For inbound, this is the layer cost; for outbound, the cost picked by the costing rule (FIFO from the consumed layer, or the moving-average at post time). |
| `total_cost` | `Decimal @db.Decimal(20, 5)` | Yes | `qty × cost_per_unit`; default `0`. Signed alongside `qty`. |
| `note` | `String @db.VarChar` | Yes | Free-text note. |
| `info` | `Json @db.JsonB` | Yes | Extension bag; default `{}`. |
| `dimension` | `Json @db.JsonB` | Yes | Cost-dimension array; default `[]`. |
| `created_at` | `DateTime @db.Timestamptz(6)` | Yes | Creation timestamp. |
| `created_by_id` | `String @db.Uuid` | Yes | Creator id. |
| `updated_at` | `DateTime @db.Timestamptz(6)` | Yes | Last-update timestamp. |
| `updated_by_id` | `String @db.Uuid` | Yes | Updater id. |

**Constraints:** `@id` on `id`. FK `inventory_transaction_id → tb_inventory_transaction.id` (`NoAction`). Note: `location_id` and `product_id` are stored on the row but **have no Prisma `@relation`** — they are application-resolved lookups. No soft-delete columns on this entity (unlike most others); reversal is by writing a compensating transaction with negated `qty`, not by `deleted_at`.
**Indexes:** `@@index([inventory_transaction_id])` as `inventorytransactiondetail_inventory_transaction_id_idx`.

### 2.3 tb_inventory_transaction_cost_layer

The **cost-flow record** — the canonical store of FIFO / weighted-average state. One cost-layer row per consumed or created layer-event per movement. For inbound movements the row carries `in_qty > 0` and a new `lot_no` / `lot_index`; for outbound movements the row carries `out_qty > 0` and `from_lot_no` resolved by FIFO ordering on `lot_seq_no`. The row also persists `average_cost_per_unit` so weighted-average products read the post-movement moving average without re-aggregating the whole history. `at_period` (`YYMM`) and `period_id` tie the layer to an accounting period for snapshot rollup.

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `inventory_transaction_detail_id` | `String @db.Uuid` | No | FK to `tb_inventory_transaction_detail.id`. |
| `lot_no` | `String @db.VarChar` | Yes | Lot identifier — for inbound, the new lot created; for outbound, the lot consumed from. |
| `lot_index` | `Int` | No | Sequence number within a lot; default `1`. Lots with the same `lot_no` (e.g. split or re-opened) are disambiguated by `lot_index`. |
| `location_id` | `String @db.Uuid` | Yes | FK reference to `tb_location.id`. Nullable for period-rollup rows. |
| `location_code` | `String @db.VarChar` | Yes | Snapshot. |
| `lot_at_date` | `DateTime @db.Timestamptz(6)` | Yes | Effective date of the layer (receipt date for inbound, consumption date for outbound). |
| `lot_seq_no` | `Int` | Yes | FIFO ordering anchor within `(location_id, product_id)`; default `1`. Lower `lot_seq_no` is consumed first under FIFO. |
| `product_id` | `String @db.Uuid` | Yes | FK reference to `tb_product.id`. |
| `parent_lot_no` | `String @db.VarChar` | Yes | When the layer was created from a transfer / split / re-pack, the originating lot. |
| `period_id` | `String @db.Uuid` | Yes | FK to `tb_period.id` — the accounting period containing this layer event. |
| `at_period` | `String @db.VarChar` | Yes | Period in `YYMM` form (denormalised from `tb_period.period`). |
| `transaction_type` | `enum_transaction_type` | Yes | Classifier independent of `inventory_doc_type`: `good_received_note`, `transfer_in`, `transfer_out`, `issue`, `adjustment_in`, `adjustment_out`, `credit_note_amount`, `credit_note_quantity`, `eop_in`, `eop_out`, `close_period`, `open_period`. |
| `in_qty` | `Decimal @db.Decimal(20, 5)` | Yes | Inbound qty; default `0`. Non-zero for inbound layer events. |
| `out_qty` | `Decimal @db.Decimal(20, 5)` | Yes | Outbound qty; default `0`. Non-zero for outbound layer events. |
| `cost_per_unit` | `Decimal @db.Decimal(20, 5)` | Yes | Per-unit cost on this layer event; default `0`. |
| `total_cost` | `Decimal @db.Decimal(20, 5)` | Yes | `(in_qty − out_qty) × cost_per_unit` (or the rule-specific equivalent); default `0`. |
| `diff_amount` | `Decimal @db.Decimal(20, 5)` | Yes | Variance amount used for credit-note-amount adjustments and EOP price-revaluation; default `0`. |
| `average_cost_per_unit` | `Decimal @db.Decimal(20, 5)` | Yes | Post-movement moving-average unit cost at `(location_id, product_id)`; default `0`. |
| `note` | `String @db.VarChar` | Yes | Free-text. |
| `info` | `Json @db.JsonB` | Yes | Extension bag. |
| `dimension` | `Json @db.JsonB` | Yes | Cost-dimension array. |
| `created_at` | `DateTime @db.Timestamptz(6)` | Yes | Creation timestamp. |
| `created_by_id` | `String @db.Uuid` | Yes | Creator id. |
| `updated_at` | `DateTime @db.Timestamptz(6)` | Yes | Last-update timestamp. |
| `updated_by_id` | `String @db.Uuid` | Yes | Updater id. |
| `deleted_at` | `DateTime @db.Timestamptz(6)` | Yes | Soft-delete timestamp. |
| `deleted_by_id` | `String @db.Uuid` | Yes | Soft-delete actor id. |

**Constraints:** `@id` on `id`. FKs: `inventory_transaction_detail_id → tb_inventory_transaction_detail.id` (`NoAction`); `period_id → tb_period.id` (`NoAction`). Note: `location_id` and `product_id` are stored without `@relation`. The map name `tb_inventory_transaction_clos_inventory_transaction_detail_fkey` reflects an earlier "closing balance" naming.
**Indexes:** `@@unique([lot_no, lot_index])` as `inventorytransactionclosingbalance_lotno_lot_index_u` (lot identity); `@@index([lot_no, lot_index])` as `inventorytransactioncostlayer_lotno_lot_index_idx`.

### 2.4 tb_location

The **storage / cost-centre definition**. Locations are the second key (after `product_id`) of every balance and movement. The `location_type` enum is the single most consequential setting on the location: it determines whether a posting hits the inventory asset (`inventory`), the department expense (`direct`), or a memo register (`consignment`).

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `code` | `String @db.VarChar` | No | Human-readable location code. |
| `name` | `String @db.VarChar` | No | Display name. |
| `location_type` | `enum_location_type` | No | `inventory` (default — owned-stock asset), `direct` (direct-cost centre — bypasses inventory, posts to expense), `consignment` (vendor-owned — memo only). |
| `description` | `String` | Yes | Free-text. |
| `delivery_point_id` | `String @db.Uuid` | Yes | FK to `tb_delivery_point.id`. |
| `delivery_point_name` | `String @db.VarChar` | Yes | Snapshot. |
| `physical_count_type` | `enum_physical_count_type` | No | `no` (default — location not subject to scheduled physical count) or `yes` (counted at period end). |
| `is_active` | `Boolean` | Yes | Default `true`. |
| `note` | `String @db.VarChar` | Yes | Free-text. |
| `info` | `Json @db.JsonB` | Yes | Extension bag; default `{}`. |
| `dimension` | `Json @db.JsonB` | Yes | Cost-dimension array; default `[]`. |
| `created_at` | `DateTime @db.Timestamptz(6)` | Yes | Creation timestamp. |
| `created_by_id` | `String @db.Uuid` | Yes | Creator id. |
| `updated_at` | `DateTime @db.Timestamptz(6)` | Yes | Last-update timestamp. |
| `updated_by_id` | `String @db.Uuid` | Yes | Updater id. |
| `deleted_at` | `DateTime @db.Timestamptz(6)` | Yes | Soft-delete timestamp. |
| `deleted_by_id` | `String @db.Uuid` | Yes | Soft-delete actor id. |

**Constraints:** `@id` on `id`. FK `delivery_point_id → tb_delivery_point.id` (`NoAction`). Back-relations span many downstream tables: `tb_good_received_note_detail`, `tb_purchase_request_detail`, `tb_stock_in`, `tb_stock_out`, `tb_count_stock`, `tb_spot_check`, `tb_physical_count`, `tb_product_location`, `tb_user_location`, `tb_credit_note_detail`, `tb_store_requisition_from`, `tb_store_requisition_to`, `tb_location_comment`, `tb_purchase_request_template_detail`, `tb_purchase_order_detail_tb_purchase_request_detail`.
**Indexes:** `@@unique([name, deleted_at])` as `location_name_u`; `@@index([name])` as `location_name_idx`; `@@index([code])` as `location_code_idx`.

### 2.5 tb_product_location

The **per-product / per-location stock-policy row**. Holds par / min / max / reorder quantities used by the replenishment rules and on-hand alerts; does **not** store on-hand qty (that is derived from the cost-layer ledger).

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `product_id` | `String @db.Uuid` | No | FK to `tb_product.id`. |
| `location_id` | `String @db.Uuid` | Yes | FK to `tb_location.id`. |
| `min_qty` | `Decimal @db.Decimal(20, 5)` | Yes | Below-this triggers a replenishment alert; default `0`. |
| `max_qty` | `Decimal @db.Decimal(20, 5)` | Yes | Above-this triggers an over-stock alert; default `0`. |
| `re_order_qty` | `Decimal @db.Decimal(20, 5)` | Yes | Suggested order qty when on-hand drops below `min_qty`; default `0`. |
| `par_qty` | `Decimal @db.Decimal(20, 5)` | Yes | Par level for outlet stocking; default `0`. |
| `note` | `String @db.VarChar` | Yes | Free-text. |
| `info` | `Json @db.JsonB` | Yes | Extension bag. |
| `dimension` | `Json @db.JsonB` | Yes | Cost-dimension array. |
| `doc_version` | `Int` | No | Optimistic-concurrency counter; default `0`. |
| `created_at` | `DateTime @db.Timestamptz(6)` | Yes | Creation timestamp. |
| `created_by_id` | `String @db.Uuid` | Yes | Creator id. |
| `updated_at` | `DateTime @db.Timestamptz(6)` | Yes | Last-update timestamp. |
| `updated_by_id` | `String @db.Uuid` | Yes | Updater id. |
| `deleted_at` | `DateTime @db.Timestamptz(6)` | Yes | Soft-delete timestamp. |
| `deleted_by_id` | `String @db.Uuid` | Yes | Soft-delete actor id. |

**Constraints:** `@id` on `id`. FKs: `product_id → tb_product.id` (`NoAction`); `location_id → tb_location.id` (`NoAction`).
**Indexes:** `@@unique([product_id, location_id, deleted_at])` as `product_location_product_id_location_id_u`; `@@index([product_id, location_id])` as `product_location_product_id_location_id_idx`.

### 2.6 tb_period

The **accounting period header** — the time-boundary primitive that the period-end process operates on. The period status enum (`open`, `closed`, `locked`) gates whether backdated postings into this period are accepted; movement-side validation reads this status at post time.

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `period` | `String @db.VarChar` | No | `YYMM` form (e.g. `2604` for April 2026). |
| `fiscal_year` | `Int @db.Integer` | No | 4-digit fiscal year. |
| `fiscal_month` | `Int @db.Integer` | No | 1-12. |
| `start_at` | `DateTime @db.Timestamptz(6)` | No | Period start. |
| `end_at` | `DateTime @db.Timestamptz(6)` | No | Period end. |
| `status` | `enum_period_status` | No | `open` (default — accepting postings), `closed` (no new movements, snapshot computed), `locked` (audited and immutable). |
| `note` | `String @db.VarChar` | Yes | Free-text. |
| `info` | `Json @db.JsonB` | Yes | Extension bag. |
| `dimension` | `Json @db.JsonB` | Yes | Cost-dimension array. |
| `created_at` | `DateTime @db.Timestamptz(6)` | Yes | Creation timestamp. |
| `created_by_id` | `String @db.Uuid` | Yes | Creator id. |
| `updated_at` | `DateTime @db.Timestamptz(6)` | Yes | Last-update timestamp. |
| `updated_by_id` | `String @db.Uuid` | Yes | Updater id. |
| `deleted_at` | `DateTime @db.Timestamptz(6)` | Yes | Soft-delete timestamp. |
| `deleted_by_id` | `String @db.Uuid` | Yes | Soft-delete actor id. |

**Constraints:** `@id` on `id`. Back-relations: many `tb_period_snapshot`, many `tb_inventory_transaction_cost_layer`, many `tb_period_comment`, many `tb_physical_count_period`.
**Indexes:** `@@unique([period, deleted_at])` as `period_period_u`; `@@unique([fiscal_year, fiscal_month, deleted_at])` as `period_fiscal_year_month_u`; `@@index([fiscal_year, fiscal_month])` as `period_fiscal_year_month_idx`; `@@index([period])` as `period_period_idx`.

### 2.7 tb_period_snapshot

The **locked opening / closing balance row per period × location × product × lot**. Written at period close as the audit anchor for the closed period and the opening for the next period. Carries opening / movement-bucket / closing qty and cost columns so reporting can read a period's net activity directly without re-walking the cost-layer ledger.

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `period_id` | `String @db.Uuid` | No | FK to `tb_period.id`. |
| `snapshot_at` | `DateTime @db.Timestamptz(6)` | No | Effective timestamp of the snapshot. |
| `location_id` | `String @db.Uuid` | No | FK reference to `tb_location.id`. |
| `location_code` | `String @db.VarChar` | Yes | Snapshot. |
| `location_name` | `String @db.VarChar` | Yes | Snapshot. |
| `product_id` | `String @db.Uuid` | No | FK reference to `tb_product.id`. |
| `product_code` | `String @db.VarChar` | Yes | Snapshot. |
| `product_name` | `String @db.VarChar` | Yes | Snapshot. |
| `product_local_name` | `String @db.VarChar` | Yes | Localised snapshot. |
| `product_sku` | `String @db.VarChar` | Yes | SKU snapshot. |
| `lot_no` | `String @db.VarChar` | Yes | Lot identifier (when batch-tracked). |
| `lot_index` | `Int` | Yes | Default `1`. |
| `lot_at_date` | `DateTime @db.Timestamptz(6)` | Yes | Original lot date. |
| `lot_seq_no` | `Int` | Yes | FIFO sequence. |
| `opening_qty` | `Decimal @db.Decimal(20, 5)` | Yes | Opening on-hand qty for the period. |
| `opening_cost_per_unit` | `Decimal @db.Decimal(20, 5)` | Yes | Opening unit cost. |
| `opening_total_cost` | `Decimal @db.Decimal(20, 5)` | Yes | `opening_qty × opening_cost_per_unit`. |
| `receipt_qty` | `Decimal @db.Decimal(20, 5)` | Yes | Total inbound qty during the period. |
| `receipt_total_cost` | `Decimal @db.Decimal(20, 5)` | Yes | Total inbound cost during the period. |
| `issue_qty` | `Decimal @db.Decimal(20, 5)` | Yes | Total outbound qty during the period. |
| `issue_total_cost` | `Decimal @db.Decimal(20, 5)` | Yes | Total outbound cost during the period. |
| `adjustment_qty` | `Decimal @db.Decimal(20, 5)` | Yes | Net adjustment qty during the period. |
| `adjustment_total_cost` | `Decimal @db.Decimal(20, 5)` | Yes | Net adjustment cost during the period. |
| `closing_qty` | `Decimal @db.Decimal(20, 5)` | Yes | Closing on-hand qty (period anchor). |
| `closing_cost_per_unit` | `Decimal @db.Decimal(20, 5)` | Yes | Closing unit cost. |
| `closing_total_cost` | `Decimal @db.Decimal(20, 5)` | Yes | `closing_qty × closing_cost_per_unit`. |
| `diff_amount` | `Decimal @db.Decimal(20, 5)` | Yes | Reconciliation variance (typically from physical-count adjustments captured in the period). |
| `note` | `String @db.VarChar` | Yes | Free-text. |
| `info` | `Json @db.JsonB` | Yes | Extension bag. |
| `dimension` | `Json @db.JsonB` | Yes | Cost-dimension array. |
| `created_at` | `DateTime @db.Timestamptz(6)` | Yes | Creation timestamp. |
| `created_by_id` | `String @db.Uuid` | Yes | Creator id. |
| `updated_at` | `DateTime @db.Timestamptz(6)` | Yes | Last-update timestamp. |
| `updated_by_id` | `String @db.Uuid` | Yes | Updater id. |
| `deleted_at` | `DateTime @db.Timestamptz(6)` | Yes | Soft-delete timestamp. |
| `deleted_by_id` | `String @db.Uuid` | Yes | Soft-delete actor id. |

**Constraints:** `@id` on `id`. FK `period_id → tb_period.id` (`NoAction`). Note: `location_id` and `product_id` are stored without `@relation`.
**Indexes:** `@@unique([period_id, snapshot_at, deleted_at])` as `periodsnapshot_period_id_snapshot_at_u`; `@@index([period_id, snapshot_at])` as `periodsnapshot_period_id_snapshot_at_idx`.

## 3. Relationships

```
tb_inventory_transaction        (movement header — polymorphic source)
    │  inventory_doc_type ∈ {good_received_note, credit_note, store_requisition,
    │                        stock_in, stock_out, close, open}
    │  inventory_doc_no → application-resolved (no @relation):
    │       good_received_note → tb_good_received_note.id
    │       credit_note        → tb_credit_note.id
    │       store_requisition  → tb_store_requisition.id
    │       stock_in           → tb_stock_in.id
    │       stock_out          → tb_stock_out.id
    │       close / open       → tb_period.id
    │
    │ * inventory_transaction_id
    ▼
tb_inventory_transaction_detail (per-product/lot ledger line)
    │  qty (signed), cost_per_unit, total_cost,
    │  from_lot_no (outbound source layer), current_lot_no (inbound new layer)
    │
    │ FK references (no @relation declared on these)
    ├──► tb_location  (location_id)
    └──► tb_product   (product_id)
    │
    │ * inventory_transaction_detail_id
    ▼
tb_inventory_transaction_cost_layer  (FIFO / weighted-average layer event —
                                       the canonical cost-flow record)
    │  transaction_type ∈ {good_received_note, transfer_in, transfer_out,
    │                      issue, adjustment_in, adjustment_out,
    │                      credit_note_amount, credit_note_quantity,
    │                      eop_in, eop_out, close_period, open_period}
    │  in_qty / out_qty, cost_per_unit, average_cost_per_unit,
    │  lot_no, lot_index, lot_seq_no (FIFO ordering anchor),
    │  parent_lot_no (transfer/split source)
    │
    └──► tb_period   (period_id — accounting period containing the layer event)


tb_location ──1──*──► tb_product_location  (per-product stock policy:
    │                                        min/max/par/reorder — no on-hand)
    │
    └──► tb_delivery_point  (delivery_point_id)


tb_period ──1──*──► tb_period_snapshot  (locked period × location × product × lot
                                          balance row — opening/closing anchor)


tb_inventory_transaction is reached BACK from the source modules:
    tb_good_received_note_detail_item.inventory_transaction_id  (GRN receipts)
    tb_stock_in_detail.inventory_transaction_id                  (manual stock-in)
    tb_stock_out_detail.inventory_transaction_id                 (manual stock-out)
    tb_store_requisition_detail.inventory_transaction_id         (requisition issues)
    tb_credit_note_detail.inventory_transaction_id               (credit-note adj)

    All five of these source-side columns are UUID references with NO Prisma @relation;
    the link runs source → inventory in the source module's @relation set,
    and inventory → source via the polymorphic inventory_doc_no.
```

Notes:

- **Movement-driven, not balance-stored.** There is no `tb_stock_balance` row that the system updates on each transaction. Current on-hand at `(location_id, product_id, lot_no)` is computed as `last_snapshot.closing_qty + Σ (cost_layer.in_qty − cost_layer.out_qty)` since that snapshot. Performance-sensitive queries use a materialised view or read from the source-module's cached `last_unit_cost` snapshot, but the canonical answer is always the algebraic sum.
- **Polymorphic source link.** `tb_inventory_transaction.inventory_doc_type` + `inventory_doc_no` is the only way to walk back to the originating document; there is no Prisma `@relation` because the target table varies. The reverse direction (source-side column `inventory_transaction_id` on every source-detail table) is the symmetric polymorphic link without a `@relation`.
- **Two enums for "movement type".** `enum_inventory_doc_type` classifies the **source module** (`good_received_note`, `store_requisition`, etc.), while `enum_transaction_type` on the cost-layer classifies the **cost-flow effect** (`good_received_note`, `issue`, `transfer_in`, `eop_in`, `close_period`, etc.). They overlap but are not identical — a GRN receipt is `good_received_note` on both, but a store-requisition transfer creates two cost-layer rows (`transfer_out` from source location, `transfer_in` to destination) under a single `store_requisition` doc.
- **No header-level totals on the transaction.** Unlike documents (GRN / PO / PR), `tb_inventory_transaction` has no roll-up columns. Sum the detail rows or the cost layers for valuation; the period snapshot is the only place where pre-aggregated bucket totals live.
- **Soft-delete asymmetry.** Most inventory entities support `deleted_at` soft-delete. `tb_inventory_transaction_detail` is the exception — it has no soft-delete columns. To reverse a posted detail row, post a compensating transaction with negated `qty` rather than soft-deleting; this preserves the audit trail and is the path the credit-note and period-end-EOP flows take.
- **All explicit `@relation` FK declarations use `onDelete: NoAction, onUpdate: NoAction`** — referential integrity is preserved by application-level soft-delete (`deleted_at`) and by the period-lock guard, not by cascade.

## 4. Enums

- **`enum_inventory_doc_type`**: source-module classifier on `tb_inventory_transaction.inventory_doc_type`. Seven values, no default declared on the column (every transaction must specify):
  - `good_received_note` — receipt from [good-receive-note](/en/inventory/good-receive-note) commit (`saved → committed`).
  - `credit_note` — vendor credit-note adjustment (post-receipt correction; can be quantity-only or amount-only).
  - `store_requisition` — internal issue / transfer from [store-requisition](/en/inventory/store-requisition) approve / dispatch.
  - `stock_in` — manual stock-in (`tb_stock_in` document — typically used for inventory-adjustment-in, found-stock, or count overage corrections).
  - `stock_out` — manual stock-out (`tb_stock_out` document — typically write-off, breakage, count shortage corrections).
  - `close` — period-close rollforward (system-posted at period transition).
  - `open` — period-open rollforward (system-posted as the matching opening of the next period).
- **`enum_location_type`**: posting behaviour for `tb_location.location_type`. Default `inventory`. Three values:
  - `inventory` — owned-stock asset. Posting debits/credits the **Inventory** GL account; on-hand qty is tracked; valuation is per the costing method.
  - `direct` — direct-cost centre. Posting **bypasses the inventory asset** and debits **Department Expense** directly. No on-hand carried; no consumption posting later — receipt = expense. See `../carmen/docs/Inventory/location-type-and-financial-treatment.md` for the journal-entry breakdown.
  - `consignment` — vendor-owned stock held at the location. **Memo register only at receipt** (no inventory asset, no AP liability); consumption posts COGS and the AP liability simultaneously.
- **`enum_transaction_type`**: cost-flow effect on `tb_inventory_transaction_cost_layer.transaction_type`. Twelve values, nullable on the column:
  - `good_received_note` — inbound layer creation from a GRN receipt (`in_qty > 0`, new `lot_no`).
  - `transfer_in` — inbound layer at destination from a store-requisition transfer (`in_qty > 0`, `parent_lot_no` set).
  - `transfer_out` — outbound layer at source from a transfer (`out_qty > 0`, FIFO consumes by `lot_seq_no`).
  - `issue` — outbound consumption from a store-requisition issue (`out_qty > 0`).
  - `adjustment_in` — inbound from manual stock-in (`tb_stock_in`) — found-stock, count overage, etc.
  - `adjustment_out` — outbound from manual stock-out (`tb_stock_out`) — breakage, count shortage, etc.
  - `credit_note_amount` — amount-only credit-note adjustment (`diff_amount` set; `in_qty` / `out_qty` zero).
  - `credit_note_quantity` — quantity credit note (compensating outbound from the original receipt's lot).
  - `eop_in` — end-of-period inbound rollforward (system-posted, ties opening of next period to closing of this period).
  - `eop_out` — end-of-period outbound rollforward.
  - `close_period` — period-close anchor row written to the period being closed.
  - `open_period` — period-open anchor row written to the next period.
- **`enum_period_status`**: status of an accounting period on `tb_period.status`. Default `open`. Three values:
  - `open` — accepting movements (current or future open period).
  - `closed` — period-end run, snapshot written; no new movements accepted with a transaction date inside this period unless explicitly re-opened.
  - `locked` — audited and immutable. Even an admin re-open is not permitted; corrections post into a current open period as restatement.
- **`enum_physical_count_type`**: count-eligibility flag on `tb_location.physical_count_type`. Default `no`. Two values:
  - `no` — location is **not** swept by the scheduled physical-count run (typically direct / consignment / staging locations).
  - `yes` — location **is** swept by the scheduled physical count.

## 5. Divergences from carmen/docs

The carmen/docs Inventory PRD (`inventory-management-prd.md`), the data-structure trace (`data-structure-trace.md`), the financial-treatment doc (`location-type-and-financial-treatment.md`), and the period-end process doc (`inventory-management/period-end-process.md`) collectively describe a richer interface model than the Prisma reality — in particular, several "balance" and "status" interfaces that are derived in the application layer rather than persisted as schema rows. Cross-checking against the canonical Prisma schema yields the following divergences:

| # | Item | carmen/docs says | Prisma has | Action |
|---|------|------------------|------------|--------|
| 1 | Stock balance entity | `InventoryStatus` / `StockBalance` interface with `QuantityOnHand`, `QuantityAllocated`, `QuantityAvailable`, `QuantityInTransit`, `LastUnitCost`, `AverageCost`, `TotalCost` as **persisted columns** keyed by `(location_id, product_id, lot_no)`. PRD §3 and `data-structure-trace.md` describe writes to this entity on every movement. | **No `tb_stock_balance` model exists.** On-hand is computed as `Σ cost_layer.in_qty − Σ cost_layer.out_qty` since the most recent `tb_period_snapshot.closing_qty` anchor, scoped to `(location_id, product_id, lot_no)`. `LastUnitCost` and `AverageCost` are surfaced via `tb_inventory_transaction_cost_layer.cost_per_unit` and `.average_cost_per_unit` on the most recent layer event. `inTransit` and `Allocated` are derived from open-document state (issued-but-not-received SR transfers, reserved-but-not-issued requisitions) rather than columns. | Treat Prisma as canonical. Update carmen/docs to describe `InventoryStatus` as a **read-model / derived view**, not a persisted row. Document the derivation rule (period snapshot anchor + cost-layer sum) so consumers understand the canonical query shape. |
| 2 | Movement entity name and type values | PRD describes `StockMovement` with `type ∈ {RECEIPT, ISSUE, TRANSFER, ADJUSTMENT, RETURN, WRITE_OFF}` and a workflow status (`DRAFT → PENDING → IN_TRANSIT → COMPLETED → CANCELLED`). | Two-table model: `tb_inventory_transaction` carries `inventory_doc_type` (source-module classifier — `good_received_note`, `credit_note`, `store_requisition`, `stock_in`, `stock_out`, `close`, `open`), and `tb_inventory_transaction_cost_layer.transaction_type` (twelve cost-flow types listed in Section 4). **There is no `RETURN`, no `WRITE_OFF`, and no workflow status on the transaction itself** — the transaction is a posted ledger record, not a workflow document. Returns are modelled as credit notes (`credit_note_amount` / `credit_note_quantity`); write-offs are modelled as `tb_stock_out` with an appropriate `adjustment_type_id`. | Realign carmen/docs to describe two enums (`enum_inventory_doc_type` source-module classifier, `enum_transaction_type` cost-flow effect) rather than a single combined type field. Document that returns and write-offs are routed through credit-note / stock-out documents respectively. |
| 3 | Stock movement workflow status | PRD §3 implies a multi-state workflow on the movement (`DRAFT → PENDING → IN_TRANSIT → COMPLETED → CANCELLED`). | `tb_inventory_transaction` has **no** `doc_status` enum, **no** `workflow_history`, **no** `workflow_current_stage`, and **no** `user_action`. Workflow lives on the source-module document (GRN's `enum_good_received_note_status`, SR's `enum_doc_status`, etc.); the inventory transaction is **posted-only** — it exists if and only if the source document is at a committed/posted state. Reversal is by writing a compensating transaction (or by the source document moving to a void/credit-note state that triggers the compensating write), not by a state change on the transaction row. | Drop the workflow-status claim from carmen/docs's inventory entity description. Note that the workflow lives on the source document and the inventory transaction is the immutable posted artefact. |
| 4 | Valuation method on the product | PRD §3 cites `valuationMethod: FIFO | WEIGHTED_AVERAGE` configured per product. | Costing method per product is held on the **product** model (`tb_product`) — not on inventory. The inventory module **consumes** the method when picking the cost on outbound transactions (FIFO scans `tb_inventory_transaction_cost_layer` by `lot_seq_no` ascending; weighted-average reads the most recent `average_cost_per_unit`). | Move the valuation-method documentation under [product](/en/inventory/product) / [costing](/en/inventory/costing). Inventory documents the **consumption** rule, not the configuration. |
| 5 | Period-end snapshot scope and shape | `inventory-management/period-end-process.md` describes a period-end snapshot as a procedural checklist outcome with reports (Inventory Valuation Report, Movement Report, Variance Report). | `tb_period_snapshot` is the **persistent** snapshot — one row per `(period_id, location_id, product_id, lot_no, lot_index)` carrying opening / receipt / issue / adjustment / closing buckets in both qty and cost. The reports are read from this table; the table itself is the audit anchor. The checklist is process around the table write. | Update carmen/docs to add the `tb_period_snapshot` entity definition. Document that the snapshot is the system's locked anchor, not just a report output. |
| 6 | "Free / Allocated / Available / InTransit" qty columns | PRD §3 Key Concepts lists `onHand`, `allocated`, `available`, and `inTransit` as parallel columns on the stock balance. | None of the four are persisted on any inventory table. `onHand` is the derived sum (item 1 above). `allocated` and `available` are derived from open-document state: `allocated = Σ open store-requisition reservations` for the product/location; `available = onHand − allocated`. `inTransit` is `Σ store-requisition lines in transfer-dispatched-but-not-received state`. | Document the derivation rules in carmen/docs and the read-model that surfaces them; drop the "persisted column" framing. |
| 7 | Direct-cost location not part of inventory | `location-type-and-financial-treatment.md` mentions Direct Location Inventory bypasses balance sheet ("No inventory asset recorded… Bypasses balance sheet entirely"). | This is consistent with Prisma — `tb_location.location_type = direct` posts the inbound transaction with `Dr Department Expense / Cr AP` and **does not** create a `tb_inventory_transaction_cost_layer` row for the consumption (since the goods are immediately expensed). The cost-layer ledger contains only inventory-type movements. | No divergence; add a note in carmen/docs cross-referencing `enum_location_type = direct` and clarifying that direct-location movements are still recorded in `tb_inventory_transaction` (for audit) but do not produce a layer row. |
| 8 | Consignment inventory tracking | `location-type-and-financial-treatment.md`: consignment receipt is memo-only ("Receipt: No entry — memo record only"); consumption triggers `Dr COGS / Cr AP`. | Consistent with Prisma — `tb_location.location_type = consignment` produces a `tb_inventory_transaction` row at receipt (for audit) but the cost-layer ledger flagged consignment registers separately; consumption posts both COGS and AP liability simultaneously. | No divergence; clarify in carmen/docs that consignment-type locations still write transactions (for audit) but the cost-layer flag distinguishes vendor-owned from owned-stock layers. |
| 9 | Location ↔ delivery point | `data-structure-trace.md` describes `Location` and `DeliveryPoint` as separate, peer entities with a join. | `tb_location` carries `delivery_point_id` (nullable FK) and `delivery_point_name` (snapshot) directly on the location row — a delivery point is the dock / receiving point associated with the location, not a separate fan-out. The FK has a Prisma `@relation` to `tb_delivery_point`. | Update carmen/docs to document the 1:1 (or N:1) relationship: each location may have one default delivery point; multiple locations may share a delivery point. |
| 10 | `physical_count_type` on the location | Not described in carmen/docs. | Prisma has `tb_location.physical_count_type ∈ {yes, no}` (default `no`); the field gates whether the scheduled physical-count run sweeps the location. Some location-type rows default to `yes` in the seed data (e.g. main warehouse), others to `no` (staging / transit / direct / consignment). | Add to carmen/docs as a configuration field. Document that direct- and consignment-type locations typically have `physical_count_type = no` (counts are unmeaningful there). |
| 11 | Transaction-detail `from_lot_no` / `current_lot_no` semantics | `data-structure-trace.md` describes lot numbers as fields on the receipt document. | Lot numbers are on `tb_inventory_transaction_detail` (`from_lot_no` for the source layer on outbound, `current_lot_no` for the new layer on inbound) **and** on `tb_inventory_transaction_cost_layer` (`lot_no` for the layer identity, `parent_lot_no` for transfer/split lineage). The receipt-document linkage to lot data is **via** the inventory transaction (e.g. GRN's `tb_good_received_note_detail_item.inventory_transaction_id`), not on the document row itself — this is the same divergence pattern called out in [good-receive-note](/en/inventory/good-receive-note) § 5 item 3. | Update carmen/docs to document lot data on the inventory transaction side. The receipt document is the entry-point UI, not the lot store. |
| 12 | Cost-layer `diff_amount` column | Not described in carmen/docs. | `tb_inventory_transaction_cost_layer.diff_amount` is used for credit-note-amount adjustments (vendor concedes a price discount post-receipt) and for end-of-period price revaluation; carries the cost variance independent of the in/out qty. | Add to carmen/docs as the "cost variance on a layer event" field; clarify that it is separate from `total_cost` and is summed into the period snapshot's `adjustment_total_cost`. |

## 6. References

- **Primary (source of truth):** Prisma schemas listed in the header callout — concretely `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` (all seven inventory entities: `tb_inventory_transaction`, `tb_inventory_transaction_detail`, `tb_inventory_transaction_cost_layer`, `tb_location`, `tb_product_location`, `tb_period`, `tb_period_snapshot`, plus the five enums `enum_inventory_doc_type`, `enum_location_type`, `enum_transaction_type`, `enum_period_status`, `enum_physical_count_type`) and `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` (verified to contain no inventory models).
- **Secondary (concept cross-check):**
  - `../carmen/docs/Inventory/inventory-management-prd.md` — PRD describing `InventoryStatus` / `StockMovement` / valuation methods; divergences in Section 5 (items 1, 2, 3, 4, 6).
  - `../carmen/docs/Inventory/data-structure-trace.md` — data-structure trace describing the lot / location / delivery-point relationships; divergences in Section 5 (items 9, 11).
  - `../carmen/docs/Inventory/location-type-and-financial-treatment.md` — journal-entry breakdown per location type (inventory / direct / consignment); cross-checked against `enum_location_type` and the cost-layer ledger behaviour (items 7, 8).
  - `../carmen/docs/Inventory/stock-in-detail.md` — manual stock-in adjustment workflow; cross-referenced for the `enum_inventory_doc_type = stock_in` path.
  - `../carmen/docs/inventory-management/period-end-process.md` — period-end checklist and snapshot framing; divergences in Section 5 (item 5 — `tb_period_snapshot` is the persistent anchor, not just a report output).
- Related modules: [good-receive-note](/en/inventory/good-receive-note) (receipts post `enum_inventory_doc_type = good_received_note` transactions; the cross-link to the inventory transaction lives on `tb_good_received_note_detail_item.inventory_transaction_id`), [store-requisition](/en/inventory/store-requisition) (issues / transfers; SR detail carries `inventory_transaction_id`), [physical-count](/en/inventory/physical-count) (count adjustments post `tb_stock_in` / `tb_stock_out` rows mapped to `adjustment_in` / `adjustment_out`), [spot-check](/en/inventory/spot-check) (partial counts; same posting path as physical-count), [inventory-adjustment](/en/inventory/inventory-adjustment) (manual stock-in / stock-out for non-count corrections), [costing](/en/inventory/costing) (consumes `tb_inventory_transaction_cost_layer.cost_per_unit` / `.average_cost_per_unit` for outbound cost picking and for COGS), [product](/en/inventory/product) (carries the costing-method configuration the cost-layer reads at post time), [vendor-pricelist](/en/inventory/vendor-pricelist) (price-variance against the receiving GRN's unit cost, indirectly via the inbound layer).

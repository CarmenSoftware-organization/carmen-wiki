---
title: Inventory Adjustment — Data Model
description: Entities, fields, relationships, and enums for the inventory-adjustment module.
published: true
date: 2026-05-15T13:00:00.000Z
tags: inventory-adjustment, data-model, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T13:00:00.000Z
---

# Inventory Adjustment — Data Model

> **Source of truth:** Backend Prisma schema. Always read these first when writing or updating this page:
> - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma`
> - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma`
>
> The `generated/client/schema.prisma` files under each package are auto-generated copies and not authoritative.

## 1. Overview

The Inventory Adjustment module is the **document layer** for manual stock-in / stock-out corrections — write-offs, write-ons, found stock, expiry / damage / breakage adjustments, count-variance rollups, and any other quantity / value change that does not flow through a procurement (GRN), consumption (Store Requisition), or count document on its own. Unlike the other document-centric modules, the adjustment module **does not own a single `tb_inventory_adjustment` model** in the canonical Prisma schema: the persisted shape is **two parallel document trees** — `tb_stock_in` (inbound / write-on direction) and `tb_stock_out` (outbound / write-off direction) — joined by a shared classifier table `tb_adjustment_type` that distinguishes adjustment reasons (e.g. `FOUND_STOCK`, `COUNT_OVERAGE`, `BREAKAGE`, `EXPIRY_WRITE_OFF`) and is keyed by `enum_adjustment_type` (`STOCK_IN` / `STOCK_OUT`).

Both `tb_stock_in` and `tb_stock_out` follow the standard document spine — header (`si_no` / `so_no`, `si_date` / `so_date`, location, adjustment-type, `doc_status`, workflow, comments, attachments) plus child detail rows (per product, with `qty`, `cost_per_unit`, `total_cost`, and the `inventory_transaction_id` back-reference to the [[inventory]] ledger). The header `doc_status` enum (`draft` → `in_progress` → `completed` → `cancelled` / `voided`) carries the workflow state; posting fires on the `in_progress → completed` transition and writes a `tb_inventory_transaction` row of `inventory_doc_type = stock_in` / `stock_out` with the detail's `inventory_transaction_id` stamped onto it. Lot data lives on the inventory transaction side (`current_lot_no` / `from_lot_no` on `tb_inventory_transaction_detail`, `lot_no` / `lot_index` on `tb_inventory_transaction_cost_layer`), **not** on the stock-in / stock-out detail row itself — a divergence pattern shared with [[good-receive-note]] (`GRN_*` data-model § 5 item 3).

The module sits **between the operations floor and the inventory ledger**. It is downstream of (a) [[physical-count]] / [[spot-check]] — count variance produces a `tb_stock_in` (overage) and/or `tb_stock_out` (shortage) rollup document that auto-stages under Inventory Controller authority, (b) ad-hoc floor activity — Store Keeper raises `tb_stock_in` for found stock and `tb_stock_out` for breakage / expiry, and (c) recall / reclassification — Sysadmin or Inventory Controller raises adjustments to consignment-to-inventory ownership transfers and migration data fix-ups. It is upstream of [[inventory]] — every approved adjustment writes one `tb_inventory_transaction` per detail line with `enum_transaction_type = adjustment_in` / `adjustment_out` on the cost-layer ledger, feeding [[costing]] for FIFO layer creation / weighted-average refresh and producing the GL postings keyed by the adjustment-type's mapped account.

## 2. Entities

### 2.1 tb_adjustment_type

The **reason-code classifier** for both `tb_stock_in` and `tb_stock_out` documents. A reason-code row carries a `code` (e.g. `BREAKAGE`, `FOUND_STOCK`), a human-readable `name`, the constrained direction via `enum_adjustment_type` (`STOCK_IN` or `STOCK_OUT` — note the Prisma enum has only the two direction values; "BOTH" is application-layer convenience, not a schema value), and a free-text `description`. Reason codes are master data maintained by the System Administrator under [[inventory]]-`INV_AUTH_008` and used at adjustment-document creation time to drive (i) reason-list filtering by direction, (ii) the GL account mapping for the resulting journal entry (resolved application-side via `info` / `dimension` JSON, no Prisma column for `gl_account`), and (iii) reporting categorisation.

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key; `gen_random_uuid()`. |
| `code` | `String @db.VarChar` | No | Reason-code mnemonic, e.g. `BREAKAGE`, `EXPIRY_WRITE_OFF`, `FOUND_STOCK`, `COUNT_OVERAGE`, `COUNT_SHORTAGE`, `RECALL_REPLACEMENT`, `VENDOR_FREE_REPLACEMENT`, `DATA_FIX`. Unique within `deleted_at`. |
| `name` | `String @db.VarChar` | No | Display name for picker UI. |
| `type` | `enum_adjustment_type` | No | Direction classifier: `STOCK_IN` or `STOCK_OUT`. Filters the reason list shown on the corresponding document. |
| `description` | `String @db.VarChar` | Yes | Free-text explanation. |
| `is_active` | `Boolean` | Yes | Default `true`. Inactive reasons are hidden from new-document pickers but remain readable on historical documents. |
| `note` | `String @db.VarChar` | Yes | Free-text note. |
| `info` | `Json @db.JsonB` | Yes | Extension bag; default `{}`. Typical use: `glAccount`, `requiresDocument`, `requiresQualityCheck` flags from the carmen/docs `AdjustmentReason` interface — see Section 5 item 2 below. |
| `dimension` | `Json @db.JsonB` | Yes | Cost-dimension array; default `[]`. |
| `created_at` | `DateTime @db.Timestamptz(6)` | Yes | Creation timestamp; defaults to `now()`. |
| `created_by_id` | `String @db.Uuid` | Yes | Creator id. |
| `updated_at` | `DateTime @db.Timestamptz(6)` | Yes | Last-update timestamp. |
| `updated_by_id` | `String @db.Uuid` | Yes | Updater id. |
| `deleted_at` | `DateTime @db.Timestamptz(6)` | Yes | Soft-delete timestamp; non-null hides the row from new-document pickers. |
| `deleted_by_id` | `String @db.Uuid` | Yes | Soft-delete actor id. |

**Constraints:** `@id` on `id`. Back-relations: many `tb_stock_in`, many `tb_stock_out`.
**Indexes:** `@@unique([code, deleted_at])` as `AT1_code_u`; `@@index([code])` as `AT1_code_idx`.

### 2.2 tb_stock_in

The **inbound adjustment document header**. One row per stock-in event, carrying the document number (`si_no`), document date (`si_date`), location (the destination of the inbound), the chosen `adjustment_type` (a row in `tb_adjustment_type` with `type = STOCK_IN`), the `doc_status` lifecycle, the workflow state (current / previous / next stage, history, executor list), and the standard audit-trail columns. Comments and attachments hang off `tb_stock_in_comment`; per-product detail rows hang off `tb_stock_in_detail`.

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `si_date` | `DateTime @db.Timestamptz(6)` | Yes | Document date. Drives the period containment check at post time per [[inventory]] `INV_VAL_008`. |
| `si_no` | `String @db.VarChar` | Yes | Human-readable stock-in number; unique within `deleted_at`. |
| `description` | `String @db.VarChar` | Yes | Header-level free-text description of why the adjustment is happening. |
| `adjustment_type_id` | `String @db.Uuid` | Yes | FK to `tb_adjustment_type.id` (`onDelete: NoAction`). Restricted at the application layer to rows with `type = STOCK_IN`. |
| `adjustment_type_code` | `String @db.VarChar` | Yes | Snapshot of the chosen reason code. |
| `doc_status` | `enum_doc_status` | No | `draft` (default), `in_progress`, `completed`, `cancelled`, `voided`. Posting fires on `in_progress → completed`. |
| `location_id` | `String @db.Uuid` | Yes | FK to `tb_location.id` — destination location for the inbound. |
| `location_code` | `String @db.VarChar` | Yes | Snapshot of the location code. |
| `location_name` | `String @db.VarChar` | Yes | Snapshot of the location name. |
| `workflow_id` | `String @db.Uuid` | Yes | Reference to the workflow definition (`tb_workflow`) governing this document. |
| `workflow_name` | `String @db.VarChar` | Yes | Snapshot of the workflow name. |
| `workflow_history` | `Json @db.JsonB` | Yes | Array of stage transitions: `[{stage, action, message, by: {id, name}, at}]`; default `{}`. |
| `workflow_current_stage` | `String @db.VarChar` | Yes | Current workflow stage name. |
| `workflow_previous_stage` | `String @db.VarChar` | Yes | Previous stage. |
| `workflow_next_stage` | `String @db.VarChar` | Yes | Next stage (computed by the workflow engine). |
| `user_action` | `Json @db.JsonB` | Yes | Execute list: `{execute: [{id: <user_uuid>}, ...]}`; default `{}`. The set of users authorised to fire the current-stage action. |
| `last_action` | `enum_last_action` | Yes | `submitted` (default), `approved`, `reviewed`, `rejected`. |
| `last_action_at_date` | `DateTime @db.Timestamptz(6)` | Yes | When the last action was taken. |
| `last_action_by_id` | `String @db.Uuid` | Yes | Actor id of the last action. |
| `last_action_by_name` | `String @db.VarChar` | Yes | Actor display-name snapshot. |
| `note` | `String @db.VarChar` | Yes | Free-text note. |
| `info` | `Json @db.JsonB` | Yes | Extension bag; default `{}`. Typical use: count-source reference (e.g. `{ countId: "<count_uuid>" }` for rollup documents). |
| `dimension` | `Json @db.JsonB` | Yes | Cost-dimension array; default `[]`. |
| `doc_version` | `Int @db.Integer` | No | Optimistic-concurrency counter; default `0`. |
| `created_at` | `DateTime @db.Timestamptz(6)` | Yes | Creation timestamp. |
| `created_by_id` | `String @db.Uuid` | Yes | Creator id (Store Keeper or Inventory Controller). |
| `updated_at` | `DateTime @db.Timestamptz(6)` | Yes | Last-update timestamp. |
| `updated_by_id` | `String @db.Uuid` | Yes | Updater id. |
| `deleted_at` | `DateTime @db.Timestamptz(6)` | Yes | Soft-delete timestamp. |
| `deleted_by_id` | `String @db.Uuid` | Yes | Soft-delete actor id. |

**Constraints:** `@id` on `id`. FKs: `adjustment_type_id → tb_adjustment_type.id` (`NoAction`); `location_id → tb_location.id` (`NoAction`). Back-relations: many `tb_stock_in_detail`, many `tb_stock_in_comment`.
**Indexes:** `@@unique([si_no, deleted_at])` as `SI1_si_no_u`; `@@index([si_no])` as `SI0_si_no_idx`.

### 2.3 tb_stock_in_detail

The **per-product detail line on a stock-in document**. One row per affected product line; carries `qty` (positive for inbound), `cost_per_unit`, `total_cost`, and the back-reference `inventory_transaction_id` that links to the [[inventory]] ledger row created at posting time. Comments and attachments per detail line hang off `tb_stock_in_detail_comment`.

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `inventory_transaction_id` | `String @db.Uuid` | Yes | FK to `tb_inventory_transaction.id` — populated at post (`completed`) only; null while `draft`. |
| `stock_in_id` | `String @db.Uuid` | No | FK to `tb_stock_in.id`. |
| `sequence_no` | `Int` | Yes | Line ordering within the document; default `1`. |
| `description` | `String @db.VarChar` | Yes | Free-text description for the line. |
| `comment` | `String @db.VarChar` | Yes | Free-text comment for the line. |
| `product_id` | `String @db.Uuid` | No | FK to `tb_product.id`. Required. |
| `product_code` | `String @db.VarChar` | Yes | Snapshot of the product code. |
| `product_name` | `String @db.VarChar` | Yes | Snapshot of the product name. |
| `product_local_name` | `String @db.VarChar` | Yes | Localised snapshot. |
| `product_sku` | `String @db.VarChar` | Yes | SKU snapshot. |
| `qty` | `Decimal @db.Decimal(20, 5)` | Yes | Inbound quantity in base UoM. Positive for stock-in by convention (the sign is applied on the inventory-side detail per [[inventory]] `INV_VAL_004`); default `0`. |
| `cost_per_unit` | `Decimal @db.Decimal(20, 5)` | Yes | Unit cost in base currency at the moment of posting; default `0`. User-entered for new lots (Controller approval required); auto-filled from the existing lot's most recent cost-layer for existing lots. |
| `total_cost` | `Decimal @db.Decimal(20, 5)` | Yes | `qty × cost_per_unit`; default `0`. |
| `note` | `String @db.VarChar` | Yes | Free-text note. |
| `info` | `Json @db.JsonB` | Yes | Extension bag; default `{}`. Typical use: `{ lotNo, expiryDate, isNewLot, evidenceAttachments: [...] }` mirroring the carmen/docs `AdjustmentItem` / `Lot` interfaces — see Section 5 item 3. |
| `dimension` | `Json @db.JsonB` | Yes | Cost-dimension array; default `[]`. |
| `doc_version` | `Int @db.Integer` | No | Optimistic-concurrency counter; default `0`. |
| `created_at` | `DateTime @db.Timestamptz(6)` | Yes | Creation timestamp. |
| `created_by_id` | `String @db.Uuid` | Yes | Creator id. |
| `updated_at` | `DateTime @db.Timestamptz(6)` | Yes | Last-update timestamp. |
| `updated_by_id` | `String @db.Uuid` | Yes | Updater id. |
| `deleted_at` | `DateTime @db.Timestamptz(6)` | Yes | Soft-delete timestamp. |
| `deleted_by_id` | `String @db.Uuid` | Yes | Soft-delete actor id. |

**Constraints:** `@id` on `id`. FKs: `inventory_transaction_id → tb_inventory_transaction.id` (`NoAction`); `product_id → tb_product.id` (`NoAction`); `stock_in_id → tb_stock_in.id` (`NoAction`). Back-relations: many `tb_stock_in_detail_comment`.
**Indexes:** `@@unique([stock_in_id, product_id, dimension, deleted_at])` as `SIT1_stock_in_product_dimension_u`; `@@index([stock_in_id, product_id])` as `SIT2_stock_in_product_idx`; `@@index([stock_in_id])` as `SIT2_stock_in_idx`.

### 2.4 tb_stock_in_comment

The **document-level comment / attachment** on a stock-in. Carries free-text `message` and an `attachments` JSON array of S3-token records (photo of damage, vendor RMA, count sheet scan). User-vs-system tagging via `enum_comment_type`.

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `stock_in_id` | `String @db.Uuid` | No | FK to `tb_stock_in.id`. |
| `type` | `enum_comment_type` | No | `user` (default) or `system`. |
| `user_id` | `String @db.Uuid` | Yes | User who left the comment. |
| `message` | `String` | Yes | Free-text comment body. |
| `attachments` | `Json @db.JsonB` | Yes | Array of `{originalName, fileToken, contentType}`; default `[]`. |
| `created_at` | `DateTime @db.Timestamptz(6)` | Yes | Creation timestamp. |
| `created_by_id` | `String @db.Uuid` | Yes | Creator id. |
| `updated_at` | `DateTime @db.Timestamptz(6)` | Yes | Last-update timestamp. |
| `updated_by_id` | `String @db.Uuid` | Yes | Updater id. |
| `deleted_at` | `DateTime @db.Timestamptz(6)` | Yes | Soft-delete timestamp. |
| `deleted_by_id` | `String @db.Uuid` | Yes | Soft-delete actor id. |

**Constraints:** `@id` on `id`. FK `stock_in_id → tb_stock_in.id` (`NoAction`).

### 2.5 tb_stock_in_detail_comment

The **line-level comment / attachment** on a stock-in detail row. Same shape as `tb_stock_in_comment` but anchored to a specific line — used for "photo of this specific item's damage" or "vendor RMA for this product".

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `stock_in_detail_id` | `String @db.Uuid` | No | FK to `tb_stock_in_detail.id`. |
| `type` | `enum_comment_type` | No | `user` (default) or `system`. |
| `user_id` | `String @db.Uuid` | Yes | User. |
| `message` | `String` | Yes | Free-text. |
| `attachments` | `Json @db.JsonB` | Yes | Array of attachment records; default `[]`. |
| `created_at` | `DateTime @db.Timestamptz(6)` | Yes | Creation timestamp. |
| `created_by_id` | `String @db.Uuid` | Yes | Creator id. |
| `updated_at` | `DateTime @db.Timestamptz(6)` | Yes | Last-update timestamp. |
| `updated_by_id` | `String @db.Uuid` | Yes | Updater id. |
| `deleted_at` | `DateTime @db.Timestamptz(6)` | Yes | Soft-delete timestamp. |
| `deleted_by_id` | `String @db.Uuid` | Yes | Soft-delete actor id. |

**Constraints:** `@id` on `id`. FK `stock_in_detail_id → tb_stock_in_detail.id` (`NoAction`).

### 2.6 tb_stock_out

The **outbound adjustment document header**. Mirror-image of `tb_stock_in` with `so_no` / `so_date` and `adjustment_type_id` restricted at the application layer to rows with `type = STOCK_OUT`. Identical workflow / status / audit fields; same comment / detail / detail-comment children.

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `so_date` | `DateTime @db.Timestamptz(6)` | Yes | Document date. |
| `so_no` | `String @db.VarChar` | Yes | Human-readable stock-out number; unique within `deleted_at`. |
| `description` | `String @db.VarChar` | Yes | Header-level description. |
| `adjustment_type_id` | `String @db.Uuid` | Yes | FK to `tb_adjustment_type.id` (`onDelete: NoAction`). Restricted application-side to rows with `type = STOCK_OUT`. |
| `adjustment_type_code` | `String @db.VarChar` | Yes | Snapshot. |
| `doc_status` | `enum_doc_status` | No | `draft` default; same lifecycle as stock-in. |
| `location_id` | `String @db.Uuid` | Yes | FK to `tb_location.id` — source location for the outbound. |
| `location_code` | `String @db.VarChar` | Yes | Snapshot. |
| `location_name` | `String @db.VarChar` | Yes | Snapshot. |
| `workflow_id` | `String @db.Uuid` | Yes | Workflow definition reference. |
| `workflow_name` | `String @db.VarChar` | Yes | Snapshot. |
| `workflow_history` | `Json @db.JsonB` | Yes | History array; default `{}`. |
| `workflow_current_stage` | `String @db.VarChar` | Yes | Current stage. |
| `workflow_previous_stage` | `String @db.VarChar` | Yes | Previous stage. |
| `workflow_next_stage` | `String @db.VarChar` | Yes | Next stage. |
| `user_action` | `Json @db.JsonB` | Yes | Execute list; default `{}`. |
| `last_action` | `enum_last_action` | Yes | Default `submitted`. |
| `last_action_at_date` | `DateTime @db.Timestamptz(6)` | Yes | When the last action was taken. |
| `last_action_by_id` | `String @db.Uuid` | Yes | Actor. |
| `last_action_by_name` | `String @db.VarChar` | Yes | Actor name snapshot. |
| `note` | `String @db.VarChar` | Yes | Free-text. |
| `info` | `Json @db.JsonB` | Yes | Extension bag. |
| `dimension` | `Json @db.JsonB` | Yes | Cost-dimension array. |
| `doc_version` | `Int @db.Integer` | No | Default `0`. |
| `created_at` | `DateTime @db.Timestamptz(6)` | Yes | Creation timestamp. |
| `created_by_id` | `String @db.Uuid` | Yes | Creator id. |
| `updated_at` | `DateTime @db.Timestamptz(6)` | Yes | Last-update timestamp. |
| `updated_by_id` | `String @db.Uuid` | Yes | Updater id. |
| `deleted_at` | `DateTime @db.Timestamptz(6)` | Yes | Soft-delete timestamp. |
| `deleted_by_id` | `String @db.Uuid` | Yes | Soft-delete actor id. |

**Constraints:** `@id` on `id`. FKs: `adjustment_type_id → tb_adjustment_type.id` (`NoAction`); `location_id → tb_location.id` (`NoAction`). Back-relations: many `tb_stock_out_detail`, many `tb_stock_out_comment`.
**Indexes:** `@@unique([so_no, deleted_at])` as `SO1_so_no_u`; `@@index([so_no])` as `SO0_so_no_idx`.

### 2.7 tb_stock_out_detail

The **per-product detail line on a stock-out document**. Mirror of `tb_stock_in_detail` with the cost-per-unit semantics inverted: on stock-out, `cost_per_unit` is typically **picked at post time by the costing engine** (FIFO from the oldest layer, or current weighted-average) per [[inventory]] `INV_CALC_005` / `INV_CALC_006` — the user-entered cost on the draft is a preview, not the authoritative final cost (which is resolved on the cost-layer ledger).

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `inventory_transaction_id` | `String @db.Uuid` | Yes | FK to `tb_inventory_transaction.id`; populated at post. |
| `stock_out_id` | `String @db.Uuid` | No | FK to `tb_stock_out.id`. |
| `sequence_no` | `Int` | Yes | Line ordering; default `1`. |
| `description` | `String @db.VarChar` | Yes | Free-text. |
| `comment` | `String @db.VarChar` | Yes | Free-text. |
| `product_id` | `String @db.Uuid` | No | FK to `tb_product.id`. |
| `product_code` | `String @db.VarChar` | Yes | Snapshot. |
| `product_name` | `String @db.VarChar` | Yes | Snapshot. |
| `product_local_name` | `String @db.VarChar` | Yes | Localised snapshot. |
| `product_sku` | `String @db.VarChar` | Yes | SKU snapshot. |
| `qty` | `Decimal @db.Decimal(20, 5)` | Yes | Outbound quantity (entered positive on the document; the inventory-side detail sign is negative per [[inventory]] `INV_VAL_004`); default `0`. |
| `cost_per_unit` | `Decimal @db.Decimal(20, 5)` | Yes | Cost-per-unit preview on the draft; final cost is picked at post time by the costing engine; default `0`. |
| `total_cost` | `Decimal @db.Decimal(20, 5)` | Yes | `qty × cost_per_unit`; default `0`. |
| `note` | `String @db.VarChar` | Yes | Free-text. |
| `info` | `Json @db.JsonB` | Yes | Extension bag; default `{}`. Typical use: lot-override pick (`{lotNo}` when user overrides FIFO default for expiry-write-off), evidence attachments. |
| `dimension` | `Json @db.JsonB` | Yes | Cost-dimension array; default `[]`. |
| `doc_version` | `Int @db.Integer` | No | Default `0`. |
| `created_at` | `DateTime @db.Timestamptz(6)` | Yes | Creation timestamp. |
| `created_by_id` | `String @db.Uuid` | Yes | Creator id. |
| `updated_at` | `DateTime @db.Timestamptz(6)` | Yes | Last-update timestamp. |
| `updated_by_id` | `String @db.Uuid` | Yes | Updater id. |
| `deleted_at` | `DateTime @db.Timestamptz(6)` | Yes | Soft-delete timestamp. |
| `deleted_by_id` | `String @db.Uuid` | Yes | Soft-delete actor id. |

**Constraints:** `@id` on `id`. FKs: `inventory_transaction_id → tb_inventory_transaction.id` (`NoAction`); `product_id → tb_product.id` (`NoAction`); `stock_out_id → tb_stock_out.id` (`NoAction`). Back-relations: many `tb_stock_out_detail_comment`.
**Indexes:** `@@unique([stock_out_id, product_id, dimension, deleted_at])` as `SOT1_stock_out_product_dimension_u`; `@@index([stock_out_id, product_id])` as `SOT2_stock_out_product_idx`; `@@index([stock_out_id])` as `SOT2_stock_out_idx`.

### 2.8 tb_stock_out_comment, tb_stock_out_detail_comment

Mirror of `tb_stock_in_comment` / `tb_stock_in_detail_comment` for the outbound document. Same column shape; FKs to `tb_stock_out.id` / `tb_stock_out_detail.id` respectively. Used for damage-photo attachment on write-off lines, recall-RMA references, count-shortage sign-off notes.

## 3. Relationships

```
tb_adjustment_type  (reason-code master — STOCK_IN or STOCK_OUT direction)
    │  enum_adjustment_type ∈ {STOCK_IN, STOCK_OUT}
    │
    ├─1──*──► tb_stock_in   (inbound adjustment document, doc_status lifecycle)
    │           │
    │           ├─1──*──► tb_stock_in_detail   (per-product line)
    │           │           │
    │           │           ├──► tb_inventory_transaction (inventory_transaction_id,
    │           │           │     populated at post — completed state)
    │           │           ├──► tb_product
    │           │           └─1──*──► tb_stock_in_detail_comment
    │           │
    │           ├─1──*──► tb_stock_in_comment (header attachments / messages)
    │           └──► tb_location  (location_id — destination of inbound)
    │
    └─1──*──► tb_stock_out  (outbound adjustment document, doc_status lifecycle)
                │
                ├─1──*──► tb_stock_out_detail   (per-product line)
                │           │
                │           ├──► tb_inventory_transaction (inventory_transaction_id)
                │           ├──► tb_product
                │           └─1──*──► tb_stock_out_detail_comment
                │
                ├─1──*──► tb_stock_out_comment
                └──► tb_location  (location_id — source of outbound)


At post (doc_status: in_progress → completed), each detail line writes
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

- **Two parallel document trees, one classifier.** `tb_stock_in` and `tb_stock_out` are independent Prisma models with the same shape; the `tb_adjustment_type` row's `type` column gates which document tree a given reason-code can be used on. There is no shared `tb_inventory_adjustment` parent — joining the inbound and outbound activity for reporting is a `UNION` at the application / read-model layer (typically off the `tb_inventory_transaction` row, which is shared).
- **Inventory-transaction back-reference is the integration anchor.** Each detail row carries `inventory_transaction_id` as a **nullable** FK populated only at posting (`completed` state). While `draft` / `in_progress`, the column is null and no inventory effect exists. This mirrors the `tb_good_received_note_detail_item.inventory_transaction_id` pattern in [[good-receive-note]] and the same pattern in [[store-requisition]] detail.
- **Lot data not on the adjustment detail.** The detail row's `info` JSON typically carries `{lotNo, expiryDate}` for the draft / user-facing view, but the canonical lot identity persists on the inventory side (`tb_inventory_transaction_detail.current_lot_no` / `from_lot_no` and `tb_inventory_transaction_cost_layer.lot_no` / `lot_index`). This is the same divergence pattern called out in [[good-receive-note]] data-model § 5 item 3 and [[inventory]] data-model § 5 item 11.
- **Adjustment type is restricted by direction.** While the Prisma model `tb_stock_in.adjustment_type_id` and `tb_stock_out.adjustment_type_id` are both untyped FKs to `tb_adjustment_type`, the application layer filters the picker so a `tb_stock_in` document can only reference an `adjustment_type` row with `type = STOCK_IN` (and vice versa). This is the source of the carmen/docs `AdjustmentReason.type: 'IN' | 'OUT' | 'BOTH'` interface — see Section 5 item 1.
- **`adjustment_type_code` is a snapshot, not a live join.** Both documents persist the snapshot code on the header for performance and audit; deleting / renaming the reason code after posting does not retroactively change the historical document.
- **All explicit `@relation` FK declarations use `onDelete: NoAction, onUpdate: NoAction`** — referential integrity is preserved by application-level soft-delete (`deleted_at`) and by the doc-status / posting guard, not by cascade.

## 4. Enums

- **`enum_adjustment_type`**: direction classifier on `tb_adjustment_type.type`. Two values, no default declared (every reason code must specify direction):
  - `STOCK_IN` — inbound / write-on reasons. Filters into `tb_stock_in` reason-picker. Typical codes: `FOUND_STOCK`, `COUNT_OVERAGE`, `RECALL_REPLACEMENT`, `VENDOR_FREE_REPLACEMENT`, `DATA_FIX`.
  - `STOCK_OUT` — outbound / write-off reasons. Filters into `tb_stock_out` reason-picker. Typical codes: `BREAKAGE`, `EXPIRY_WRITE_OFF`, `THEFT_WRITE_OFF`, `COUNT_SHORTAGE`, `RECALL_WRITE_OFF`.
- **`enum_doc_status`**: document lifecycle on `tb_stock_in.doc_status` / `tb_stock_out.doc_status`. Default `draft`. Five values:
  - `draft` — editable, no inventory effect; document deletable.
  - `in_progress` — submitted for approval; in the Inventory Controller's queue (above threshold) or auto-advancing (below threshold).
  - `completed` — terminal active state; posting has fired; one `tb_inventory_transaction` row exists per detail line; document is immutable.
  - `cancelled` — terminal inactive; user / approver cancelled before posting; no inventory effect.
  - `voided` — terminal inactive; document voided after the fact; if posted, a compensating inventory transaction is required (the original ledger entry is not edited per [[inventory]] `INV_POST_012`).
- **`enum_last_action`**: workflow last-action classifier on `tb_stock_in.last_action` / `tb_stock_out.last_action`. Default `submitted`. Four values: `submitted`, `approved`, `reviewed`, `rejected`. Drives the workflow-history rendering and reviewer routing.
- **`enum_comment_type`**: on `tb_stock_in_comment.type` / `tb_stock_in_detail_comment.type` / `tb_stock_out_comment.type` / `tb_stock_out_detail_comment.type`. Default `user`. Two values: `user` (user-authored), `system` (system-generated, e.g. status-transition notes, evidence-required reminders).

## 5. Divergences from carmen/docs

The carmen/docs Inventory Adjustment set (`INV-ADJ-PRD.md`, `INV-ADJ-Business-Requirements.md`, `INV-ADJ-Business-Logic.md`, `INV-ADJ-Component-Structure.md`, `INV-ADJ-Overview.md`) describes an interface model centred on a single `InventoryAdjustment` entity with embedded `items[]`, `lots[]`, `journal entries`, and a three-state lifecycle (`Draft → Posted → Void`). Cross-checking against the canonical Prisma schema yields the following divergences:

| # | Item | carmen/docs says | Prisma has | Action |
|---|------|------------------|------------|--------|
| 1 | Single `InventoryAdjustment` entity | `interface InventoryAdjustment { id, date, type: 'IN' | 'OUT', status: 'Draft' | 'Posted' | 'Void', location, reason, items: StockMovementItem[], totals: {inQty, outQty, totalCost}, ... }` — single-table model with a `type` discriminator. | **Two parallel tables** — `tb_stock_in` (inbound) and `tb_stock_out` (outbound) — with the same column shape but no shared `tb_inventory_adjustment` parent. The `type` discriminator lives on `tb_adjustment_type` (via `enum_adjustment_type`), not on the document header. | Treat Prisma as canonical. Update carmen/docs to describe the two-table model; the `InventoryAdjustment` interface is a read-model union of stock-in and stock-out rows. The `totals.inQty / outQty / totalCost` is an application-derived roll-up (sum of `tb_stock_in_detail.qty × cost_per_unit` and the parallel `tb_stock_out_detail` sum), not a persisted header column. |
| 2 | `AdjustmentReason.type: 'IN' | 'OUT' | 'BOTH'` | `interface AdjustmentReason { id, code, description, type: 'IN' | 'OUT' | 'BOTH', requiresDocument, requiresQualityCheck, glAccount, isActive, ... }` — three values for the direction-filter, plus `requiresDocument`, `requiresQualityCheck`, `glAccount` as first-class fields. | `tb_adjustment_type.type` is the enum `enum_adjustment_type` with **only two values**: `STOCK_IN` and `STOCK_OUT`. `BOTH` is not a schema value — a reason code that is usable on both directions must be defined twice (one row per direction). `requiresDocument`, `requiresQualityCheck`, `glAccount` are **not Prisma columns**; if used, they live in `info` JSON (typical key names `requiresDocument: boolean`, `requiresQualityCheck: boolean`, `glAccount: string`). | Document the two-value enum reality. The `BOTH` direction needs a two-row registration pattern in seed data. Move `glAccount` and the flag fields into a documented `info`-JSON contract (or propose a schema change to promote them to columns). |
| 3 | `AdjustmentItem` with `lots: Lot[]` embedded array | `interface StockMovementItem { id, productName, sku, location, lots: Lot[], uom, unitCost, totalCost, currentStock, adjustedStock }`; `interface Lot { lotNo, quantity, uom, expiryDate? }` — embedded lot array per item, with `currentStock` / `adjustedStock` previews. | `tb_stock_in_detail` / `tb_stock_out_detail` has **no embedded `lots` array**. Lot data persists on the inventory-transaction side: `current_lot_no` / `from_lot_no` on `tb_inventory_transaction_detail` (one line per inventory effect; multiple lots ⇒ multiple cost-layer rows under one detail) and `lot_no` / `lot_index` on `tb_inventory_transaction_cost_layer`. The draft / user-facing view typically carries lot info in `info` JSON on the detail; the canonical persistence is on the inventory side. `currentStock` / `adjustedStock` are derived (not persisted). | Treat the lot array as a draft / UI concern; the canonical lot identity is on the inventory side. Document `info` JSON shape for draft lot entry. `currentStock` / `adjustedStock` are read-model values computed against `tb_inventory_transaction_cost_layer`. Mirror the [[good-receive-note]] § 5 item 3 framing. |
| 4 | Three-state lifecycle `Draft → Posted → Void` | `interface InventoryAdjustment.status: 'Draft' | 'Posted' | 'Void'` — three discrete states with `Draft` being editable, `Posted` being immutable terminal, `Void` reversing a posted adjustment. | `tb_stock_in.doc_status` / `tb_stock_out.doc_status` is **five values**: `draft`, `in_progress`, `completed`, `cancelled`, `voided` (the shared `enum_doc_status`). `completed` is the "posted" equivalent (terminal active, inventory transaction written); `voided` is the post-fact-void state; `cancelled` is the additional state for documents cancelled before posting. `in_progress` is the explicit workflow state between `draft` and `completed` that carmen/docs collapses into `Draft`. | Update carmen/docs to describe the five-state lifecycle. The `Draft → Posted` transition in carmen/docs is actually `draft → in_progress → completed`; the `Posted → Void` transition is `completed → voided` with the constraint that a compensating inventory transaction must be posted first per [[inventory]] `INV_POST_012` / `INV_VAL_013`. The pre-post `cancelled` state is the equivalent of "abandon draft" and has no carmen/docs counterpart. |
| 5 | Embedded `journalEntries: JournalEntry[]` on the adjustment | `interface JournalEntry { id, account, accountName, debit, credit, department, reference }` — embedded journal-entry array on the `InventoryAdjustment` interface. | No `tb_journal_entry` model in the canonical Prisma schema for tenant. Journal entries are produced at posting time by the application-layer GL-mapping engine, read from the adjustment-type's `info.glAccount` and the affected location's cost-centre, and **emitted to the GL ledger** (Finance subsystem) — not persisted on the adjustment row. The adjustment-side audit trail of the journal-entry effect is reconstructed from the `tb_inventory_transaction_cost_layer.total_cost` + `diff_amount` for the matching `inventory_doc_type = stock_in / stock_out`. | Document journal entries as a downstream artefact, not an embedded array. The Finance read-model joins the inventory transaction → cost-layer ledger to the GL journal-entry table (outside this schema). The `JournalEntry` interface is a Finance-module concern, not an Inventory Adjustment column. |
| 6 | Document numbering — `Adjustment.id` is "reference number" | "Each adjustment must have a unique reference number" (ADJ_CRT_001), implicitly using `id`. | `id` is the UUID primary key (`gen_random_uuid()`). The **human-readable reference number** is `si_no` on `tb_stock_in` and `so_no` on `tb_stock_out`, each unique within `deleted_at`. Two parallel sequence-streams; the application layer typically generates `SI-YYMM-NNNNN` and `SO-YYMM-NNNNN` patterns. | Update carmen/docs to distinguish UUID `id` from human-readable `si_no` / `so_no`. The "reference number" maps to `si_no` / `so_no`, not `id`. |
| 7 | `Department` field on the adjustment | "Department code is mandatory" (ADJ_CRT_009) — `interface InventoryAdjustment.department: string`. | **No `department_id` column** on `tb_stock_in` or `tb_stock_out`. Department / cost-centre information is carried via `dimension` JSON on the header (and propagated to the inventory-transaction `dimension`). The dimension array shape is `[{type: "department", id: "<uuid>", code: "DEPT-A"}, ...]`. | Update carmen/docs to describe `dimension` JSON as the department / cost-centre carrier. The "mandatory department" rule is enforced at the application layer reading `dimension`. |
| 8 | "Supporting documents must be attached" (ADJ_CRT_008) | Implies a document-attachment array on the adjustment header. | Attachments live on `tb_stock_in_comment` / `tb_stock_in_detail_comment` (and parallel stock-out tables) as the `attachments` JSON array on a comment row. There is no dedicated `tb_attachment` table for the adjustment header — the comment row is the carrier, with `message` optional and `attachments` carrying `[{originalName, fileToken, contentType}]`. | Document the comment-as-attachment-carrier pattern. The "supporting documents required" rule is enforced by the application checking at-least-one comment row with non-empty `attachments` when the adjustment-type's `info.requiresDocument = true`. |
| 9 | "Total cost must match sum of item costs" (ADJ_VAL_005) | Implies header `totals.totalCost` is a persisted column reconciled against `Σ items[].totalCost`. | **No `total_cost` header column** on `tb_stock_in` or `tb_stock_out`. The header carries no roll-up; total cost is a derived sum over `tb_stock_in_detail.total_cost` (or the parallel stock-out detail). The "matches" rule is degenerate — there is no header value to match against; the application-layer read-model is always the sum of the details. | Drop the "match" framing; the header has no totals. The rule reduces to the per-line `total_cost = qty × cost_per_unit` (the standard line calculation rule, captured under `INV_CALC_001`). |
| 10 | Adjustment "Date" semantics | "Adjustment date must be within open accounting periods" (ADJ_CRT_010). | The relevant date is `tb_stock_in.si_date` / `tb_stock_out.so_date` (or the inventory transaction's `created_at` if `si_date` / `so_date` is null at post time). The period-containment check runs against this date per [[inventory]] `INV_VAL_008`. | Document that the period gate uses `si_date` / `so_date` (or `created_at` as fallback). The check applies on the `in_progress → completed` transition, not at draft creation. |
| 11 | "Lot quantities must not exceed available balance" (ADJ_VAL_004) | Implied to run on the adjustment detail. | This is enforced on the inventory-side at post time per [[inventory]] `INV_VAL_005` (no negative balance at `(location, product, lot_no, lot_index)`). The adjustment document detail does not store available-balance — it is read live from the cost-layer ledger. | Document the rule as inventory-side enforced; the adjustment document is the entry point but the validation belongs to the ledger. |
| 12 | "Real-time stock validation" (ADJ_PRC_010) | Implies live balance validation throughout the draft. | Live validation runs at submit (`in_progress` transition) per [[inventory]] `INV_VAL_005`; during `draft`, the UI may show a balance preview but the authoritative rejection happens only at submit. The post-time check is the one that matters because between draft creation and submit, balance can change (other postings landing). | Clarify that validation is at submit, not continuous; the draft view is a snapshot, not a live guard. |

## 6. References

- **Primary (source of truth):** Prisma schemas listed in the header callout — concretely `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` (eight entities: `tb_adjustment_type`, `tb_stock_in`, `tb_stock_in_detail`, `tb_stock_in_comment`, `tb_stock_in_detail_comment`, `tb_stock_out`, `tb_stock_out_detail`, `tb_stock_out_comment`, `tb_stock_out_detail_comment`; four enums: `enum_adjustment_type`, `enum_doc_status`, `enum_last_action`, `enum_comment_type`) and `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` (verified to contain no inventory-adjustment models).
- **Secondary (concept cross-check):**
  - `../carmen/docs/inventory-adjustment/INV-ADJ-Overview.md` — module introduction and key features; divergence § 5 items 4 (lifecycle), 7 (department), 8 (attachments).
  - `../carmen/docs/inventory-adjustment/INV-ADJ-PRD.md` — Product Requirements; divergence § 5 items 1 (single entity), 5 (journal entries), 6 (reference number).
  - `../carmen/docs/inventory-adjustment/INV-ADJ-Business-Requirements.md` — business rules catalogue (ADJ_CRT_*, ADJ_VAL_*, ADJ_PRC_*, ADJ_UI_*, ADJ_CALC_*); the source of the rule IDs realigned in [[inventory-adjustment/02-business-rules]] and the `InventoryAdjustment` / `AdjustmentReason` / `StockMovementItem` / `Lot` / `JournalEntry` TypeScript interfaces that ground § 5.
  - `../carmen/docs/inventory-adjustment/INV-ADJ-Business-Logic.md` — process flows for receive / issue / transfer / adjust / vendor-return; the FIFO / weighted-average framing applied to adjustments in § 5 (via [[costing]] / [[inventory]]).
  - `../carmen/docs/inventory-adjustment/INV-ADJ-Component-Structure.md` — component hierarchy (`InventoryAdjustmentList`, `InventoryAdjustmentDetail`, `InventoryAdjustmentForm`, `LotSelectionDialog`, `JournalEntryViewer`); referenced for the UI-side data shape that drives `info` JSON contract (lot draft, attachments).
  - E2E: `../carmen-inventory-frontend-e2e/tests/031-adjustment-type.spec.ts` — adjustment-type (reason-code) admin CRUD, the master-data side of the module.
- Related modules: [[inventory]] (the canonical ledger that adjustment posts write to — `tb_inventory_transaction` / `tb_inventory_transaction_detail` / `tb_inventory_transaction_cost_layer`, with `enum_inventory_doc_type ∈ {stock_in, stock_out}` and `enum_transaction_type ∈ {adjustment_in, adjustment_out}`), [[costing]] (FIFO layer creation on inbound adjustment, FIFO consumption / WA refresh on outbound), [[physical-count]] (variance rollup posts as adjustments per `INV_XMOD_003`), [[spot-check]] (partial-count variance posts as adjustments per `INV_XMOD_004`), [[good-receive-note]] (parallel data-model pattern for `inventory_transaction_id` linkage and lot-data-on-inventory-side framing), [[product]] (carries `costing_method` that gates outbound cost-pick on stock-out posting).

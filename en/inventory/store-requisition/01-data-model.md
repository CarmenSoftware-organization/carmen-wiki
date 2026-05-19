---
title: Store Requisition — Data Model
description: Entities, fields, relationships, and enums for the store-requisition module.
published: true
date: 2026-05-19T23:55:00.000Z
tags: store-requisition, data-model, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T13:30:00.000Z
---

# Store Requisition — Data Model

> **At a Glance**
> **Tables:** `tb_store_requisition` &nbsp;·&nbsp; `tb_store_requisition_detail` &nbsp;·&nbsp; `tb_store_requisition_comment` &nbsp;·&nbsp; `tb_store_requisition_detail_comment`
> **Audience:** Developer / Auditor (dev reference)
> **Key FKs:** header `→ tb_location` ×2 (`from_location_id` + `to_location_id`, named relations) and `→ tb_workflow` (explicit `@relation`, unlike PR/PO/GRN); detail `→ tb_product` and `→ tb_inventory_transaction` (populated at commit — canonical lot / cost / expiry data lives on the inventory side)
> **Audit pattern:** standard `created_*` / `updated_*` / `deleted_*`; three-qty per line (`requested` / `approved` / `issued`); per-line approval / review / reject signature columns; **no monetary roll-ups on header** (SR is a qty document)

> **Source of truth:** Backend Prisma schema. Always read these first when writing or updating this page:
> - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma`
> - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma`
>
> The `generated/client/schema.prisma` files under each package are auto-generated copies and not authoritative.

## 1. Overview

The store-requisition module owns four tenant-schema entities: the SR document header (`tb_store_requisition`), its line items (`tb_store_requisition_detail`), and matching workflow / activity-log comment tables at both header and line level (`tb_store_requisition_comment`, `tb_store_requisition_detail_comment`). Workflow stage tracking is not a dedicated table — the JSON columns on the header (`workflow_history`, `workflow_current_stage`, `workflow_previous_stage`, `workflow_next_stage`, `user_action`) plus the comment tables together form the persistent record of the workflow timeline; the shared `tb_workflow` configuration is referenced through an explicit Prisma `@relation` on `workflow_id`. There is no separate `tb_store_requisition_workflow` table — `enum_inventory_doc_type` lists `store_requisition` as one of the seven document types that drive stock-movement journal entries, but the SR document status itself reuses the shared `enum_doc_status` (`draft / in_progress / completed / cancelled / voided`), not a dedicated SR enum.

The SR sits **between [inventory](/en/inventory/inventory) and the consuming-cost-centre side of the world**. The source location (`from_location_id` → `tb_location`) is typically a central store or warehouse; the destination location (`to_location_id` → `tb_location`) is the consuming outlet (kitchen, bar, banquet) — its `tb_location.location_type` (`direct` for cost-centre consumption, `inventory` for an onward inventory holding) is what gates the allowed `sr_type`: `enum_sr_type.issue` requires a direct-cost destination, `enum_sr_type.transfer` requires an inventory destination. On commit (`in_progress → completed`), the SR's downstream effects fan out: every line writes — through `tb_store_requisition_detail.inventory_transaction_id` — into `tb_inventory_transaction` / `tb_inventory_transaction_detail`, which is where the actual stock-OUT (and, for `transfer`, the paired stock-IN at destination) is recorded along with lot, expiry, and cost-layer data; the `[costing](/en/inventory/costing)` module is responsible for the per-line unit cost (source location's weighted-average or FIFO); and the SR header transitions `draft → in_progress → completed` (with `cancelled` and `voided` as the two terminal cancellation paths).

A noteworthy structural point: the SR line model carries **three quantities per row** — `requested_qty`, `approved_qty`, `issued_qty` (all `Decimal(20, 5)`) — which together tell the whole story across the four-state lifecycle. `requested_qty` is what the requester asked for; `approved_qty` is what the approver authorised (`≤ requested_qty`); `issued_qty` is what the store keeper actually released at fulfilment (`≤ approved_qty`). Unlike GRN's `detail_item` event-row split, an SR line is a single row whose three columns mutate as the document moves through its lifecycle — there is no nested event table. Per-line approval / review / rejection signatures (`approved_by_id`, `review_by_id`, `reject_by_id` and matching name / date / message columns) are persisted directly on the line for audit, alongside a `history` JSON array of stage-by-stage actor + decision entries and a `stages_status` JSON object summarising current per-stage status. The carmen/docs PRD describes a 6-state lifecycle (`Draft → Submitted → UnderReview → Approved/PartiallyApproved → InProcess → Fulfilled → Completed`) and a `RequisitionItem.approvalStatus` enum (`Accept / Reject / Review`) — both differ from the canonical Prisma 5-state `enum_doc_status` and the absence of a per-line status enum. See Section 5.

## 2. Entities

### 2.1 tb_store_requisition

SR document header. Carries reference number, dates, source / destination locations, movement type, workflow snapshot, requestor / department context, header dimension (cost-centre / project / job), and the standard audit columns. One header has many detail rows and many comments.

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key, generated via `gen_random_uuid()`. |
| `sr_no` | `String @db.VarChar` | No | Human-readable SR reference number. Required (note: GRN's equivalent is nullable; SR is not). |
| `sr_date` | `DateTime @db.Timestamptz(6)` | Yes | The requisition date — when the outlet raised the request. |
| `expected_date` | `DateTime @db.Timestamptz(6)` | Yes | The date the outlet needs the goods by. Used for fulfilment prioritisation. |
| `description` | `String @db.VarChar` | Yes | Free-text description on the header. |
| `doc_status` | `enum_doc_status` | No | Document status; default `draft`. Shared 5-value enum (see Section 4). |
| `from_location_id` | `String @db.Uuid` | Yes | FK to `tb_location.id` — the source location (warehouse / main store releasing the stock). Named relation `store_requisition_from_location`. Nullable on early drafts. |
| `from_location_code` | `String @db.VarChar` | Yes | Snapshot of source location code. |
| `from_location_name` | `String @db.VarChar` | Yes | Snapshot of source location name. |
| `to_location_id` | `String @db.Uuid` | Yes | FK to `tb_location.id` — the destination location (consuming outlet or onward inventory store). Named relation `store_requisition_to_location`. Nullable on early drafts. |
| `to_location_code` | `String @db.VarChar` | Yes | Snapshot of destination location code. |
| `to_location_name` | `String @db.VarChar` | Yes | Snapshot of destination location name. |
| `sr_type` | `enum_sr_type` | No | Movement type; default `transfer`. Either `issue` (consumption to a direct-cost destination) or `transfer` (inventory location-to-location). |
| `workflow_id` | `String @db.Uuid` | Yes | FK to `tb_workflow.id` via the named relation `workflow`. Unlike the GRN module, the SR header **does** declare an explicit Prisma `@relation` on `workflow_id`. |
| `workflow_name` | `String @db.VarChar` | Yes | Snapshot of the workflow name. |
| `workflow_history` | `Json @db.JsonB` | Yes | Append-only stage-transition timeline; default `{}`. Entries hold `stage`, `action`, `message`, `by` (`{id, name}`), `at`. |
| `workflow_current_stage` | `String @db.VarChar` | Yes | Slug of the stage currently holding the SR. |
| `workflow_previous_stage` | `String @db.VarChar` | Yes | Slug of the stage that just released the SR. |
| `workflow_next_stage` | `String @db.VarChar` | Yes | Slug of the next stage in the chain. |
| `user_action` | `Json @db.JsonB` | Yes | Pending-action metadata, default `{}`. Typically `{ "execute": [{ "id": "<user-id>" }, ...] }`. |
| `last_action` | `enum_last_action` | Yes | Last action taken on the document; default `submitted`. |
| `last_action_at_date` | `DateTime @db.Timestamptz(6)` | Yes | Timestamp of `last_action`. |
| `last_action_by_id` | `String @db.Uuid` | Yes | User id who performed `last_action`. |
| `last_action_by_name` | `String @db.VarChar` | Yes | Snapshot of the actor's name. |
| `requestor_id` | `String @db.Uuid` | Yes | User id of the requester (outlet manager who raised the SR). No Prisma `@relation` declared. |
| `requestor_name` | `String @db.VarChar` | Yes | Snapshot of the requester's display name. |
| `department_id` | `String @db.Uuid` | Yes | Department id of the requesting outlet. No Prisma `@relation` declared. |
| `department_name` | `String @db.VarChar` | Yes | Snapshot of the department name. |
| `info` | `Json @db.JsonB` | Yes | Extension bag for tenant-specific header attributes; default `{}`. |
| `dimension` | `Json @db.JsonB` | Yes | Cost-dimension array (project, cost-centre, job code, etc.); default `[]`. |
| `doc_version` | `Int @db.Integer` | No | Optimistic-concurrency version counter; default `0`. |
| `created_at` | `DateTime @db.Timestamptz(6)` | Yes | Creation timestamp; defaults to `now()`. |
| `created_by_id` | `String @db.Uuid` | Yes | User id who created the row. |
| `updated_at` | `DateTime @db.Timestamptz(6)` | Yes | Last-update timestamp; defaults to `now()`. |
| `updated_by_id` | `String @db.Uuid` | Yes | User id who last updated the row. |
| `deleted_at` | `DateTime @db.Timestamptz(6)` | Yes | Soft-delete timestamp; non-null means logically deleted. |

**Constraints:** `@id` on `id`. FKs: `from_location_id → tb_location.id` (`NoAction`, named relation `store_requisition_from_location`); `to_location_id → tb_location.id` (`NoAction`, named relation `store_requisition_to_location`); `workflow_id → tb_workflow.id` (`NoAction`). Note: `requestor_id` and `department_id` are stored as UUIDs but have no Prisma `@relation` on this model — they are application-resolved. Back-relations: many `tb_store_requisition_detail`, many `tb_store_requisition_comment`.
**Indexes:** `@@unique([sr_no, deleted_at])` as `sr_no_u`; `@@index([sr_no])` as `sr_no_idx`; `@@index([sr_type])` as `sr_type_idx`. Unlike GRN's `grn_no` (nullable), `sr_no` is `NOT NULL`.

### 2.2 tb_store_requisition_comment

Workflow / activity-log entries attached to an SR header. There is no dedicated `tb_store_requisition_workflow` table — this comment table, combined with the JSON workflow columns on the header, is the persistent record of the workflow timeline. Each row is either a user comment (`type = user`) or a system event (`type = system`) such as a stage transition.

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `store_requisition_id` | `String @db.Uuid` | No | FK to `tb_store_requisition.id`. |
| `type` | `enum_comment_type` | No | `user` or `system`; default `user`. |
| `user_id` | `String @db.Uuid` | Yes | Author user id (null for `system` entries). |
| `message` | `String` | Yes | Free-text comment body. |
| `attachments` | `Json @db.JsonB` | Yes | Array of `{ originalName, fileToken, contentType }`; default `[]`. |
| `created_at` | `DateTime @db.Timestamptz(6)` | Yes | Creation timestamp. |
| `created_by_id` | `String @db.Uuid` | Yes | Creator id. |
| `updated_at` | `DateTime @db.Timestamptz(6)` | Yes | Last-update timestamp. |
| `updated_by_id` | `String @db.Uuid` | Yes | Updater id. |
| `deleted_at` | `DateTime @db.Timestamptz(6)` | Yes | Soft-delete timestamp. |
| `deleted_by_id` | `String @db.Uuid` | Yes | Soft-delete actor id. |

**Constraints:** `@id` on `id`. FK `store_requisition_id → tb_store_requisition.id` (`NoAction` on delete/update).
**Indexes:** None declared beyond the primary key.

### 2.3 tb_store_requisition_detail

SR line item. Identifies the product being requisitioned and carries the three-quantity story (`requested_qty / approved_qty / issued_qty`) plus per-line approval / review / rejection signatures, a per-line `history` JSON timeline, and the link to the inventory transaction that records the actual stock movement on commit. Note: unlike GRN, an SR line is a **single row** for the whole lifecycle — there is no `detail_item` event-row split; the row's columns mutate as the document moves from `draft → in_progress → completed`.

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `inventory_transaction_id` | `String @db.Uuid` | Yes | FK to `tb_inventory_transaction.id` (Prisma `@relation` declared). Populated on commit (`in_progress → completed`); the linked row's `tb_inventory_transaction_detail` children hold `lot_no`, `expiry_date`, and `cost_per_unit`. |
| `store_requisition_id` | `String @db.Uuid` | No | FK to `tb_store_requisition.id`. |
| `sequence_no` | `Int` | Yes | Line ordering within the SR; default `1`. |
| `description` | `String @db.VarChar` | Yes | Free-text line description. |
| `comment` | `String @db.VarChar` | Yes | Free-text comment on this line (separate from the `_detail_comment` table). |
| `product_id` | `String @db.Uuid` | No | FK to `tb_product.id`. Required. |
| `product_code` | `String @db.VarChar` | Yes | Snapshot of product code. |
| `product_name` | `String @db.VarChar` | Yes | Snapshot of product name. |
| `product_local_name` | `String @db.VarChar` | Yes | Localised product name snapshot. |
| `product_sku` | `String @db.VarChar` | Yes | Snapshot of SKU. |
| `requested_qty` | `Decimal @db.Decimal(20, 5)` | Yes | Quantity the outlet asked for; default `0`. Set on `draft`; locked at submit. |
| `approved_qty` | `Decimal @db.Decimal(20, 5)` | Yes | Quantity the approver authorised; default `0`. `approved_qty ≤ requested_qty`. Set during approval; locked at issue. |
| `issued_qty` | `Decimal @db.Decimal(20, 5)` | Yes | Quantity the store keeper actually released at fulfilment; default `0`. `issued_qty ≤ approved_qty`. Set on commit. |
| `last_action` | `enum_last_action` | Yes | Most recent action on the line; default `submitted`. |
| `approved_message` | `String @db.VarChar` | Yes | Free-text approver note. |
| `approved_by_id` | `String @db.Uuid` | Yes | User id who approved the line. |
| `approved_by_name` | `String @db.VarChar` | Yes | Snapshot of approver name. |
| `approved_date_at` | `DateTime @db.Timestamptz(6)` | Yes | Approval timestamp. |
| `review_message` | `String @db.VarChar` | Yes | Free-text reviewer note (for send-back-for-correction). |
| `review_by_id` | `String @db.Uuid` | Yes | User id who reviewed the line. |
| `review_by_name` | `String @db.VarChar` | Yes | Snapshot of reviewer name. |
| `review_date_at` | `DateTime @db.Timestamptz(6)` | Yes | Review timestamp. |
| `reject_message` | `String @db.VarChar` | Yes | Mandatory reason text on rejection. |
| `reject_by_id` | `String @db.Uuid` | Yes | User id who rejected the line. |
| `reject_by_name` | `String @db.VarChar` | Yes | Snapshot of rejecter name. |
| `reject_date_at` | `DateTime @db.Timestamptz(6)` | Yes | Rejection timestamp. |
| `history` | `Json @db.JsonB` | Yes | Append-only per-line stage-by-stage action log; default `[]`. Each entry: `{ seq, name, status, message, to_stage?, by_id, by_name, at_date }`. |
| `stages_status` | `Json @db.JsonB` | Yes | Per-stage status snapshot; default `{}`. Each entry: `{ seq, name, status }`. |
| `current_stage_status` | `String @db.VarChar` | Yes | Temp field storing current stage status string. |
| `info` | `Json @db.JsonB` | Yes | Extension bag for tenant-specific line attributes; default `{}`. |
| `dimension` | `Json @db.JsonB` | Yes | Cost-dimension array (project, cost-centre, job code); default `[]`. Used in the unique index. |
| `doc_version` | `Int @db.Integer` | No | Optimistic-concurrency version counter; default `0`. |
| `created_at` | `DateTime @db.Timestamptz(6)` | Yes | Creation timestamp. |
| `created_by_id` | `String @db.Uuid` | Yes | Creator id. |
| `updated_at` | `DateTime @db.Timestamptz(6)` | Yes | Last-update timestamp. |
| `updated_by_id` | `String @db.Uuid` | Yes | Updater id. |
| `deleted_at` | `DateTime @db.Timestamptz(6)` | Yes | Soft-delete timestamp. |
| `deleted_by_id` | `String @db.Uuid` | Yes | Soft-delete actor id. |

**Constraints:** `@id` on `id`. FKs: `store_requisition_id → tb_store_requisition.id` (`NoAction`); `product_id → tb_product.id` (`NoAction`); `inventory_transaction_id → tb_inventory_transaction.id` (`NoAction`, nullable). Back-relations: many `tb_store_requisition_detail_comment`.
**Indexes:** `@@unique([store_requisition_id, product_id, dimension, deleted_at])` as `SRT1_store_requisition_product_location_dimension_u` — a single product+cost-dimension can only appear once on a non-soft-deleted SR; soft-deleted rows free the slot. `@@index([store_requisition_id, product_id])` as `SRT2_store_requisition_product_location_idx`.

### 2.4 tb_store_requisition_detail_comment

Line-level counterpart of `tb_store_requisition_comment`. Captures comments and system events attached to a single SR line — typically used during approval to record per-line decisions (with `approved_message` / `review_message` / `reject_message` carrying the formal signature on the line itself) and during issue to log fulfilment decisions.

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `store_requisition_detail_id` | `String @db.Uuid` | No | FK to `tb_store_requisition_detail.id`. |
| `type` | `enum_comment_type` | No | `user` or `system`; default `user`. |
| `user_id` | `String @db.Uuid` | Yes | Author user id (null for `system` entries). |
| `message` | `String` | Yes | Free-text comment body. |
| `attachments` | `Json @db.JsonB` | Yes | Array of attachments; default `[]`. |
| `created_at` | `DateTime @db.Timestamptz(6)` | Yes | Creation timestamp. |
| `created_by_id` | `String @db.Uuid` | Yes | Creator id. |
| `updated_at` | `DateTime @db.Timestamptz(6)` | Yes | Last-update timestamp. |
| `updated_by_id` | `String @db.Uuid` | Yes | Updater id. |
| `deleted_at` | `DateTime @db.Timestamptz(6)` | Yes | Soft-delete timestamp. |
| `deleted_by_id` | `String @db.Uuid` | Yes | Soft-delete actor id. |

**Constraints:** `@id` on `id`. FK `store_requisition_detail_id → tb_store_requisition_detail.id` (`NoAction` on delete/update).
**Indexes:** None declared beyond the primary key.

## 3. Relationships

```
tb_workflow
    │  (workflow_id stored with an explicit Prisma @relation on tb_store_requisition,
    │   unlike PR / PO / GRN where the workflow link is application-resolved only)
    ▼
tb_store_requisition ──1──*──► tb_store_requisition_comment
    │  1
    │
    │ FK references (denormalised snapshots on the row)
    ├──► tb_location  (from_location_id, named relation store_requisition_from_location)
    └──► tb_location  (to_location_id,   named relation store_requisition_to_location)
    │
    │ * store_requisition_id
    ▼
tb_store_requisition_detail ──1──*──► tb_store_requisition_detail_comment
    │  1
    │
    │ FK references
    ├──► tb_product                   (required, product_id)
    └──► tb_inventory_transaction     (optional, inventory_transaction_id;
                                       populated on commit; the linked row's
                                       _detail children hold lot, expiry, cost)

tb_store_requisition_detail ──1──*──► tb_inventory_transaction_detail
    indirectly via tb_store_requisition_detail.inventory_transaction_id.
    The inventory transaction is the canonical store of lot_no, expiry_date,
    and FIFO / average-cost layer data — and, for sr_type = transfer, the
    paired stock-IN row at the destination location.
```

Notes:

- **Header → detail** is 1-to-many on `store_requisition_id` (non-nullable on the detail).
- **Header → comment** and **detail → comment** are both 1-to-many. The comment tables are the persistent record of workflow activity; the JSON columns on the header (`workflow_history`, `user_action`) are the in-place cursor. Per-line approval / review / rejection signatures live directly on `tb_store_requisition_detail` (`approved_by_*`, `review_by_*`, `reject_by_*`) — they are **not** in the comment table; the comment table is for free-text discussion threads.
- **SR → inventory** is reached through `tb_store_requisition_detail.inventory_transaction_id`, which has an explicit Prisma `@relation` (unlike GRN's `detail_item.inventory_transaction_id` which is UUID-only). The linked inventory transaction is the canonical store of lot, expiry, and cost-layer data; for `sr_type = transfer`, the same transaction (or a paired one) records the stock-IN at the destination.
- **Location resolution** is explicit on both sides — `from_location_id` and `to_location_id` both declare named Prisma `@relation`s into `tb_location`. The `tb_location.location_type` on each end gates the legal `sr_type` (`issue` requires `to_location.location_type = 'direct'`; `transfer` requires `to_location.location_type = 'inventory'`).
- **No header-level monetary roll-ups.** Unlike GRN, the SR header carries **no** `net_amount` / `total_amount` columns. Cost roll-up is computed on demand from the linked inventory transactions (`tb_inventory_transaction.total_cost` × line, summed per SR) rather than persisted; the SR is a quantity document, not a price document.
- All explicit `@relation` FK declarations use `onDelete: NoAction, onUpdate: NoAction`, so referential integrity is preserved by application-level soft-delete (`deleted_at`) rather than cascade.

## 4. Enums

- **`enum_doc_status`** (shared with several other modules — not SR-specific): five values used by `tb_store_requisition.doc_status`. Default `draft`.
  - `draft` — initial editable state; the requester is still entering line data; no stock or GL impact.
  - `in_progress` — submitted for approval and / or fulfilment; under workflow control. The SR has left the requester's hands but has not yet been issued. Both approve-line and fulfil-line actions happen while the document is `in_progress`; the workflow stage (`workflow_current_stage`) is what distinguishes "awaiting approval" from "awaiting issue".
  - `completed` — fulfilment posted: the stock-OUT at source (and, for `transfer`, the stock-IN at destination) has been written through `tb_store_requisition_detail.inventory_transaction_id`; on-hand at source decremented; cost-layer consumed; journal entries written. The document is locked; corrections require a compensating adjustment in `[inventory-adjustment](/en/inventory/inventory-adjustment)`.
  - `cancelled` — request retracted before commit (e.g. requester withdrew, approver rejected the whole SR, source stock-out at fulfilment time made it un-fillable). No inventory or GL impact.
  - `voided` — administratively voided (audit / data-hygiene path). No inventory or GL impact. Terminal.
- **`enum_sr_type`**: SR movement type for `tb_store_requisition.sr_type`. Default `transfer`. Two values:
  - `issue` — stock leaves inventory and is immediately consumed at the destination's cost-centre (kitchen pull, bar pull). Requires `to_location.location_type = 'direct'`. Single stock-OUT at source; value routed to the destination's consumption expense account on its cost-centre.
  - `transfer` — stock physically moves between two inventory-holding locations without yet being consumed. Requires `to_location.location_type = 'inventory'`. Paired stock-OUT at source and stock-IN at destination; value moves from one inventory account to another, no expense recognised yet.
- **`enum_inventory_doc_type`** (shared, not on `tb_store_requisition` directly but on the linked `tb_inventory_transaction.inventory_doc_type`): lists `store_requisition` as one of seven values (`good_received_note`, `credit_note`, `store_requisition`, `stock_in`, `stock_out`, `close`, `open`). The inventory transaction created on commit stamps `store_requisition` here, so downstream queries can filter inventory movements by originating document type.
- **`enum_comment_type`** (shared with PR / PO / GRN): `user` (human-authored comment), `system` (auto-generated activity-log entry written by the workflow engine). Used by both `tb_store_requisition_comment.type` and `tb_store_requisition_detail_comment.type`.
- **`enum_last_action`** (shared with PR / PO / GRN): `submitted`, `approved`, `reviewed`, `rejected` — used by `tb_store_requisition.last_action` and `tb_store_requisition_detail.last_action` to capture the most recent workflow action.

## 5. Divergences from carmen/docs

The `SR-Overview.md`, `SR-Technical-Specification.md`, `SR-User-Experience.md`, and `Store Requisitions.md` describe a TypeScript interface model (with `Requisition`, `RequisitionItem`, `StockMovement`, `StockMovementItem`, `LotInfo`, `JournalEntry`) and several status enums that do not match the canonical Prisma schema. The differences below are catalogued from those sources.

| # | Item | carmen/docs says | Prisma has | Action |
|---|------|------------------|------------|--------|
| 1 | SR header status values | Tech Spec: `status: 'In Process' | 'Complete' | 'Reject' | 'Void' | 'Draft'`. User-Experience.md state diagram: 6-state `Draft → Submitted → UnderReview → Approved → InProcess → Fulfilled → Completed` plus `PartiallyApproved`, `Rejected`, `Voided`. | `tb_store_requisition.doc_status` uses the shared `enum_doc_status { draft, in_progress, completed, cancelled, voided }`. The carmen/docs `In Process`, `Submitted`, `UnderReview`, `Approved`, `PartiallyApproved`, `InProcess`, `Fulfilled` all collapse into Prisma's `in_progress`; `Complete` / `Fulfilled` / `Completed` collapse into Prisma's `completed`; `Reject` / `Rejected` collapse into `cancelled`; `Void` / `Voided` into `voided`. | Treat Prisma as canonical. The "stage" the document is at during `in_progress` (awaiting approval vs awaiting issue vs partially issued) is what `workflow_current_stage` and the per-line `current_stage_status` capture, not separate header enum values. |
| 2 | Per-line approval status | Tech Spec `RequisitionItem.approvalStatus: 'Accept' | 'Reject' | 'Review'`. Mentioned on the detail-view UI as a per-row badge. | `tb_store_requisition_detail` carries **no** `approval_status` enum column. Per-line decision is inferred from the signature columns (`approved_by_id IS NOT NULL` → accepted; `reject_by_id IS NOT NULL` → rejected; `review_by_id IS NOT NULL` → sent back for review) and the per-line `history` / `stages_status` JSON. | Drop the `approvalStatus` enum from carmen/docs or document that it is an application-layer derived field computed from the signature columns. |
| 3 | Monetary fields on the line | Tech Spec `RequisitionItem.costPerUnit`, `total`. The detail-view UI shows "Unit Cost" and "Total" columns. | `tb_store_requisition_detail` has **no** `cost_per_unit`, `total`, `unit_cost`, `total_cost`, or any monetary column. The unit cost is sourced at commit from the linked `tb_inventory_transaction_cost_layer.cost_per_unit` (the source location's costing-method value); the total is computed for display from `issued_qty × cost_per_unit` but not persisted. | Update carmen/docs to describe SR as a quantity document; cost data lives on the linked inventory transaction and is computed for display, not stored on the SR line. |
| 4 | Monetary fields on the header | Tech Spec `Requisition.totalAmount`. Detail-view UI footer shows "Total: $100.00". | `tb_store_requisition` has **no** `total_amount`, `net_amount`, `subtotal`, or any monetary column on the header. | Drop `totalAmount` from the header interface; document that the header total is a display-only sum across the linked inventory transactions. |
| 5 | Inventory snapshot on the line | Tech Spec `RequisitionItem.inventory: { onHand, onOrder, lastPrice, lastVendor }` and `itemInfo` (location / category / barcode / `locationType`). | `tb_store_requisition_detail` has none of these columns. `onHand` / `onOrder` / `lastPrice` are read at the moment of line entry from `tb_inventory_status` / `tb_product_info` and surfaced in the UI for the requester's decision support; they are not persisted on the SR line. | Update carmen/docs to describe `inventory` and `itemInfo` as UI-only enrichment from the inventory module at line-edit time, not SR columns. |
| 6 | `StockMovement` as an SR-owned table | Tech Spec defines `StockMovement` / `StockMovementItem` interfaces and a `StockMovement` table with `commitDate`, `postingDate`, `status`, `inQty`, `outQty`, `unitCost`, lot info. | There is no `tb_stock_movement` or `tb_store_requisition_stock_movement` table in Prisma. Stock movements live on the shared `tb_inventory_transaction` / `tb_inventory_transaction_detail` family; the SR line reaches them via `inventory_transaction_id`. For `sr_type = transfer`, the OUT at source and the IN at destination are both inventory transactions and are reached the same way. | Realign carmen/docs to describe stock movements as inventory-module records the SR points at, not SR-owned children. |
| 7 | `JournalEntry` as an SR-owned table | Tech Spec defines a `JournalEntry` interface with header / line accounting fields. | There is no SR-owned journal-entry table. Journal entries are generated downstream in the finance module from the linked inventory transactions; the SR module is responsible for triggering them but not for storing them. | Update carmen/docs to describe journal entries as a finance-module concern, reachable from the SR via the linked inventory transaction's downstream postings. |
| 8 | Reference-number format and nullability | Tech Spec validation rule: "Must be unique and follow the format 'SR-YYYY-NNN'". | `tb_store_requisition.sr_no` is `NOT NULL` `VarChar` with no length cap; uniqueness is enforced jointly with `deleted_at` (`@@unique([sr_no, deleted_at])`). The format is application-controlled, not schema-enforced. | Document that the format is an application-layer convention; the column is `NOT NULL` (no draft can save without a reference number assigned — different from GRN's `grn_no` which is nullable on draft). |
| 9 | Movement-type cardinality | User-Experience.md state diagram and Tech Spec describe `movement.type` as a free string on the header. | `tb_store_requisition.sr_type` is the closed enum `enum_sr_type { issue, transfer }`. There are exactly two values, and `transfer` is the default. | Update carmen/docs to reflect the closed two-value enum; drop any reference to `Direct` / `Inventory` movement types — those are `tb_location.location_type` values that gate the SR type, not SR types themselves. |
| 10 | Per-line dimension uniqueness | Tech Spec and Component-Specifications describe lines keyed by `product_id` alone. | The unique index `SRT1_store_requisition_product_location_dimension_u` is `(store_requisition_id, product_id, dimension, deleted_at)` — a single product can appear multiple times on the same SR provided each appearance has a different `dimension` JSON (different cost-centre allocation). | Document the dimension-aware uniqueness: split-cost-centre allocations on the same product are modelled as separate lines, not aggregated. |

## 6. References

- **Primary (source of truth):** Prisma schemas listed in the header callout — concretely `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` (all four SR models, the SR-specific `enum_sr_type`, the shared `enum_doc_status` / `enum_inventory_doc_type` / `enum_comment_type` / `enum_last_action`, and the related `tb_inventory_transaction*` family) and `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` (verified to contain no SR models).
- **Secondary (concept cross-check):**
  - `../carmen/docs/store-requisitions/SR-Overview.md` — module purpose, business context, key features, user roles; divergences in Section 5 (items 2, 3, 4).
  - `../carmen/docs/store-requisitions/SR-Technical-Specification.md` — TypeScript interface model, `RequisitionItem.approvalStatus` enum, `StockMovement` / `JournalEntry` interfaces, validation rules; divergences in Section 5 (items 1, 2, 3, 4, 5, 6, 7, 8).
  - `../carmen/docs/store-requisitions/SR-User-Experience.md` — persona descriptions (Store Manager, Warehouse Supervisor, Department Head, Finance Manager), user journeys, 6-state lifecycle diagram; divergences in Section 5 (items 1, 9).
  - `../carmen/docs/store-requisitions/SR-Component-Specifications.md` — UI component contracts; lines keyed by `product_id` (divergence item 10).
  - `../carmen/docs/store-requisitions/Store Requisitions.md` — listing / detail-view layouts and the UC-64..UC-69 use cases (`Approve`, `Deny`, `Modify`, `Monitor`, `Create and Manage`, `Approve and Record Stock as Issued`); maps onto the lifecycle in Section 2 of the user-flow page.
- **Sibling reference:** [01-data-model.md](../good-receive-note/01-data-model.md) (good-receive-note) — describes the inverse side of the inventory-write pattern; do not duplicate that material here.
- Related modules: [inventory](/en/inventory/inventory) (downstream — the inventory transaction is where lot, expiry, and cost-layer data live), [costing](/en/inventory/costing) (source-location weighted-average or FIFO valuation feeds the issued unit cost), [recipe](/en/inventory/recipe) (recipe demand may auto-generate SRs for ingredient pulls), [good-receive-note](/en/inventory/good-receive-note) (inter-location transfers can pair an SR-OUT at the source warehouse with a GRN-IN at the destination warehouse), [inventory-adjustment](/en/inventory/inventory-adjustment) (post-commit corrections), [product](/en/inventory/product) (per-line product reference).

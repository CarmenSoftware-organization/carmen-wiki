---
title: Good Receive Note (GRN) — Data Model
description: Entities, fields, relationships, and enums for the good-receive-note module.
published: true
date: 2026-05-20T00:00:00.000Z
tags: good-receive-note, data-model, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T11:00:00.000Z
---

# Good Receive Note (GRN) — Data Model

> **At a Glance**
> **Tables:** `tb_good_received_note` &nbsp;·&nbsp; `tb_good_received_note_detail` &nbsp;·&nbsp; `tb_good_received_note_detail_item` &nbsp;·&nbsp; `tb_good_received_note_comment` &nbsp;·&nbsp; `tb_good_received_note_detail_comment`
> **Audience:** Developer / Auditor (dev reference)
> **Key FKs:** detail `→ tb_purchase_order_detail` (upstream PO line); `detail_item.inventory_transaction_id → tb_inventory_transaction` (UUID-only, no `@relation` — downstream inventory ledger); detail `→ tb_location` / `tb_product`; header `→ tb_vendor` / `tb_currency`
> **Audit pattern:** standard `created_*` / `updated_*` / `deleted_*` across all five tables; per-line workflow signatures + `workflow_history` JSON on header

> **Source of truth:** Backend Prisma schema. Always read these first when writing or updating this page:
> - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma`
> - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma`
>
> The `generated/client/schema.prisma` files under each package are auto-generated copies and not authoritative.

## 1. Overview

The good-receive-note module owns five tenant-schema entities: the GRN document header (`tb_good_received_note`), its line items (`tb_good_received_note_detail`), per-line receipt-event rows (`tb_good_received_note_detail_item`) that record the actual received / FOC / accepted qty plus the price-and-tax computation snapshot for each receiving event, and matching workflow / activity-log comment tables at both header and line level (`tb_good_received_note_comment`, `tb_good_received_note_detail_comment`). As with PR and PO, workflow stage tracking is not a dedicated table — the JSON columns on the header (`workflow_history`, `workflow_current_stage`, etc.) plus the comment tables together form the persistent record of the workflow timeline; the shared `tb_workflow` configuration is referenced by `workflow_id` but without a Prisma `@relation`.

The GRN sits **downstream of [purchase-order](/en/inventory/purchase-order)** and **upstream of [inventory](/en/inventory/inventory)** in the procure-to-pay chain. Linkage to PO runs through two columns on `tb_good_received_note_detail` — `purchase_order_id` and `purchase_order_detail_id` — with `purchase_order_detail_id` carrying the explicit Prisma `@relation` back to `tb_purchase_order_detail`. Both columns are nullable so the same line table can also represent a manual GRN with no upstream PO (governed by the `doc_type` enum). On commit, the GRN's downstream effects fan out: every line resolves to one or more rows in `tb_inventory_transaction` / `tb_inventory_transaction_detail` (via `tb_good_received_note_detail_item.inventory_transaction_id`), which is where the actual on-hand increment, cost layer, and lot / expiry data live; the PO line's `received_qty` advances; and the GRN itself transitions from `draft` → `saved` → `committed`. The GRN is also the central anchor for the **three-way match** (PO ↔ GRN ↔ vendor invoice) — the matched leg is what unlocks AP posting downstream.

A noteworthy structural point: the `tb_good_received_note_detail_item` entity has no equivalent in PR or PO. Where a PO line is a single qty/unit/price triple, a GRN line can span **multiple receipt events** (split deliveries, mixed-lot stock landed on the same line, FOC bundles received alongside paid stock). Each event is a `detail_item` row carrying its own `order_qty` / `received_qty` / `foc_qty` triple and the financial snapshot (tax, discount, price, base-currency equivalents) computed at the moment of receipt — and each event also carries `inventory_transaction_id`, which is the link to the inventory side of the world where lot number, expiry date, and cost-layer data are persisted. So while the carmen/docs PRD describes lot / expiry as fields **on the GRN line itself**, the Prisma reality is that they live on the linked inventory transaction; the `detail_item` row is the receipt-event cursor and the bridge. See Section 5 for this divergence.

## 2. Entities

### 2.1 tb_good_received_note

GRN document header. Carries reference number, vendor / currency / credit-term context, invoice and receipt metadata, workflow snapshot, consignment / cash flags, header totals in transaction and base currency, and the standard audit columns. One header has many detail rows, many comments, and many extra-cost rows (`tb_extra_cost`).

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key, generated via `gen_random_uuid()`. |
| `grn_no` | `String @db.VarChar` | Yes | Human-readable GRN reference number. Nullable to support draft GRNs that have not yet been assigned a number. |
| `grn_date` | `DateTime @db.Timestamptz(6)` | Yes | The receipt date — when goods were physically received. |
| `invoice_no` | `String @db.VarChar` | Yes | Vendor invoice number (carried into the three-way match). |
| `invoice_date` | `DateTime @db.Timestamptz(6)` | Yes | Vendor invoice date. |
| `description` | `String @db.VarChar` | Yes | Free-text description on the header. |
| `doc_status` | `enum_good_received_note_status` | No | Document status; default `draft`. |
| `doc_type` | `enum_good_received_note_type` | No | GRN creation mode; default `purchase_order` (PO-sourced is the standard path). |
| `vendor_id` | `String @db.Uuid` | Yes | FK to `tb_vendor.id`. |
| `vendor_name` | `String @db.VarChar` | Yes | Snapshot of the vendor name. |
| `currency_id` | `String @db.Uuid` | No | FK to `tb_currency.id` — the GRN transaction currency. Required. |
| `currency_code` | `String @db.VarChar` | Yes | Snapshot of the currency code. |
| `exchange_rate` | `Decimal @db.Decimal(15, 5)` | Yes | Transaction-to-base exchange rate; default `1`. |
| `exchange_rate_date` | `DateTime @db.Timestamptz(6)` | Yes | Effective date of the exchange rate used. |
| `workflow_id` | `String @db.Uuid` | Yes | FK reference to a `tb_workflow` row (no Prisma `@relation` — selection is application-resolved). |
| `workflow_name` | `String @db.VarChar` | Yes | Snapshot of the workflow name. |
| `workflow_history` | `Json @db.JsonB` | Yes | Append-only stage-transition timeline; default `{}`. Entries hold `stage`, `action`, `message`, `by`, `at`. |
| `workflow_current_stage` | `String @db.VarChar` | Yes | Slug of the stage currently holding the GRN. |
| `workflow_previous_stage` | `String @db.VarChar` | Yes | Slug of the stage that just released the GRN. |
| `workflow_next_stage` | `String @db.VarChar` | Yes | Slug of the next stage in the chain. |
| `user_action` | `Json @db.JsonB` | Yes | Pending-action metadata, default `{}`. Typically `{ "execute": [{ "id": "<user-id>" }, ...] }`. |
| `last_action` | `enum_last_action` | Yes | Last action taken on the document; default `submitted`. |
| `last_action_at_date` | `DateTime @db.Timestamptz(6)` | Yes | Timestamp of `last_action`. |
| `last_action_by_id` | `String @db.Uuid` | Yes | User id who performed `last_action`. |
| `last_action_by_name` | `String @db.VarChar` | Yes | Snapshot of the actor's name. |
| `is_consignment` | `Boolean` | Yes | `true` when the GRN records consignment-in stock (vendor-owned); default `false`. |
| `is_cash` | `Boolean` | Yes | `true` when the receipt is a cash purchase (no AP liability raised); default `false`. |
| `signature_image_url` | `String @db.VarChar` | Yes | URL / token for the receiver's signature image. |
| `received_by_id` | `String @db.Uuid` | Yes | User id of the receiver. |
| `received_by_name` | `String @db.VarChar` | Yes | Snapshot of the receiver's display name. |
| `received_at` | `DateTime @db.Timestamptz(6)` | Yes | Timestamp of physical receipt. |
| `credit_term_id` | `String @db.Uuid` | Yes | FK reference to `tb_credit_term.id` (no Prisma `@relation` declared). |
| `credit_term_name` | `String @db.VarChar` | Yes | Snapshot of the credit term name. |
| `credit_term_days` | `Int` | Yes | Snapshot of the credit term in days. |
| `payment_due_date` | `DateTime @db.Timestamptz(6)` | Yes | Computed `invoice_date + credit_term_days`, persisted. |
| `net_amount` | `Decimal @db.Decimal(15, 5)` | No | Roll-up of line `net_amount` (transaction currency); default `0`. |
| `base_net_amount` | `Decimal @db.Decimal(15, 5)` | No | Roll-up of line `base_net_amount` (base currency); default `0`. |
| `total_amount` | `Decimal @db.Decimal(15, 5)` | No | Roll-up of line `total_price` (net + tax, transaction currency); default `0`. |
| `base_total_amount` | `Decimal @db.Decimal(15, 5)` | No | Roll-up of line `base_total_price` (base currency); default `0`. |
| `is_active` | `Boolean` | Yes | Whether the GRN is active; default `true`. |
| `note` | `String @db.VarChar` | Yes | Free-text note attached to the header. |
| `info` | `Json @db.JsonB` | Yes | Extension bag for tenant-specific header attributes; default `{}`. |
| `dimension` | `Json @db.JsonB` | Yes | Cost-dimension array (project, cost-centre, job code, etc.); default `[]`. |
| `doc_version` | `Int @db.Integer` | No | Optimistic-concurrency version counter; default `0`. |
| `created_at` | `DateTime @db.Timestamptz(6)` | Yes | Creation timestamp; defaults to `now()`. |
| `created_by_id` | `String @db.Uuid` | Yes | User id who created the row. |
| `updated_at` | `DateTime @db.Timestamptz(6)` | Yes | Last-update timestamp; defaults to `now()`. |
| `updated_by_id` | `String @db.Uuid` | Yes | User id who last updated the row. |
| `deleted_at` | `DateTime @db.Timestamptz(6)` | Yes | Soft-delete timestamp; non-null means logically deleted. |
| `deleted_by_id` | `String @db.Uuid` | Yes | User id who soft-deleted the row. |

**Constraints:** `@id` on `id`. FKs: `currency_id → tb_currency.id` (`NoAction`); `vendor_id → tb_vendor.id` (`NoAction`). Note: `credit_term_id` and `workflow_id` are stored as UUIDs but have no Prisma `@relation` on this model — they are application-resolved. Back-relations: many `tb_good_received_note_detail`, many `tb_good_received_note_comment`, many `tb_extra_cost`, many `tb_credit_note`.
**Indexes:** `@@unique([grn_no, deleted_at])` as `goodreceivednote_grn_no_u`; `@@index([grn_no])` as `goodreceivednote_grn_no_idx`.

Comment / attachment tables for this module are documented separately — see [01a — Data Model: Comment Tables](/en/inventory/good-receive-note/01a-data-model-comments).

### 2.2 tb_good_received_note_detail

GRN line item. Identifies the receiving location, the product being received, and the upstream PO line (when PO-sourced). Notably, this table holds **only identifying / locating information** — the actual quantities, prices, taxes, and per-receipt-event detail live on the child `tb_good_received_note_detail_item` rows (Section 2.3). One detail can have many detail-item rows to represent split deliveries, mixed lots, or paid-plus-FOC events posted onto the same line.

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `good_received_note_id` | `String @db.Uuid` | No | FK to `tb_good_received_note.id`. |
| `sequence_no` | `Int` | No | Line ordering within the GRN; default `1`. |
| `purchase_order_id` | `String @db.Uuid` | Yes | FK reference to `tb_purchase_order.id` (no Prisma `@relation` declared on this column — only `purchase_order_detail_id` carries the explicit relation). Nullable to allow manual GRN lines. |
| `purchase_order_detail_id` | `String @db.Uuid` | Yes | FK to `tb_purchase_order_detail.id` — the upstream PO line being fulfilled. Nullable for manual receipts. |
| `location_id` | `String @db.Uuid` | No | FK to `tb_location.id` — the receiving store / location. Required. |
| `location_code` | `String @db.VarChar` | Yes | Snapshot of the location code. |
| `location_name` | `String @db.VarChar` | Yes | Snapshot of the location name. |
| `product_id` | `String @db.Uuid` | No | FK to `tb_product.id`. Required. |
| `product_code` | `String @db.VarChar` | Yes | Snapshot of product code. |
| `product_name` | `String @db.VarChar` | Yes | Snapshot of product name. |
| `product_local_name` | `String @db.VarChar` | Yes | Localised product name snapshot. |
| `product_sku` | `String @db.VarChar` | Yes | Snapshot of SKU. |

**Constraints:** `@id` on `id`. FKs: `good_received_note_id → tb_good_received_note.id`; `location_id → tb_location.id` (required); `product_id → tb_product.id` (required); `purchase_order_detail_id → tb_purchase_order_detail.id` (nullable). Note: `purchase_order_id` is stored on the row but has no Prisma `@relation` — the PO link is reached through `purchase_order_detail_id`'s relation. Back-relations: many `tb_good_received_note_detail_item`, many `tb_good_received_note_detail_comment`.
**Indexes:** `@@unique([good_received_note_id, sequence_no])` as `goodreceivednotedetail_good_received_note_id_sequence_no_u`; `@@index([good_received_note_id, sequence_no])` as `goodreceivednotedetail_good_received_note_id_sequence_no_idx`. Note: the unique constraint here does **not** include `deleted_at` (unlike the PR / PO equivalents), so soft-deleted lines still occupy a `sequence_no` slot.

### 2.3 tb_good_received_note_detail_item

**GRN-specific receipt-event row — no equivalent in PR or PO.** A single GRN detail (Section 2.2) can spawn multiple `detail_item` rows to record split deliveries (one line, two cartons that arrived on different trucks), mixed-lot landings (one line, two different lots placed onto the same product / location), or paid-plus-FOC bundles posted against the same line. Each row carries three parallel qty / unit / conversion-factor triples — `order_*`, `received_*`, and `foc_*` — plus the full price-tax-discount-totals snapshot **in both transaction and base currency** computed at the moment of receipt. The row's `inventory_transaction_id` is the link to the inventory side of the world; that linked transaction (and its `tb_inventory_transaction_detail` children) is where the actual lot number, expiry date, and FIFO / average-cost layer data persist. So the `detail_item` row is **not itself the lot store** — it is the GRN-side cursor for the receiving event, and the inventory transaction is the lot store.

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `good_received_note_detail_id` | `String @db.Uuid` | No | FK to `tb_good_received_note_detail.id`. |
| `inventory_transaction_id` | `String @db.Uuid` | Yes | FK reference to `tb_inventory_transaction.id` (no Prisma `@relation` declared). Populated on commit; the linked row's `tb_inventory_transaction_detail` children hold `lot_no`, `expiry_date`, and `cost_per_unit`. |
| `comment` | `String @db.VarChar` | Yes | Free-text comment on this receipt event. |
| `purchase_order_detail_purchase_request_detail_id` | `String @db.Uuid` | Yes | FK reference to `tb_purchase_order_detail_tb_purchase_request_detail.id` (no Prisma `@relation`). Points to the PO↔PR bridge row, so the receipt event can be traced all the way back to the originating PR line. |
| `order_qty` | `Decimal @db.Decimal(20, 5)` | Yes | Ordered qty for this event (in order UoM); default `0`. |
| `order_unit_id` | `String @db.Uuid` | Yes | UoM used at ordering time. |
| `order_unit_name` | `String @db.VarChar` | Yes | Snapshot of the order UoM name. |
| `order_unit_conversion_factor` | `Decimal @db.Decimal(20, 5)` | Yes | Conversion factor from order UoM to base UoM; default `0`. |
| `order_base_qty` | `Decimal @db.Decimal(20, 5)` | Yes | `order_qty × order_unit_conversion_factor`; default `0`. |
| `received_qty` | `Decimal @db.Decimal(20, 5)` | Yes | Received qty for this event (in receiving UoM); default `0`. This is the qty that posts to inventory. |
| `received_unit_id` | `String @db.Uuid` | Yes | UoM used at receiving time. |
| `received_unit_name` | `String @db.VarChar` | Yes | Snapshot of the receiving UoM name. |
| `received_unit_conversion_factor` | `Decimal @db.Decimal(20, 5)` | Yes | Conversion factor from receiving UoM to base UoM; default `0`. |
| `received_base_qty` | `Decimal @db.Decimal(20, 5)` | Yes | `received_qty × received_unit_conversion_factor`; default `0`. |
| `foc_qty` | `Decimal @db.Decimal(20, 5)` | Yes | Free-of-charge qty for this event (in FOC UoM); default `0`. |
| `foc_unit_id` | `String @db.Uuid` | Yes | UoM used for the FOC portion. |
| `foc_unit_name` | `String @db.VarChar` | Yes | Snapshot of the FOC UoM name. |
| `foc_unit_conversion_factor` | `Decimal @db.Decimal(20, 5)` | Yes | Conversion factor from FOC UoM to base UoM; default `0`. |
| `foc_base_qty` | `Decimal @db.Decimal(20, 5)` | Yes | `foc_qty × foc_unit_conversion_factor`; default `0`. |
| `tax_profile_id` | `String @db.Uuid` | Yes | FK to `tb_tax_profile.id`. |
| `tax_profile_name` | `String @db.VarChar` | Yes | Snapshot. |
| `tax_rate` | `Decimal @db.Decimal(15, 5)` | Yes | Effective tax rate; default `0`. |
| `tax_amount` | `Decimal @db.Decimal(20, 5)` | Yes | Tax amount in transaction currency; default `0`. |
| `base_tax_amount` | `Decimal @db.Decimal(20, 5)` | Yes | Tax amount in base currency; default `0`. |
| `is_tax_adjustment` | `Boolean` | Yes | `true` when the user manually overrode the tax amount; default `false`. |
| `discount_rate` | `Decimal @db.Decimal(15, 5)` | Yes | Discount rate %; default `0`. |
| `discount_amount` | `Decimal @db.Decimal(20, 5)` | Yes | Discount amount in transaction currency; default `0`. |
| `base_discount_amount` | `Decimal @db.Decimal(20, 5)` | Yes | Discount amount in base currency; default `0`. |
| `is_discount_adjustment` | `Boolean` | Yes | `true` when the user manually overrode the discount; default `false`. |
| `sub_total_price` | `Decimal @db.Decimal(20, 5)` | Yes | `price × received_qty` (transaction currency); default `0`. |
| `net_amount` | `Decimal @db.Decimal(20, 5)` | Yes | `sub_total_price − discount_amount`; default `0`. |
| `total_price` | `Decimal @db.Decimal(20, 5)` | Yes | `net_amount + tax_amount`; default `0`. |
| `base_price` | `Decimal @db.Decimal(20, 5)` | Yes | `price × exchange_rate` (base unit price); default `0`. |
| `base_sub_total_price` | `Decimal @db.Decimal(20, 5)` | Yes | `base_price × received_qty`; default `0`. |
| `base_net_amount` | `Decimal @db.Decimal(20, 5)` | Yes | `base_sub_total_price − base_discount_amount`; default `0`. |
| `base_total_price` | `Decimal @db.Decimal(20, 5)` | Yes | `base_net_amount + base_tax_amount`; default `0`. |
| `note` | `String @db.VarChar` | Yes | Free-text note. |
| `created_at` | `DateTime @db.Timestamptz(6)` | Yes | Creation timestamp. |
| `created_by_id` | `String @db.Uuid` | Yes | Creator id. |
| `updated_at` | `DateTime @db.Timestamptz(6)` | Yes | Last-update timestamp. |
| `updated_by_id` | `String @db.Uuid` | Yes | Updater id. |
| `deleted_at` | `DateTime @db.Timestamptz(6)` | Yes | Soft-delete timestamp. |
| `deleted_by_id` | `String @db.Uuid` | Yes | Soft-delete actor id. |

**Constraints:** `@id` on `id`. FKs: `good_received_note_detail_id → tb_good_received_note_detail.id`; `tax_profile_id → tb_tax_profile.id`; three named `@relation` FKs into `tb_unit` — `tb_good_received_note_detail_item_order_unit_idTotb_unit` for `order_unit_id`, `tb_good_received_note_detail_item_received_unit_idTotb_unit` for `received_unit_id`, and `tb_good_received_note_detail_item_foc_unit_idTotb_unit` for `foc_unit_id`. Note: `inventory_transaction_id` and `purchase_order_detail_purchase_request_detail_id` are stored as UUIDs but have no Prisma `@relation` on this model.
**Indexes:** None declared beyond the primary key.

## 3. Relationships

```
tb_workflow
    │  (workflow_id stored but no Prisma @relation on tb_good_received_note)
    ▼
tb_good_received_note ──1──*──► tb_good_received_note_comment
    │  1                  ──1──*──► tb_extra_cost            (landed-cost components,
    │                                                          owned by extra-cost / costing module)
    │                     ──1──*──► tb_credit_note           (vendor credit notes raised against this GRN)
    │
    │ * good_received_note_id
    ▼
tb_good_received_note_detail ──1──*──► tb_good_received_note_detail_comment
    │  1
    │
    │ FK references (denormalised snapshots on the row)
    ├──► tb_location                  (required, location_id)
    ├──► tb_product                   (required, product_id)
    └──► tb_purchase_order_detail     (optional, purchase_order_detail_id — the PO line link)
    └──  (purchase_order_id is stored on the row but has no Prisma @relation —
          PO header is reached through purchase_order_detail's relation)
    │
    │ * good_received_note_detail_id
    ▼
tb_good_received_note_detail_item    (receipt-event row — GRN-specific, no PR/PO equivalent)
    │
    │ FK references
    ├──► tb_unit ×3                   (order_unit_id, received_unit_id, foc_unit_id — named relations)
    ├──► tb_tax_profile               (tax_profile_id)
    └──  (inventory_transaction_id and purchase_order_detail_purchase_request_detail_id
          stored as UUIDs but have no Prisma @relation — they are application-resolved
          and provide the inventory-side and PR-traceback links respectively)

tb_good_received_note (header-level FKs)
    ├──► tb_currency                  (currency_id, required)
    └──► tb_vendor                    (vendor_id, optional)

tb_good_received_note_detail ──1──*──► tb_inventory_transaction_detail
    indirectly via tb_good_received_note_detail_item.inventory_transaction_id.
    The inventory transaction is the canonical store of lot_no, expiry_date,
    and FIFO / average-cost layer data — those fields are NOT on the GRN
    detail_item itself.

tb_purchase_order_detail ──1──*──► tb_good_received_note_detail
    PO line back-reference; PO line's received_qty is incremented on GRN commit,
    advancing the PO from `sent` → `partial` → `completed`.
```

Notes:

- **Header → detail** is 1-to-many on `good_received_note_id` (non-nullable on the detail).
- **Detail → detail_item** is 1-to-many on `good_received_note_detail_id` (non-nullable on the item). This is the structural difference from PR / PO: GRN has an extra level of nesting to support split / mixed-lot receipts on a single ordered line.
- **Header → comment** and **detail → comment** are both 1-to-many. The comment tables are the persistent record of workflow activity; the JSON columns on the header (`workflow_history`, `user_action`) are the in-place cursor.
- **PO → GRN** is 1-to-many via `tb_good_received_note_detail.purchase_order_detail_id` (the Prisma `@relation`-bearing column). `purchase_order_id` is also stored on the row but is denormalised — the canonical link is through `purchase_order_detail_id`. Both columns are nullable to support manual GRNs (governed by `doc_type = manual`).
- **GRN → inventory** is reached through `tb_good_received_note_detail_item.inventory_transaction_id`, which has no Prisma `@relation` but is the application-resolved bridge into `tb_inventory_transaction` and its children. **Lot number, expiry date, and cost-layer data live on the inventory transaction, not on the GRN detail_item.**
- **GRN ↔ PR traceback** runs through `tb_good_received_note_detail_item.purchase_order_detail_purchase_request_detail_id`, which is a UUID reference (no `@relation`) to the PO↔PR bridge — closing the procure-to-pay loop from PR origin to inventory landing.
- All explicit `@relation` FK declarations use `onDelete: NoAction, onUpdate: NoAction`, so referential integrity is preserved by application-level soft-delete (`deleted_at`) rather than cascade.

## 4. Enums

- **`enum_good_received_note_status`**: document-status enum for `tb_good_received_note.doc_status`. Default `draft`. Four values:
  - `draft` — initial editable state; the receiving clerk is still entering qty / lot data; no stock or GL impact.
  - `saved` — line entry complete and the document has been saved for review (e.g. by Inventory Manager or Finance) but not yet committed; still editable, still no stock or GL impact.
  - `committed` — the single posting event has fired: inventory on-hand has been incremented, FIFO / average-cost layers updated, journal entries written, the source PO line's `received_qty` advanced. The document is locked; corrections require either a `tb_credit_note` against this GRN or a compensating adjustment in [inventory-adjustment](/en/inventory/inventory-adjustment).
  - `voided` — the GRN was administratively voided before commit; receiving is cancelled with no inventory or GL impact.
- **`enum_good_received_note_type`**: GRN creation mode for `tb_good_received_note.doc_type`. Default `purchase_order`. Two values:
  - `purchase_order` — PO-sourced (standard path); detail rows carry `purchase_order_detail_id`, qty validation runs against the PO line's remaining `order_qty − received_qty − cancelled_qty`.
  - `manual` — manual GRN with no upstream PO; detail rows' `purchase_order_id` and `purchase_order_detail_id` are null, and the user supplies vendor / product / qty / price directly.
- **`enum_comment_type`** (shared with PR and PO): `user` (human-authored comment), `system` (auto-generated activity-log entry written by the workflow engine). Used by both `tb_good_received_note_comment.type` and `tb_good_received_note_detail_comment.type`.
- **`enum_last_action`** (shared with PR and PO): `submitted`, `approved`, `reviewed`, `rejected` — used by `tb_good_received_note.last_action` to capture the most recent workflow action.

## 5. Divergences from carmen/docs

The `GRN-Technical-Specification.md` describes a TypeScript interface model (with `GoodsReceivedNote`, `GRNItem`, `GRNExtraCost`, `GRNExtraCostAllocation`, etc.) and a status enum (`DRAFT, PENDING_APPROVAL, APPROVED, REJECTED, CANCELLED`); `grn-master-prd.md` describes a 3-status lifecycle (`Received` / `Draft` → `Committed` → `Voided`) and references a Department, Delivery Point, and lot-level fields on the line. Several of these differ from the canonical Prisma schema:

| # | Item | carmen/docs says | Prisma has | Action |
|---|------|------------------|------------|--------|
| 1 | GRN status values | Technical Spec: `enum GRNStatus { DRAFT, PENDING_APPROVAL, APPROVED, REJECTED, CANCELLED }`. PRD §5.1: 3-state model `Received` / `Draft` → `Committed` → `Voided`. | `enum_good_received_note_status { draft, saved, committed, voided }` — adds an intermediate `saved` state (review-ready) between `draft` and `committed`; no `pending_approval`, `approved`, `rejected`, or `cancelled` values. | Treat Prisma as canonical. The Technical Spec enum is from an earlier modelling pass and should be deprecated; PRD's 3-state model maps closely but is missing `saved`. Update both. |
| 2 | Header fields not in Prisma | Technical Spec `GoodsReceivedNote` includes `departmentId`, `locationId`, `referenceNumber`, `subtotal`, `discountAmount`, `taxAmount`, `extraCostsTotal`, `total`, `approvedBy`, `approvedAt` on the header. | `tb_good_received_note` has **no** `department_id` or header `location_id` (location is per-line on the detail), **no** `reference_number` (only `grn_no` and `invoice_no`), and a different totals shape (`net_amount`, `base_net_amount`, `total_amount`, `base_total_amount` — no `subtotal`, `discount_amount`, `tax_amount`, or `extra_costs_total` at the header level — those roll up from line / extra-cost tables on read). No `approved_by` / `approved_at` — approval data lives in workflow JSON and `last_action_*` columns. | Realign carmen/docs `GoodsReceivedNote` interface to match Prisma column names. Document that header location is *not* modelled (location is per-line) and that approval lives in the workflow snapshot. |
| 3 | Lot / expiry / serial location | PRD §3.5 and Technical Spec `GRNItem` claim `lotNumber`, `expiryDate`, `manufacturingDate` are fields **on the GRN line**. | `tb_good_received_note_detail` and `tb_good_received_note_detail_item` have **no** `lot_no`, `expiry_date`, `manufacturing_date`, or `serial_no` columns. Lot and expiry data live on `tb_inventory_transaction_detail.from_lot_no` / `current_lot_no` (and `tb_inventory_transaction_cost_layer.lot_no`), reached through `tb_good_received_note_detail_item.inventory_transaction_id`. | Update carmen/docs to describe lot/expiry as inventory-transaction-side fields surfaced **via** the GRN detail_item link, not stored on the GRN row itself. The GRN detail_item is the receipt-event cursor; the inventory transaction is the lot store. |
| 4 | Item-status on the line | Technical Spec `GRNItem` includes `status: GRNItemStatus { RECEIVED, REJECTED, PARTIALLY_REJECTED }` and `rejectedQuantity`, `rejectionReason`. | `tb_good_received_note_detail` and `tb_good_received_note_detail_item` carry no per-line status enum, no `rejected_qty`, and no `rejection_reason` columns. Acceptance / rejection is modelled by writing reject-quantity events as additional `detail_item` rows or as line `_comment` entries; there is no first-class enum. | Drop the `GRNItemStatus` enum from carmen/docs or document that it is an application-layer derived field, not a schema column. |
| 5 | Extra-cost allocation modelling | Technical Spec defines `GRNExtraCost` and `GRNExtraCostAllocation` as GRN-owned entities with `allocationMethod: AllocationMethod { MANUAL, BY_VALUE, BY_QUANTITY, BY_WEIGHT, BY_VOLUME }`. | Prisma has a separate `tb_extra_cost` model with `allocate_extra_cost_type: enum_allocate_extra_cost_type { manual, by_value, by_qty }` — and only 3 allocation modes (`manual`, `by_value`, `by_qty`); no `by_weight` or `by_volume`. There is **no** `tb_extra_cost_allocation` bridge table — allocation is computed and written into the per-item financial snapshot, not persisted as a separate row. The model is shared (not GRN-owned); GRN back-references it through `tb_extra_cost.good_received_note_id`. | Update carmen/docs to (a) drop `BY_WEIGHT` / `BY_VOLUME` from the allocation enum, (b) describe `tb_extra_cost` as a shared model GRN attaches to, not a GRN-owned child, and (c) drop the separate `GRNExtraCostAllocation` entity claim. |
| 6 | Reference-number column name | Technical Spec: `grnNumber`. PRD: "GRN Reference Number". | `tb_good_received_note.grn_no` (nullable, no length cap). | Rename in carmen/docs data dictionary; flag that the column is nullable on draft GRNs and that uniqueness is enforced jointly with `deleted_at` (`@@unique([grn_no, deleted_at])`). |
| 7 | FOC on the line | PRD §3.4.4 / §3.4.5 lists `FOC quantities` and `FOC Unit` per line. | FOC is modelled **at the receipt-event level** (`tb_good_received_note_detail_item.foc_qty` / `foc_unit_id` / `foc_unit_conversion_factor` / `foc_base_qty`), not at the GRN-line level. This means a single line can record paid stock and FOC stock as **separate** detail_item rows under the same `good_received_note_detail_id`. | Update carmen/docs to describe FOC at the receipt-event level; clarify that paid and FOC for the same product / location are typically recorded as parallel detail_item rows, not as two columns on one line. |
| 8 | Delivery point on the header | PRD §3.4.1 lists "Delivery Point" in the GRN header. | `tb_good_received_note` has **no** `delivery_point_id` column. Delivery context is captured implicitly through the per-line `location_id` and through the upstream PO's delivery-point snapshot reached via `tb_purchase_order_detail_tb_purchase_request_detail.delivery_point_*`. | Drop "Delivery Point" from the GRN header data dictionary; document that delivery context is per-line via `location_id` (and traceable upstream via the PR-bridge snapshot). |
| 9 | Department on the header | Technical Spec `GoodsReceivedNote.departmentId` (required). | No `department_id` column on `tb_good_received_note`. Department / cost-centre information is held in the JSON `dimension` array (an array of cost-dimension objects). | Drop `departmentId` from the carmen/docs header dictionary; document that cost-centre / department lives in the per-row `dimension` JSON, which is the tenant-extensible cost-dimension contract. |
| 10 | `is_consignment` / `is_cash` flags | PRD §3.4.1 lists "Consignment checkbox" and "Cash checkbox" on the header but does not include them in the `GoodsReceivedNote` Technical Spec interface. | Both fields are present on `tb_good_received_note` (`is_consignment Boolean?`, `is_cash Boolean?`, both default `false`). | Add the two boolean fields to the carmen/docs `GoodsReceivedNote` interface and document their semantics (consignment-in suppresses owned-stock + AP impact; cash suppresses AP liability). |

## 6. References

- **Primary (source of truth):** Prisma schemas listed in the header callout — concretely `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` (all five GRN models, both enums, and the related `tb_extra_cost` / `tb_inventory_transaction*` models) and `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` (verified to contain no GRN models).
- **Secondary (concept cross-check):**
  - `../carmen/docs/good-recive-note-managment/GRN-Technical-Specification.md` — TypeScript interface model and calculation rules; divergences in Section 5 (items 1, 2, 4, 5, 9).
  - `../carmen/docs/good-recive-note-managment/grn-master-prd.md` — PRD with header field list, FOC behaviour, and 3-state lifecycle prose; divergences in Section 5 (items 1, 3, 6, 7, 8, 10).
- **Sibling reference:** [01-data-model.md](../purchase-order/01-data-model.md) (purchase-order) — describes the PO side of the PO→GRN linkage; do not duplicate that material here.
- Related modules: [purchase-order](/en/inventory/purchase-order) (upstream source via `purchase_order_detail_id`), [purchase-request](/en/inventory/purchase-request) (origin, reached through the PO↔PR bridge id stored on the detail_item), [inventory](/en/inventory/inventory) (downstream — the inventory transaction is where lot, expiry, and cost-layer data live), [costing](/en/inventory/costing) (FIFO / average-cost layer creation on commit), [inventory-adjustment](/en/inventory/inventory-adjustment) (post-commit corrections), [vendor-pricelist](/en/inventory/vendor-pricelist) (price-variance check against the GRN unit price), [product](/en/inventory/product) (per-line product reference).

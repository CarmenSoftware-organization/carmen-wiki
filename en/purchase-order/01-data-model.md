---
title: Purchase Order — Data Model
description: Entities, fields, relationships, and enums for the purchase-order module.
published: true
date: 2026-05-15T10:00:00.000Z
tags: purchase-order, data-model, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T10:00:00.000Z
---

# Purchase Order — Data Model

> **Source of truth:** Backend Prisma schema. Always read these first when writing or updating this page:
> - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma`
> - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma`
>
> The `generated/client/schema.prisma` files under each package are auto-generated copies and not authoritative.

## 1. Overview

The purchase-order module owns five tenant-schema entities: the PO document header (`tb_purchase_order`), its line items (`tb_purchase_order_detail`), workflow / activity-log comments at both header and line level (`tb_purchase_order_comment`, `tb_purchase_order_detail_comment`), and the bridge table (`tb_purchase_order_detail_tb_purchase_request_detail`) that links PO lines back to one or more originating PR lines. As with PR, workflow stage tracking is not a dedicated table — it is stored inline on the header as JSON columns (`workflow_history`, `workflow_current_stage`, `stages_status`) plus a foreign key into the shared `tb_workflow` configuration, while the persisted timeline of stage-transition events is captured through the comment tables.

The PO sits **downstream of [[purchase-request]]** and **upstream of [[good-receive-note]]** in the procure-to-pay chain. PR-to-PO linkage runs through the bridge table noted above; the same bridge captures per-PR-line received and FOC quantities, supporting both PR consolidation (many PR lines → one PO line) and partial conversion (one PR line → many PO lines). PO lines carry running `received_qty` and `cancelled_qty` columns so that the "pending qty" available for GRN is `order_qty − received_qty − cancelled_qty`; the relation from PO detail to GRN detail (`tb_good_received_note_detail`) is what closes the loop. PO detail rows also reference [[product]], `tb_tax_profile`, and `tb_unit` (twice — for order UoM and base UoM), and the header references `tb_vendor`, `tb_currency`, and `tb_credit_term`. All PO entities live in the tenant Prisma schema; the platform schema contains no purchase-order models.

The header carries vendor, currency, exchange-rate and credit-term context once for the whole PO — by design, every line on a PO shares the same vendor and currency, which is why the PR-to-PO conversion flow must group selected PRs by `(vendor, currency)` before fan-out. The default value of `tb_purchase_order.po_type` is `purchase_request`, which makes PR-sourced the standard creation path; `manual` is the alternative for procurement-only POs that have no upstream PR.

## 2. Entities

### 2.1 tb_purchase_order

PO document header. Carries reference number, vendor / currency / credit-term context, workflow snapshot, totals, and audit columns. One header has many detail rows and many comments.

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key, generated via `gen_random_uuid()`. |
| `po_no` | `String @db.VarChar` | No | Human-readable PO reference number. |
| `po_status` | `enum_purchase_order_doc_status` | Yes | Document status; default `draft`. |
| `po_type` | `enum_purchase_order_type` | No | PO creation mode; default `purchase_request` (PR-sourced is the standard path). |
| `description` | `String` | Yes | Free-text description / justification entered on the header. |
| `order_date` | `DateTime @db.Timestamptz(6)` | Yes | Order date assigned on the header. |
| `delivery_date` | `DateTime @db.Timestamptz(6)` | Yes | Header-level required delivery date. |
| `workflow_id` | `String @db.Uuid` | Yes | FK reference to a `tb_workflow` row (no Prisma `@relation` declared on this model — selection is application-resolved). |
| `workflow_name` | `String @db.VarChar` | Yes | Snapshot of the workflow name. |
| `workflow_history` | `Json @db.JsonB` | Yes | Append-only stage-transition timeline; default `[]`. Each entry holds `stage`, `action`, `message`, `by`, `at`. |
| `workflow_current_stage` | `String @db.VarChar` | Yes | Slug of the stage currently holding the PO. |
| `workflow_previous_stage` | `String @db.VarChar` | Yes | Slug of the stage that just released the PO. |
| `workflow_next_stage` | `String @db.VarChar` | Yes | Slug of the next stage in the chain. |
| `user_action` | `Json @db.JsonB` | Yes | Pending-action metadata, default `{}`. Typically `{ "execute": [{ "id": "<user-id>" }, ...] }` listing who can act next. |
| `last_action` | `enum_last_action` | Yes | Last action taken on the document; default `submitted`. |
| `last_action_at_date` | `DateTime @db.Timestamptz(6)` | Yes | Timestamp of `last_action`. |
| `last_action_by_id` | `String @db.Uuid` | Yes | User id who performed `last_action`. |
| `last_action_by_name` | `String @db.VarChar` | Yes | Snapshot of the actor's name. |
| `vendor_id` | `String @db.Uuid` | Yes | FK to `tb_vendor.id` — the PO's single vendor. |
| `vendor_name` | `String @db.VarChar` | Yes | Snapshot of the vendor name. |
| `currency_id` | `String @db.Uuid` | Yes | FK to `tb_currency.id` — transaction currency for the whole PO. |
| `currency_code` | `String @db.VarChar` | Yes | Snapshot of the currency code. |
| `exchange_rate` | `Decimal @db.Decimal(15, 5)` | Yes | Transaction-to-base exchange rate; default `1`. |
| `approval_date` | `DateTime @db.Timestamptz(6)` | Yes | Timestamp when the PO was approved. |
| `email` | `String @db.VarChar` | Yes | Email address used when sending the PO to the vendor. |
| `buyer_id` | `String @db.Uuid` | Yes | Buyer / procurement officer id. |
| `buyer_name` | `String @db.VarChar` | Yes | Snapshot of the buyer's display name. |
| `credit_term_id` | `String @db.Uuid` | Yes | FK to `tb_credit_term.id`. |
| `credit_term_name` | `String @db.VarChar` | Yes | Snapshot of the credit term name. |
| `credit_term_value` | `Int @db.Integer` | Yes | Snapshot of the credit term in days; default `0`. |
| `remarks` | `String @db.VarChar` | Yes | Free-text remarks for the vendor or audit trail. |
| `history` | `Json @db.JsonB` | Yes | Header-level audit history; default `[]`. Each entry holds `po_status`, `action`, `by`, `at`. |
| `total_qty` | `Decimal @db.Decimal(20, 5)` | Yes | Roll-up of line `order_qty` (base-UoM equivalent); default `0`. |
| `total_price` | `Decimal @db.Decimal(20, 5)` | Yes | Roll-up of line `net_amount`; default `0`. |
| `total_tax` | `Decimal @db.Decimal(20, 5)` | Yes | Roll-up of line `tax_amount`; default `0`. |
| `total_amount` | `Decimal @db.Decimal(20, 5)` | Yes | Roll-up of line `total_price` (net + tax); default `0`. |
| `is_active` | `Boolean` | Yes | Whether the PO is active; default `true`. |
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

**Constraints:** `@id` on `id`. FKs: `credit_term_id → tb_credit_term.id` (`NoAction`); `currency_id → tb_currency.id` via named relation `tb_purchase_order_currency_idTotb_currency` (`NoAction`); `vendor_id → tb_vendor.id` (`NoAction`). Note: `workflow_id` is stored as a UUID but has no Prisma `@relation` on this model.
**Indexes:** `@@unique([po_no, deleted_at])` as `PO_po_no_u`; `@@index([po_no])` as `PO_po_no_idx`; `@@index([vendor_id])` as `PO_vendor_id_idx`.

### 2.2 tb_purchase_order_comment

Workflow / activity-log entries attached to a PO header. As with PR, there is no dedicated `tb_purchase_order_workflow` table — this comment table, combined with the JSON workflow columns on the header, is the persistent record of the workflow timeline. Each row is either a user comment (`type = user`) or a system event (`type = system`) such as a stage transition.

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `purchase_order_id` | `String @db.Uuid` | No | FK to `tb_purchase_order.id`. |
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

**Constraints:** `@id` on `id`. FK `purchase_order_id → tb_purchase_order.id` (`NoAction` on delete/update).
**Indexes:** None declared beyond the primary key.

### 2.3 tb_purchase_order_detail

PO line item. Carries product reference, order-qty and base-qty pair (single qty/UoM unlike PR which carries requested/approved/FOC triples — FOC on PO is a per-line boolean), tax and discount, line totals in transaction and base currency, running received / cancelled qty, and per-line workflow stage history.

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `purchase_order_id` | `String @db.Uuid` | Yes | FK to `tb_purchase_order.id`. Nullable to support draft lines unattached to a header. |
| `description` | `String` | Yes | Line description (often overrides product name for free-text lines). |
| `comment` | `String @db.VarChar` | Yes | Line-level comment. |
| `sequence_no` | `Int` | Yes | Line ordering within the PO; default `1`. |
| `is_active` | `Boolean` | Yes | Whether the line is active; default `true`. |
| `product_id` | `String @db.Uuid` | No | FK to `tb_product.id`. Required. |
| `product_code` | `String @db.VarChar` | Yes | Snapshot of product code. |
| `product_name` | `String @db.VarChar` | Yes | Snapshot of product name. |
| `product_local_name` | `String @db.VarChar` | Yes | Localised product name snapshot. |
| `product_sku` | `String @db.VarChar` | Yes | Snapshot of SKU. |
| `order_qty` | `Decimal @db.Decimal(20, 5)` | Yes | Qty in order UoM; default `0`. |
| `order_unit_id` | `String @db.Uuid` | Yes | UoM used at ordering time. |
| `order_unit_conversion_factor` | `Decimal @db.Decimal(20, 5)` | Yes | Conversion factor from order UoM to base UoM; default `0`. |
| `order_unit_name` | `String @db.VarChar` | Yes | Snapshot of the order UoM name. |
| `base_qty` | `Decimal @db.Decimal(20, 5)` | Yes | `order_qty × order_unit_conversion_factor`; default `0`. |
| `base_unit_id` | `String @db.Uuid` | Yes | Inventory base UoM at order time. |
| `base_unit_name` | `String @db.VarChar` | Yes | Snapshot of the base UoM name. |
| `is_foc` | `Boolean` | Yes | `true` when the line is free-of-charge; default `false`. |
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
| `price` | `Decimal @db.Decimal(20, 5)` | Yes | Unit price in transaction currency; default `0`. |
| `sub_total_price` | `Decimal @db.Decimal(20, 5)` | Yes | `price × order_qty` (transaction currency); default `0`. |
| `net_amount` | `Decimal @db.Decimal(20, 5)` | Yes | `sub_total_price − discount_amount`; default `0`. |
| `total_price` | `Decimal @db.Decimal(20, 5)` | Yes | `net_amount + tax_amount`; default `0`. |
| `base_price` | `Decimal @db.Decimal(20, 5)` | Yes | `price × exchange_rate`; default `0`. |
| `base_sub_total_price` | `Decimal @db.Decimal(20, 5)` | Yes | `base_price × order_qty`; default `0`. |
| `base_net_amount` | `Decimal @db.Decimal(20, 5)` | Yes | `base_sub_total_price − base_discount_amount`; default `0`. |
| `base_total_price` | `Decimal @db.Decimal(20, 5)` | Yes | `base_net_amount + base_tax_amount`; default `0`. |
| `received_qty` | `Decimal @db.Decimal(20, 5)` | Yes | Running total of received qty (in order UoM) from GRNs; default `0`. |
| `cancelled_qty` | `Decimal @db.Decimal(20, 5)` | Yes | Qty cancelled / written off from this line; default `0`. |
| `history` | `Json @db.JsonB` | Yes | Per-line stage timeline (`seq`, `name`, `status`, `to_stage`, `message`, `by_id`, `by_name`, `at_date`); default `[]`. |
| `stages_status` | `Json @db.JsonB` | Yes | Per-line stage cursor — array of `{ seq, name, status }`; default `{}`. |
| `current_stage_status` | `String @db.VarChar` | Yes | Working copy of the current stage status. |
| `note` | `String @db.VarChar` | Yes | Free-text note attached to the line. |
| `info` | `Json @db.JsonB` | Yes | Extension bag; default `{}`. |
| `dimension` | `Json @db.JsonB` | Yes | Per-line cost dimensions; default `[]`. |
| `doc_version` | `Int @db.Integer` | No | Optimistic-concurrency version; default `0`. |
| `created_at` | `DateTime @db.Timestamptz(6)` | Yes | Creation timestamp. |
| `created_by_id` | `String @db.Uuid` | Yes | Creator id. |
| `updated_at` | `DateTime @db.Timestamptz(6)` | Yes | Last-update timestamp. |
| `updated_by_id` | `String @db.Uuid` | Yes | Updater id. |
| `deleted_at` | `DateTime @db.Timestamptz(6)` | Yes | Soft-delete timestamp. |
| `deleted_by_id` | `String @db.Uuid` | Yes | Soft-delete actor id. |

**Constraints:** `@id` on `id`. FKs: `purchase_order_id → tb_purchase_order.id`; `product_id → tb_product.id` (required); `tax_profile_id → tb_tax_profile.id`; two named `@relation` FKs into `tb_unit` — `tb_purchase_order_detail_order_unit_idTotb_unit` for `order_unit_id` and `tb_purchase_order_detail_base_unit_idTotb_unit` for `base_unit_id`. Back-relations to `tb_good_received_note_detail`, `tb_purchase_order_detail_comment`, and `tb_purchase_order_detail_tb_purchase_request_detail`.
**Indexes:** `@@unique([purchase_order_id, sequence_no, deleted_at])` as `PO1_purchase_order_detail_sequence_no_u`; `@@index([purchase_order_id])` as `PO1_purchase_order_detail_idx`.

### 2.4 tb_purchase_order_detail_comment

Line-level counterpart of `tb_purchase_order_comment`. Captures comments and system events attached to a single PO line — typically used during approval to record stage-level decisions and during fulfilment to log per-line vendor exchanges.

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `purchase_order_detail_id` | `String @db.Uuid` | No | FK to `tb_purchase_order_detail.id`. |
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

**Constraints:** `@id` on `id`. FK `purchase_order_detail_id → tb_purchase_order_detail.id` (`NoAction` on delete/update).
**Indexes:** None declared beyond the primary key.

### 2.5 tb_purchase_order_detail_tb_purchase_request_detail

Bridge table linking a PO detail row to one or more originating PR detail rows. The same row also denormalises the PR-side qty / unit / location snapshot and tracks per-PR-line received and FOC quantities, so the bridge is both the linkage table and the cursor for "how much of this PR line was already covered by this PO line". See [[purchase-request]] § 2 for the PR-side view.

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `po_detail_id` | `String @db.Uuid` | No | FK to `tb_purchase_order_detail.id`. |
| `pr_detail_id` | `String @db.Uuid` | Yes | FK to `tb_purchase_request_detail.id`. Nullable to allow PO lines that were not sourced from a PR (manual POs) to still write a bridge row if needed. |
| `pr_detail_order_unit_id` | `String @db.Uuid` | Yes | UoM snapshot from the originating PR line. |
| `pr_detail_order_unit_name` | `String @db.VarChar` | Yes | Snapshot of the PR-line UoM name. |
| `pr_detail_qty` | `Decimal @db.Decimal(20, 5)` | Yes | Qty consumed from the PR line (in PR-line UoM); default `0`. |
| `received_qty` | `Decimal @db.Decimal(20, 5)` | Yes | Qty already received against this PR-line allocation; default `0`. |
| `foc_qty` | `Decimal @db.Decimal(20, 5)` | Yes | Free-of-charge qty allocated from this PR line; default `0`. |
| `location_id` | `String @db.Uuid` | Yes | Store / location snapshot from the PR line. |
| `location_code` | `String @db.VarChar` | Yes | Snapshot. |
| `location_name` | `String @db.VarChar` | Yes | Snapshot. |
| `delivery_point_id` | `String @db.Uuid` | Yes | Delivery point snapshot from the PR line. |
| `delivery_point_name` | `String @db.VarChar` | Yes | Snapshot. |
| `pr_detail_base_qty` | `Decimal @db.Decimal(20, 5)` | Yes | Base-UoM equivalent of `pr_detail_qty`; default `0`. |
| `pr_detail_base_unit_id` | `String @db.Uuid` | Yes | Base UoM snapshot from the PR line. |
| `pr_detail_base_unit_name` | `String @db.VarChar` | Yes | Snapshot of the base UoM name. |
| `created_at` | `DateTime @db.Timestamptz(6)` | Yes | Creation timestamp. |
| `created_by_id` | `String @db.Uuid` | Yes | Creator id. |
| `updated_at` | `DateTime @db.Timestamptz(6)` | Yes | Last-update timestamp. |
| `updated_by_id` | `String @db.Uuid` | Yes | Updater id. |
| `deleted_at` | `DateTime @db.Timestamptz(6)` | Yes | Soft-delete timestamp. |
| `deleted_by_id` | `String @db.Uuid` | Yes | Soft-delete actor id. |

**Constraints:** `@id` on `id`. FKs: `po_detail_id → tb_purchase_order_detail.id` (`NoAction`); `pr_detail_id → tb_purchase_request_detail.id` (`NoAction`); `delivery_point_id → tb_delivery_point.id` (`NoAction`); `location_id → tb_location.id` (`NoAction`).
**Indexes:** `@@unique([po_detail_id, pr_detail_id, deleted_at])` as `PO1_purchase_order_purchase_request_detail_u`; `@@index([po_detail_id, pr_detail_id])` as `PO1_purchase_order_purchase_request_detail_idx`; `@@index([pr_detail_id])` as `PO1_purchase_request_detail_idx`.

## 3. Relationships

```
tb_workflow
    │  (workflow_id stored but no Prisma @relation on tb_purchase_order)
    ▼
tb_purchase_order ──1──*──► tb_purchase_order_comment
    │  1
    │
    │ * purchase_order_id
    ▼
tb_purchase_order_detail ──1──*──► tb_purchase_order_detail_comment
    │
    │ FK references (denormalised snapshots on the row)
    ├──► tb_product           (required, product_id)
    ├──► tb_tax_profile       (tax_profile_id)
    └──► tb_unit  ×2          (order_unit_id, base_unit_id — named relations)

tb_purchase_order (header-level FKs)
    ├──► tb_vendor             (vendor_id)
    ├──► tb_currency           (currency_id — named relation)
    └──► tb_credit_term        (credit_term_id)

tb_purchase_request_detail ──*──*──► tb_purchase_order_detail
    via bridge tb_purchase_order_detail_tb_purchase_request_detail
    (po_detail_id, pr_detail_id) — many PR lines → one PO line
    (consolidation); one PR line → many PO lines (partial conversion).
    Bridge row also references tb_location and tb_delivery_point.

tb_purchase_order_detail ──1──*──► tb_good_received_note_detail
    (GRN detail back-references the PO line it fulfils;
     "pending qty" = order_qty − received_qty − cancelled_qty.)
```

Notes:

- **Header → detail** is 1-to-many. The detail's `purchase_order_id` is nullable, which permits orphan / scratch lines but is enforced 1-to-many in practice by the application layer.
- **Header → comment** and **detail → comment** are both 1-to-many. The comment tables are the persistent record of workflow activity; the JSON columns on the header (`workflow_history`, `stages_status`) are the in-place cursor.
- **PR ↔ PO** is many-to-many via `tb_purchase_order_detail_tb_purchase_request_detail` to support PR consolidation (multiple PR lines → one PO line) and partial conversion (one PR line → multiple PO lines). The bridge is also the per-allocation cursor for received and FOC qty.
- **PO → GRN** is 1-to-many via `tb_purchase_order_detail.tb_good_received_note_detail` (back-relation). The PO line's `received_qty` is updated by GRN posting; `received_qty < order_qty − cancelled_qty` means the PO line still has pending fulfilment.
- **Vendor / currency invariant**: vendor, currency, exchange-rate and credit-term live on the header, not the line. This implies every PO line on a given PO shares the same vendor and currency, which is why PR-to-PO conversion must pre-group PRs by `(vendor, currency)`.
- All `@relation` FK declarations use `onDelete: NoAction, onUpdate: NoAction`, so referential integrity is preserved by application-level soft-delete (`deleted_at`) rather than cascade.

## 4. Enums

- **`enum_purchase_order_type`**: `manual` (PO created directly by procurement without an upstream PR), `purchase_request` (PO sourced from one or more PRs via the conversion flow). This is **also the default value on `tb_purchase_order.po_type`** — meaning PR-sourced is the standard procure-to-pay path, and `manual` is the explicit opt-out for procurement-only POs. The same enum is shared between PR and PO documentation because it lives in the tenant schema namespace once.
- **`enum_purchase_order_doc_status`**: document-status enum for `tb_purchase_order.po_status`.
  - `draft` (`ร่าง`) — initial editable state; PO can be modified freely, no commitment to the vendor.
  - `in_progress` (`กำลังดำเนินการ`) — submitted and traversing the approval chain.
  - `voided` (`โมฆะ`) — administratively voided after submission; PO is terminated without fulfilment.
  - `sent` — PO has been sent to the vendor; awaiting first GRN.
  - `partial` — at least one GRN has posted but `received_qty < order_qty − cancelled_qty` on one or more lines; partial fulfilment.
  - `closed` (annotated in Prisma as "closed หยุดหาไม่เจอ") — PO closed before full fulfilment, typically because the vendor cannot supply the outstanding qty; remaining qty is treated as cancelled.
  - `completed` (annotated as "รับครบผ่าน receiving") — every line fully received via GRN; PO is closed normally.
- **`enum_comment_type`** (shared with PR): `user` (human-authored comment), `system` (auto-generated activity-log entry written by the workflow engine). Used by both `tb_purchase_order_comment.type` and `tb_purchase_order_detail_comment.type`.
- **`enum_last_action`** (shared with PR): `submitted`, `approved`, `reviewed`, `rejected` — used by `tb_purchase_order.last_action` to capture the most recent workflow action.

## 5. Divergences from carmen/docs

The legacy `purchase-order-module.md` describes a high-level data dictionary (a thin `purchase_orders` / `purchase_order_items` table sketch) and a state-machine diagram, not Prisma entities. The items below capture material differences that downstream documentation must reconcile.

| # | Item | carmen/docs says | Prisma has | Action |
|---|------|------------------|------------|--------|
| 1 | PO status values | State diagram uses `Draft → Sent → Partial / FullyReceived → Closed`, plus `Voided` and `Deleted` branches. | `enum_purchase_order_doc_status { draft, in_progress, voided, sent, partial, closed, completed }` — adds `in_progress` (approval-chain state, absent from the state diagram) and uses `completed` rather than `FullyReceived`. | Treat Prisma as canonical. Update the state diagram to insert `in_progress` between `draft` and `sent`, and rename `FullyReceived` → `completed`. `Deleted` in the diagram is the soft-delete (`deleted_at`) flag, not a status value. |
| 2 | Reference number column | `purchase_orders.number VARCHAR(20)` | `tb_purchase_order.po_no VARCHAR` (no length cap declared) | Rename `number` → `po_no` in the carmen/docs data dictionary, drop the 20-char cap claim. |
| 3 | PO header data dictionary | Lists `id, number, vendor_id, order_date, status, currency_code, exchange_rate, total_amount, created_by` only (8 columns). | `tb_purchase_order` has ~45 columns including workflow JSON, credit-term snapshot, buyer, history, multiple totals (`total_qty`, `total_price`, `total_tax`, `total_amount`), `is_active`, `info`, `dimension`, `doc_version`, and the full audit set. | The carmen/docs dictionary is illustrative only; do not treat it as a field-complete spec. Cross-reference Section 2.1 of this page instead. |
| 4 | PO line data dictionary | Lists `id, purchase_order_id, item_id, ordered_quantity, unit_price, total_amount, pr_item_id` (7 columns). | `tb_purchase_order_detail` has ~50 columns including separate `order_*` / `base_*` UoM pairs, FOC boolean, full tax + discount columns, transaction- and base-currency totals, `received_qty`, `cancelled_qty`, per-line workflow JSON. Also: there is no `pr_item_id` on the detail row — PR linkage lives on the bridge table `tb_purchase_order_detail_tb_purchase_request_detail`. | Drop `pr_item_id` from the carmen/docs claim; document the bridge table as the canonical PR linkage. Cross-reference Section 2.3 / 2.5 of this page. |
| 5 | PR→PO traceability mechanism | "Each PO item maintains references to its originating PR" (implies a column on the PO line). | Linkage is a many-to-many bridge (`tb_purchase_order_detail_tb_purchase_request_detail`), not a single FK column on the PO line. This is required to support consolidation (many PR → one PO) and partial conversion (one PR → many PO). | Update carmen/docs prose to describe the bridge; the single-FK model would not support the documented vendor+currency grouping behaviour. |
| 6 | Status field name | `purchase_orders.status` | `tb_purchase_order.po_status` (column is `po_status`, not `status`). | Rename in carmen/docs data dictionary. |
| 7 | Reference number format | Not specified in carmen/docs. | `po_no` is `VarChar` with no format constraint at the DB level; format is enforced by the application. | Note in carmen/docs that the format is application-policy, not schema-enforced — parallel to PR. |

## 6. References

- **Primary (source of truth):** Prisma schemas listed in the header callout — concretely `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` (all PO models and both enums) and `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` (verified to contain no PO models).
- **Secondary (concept cross-check):** `../carmen/docs/purchase-order-management/purchase-order-module.md` — high-level business-analysis document; divergences captured in Section 5.
- **Sibling reference:** `en/purchase-request/01-data-model.md` — describes the PR side of the PR↔PO bridge; do not duplicate that material here.
- Related modules: [[purchase-request]] (upstream source), [[good-receive-note]] (downstream fulfilment via `received_qty`), [[product]] (line product reference), [[vendor-pricelist]] (price snapshot at PR-to-PO conversion time), [[inventory]] (on-hand context).

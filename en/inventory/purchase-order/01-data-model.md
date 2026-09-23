---
title: Purchase Order — Data Model
description: Entities, fields, relationships, and enums for the purchase-order module.
published: true
date: '2026-09-22T18:00:00.000Z'
tags: purchase-order, data-model, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T10:00:00.000Z
---

# Purchase Order — Data Model

> **At a Glance**
> **Tables:** `tb_purchase_order` (schema.prisma L2063) &nbsp;·&nbsp; `tb_purchase_order_detail` (L2179) &nbsp;·&nbsp; `tb_purchase_order_comment` (L2144) &nbsp;·&nbsp; `tb_purchase_order_detail_comment` (L2293) &nbsp;·&nbsp; `tb_purchase_order_detail_tb_purchase_request_detail` (L2328, PR↔PO bridge)
> **Audience:** Developer / Auditor (dev reference)
> **Key FKs:** detail `→ tb_product` / `tb_tax_profile` / `tb_unit` ×2 (order + base); header `→ tb_vendor` / `tb_currency` / `tb_credit_term` / `tb_delivery_point` (new 2026-09-15); bridge `→ tb_purchase_request_detail` / `tb_location` / `tb_delivery_point` (many-to-many supports PR consolidation & partial conversion); back-relation from `tb_good_received_note_detail` (downstream GRN)
> **Audit pattern:** standard `created_*` / `updated_*` / `deleted_*`; per-line `received_qty` / `cancelled_qty` running counters; bridge-level `received_qty` / `foc_received_qty` per PR-line allocation; workflow snapshot on header JSON
> **Re-synced 2026-09-22:** status enum `sent` → `sent_or_print` + new `approved` (migrations `20260914080000`, `20260914080100`); header `delivery_point_id/name` (`20260915120000`); bridge `pr_detail_foc_qty` / `foc_received_qty` (`20260916030000`); API response shape now one row = one location with nested entity objects (§ 2.4).

> **Source of truth:** Backend Prisma schema. Always read these first when writing or updating this page:
> - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma`
> - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma`
>
> The `generated/client/schema.prisma` files under each package are auto-generated copies and not authoritative.

## 1. Overview

The purchase-order module owns five tenant-schema entities: the PO document header (`tb_purchase_order`), its line items (`tb_purchase_order_detail`), workflow / activity-log comments at both header and line level (`tb_purchase_order_comment`, `tb_purchase_order_detail_comment`), and the bridge table (`tb_purchase_order_detail_tb_purchase_request_detail`) that links PO lines back to one or more originating PR lines. As with PR, workflow stage tracking is not a dedicated table — it is stored inline on the header as JSON columns (`workflow_history`, `workflow_current_stage`, `stages_status`) plus a foreign key into the shared `tb_workflow` configuration, while the persisted timeline of stage-transition events is captured through the comment tables.

The PO sits **downstream of [purchase-request](/en/inventory/purchase-request)** and **upstream of [good-receive-note](/en/inventory/good-receive-note)** in the procure-to-pay chain. PR-to-PO linkage runs through the bridge table noted above; the same bridge captures per-PR-line received and FOC quantities, supporting both PR consolidation (many PR lines → one PO line) and partial conversion (one PR line → many PO lines). PO lines carry running `received_qty` and `cancelled_qty` columns so that the "pending qty" available for GRN is `order_qty − received_qty − cancelled_qty`; the relation from PO detail to GRN detail (`tb_good_received_note_detail`) is what closes the loop. PO detail rows also reference [product](/en/inventory/product), `tb_tax_profile`, and `tb_unit` (twice — for order UoM and base UoM), and the header references `tb_vendor`, `tb_currency`, and `tb_credit_term`. All PO entities live in the tenant Prisma schema; the platform schema contains no purchase-order models.

The header carries vendor, currency, exchange-rate, credit-term and — since 2026-09-15 — delivery-point context once for the whole PO — by design, every line on a PO shares the same vendor and currency, which is why the PR-to-PO conversion flow must group selected PRs by `(vendor_id, delivery_date, currency_id)` before fan-out (confirmed in `purchase-order.service.ts` `buildPoGroupKey`: `` `${vendor_id}|${yyyy-MM-dd}|${currency_id}` ``; an optional caller-supplied `delivery_date` override replaces the PR line's date in that key, so `groupPrForPo` / `confirmPrToPo` merge lines that would otherwise have split by date). The default value of `tb_purchase_order.po_type` is `purchase_request`, which makes PR-sourced the standard creation path; `manual` is for procurement-only POs with no upstream PR; `pricelist` is a third path — a PO created directly from a vendor price list through a 4-step wizard (`routes/procurement/purchase-order/from-price-list/`), bypassing the PR stage entirely.

**One line = one location.** Since `feat(po)!: location ย้ายมาแบนบน detail` (2026-09-09) a `tb_purchase_order_detail` row is a product going to a single delivery location. The Prisma table itself has no `location_id` column — the location still lives on the bridge row(s) under the line — but the create DTO requires `location_id` per line (`dto/create-purchase-order.dto.ts` L60-69) and the detail serializer lifts `location_id/code/name` and `delivery_point_*` off the junction onto the row (`dto/purchase-order.serializer.ts` L74-80). The former nested `locations[]` breakdown, whose per-location quantities summed to the row's `order_qty`, no longer exists on create payloads or detail responses; it survives only on the GRN-facing `GET .../purchase-orders/grn*` views (`PoForGrnLocationResponseSchema`).

**Concurrency:** updates to this document use [system-config/doc-version](/en/inventory/system-config/doc-version) optimistic locking — the client must echo the current `doc_version` on save or receive a `409 Conflict`.

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
| `delivery_point_id` | `String @db.Uuid` | Yes | FK to `tb_delivery_point.id` — where the whole order is delivered. Added by `20260915120000_po_header_delivery_point`, nullable with no backfill (pre-existing orders genuinely never recorded one). Distinct from the per-line `delivery_point_id` on the PR↔PO bridge, which records where each *source request line* asked for its goods. Populated from the `delivery_point_id` override on `confirm-pr`, or the header form on manual / pricelist POs. |
| `delivery_point_name` | `String @db.VarChar` | Yes | Snapshot of the delivery point name, resolved server-side (`resolvePrToPoOverrides`) so a renamed or deleted delivery point cannot change what a historical order says. |
| `workflow_id` | `String @db.Uuid` | Yes | FK reference to a `tb_workflow` row (no Prisma `@relation` declared on this model — selection is application-resolved). |
| `workflow_name` | `String @db.VarChar` | Yes | Snapshot of the workflow name. |
| `workflow_history` | `Json @db.JsonB` | Yes | Append-only stage-transition timeline; default `[]`. Each entry holds `action`, `at`, `user { id, name }`, `current_stage`, `next_stage` (schema comment L2083). `action` is `submitted \| approved \| reviewed \| rejected \| completed` — `completed` is pushed by `WorkflowOrchestratorService` on final approval and is **not** a member of `enum_last_action`. |
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
| `approval_date` | `DateTime @db.Timestamptz(6)` | Yes | Timestamp when the PO passed its final approval stage (`performApprove` sets it to `workflow.last_action_at_date` together with `po_status = approved`). |
| `email` | `String @db.VarChar` | Yes | Vendor email captured on the header form. Not written by `send-email` — the actual recipients, subject and outcome of each send attempt go to `tb_activity` (`email_sent`), not to this column. |
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

**Constraints:** `@id` on `id`. FKs: `credit_term_id → tb_credit_term.id` (`NoAction`); `currency_id → tb_currency.id` via named relation `tb_purchase_order_currency_idTotb_currency` (`NoAction`); `vendor_id → tb_vendor.id` (`NoAction`); `delivery_point_id → tb_delivery_point.id` (`NoAction`, constraint `tb_purchase_order_delivery_point_id_fkey`). Note: `workflow_id` is stored as a UUID but has no Prisma `@relation` on this model.
**Indexes:** `@@unique([po_no, deleted_at])` as `PO_po_no_u`; `@@index([po_no])` as `PO_po_no_idx`; `@@index([vendor_id])` as `PO_vendor_id_idx`; `PO_delivery_point_id_idx` on `delivery_point_id` (created by the migration SQL; not declared as `@@index` in the Prisma model).

Comment / attachment tables for this module are documented separately — see [01a — Data Model — Comment Tables](/en/inventory/purchase-order/01a-data-model-comments).

### 2.2 tb_purchase_order_detail

PO line item — one product for one delivery location. Carries product reference, order-qty and base-qty pair (single qty/UoM unlike PR which carries requested/approved/FOC triples — FOC on PO is a per-line `is_foc` boolean at table level; the FOC *quantities* `foc_qty` / `foc_received_qty` that the detail response exposes on the row are aggregated from the bridge rows, `purchase-order.service.ts` L767), tax and discount, line totals in transaction and base currency, running received / cancelled qty, and per-line workflow stage history. Note there is **no** `location_id` column on this table even though the API treats the row as single-location — see § 2.4.

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
| `current_stage_status` | `String @db.VarChar` | Yes | Working copy of the current stage status. The Prisma schema declares `enum_stage_action { submit, approve, reject, review, … }` (schema.prisma L2511-2524, "present-tense action verbs for `current_stage_status`") intended to type this column; the column itself remains `String?` (still marked `// temp field`) until a planned migration validates historical values and retypes it. The React footer reads it per line to decide whether the document-level button is Approve / Send Back / Reject (`po-footer-action.tsx` `computePoAction`). |
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

### 2.3 tb_purchase_order_detail_tb_purchase_request_detail

Bridge table linking a PO detail row to one or more originating PR detail rows. The same row also denormalises the PR-side qty / unit / location snapshot and tracks per-PR-line received and FOC quantities, so the bridge is both the linkage table and the cursor for "how much of this PR line was already covered by this PO line". See [purchase-request](/en/inventory/purchase-request) § 2 for the PR-side view.

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `po_detail_id` | `String @db.Uuid` | No | FK to `tb_purchase_order_detail.id`. |
| `pr_detail_id` | `String @db.Uuid` | Yes | FK to `tb_purchase_request_detail.id`. Nullable to allow PO lines that were not sourced from a PR (manual POs) to still write a bridge row if needed. |
| `pr_detail_order_unit_id` | `String @db.Uuid` | Yes | UoM snapshot from the originating PR line. |
| `pr_detail_order_unit_name` | `String @db.VarChar` | Yes | Snapshot of the PR-line UoM name. |
| `pr_detail_qty` | `Decimal @db.Decimal(20, 5)` | Yes | Paid qty ordered from the PR line (in PR-line UoM); default `0`. |
| `received_qty` | `Decimal @db.Decimal(20, 5)` | Yes | Paid qty already received against this PR-line allocation; default `0`. Incremented by GRN posting (`good-received-note.service.ts` L3720 region). |
| `pr_detail_foc_qty` | `Decimal @db.Decimal(20, 5)` | Yes | **New 2026-09-16** (`20260916030000_po_junction_foc_ordered_vs_received`). Free-of-charge qty *ordered* from this PR line; default `0`. Backfilled from `foc_qty` where still at default. Paired with `pr_detail_qty` (ordered side). |
| `foc_received_qty` | `Decimal @db.Decimal(20, 5)` | Yes | **New 2026-09-16.** Free-of-charge qty that actually *arrived*; default `0`. Incremented by GRN posting (`foc_received_qty: { increment }`, `good-received-note.service.ts` L3720) — FOC goods now go to stock (`f8cd9f0d9`, 2026-09-10). Paired with `received_qty`. Summed onto the PO line as `foc_received_qty` in the detail response and shown under the FOC / GRN column. |
| `foc_qty` | `Decimal @db.Decimal(20, 5)` | Yes | **Superseded** by `pr_detail_foc_qty`. Kept only so the expand migration could run while old services were still deployed; nothing writes it any more and a later migration drops it (schema comment). Do not read it in new code. |
| `location_id` | `String @db.Uuid` | Yes | Store / location for this allocation. Since 2026-09-09 this is the line's single delivery location (lifted onto the detail response as `location`). |
| `location_code` | `String @db.VarChar` | Yes | Snapshot. |
| `location_name` | `String @db.VarChar` | Yes | Snapshot. |
| `delivery_point_id` | `String @db.Uuid` | Yes | Delivery point snapshot from the PR line. |
| `delivery_point_name` | `String @db.VarChar` | Yes | Snapshot. |
| `pr_detail_base_qty` | `Decimal @db.Decimal(20, 5)` | Yes | Base-UoM equivalent of `pr_detail_qty`; default `0`. |
| `pr_detail_base_unit_id` | `String @db.Uuid` | Yes | Base UoM snapshot from the PR line. |
| `pr_detail_base_unit_name` | `String @db.VarChar` | Yes | Snapshot of the base UoM name (`fix(po): junction เก็บจำนวนฐานโดยไม่มีหน่วยกำกับ`, 2026-09-17 — previously null on every row). |
| `price`, `sub_total_price`, `net_amount`, `total_price` | `Decimal @db.Decimal(20, 5)` | Yes | Per-allocation money in transaction currency (mirrors the detail row so each location can carry its own price; `20260709120000_add_po_pr_detail_location_price_tax_discount`); default `0`. |
| `base_price`, `base_sub_total_price`, `base_net_amount`, `base_total_price` | `Decimal @db.Decimal(20, 5)` | Yes | Same in base currency; default `0`. |
| `tax_profile_id`, `tax_profile_name`, `tax_rate`, `tax_amount`, `base_tax_amount`, `is_tax_adjustment` | mixed | Yes | Per-allocation tax snapshot (`tax_rate` is `Decimal(15, 5)`). |
| `discount_rate`, `discount_amount`, `base_discount_amount`, `is_discount_adjustment` | mixed | Yes | Per-allocation discount snapshot. |
| `doc_version` | `Int @db.Integer` | No | Optimistic-concurrency version; default `0`. |
| `created_at` | `DateTime @db.Timestamptz(6)` | Yes | Creation timestamp. |
| `created_by_id` | `String @db.Uuid` | Yes | Creator id. |
| `updated_at` | `DateTime @db.Timestamptz(6)` | Yes | Last-update timestamp. |
| `updated_by_id` | `String @db.Uuid` | Yes | Updater id. |
| `deleted_at` | `DateTime @db.Timestamptz(6)` | Yes | Soft-delete timestamp. |
| `deleted_by_id` | `String @db.Uuid` | Yes | Soft-delete actor id. |

**Constraints:** `@id` on `id`. FKs: `po_detail_id → tb_purchase_order_detail.id` (`NoAction`); `pr_detail_id → tb_purchase_request_detail.id` (`NoAction`); `delivery_point_id → tb_delivery_point.id` (`NoAction`); `location_id → tb_location.id` (`NoAction`).
**Indexes:** `@@unique([po_detail_id, pr_detail_id, deleted_at])` as `PO1_purchase_order_purchase_request_detail_u`; `@@index([po_detail_id, pr_detail_id])` as `PO1_purchase_order_purchase_request_detail_idx`; `@@index([pr_detail_id])` as `PO1_purchase_request_detail_idx`.

### 2.4 API response shape (`GET .../purchase-orders/:id`) — one row = one location, nested entity refs

The wire shape diverged from the tables twice since 2026-07-29, and the React types (`carmen-inventory-frontend-react/types/purchase-order.ts`) are the executable record of it:

```
PurchaseOrder
  po_status            enum (draft | in_progress | approved | sent_or_print | partial | closed | completed — voided never appears in the UI enum)
  vendor, currency     EntityRef { id, name/code }   ← nested objects since 2026-09-17 (@ExpandRefs / @CollapseRefs), not vendor_id / vendor_name
  buyer, workflow, credit_term   EntityRef | null   (detail endpoint only)
  purchase_order_detail[]
    product, order_unit, base_unit, tax_profile   EntityRef | null
    location, delivery_point                       EntityRef | null   ← the line's single location, lifted off the bridge row
    order_qty, price, …money…, is_foc
    foc_qty, foc_received_qty                      aggregated from bridge rows
    current_stage_status, stages_status, history[] (PoItemHistoryEntry: at, seq, name, user, status, message)
    pr_details[]                                   PrDetailRef
      pr_detail   EntityRef | null
      pr_id, pr_no                                 null on manual / pricelist rows
      grn[]       { grn_id, grn_no }               receipts against this allocation (2e38ba899, 2026-09-21)
      order_qty, order_base_qty, received_qty, foc_qty, foc_received_qty
```

Write payloads (`PoDetailPayload`) still send flat ids — `location_id`, `location_code`, `location_name`, `delivery_point_id`, `delivery_point_name`, `pr_details[] { pr_detail_id, … }` — because the read and write contracts changed on different dates. A manual / pricelist line has `pr_details = []`, so it can never show a GRN label on the detail screen even after receipt: `grn[]` hangs under `pr_details`, and the backend has nowhere else to put it (`pr-source-button.tsx` comment). `received_qty` for the paid quantity is likewise summed from `pr_details[]` by the client, whereas `foc_received_qty` arrives on the row.

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
    ├──► tb_credit_term        (credit_term_id)
    └──► tb_delivery_point     (delivery_point_id — header-level, since 2026-09-15)

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
- **PO → GRN** is 1-to-many via `tb_purchase_order_detail.tb_good_received_note_detail` (back-relation). The PO line's `received_qty` is updated by GRN posting; `received_qty < order_qty − cancelled_qty` means the PO line still has pending fulfilment. GRN posting also increments the bridge row's `received_qty` and `foc_received_qty`, and then recomputes the header status (`good-received-note.logic.ts` `updatePoStatuses`: every line `received_qty ≥ order_qty − cancelled_qty` → `completed`, else `partial`) — regardless of whether the PO was `approved` or `sent_or_print` before the receipt.
- **One line = one location** (2026-09-09): the location is still stored on the bridge row, not on the detail row, but the application enforces exactly one location per detail (`location_id` required in the create DTO) and lifts it onto the response (§ 2.4).
- **Vendor / currency invariant**: vendor, currency, exchange-rate and credit-term live on the header, not the line. This implies every PO line on a given PO shares the same vendor and currency, which is why PR-to-PO conversion must pre-group PR lines by `(vendor_id, delivery_date, currency_id)` (`buildPoGroupKey`) — the delivery-date dimension additionally splits same-vendor, same-currency lines with different delivery dates into separate POs.
- All `@relation` FK declarations use `onDelete: NoAction, onUpdate: NoAction`, so referential integrity is preserved by application-level soft-delete (`deleted_at`) rather than cascade.

## 4. Enums

- **`enum_purchase_order_type`**: `manual` (PO created directly by procurement without an upstream PR), `purchase_request` (PO sourced from one or more PRs via the conversion flow), `pricelist` (PO created directly from a vendor price list via the 4-step from-price-list wizard, no upstream PR). `purchase_request` is **also the default value on `tb_purchase_order.po_type`** — meaning PR-sourced is the standard procure-to-pay path; `manual` and `pricelist` are the two explicit opt-outs for procurement-only / catalog-driven POs. The same enum is shared between PR and PO documentation because it lives in the tenant schema namespace once.
- **`enum_purchase_order_doc_status`** (schema.prisma L246-255): document-status enum for `tb_purchase_order.po_status`. **Changed 2026-09-14** — `sent` was renamed `sent_or_print` and a new `approved` member was inserted before it; every row that was `sent` was reclassified to `approved` because the old code set `sent` at final approval, before anything had actually been sent (`20260914080100_po_status_backfill_and_rename_sent`).
  - `draft` (`ร่าง`) — initial editable state; PO can be modified freely, no commitment to the vendor.
  - `in_progress` (`กำลังดำเนินการ`) — submitted and traversing the approval chain.
  - `voided` (`โมฆะ`) — terminal outcome of `/reject` from `in_progress`; PO is terminated without fulfilment.
  - `approved` (`อนุมัติ`) — **new.** Passed the final approval stage (`performApprove`, `purchase-order.logic.ts` L433-435). Receivable by GRN from here. Says nothing about whether the vendor has seen the order.
  - `sent_or_print` ("sent to vendor") — **renamed from `sent`.** The vendor actually has the document: reached by `send-email` success or `mark-sent`, both `updateMany where po_status = approved` (`markPoAsSent`, service L7218). Awaiting first GRN (or already partially received before the send).
  - `partial` — at least one GRN has posted but `received_qty < order_qty − cancelled_qty` on one or more lines; partial fulfilment.
  - `closed` (annotated in Prisma as "closed หยุดหาไม่เจอ") — PO cancelled or closed before full fulfilment, typically because the vendor cannot supply the outstanding qty; remaining qty is written to `cancelled_qty`.
  - `completed` (annotated as "รับครบผ่าน receiving") — every line fully received via GRN; PO is closed normally.
  - Period-end treats `completed`, `closed`, `voided` as complete (`period-end.validate.ts` `PO_COMPLETE`); every other status counts as an open PO when a period is closed.
- **`enum_comment_type`** (shared with PR): `user` (human-authored comment), `system` (auto-generated activity-log entry written by the workflow engine). Used by both `tb_purchase_order_comment.type` and `tb_purchase_order_detail_comment.type`.
- **`enum_last_action`** (shared with PR): `submitted`, `approved`, `reviewed`, `rejected` — used by `tb_purchase_order.last_action` to capture the most recent workflow action.

## 5. Divergences from carmen/docs

The legacy `purchase-order-module.md` describes a high-level data dictionary (a thin `purchase_orders` / `purchase_order_items` table sketch) and a state-machine diagram, not Prisma entities. The items below capture material differences that downstream documentation must reconcile.

| # | Item | carmen/docs says | Prisma has | Action |
|---|------|------------------|------------|--------|
| 1 | PO status values | State diagram uses `Draft → Sent → Partial / FullyReceived → Closed`, plus `Voided` and `Deleted` branches (`purchase-order-module.md` L220-229, incl. `Sent --> Voided: Void`). | `enum_purchase_order_doc_status { draft, in_progress, voided, approved, sent_or_print, partial, closed, completed }` — adds `in_progress` (approval-chain state) and `approved` (post-approval, pre-send), renames `Sent` → `sent_or_print`, uses `completed` rather than `FullyReceived`, and has no `Sent → Voided` path (cancel/close land on `closed`). | Treat Prisma as canonical. `Deleted` in the diagram is the soft-delete (`deleted_at`) flag, not a status value. |
| 1b | Header delivery point | Not modelled. | `tb_purchase_order.delivery_point_id/name` (2026-09-15). | Add to the carmen/docs data dictionary. |
| 1c | FOC on PO line | Single `foc` concept. | Bridge row splits ordered (`pr_detail_foc_qty`) from received (`foc_received_qty`); FOC now posts to stock on GRN. | Document the ordered/received pair. |
| 2 | Reference number column | `purchase_orders.number VARCHAR(20)` | `tb_purchase_order.po_no VARCHAR` (no length cap declared) | Rename `number` → `po_no` in the carmen/docs data dictionary, drop the 20-char cap claim. |
| 3 | PO header data dictionary | Lists `id, number, vendor_id, order_date, status, currency_code, exchange_rate, total_amount, created_by` only (8 columns). | `tb_purchase_order` has ~45 columns including workflow JSON, credit-term snapshot, buyer, history, multiple totals (`total_qty`, `total_price`, `total_tax`, `total_amount`), `is_active`, `info`, `dimension`, `doc_version`, and the full audit set. | The carmen/docs dictionary is illustrative only; do not treat it as a field-complete spec. Cross-reference Section 2.1 of this page instead. |
| 4 | PO line data dictionary | Lists `id, purchase_order_id, item_id, ordered_quantity, unit_price, total_amount, pr_item_id` (7 columns). | `tb_purchase_order_detail` has ~50 columns including separate `order_*` / `base_*` UoM pairs, FOC boolean, full tax + discount columns, transaction- and base-currency totals, `received_qty`, `cancelled_qty`, per-line workflow JSON. Also: there is no `pr_item_id` on the detail row — PR linkage lives on the bridge table `tb_purchase_order_detail_tb_purchase_request_detail`. | Drop `pr_item_id` from the carmen/docs claim; document the bridge table as the canonical PR linkage. Cross-reference Section 2.2 / 2.3 of this page. |
| 5 | PR→PO traceability mechanism | "Each PO item maintains references to its originating PR" (implies a column on the PO line). | Linkage is a many-to-many bridge (`tb_purchase_order_detail_tb_purchase_request_detail`), not a single FK column on the PO line. This is required to support consolidation (many PR → one PO) and partial conversion (one PR → many PO). | Update carmen/docs prose to describe the bridge; the single-FK model would not support the documented `(vendor, delivery_date, currency)` grouping behaviour. |
| 6 | Status field name | `purchase_orders.status` | `tb_purchase_order.po_status` (column is `po_status`, not `status`). | Rename in carmen/docs data dictionary. |
| 7 | Reference number format | Not specified in carmen/docs. | `po_no` is `VarChar` with no format constraint at the DB level; format is enforced by the application. | Note in carmen/docs that the format is application-policy, not schema-enforced — parallel to PR. |

## 6. References

- **Primary (source of truth):** Prisma schemas listed in the header callout — concretely `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` (all PO models and both enums) and `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` (verified to contain no PO models). Migrations since baseline: `20260914080000_po_status_add_approved`, `20260914080100_po_status_backfill_and_rename_sent`, `20260915120000_po_header_delivery_point`, `20260916030000_po_junction_foc_ordered_vs_received` (all under `prisma/migrations/`).
- **Wire contract:** `../carmen-turborepo-backend-v2/apps/micro-business/src/procurement/purchase-order/dto/purchase-order.serializer.ts` (response) and `dto/create-purchase-order.dto.ts` (payload); `../carmen-inventory-frontend-react/types/purchase-order.ts` (client-side mirror, with the change notes quoted in § 2.4).
- **Secondary (concept cross-check):** `../carmen/docs/purchase-order-management/purchase-order-module.md` — high-level business-analysis document; divergences captured in Section 5.
- **Sibling reference:** `en/purchase-request/01-data-model.md` — describes the PR side of the PR↔PO bridge; do not duplicate that material here.
- Related modules: [purchase-request](/en/inventory/purchase-request) (upstream source), [good-receive-note](/en/inventory/good-receive-note) (downstream fulfilment via `received_qty`), [product](/en/inventory/product) (line product reference), [vendor-pricelist](/en/inventory/vendor-pricelist) (price snapshot at PR-to-PO conversion time), [inventory](/en/inventory/inventory) (on-hand context).

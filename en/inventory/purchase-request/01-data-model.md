---
title: Purchase Request — Data Model
description: Entities, fields, relationships, and enums for the purchase-request module.
published: true
date: 2026-05-20T00:00:00.000Z
tags: purchase-request, data-model, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T09:00:00.000Z
---

# Purchase Request — Data Model

> **At a Glance**
> **Tables:** `tb_purchase_request` &nbsp;·&nbsp; `tb_purchase_request_detail` &nbsp;·&nbsp; `tb_purchase_request_comment` &nbsp;·&nbsp; `tb_purchase_request_detail_comment` &nbsp;·&nbsp; `tb_purchase_request_template` / `_detail` (recurring orders)
> **Audience:** Developer / Auditor (dev reference)
> **Key FKs:** header `→ tb_workflow`; detail `→ tb_product` / `tb_vendor` / `tb_pricelist_detail` / `tb_location` / `tb_delivery_point` / `tb_unit` ×3 (requested + approved + FOC); many-to-many bridge to PO via `tb_purchase_order_detail_tb_purchase_request_detail`
> **Audit pattern:** standard `created_*` / `updated_*` / `deleted_*`; three-qty per line (`requested` / `approved` / FOC); per-line `history` / `stages_status` JSON for workflow

> **Source of truth:** Backend Prisma schema. Always read these first when writing or updating this page:
> - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma`
> - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma`
>
> The `generated/client/schema.prisma` files under each package are auto-generated copies and not authoritative.

## 1. Overview

The purchase-request module owns six tenant-schema entities: the document header (`tb_purchase_request`), its line items (`tb_purchase_request_detail`), workflow / activity-log comments at both header and line level (`tb_purchase_request_comment`, `tb_purchase_request_detail_comment`), and a reusable template pair (`tb_purchase_request_template`, `tb_purchase_request_template_detail`) for recurring requests such as monthly market-list orders. Workflow stage tracking is not a separate table — it lives inline on the header as JSON columns (`workflow_history`, `workflow_current_stage`, `stages_status`) plus a foreign key into the shared `tb_workflow` configuration table, while the persisted timeline of submit/approve/reject/send-back events is captured through the comment table.

The PR sits upstream of [purchase-order](/en/inventory/purchase-order) in the procure-to-pay chain. Approved PR lines are linked to the resulting PO line through the bridge table `tb_purchase_order_detail_tb_purchase_request_detail` (one PO line can fan in from many PR lines for consolidation; one PR line can fan out across multiple POs for partial conversion). PR detail rows also reference [product](/en/inventory/product), [vendor-pricelist](/en/inventory/vendor-pricelist), `tb_tax_profile`, `tb_currency`, `tb_unit`, `tb_location`, `tb_delivery_point`, and `tb_vendor`, denormalising lookup fields (codes, names, snapshot prices) onto the line at submission time so historical PR data remains stable even when master records change. All PR entities live in the tenant Prisma schema; the platform schema contains no purchase-request models.

## 2. Entities

### 2.1 tb_purchase_request

PR document header. Carries reference number, requestor and department context, workflow snapshot, base-currency totals, and audit columns. One header has many detail rows and many comments.

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key, generated via `gen_random_uuid()`. |
| `pr_no` | `String @db.VarChar` | No | Human-readable PR reference number (e.g. `PR-2301-0001`). |
| `pr_date` | `DateTime @db.Timestamptz(6)` | Yes | Document date the requestor selects on submission. |
| `description` | `String @db.VarChar` | Yes | Free-text description / justification entered on the header. |
| `workflow_id` | `String @db.Uuid` | Yes | FK into `tb_workflow` — selects the approval-chain definition this PR follows. |
| `workflow_name` | `String @db.VarChar` | Yes | Snapshot of the workflow name at submission. |
| `workflow_history` | `Json @db.JsonB` | Yes | Append-only timeline of stage transitions; default `[]`. Each entry holds `stage`, `action`, `message`, `by`, `at`. |
| `workflow_current_stage` | `String @db.VarChar` | Yes | Slug of the stage currently holding the PR. |
| `workflow_previous_stage` | `String @db.VarChar` | Yes | Slug of the stage that just released the PR. |
| `workflow_next_stage` | `String @db.VarChar` | Yes | Slug of the next stage in the chain. |
| `user_action` | `Json @db.JsonB` | Yes | Pending-action metadata, default `{}`. Typically `{ "execute": [{ "id": "<user-id>" }, ...] }` listing who can act next. |
| `last_action` | `enum_last_action` | Yes | Last action taken on the document; default `submitted`. |
| `last_action_at_date` | `DateTime @db.Timestamptz(6)` | Yes | Timestamp of `last_action`. |
| `last_action_by_id` | `String @db.Uuid` | Yes | User id who performed `last_action`. |
| `last_action_by_name` | `String @db.VarChar` | Yes | Snapshot of the actor's name. |
| `pr_status` | `enum_purchase_request_doc_status` | Yes | Document status; default `draft`. |
| `requestor_id` | `String @db.Uuid` | Yes | User id who raised the PR. |
| `requestor_name` | `String @db.VarChar` | Yes | Snapshot of the requestor's display name. |
| `department_id` | `String @db.Uuid` | Yes | Department the PR belongs to. |
| `department_name` | `String @db.VarChar` | Yes | Snapshot of the department name. |
| `base_net_amount` | `Decimal @db.Decimal(15, 5)` | No | Roll-up of line `base_net_amount`; default `0`. |
| `base_total_amount` | `Decimal @db.Decimal(15, 5)` | No | Roll-up of line `base_total_price` (net + tax); default `0`. |
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

**Constraints:** `@id` on `id`. FK `workflow_id → tb_workflow.id` (`NoAction` on delete/update).
**Indexes:** `@@unique([pr_no, deleted_at])` as `PR0_pr_no_u`; `@@index([pr_no])` as `PR0_pr_no_idx`; `@@index([requestor_id])` as `PR0_requestor_id_idx`.

### 2.2 tb_purchase_request_detail

PR line item. Carries product reference, qty / unit triples (requested, approved, FOC), vendor and pricelist snapshot, tax and discount, line totals in both transaction and base currency, and per-line workflow stage history.

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `purchase_request_id` | `String @db.Uuid` | Yes | FK to `tb_purchase_request.id`. Nullable to support draft lines unattached to a header. |
| `sequence_no` | `Int` | Yes | Line ordering within the PR; default `1`. |
| `location_id` | `String @db.Uuid` | Yes | Store / location needing the item. |
| `location_code` | `String @db.VarChar` | Yes | Snapshot of location code. |
| `location_name` | `String @db.VarChar` | Yes | Snapshot of location name. |
| `delivery_point_id` | `String @db.Uuid` | Yes | Specific delivery point. |
| `delivery_point_name` | `String @db.VarChar` | Yes | Snapshot. |
| `delivery_date` | `DateTime @db.Timestamptz(6)` | Yes | Required delivery date for this line. |
| `product_id` | `String @db.Uuid` | No | FK to `tb_product.id`. Required. |
| `product_code` | `String @db.VarChar` | Yes | Snapshot of product code. |
| `product_name` | `String @db.VarChar` | Yes | Snapshot. |
| `product_local_name` | `String @db.VarChar` | Yes | Localised product name snapshot. |
| `product_sku` | `String @db.VarChar` | Yes | Snapshot of SKU. |
| `inventory_unit_id` | `String @db.Uuid` | Yes | Inventory base unit at submission. |
| `inventory_unit_name` | `String @db.VarChar` | Yes | Snapshot. |
| `description` | `String @db.VarChar` | Yes | Line description (often overrides product name for free-text lines). |
| `comment` | `String @db.VarChar` | Yes | Line-level comment. |
| `vendor_id` | `String @db.Uuid` | Yes | FK to `tb_vendor.id` — the allocated vendor for this line. |
| `vendor_name` | `String @db.VarChar` | Yes | Snapshot. |
| `pricelist_detail_id` | `String @db.Uuid` | Yes | FK to `tb_pricelist_detail.id` — the pricelist row the price came from. |
| `pricelist_no` | `String @db.VarChar` | Yes | Snapshot of pricelist reference number. |
| `pricelist_unit` | `String @db.VarChar` | Yes | Snapshot of pricelist UoM. |
| `pricelist_price` | `Decimal @db.Decimal(20, 5)` | Yes | Snapshot of unit price from pricelist; default `0`. |
| `pricelist_type` | `enum_pricelist_compare_type` | Yes | How this price was selected (`automatic` default). |
| `currency_id` | `String @db.Uuid` | Yes | FK to `tb_currency.id` — transaction currency. |
| `currency_code` | `String @db.VarChar` | Yes | Snapshot. |
| `exchange_rate` | `Decimal @db.Decimal(15, 5)` | Yes | Transaction-to-base exchange rate; default `1`. |
| `exchange_rate_date` | `DateTime @db.Timestamptz(6)` | Yes | Effective date of the exchange rate snapshot. |
| `requested_qty` | `Decimal @db.Decimal(20, 5)` | Yes | Qty in requested UoM; default `0`. |
| `requested_unit_id` | `String @db.Uuid` | Yes | UoM the requestor entered. |
| `requested_unit_name` | `String @db.VarChar` | Yes | Snapshot. |
| `requested_unit_conversion_factor` | `Decimal @db.Decimal(20, 5)` | Yes | Conversion factor to inventory base UoM. |
| `requested_base_qty` | `Decimal @db.Decimal(20, 5)` | Yes | `requested_qty × requested_unit_conversion_factor`. |
| `approved_qty` | `Decimal @db.Decimal(20, 5)` | Yes | Qty in approved UoM; may differ from `requested_qty`. |
| `approved_unit_id` | `String @db.Uuid` | Yes | UoM used for the approved qty. |
| `approved_unit_name` | `String @db.VarChar` | Yes | Snapshot. |
| `approved_unit_conversion_factor` | `Decimal @db.Decimal(20, 5)` | Yes | Conversion factor to base UoM. |
| `approved_base_qty` | `Decimal @db.Decimal(20, 5)` | Yes | `approved_qty × approved_unit_conversion_factor`. |
| `foc_qty` | `Decimal @db.Decimal(20, 5)` | Yes | Free-of-charge qty in FOC UoM; default `0`. |
| `foc_unit_id` | `String @db.Uuid` | Yes | UoM for FOC qty. |
| `foc_unit_name` | `String @db.VarChar` | Yes | Snapshot. |
| `foc_unit_conversion_factor` | `Decimal @db.Decimal(20, 5)` | Yes | Conversion factor to base UoM. |
| `foc_base_qty` | `Decimal @db.Decimal(20, 5)` | Yes | `foc_qty × foc_unit_conversion_factor`. |
| `tax_profile_id` | `String @db.Uuid` | Yes | FK to `tb_tax_profile.id`. |
| `tax_profile_name` | `String @db.VarChar` | Yes | Snapshot. |
| `tax_rate` | `Decimal @db.Decimal(15, 5)` | Yes | Effective tax rate; default `0`. |
| `tax_amount` | `Decimal @db.Decimal(20, 5)` | Yes | Tax amount in transaction currency. |
| `base_tax_amount` | `Decimal @db.Decimal(20, 5)` | Yes | Tax amount in base currency. |
| `is_tax_adjustment` | `Boolean` | Yes | `true` when the user manually overrode the tax amount; default `false`. |
| `discount_rate` | `Decimal @db.Decimal(15, 5)` | Yes | Discount rate %; default `0`. |
| `discount_amount` | `Decimal @db.Decimal(20, 5)` | Yes | Discount amount in transaction currency. |
| `base_discount_amount` | `Decimal @db.Decimal(20, 5)` | Yes | Discount amount in base currency. |
| `is_discount_adjustment` | `Boolean` | Yes | `true` when the user manually overrode the discount; default `false`. |
| `sub_total_price` | `Decimal @db.Decimal(20, 5)` | Yes | `pricelist_price × approved_qty` (transaction currency). |
| `net_amount` | `Decimal @db.Decimal(20, 5)` | Yes | `sub_total_price − discount_amount`. |
| `total_price` | `Decimal @db.Decimal(20, 5)` | Yes | `net_amount + tax_amount`. |
| `base_price` | `Decimal @db.Decimal(20, 5)` | Yes | `pricelist_price × exchange_rate`. |
| `base_sub_total_price` | `Decimal @db.Decimal(20, 5)` | Yes | `base_price × approved_qty`. |
| `base_net_amount` | `Decimal @db.Decimal(20, 5)` | Yes | `base_sub_total_price − base_discount_amount`. |
| `base_total_price` | `Decimal @db.Decimal(20, 5)` | Yes | `base_net_amount + base_tax_amount`. |
| `history` | `Json @db.JsonB` | Yes | Per-line stage timeline (`seq`, `name`, `status`, `to_stage`, `message`, `by_id`, `by_name`, `at_date`); default `[]`. |
| `stages_status` | `Json @db.JsonB` | Yes | Per-line stage cursor — array of `{ seq, name, status }`; default `{}`. |
| `current_stage_status` | `String @db.VarChar` | Yes | Working copy of the current stage status. The Prisma schema declares `enum_stage_action { submit, approve, reject, review, pending }` (May 2026 enum-cleanup pass) intended to type this column; the column itself remains `String?` until a planned migration validates historical values and retypes it. Treat values outside `enum_stage_action` as legacy data that the migration will normalise. |
| `info` | `Json @db.JsonB` | Yes | Extension bag; default `{}`. |
| `dimension` | `Json @db.JsonB` | Yes | Per-line cost dimensions; default `[]`. |
| `doc_version` | `Int @db.Integer` | No | Optimistic-concurrency version; default `0`. |
| `created_at` | `DateTime @db.Timestamptz(6)` | Yes | Creation timestamp. |
| `created_by_id` | `String @db.Uuid` | Yes | Creator id. |
| `updated_at` | `DateTime @db.Timestamptz(6)` | Yes | Last-update timestamp. |
| `updated_by_id` | `String @db.Uuid` | Yes | Updater id. |
| `deleted_at` | `DateTime @db.Timestamptz(6)` | Yes | Soft-delete timestamp. |
| `deleted_by_id` | `String @db.Uuid` | Yes | Soft-delete actor id. |

**Constraints:** `@id` on `id`. FKs: `purchase_request_id → tb_purchase_request.id`; `product_id → tb_product.id` (required); `vendor_id → tb_vendor.id`; `pricelist_detail_id → tb_pricelist_detail.id`; `tax_profile_id → tb_tax_profile.id`; `currency_id → tb_currency.id`; `location_id → tb_location.id`; `delivery_point_id → tb_delivery_point.id`; three named `@relation` FKs into `tb_unit` for requested / approved / FOC unit.
**Indexes:** `@@unique([purchase_request_id, product_id, location_id, dimension, deleted_at])` as `PR1_purchase_request_product_location_dimension_u`; `@@index([product_id])` as `PRD1_product_id_idx`; `@@index([location_id])` as `PRD1_location_id_idx`; `@@index([location_id, product_id])` as `PRD1_location_product_idx`; `@@index([purchase_request_id])` as `PRD1_purchase_request_id_idx`.

### 2.3 tb_purchase_request_comment

Workflow / activity-log entries attached to a PR header. The Prisma schema has no dedicated `tb_purchase_request_workflow` table — this comment table, combined with the JSON workflow columns on the header, is the persistent record of the workflow timeline. Each row is either a user comment (`type = user`) or a system event (`type = system`) such as a stage transition.

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `purchase_request_id` | `String @db.Uuid` | No | FK to `tb_purchase_request.id`. |
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

**Constraints:** `@id` on `id`. FK `purchase_request_id → tb_purchase_request.id` (`NoAction` on delete/update).
**Indexes:** None declared beyond the primary key.

### 2.4 tb_purchase_request_detail_comment

Line-level counterpart of `tb_purchase_request_comment`. Captures comments and system events attached to a single PR line — typically used during approval to record stage-level decisions and rejection reasons per line.

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `purchase_request_detail_id` | `String @db.Uuid` | No | FK to `tb_purchase_request_detail.id`. |
| `type` | `enum_comment_type` | No | `user` or `system`; default `user`. |
| `user_id` | `String @db.Uuid` | Yes | Author user id. |
| `message` | `String` | Yes | Free-text comment body. |
| `attachments` | `Json @db.JsonB` | Yes | Array of attachments; default `[]`. |
| `created_at` | `DateTime @db.Timestamptz(6)` | Yes | Creation timestamp. |
| `created_by_id` | `String @db.Uuid` | Yes | Creator id. |
| `updated_at` | `DateTime @db.Timestamptz(6)` | Yes | Last-update timestamp. |
| `updated_by_id` | `String @db.Uuid` | Yes | Updater id. |
| `deleted_at` | `DateTime @db.Timestamptz(6)` | Yes | Soft-delete timestamp. |
| `deleted_by_id` | `String @db.Uuid` | Yes | Soft-delete actor id. |

**Constraints:** `@id` on `id`. FK `purchase_request_detail_id → tb_purchase_request_detail.id`.
**Indexes:** None declared beyond the primary key.

### 2.5 tb_purchase_request_template

Header for a reusable PR template (e.g. a weekly market-list set). Templates do not themselves enter a workflow — they seed new PRs.

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `name` | `String @db.VarChar` | No | Template name. |
| `description` | `String @db.VarChar` | Yes | Free-text description. |
| `workflow_id` | `String @db.Uuid` | Yes | FK into `tb_workflow` — default workflow for PRs spawned from this template. |
| `workflow_name` | `String @db.VarChar` | Yes | Snapshot of workflow name. |
| `is_active` | `Boolean` | Yes | Whether the template is selectable; default `true`. |
| `note` | `String @db.VarChar` | Yes | Free-text note. |
| `info` | `Json @db.JsonB` | Yes | Extension bag; default `{}`. |
| `dimension` | `Json @db.JsonB` | Yes | Default cost dimensions; default `[]`. |
| `created_at` | `DateTime @db.Timestamptz(6)` | Yes | Creation timestamp. |
| `created_by_id` | `String @db.Uuid` | Yes | Creator id. |
| `updated_at` | `DateTime @db.Timestamptz(6)` | Yes | Last-update timestamp. |
| `updated_by_id` | `String @db.Uuid` | Yes | Updater id. |
| `deleted_at` | `DateTime @db.Timestamptz(6)` | Yes | Soft-delete timestamp. |
| `deleted_by_id` | `String @db.Uuid` | Yes | Soft-delete actor id. |

**Constraints:** `@id` on `id`. FK `workflow_id → tb_workflow.id`.
**Indexes:** `@@unique([name, workflow_id, deleted_at])` as `PRT1_name_workflow_id_u`; `@@index([workflow_id])` as `PRT1_workflow_id_idx`; `@@index([name])` as `PRT1_name_idx`.

### 2.6 tb_purchase_request_template_detail

Line item belonging to a PR template. Schema mirrors `tb_purchase_request_detail` for the fields a template needs to seed — product, location, requested qty / unit, FOC, tax, discount, currency — but deliberately omits approval-side fields (`approved_qty`, `approved_unit_*`, workflow `history`, `stages_status`) and the `vendor_id` / `pricelist_detail_id` columns; those are set at PR creation time, not stored on the template.

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `purchase_request_template_id` | `String @db.Uuid` | Yes | FK to `tb_purchase_request_template.id`. |
| `location_id` | `String @db.Uuid` | Yes | Store / location. |
| `location_code` | `String @db.VarChar` | Yes | Snapshot. |
| `location_name` | `String @db.VarChar` | Yes | Snapshot. |
| `delivery_point_id` | `String @db.Uuid` | Yes | Delivery point. |
| `delivery_point_name` | `String @db.VarChar` | Yes | Snapshot. |
| `product_id` | `String @db.Uuid` | No | FK to `tb_product.id`. Required. |
| `product_code` | `String @db.VarChar` | Yes | Snapshot. |
| `product_name` | `String @db.VarChar` | Yes | Snapshot. |
| `product_local_name` | `String @db.VarChar` | Yes | Snapshot. |
| `product_sku` | `String @db.VarChar` | Yes | Snapshot. |
| `inventory_unit_id` | `String @db.Uuid` | Yes | Inventory base unit. |
| `inventory_unit_name` | `String @db.VarChar` | Yes | Snapshot. |
| `description` | `String @db.VarChar` | Yes | Line description. |
| `comment` | `String @db.VarChar` | Yes | Line comment. |
| `currency_id` | `String @db.Uuid` | Yes | FK to `tb_currency.id`. |
| `currency_code` | `String @db.VarChar` | Yes | Snapshot. |
| `exchange_rate` | `Decimal @db.Decimal(15, 5)` | Yes | Default exchange rate; default `1`. |
| `exchange_rate_date` | `DateTime @db.Timestamptz(6)` | Yes | Effective date. |
| `requested_qty` | `Decimal @db.Decimal(20, 5)` | Yes | Default requested qty; default `0`. |
| `requested_unit_id` | `String @db.Uuid` | Yes | Requested UoM. |
| `requested_unit_name` | `String @db.VarChar` | Yes | Snapshot. |
| `requested_unit_conversion_factor` | `Decimal @db.Decimal(20, 5)` | Yes | Conversion factor. |
| `requested_base_qty` | `Decimal @db.Decimal(20, 5)` | Yes | Default base qty. |
| `foc_qty` | `Decimal @db.Decimal(20, 5)` | Yes | Default FOC qty. |
| `foc_unit_id` | `String @db.Uuid` | Yes | FOC UoM. |
| `foc_unit_name` | `String @db.VarChar` | Yes | Snapshot. |
| `foc_unit_conversion_factor` | `Decimal @db.Decimal(20, 5)` | Yes | Conversion factor. |
| `foc_base_qty` | `Decimal @db.Decimal(20, 5)` | Yes | Default base FOC qty. |
| `tax_profile_id` | `String @db.Uuid` | Yes | FK to `tb_tax_profile.id`. |
| `tax_profile_name` | `String @db.VarChar` | Yes | Snapshot. |
| `tax_rate` | `Decimal @db.Decimal(15, 5)` | Yes | Default tax rate. |
| `tax_amount` | `Decimal @db.Decimal(20, 5)` | Yes | Default tax amount. |
| `base_tax_amount` | `Decimal @db.Decimal(20, 5)` | Yes | Default base tax amount. |
| `is_tax_adjustment` | `Boolean` | Yes | Default tax-adjustment flag. |
| `discount_rate` | `Decimal @db.Decimal(15, 5)` | Yes | Default discount rate. |
| `discount_amount` | `Decimal @db.Decimal(20, 5)` | Yes | Default discount amount. |
| `base_discount_amount` | `Decimal @db.Decimal(20, 5)` | Yes | Default base discount amount. |
| `is_discount_adjustment` | `Boolean` | Yes | Default discount-adjustment flag. |
| `is_active` | `Boolean` | Yes | Whether this template line is enabled; default `true`. |
| `info` | `Json @db.JsonB` | Yes | Extension bag; default `{}`. |
| `dimension` | `Json @db.JsonB` | Yes | Default per-line dimensions; default `[]`. |
| `doc_version` | `Int @db.Integer` | No | Optimistic-concurrency version; default `0`. |
| `created_at` | `DateTime @db.Timestamptz(6)` | Yes | Creation timestamp. |
| `created_by_id` | `String @db.Uuid` | Yes | Creator id. |
| `updated_at` | `DateTime @db.Timestamptz(6)` | Yes | Last-update timestamp. |
| `updated_by_id` | `String @db.Uuid` | Yes | Updater id. |
| `deleted_at` | `DateTime @db.Timestamptz(6)` | Yes | Soft-delete timestamp. |
| `deleted_by_id` | `String @db.Uuid` | Yes | Soft-delete actor id. |

**Constraints:** `@id` on `id`. FKs: `purchase_request_template_id → tb_purchase_request_template.id`; `product_id → tb_product.id` (required); `currency_id → tb_currency.id`; `tax_profile_id → tb_tax_profile.id`; `location_id → tb_location.id`; two named `@relation` FKs into `tb_unit` for requested and FOC unit.
**Indexes:** `@@unique([purchase_request_template_id, product_id, location_id, dimension, deleted_at])` as `PRT1_purchase_request_template_product_location_dimension_u`; `@@index([purchase_request_template_id, product_id, location_id])` as `PRT2_purchase_request_template_product_location_idx`; `@@index([purchase_request_template_id])` as `PRT2_purchase_request_template_idx`.

## 3. Relationships

```
tb_workflow
    │  1
    │
    │ * workflow_id
    ▼
tb_purchase_request ──1──*──► tb_purchase_request_comment
    │  1
    │
    │ * purchase_request_id
    ▼
tb_purchase_request_detail ──1──*──► tb_purchase_request_detail_comment
    │
    │ FK references (denormalised snapshots on the row)
    ├──► tb_product           (required, product_id)
    ├──► tb_vendor             (vendor_id)
    ├──► tb_pricelist_detail   (pricelist_detail_id)
    ├──► tb_tax_profile        (tax_profile_id)
    ├──► tb_currency           (currency_id)
    ├──► tb_location           (location_id)
    ├──► tb_delivery_point     (delivery_point_id)
    └──► tb_unit  ×3           (requested_unit_id, approved_unit_id, foc_unit_id — named relations)

tb_purchase_request_detail ──*──*──► tb_purchase_order_detail
    via bridge tb_purchase_order_detail_tb_purchase_request_detail
    (po_detail_id, pr_detail_id) — many PR lines can fan into one PO line
    (consolidation); one PR line can fan into many PO lines (partial conversion).

tb_workflow
    │
    │ * workflow_id
    ▼
tb_purchase_request_template
    │
    │ * purchase_request_template_id
    ▼
tb_purchase_request_template_detail
    │
    ├──► tb_product           (required)
    ├──► tb_currency
    ├──► tb_tax_profile
    ├──► tb_location
    └──► tb_unit  ×2           (requested_unit_id, foc_unit_id)
```

Notes:

- **Header → detail** is 1-to-many. The detail's `purchase_request_id` is nullable, which permits orphan / scratch lines but is enforced 1-to-many in practice by the application layer.
- **Header → comment** and **detail → comment** are both 1-to-many. The comment table is the persistent record of workflow activity; the JSON columns on the header (`workflow_history`, `stages_status`) are the in-place cursor.
- **PR → PO** is many-to-many via `tb_purchase_order_detail_tb_purchase_request_detail` to support both PR consolidation (multiple PRs → one PO) and partial conversion (one PR → multiple POs).
- **Template → template_detail** mirrors header → detail but is one-to-many for seeding only; templates do not have their own approval chain.
- All `@relation` FK declarations use `onDelete: NoAction, onUpdate: NoAction`, so referential integrity is preserved by application-level soft-delete (`deleted_at`) rather than cascade.

## 4. Enums

- **`enum_purchase_request_doc_status`**: `draft` (`ร่าง` — initial editable state, no commitment), `in_progress` (`กำลังดำเนินการ` — submitted and traversing the approval chain), `voided` (`โมฆะ` / `ยกเลิก` — terminal terminated state; covers Requestor cancel on an unsubmitted draft, approver reject mid-chain, and Sysadmin void after submission — see [03-user-flow](./03-user-flow) § 2), `approved` (`อนุมัติ` — chain complete, ready for procurement conversion), `completed` (`เสร็จสิ้น` — fully converted to PO and closed). The previously-separate `cancelled` value was dropped in the May 2026 enum-cleanup pass; all termination paths now converge on `voided`.
- **`enum_purchase_order_type`**: `manual` (PO created directly by procurement without an upstream PR), `purchase_request` (PO sourced from one or more PRs via the conversion flow — also the default value on `tb_purchase_order.po_type`, which is why PR-sourced is the standard procure-to-pay path).
- **`enum_last_action`**: `submitted`, `approved`, `reviewed`, `rejected` — used by `tb_purchase_request.last_action` to capture the most recent workflow action.
- **`enum_comment_type`**: `user` (human-authored comment), `system` (auto-generated activity-log entry written by the workflow engine).
- **`enum_pricelist_compare_type`**: referenced by `tb_purchase_request_detail.pricelist_type` to describe how the price snapshot was selected (default `automatic` — see [vendor-pricelist](/en/inventory/vendor-pricelist) for the full enum values).
- **`enum_stage_role`**: `create`, `approve`, `purchase`, `issue`, `view_only` — used by the shared `tb_workflow` configuration to label what each stage allows; surfaces on the PR through the `workflow_*` columns.

## 5. Divergences from carmen/docs

The legacy `data-models.md` document describes TypeScript front-end interfaces (`PurchaseRequest`, `PurchaseRequestItem`, etc.), not Prisma entities. The interfaces have a different shape and naming convention from the persisted schema; the items below capture material differences that downstream documentation must reconcile.

| # | Item | carmen/docs says | Prisma has | Action |
|---|------|------------------|------------|--------|
| 1 | Document status values | `enum DocumentStatus { Draft, Submitted, InProgress, Completed, Rejected }` | `enum_purchase_request_doc_status { draft, in_progress, voided, approved, completed }` | Treat Prisma as canonical. `Submitted` in the UI maps to `in_progress`; `Rejected` is not a stored status (rejection terminates the chain and the PR is `voided`); `approved` exists in Prisma but not in the carmen/docs enum; `voided` has no carmen/docs counterpart. The `cancelled` value was present in earlier revisions of this wiki and earlier schema iterations but was dropped in the May 2026 enum-cleanup pass — all termination paths now converge on `voided`. Update `02-business-rules` and the front-end status enum accordingly. |
| 2 | PR type | TypeScript `enum PRType { GeneralPurchase, MarketList, AssetPurchase, ServiceRequest }` | No `pr_type` / `type` column on `tb_purchase_request`; the schema carries no enumerated PR type. PR-type behaviour is currently configured indirectly via workflow selection and `info`/`dimension` extension fields. | Either add a Prisma `pr_type` column + enum (preferred, requires migration), or document the workaround that PR type is encoded under `info.pr_type`. Decision pending; flag for backend architecture review. |
| 3 | Workflow stages | TypeScript `enum WorkflowStage { requester, departmentHeadApproval, purchaseCoordinatorReview, financeManagerApproval, generalManagerApproval, completed }` | No fixed stage enum. Stages are user-configurable rows in `tb_workflow` referenced through `tb_purchase_request.workflow_id`; the current stage slug is stored as `workflow_current_stage` (string), and the role-per-stage label uses `enum_stage_role` (`create / approve / purchase / issue / view_only`). | Document the configurable workflow as canonical; the carmen/docs enum represents only one default configuration. |
| 4 | Workflow status | TypeScript `enum WorkflowStatus { pending, approved, rejected }` distinct from document status | No separate workflow-status column. `tb_purchase_request.last_action` (`submitted / approved / reviewed / rejected`) covers the same intent. | Drop the front-end `WorkflowStatus` enum in favour of `last_action` + `workflow_current_stage`. |
| 5 | Line status | TypeScript `PurchaseRequestItemStatus = "Pending" \| "Accepted" \| "Rejected" \| "Review"` | `tb_purchase_request_detail` has no scalar status field; per-line state is stored in the `stages_status` JSON column and `current_stage_status` string. The schema now declares `enum_stage_action { submit, approve, reject, review, pending }` (May 2026 cleanup pass) intended to type `current_stage_status`, but the column itself remains `String?` until a planned migration validates historical values — see Section 2.2 field row and Section 4 for the enum body. | Migration to retype `current_stage_status` as `enum_stage_action` is pending. After migration, the front-end's `PurchaseRequestItemStatus` set will map directly: `Pending → pending`, `Accepted → approve`, `Rejected → reject`, `Review → review`. |
| 6 | Vendor on header | `PurchaseRequest.vendor: string; vendorId: number` (header-level vendor) | Vendor is a **line-level** denormalised reference (`tb_purchase_request_detail.vendor_id` / `vendor_name`). The header has no vendor column. | Front-end "header vendor" must be derived (e.g. show the first line's vendor or `Mixed`); update the interface. |
| 7 | `deliveryDate` on header | Present on `PurchaseRequest` | Header has no `delivery_date`. Each line carries its own `tb_purchase_request_detail.delivery_date`. | Same as above — derived field, not stored. |
| 8 | Reference number format | Documented as `PR-2301-0001` | `tb_purchase_request.pr_no` is `VarChar` with no format constraint at the DB level; format is enforced by the application. | Note that the format is application-policy, not schema-enforced. |

## 6. References

- **Primary (source of truth):** Prisma schemas listed in the header callout — concretely `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` (all PR models) and `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` (verified to contain no PR models).
- **Secondary (concept cross-check):** `../carmen/docs/purchase-request-management/data-models.md` — TypeScript front-end interfaces; divergences captured in Section 5.
- Related modules: [purchase-order](/en/inventory/purchase-order) (conversion target), [product](/en/inventory/product) (line product reference), [vendor-pricelist](/en/inventory/vendor-pricelist) (price + tax snapshot source), [inventory](/en/inventory/inventory) (on-hand context for the requestor).

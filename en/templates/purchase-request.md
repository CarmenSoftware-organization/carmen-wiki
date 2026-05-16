---
title: Purchase Request Template
description: Reusable PR scaffold — frequently-purchased line bundles saved as templates so a Requestor can instantiate a PR with one click.
published: true
date: 2026-05-16T17:00:00.000Z
tags: templates, purchase-request, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# Purchase Request Template

## 1. Purpose

A **Purchase Request Template** is a reusable scaffold that captures the line bundle a Requestor would otherwise re-enter on every recurring PR: standard product list, default locations, default requested quantities, currency, tax / discount snapshots, and the workflow under which the eventual PR will route. When the Requestor picks **Create PR from Template**, the template header (currency, workflow, type) and detail rows are deep-cloned into a brand-new `tb_purchase_request` at `pr_status = draft`. The template itself is untouched; the new PR is independent and can be edited freely before submission.

Templates sit alongside [[templates/price-list]] under the [[templates]] umbrella — both are seed-only documents that never enter a workflow themselves and never post to any ledger. The PR template's value is operational: it removes data-entry friction for procurement teams that issue the same 30-line PR every Monday (kitchen daily orders, weekly housekeeping consumables, monthly amenity restock).

## 2. Prisma Model(s)

Source: tenant schema.

### 2.1 `tb_purchase_request_template`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `name` | `String @db.VarChar` | No | Template name (unique with workflow). |
| `description` | `String? @db.VarChar` | Yes | Free text. |
| `workflow_id` | `String? @db.Uuid` | Yes | FK to `tb_workflow`. The workflow assigned to PRs cloned from this template. |
| `workflow_name` | `String? @db.VarChar` | Yes | Denormalised snapshot of the workflow name. |
| `is_active` | `Boolean? @default(true)` | Yes | Lifecycle flag. `true` = selectable in the "Create from Template" picker; `false` = retired. |
| `note`, `info`, `dimension` | mixed | Yes | Standard metadata. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** `@@unique([name, workflow_id, deleted_at])` map `PRT1_name_workflow_id_u` — the same name may exist under different workflows; `@@index([workflow_id])`; `@@index([name])`. FK to `tb_workflow` `onDelete: NoAction`.

Note: there is no `status` enum on the template — lifecycle is the boolean `is_active` plus `deleted_at`. See Section 3 for how the three logical states (draft / active / inactive) map to these columns.

### 2.2 `tb_purchase_request_template_detail`

One row per template line.

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id`, `purchase_request_template_id` | mixed | No / Yes | PK + parent FK. |
| `location_id`, `location_code`, `location_name`, `delivery_point_id`, `delivery_point_name` | mixed | Yes | Default destination snapshot. |
| `product_id`, `product_code`, `product_name`, `product_local_name`, `product_sku` | mixed | No / Yes | Product snapshot. |
| `inventory_unit_id`, `inventory_unit_name` | mixed | Yes | Inventory unit snapshot. |
| `description`, `comment` | `String? @db.VarChar` | Yes | Free text. |
| `currency_id`, `currency_code`, `exchange_rate`, `exchange_rate_date` | mixed | Yes | Currency snapshot — resolved at clone time, not on template edit. |
| `requested_qty`, `requested_unit_id`, `requested_unit_name`, `requested_unit_conversion_factor`, `requested_base_qty` | `Decimal(20,5)` / mixed | Yes | Default requested quantity in user-entered unit + converted base-unit value. |
| `foc_qty`, `foc_unit_id`, `foc_unit_name`, `foc_unit_conversion_factor`, `foc_base_qty` | `Decimal(20,5)` / mixed | Yes | Default free-of-charge quantity. |
| `tax_profile_id`, `tax_profile_name`, `tax_rate`, `tax_amount`, `base_tax_amount`, `is_tax_adjustment` | mixed | Yes | Tax snapshot. |
| `discount_rate`, `discount_amount`, `base_discount_amount`, `is_discount_adjustment` | mixed | Yes | Discount snapshot. |
| `is_active` | `Boolean? @default(true)` | Yes | Per-line active flag — inactive lines are skipped at clone time. |
| `info`, `dimension`, `doc_version` | mixed | Yes | Standard metadata. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** `@@unique([purchase_request_template_id, product_id, location_id, dimension, deleted_at])` map `PRT1_purchase_request_template_product_location_dimension_u` — one line per (template, product, location, dimension); `@@index([purchase_request_template_id, product_id, location_id])`; `@@index([purchase_request_template_id])`. FKs to `tb_currency`, `tb_unit` (twice — requested_unit and foc_unit), `tb_location`, `tb_product`, `tb_purchase_request_template`, `tb_tax_profile` — all `onDelete: NoAction`.

Note that the comment block (vendor_id, approved_*, foc_*) commented out in the schema indicates the template intentionally **omits** vendor allocation and approved quantities — those resolve at PR creation time, not template-design time.

### 2.3 `tb_purchase_request_template_comment`

Comments on the template itself, following the canonical comment shape.

## 3. Workflow / Lifecycle

The template **does not** participate in the workflow engine — it has no `workflow_current_stage`, no `user_action`, no `doc_status`. Its three logical states are derived from `is_active` and `deleted_at`:

- **`draft`** (`is_active = false`, `deleted_at IS NULL`, no usage yet) — editable, not surfaced in the "Create from Template" picker. Allows the configurer to assemble the line bundle privately before publishing.
- **`active`** (`is_active = true`, `deleted_at IS NULL`) — surfaced in the picker; can still be edited, but edits do **not** propagate to PRs already cloned from it.
- **`inactive`** (`is_active = false`, `deleted_at IS NULL`, has been used at least once) — retired from the picker; remains readable on historical PRs that record `created_from_template_id`.

`deleted_at` is the soft-delete sentinel — used only when the template was never instantiated and is being purged.

## 4. Usage / Cross-References

- [[purchase-request]] — sole consumer. **Create PR from Template** clones header + detail into a new `tb_purchase_request` + `tb_purchase_request_detail` set at `pr_status = draft`.
- [[purchase-request/03-user-flow-requestor]] — REQ-HP-06 happy-path scenario uses this template flow.
- [[system-config/workflow]] — the workflow assigned on `workflow_id` is the workflow the cloned PR enters at submit.
- [[master-data/product]], [[master-data/location]], [[master-data/currency]], [[master-data/tax-profile]] — every line snapshots from these masters at template-edit time; the *clone* re-resolves currency-and-rate but leaves product/location/tax references as-is.

## 5. Business Rules

- **Seed-only persistence.** Template rows are never referenced as foreign keys by transactional documents — the PR records a copy, not a reference. Editing a template after a PR has been cloned does **not** retroactively change that PR.
- **Deep-copy clone semantics.** "Create from Template" inserts a new `tb_purchase_request` (with a fresh `pr_no`, `pr_status = draft`, current timestamps, current user as creator) and, for every `is_active = true` detail row, inserts a corresponding `tb_purchase_request_detail`. Quantities, units, tax snapshots, discount snapshots, and dimensions are copied verbatim. Inactive lines are skipped.
- **Currency / FX resolution at clone.** Currency code is copied verbatim; `exchange_rate` and `exchange_rate_date` are **re-resolved** at clone time against [[master-data/exchange-rate]] using the new PR's `pr_date`. This prevents stale FX on cloned PRs.
- **Workflow snapshot.** `workflow_id` copies onto the new PR; the workflow engine then routes the PR identically to a hand-authored one.
- **Validation on save.** Template name must be unique within its `workflow_id` (the unique constraint enforces this at the DB layer). At least one detail row with `is_active = true` is required to enable the picker entry.
- **Authorization.** Templates are typically maintained by **Procurement Manager** or **Product Admin**. Requestors can use templates but cannot edit them (enforced by role).
- **No workflow on template itself.** The template has no approval gate — edits go live immediately when saved. This is intentional: templates are a configuration concern, not a transactional one.
- **Hard-delete guard.** Once at least one PR has been cloned from a template, hard-delete is blocked; flip `is_active = false` instead.
- **Per-line `is_active`.** A line can be temporarily disabled without removing it from the template — useful for seasonal SKUs.
- **Dimension awareness.** `dimension` JSON participates in the per-line unique key, so a single product can appear twice in a template under different dimension values (e.g. different cost centers).

## 6. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_purchase_request_template` (lines 2402-2430), `tb_purchase_request_template_detail` (lines 2466-2562), `tb_purchase_request_template_comment` (lines 2432-2464).
- **Frontend route:** `../carmen-inventory-frontend/app/(root)/procurement/purchase-request-template/`.
- **Carmen docs:** `../carmen/docs/purchase-request-management/purchase-request-template-ba.md`; `../carmen/docs/purchase-request-management/PR-User-Experience.md` (template-based creation flow).
- **Cross-module:** see Section 4.

---
title: Unit
description: Units of measure and inter-unit conversions used by every transactional document and product record.
published: true
date: 2026-05-17T07:28:28.000Z
tags: master-data, unit, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# Unit

> **At a Glance**
> **Owner:** Product Admin &nbsp;·&nbsp; **Tables:** `tb_unit`, `tb_unit_conversion` &nbsp;·&nbsp; **Used by:** product, recipe, PR / PO / GRN / SR / inventory / costing &nbsp;·&nbsp; Inventory + order units and the multipliers between them.

![Unit screen](/screenshots/master-data/unit.png)

## 1. What & Who

**Units** catalogue every unit of measure used for quantities, prices, and balances — both **inventory/ingredient** units (kg, L, each) and **order/purchase** units (case-of-12, sack-25kg). Every priced or counted line in Carmen carries one or more unit references, so this is the smallest piece of master data that touches every transactional module.

The companion table `tb_unit_conversion` stores **multipliers between two units**, optionally scoped per product. Conversions power purchase-to-inventory translation in GRN, recipe yield calc, and pricelist comparison across vendors quoting different pack sizes. **Without correct conversions, every downstream costing and balance number is wrong.** Maintained by Product Admin; read by every transactional path.

## 2. Common Tasks

| Task | Where | Notes |
|---|---|---|
| Add a unit | Configuration → Master Data → Unit → **New** | Required: `name`; `decimal_place` defaults `2` |
| Deactivate | Toggle `is_active` | Hidden from new transactions; historical lines unchanged |
| Add a global conversion | Conversion matrix | `product_id = NULL`; pick `unit_type`, from-unit/qty, to-unit/qty |
| Add a per-product conversion | Product detail → Conversions | Overrides global for that product |
| Mark default conversion | Toggle `is_default` | Primary when multiple conversions exist for the same pair |
| Identity conversion | Same from/to with equal qty | Permitted; otherwise from ≠ to required |

## 3. Validation & Errors

| Symptom / Message | Cause | Action |
|---|---|---|
| "Duplicate unit name" | Same `name` already active (case-insensitive) | Reactivate the existing row or pick a different name |
| "Conversion qty must be > 0" | Either `from_unit_qty` or `to_unit_qty` is zero/negative | Enter positive values |
| "Same-unit conversion needs equal qty" | `from_unit_id == to_unit_id` but qty differs | Use the identity (`1 = 1`) or pick a different pair |
| "Conversion already exists for this product/pair" | Unique constraint violated | Edit the existing row |
| "Cannot delete — unit in use" | Active products, recipes, or postings reference the unit | Inactivate instead |

## 4. Edge Cases

- **Uniqueness on `name` is app-enforced** (no DB unique constraint) — case-insensitive duplicates can slip through if app validation is bypassed.
- **`decimal_place` is rendering only** — storage is `Decimal(20, 5)`.
- **Per-product conversion overrides global** — resolution picks the product-scoped row first.
- **Identity conversions are allowed** but only with equal `qty` on both sides.
- **Inactive units** stay readable on historical documents; cannot be selected in new transactions.
- **`enum_unit_type`** discriminates `order_unit` vs. `ingredient_unit` — different resolution paths in GRN vs. recipe.

---

## 5. Data Model (Dev)

Source: tenant schema (`packages/prisma-shared-schema-tenant/prisma/schema.prisma`).

### 5.1 `tb_unit`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key (`gen_random_uuid()`). |
| `name` | `String @db.VarChar` | No | Display name, e.g. `kg`, `each`, `case`. |
| `description` | `String? @db.VarChar` | Yes | Free-text description. |
| `is_active` | `Boolean?` | Yes | Active flag, defaults `true`. |
| `decimal_place` | `Int` | No | Render precision (default `2`). |
| `note` | `String? @db.VarChar` | Yes | Internal note. |
| `info` | `Json?` | Yes | Metadata (`{}` default). |
| `dimension` | `Json?` | Yes | Dimension tag array. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** primary key on `id`. Soft-delete via `deleted_at`. No explicit unique on `name` — app-layer enforcement against active rows.

### 5.2 `tb_unit_conversion`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `product_id` | `String? @db.Uuid` | Yes | Optional product scope; `NULL` = global. |
| `unit_type` | `enum_unit_type` | No | `order_unit` or `ingredient_unit`. |
| `from_unit_id` / `from_unit_name` / `from_unit_qty` | — | Mixed | Source side. `qty` default `0`, `Decimal(20,5)`. |
| `to_unit_id` / `to_unit_name` / `to_unit_qty` | — | Mixed | Target side. |
| `decimal_place` | `Int` | No | Render precision for converted qty. |
| `is_default` | `Boolean?` | Yes | Primary when multiple conversions exist for the same pair. |
| `description` | `Json?` | Yes | Localised description. |
| `is_active`, `note`, `info`, `dimension` | — | Mixed | Standard activation/metadata. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** `@@unique([product_id, unit_type, from_unit_id, to_unit_id, deleted_at])` named `unitconversion_product_unit_type_from_unit_to_unit_deletedat_u`. Index on the same prefix. Both FKs to `tb_unit` `onDelete: NoAction`.

`enum_unit_type` values: `order_unit`, `ingredient_unit`.

## 6. Business Rules

- **Uniqueness.** App enforces no duplicate active unit `name` (case-insensitive). Conversions unique per `(product_id, unit_type, from_unit_id, to_unit_id)` among non-deleted rows.
- **Deletion guards.** Active product/recipe/posting references block hard-delete — inactivate.
- **Validation.** Conversion `from_unit_qty` and `to_unit_qty` both `> 0`. Same-unit pairs only with equal qty.
- **Lifecycle.** Inactive units visible on historical documents; locked from new transactions.
- **Decimal precision.** `decimal_place` is rendering only; storage `Decimal(20,5)`.

## 7. Cross-References

- [[product]] — every product has order/ingredient/inventory unit refs and a per-product conversion set.
- [[recipe]] — recipe lines use ingredient units; yields convert to inventory unit.
- [[purchase-request]] — requested / approved / FOC qtys carry a unit FK.
- [[purchase-order]] — order_unit and base_unit per detail line.
- [[good-receive-note]] — ordered / received / FOC unit columns; conversion applied to post inventory qty.
- [[store-requisition]] — requisition lines carry unit references.
- [[inventory]] — balances kept in inventory unit; conversions translate from receipt.
- [[inventory-adjustment]] — adjustment qtys in inventory unit.
- [[costing]] — costing engine consumes inventory-unit balances.

## 8. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_unit` (lines ~3132-3208), `tb_unit_conversion` (lines ~3210-3246), `enum_unit_type` (lines ~254-257).
- **Frontend:** `../carmen-turborepo-frontend/apps/web/app/(app)/configuration/unit/`.

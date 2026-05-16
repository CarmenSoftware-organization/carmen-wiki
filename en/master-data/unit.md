---
title: Unit
description: Units of measure and inter-unit conversions used by every transactional document and product record.
published: true
date: 2026-05-16T08:00:00.000Z
tags: master-data, unit, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# Unit

## 1. Purpose

Units catalogue every unit of measure that quantities, prices, and balances are expressed in — both *inventory/ingredient* units (e.g. kg, L, each) and *order/purchase* units (e.g. case-of-12, sack-25kg). Every priced or counted line in Carmen carries one or more unit references, so the catalogue is the smallest piece of master data that touches every transactional module.

The companion table `tb_unit_conversion` stores the multipliers that translate quantities between two units, optionally scoped per product. Conversions power purchase-to-inventory unit translation in GRN, recipe yield calculations, and pricelist comparison across vendors who quote in different pack sizes. Without correct conversions, every downstream costing and balance number is wrong.

## 2. Prisma Model(s)

Source: tenant schema (`packages/prisma-shared-schema-tenant/prisma/schema.prisma`).

### 2.1 `tb_unit`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key (`gen_random_uuid()`). |
| `name` | `String @db.VarChar` | No | Display name, e.g. `kg`, `each`, `case`. |
| `description` | `String? @db.VarChar` | Yes | Free-text description. |
| `is_active` | `Boolean?` | Yes | Active flag, defaults to `true`. |
| `decimal_place` | `Int` | No | Number of decimal places used when rendering quantities in this unit (default `2`). |
| `note` | `String? @db.VarChar` | Yes | Internal note. |
| `info` | `Json?` | Yes | Free-form metadata (`{}` default). |
| `dimension` | `Json?` | Yes | Dimension tag array. |
| `created_at` / `created_by_id` | — | Yes | Audit columns. |
| `updated_at` / `updated_by_id` | — | Yes | Audit columns. |
| `deleted_at` / `deleted_by_id` | — | Yes | Soft-delete columns. |

**Constraints:** primary key on `id`. Soft-delete via `deleted_at`. No explicit unique on `name` at schema level — uniqueness is enforced by application logic against active rows.

### 2.2 `tb_unit_conversion`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `product_id` | `String? @db.Uuid` | Yes | Optional product scope; `NULL` means the conversion is global. |
| `unit_type` | `enum_unit_type` | No | `order_unit` or `ingredient_unit`. |
| `from_unit_id` / `from_unit_name` / `from_unit_qty` | — | Mixed | Source side of the conversion. `qty` defaults to `0`, `db.Decimal(20,5)`. |
| `to_unit_id` / `to_unit_name` / `to_unit_qty` | — | Mixed | Target side of the conversion. |
| `decimal_place` | `Int` | No | Rendering precision for converted quantities. |
| `is_default` | `Boolean?` | Yes | Marks the primary conversion when multiple exist for the same pair. |
| `description` | `Json?` | Yes | Localised description. |
| `is_active`, `note`, `info`, `dimension` | — | Mixed | Standard activation/metadata. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** `@@unique([product_id, unit_type, from_unit_id, to_unit_id, deleted_at])` named `unitconversion_product_unit_type_from_unit_to_unit_deletedat_u`. Index on the same prefix. Both FKs to `tb_unit` with `onDelete: NoAction`.

`enum_unit_type` values: `order_unit`, `ingredient_unit`.

## 3. Usage / Cross-References

- [[product]] — every product has order, ingredient, and inventory unit references and a per-product conversion set.
- [[recipe]] — recipe lines reference ingredient units and rely on conversions to convert recipe yield to inventory unit.
- [[purchase-request]] — requested, approved, and FOC quantities each carry a unit FK.
- [[purchase-order]] — order_unit and base_unit per detail line.
- [[good-receive-note]] — ordered, received, and FOC unit columns; conversion is applied to post the inventory unit quantity.
- [[store-requisition]] — requisition lines carry unit references.
- [[inventory]] — stock balances are kept in inventory unit; conversions translate from receipt to balance.
- [[inventory-adjustment]] — adjustment quantities use inventory unit.
- [[costing]] — costing engine consumes inventory-unit balances.

## 4. Configuration UI

Managed by **Product Admin** under the Master Data area of the configuration UI. Two screens: a flat unit listing (CRUD on `tb_unit`) and a conversion matrix (CRUD on `tb_unit_conversion`, scoped either globally or per product from the product detail screen).

## 5. Business Rules

- **Uniqueness.** Application logic must prevent two active units with the same `name` (case-insensitive). Conversions are unique per `(product_id, unit_type, from_unit_id, to_unit_id)` among non-deleted rows.
- **Deletion guards.** A unit referenced by any active product, recipe, or transactional line cannot be hard-deleted. Use `is_active = false` to retire a unit; soft-delete via `deleted_at` only when no active references remain.
- **Validation.** Conversion `from_unit_qty` and `to_unit_qty` must both be `> 0`. A conversion cannot have `from_unit_id == to_unit_id` unless `from_unit_qty == to_unit_qty` (identity).
- **Lifecycle.** Inactive units stay visible on historical documents but cannot be selected in new transactions.
- **Decimal precision.** `decimal_place` controls UI rendering only; the underlying storage uses `Decimal(20,5)`.

## 6. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_unit` (lines ~3132-3208), `tb_unit_conversion` (lines ~3210-3246), `enum_unit_type` (lines ~254-257).
- **Frontend route (if known):** `../carmen-turborepo-frontend/apps/web/app/(app)/configuration/unit/`.
- **carmen/docs:** not documented separately.
- **Cross-module:** see Section 3.

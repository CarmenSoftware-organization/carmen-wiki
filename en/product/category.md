---
title: Product Category
description: Three-level product taxonomy (category > sub-category > item group) that drives catalogue navigation, attribute inheritance, deviation tolerances, and category-scoped permission filters.
published: true
date: 2026-05-16T17:00:00.000Z
tags: product, category, taxonomy, master-data, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# Product Category

## 1. Purpose

Product Category is the classification layer over the product master. Every product carries a category assignment that drives:

1. **Catalogue navigation** in PR / PO / SR / recipe line entry — users drill `Food > Beverage > Coffee Beans` rather than scrolling thousands of items.
2. **Attribute inheritance** — tax profile, deviation tolerances, "used in recipe", and "sold directly" flags default from the category and can be overridden at the product level.
3. **Cost / loss reporting roll-ups** — food cost, wastage, and variance reports group by category at every level of the tree.
4. **Permission scoping** — Purchaser and Store Keeper roles can be restricted to specific category branches via the access-control layer.

Maintained by the **Product Admin** persona. Categories are referenced by `category_id` on every `tb_product` row.

## 2. Prisma Model(s)

Source: tenant schema. The taxonomy is **three fixed levels**, not a single self-referential tree — each level has its own table with a FK pointing up to the parent level.

### 2.1 `tb_product_category` (level 1)

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `code` | `String @db.VarChar` | No | Short code (e.g. `FOOD`, `BEV`, `SUPP`). |
| `name` | `String @db.VarChar` | No | Display name. |
| `description` | `String? @db.VarChar` | Yes | Free text. |
| `is_active` | `Boolean?` | Yes | Default `true`. |
| `price_deviation_limit` | `Decimal(20,5)?` | Yes | Max % PO unit price may diverge from master/last-receiving for products in category before approval (default `0`). |
| `qty_deviation_limit` | `Decimal(20,5)?` | Yes | Max % GRN qty may diverge from PO qty (default `0`). |
| `is_used_in_recipe` | `Boolean?` | Yes | Default flag inherited by child products (default `true`). |
| `is_sold_directly` | `Boolean?` | Yes | Default flag (default `false`). |
| `tax_profile_id` / `tax_rate` | mixed | Yes | Default tax setup inherited by products. |
| `note`, `info`, `dimension` | — | Yes | Standard metadata. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** `@@unique([code, deleted_at])`, `@@unique([code, name, deleted_at])`. Reverse relations to `tb_product_sub_category`, `tb_product_category_comment`, `tb_tax_profile`.

### 2.2 `tb_product_sub_category` (level 2)

| Field | Prisma Type | Description |
| --- | --- | --- |
| `id` | `String @db.Uuid` | Primary key. |
| `product_category_id` | `String @db.Uuid` | **FK to `tb_product_category`** — the parent in the hierarchy. |
| `code`, `name`, `description` | `String` | Identification. |
| `price_deviation_limit` / `qty_deviation_limit` | `Decimal(20,5)?` | Override of parent category's tolerance. |
| `is_used_in_recipe` / `is_sold_directly` / `is_active` | `Boolean?` | Flag overrides. |
| `tax_profile_id` / `tax_rate` | mixed | Tax override. |
| Audit columns | — | Standard. |

**Constraints:** `@@unique([code, name, deleted_at])`. Reverse relation to `tb_product_item_group`.

### 2.3 `tb_product_item_group` (level 3 — leaf)

| Field | Prisma Type | Description |
| --- | --- | --- |
| `id` | `String @db.Uuid` | Primary key. |
| `product_subcategory_id` | `String @db.Uuid` | **FK to `tb_product_sub_category`** — the parent. |
| `code`, `name`, `description` | `String` | Identification. |
| `price_deviation_limit` / `qty_deviation_limit` / `is_*` / `tax_*` | mixed | Same shape as parents; finest-grained override. |
| Audit columns | — | Standard. |

Each level also has its own `*_comment` table for discussion and attachments.

> **Hierarchy depth.** The schema fixes the tree at exactly three levels. The carmen/docs Product Overview describes "up to five levels deep" as a product-management ambition; the Prisma schema currently enforces three. (Inferred — schema is source of truth here.)

## 3. Workflow / Lifecycle

```
1. Product Admin creates a category (code + name unique)
2. Sub-categories added under it, item groups under each sub-category
3. Defaults (tax profile, deviation tolerances, is_used_in_recipe, is_sold_directly)
   cascade downward at INSERT time, can be overridden at any level
4. Each tb_product references one (category, sub_category, item_group) triple
5. Deactivation (is_active = false) hides from new-product pickers but keeps
   the row readable on historical products; soft-delete is blocked while any
   tb_product still references the row (application-enforced; FK is NoAction)
```

Attribute inheritance is computed at product save: effective value = `item_group ?? sub_category ?? category ?? app default`.

## 4. Usage / Cross-References

- [[product]] — every product carries a `(category, sub_category, item_group)` triple
- [[product/03-user-flow-product-admin]] — Product Admin maintains the tree
- [[purchase-request]] — PR line entry drills the category tree to find products; deviation tolerances govern PR / PO / GRN price and qty checks
- [[purchase-order]] — uses category-level `price_deviation_limit`
- [[good-receive-note]] — uses category-level `qty_deviation_limit`
- [[recipe]] — `is_used_in_recipe` filter excludes non-ingredient categories from recipe builders
- [[access-control/permission]] — category-scoped permission filters for Purchaser / Store Keeper
- [[master-data/tax-profile]] — default `tax_profile_id` cascades from category to product

## 5. Business Rules

- **Code uniqueness.** `tb_product_category.code` unique among non-deleted rows. Sub-category and item-group codes are unique within their parent (application-enforced via the `(code, name, deleted_at)` composite key).
- **Hierarchy integrity.** A sub-category cannot be re-parented to a different category once products reference its item groups — FK on `product_subcategory_id` is `NoAction`. Move via re-key requires manual data migration.
- **Deletion guards.** A category, sub-category, or item-group with any active referencing product is blocked from soft-delete (application-enforced).
- **Tax profile.** Changing `tax_profile_id` on a category affects only new products; existing products keep their snapshotted tax setup unless re-saved.
- **Deviation tolerances.** `price_deviation_limit` and `qty_deviation_limit` are percentages (0-100). A `0` value means "no tolerance configured" and falls back to the application default rather than blocking 0% deviation.
- **Recipe / sold-directly flags.** Used by downstream pickers — `is_used_in_recipe = false` excludes from recipe builders; `is_sold_directly = true` enables direct POS sale.

## 6. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_product_category` (lines ~1566-1602), `tb_product_sub_category` (lines ~1711-1748), `tb_product_item_group` (lines ~1638-1675), `tb_product_category_comment` (lines ~1604-1636).
- **Frontend route:** `../carmen-inventory-frontend/app/(root)/product-management/category/`.
- **carmen/docs:** `../carmen/docs/product-management/PROD-API-Endpoints-Categories.md`; `../carmen/docs/product-management/PROD-Overview.md`.
- **Module landing:** [[product]] § 3 (Product Category key concept).
- **Cross-module:** see Section 4.

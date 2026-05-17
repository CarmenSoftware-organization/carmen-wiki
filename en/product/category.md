---
title: Product Category
description: Three-level product taxonomy (category > sub-category > item group) that drives catalogue navigation, attribute inheritance, deviation tolerances, and category-scoped permission filters.
published: true
date: 2026-05-17T07:00:16.000Z
tags: product, category, taxonomy, master-data, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# Product Category

> **At a Glance**
> **Owner:** Product Admin &nbsp;·&nbsp; **Tables:** `tb_product_category` → `tb_product_sub_category` → `tb_product_item_group` (**3 FIXED levels**, NOT self-referential) &nbsp;·&nbsp; **Trigger:** taxonomy maintenance &nbsp;·&nbsp; **Used by:** PR / PO / GRN / recipe / reports / permission scoping &nbsp;·&nbsp; **1-liner:** classification layer driving navigation, inherited defaults, and tolerances.

![Product Category screen](/screenshots/product/category.png)

## 1. What & Who

Product Category is the classification layer over the product master. Every product carries a `(category, sub_category, item_group)` triple that drives:

1. **Catalogue navigation** — users drill `Food > Beverage > Coffee Beans` rather than scrolling
2. **Attribute inheritance** — tax profile, deviation tolerances, `is_used_in_recipe`, `is_sold_directly` default down the tree
3. **Cost / loss reporting roll-ups** — food cost, wastage, variance group by category at every level
4. **Permission scoping** — Purchaser and Store Keeper can be restricted to category branches

Maintained by the **Product Admin** persona. Referenced by `category_id` on every `tb_product` row.

## 2. Common Tasks

| Task | Where | Notes |
|---|---|---|
| Add a top-level category | Product Management → Category → **New** | `code` must be unique among non-deleted rows |
| Add a sub-category | Open category → **Add sub-category** | FK `product_category_id` set to parent |
| Add an item group (leaf) | Open sub-category → **Add item group** | FK `product_subcategory_id` set to parent |
| Set price deviation tolerance | Edit any level → `price_deviation_limit` | % cap on PO unit price vs master/last-receiving; finest level wins |
| Set qty deviation tolerance | Edit any level → `qty_deviation_limit` | % cap on GRN qty vs PO qty; finest level wins |
| Override tax profile | Edit any level → `tax_profile_id` / `tax_rate` | Affects NEW products only — existing products keep snapshotted setup |
| Toggle `is_used_in_recipe` / `is_sold_directly` | Flag fields on any level | Used by recipe builder and POS pickers |
| Inactivate a leaf | Edit item group → `is_active = false` | Hides from new-product pickers; historical products still render |
| Soft-delete a level | **Delete** action | Blocked while any active `tb_product` still references the row (application-enforced) |

## 3. Validation & Errors

| Symptom / Message | Cause | Action |
|---|---|---|
| "Code already exists" on category | `tb_product_category.code` unique among non-deleted rows | Pick a different code, or restore the soft-deleted row |
| "Cannot delete — products still reference this" | Active `tb_product` rows point here | Reassign products first, then retry |
| "Cannot re-parent sub-category" | FK on `product_subcategory_id` is `NoAction`; products reference its item groups | Manual data migration required — not a UI action |
| Tax change not reflected on existing products | Tax profile snapshot at product save | Re-save the product to pick up the new default |
| `price_deviation_limit = 0` doesn't block 0% deviation | `0` means "no tolerance configured" — falls back to app default | Set a positive `%` to enforce a real cap |
| Hierarchy ambition vs schema | carmen/docs describes "up to 5 levels"; schema enforces 3 | Schema is source of truth — 3 fixed levels (Inferred) |

## 4. Edge Cases

- **3 FIXED levels, NOT self-referential.** Each level has its own table with FK pointing to the parent — there is **no recursive `parent_id` column**. Tooling that assumes a self-referential tree will not work.
- **Inheritance is `item_group ?? sub_category ?? category ?? app default`** — finest level wins, computed at product save.
- **Re-parenting blocked.** Once products reference an item group, the sub-category cannot be moved to a different category — FK `NoAction`.
- **Tax profile snapshot.** Changing `tax_profile_id` on a category affects only NEW products; existing products keep their snapshotted setup until re-saved.
- **Code scoping.** Sub-category and item-group codes are unique within their parent (composite `(code, name, deleted_at)`), not globally.
- **`0` deviation tolerance.** Means "not configured" — falls back to application default rather than blocking 0% deviation.

---

## 5. Data Model (Dev)

Source: tenant schema. **The taxonomy is THREE FIXED LEVELS** — each level a separate table with FK to parent. NOT a single self-referential tree.

### 5.1 `tb_product_category` (level 1)

| Field | Prisma Type | Nullable | Description |
|---|---|---|---|
| `id` | `String @db.Uuid` | No | Primary key. |
| `code` | `String @db.VarChar` | No | Short code (e.g. `FOOD`, `BEV`, `SUPP`). |
| `name` | `String @db.VarChar` | No | Display name. |
| `description` | `String? @db.VarChar` | Yes | Free text. |
| `is_active` | `Boolean?` | Yes | Default `true`. |
| `price_deviation_limit` | `Decimal(20,5)?` | Yes | Max % PO unit-price divergence (default `0`). |
| `qty_deviation_limit` | `Decimal(20,5)?` | Yes | Max % GRN qty divergence from PO (default `0`). |
| `is_used_in_recipe` | `Boolean?` | Yes | Inherited default (default `true`). |
| `is_sold_directly` | `Boolean?` | Yes | Inherited default (default `false`). |
| `tax_profile_id` / `tax_rate` | mixed | Yes | Default tax setup. |
| `note`, `info`, `dimension` | — | Yes | Standard metadata. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** `@@unique([code, deleted_at])`, `@@unique([code, name, deleted_at])`. Reverse relations to `tb_product_sub_category`, `tb_product_category_comment`, `tb_tax_profile`.

### 5.2 `tb_product_sub_category` (level 2)

| Field | Prisma Type | Description |
|---|---|---|
| `id` | `String @db.Uuid` | Primary key. |
| `product_category_id` | `String @db.Uuid` | **FK to `tb_product_category`** — parent in hierarchy. |
| `code`, `name`, `description` | `String` | Identification. |
| `price_deviation_limit` / `qty_deviation_limit` | `Decimal(20,5)?` | Override parent. |
| `is_used_in_recipe` / `is_sold_directly` / `is_active` | `Boolean?` | Flag overrides. |
| `tax_profile_id` / `tax_rate` | mixed | Tax override. |
| Audit columns | — | Standard. |

**Constraints:** `@@unique([code, name, deleted_at])`. Reverse relation to `tb_product_item_group`.

### 5.3 `tb_product_item_group` (level 3 — leaf)

| Field | Prisma Type | Description |
|---|---|---|
| `id` | `String @db.Uuid` | Primary key. |
| `product_subcategory_id` | `String @db.Uuid` | **FK to `tb_product_sub_category`** — parent. |
| `code`, `name`, `description` | `String` | Identification. |
| `price_deviation_limit` / `qty_deviation_limit` / `is_*` / `tax_*` | mixed | Same shape as parents; finest-grained override. |
| Audit columns | — | Standard. |

Each level also has a `*_comment` table for discussion and attachments.

> **Hierarchy depth.** Schema fixes the tree at exactly three levels. `../carmen/docs/product-management/PROD-Overview.md` describes "up to five levels" as an ambition; the Prisma schema currently enforces three. (Inferred — schema is source of truth.)

## 6. Lifecycle / Business Rules

```
1. Product Admin creates a category (unique code + name)
2. Sub-categories added under it; item groups under each sub-category
3. Defaults (tax, deviation tolerances, is_used_in_recipe, is_sold_directly)
   cascade downward at INSERT; can be overridden at any level
4. Each tb_product references one (category, sub_category, item_group) triple
5. Deactivation (is_active = false) hides from new-product pickers;
   historical products still render. Soft-delete is BLOCKED while any
   tb_product still references the row (application-enforced; FK = NoAction)
```

- **Code uniqueness.** Category `code` unique among non-deleted; sub-category / item-group codes unique within parent.
- **Hierarchy integrity.** Sub-category cannot be re-parented once item groups have products — FK `NoAction`.
- **Tax change.** Affects new products only; existing products keep snapshotted setup unless re-saved.
- **Deviation tolerances.** Percentages 0-100; `0` = "no tolerance configured" → falls back to app default.

## 7. Cross-References

- [[product]] — every product carries a `(category, sub_category, item_group)` triple
- [[product/03-user-flow-product-admin]] — Product Admin maintains the tree
- [[purchase-request]] &nbsp;·&nbsp; [[purchase-order]] (`price_deviation_limit`) &nbsp;·&nbsp; [[good-receive-note]] (`qty_deviation_limit`)
- [[recipe]] — `is_used_in_recipe` filter
- [[access-control/permission]] — category-scoped filters for Purchaser / Store Keeper
- [[master-data/tax-profile]] — `tax_profile_id` cascade

## 8. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_product_category` (~1566-1602), `tb_product_sub_category` (~1711-1748), `tb_product_item_group` (~1638-1675), `tb_product_category_comment` (~1604-1636).
- **Frontend:** `../carmen-inventory-frontend/app/(root)/product-management/category/`.
- **carmen/docs:** `../carmen/docs/product-management/PROD-API-Endpoints-Categories.md`; `../carmen/docs/product-management/PROD-Overview.md`.
- **Module landing:** [[product]] § 3 (Product Category key concept).

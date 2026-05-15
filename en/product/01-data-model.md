---
title: Product — Data Model
description: Entities, fields, relationships, and enums for the product module.
published: true
date: 2026-05-15T15:30:00.000Z
tags: product, data-model, carmen-software
editor: markdown
dateCreated: 2026-05-15T15:30:00.000Z
---

# Product — Data Model

> **Source of truth:** Backend Prisma schema. Always read these first when writing or updating this page:
> - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma`
> - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma`
>
> The `generated/client/schema.prisma` files under each package are auto-generated copies and not authoritative.

## 1. Overview

The Product module is the **system of record for the catalogue every transactional document references**. Unlike a document-centric module (PR, PO, GRN, SR) that carries a workflow document with a header → detail → comment tree, the product tree is a **family of master-data tables** anchored by `tb_product`. Each product is identified by a UUID `id` and a human `code`/`name`, sits in a classification chain (`tb_product_item_group → tb_product_sub_category → tb_product_category`), is measured in a base inventory `tb_unit`, optionally has unit-conversions (`tb_unit_conversion` with `enum_unit_type ∈ {order_unit, ingredient_unit}`), is enabled at storage locations via `tb_product_location` (carrying per-location `min_qty` / `max_qty` / `re_order_qty` / `par_qty`), and may carry vendor mappings via `tb_product_tb_vendor`. The product itself has a small but consequential set of header fields: `code`, `name`, `local_name`, `description`, `inventory_unit_id`, `product_status_type` (`enum_product_status_type = active | inactive`), `product_item_group_id`, `is_used_in_recipe`, `is_sold_directly`, `barcode`, `sku`, `price_deviation_limit`, `qty_deviation_limit`, `standard_cost`, `tax_profile_id` / `tax_profile_name` / `tax_rate`, `is_active`, plus extension JSON (`info`, `dimension`, `certification`). Comment threads (`tb_product_comment`, plus parallel comment tables on every classification level) supply the auditable conversation surface used everywhere else in the ERP.

The module sits **at the dependency root of every transactional module**. Every PR line, PO line, GRN line, SR line, count line, recipe ingredient, inventory transaction, and cost-layer row carries a `product_id` reference. There is no transactional posting on a product — the lifecycle is `create → active → deprecated (inactive) → soft-deleted`, gated by usage checks (a product with non-zero inventory, with open documents, or referenced by an active recipe cannot be soft-deleted). The classification tree (`category → sub-category → item-group`) carries cascading tax-profile and deviation-tolerance defaults; the product can override category-level values but most installations keep them in inheritance to keep the catalogue consistent. Unit conversions are validated for **bidirectional consistency** at the application layer (`from_unit_qty × conversion_factor = to_unit_qty` must round-trip), and the engine resolves any document line's qty back to the base unit using `tb_unit_conversion` rows.

A few structural points are worth restating up front. **First**, the canonical schema is **flatter and simpler than the carmen/docs PRD describes** — there is no `tb_product_variant` model, no `tb_product_attribute` typed key-value table, no `tb_product_media` table, no `tb_product_carbon_footprint` model. Attributes, variants, media, sustainability data, and certification are persisted on the **JSON extension bags** (`info`, `dimension`, `certification`) on `tb_product` or referenced via free-form `attachments` JSON on the comment tables. Section 5 catalogues these divergences in full. **Second**, `tb_product_location` does **not** carry on-hand qty — it is the **stock-policy row** only (min / max / par / reorder). On-hand qty is derived from the inventory cost-layer ledger (see [[inventory/01-data-model]] § 5 item 1). **Third**, the **costing method is not on the product** — it lives on `tb_business_unit.calculation_method` (platform schema, `enum_calculation_method = average | fifo`) and applies to every product at that business unit. The product carries `standard_cost` (the reference cost used by the `standard` count-costing method and by recipe baselining) but not the FIFO / WA selector itself.

## 2. Entities

### 2.1 tb_product

The **product master row**. The single source of truth for product identity; every other transactional table joins back to this row via `product_id`.

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key; `gen_random_uuid()`. |
| `code` | `String @db.VarChar` | No | Human-readable product code. Used as the lookup key on pickers, on barcode labels (when `barcode` is not separately set), and on every downstream document line. Unique within `(code, name, deleted_at)` per the index `product_code_name_u`. |
| `name` | `String @db.VarChar` | No | English / primary display name. Indexed. |
| `local_name` | `String? @db.VarChar` | Yes | Localised name (e.g. Thai for Thai properties). Surfaced on receipts and on the local-language UI. |
| `description` | `String? @db.VarChar` | Yes | Free-text long description. |
| `inventory_unit_id` | `String @db.Uuid` | No | FK to `tb_unit.id` — the **base inventory unit** in which every balance, cost, and valuation for this product is stored. Cannot be changed once the product has any inventory transaction (no schema-level enforcement; business rule). |
| `inventory_unit_name` | `String @db.VarChar` | No | Snapshot of the base unit's display name; default `""`. |
| `product_status_type` | `enum_product_status_type` | No | Lifecycle status: `active` (appears on pickers, available for new transactions) or `inactive` (frozen — past history retained, excluded from new documents). Default `active`. |
| `product_item_group_id` | `String? @db.Uuid` | Yes | FK to `tb_product_item_group.id` — the leaf classification node (category → sub-category → **item-group → product**). Nullable for un-classified imports, but production catalogue requires it. |
| `is_used_in_recipe` | `Boolean?` | Yes | Default `true`. Marks the product as eligible to appear on recipe ingredient lines. Disabled for fixed-asset / non-consumable products (cleaning agents, equipment). |
| `is_sold_directly` | `Boolean?` | Yes | Default `false`. Marks the product as a POS-sellable item (e.g. bottled beverages sold over the counter, not just used in recipes). Drives menu-item linkage availability. |
| `barcode` | `String? @db.VarChar` | Yes | Scannable identifier (UPC, EAN, CODE128, etc.). Primary lookup key for mobile receiving / picking / counting. Business rule enforces uniqueness within `(barcode, deleted_at)`; no Prisma `@unique` declared, so the constraint runs in application code. |
| `sku` | `String? @db.VarChar` | Yes | Stock Keeping Unit identifier (typically distinct from `code` and `barcode` — used by external integrations / POS / e-commerce systems). |
| `price_deviation_limit` | `Decimal? @db.Decimal(20, 5)` | Yes | Default `0`. Percentage tolerance bound used by procurement / receiving rules (`PR_VAL_*`, `GRN_VAL_*`) to flag a downstream document line whose price diverges from the master by more than this amount. 0–100% by convention. |
| `qty_deviation_limit` | `Decimal? @db.Decimal(20, 5)` | Yes | Default `0`. Same idea as `price_deviation_limit` but for qty (e.g. ordered vs received). |
| `standard_cost` | `Decimal? @db.Decimal(20, 5)` | Yes | Default `0`. Reference / standard cost per base unit. Used by the `standard` count-costing method (`enum_physical_count_costing_method = standard`) and by recipe baseline costing. Not consumed by the FIFO / WA cost-pick engine — those read the cost-layer's `cost_per_unit`. |
| `tax_profile_id` | `String? @db.Uuid` | Yes | FK to `tb_tax_profile.id` — the tax profile (VAT category, tax rule set) applied to the product on downstream transactions. Typically inherited from the classification chain (`tb_product_item_group.tax_profile_id` or `tb_product_sub_category.tax_profile_id` or `tb_product_category.tax_profile_id`); product-level setting overrides. |
| `tax_profile_name` | `String? @db.VarChar` | Yes | Snapshot of the tax profile name. |
| `tax_rate` | `Decimal? @db.Decimal(15, 5)` | Yes | Default `0`. Snapshot of the rate from the tax profile at the time of last sync. |
| `is_active` | `Boolean?` | Yes | Default `true`. Hard-disable flag (distinct from `product_status_type` — `is_active = false` removes the product from all pickers including admin views; `product_status_type = inactive` removes it from new-transaction pickers but still admin-visible). |
| `note` | `String? @db.VarChar` | Yes | Free-text note. |
| `info` | `Json? @db.JsonB` | Yes | Extension bag for tenant-specific attributes (shelf life, storage instructions, size, color, allergens, packaging — anything the canonical PRD describes as "attribute" lives here as JSON); default `{}`. |
| `dimension` | `Json? @db.JsonB` | Yes | Cost-dimension array (project, cost-centre, job code) for default dimension on downstream documents; default `[]`. |
| `certification` | `Json? @db.JsonB` | Yes | Extension bag for certification data (organic, fair-trade, halal, kosher, sustainability ratings, carbon footprint score); default `{}`. |
| `created_at` | `DateTime? @db.Timestamptz(6)` | Yes | Creation timestamp; defaults to `now()`. |
| `created_by_id` | `String? @db.Uuid` | Yes | Creator id. |
| `updated_at` | `DateTime? @db.Timestamptz(6)` | Yes | Last-update timestamp. |
| `updated_by_id` | `String? @db.Uuid` | Yes | Updater id. |
| `deleted_at` | `DateTime? @db.Timestamptz(6)` | Yes | Soft-delete timestamp; non-null means logically deleted. |
| `deleted_by_id` | `String? @db.Uuid` | Yes | Soft-delete actor id. |

**Constraints:** `@id` on `id`. FKs: `inventory_unit_id → tb_unit.id` (`NoAction`); `product_item_group_id → tb_product_item_group.id` (`NoAction`); `tax_profile_id → tb_tax_profile.id` (`NoAction`).
**Indexes:** `@@unique([code, name, deleted_at])` as `product_code_name_u`; `@@index([code])` as `product_code_idx`; `@@index([name])` as `product_name_idx`.
**Back-relations:** an extensive list including `tb_count_stock_detail`, `tb_credit_note_detail`, `tb_good_received_note_detail`, `tb_pricelist_detail`, `tb_product_location`, `tb_product_tb_vendor`, `tb_purchase_request_detail`, `tb_purchase_request_template_detail`, `tb_stock_in_detail`, `tb_stock_out_detail`, `tb_store_requisition_detail`, `tb_unit_conversion`, `tb_pricelist_template_detail`, `tb_spot_check_detail`, `tb_physical_count_detail`, `tb_product_comment`, `tb_recipe_ingredient`, `tb_purchase_order_detail`. Every transactional table downstream of inventory references the product.

### 2.2 tb_product_category

The **top-level classification node**. The first level of the classification hierarchy (`category → sub-category → item-group`) and the carrier of category-level defaults that propagate to children.

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `code` | `String @db.VarChar` | No | Human-readable category code. |
| `name` | `String @db.VarChar` | No | Display name. |
| `description` | `String? @db.VarChar` | Yes | Free-text. |
| `is_active` | `Boolean?` | Yes | Default `true`. |
| `price_deviation_limit` | `Decimal? @db.Decimal(20, 5)` | Yes | Default `0`. Category-level default for the product's `price_deviation_limit`. Inherited unless the product overrides. |
| `qty_deviation_limit` | `Decimal? @db.Decimal(20, 5)` | Yes | Default `0`. Category-level default for the product's `qty_deviation_limit`. |
| `is_used_in_recipe` | `Boolean?` | Yes | Default `true`. Category-level default for the product's `is_used_in_recipe`. |
| `is_sold_directly` | `Boolean?` | Yes | Default `false`. Category-level default. |
| `tax_profile_id` | `String? @db.Uuid` | Yes | FK to `tb_tax_profile.id`. Category-level default; inherited by sub-categories, item-groups, and products unless overridden. |
| `tax_profile_name` | `String? @db.VarChar` | Yes | Snapshot. |
| `tax_rate` | `Decimal? @db.Decimal(15, 5)` | Yes | Default `0`. Snapshot. |
| `note` | `String? @db.VarChar` | Yes | Free-text. |
| `info` | `Json? @db.JsonB` | Yes | Extension bag; default `{}`. |
| `dimension` | `Json? @db.JsonB` | Yes | Cost-dimension array; default `[]`. |
| `created_at` / `created_by_id` / `updated_at` / `updated_by_id` / `deleted_at` / `deleted_by_id` | audit | Yes | Standard audit columns. |

**Constraints:** `@id` on `id`. FK `tax_profile_id → tb_tax_profile.id` (`NoAction`).
**Indexes:** `@@unique([code, name, deleted_at])` as `productcategory_code_name_u`; `@@unique([code, deleted_at])` as `productcategory_code_u`; `@@index([code])` as `productcategory_code_idx`; `@@index([name])` as `productcategory_name_idx`.
**Back-relations:** `tb_product_sub_category`, `tb_product_category_comment`.

### 2.3 tb_product_sub_category

The **second-level classification node**. Hangs off a `tb_product_category` and carries inherited / override defaults to its `tb_product_item_group` children.

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `product_category_id` | `String @db.Uuid` | No | FK to `tb_product_category.id`. |
| `code` | `String @db.VarChar` | No | Default `""`. Sub-category code. |
| `name` | `String @db.VarChar` | No | Display name. |
| `description` | `String? @db.VarChar` | Yes | Free-text. |
| `price_deviation_limit` | `Decimal? @db.Decimal(20, 5)` | Yes | Default `0`. Sub-category-level default; inherits from category if zero. |
| `qty_deviation_limit` | `Decimal? @db.Decimal(20, 5)` | Yes | Default `0`. |
| `is_used_in_recipe` | `Boolean?` | Yes | Default `true`. |
| `is_sold_directly` | `Boolean?` | Yes | Default `false`. |
| `is_active` | `Boolean?` | Yes | Default `true`. |
| `tax_profile_id` | `String? @db.Uuid` | Yes | FK to `tb_tax_profile.id`. Override; falls back to category-level. |
| `tax_profile_name` | `String? @db.VarChar` | Yes | Snapshot. |
| `tax_rate` | `Decimal? @db.Decimal(15, 5)` | Yes | Default `0`. |
| `note` / `info` / `dimension` / audit | various | Yes | Standard. |

**Constraints:** `@id` on `id`. FKs: `product_category_id → tb_product_category.id` (`NoAction`); `tax_profile_id → tb_tax_profile.id` (`NoAction`).
**Indexes:** `@@unique([code, name, deleted_at])` as `productsubcategory_code_name_u`; `@@index([code])` / `@@index([name])`.
**Back-relations:** `tb_product_item_group`, `tb_product_sub_category_comment`.

### 2.4 tb_product_item_group

The **third-level (leaf) classification node** — the level the product directly attaches to. Carries the final inherited / override defaults and is the join point for products to the classification tree.

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `product_subcategory_id` | `String @db.Uuid` | No | FK to `tb_product_sub_category.id`. Note the column name uses `subcategory` (no underscore between `sub` and `category`); the parent model uses `tb_product_sub_category`. |
| `code` | `String @db.VarChar` | No | Item-group code. |
| `name` | `String @db.VarChar` | No | Display name. |
| `description` | `String? @db.VarChar` | Yes | Free-text. |
| `price_deviation_limit` | `Decimal? @db.Decimal(20, 5)` | Yes | Default `0`. Item-group-level override. |
| `qty_deviation_limit` | `Decimal? @db.Decimal(20, 5)` | Yes | Default `0`. |
| `is_used_in_recipe` | `Boolean?` | Yes | Default `true`. |
| `is_sold_directly` | `Boolean?` | Yes | Default `false`. |
| `is_active` | `Boolean?` | Yes | Default `true`. |
| `tax_profile_id` | `String? @db.Uuid` | Yes | FK to `tb_tax_profile.id`. Final override; falls back through sub-category to category. |
| `tax_profile_name` | `String? @db.VarChar` | Yes | Snapshot. |
| `tax_rate` | `Decimal? @db.Decimal(15, 5)` | Yes | Default `0`. |
| `note` / `info` / `dimension` / audit | various | Yes | Standard. |

**Constraints:** `@id` on `id`. FKs: `product_subcategory_id → tb_product_sub_category.id` (`NoAction`); `tax_profile_id → tb_tax_profile.id` (`NoAction`).
**Indexes:** `@@unique([code, name, product_subcategory_id, deleted_at])` as `productitemgroup_code_name_product_subcategory_u`; `@@index([code])` / `@@index([name])`.
**Back-relations:** `tb_product`, `tb_product_item_group_comment`.

### 2.5 tb_unit

The **unit-of-measure definition**. Both inventory base units (`KG`, `LITRE`, `EACH`) and order / recipe units (`CASE`, `DOZEN`, `TBSP`) share this single table — there is no `unit_type` column on the unit itself; the type emerges from the join (`tb_product.inventory_unit_id` for base, `tb_unit_conversion` for order / recipe).

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `name` | `String @db.VarChar` | No | Display name (e.g. `KG`, `CASE`). |
| `description` | `String? @db.VarChar` | Yes | Free-text. |
| `is_active` | `Boolean?` | Yes | Default `true`. |
| `decimal_place` | `Int` | No | Default `2`. Display precision for quantities expressed in this unit. The underlying storage on cost-layer / detail is always `Decimal(20, 5)`; this column drives rounding for display only. |
| `note` / `info` / `dimension` / audit | various | Yes | Standard. |

**Constraints:** `@id` on `id`.
**Indexes:** `@@unique([name, deleted_at])` as `unit_name_deletedat_u`; `@@index([name])` as `unit_name_idx`.
**Back-relations:** wide — `tb_product` (as base), `tb_pricelist_detail`, multiple variants on `tb_purchase_order_detail` (base / order), `tb_purchase_request_detail` (approved / foc / requested), `tb_unit_conversion` (as `from_unit` and `to_unit`), GRN detail-item variants (foc / received / order), recipe ingredient (ingredient / inventory), physical-count detail, spot-check detail, `tb_unit_comment`.

### 2.6 tb_unit_conversion

The **conversion-factor row**. Defines how a quantity expressed in one unit translates to another, scoped to a `product_id` (so the same `CASE` can mean 12 `EACH` of product A but 24 `EACH` of product B) and to a `unit_type` (`order_unit` for procurement-side conversions, `ingredient_unit` for recipe-side conversions).

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `product_id` | `String? @db.Uuid` | Yes | FK to `tb_product.id`. Nullable for "generic" conversions (e.g. `1 KG = 1000 G`) but typically populated per-product because the multiplier varies. |
| `unit_type` | `enum_unit_type` | No | `order_unit` (procurement / receiving / vendor pricelist conversions) or `ingredient_unit` (recipe / consumption conversions). The two namespaces are kept distinct so a product's order-unit conversions don't bleed into recipe scaling. |
| `from_unit_id` | `String? @db.Uuid` | Yes | FK to `tb_unit.id` — the source unit. Nullable for the rare case where only a name snapshot is needed. |
| `from_unit_name` | `String @db.VarChar` | No | Snapshot of the source unit name. |
| `from_unit_qty` | `Decimal? @db.Decimal(20, 5)` | Yes | Default `0`. Quantity on the source side of the conversion (e.g. `1` for "1 CASE = 12 EACH"). |
| `to_unit_id` | `String? @db.Uuid` | Yes | FK to `tb_unit.id` — the destination unit. |
| `to_unit_name` | `String @db.VarChar` | No | Snapshot. |
| `to_unit_qty` | `Decimal? @db.Decimal(20, 5)` | Yes | Default `0`. Quantity on the destination side (e.g. `12` for "1 CASE = 12 EACH"). The conversion factor is `to_unit_qty / from_unit_qty`. |
| `decimal_place` | `Int` | No | Default `2`. Display precision. |
| `is_default` | `Boolean?` | Yes | Default `false`. Marks this conversion as the default order-unit (or default ingredient-unit) for the product — surfaced first on pickers. |
| `description` | `Json? @db.JsonB` | Yes | Free-text / structured note; default `{}`. |
| `is_active` | `Boolean?` | Yes | Default `true`. |
| `note` / `info` / `dimension` / audit | various | Yes | Standard. |

**Constraints:** `@id` on `id`. FKs: `from_unit_id → tb_unit.id` (`NoAction`) via the named relation `tb_unit_conversion_from_unit_idTotb_unit`; `to_unit_id → tb_unit.id` (`NoAction`) via `tb_unit_conversion_to_unit_idTotb_unit`; `product_id → tb_product.id` (`NoAction`).
**Indexes:** `@@unique([product_id, unit_type, from_unit_id, to_unit_id, deleted_at])` as `unitconversion_product_unit_type_from_unit_to_unit_deletedat_u`; `@@index([product_id, unit_type, from_unit_id, to_unit_id])`; `@@index([product_id])`.

### 2.7 tb_product_location

The **per-product / per-location stock-policy row**. Holds par / min / max / reorder qty used by the replenishment-suggestion and over/under-stock alert logic. Does **not** carry on-hand qty (derived from the inventory cost-layer ledger).

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `product_id` | `String @db.Uuid` | No | FK to `tb_product.id`. |
| `location_id` | `String? @db.Uuid` | Yes | FK to `tb_location.id`. |
| `min_qty` | `Decimal? @db.Decimal(20, 5)` | Yes | Default `0`. Below this triggers a replenishment alert. |
| `max_qty` | `Decimal? @db.Decimal(20, 5)` | Yes | Default `0`. Above this triggers an over-stock alert. |
| `re_order_qty` | `Decimal? @db.Decimal(20, 5)` | Yes | Default `0`. Suggested order qty when on-hand drops below `min_qty`. |
| `par_qty` | `Decimal? @db.Decimal(20, 5)` | Yes | Default `0`. Par level for outlet stocking (target on-hand). |
| `note` / `info` / `dimension` | various | Yes | Standard. |
| `doc_version` | `Int` | No | Default `0`. Optimistic-concurrency counter; used when multiple users edit the policy concurrently. |
| audit | various | Yes | Standard `created_at` / `created_by_id` / `updated_at` / `updated_by_id` / `deleted_at` / `deleted_by_id`. |

**Constraints:** `@id` on `id`. FKs: `product_id → tb_product.id` (`NoAction`); `location_id → tb_location.id` (`NoAction`).
**Indexes:** `@@unique([product_id, location_id, deleted_at])` as `product_location_product_id_location_id_u`; `@@index([product_id, location_id])`.

### 2.8 tb_product_tb_vendor

The **product–vendor join** that lists which vendors supply a product, with the vendor's own product code and name for cross-reference. Used by [[vendor-pricelist]] and [[purchase-request]] / [[purchase-order]] to scope vendor pickers.

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `product_id` | `String @db.Uuid` | No | FK to `tb_product.id`. |
| `product_code` / `product_name` / `product_local_name` / `product_sku` | `String? @db.VarChar` | Yes | Snapshots of the master fields (denormalised so the join row survives product re-coding). |
| `vendor_id` | `String? @db.Uuid` | Yes | FK to `tb_vendor.id`. |
| `vendor_product_code` | `String? @db.VarChar` | Yes | The vendor's own code for this product (used on POs and pricelists when the vendor expects their own SKU on the document). |
| `vendor_product_name` | `String? @db.VarChar` | Yes | Vendor's own product name. |
| `description` | `String? @db.VarChar` | Yes | Free-text. |
| `is_active` | `Boolean?` | Yes | Default `true`. |
| `note` / `info` / `dimension` / audit | various | Yes | Standard. |

**Constraints:** `@id` on `id`. FKs: `product_id → tb_product.id` (`NoAction`); `vendor_id → tb_vendor.id` (`NoAction`).
**Indexes:** `@@unique([vendor_id, product_id, deleted_at])` as `product_vendor_vendor_product_u`; `@@index([product_id])` as `product_vendor_product_id_idx`; `@@index([vendor_id])` as `product_vendor_vendor_id_idx`.

### 2.9 Comment tables (tb_product_comment, tb_product_category_comment, tb_product_sub_category_comment, tb_product_item_group_comment, tb_unit_comment)

Each entity in the product tree has a **parallel comment table** carrying the conversation surface. All comment tables share the same shape: `id`, `<parent>_id` FK to the parent, `type` (`enum_comment_type`, default `user`), `user_id`, `message`, `attachments` (JSON array of `{originalName, fileToken, contentType}` objects mapping to S3-uploaded files), and the standard audit columns. The `enum_comment_type` distinguishes `user` (free-text from a person) from `system` (automated event annotations — e.g. import-job summary, status-transition log line); this convention is consistent across every module that uses comments.

The comment tables are the **audit-conversation surface**, not the activity log. The activity log (workflow-history, status transitions, field changes) lives on the parent row's `info` JSON or in dedicated workflow columns; the comment table is for free-form human discussion attached to the master-data entity.

## 3. Relationships

```
tb_product_category
    │ 1 — *
    ▼
tb_product_sub_category   (product_category_id)
    │ 1 — *
    ▼
tb_product_item_group     (product_subcategory_id — note: column name uses 'subcategory')
    │ 1 — *
    ▼
tb_product                (product_item_group_id)
    │
    ├──► tb_unit          (inventory_unit_id — the base inventory unit)
    │
    ├──► tb_tax_profile   (tax_profile_id — override-able; falls back through item-group → sub-category → category)
    │
    │ 1 — *
    ▼
tb_unit_conversion        (product_id; unit_type ∈ {order_unit, ingredient_unit};
                           from_unit_id, to_unit_id → tb_unit.id)
    │
    │ 1 — *
    ▼
tb_product_location       (product_id, location_id; min/max/par/reorder — no on-hand)
    │
    └──► tb_location

tb_product
    │ 1 — *
    ▼
tb_product_tb_vendor      (product_id, vendor_id; vendor_product_code / vendor_product_name)
    │
    └──► tb_vendor


tb_product is reached BY every transactional table downstream:
    tb_purchase_request_detail.product_id
    tb_purchase_order_detail.product_id
    tb_good_received_note_detail.product_id
    tb_store_requisition_detail.product_id
    tb_stock_in_detail.product_id / tb_stock_out_detail.product_id
    tb_count_stock_detail.product_id / tb_spot_check_detail.product_id / tb_physical_count_detail.product_id
    tb_credit_note_detail.product_id
    tb_pricelist_detail.product_id / tb_pricelist_template_detail.product_id
    tb_recipe_ingredient.product_id
    tb_inventory_transaction_detail.product_id (no @relation — application-resolved)
    tb_inventory_transaction_cost_layer.product_id (no @relation — application-resolved)
    tb_period_snapshot.product_id (no @relation — application-resolved)
```

Notes:

- **The classification tree carries cascading defaults.** `price_deviation_limit`, `qty_deviation_limit`, `is_used_in_recipe`, `is_sold_directly`, and `tax_profile_id` exist on **every level** of the tree (`tb_product_category`, `tb_product_sub_category`, `tb_product_item_group`, `tb_product`). The application's inheritance rule is to read the most-specific non-zero / non-null value walking up from the product through the classification chain. This is **not** Prisma-enforced — the inheritance happens at read time in the service layer.
- **No `tb_product_variant` model.** Variants (size, color, packaging combinations) are not modelled as a separate table; they live as JSON in `tb_product.info` or as additional `tb_product` rows with shared category/item-group. See Section 5 item 1.
- **No `tb_product_attribute` model.** Typed key-value attributes (the PRD's `attributeType ∈ {text, number, boolean, date, select, multi-select, rich-text}`) are not modelled as a normalised table; they live as JSON in `tb_product.info`. The category-level attribute requirement / inheritance is documented in carmen/docs but is **not** schema-enforced. See Section 5 item 2.
- **No `tb_product_media` model.** Product images / documents / videos are not modelled as a separate table. The `tb_product_comment.attachments` JSON array (file-token references) is the only attachment surface in the canonical schema; first-class product-media (designated primary image, thumbnails, ordering) lives in the application layer or is deferred. See Section 5 item 3.
- **Soft-delete is universal.** Every entity in this module carries `deleted_at` / `deleted_by_id`. The unique constraints include `deleted_at` (e.g. `product_code_name_u = (code, name, deleted_at)`) so a deleted product's code can be reused; the live row guards uniqueness only against other live rows.
- **All explicit `@relation` FK declarations use `onDelete: NoAction, onUpdate: NoAction`** — referential integrity is preserved by application-level soft-delete and by the in-use guards (a product with non-zero on-hand or open documents cannot be deleted).

## 4. Enums

- **`enum_product_status_type`**: lifecycle status on `tb_product.product_status_type`. Default `active`. Two values:
  - `active` — the product appears on pickers and is available for new transactions.
  - `inactive` — the product is frozen. Past history (balances, posted documents, recipes) is retained, but the product is excluded from new-document pickers. The transition is auditable and can be scheduled to take effect on a future date by the application layer (no schema-level effective-date column).
- **`enum_unit_type`**: scope on `tb_unit_conversion.unit_type`. No default declared; required on every row. Two values:
  - `order_unit` — conversion is used by procurement / receiving / vendor-pricelist (e.g. `1 CASE = 12 EACH`). Drives PR / PO / GRN qty translation back to the base inventory unit.
  - `ingredient_unit` — conversion is used by recipe / consumption (e.g. `1 TBSP = 15 ML`). Drives recipe ingredient qty translation back to the base unit at theoretical-consumption explosion time.
- **`enum_comment_type`**: comment classifier on every `*_comment.type`. Default `user`. Values: `user` (human free-text), `system` (automated event annotation).

The schema also relies on **upstream enums consumed by the product module but not owned by it**:

- `enum_calculation_method` (on `tb_business_unit.calculation_method`, platform schema): `average`, `fifo`. The costing-method selector — **not on the product**. See [[costing/01-data-model]] § 2.4.
- `enum_physical_count_costing_method` (on count documents): `standard`, `last`, `average`, `last_receiving`. Selects which cost source feeds count-variance posts; `standard` reads `tb_product.standard_cost`. See [[costing/01-data-model]] § 2.6.

## 5. Divergences from carmen/docs

The carmen/docs product-management PRD (`PROD-PRD.md`) and product-master PRD (`product-master-prd.md`) describe a substantially richer interface model than the Prisma reality. Cross-checking against the canonical Prisma schema yields the following divergences — expected for a master-data module of this breadth.

| # | Item | carmen/docs says | Prisma has | Action |
|---|------|------------------|------------|--------|
| 1 | Product Variants | `PROD-PRD.md` § 3.1.3 (FR-PRD-021..030): explicit `Variant` entity with unique variant code, variant-specific pricing / costing, variant-specific media, variant attribute matrix, variant-specific inventory tracking, variant-specific sustainability info. `product-master-prd.md` § 3.2.8 product types include `Variant`. | **No `tb_product_variant` model exists.** Variants are modelled as either: (a) additional `tb_product` rows (each variant is its own product with its own `code` / `sku` / `barcode`, sharing category / item-group / base unit with the "parent"); or (b) JSON keys in `tb_product.info` for low-cardinality variations (e.g. `{ "variants": [{ "size": "small", "barcode": "...", "price": 95 }, ...] }`). There is no parent-variant relationship column on `tb_product`. | Treat Prisma as canonical. Update carmen/docs to describe variants as "products-as-variants" (one row per variant) for production-quality variant tracking, or "JSON variants" for catalog-display-only variations. The "variant matrix generator" UI described in `UI-PRD-025` lives as a frontend-only helper that creates multiple `tb_product` rows in one flow. |
| 2 | Typed Product Attributes | `PROD-PRD.md` § 3.1.2 (FR-PRD-011..020): typed attributes (`text`, `number`, `boolean`, `date`, `select`, `multi-select`, `rich-text`), assignment of attributes to products, required / optional flags, validation rules, inheritance from categories, bulk update of attribute values. Category-level attribute definition with sub-category override. | **No `tb_product_attribute` / `tb_product_attribute_value` models exist.** Product attributes live as **untyped JSON** in `tb_product.info` (and category-level "attribute defaults" similarly in `tb_product_category.info`). No schema-level validation of attribute types, required-ness, or inheritance — those rules run in the application layer (when they run at all). The carmen/docs PRD describes a feature that is partially aspirational. | Document that the "attribute system" is **JSON-only** at the schema level; typed validation and category inheritance are application-layer conventions. Update carmen/docs to describe the JSON shape (`info: { attributes: { <key>: <value> } }`) and the application-layer rules that police it. |
| 3 | Product Media (images / documents / videos / 3D models) | `PROD-PRD.md` § 3.1.4 (FR-PRD-031..040): designated primary media, ordering, thumbnails, AI-powered auto-tagging, mobile-optimised delivery. `UI-PRD-013` references a media gallery on the product detail view. | **No `tb_product_media` model.** Attachments live on the comment table (`tb_product_comment.attachments` — JSON array of `{originalName, fileToken, contentType}`); there is no first-class "product image" with `is_primary` / `display_order` / `thumbnail_url`. The frontend may pick the first comment attachment with `contentType` starting with `image/` as the primary, but this is convention, not schema. | Add `tb_product_media` to the future-schema backlog (or document the JSON convention if media is left in the comment table); for now, frontend renders attachments-as-media without the rich metadata the PRD describes. |
| 4 | Product Lifecycle States | `PROD-PRD.md` § 3.1.5 (FR-PRD-041..050) and `product-master-prd.md`: lifecycle includes `Active`, `Inactive`, **`Discontinued`**, plus scheduled status changes, status history tracking, status-based visibility controls, lifecycle visualisation. | `enum_product_status_type` has **two values only**: `active`, `inactive`. There is no `discontinued` value; no first-class status-history table (the implicit history is on the audit columns and on `tb_product_comment` system entries); no schema-level scheduled-change column. | Add `discontinued` to the enum if it's needed for operational distinction (e.g. "inactive but explicitly end-of-life"), or document that "discontinued" maps to `inactive` with a comment explaining the reason. Scheduled changes and status-history reporting are application-layer concerns. |
| 5 | Barcode Uniqueness and Generation | `PROD-PRD.md` § 3.1.6 (FR-PRD-051..058): generation, multiple formats (UPC, EAN, CODE128), printing, scanning, uniqueness validation, bulk generation, QR with embedded product info. | `tb_product.barcode` is a free-text column with **no `@unique` constraint** at the schema level. Uniqueness is application-enforced (rejected at create / update). Format selection (UPC vs EAN vs CODE128) is implicit in the value; no `barcode_format` enum on the product. | Document that barcode uniqueness is application-only; if uniqueness is critical at the DB level, add `@@unique([barcode, deleted_at])` in the next migration. Format selection is a frontend / printing concern. |
| 6 | Carbon Footprint and Sustainability Tracking | `PROD-PRD.md` § 3.1.7 (FR-PRD-059..066): track carbon footprint, sustainability ratings and certifications, packaging info, sustainability comparisons, third-party DB integration, sustainability goal tracking. | `tb_product.certification` is a single `Json @db.JsonB` column with default `{}`. There is **no `tb_product_carbon_footprint` model**, no `tb_product_sustainability_rating` model, and no schema-level certification typing. All sustainability data lives in the `certification` JSON. | Document the JSON shape convention (e.g. `certification: { carbonFootprintKgCo2e: <n>, certifications: ['organic', 'fair-trade'], packagingMaterial: '...' }`) and acknowledge that the rich sustainability features in the PRD are application-layer or future-schema. |
| 7 | Per-product Costing Method (FIFO / Weighted Average) | `inventory-management-prd.md` and `PROD-PRD.md` derived discussions imply `valuationMethod: FIFO | WEIGHTED_AVERAGE` configured per product. | **The costing method is not on `tb_product`.** It lives on `tb_business_unit.calculation_method` (platform schema, `enum_calculation_method = average | fifo`), applying property-wide. The product carries `standard_cost` (reference cost) but not the FIFO / WA selector. | Realign carmen/docs to describe the costing method as **business-unit-level**, not per-product. Document the parallel `enum_business_unit_config_key.calculation_method` runtime-config surface for tenant-level overrides. See [[costing/01-data-model]] § 2.4. |
| 8 | Category Hierarchy Depth ("up to 5 levels") | `PROD-PRD.md` § 3.2.2 (FR-CAT-011): "hierarchical category structures up to 5 levels deep"; index claim repeated. | The Prisma schema implements **exactly 3 levels**: `tb_product_category → tb_product_sub_category → tb_product_item_group`. There is no `tb_product_sub_sub_category` or self-referential `parent_id` on category. Five levels are not supported by the canonical schema. | Update carmen/docs to state "three-level classification (category → sub-category → item-group)". If a deeper hierarchy is operationally required, it must come from a schema change (self-referential `parent_id` on `tb_product_category` and migration of sub-category / item-group). |
| 9 | Conversion Factor Bidirectional Validation | `PROD-PRD.md` § 3.3.2 (FR-UNT-011..020): bidirectional conversions, circular-conversion validation, conversion-factor integrity, complex conversions across multiple unit types. | `tb_unit_conversion` carries `from_unit_qty` / `to_unit_qty` on each row; the "conversion factor" is `to_unit_qty / from_unit_qty`. Bidirectional consistency (`from → to → from` round-trip exactness) is **application-layer-validated** at row create / update — no schema-level constraint enforces consistency across multiple rows for the same `(product_id, unit_type)`. Circular detection is also application-only. | Document that the bidirectional / circular checks live in the service layer; if they're not yet implemented, log as a backlog item. The schema permits inconsistent rows; the application guard is what keeps them consistent. |
| 10 | Sub-category Code Optional | `PROD-PRD.md` § 3.2: implies a code is required at every classification level. | `tb_product_sub_category.code` is declared `String @db.VarChar` (non-null) but **with `@default("")`** — i.e. the empty string is a valid value at the schema level. This is unusual; `tb_product_category.code` and `tb_product_item_group.code` are non-null without a default. | Document the schema quirk: the application UI requires a code on sub-categories, but the schema permits an empty string for legacy / migration cases. The `@@unique` on sub-category is `(code, name, deleted_at)`, so a sub-category with empty code is permitted as long as its `name` is unique within deleted_at-scope. |
| 11 | Product Templates and Bulk Operations | `PROD-PRD.md` § 3.1.1 / FR-PRD-006..008: bulk creation / editing, product templates, duplicate-as-starting-point. | No `tb_product_template` model. Bulk creation / editing is application-layer (CSV / Excel import). The "template" UI flow is a frontend convenience that produces multiple `tb_product` inserts in one transaction. | Document templates and bulk operations as application-layer / frontend conveniences without schema backing. |
| 12 | Standard vs Last Receiving Cost | `product-master-prd.md` § 3.2.6: discusses Standard Cost and "Last Receiving Cost" as paired figures on the product. | `tb_product.standard_cost` exists; **`last_receiving_cost` is not a column** on `tb_product`. The "last receiving cost" referenced in carmen/docs is **derived** from `tb_inventory_transaction_cost_layer` (most recent inbound row at `(product_id, *)` with `transaction_type ∈ {good_received_note, adjustment_in}`); the source GRN / vendor / date are also derived from the inventory transaction's source-document link. | Update carmen/docs to describe `lastReceivingCost` as a **derived field** read from the inventory ledger, not a persisted column. The product header surfaces it via a join, not via a column read. |
| 13 | Product–Vendor Mapping with Preferred / Primary Vendor | `PROD-PRD.md` § 6.2 (IR-PROC-009): preferred vendor assignments for products. | `tb_product_tb_vendor` carries the product–vendor join but has **no `is_preferred` / `is_primary` column**. Multiple vendors can be associated with a product, and the application typically uses the most-recent `tb_pricelist` price or vendor ranking, not a flag. | Document that preferred-vendor designation is **derived** (most recent pricelist, lowest price, or application-configurable rule) rather than persisted. Add an `is_preferred` column to `tb_product_tb_vendor` if first-class preferred-vendor designation is required. |
| 14 | Two-flag Active Status | `PROD-PRD.md` § 3.1.5: single status enum. | The product has **two** Active flags: `product_status_type ∈ {active, inactive}` AND `is_active: Boolean? @default(true)`. The semantic distinction (per Section 2.1) is `product_status_type = inactive` removes the product from new-transaction pickers but keeps it admin-visible; `is_active = false` is a hard-disable that removes the product everywhere. In practice, the two flags are often kept aligned. | Document the two-flag pattern. Recommend the application enforce that `is_active = false` always implies `product_status_type = inactive` (the reverse is not required). |

## 6. References

- **Primary (source of truth):** Prisma schemas listed in the header callout — concretely `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` for the product entities (`tb_product`, `tb_product_category`, `tb_product_sub_category`, `tb_product_item_group`, `tb_unit`, `tb_unit_conversion`, `tb_product_location`, `tb_product_tb_vendor`, and the parallel comment tables) and the enums `enum_product_status_type`, `enum_unit_type`. The platform schema `prisma-shared-schema-platform/prisma/schema.prisma` carries `tb_business_unit.calculation_method` and `enum_calculation_method` referenced from the costing perspective.
- **Secondary (concept cross-check):**
  - `../carmen/docs/product-management/PROD-PRD.md` — primary PRD describing the product-management feature set; divergences in Section 5 (items 1, 2, 3, 4, 5, 6, 8, 9, 11, 12, 13, 14).
  - `../carmen/docs/product-management/product-master-prd.md` — product-master PRD describing UI structure (List page, Detail page with tabs, Latest Purchase tab) and functional requirements; divergences in Section 5 (items 1, 6, 12).
  - `../carmen/docs/product-management/README.md` — module index.
  - `../carmen/docs/product-management/PROD-API-Endpoints-*.md` — REST endpoint catalogues (Products, Categories, Units, Locations, Import-Export, Overview); not used for schema authority but useful for surface-area reference.
- Related modules: [[inventory]] (every inventory balance and cost-layer references the product; product activation / deactivation gates new inventory transactions), [[costing]] (consumes `tb_product.standard_cost`; costing method lives at `tb_business_unit.calculation_method` not on the product), [[vendor-pricelist]] (pricelist lines reference products via `product_id`; vendor mapping comes through `tb_product_tb_vendor`), [[purchase-request]] / [[purchase-order]] / [[good-receive-note]] (every line references a product), [[store-requisition]] (issue / transfer lines reference products), [[recipe]] (recipe ingredient lines reference products as `product_id`, and sub-recipes reference other recipes — products with `is_used_in_recipe = true` appear on the picker), [[physical-count]] / [[spot-check]] / [[inventory-adjustment]] (count and adjustment documents reference products).

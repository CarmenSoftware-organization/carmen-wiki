---
title: Product Category
description: Three-level product taxonomy (category > sub-category > item group) that drives catalogue navigation, attribute inheritance, deviation tolerances, the Inventory / Direct GL account defaults used by account mapping, and an overwrite-to-descendants flow.
published: true
date: 2026-10-27T00:00:00.000Z
tags: product, category, taxonomy, master-data, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# Product Category

> **At a Glance**
> **Owner:** Product Admin &nbsp;·&nbsp; **Tables:** `tb_product_category` → `tb_product_sub_category` → `tb_product_item_group` (**3 FIXED levels**, NOT self-referential) &nbsp;·&nbsp; **Trigger:** taxonomy maintenance &nbsp;·&nbsp; **Used by:** PR / PO / GRN / recipe / reports / permission scoping &nbsp;·&nbsp; **1-liner:** classification layer driving navigation, inherited defaults, tolerances, and the GL account defaults.

![Product Category screen](/screenshots/product/category.png)

## 1. What & Who

Product Category is the classification layer over the product master. Every product carries a `(category, sub_category, item_group)` triple that drives:

1. **Catalogue navigation** — users drill `Food > Beverage > Coffee Beans` rather than scrolling
2. **Attribute inheritance** — tax profile, deviation tolerances, `is_used_in_recipe`, `is_sold_directly` default down the tree
3. **Cost / loss reporting roll-ups** — food cost, wastage, variance group by category at every level
4. **Permission scoping** — **unconfirmed**: the only category-related permission keys are the route-level `product_management.category` / `product_management.sub_category` (`permission.route-map.ts:110-114`); no code that restricts a Purchaser or Store Keeper to a category *branch* was found in the gateway auth layer this pass.

Maintained by the **Product Admin** persona. Referenced through `product_item_group_id` on every `tb_product` row (the category and sub-category are resolved by walking up; there is no `category_id` column on `tb_product`).

## 2. Common Tasks

| Task | Where | Notes |
|---|---|---|
| Add a top-level category | Product Management → Category → **Add Category** | The tree shows a live product count on each node (`product_count`; item groups carry it in the list payload). `code` is **server-generated** (running-number) — corrected this pass (2026-07-13 frontend change): the dialog's Code field is always disabled with an "auto-generated" placeholder and is stripped from the create payload; the API itself still accepts a client-supplied code (e.g. bulk import). |
| Add a sub-category | Hover the parent category row → click the **Add child** (+) icon that appears | FK `product_category_id` set to parent; child inherits the parent's tax profile / deviation defaults. There is no separate "Add sub-category" button — the same hover "Add child" action is used at every non-leaf level. |
| Add an item group (leaf) | Hover the sub-category row → click **Add child** (+) | FK `product_subcategory_id` set to parent; item groups are the leaf level and have no "Add child" action of their own. |
| Set price deviation tolerance | Edit any level → `price_deviation_limit` | 0–100 %. **Correction to the 2026-09-22 text, which called `cascade_deviation` a form-time helper with no stored effect — that was wrong.** The update API takes `cascade_deviation` (gateway and micro-business DTOs, `z.boolean().default(true).optional()`): when true and a limit is in the payload, the new value is **written onto every live descendant, including every product under the node** (`updateMany` inside the same transaction as the node update). The 2026-10 frontend replaced the old toggle with a confirmation dialog (below) and always sends `cascade_deviation` explicitly. **What reads the limit:** GRN save checks the *product-level* `tb_product.price_deviation_limit` against the ordered price (`good-received-note.deviation.ts:149`) — so an edit on the tree reaches the GRN only through this cascade or by re-saving the product |
| Set qty deviation tolerance | Edit any level → `qty_deviation_limit` | Same mechanics; enforced on GRN save via `tb_product.qty_deviation_limit` (received base qty vs ordered, over-receipt only) |
| Override tax profile | Edit any level → `tax_profile_id` / `tax_rate` | By default affects NEW products only — existing products keep their snapshotted setup. With the **cascade** choice the API (`cascade_tax: true`, default off) copies the saved node's `tax_profile_id` / name / rate onto every live descendant **and product** |
| Set the Inventory / Direct GL account | Edit any level → **Inventory account** / **Direct account** (account pickers; empty = inherit from the level above, shown as a placeholder) | Writes `tb_product_account_code_mapping` rows (`account_type` `inventory` / `direct`) via `account_codes: { add[], update[], remove[] }`. These are the defaults [chart-of-account-mapping](/en/inventory/master-data/chart-of-account-mapping) resolves (item group → sub-category → category). The list endpoints do not return `account_codes`; the dialog loads them from the single-record GET |
| Push edited values to descendants | Save an edit that changes deviation, either account, or the tax profile on a node that has children → **confirmation dialog** (`cascade-confirm-dialog.tsx`) | Two choices: *cascade* (overwrite descendants) or *self only*. The dialog lists exactly the changed values and the number of sub-categories / item groups affected. Choosing cascade sends `cascade_deviation` (only if a limit changed, and only the changed limit), `cascade_account_codes` (the changed types; an **emptied** account clears it on all descendants) and `cascade_tax`. Choosing self sends `cascade_deviation: false` and nothing else. A separate confirmation also appears when `is_used_in_recipe` / `is_sold_directly` changed |
| Print / export the category tree | **Print** / **Export** buttons → range dialog (Category / Sub Category / Item Group *from–to* codes, `ALL` = unbounded) | "Product Category Report": Print opens the report viewer, Export downloads a flat CSV from `/reports/export`; `REPORT_TEMPLATE_UNAVAILABLE` means the template is not installed or disabled for the BU |
| Toggle `is_used_in_recipe` / `is_sold_directly` | Flag fields on any level | Used by recipe builder and POS pickers |
| Inactivate a leaf | Edit item group → `is_active = false` | Hides from new-product pickers; historical products still render |
| Soft-delete a level | **Delete** action | **Confirmed guards, one level down only:** category → `409 PRODUCT_CATEGORY_HAS_SUB_CATEGORY` while live sub-categories exist; sub-category → `PRODUCT_SUB_CATEGORY_HAS_ITEM_GROUP`; item group → `PRODUCT_ITEM_GROUP_HAS_PRODUCTS` while live products reference it (`product-category.service.ts`, `product-sub-category.service.ts`, `product-item-group.service.ts` `delete()`) |

## 3. Validation & Errors

| Symptom / Message | Cause | Action |
|---|---|---|
| `409 PRODUCT_SUB_CATEGORY_ALREADY_EXISTS` / `PRODUCT_ITEM_GROUP_ALREADY_EXISTS` / "Code already exists" | **Changed 2026-09 (`57b34748d`):** sub-category and item-group `code`s (and product codes) must be unique **across the business unit**, case-insensitive — not merely within the parent — on create-with-code and on a code change. Name must be unique within the parent. Category `code` unique among non-deleted rows | Server-side rule, still enforced — but since the UI no longer accepts a typed code (corrected this pass), this error path is now reachable only via bulk import or direct API, not the interactive Add-Category dialog |
| "Cannot delete — products still reference this" (`PRODUCT_ITEM_GROUP_HAS_PRODUCTS`) / "has sub-categories" / "has item groups" | Live children one level below | Reassign or delete the children first, then retry |
| "Cannot re-parent sub-category" | FK on `product_subcategory_id` is `NoAction`; products reference its item groups | Manual data migration required — not a UI action |
| Tax change not reflected on existing products | Tax profile snapshot at product save | Re-save the product, or choose *cascade* in the confirmation dialog (`cascade_tax`) |
| `price_deviation_limit = 0` doesn't block 0% deviation | `0` means "no tolerance configured" — falls back to app default | Set a positive `%` to enforce a real cap |
| Hierarchy ambition vs schema | carmen/docs describes "up to 5 levels"; schema enforces 3 | Schema is source of truth — 3 fixed levels (Inferred) |

## 4. Edge Cases

- **3 FIXED levels, NOT self-referential.** Each level has its own table with FK pointing to the parent — there is **no recursive `parent_id` column**. Tooling that assumes a self-referential tree will not work.
- **Inheritance is `item_group ?? sub_category ?? category ?? app default`** — finest level wins, computed at product save.
- **Re-parenting blocked.** Once products reference an item group, the sub-category cannot be moved to a different category — FK `NoAction`.
- **Tax profile snapshot.** Changing `tax_profile_id` on a category affects only NEW products unless the user confirms the cascade (`cascade_tax`); then every descendant and product is overwritten, including ones with a deliberate local override.
- **Cascade is destructive and silent per row.** Overwrite replaces local overrides at lower levels; clearing an account at a node soft-deletes the same-type mapping row on every descendant (`cascadeAccountCodes`). There is no per-row diff or undo, and the whole cascade runs in one transaction (`timeout: 30000`), so a very large tree can fail as a unit.
- **Account defaults skip the product.** The mapping resolver reads item group → sub-category → category only; a product-level `tb_product_account_code_mapping` row exists in the table but is **not** consulted by account mapping.
- **Code scoping.** The DB indexes are composite (`(code, name, deleted_at)`), but since 2026-09 the service also enforces **BU-wide** uniqueness of sub-category, item-group and product `code` (case-insensitive) — because a child's auto-generated code is `<parent code><running number>`, two parents sharing a code used to hand out the same child code. The next-code sequence is now read from every live code with the same prefix under a per-prefix advisory lock (`generateSubCategoryCode`, `generateItemGroupCode`, `generateProductCode`).
- **`0` deviation tolerance.** Means "not configured" — `checkPriceDeviation` / `checkQtyDeviation` return early when the product's limit is `≤ 0`, so no check runs.
- **Tree rows come back as nested objects (2026-09-17).** Sub-category rows carry `product_category: { id, name }` and every level carries `tax_profile: { id, name }` instead of flat `*_id` / `*_name` pairs (frontend fix `f8d4026c`); default list sort is `code:asc` at all three levels (`withDefaultSort`, 2026-09-13).

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

### 5.1a Account defaults on the tree

Each level can own up to two live rows in `tb_product_account_code_mapping` (one per `account_type` in `inventory`, `direct`; unique per owner column + type + `deleted_at`). Owner columns: `product_category_id`, `product_sub_category_id`, `product_item_group_id` (and `product_id`, unused by account mapping). See [01-data-model](/en/inventory/product/01-data-model) § 2.11.

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

- [product](/en/inventory/product) — every product carries a `(category, sub_category, item_group)` triple
- [product/03-user-flow-product-admin](/en/inventory/product/03-user-flow-product-admin) — Product Admin maintains the tree
- [purchase-request](/en/inventory/purchase-request) &nbsp;·&nbsp; [purchase-order](/en/inventory/purchase-order) (`price_deviation_limit`) &nbsp;·&nbsp; [good-receive-note](/en/inventory/good-receive-note) (`qty_deviation_limit`)
- [recipe](/en/inventory/recipe) — `is_used_in_recipe` filter
- [access-control/permission](/en/inventory/access-control/permission) — category-scoped filters for Purchaser / Store Keeper
- [master-data/tax-profile](/en/inventory/master-data/tax-profile) — `tax_profile_id` cascade
- [master-data/chart-of-account-mapping](/en/inventory/master-data/chart-of-account-mapping) — consumes the Inventory / Direct account defaults set here

## 8. References

- **Prisma:** `../carmen-turborepo-backend/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_product_category` (line ~1801), `tb_product_sub_category` (~1952), `tb_product_item_group` (~1876), `tb_product_category_comment` (~1841).
- **Backend:** `../carmen-turborepo-backend/apps/micro-business/src/master/product-category/`, `product-sub-category/`, `product-item-group/` (delete guards; `update()` cascade blocks for deviation / tax / account codes), `common/account-code/account-code-cascade.helper.ts`; deviation consumer `apps/micro-business/src/inventory/good-received-note/good-received-note.deviation.ts`.
- **Frontend:** `../carmen-frontend/routes/product-management/category/` (`category-form-schema.ts`, `cascade-changes.ts`, `cascade-confirm-dialog.tsx`, `category-report-dialog.tsx`, `use-category-report.ts`, `use-node-account-codes.ts`, `use-category-tree.ts`).
- **E2E:** `../carmen-frontend-e2e/tests/101-product-category.spec.ts` (23 cases) + `docs/test-cases/gaps/101-product-category-gap.md` (39 uncovered cases).
- **carmen/docs:** `../carmen/docs/product-management/PROD-API-Endpoints-Categories.md`; `../carmen/docs/product-management/PROD-Overview.md`.
- **Module landing:** [product](/en/inventory/product) § 3 (Product Category key concept).

---
title: Recipe Category
description: Hierarchical category taxonomy for recipes — drives menu engineering, cost-band reporting, and recipe library navigation.
published: true
date: 2026-07-16T04:00:00.000Z
tags: recipe, category, taxonomy, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# Recipe Category

> **At a Glance**
> **Owner:** Chef / Product Admin &nbsp;·&nbsp; **Table:** `tb_recipe_category` &nbsp;·&nbsp; **Shape:** Hierarchical tree (self-FK on `parent_id`) &nbsp;·&nbsp; **Used by:** [recipe](/en/inventory/recipe) header, menu engineering, cost-band reports &nbsp;·&nbsp; **Seeds:** `default_cost_settings` + `default_margins` onto new recipes

![Recipe Category screen](/screenshots/recipe/category.png)

![Recipe Category detail screen](/screenshots/recipe/category-detail.png)

## 1. What & Who

Recipe Category is the **functional classification** over the recipe master, arranged as a tree (e.g. `Food > Main Course > Pasta`). Each category carries **default cost settings** and **default margins** that new recipes inherit at creation — so a property says "all Main Course recipes target 30% food-cost" once, not per recipe.

Distinct from [recipe/cuisine](/en/inventory/recipe/cuisine) (flat regional label) and `Course Type` (per-recipe enum). **Maintained by Chef** (or **Product Admin** in some tenants) under Operation Plan → Recipe Category.

## 2. Common Tasks

| Task | Where | Notes |
|---|---|---|
| Add a new sub-category | Operation Plan → Recipe Category → **+ Add** → pick **Parent Category** from a dropdown | List/grid is a flat `DataGrid` (`recipe-category-component.tsx`) — there is no tree widget; `level` is computed server-side from the chosen parent's `level + 1` |
| Reparent a category | Edit form → change the **Parent Category** dropdown | Recomputes `level` for the edited row only (`recipe-category.service.ts` `update()`); descendants' `level` is not touched |
| Edit target food-cost % for a category | Edit page (`/operation-plan/category/:id`) → **Default Cost Settings** | Affects *new* recipes only — does NOT update existing (no code path reads category defaults back into an existing `tb_recipe` row) |
| Retire a category | Edit page → set `is_active = false` | Keeps historical recipes readable; hides from picker |
| Hard-delete a category | Not allowed if it has children or recipes | Use soft-delete + inactive instead |

## 3. Validation & Errors

| Symptom / Message | Cause | Action |
|---|---|---|
| "Recipe category code already exists" (`RECIPE_CATEGORY_CODE_ALREADY_EXISTS`) | `code` collides tenant-wide, case-insensitive, among non-deleted rows (`recipe-category.service.ts`) | Pick a unique code |
| "Cannot delete: category has children" (`RECIPE_CATEGORY_HAS_SUBCATEGORIES`) | Application-level count of non-deleted `parent_id` children before delete | Reparent or soft-delete children first |
| "Cannot delete: recipes still reference this category" (`RECIPE_CATEGORY_IN_USE`) | Application-level count of non-deleted `tb_recipe.category_id` references before delete | Reassign recipes, then retire |
| "Category cannot be its own parent" (`RECIPE_CATEGORY_CANNOT_BE_OWN_PARENT`) | Direct self-reference only (`parent_id === id`) | Choose a different parent — this is the only cycle check; a multi-level cycle (reparenting a category under its own grandchild) is **not** detected |
| "Parent category not found" (`RECIPE_CATEGORY_PARENT_NOT_FOUND`) | `parent_id` does not resolve to a non-soft-deleted row | Pick an existing parent — the check does **not** require the parent to be `is_active = true`, only non-deleted |

## 4. Edge Cases

- **No tree UI.** The list/detail screens are the same flat `DataGrid` + form pattern as every other config screen in this module; hierarchy is expressed only through the `parent_id` dropdown and the derived `level` number, not a visual tree.
- **Cycle detection is shallow.** Only direct self-parenting is rejected (`RECIPE_CATEGORY_CANNOT_BE_OWN_PARENT`). Reparenting a category under one of its own descendants is not checked anywhere in `recipe-category.service.ts` and would silently create a cycle.
- **Defaults propagation.** Updating `default_cost_settings` / `default_margins` does NOT retroactively touch existing recipes — they carry their own snapshot from create time (there is no fan-out job in `recipe-category.service.ts` or `recipe.service.ts`).
- **Reparenting does not cascade `level`.** Moving a category only recomputes that category's own `level`; any subcategories under it keep their old `level` value until each is individually re-saved.
- **Inactive categories** stay readable on historical recipes but are hidden from the recipe-create picker.
- **No DB unique constraint** on `name` or `code` — uniqueness is application-enforced (case-insensitive on `code` only; `name` has no uniqueness check at all, sibling or tenant-wide), so direct SQL inserts can bypass it.

---

## 5. Data Model (Dev)

Source: tenant schema.

### 5.1 `tb_recipe_category`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `code` | `String @db.VarChar` | No | Short code (e.g. `MAIN`, `BEV-HOT`). |
| `name` | `String @db.VarChar` | No | Display name. |
| `description`, `note` | `String? @db.VarChar` | Yes | Free text / internal note. |
| `is_active` | `Boolean?` | Yes | Active flag, defaults `true`. |
| `parent_id` | `String? @db.Uuid` | Yes | Self-FK to parent (null = root). |
| `level` | `Int` | No | Depth from root, defaults `1`. Materialised. |
| `default_cost_settings` | `Json @db.JsonB` | No | Target food-cost %, rounding, labor/overhead — seeds new recipes. |
| `default_margins` | `Json @db.JsonB` | No | Default gross-margin targets. |
| `info`, `dimension` | `Json?` | Yes | Standard metadata. |
| `doc_version` | `Int` | No | Optimistic-lock version. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** Self-relation `CategoryHierarchy` on `parent_id` with `onDelete: Restrict`. Reverse relation to `tb_recipe.category_id` (also `onDelete: Restrict`). No `@@unique` at schema level — uniqueness application-enforced.

## 6. Business Rules

- **Uniqueness (app).** Unique `code` tenant-wide, case-insensitive, among non-deleted rows. There is **no** `name` uniqueness check — same-named categories (siblings or unrelated) are permitted.
- **Reparenting.** Re-computes `level` for the moved row only (`parent.level + 1`); does not cascade to descendants. Cycle rejection only covers direct self-parenting, not deeper cycles.
- **Deletion guards.** Application-level counts (`RECIPE_CATEGORY_HAS_SUBCATEGORIES`, `RECIPE_CATEGORY_IN_USE`) block delete while children or recipes exist — not a database-level `Restrict` cascade failure.
- **Defaults seed at create only** — never retroactive on update.
- **Validation.** `code`, `name` required; `parent_id` (if set) must reference a non-soft-deleted category — `is_active` is not checked on the parent.

## 7. Cross-References

- [recipe](/en/inventory/recipe) — every recipe carries `category_id` (required); reads category defaults at create time.
- [recipe/cuisine](/en/inventory/recipe/cuisine) — sibling taxonomy on the regional axis.
- [recipe/01-data-model](/en/inventory/recipe/01-data-model) — full data-model context.
- [recipe/03-user-flow-chef](/en/inventory/recipe/03-user-flow-chef), [recipe/03-user-flow-cost-controller](/en/inventory/recipe/03-user-flow-cost-controller) — Chef picks; Cost Controller sets category defaults.

## 8. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_recipe_category` (lines ~5314-5350).
- **Frontend route:** `../carmen-inventory-frontend-react/routes/operation-plan/category/`.
- **Concept docs:** `../carmen/docs/recipe/setup-pages-spec.md`.

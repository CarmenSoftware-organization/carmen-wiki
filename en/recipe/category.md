---
title: Recipe Category
description: Hierarchical category taxonomy for recipes — drives menu engineering, cost-band reporting, and recipe library navigation.
published: true
date: 2026-05-17T07:00:16.000Z
tags: recipe, category, taxonomy, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# Recipe Category

> **At a Glance**
> **Owner:** Chef / Product Admin &nbsp;·&nbsp; **Table:** `tb_recipe_category` &nbsp;·&nbsp; **Shape:** Hierarchical tree (self-FK on `parent_id`) &nbsp;·&nbsp; **Used by:** [[recipe]] header, menu engineering, cost-band reports &nbsp;·&nbsp; **Seeds:** `default_cost_settings` + `default_margins` onto new recipes

![Recipe Category screen](/assets/screenshots/recipe/category.png)

## 1. What & Who

Recipe Category is the **functional classification** over the recipe master, arranged as a tree (e.g. `Food > Main Course > Pasta`). Each category carries **default cost settings** and **default margins** that new recipes inherit at creation — so a property says "all Main Course recipes target 30% food-cost" once, not per recipe.

Distinct from [[recipe/cuisine]] (flat regional label) and `Course Type` (per-recipe enum). **Maintained by Chef** (or **Product Admin** in some tenants) under Operation Plan → Recipe Category.

## 2. Common Tasks

| Task | Where | Notes |
|---|---|---|
| Add a new sub-category | Operation Plan → Recipe Category → tree → **+ Child** | Inherits parent's defaults; can override |
| Reparent a sub-category | Drag node onto new parent in tree view | Recomputes `level` for moved node + all descendants |
| Edit target food-cost % for a category | Edit dialog → **Default Cost Settings** | Affects *new* recipes only — does NOT update existing |
| Retire a category | Edit dialog → set `is_active = false` | Keeps historical recipes readable; hides from picker |
| Hard-delete a category | Not allowed if it has children or recipes | Use soft-delete + inactive instead |

## 3. Validation & Errors

| Symptom / Message | Cause | Action |
|---|---|---|
| "Code already in use" | `code` collides tenant-wide (app-enforced) | Pick a unique code |
| "Name already exists under this parent" | Sibling-name collision (app-enforced) | Rename or pick a different parent |
| "Cannot delete: category has children" | `parent_id` FK `onDelete: Restrict` | Reparent or soft-delete children first |
| "Cannot delete: recipes still reference this category" | `tb_recipe.category_id` FK `onDelete: Restrict` | Reassign recipes, then retire |
| "Cycle detected on reparent" | Move would make node its own ancestor | Choose a different parent |
| "Parent must be active" | `parent_id` references deleted/inactive row | Pick an active parent |

## 4. Edge Cases

- **Hierarchy depth.** No DB cap, but UI typically caps at 3 levels (root → group → leaf) for menu-engineering legibility. `level` is materialised on insert/move.
- **Defaults propagation.** Updating `default_cost_settings` / `default_margins` does NOT retroactively touch existing recipes — they carry their own snapshot from create time.
- **Inactive categories** stay readable on historical recipes but are hidden from the recipe-create picker.
- **No DB unique constraint** on `name` or `code` — uniqueness is application-enforced, so direct SQL inserts can bypass it.

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

- **Uniqueness (app).** Unique `name` per parent (siblings cannot collide); unique `code` tenant-wide.
- **Reparenting.** Re-computes `level` for moved node + descendants; cycle detection rejects self-ancestor moves.
- **Deletion guards.** Both self-FK and `tb_recipe.category_id` use `onDelete: Restrict` — hard-delete blocked while children or recipes exist.
- **Defaults seed at create only** — never retroactive on update.
- **Validation.** `code`, `name` required; `level >= 1`; `parent_id` (if set) must reference a non-deleted active category.

## 7. Cross-References

- [[recipe]] — every recipe carries `category_id` (required); reads category defaults at create time.
- [[recipe/cuisine]] — sibling taxonomy on the regional axis.
- [[recipe/01-data-model]] — full data-model context.
- [[recipe/03-user-flow-chef]], [[recipe/03-user-flow-cost-controller]] — Chef picks; Cost Controller sets category defaults.

## 8. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_recipe_category` (lines ~5314-5350).
- **Frontend route:** `../carmen-inventory-frontend/app/(root)/operation-plan/category/`.
- **Concept docs:** `../carmen/docs/recipe/setup-pages-spec.md`.

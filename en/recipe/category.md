---
title: Recipe Category
description: Hierarchical category taxonomy for recipes — drives menu engineering, cost-band reporting, and recipe library navigation.
published: true
date: 2026-05-16T17:00:00.000Z
tags: recipe, category, taxonomy, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# Recipe Category

## 1. Purpose

Recipe Category is the classification layer over the recipe master. Categories are arranged as a tree (e.g. `Food > Main Course > Pasta`, `Beverage > Hot > Coffee`) and assigned per recipe to drive menu engineering, cost-band reporting, allergen/dietary filtering, and the operation-plan navigation in the F&B app. Each category can carry **default cost settings** and **default margins** that new recipes in the category inherit at creation time — this is how a property says "all Main Course recipes target a 30% food-cost percentage by default" once instead of per-recipe.

Distinct from [[recipe/cuisine]] (which is a flat regional/style label such as `Thai`, `Italian`) and from `Course Type` (which is a per-recipe enum). Category is *functional* — what kind of dish it is and how it sits in the menu structure.

## 2. Prisma Model(s)

Source: tenant schema.

### 2.1 `tb_recipe_category`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `code` | `String @db.VarChar` | No | Short code (e.g. `MAIN`, `BEV-HOT`). |
| `name` | `String @db.VarChar` | No | Display name (e.g. `Main Course`, `Hot Beverage`). |
| `description` | `String? @db.VarChar` | Yes | Free text. |
| `note` | `String? @db.VarChar` | Yes | Internal note. |
| `is_active` | `Boolean?` | Yes | Active flag, defaults `true`. |
| `parent_id` | `String? @db.Uuid` | Yes | Self-FK to parent category (null = root). |
| `level` | `Int` | No | Depth from root, defaults `1`. Materialised for fast tree queries. |
| `default_cost_settings` | `Json @db.JsonB` | No | Defaults inherited by new recipes (target food-cost %, rounding, labor/overhead). |
| `default_margins` | `Json @db.JsonB` | No | Default gross-margin targets per category. |
| `info`, `dimension` | `Json?` | Yes | Standard metadata. |
| `doc_version` | `Int` | No | Optimistic-lock version. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** Self-relation `CategoryHierarchy` on `parent_id` with `onDelete: Restrict` — a category that has children cannot be deleted. Reverse relation `tb_recipe_category_subcategories` exposes the tree. Reverse relation to `tb_recipe.category_id` (also `onDelete: Restrict`). No `@@unique` on `name` or `code` at schema level — uniqueness is application-enforced (see Section 5).

## 3. Usage / Cross-References

- [[recipe]] — every recipe carries `category_id` (required). The category's `default_cost_settings` and `default_margins` are read at recipe-create time and copied onto the recipe header.
- [[recipe/01-data-model]] — full data-model context including how category interacts with cuisine, course type, and the costing roll-up.
- [[recipe/03-user-flow-chef]] — Chef picks a category when composing a recipe; the recipe library is browsable by category tree.
- [[recipe/03-user-flow-cost-controller]] — Cost Controller sets category-level target food-cost % which becomes the per-recipe default.

## 4. Configuration UI

Managed by **Chef** (or **Product Admin** in some tenants) under Operation Plan → Recipe Category. The screen shows a tree view of categories with drag-to-reparent, plus an edit dialog (code, name, description, active flag, parent picker, default cost settings, default margins). New child categories inherit the parent's defaults as a starting point but can override.

## 5. Business Rules

- **Uniqueness.** No DB `@@unique` constraint; application enforces unique `name` per parent (siblings cannot collide) and unique `code` tenant-wide. Renaming requires both checks.
- **Hierarchy depth.** No hard limit in the schema, but UI typically caps at 3 levels (root → group → leaf) for menu-engineering reports to stay legible. `level` must be maintained on insert/move.
- **Reparenting.** Moving a subtree under a new parent re-computes `level` for the moved node and all descendants. Cycle detection rejects a move that would make a node its own ancestor.
- **Deletion guards.** `onDelete: Restrict` on both the self-FK and `tb_recipe.category_id` means a category cannot be hard-deleted if it has subcategories or referenced recipes. Use soft-delete (`deleted_at`) plus `is_active=false` to retire.
- **Defaults propagation.** Updating `default_cost_settings` or `default_margins` on a category does **not** retroactively change existing recipes; it only seeds *new* recipes created after the change. Existing recipes carry their own snapshot.
- **Validation.** `code` and `name` required; `level >= 1`; `parent_id` (if set) must reference a non-deleted active category.
- **Lifecycle.** Inactive categories stay readable on historical recipes but are hidden from the picker.

## 6. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_recipe_category` (lines ~5314-5350).
- **Frontend route:** `../carmen-inventory-frontend/app/(root)/operation-plan/category/`.
- **Concept docs:** `../carmen/docs/recipe/setup-pages-spec.md`.
- **Cross-module:** see Section 3.

---
title: Equipment Category
description: Functional grouping for kitchen equipment — preparation, cooking, holding, refrigeration, dispense, cleaning, etc.
published: true
date: 2026-05-16T17:00:00.000Z
tags: recipe, equipment, taxonomy, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# Equipment Category

## 1. Purpose

Equipment Category groups kitchen equipment by function — typical values are `Preparation` (knives, mandolins, mixers), `Cooking` (ranges, ovens, fryers, sous-vide), `Holding` (bain-marie, heat lamps), `Refrigeration` (walk-ins, blast chillers, prep fridges), `Dispense` (coffee, soda, beer), and `Cleaning` (dishwashers, sanitisers). The category drives filtering in the equipment picker, scopes maintenance dashboards, and feeds property-fit-out checklists ("does this kitchen have at least one piece in every category?").

This is a **flat** taxonomy — there is no `parent_id` on the equipment-category row, unlike [[recipe/category]] which is hierarchical. Equipment that needs sub-classification typically uses the equipment row's free-text `station` field instead.

## 2. Prisma Model(s)

Source: tenant schema.

### 2.1 `tb_recipe_equipment_category`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `name` | `String @db.VarChar` | No | Display name (e.g. `Cooking`, `Refrigeration`). |
| `description` | `String? @db.VarChar` | Yes | Free text. |
| `note` | `String? @db.VarChar` | Yes | Internal note. |
| `is_active` | `Boolean?` | Yes | Active flag, defaults `true`. |
| `info`, `dimension` | `Json?` | Yes | Standard metadata. |
| `doc_version` | `Int` | No | Optimistic-lock version. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** `@@unique([name, deleted_at])` map `recipe_equipment_category_name_u` — name unique among non-deleted rows. Index on `name`. Reverse relation `tb_recipe_equipment` exposes the children via `category_id` (with `onDelete: NoAction` on the equipment side — see [[recipe/equipment]] Section 5).

## 3. Usage / Cross-References

- [[recipe/equipment]] — every equipment row may carry `category_id` (nullable) plus a denormalised `category_name` for display. The cross-FK is `tb_recipe_equipment.category_id → tb_recipe_equipment_category.id`.
- [[recipe]] — indirect; recipes reference equipment via preparation steps, and equipment-category surfaces as a filter in the equipment picker.
- [[recipe/03-user-flow-chef]] — Chef uses the equipment-category filter when picking equipment for a preparation step.

## 4. Configuration UI

Managed by **Chef** (or **Product Admin**) under Operation Plan → Equipment Category. The screen is a flat list with an edit dialog (name, description, active flag). Most tenants seed the categories once during onboarding (`Preparation`, `Cooking`, `Holding`, `Refrigeration`, `Dispense`, `Cleaning`, `Smallwares`, `Other`) and rarely edit afterwards.

Note: the frontend also exposes a separate `/operation-plan/recipe-equipment-category/` route that historically rendered the same entity — the canonical route is `/operation-plan/equipment-category/`. Confirm which is wired to the production navigation when testing.

## 5. Business Rules

- **Uniqueness.** `name` is unique among non-deleted rows (DB-enforced via `@@unique`).
- **Flat structure.** No `parent_id` field; the table cannot represent a hierarchy. If sub-classification is needed, use the equipment row's `station` field or open a schema change.
- **Deletion guards.** Although the FK from `tb_recipe_equipment.category_id` uses `onDelete: NoAction` (i.e. the DB will *not* prevent deletion and will *not* cascade), the application layer should reject hard-delete of a category referenced by any equipment row to avoid dangling `category_name` strings. Soft-delete via `deleted_at` plus `is_active=false` is the supported retirement path.
- **Validation.** `name` required.
- **Rename propagation.** Renaming a category should refresh the denormalised `category_name` on every related `tb_recipe_equipment` row (application-level fan-out, since the FK is `onUpdate: NoAction`). Confirm this is wired in the equipment-category save handler before assuming auto-propagation.
- **Lifecycle.** Inactive categories stay readable on historical equipment rows but are hidden from the picker.

## 6. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_recipe_equipment_category` (lines ~5226-5247).
- **Frontend routes:** `../carmen-inventory-frontend/app/(root)/operation-plan/equipment-category/` (canonical) and `../carmen-inventory-frontend/app/(root)/operation-plan/recipe-equipment-category/` (legacy / parallel — verify wiring).
- **Concept docs:** `../carmen/docs/recipe/setup-pages-spec.md`.
- **Cross-module:** see Section 3.

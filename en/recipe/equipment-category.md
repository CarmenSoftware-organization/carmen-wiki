---
title: Equipment Category
description: Functional grouping for kitchen equipment — preparation, cooking, holding, refrigeration, dispense, cleaning, etc.
published: true
date: 2026-05-17T08:00:00.000Z
tags: recipe, equipment, taxonomy, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# Equipment Category

> **At a Glance**
> **Owner:** Chef / Product Admin &nbsp;·&nbsp; **Table:** `tb_recipe_equipment_category` &nbsp;·&nbsp; **Shape:** Flat (no `parent_id`) &nbsp;·&nbsp; **Children:** [[recipe/equipment]] via `category_id` &nbsp;·&nbsp; **Used by:** equipment picker filter, maintenance dashboard, fit-out checklists

## 1. What & Who

Equipment Category groups kitchen equipment by **function** — typical values are `Preparation`, `Cooking`, `Holding`, `Refrigeration`, `Dispense`, and `Cleaning`. Drives filtering in the equipment picker, scopes maintenance dashboards, and feeds property-fit-out checklists ("does this kitchen have at least one piece in every category?").

**Flat taxonomy** — no `parent_id`, unlike the hierarchical [[recipe/category]]. Sub-classification uses the equipment row's free-text `station` field. **Maintained by Chef** (or **Product Admin**) under Operation Plan → Equipment Category. Most tenants seed once at onboarding and rarely edit.

## 2. Common Tasks

| Task | Where | Notes |
|---|---|---|
| Seed initial categories | Operation Plan → Equipment Category → **+ New** | Typical seed: `Preparation`, `Cooking`, `Holding`, `Refrigeration`, `Dispense`, `Cleaning`, `Smallwares`, `Other` |
| Rename a category | Edit dialog → `name` | Triggers fan-out refresh of `category_name` on related equipment |
| Retire a category | Edit dialog → `is_active = false` | Hidden from picker; historical equipment unaffected |
| Hard-delete a category | App rejects if equipment references exist | Use soft-delete + inactive instead |
| Verify canonical route | `/operation-plan/equipment-category/` | Legacy `/recipe-equipment-category/` route may also exist — confirm wiring |

## 3. Validation & Errors

| Symptom / Message | Cause | Action |
|---|---|---|
| "Name already exists" | `@@unique([name, deleted_at])` violation | Pick a different name (or restore the deleted row) |
| "Name is required" | Blank required field | Fill before save |
| "Cannot delete: equipment references this category" | App-layer guard — DB FK is `NoAction` and won't block | Reassign or retire referenced equipment first |
| Equipment rows show stale `category_name` after rename | Fan-out handler not wired or skipped | Re-save the category, or re-save the equipment rows |
| Picker shows duplicate-looking entries | Two routes (`equipment-category` / `recipe-equipment-category`) wired in parallel | Confirm production navigation hits the canonical route |

## 4. Edge Cases

- **No hierarchy.** Schema has no `parent_id` — sub-classification must use `station` on the equipment row, or open a schema change.
- **FK is `onDelete: NoAction`** on the equipment side. The DB neither cascades nor blocks; the application must reject hard-delete to avoid dangling `category_name` strings.
- **Denormalised `category_name`** on equipment is application-maintained — confirm the rename fan-out is wired in the save handler before assuming auto-propagation.
- **Two frontend routes** historically render the same entity (`equipment-category` canonical vs. `recipe-equipment-category` legacy) — verify which is in the current build.

---

## 5. Data Model (Dev)

Source: tenant schema.

### 5.1 `tb_recipe_equipment_category`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `name` | `String @db.VarChar` | No | Display name (e.g. `Cooking`, `Refrigeration`). |
| `description`, `note` | `String? @db.VarChar` | Yes | Free text / internal note. |
| `is_active` | `Boolean?` | Yes | Active flag, defaults `true`. |
| `info`, `dimension` | `Json?` | Yes | Standard metadata. |
| `doc_version` | `Int` | No | Optimistic-lock version. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** `@@unique([name, deleted_at])` map `recipe_equipment_category_name_u`. Index on `name`. Reverse relation `tb_recipe_equipment` exposes children via `category_id` (`onDelete: NoAction` on the equipment side).

## 6. Business Rules

- **Uniqueness.** `name` unique among non-deleted rows (DB-enforced).
- **Flat structure.** No `parent_id` — cannot model a hierarchy. Use `station` on equipment or a schema change.
- **Deletion guards.** FK `onDelete: NoAction` — DB will not protect. Application must reject hard-delete while equipment references exist; soft-delete + inactive is the supported retirement.
- **Rename propagation.** Should refresh denormalised `category_name` on every related `tb_recipe_equipment` row via application fan-out (FK is `onUpdate: NoAction`).
- **Validation.** `name` required.
- **Lifecycle.** Inactive categories stay readable on historical equipment; hidden from picker.

## 7. Cross-References

- [[recipe/equipment]] — children via `category_id`; carries denormalised `category_name`.
- [[recipe]] — indirect; equipment-category surfaces as a filter in the equipment picker on preparation steps.
- [[recipe/03-user-flow-chef]] — Chef uses category filter when picking equipment.

## 8. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_recipe_equipment_category` (lines ~5226-5247).
- **Frontend routes:** `../carmen-inventory-frontend/app/(root)/operation-plan/equipment-category/` (canonical); `../carmen-inventory-frontend/app/(root)/operation-plan/recipe-equipment-category/` (legacy — verify wiring).
- **Concept docs:** `../carmen/docs/recipe/setup-pages-spec.md`.

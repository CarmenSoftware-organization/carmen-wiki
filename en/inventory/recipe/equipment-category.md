---
title: Equipment Category
description: Functional grouping for kitchen equipment — preparation, cooking, holding, refrigeration, dispense, cleaning, etc.
published: true
date: 2026-07-16T04:00:00.000Z
tags: recipe, equipment, taxonomy, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# Equipment Category

> **At a Glance**
> **Owner:** Chef / Product Admin &nbsp;·&nbsp; **Table:** `tb_recipe_equipment_category` &nbsp;·&nbsp; **Shape:** Flat (no `parent_id`) &nbsp;·&nbsp; **Children:** [recipe/equipment](/en/inventory/recipe/equipment) via `category_id` &nbsp;·&nbsp; **Used by:** equipment picker filter, maintenance dashboard, fit-out checklists

![Equipment Category screen](/screenshots/recipe/equipment-category.png)

## 1. What & Who

Equipment Category groups kitchen equipment by **function** — typical values are `Preparation`, `Cooking`, `Holding`, `Refrigeration`, `Dispense`, and `Cleaning`. Drives filtering in the equipment picker, scopes maintenance dashboards, and feeds property-fit-out checklists ("does this kitchen have at least one piece in every category?").

**Flat taxonomy** — no `parent_id`, unlike the hierarchical [recipe/category](/en/inventory/recipe/category). Sub-classification uses the equipment row's free-text `station` field. **Maintained by Chef** (or **Product Admin**) under Operation Plan → Equipment Category. Most tenants seed once at onboarding and rarely edit.

## 2. Common Tasks

| Task | Where | Notes |
|---|---|---|
| Seed initial categories | Operation Plan → Equipment Category → **+ New** | Typical seed: `Preparation`, `Cooking`, `Holding`, `Refrigeration`, `Dispense`, `Cleaning`, `Smallwares`, `Other` |
| Rename a category | Edit dialog → `name` | Refreshes `category_name` on an equipment row only when that row is next saved — there is no rename fan-out from the category side |
| Retire a category | Edit dialog → `is_active = false` | Hidden from picker; historical equipment unaffected |
| Hard-delete a category | App rejects if equipment references exist | Use soft-delete + inactive instead |
| Two frontend implementations exist for this same table | `/operation-plan/equipment-category` (in the Operation Plan nav menu, `constant/module-list.ts`) and `/operation-plan/recipe-equipment-category` (routed in `router.tsx` but **not** in the nav menu) both call the identical backend endpoint `/api/proxy/api/config/{buCode}/recipe-equipment-categories` (`API_ENDPOINTS.EQUIPMENT_CATEGORIES` and `API_ENDPOINTS.RECIPE_EQUIPMENT_CATEGORIES` resolve to the same URL) against separate component/type/hook trees (`equipment-category-component.tsx` + `types/equipment-category.ts` vs. `recipe-equipment-category-component.tsx` + `types/recipe-equipment-category.ts`) | The nav-linked screen is `equipment-category`; the only E2E coverage in this module family (`121-recipe-equipment-category.spec.ts`) exercises the non-nav-linked `/operation-plan/recipe-equipment-category` duplicate instead |

## 3. Validation & Errors

| Symptom / Message | Cause | Action |
|---|---|---|
| "Recipe equipment category already exists" (`RECIPE_EQUIPMENT_CATEGORY_ALREADY_EXISTS`) | `@@unique([name, deleted_at])` violation | Pick a different name (or restore the deleted row) |
| "Name is required" | Blank required field | Fill before save |
| "Cannot delete: equipment references this category" (`RECIPE_EQUIPMENT_CATEGORY_NOT_FOUND` / in-use guard) | App-layer guard — DB FK is `NoAction` and won't block | Reassign or retire referenced equipment first |
| Equipment rows show stale `category_name` after rename | There is no fan-out handler in `recipe-equipment-category.service.ts` at all — this is not a bug in a handler, the handler does not exist | Re-save each affected equipment row |
| Two visually-identical screens for the same data | Confirmed duplicate implementations (see §2) reading/writing the same `tb_recipe_equipment_category` table | Use the nav-linked `/operation-plan/equipment-category` screen; treat `/operation-plan/recipe-equipment-category` as a legacy duplicate pending consolidation |

## 4. Edge Cases

- **No hierarchy.** Schema has no `parent_id` — sub-classification must use `station` on the equipment row, or open a schema change.
- **FK is `onDelete: NoAction`** on the equipment side. The DB neither cascades nor blocks; the application must reject hard-delete to avoid dangling `category_name` strings.
- **Denormalised `category_name`** on equipment is refreshed only from the equipment side (see [recipe/equipment](/en/inventory/recipe/equipment)) — confirmed there is no rename-triggered fan-out anywhere in `recipe-equipment-category.service.ts`.
- **Two frontend routes render the same entity** — confirmed, not merely historical: `equipment-category` (nav-linked) and `recipe-equipment-category` (routed, not nav-linked, the one target of the module's only E2E spec) both read/write `tb_recipe_equipment_category` through the same underlying REST path.

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
- **Rename propagation.** Confirmed **not implemented** — `recipe-equipment-category.service.ts` has no code that touches `tb_recipe_equipment.category_name` on rename; the denormalised string only refreshes when the equipment row itself is next saved.
- **Validation.** `name` required.
- **Lifecycle.** Inactive categories stay readable on historical equipment; hidden from picker.
- **Duplicate frontend.** This table is served by two independent frontend feature directories (`operation-plan/equipment-category/` and `operation-plan/recipe-equipment-category/`) — see §2.

## 7. Cross-References

- [recipe/equipment](/en/inventory/recipe/equipment) — children via `category_id`; carries denormalised `category_name`.
- [recipe](/en/inventory/recipe) — indirect; equipment-category surfaces as a filter in the equipment picker on preparation steps.
- [recipe/03-user-flow-chef](/en/inventory/recipe/03-user-flow-chef) — Chef uses category filter when picking equipment.

## 8. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_recipe_equipment_category` (lines ~5226-5247).
- **Frontend routes:** `../carmen-inventory-frontend-react/routes/operation-plan/equipment-category/` (nav-linked, `constant/module-list.ts`); `../carmen-inventory-frontend-react/routes/operation-plan/recipe-equipment-category/` (routed in `router.tsx`, not nav-linked — confirmed same REST endpoint via `constant/api-endpoints.ts`).
- **E2E:** `../carmen-inventory-frontend-e2e/tests/121-recipe-equipment-category.spec.ts` — the module's only E2E spec; targets `/operation-plan/recipe-equipment-category` (the non-nav-linked duplicate), admin-only smoke + CRUD.
- **Concept docs:** `../carmen/docs/recipe/setup-pages-spec.md`.

---
title: Equipment
description: Kitchen equipment master — referenced from recipe preparation steps that require specific tools (sous-vide bath, deep fryer, smoker, etc.).
published: true
date: 2026-07-16T04:00:00.000Z
tags: recipe, equipment, master-data, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# Equipment

> **At a Glance**
> **Owner:** Chef / Product Admin &nbsp;·&nbsp; **Table:** `tb_recipe_equipment` &nbsp;·&nbsp; **Parent:** [recipe/equipment-category](/en/inventory/recipe/equipment-category) via `category_id` &nbsp;·&nbsp; **Used by:** [recipe](/en/inventory/recipe) preparation steps, fit-out checklists, maintenance dashboard &nbsp;·&nbsp; **Tracks:** specs, station, qty, usage, maintenance dates

![Equipment screen](/screenshots/recipe/equipment.png)

![Equipment detail screen](/screenshots/recipe/equipment-detail.png)

## 1. What & Who

Equipment is the master of kitchen tools and appliances — from hand tools (whisks, mandolins) through large appliances (combi-ovens, blast chillers, sous-vide) to portable mise-en-place gear. Each row carries **identification** (`code`, `name`, `brand`, `model`, `serial_no`), **specs** (capacity, power), **operational text** (operation / safety / cleaning), **maintenance schedule + dates**, **station assignment**, and **quantity counters** (`total_qty`, `available_qty`).

Recipe **preparation steps** reference equipment so the kitchen workflow planner can confirm an outlet has the required tools before adopting a recipe. Usage tracking (`usage_count`, `average_usage_time`) feeds maintenance scheduling. **Maintained by Chef** (or **Product Admin**) under Operation Plan → Equipment.

## 2. Common Tasks

| Task | Where | Notes |
|---|---|---|
| Add a new piece of equipment | Operation Plan → Equipment → **+ New** | Pick `category_id`, fill code + name (required) |
| Update maintenance dates after service | Detail page → Maintenance section | Plain date fields; no overdue indicator was found in source |
| Mark equipment portable | Detail page → `is_portable` | Indicates it can move between stations |
| Adjust on-property count | Detail page → `total_qty` / `available_qty` | Both are plain integer fields the user edits directly — no checkout flow decrements `available_qty` automatically |
| Retire equipment | Edit → `is_active = false` (soft-delete) | Stays referenceable on historical recipes; hidden from picker |
| Attach manuals or photos | Detail page → `attachments` / `manuals_urls` | JSON arrays of file links |

## 3. Validation & Errors

| Symptom / Message | Cause | Action |
|---|---|---|
| "Code + name already in use" | `@@unique([code, name, deleted_at])` violation | Pick a unique pair |
| "Code is required" / "Name is required" | Blank required field | Fill before save |
| Category dropdown empty | No active rows in [recipe/equipment-category](/en/inventory/recipe/equipment-category) | Seed categories first |
| Category renamed but old `category_name` still shown | `category_name` is only refreshed when the **equipment** row itself is saved (`recipe-equipment.service.ts` looks up the category name at that moment) — there is no fan-out from the category side | Re-save each affected equipment row after renaming the category |

**Not enforced today (checked `recipe-equipment.service.ts` and the gateway zod DTOs — no such rule exists in either):** `available_qty <= total_qty` and `next_maintenance_date >= last_maintenance_date` are not validated anywhere; both fields accept any integer / date independently.

## 4. Edge Cases

- **Category FK is `onDelete: NoAction`.** The DB will not cascade or block — application layer must reject category delete while equipment references exist (see [recipe/equipment-category](/en/inventory/recipe/equipment-category)).
- **`category_name` is denormalised** for display and refreshed only on the equipment row's own save. Treat the FK (`category_id`) as source of truth; the string is a cache with no rename fan-out from the category side.
- **Checkout flow not implemented** — `available_qty` / `total_qty` are schema-supported but no consuming UI or cross-field validation is wired today; nothing prevents `available_qty` exceeding `total_qty`.
- **Equipment on preparation steps is denormalised** onto `tb_recipe_preparation_step.equipment` payload, not a join table (see [recipe/01-data-model](/en/inventory/recipe/01-data-model)). Note the current recipe create/edit screen (`recipe-form.tsx`) has no UI that reads or writes preparation steps at all, so this equipment-on-step linkage is not currently reachable from the recipe form.
- **No "overdue" badge found.** `last_maintenance_date` / `next_maintenance_date` are plain date fields on the equipment form; no overdue-comparison logic was found in the frontend components or backend service — this callout should be treated as aspirational until a maintenance-status indicator is located in source.

---

## 5. Data Model (Dev)

Source: tenant schema.

### 5.1 `tb_recipe_equipment`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `code` | `String @db.VarChar` | No | Short code (e.g. `OVEN-COMBI-01`). |
| `name` | `String @db.VarChar` | No | Display name. |
| `description` | `String? @db.VarChar` | Yes | Free text. |
| `category_id` | `String? @db.Uuid` | Yes | FK to `tb_recipe_equipment_category`. |
| `category_name` | `String? @db.VarChar` | Yes | Denormalised display copy. |
| `brand`, `model`, `serial_no` | `String? @db.VarChar` | Yes | Physical identification. |
| `capacity`, `power_rating` | `String? @db.VarChar` | Yes | Free-text specs. |
| `station` | `String? @db.VarChar` | Yes | Kitchen station assignment. |
| `operation_instructions`, `safety_notes`, `cleaning_instructions` | `String? @db.VarChar` | Yes | Operational references. |
| `maintenance_schedule` | `String? @db.VarChar` | Yes | Cadence text. |
| `last_maintenance_date`, `next_maintenance_date` | `DateTime? @db.Timestamptz(6)` | Yes | Maintenance dates. |
| `is_active`, `is_portable` | `Boolean?` | Yes | Lifecycle flags. |
| `available_qty`, `total_qty`, `usage_count` | `Int?` | Yes | Counters. |
| `average_usage_time` | `Decimal? @db.Decimal(20, 5)` | Yes | Average minutes per use. |
| `attachments`, `manuals_urls` | `Json? @db.JsonB` | Yes | File links. |
| `note`, `info`, `dimension` | — | Yes | Standard metadata. |
| `doc_version` | `Int` | No | Optimistic-lock version. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** `@@unique([code, name, deleted_at])` map `recipe_equipment_code_name_u`. Indexes on `(code, name)` and `name`. FK `category_id → tb_recipe_equipment_category.id` `onDelete: NoAction, onUpdate: NoAction`.

## 6. Business Rules

- **Uniqueness.** `(code, name)` unique among non-deleted rows.
- **Category FK.** `NoAction` both ways — application must guard category delete while equipment refs exist.
- **Validation.** `code`, `name` required. No cross-field check between `available_qty` / `total_qty` or between the two maintenance dates was found in `recipe-equipment.service.ts` or the gateway zod DTOs — both pairs are independent, unvalidated integer/date fields.
- **Quantity semantics.** `total_qty` and `available_qty` are both plain manually-entered counters; no checkout flow reads or decrements either.
- **Lifecycle.** Inactive equipment readable on history; hidden from new-step picker (though the current recipe form has no step-adding UI at all — see [recipe/01-data-model](/en/inventory/recipe/01-data-model)).
- **`category_name`** is refreshed only when the equipment row itself is saved and its `category_id` is (re)resolved — there is no fan-out triggered from the category side.

## 7. Cross-References

- [recipe/equipment-category](/en/inventory/recipe/equipment-category) — parent taxonomy via `category_id`.
- [recipe](/en/inventory/recipe) — preparation steps reference equipment (denormalised onto the step).
- [recipe/01-data-model](/en/inventory/recipe/01-data-model) — integration point for equipment on steps.
- [recipe/03-user-flow-chef](/en/inventory/recipe/03-user-flow-chef), [recipe/03-user-flow-outlet-manager](/en/inventory/recipe/03-user-flow-outlet-manager) — Chef tags steps; Outlet Manager validates fit-out.

## 8. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_recipe_equipment` (lines ~5249-5312).
- **Frontend route:** `../carmen-inventory-frontend-react/routes/operation-plan/equipment/`.
- **Concept docs:** `../carmen/docs/recipe/setup-pages-spec.md`.

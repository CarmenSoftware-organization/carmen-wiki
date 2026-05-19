---
title: Equipment
description: Kitchen equipment master — referenced from recipe preparation steps that require specific tools (sous-vide bath, deep fryer, smoker, etc.).
published: true
date: 2026-05-19T23:55:00.000Z
tags: recipe, equipment, master-data, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# Equipment

> **At a Glance**
> **Owner:** Chef / Product Admin &nbsp;·&nbsp; **Table:** `tb_recipe_equipment` &nbsp;·&nbsp; **Parent:** [recipe/equipment-category](/en/inventory/recipe/equipment-category) via `category_id` &nbsp;·&nbsp; **Used by:** [recipe](/en/inventory/recipe) preparation steps, fit-out checklists, maintenance dashboard &nbsp;·&nbsp; **Tracks:** specs, station, qty, usage, maintenance dates

![Equipment screen](/screenshots/recipe/equipment.png)

## 1. What & Who

Equipment is the master of kitchen tools and appliances — from hand tools (whisks, mandolins) through large appliances (combi-ovens, blast chillers, sous-vide) to portable mise-en-place gear. Each row carries **identification** (`code`, `name`, `brand`, `model`, `serial_no`), **specs** (capacity, power), **operational text** (operation / safety / cleaning), **maintenance schedule + dates**, **station assignment**, and **quantity counters** (`total_qty`, `available_qty`).

Recipe **preparation steps** reference equipment so the kitchen workflow planner can confirm an outlet has the required tools before adopting a recipe. Usage tracking (`usage_count`, `average_usage_time`) feeds maintenance scheduling. **Maintained by Chef** (or **Product Admin**) under Operation Plan → Equipment.

## 2. Common Tasks

| Task | Where | Notes |
|---|---|---|
| Add a new piece of equipment | Operation Plan → Equipment → **+ New** | Pick `category_id`, fill code + name (required) |
| Update maintenance dates after service | Detail page → Maintenance section | Past `next_maintenance_date` surfaces "overdue" badge |
| Mark equipment portable | Detail page → `is_portable` | Indicates it can move between stations |
| Adjust on-property count | Detail page → `total_qty` | `available_qty` decrements on checkout (flow not yet wired) |
| Retire equipment | Edit → `is_active = false` (soft-delete) | Stays referenceable on historical recipes; hidden from picker |
| Attach manuals or photos | Detail page → `attachments` / `manuals_urls` | JSON arrays of file links |

## 3. Validation & Errors

| Symptom / Message | Cause | Action |
|---|---|---|
| "Code + name already in use" | `@@unique([code, name, deleted_at])` violation | Pick a unique pair |
| "Code is required" / "Name is required" | Blank required field | Fill before save |
| "available_qty cannot exceed total_qty" | App-enforced quantity rule | Adjust counters consistently |
| "Next maintenance must be ≥ last maintenance" | App-enforced when both dates set | Fix the dates |
| Category dropdown empty | No active rows in [recipe/equipment-category](/en/inventory/recipe/equipment-category) | Seed categories first |
| Category renamed but old `category_name` still shown | Denormalised display copy not refreshed | Save category to trigger fan-out (or re-save equipment) |

## 4. Edge Cases

- **Category FK is `onDelete: NoAction`.** The DB will not cascade or block — application layer must reject category delete while equipment references exist (see [recipe/equipment-category](/en/inventory/recipe/equipment-category)).
- **`category_name` is denormalised** for display. Treat the FK (`category_id`) as source of truth; the string is a cache.
- **Checkout flow not implemented** — `available_qty` is schema-supported but no UI wired today.
- **Equipment on preparation steps is denormalised** onto `tb_recipe_preparation_step.equipment` payload, not a join table (see [recipe/01-data-model](/en/inventory/recipe/01-data-model)).
- **Maintenance overdue badge** is purely visual; no automatic block on recipe usage.

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
- **Validation.** `code`, `name` required; `available_qty <= total_qty`; `next_maintenance_date >= last_maintenance_date` when both set.
- **Quantity semantics.** `total_qty` = on-property count; `available_qty` reserved for checkout flow.
- **Lifecycle.** Inactive equipment readable on history; hidden from new-step picker.
- **`category_name`** refreshed on category rename via application fan-out — FK is the truth.

## 7. Cross-References

- [recipe/equipment-category](/en/inventory/recipe/equipment-category) — parent taxonomy via `category_id`.
- [recipe](/en/inventory/recipe) — preparation steps reference equipment (denormalised onto the step).
- [recipe/01-data-model](/en/inventory/recipe/01-data-model) — integration point for equipment on steps.
- [recipe/03-user-flow-chef](/en/inventory/recipe/03-user-flow-chef), [recipe/03-user-flow-outlet-manager](/en/inventory/recipe/03-user-flow-outlet-manager) — Chef tags steps; Outlet Manager validates fit-out.

## 8. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_recipe_equipment` (lines ~5249-5312).
- **Frontend route:** `../carmen-inventory-frontend/app/(root)/operation-plan/equipment/`.
- **Concept docs:** `../carmen/docs/recipe/setup-pages-spec.md`.

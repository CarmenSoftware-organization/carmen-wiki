---
title: Equipment
description: Kitchen equipment master — referenced from recipe preparation steps that require specific tools (sous-vide bath, deep fryer, smoker, etc.).
published: true
date: 2026-05-16T17:00:00.000Z
tags: recipe, equipment, master-data, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# Equipment

## 1. Purpose

Equipment is the master of kitchen tools and appliances — from hand tools (whisks, mandolins) to large appliances (combi-ovens, blast chillers, sous-vide circulators) to portable mise-en-place gear. Each row carries identification (`code`, `name`, `brand`, `model`, `serial_no`), capacity and power specs, operating/cleaning/safety instructions, maintenance schedule, station assignment, and quantity counters (`total_qty`, `available_qty`).

Recipe **preparation steps** reference equipment so the kitchen workflow planner can check that a target outlet has the required tools before adding a recipe to its menu, and so the chef can size out fit-out for a new property by rolling up equipment demand across the recipe library. Usage tracking (`usage_count`, `average_usage_time`) feeds maintenance scheduling and tells F&B Ops which appliances are operationally critical.

## 2. Prisma Model(s)

Source: tenant schema.

### 2.1 `tb_recipe_equipment`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `code` | `String @db.VarChar` | No | Short code (e.g. `OVEN-COMBI-01`). |
| `name` | `String @db.VarChar` | No | Display name. |
| `description` | `String? @db.VarChar` | Yes | Free text. |
| `category_id` | `String? @db.Uuid` | Yes | FK to `tb_recipe_equipment_category`. |
| `category_name` | `String? @db.VarChar` | Yes | Denormalised display copy. |
| `brand`, `model`, `serial_no` | `String? @db.VarChar` | Yes | Physical identification. |
| `capacity`, `power_rating` | `String? @db.VarChar` | Yes | Operating specs (free text, e.g. `60L`, `5kW @ 230V`). |
| `station` | `String? @db.VarChar` | Yes | Kitchen station assignment (e.g. `Cold Section`, `Pastry`). |
| `operation_instructions`, `safety_notes`, `cleaning_instructions` | `String? @db.VarChar` | Yes | Operational references shown to kitchen staff. |
| `maintenance_schedule` | `String? @db.VarChar` | Yes | Cadence text (e.g. `Quarterly`). |
| `last_maintenance_date`, `next_maintenance_date` | `DateTime? @db.Timestamptz(6)` | Yes | Maintenance dates. |
| `is_active` | `Boolean?` | Yes | Active flag, defaults `true`. |
| `is_portable` | `Boolean?` | Yes | Portable / fixed flag, defaults `false`. |
| `available_qty`, `total_qty` | `Int?` | Yes | Counters (defaults `0`). |
| `usage_count` | `Int?` | Yes | Total times referenced by recipe execution (defaults `0`). |
| `average_usage_time` | `Decimal? @db.Decimal(20, 5)` | Yes | Average minutes per use. |
| `attachments`, `manuals_urls` | `Json? @db.JsonB` | Yes | File attachments and manual links. |
| `note`, `info`, `dimension` | — | Yes | Standard metadata. |
| `doc_version` | `Int` | No | Optimistic-lock version. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** `@@unique([code, name, deleted_at])` map `recipe_equipment_code_name_u` — `(code, name)` unique among non-deleted rows. Indexes on `(code, name)` and `name`. FK `category_id → tb_recipe_equipment_category.id` with `onDelete: NoAction, onUpdate: NoAction` (category can be edited without cascading to equipment rows).

## 3. Usage / Cross-References

- [[recipe/equipment-category]] — parent taxonomy. `category_id` FK on every equipment row.
- [[recipe]] — recipe preparation steps reference equipment (via the `tb_recipe_preparation_step.equipment` payload in the existing data model — equipment is denormalised onto the step rather than via a join table in the current schema, see [[recipe/01-data-model]] for the integration point).
- [[recipe/03-user-flow-chef]] — Chef tags preparation steps with required equipment when composing.
- [[recipe/03-user-flow-outlet-manager]] — Outlet Manager validates that the outlet has the equipment needed before adopting a recipe.

## 4. Configuration UI

Managed by **Chef** (or **Product Admin**) under Operation Plan → Equipment. The screen is a searchable list filtered by category and station, with a detail page covering basic info, physical specs, operating/safety/cleaning instructions, maintenance, quantity, and attachments. Larger properties use the maintenance dates to drive a maintenance-due dashboard. Equipment can be marked portable to indicate it can move between stations.

## 5. Business Rules

- **Uniqueness.** `(code, name)` is unique among non-deleted rows (DB-enforced).
- **Category FK.** `onDelete: NoAction` — deleting a category does **not** cascade. Application layer should block category delete while equipment references exist (see [[recipe/equipment-category]]).
- **Validation.** `code` and `name` required. `available_qty <= total_qty` (app-enforced).
- **Maintenance dates.** `next_maintenance_date` must be `>= last_maintenance_date` when both set. Past `next_maintenance_date` surfaces an "overdue maintenance" badge in lists and dashboards.
- **Quantity semantics.** `total_qty` is the on-property count; `available_qty` decrements when units are checked out (e.g. portable gear loaned to an event) — the schema supports it but checkout flow is not implemented in the current frontend.
- **Lifecycle.** Inactive equipment stays referenceable on historical recipes/steps but is hidden from the picker for new steps. Soft-delete is the path to retire.
- **Denormalised `category_name`.** Refreshed on category rename; treat the FK as the source of truth and the name as a display cache.

## 6. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_recipe_equipment` (lines ~5249-5312).
- **Frontend route:** `../carmen-inventory-frontend/app/(root)/operation-plan/equipment/`.
- **Concept docs:** `../carmen/docs/recipe/setup-pages-spec.md`.
- **Cross-module:** see Section 3.

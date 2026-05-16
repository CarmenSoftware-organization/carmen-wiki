---
title: Cuisine
description: Cuisine catalogue — regional / style label applied to recipes for menu segmentation (Thai, Italian, French, fusion, etc.).
published: true
date: 2026-05-16T17:00:00.000Z
tags: recipe, cuisine, taxonomy, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# Cuisine

## 1. Purpose

Cuisine is the flat catalogue labelling each recipe with its regional / cultural origin (`Thai`, `Italian`, `Japanese`, `French`, `Mexican`, etc.). Used downstream by the menu-engineering surface to filter recipes for property-specific outlets — a Thai-themed restaurant pulls only `Thai` and selected fusion entries from the central recipe library — and by the recipe library's search/filter UI.

Distinct from [[recipe/category]] which is *functional* (mealtype / dish-type) and *hierarchical*; cuisine is *geographical / cultural* and *flat* (no parent-child). Each cuisine is anchored to a high-level **region** (`ASIA`, `EUROPE`, `AMERICAS`, `AFRICA`, `MIDDLE_EAST`, `OCEANIA`) for region-level rollups in menu engineering. Cuisine rows also carry curated metadata (popular dishes, key ingredients) that the recipe library surfaces to help chefs explore an unfamiliar cuisine.

## 2. Prisma Model(s)

Source: tenant schema.

### 2.1 `tb_recipe_cuisines`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `name` | `String @db.VarChar` | No | Display name (e.g. `Thai`, `Northern Italian`). |
| `description` | `String? @db.VarChar` | Yes | Free text. |
| `note` | `String? @db.VarChar` | Yes | Internal note. |
| `is_active` | `Boolean?` | Yes | Active flag, defaults `true`. |
| `region` | `enum_cuisine_region` | No | Geographic region (`ASIA`, `EUROPE`, `AMERICAS`, `AFRICA`, `MIDDLE_EAST`, `OCEANIA`). |
| `popular_dishes` | `Json @db.JsonB` | No | Curated list of canonical dishes (defaults `[]`). |
| `key_ingredients` | `Json @db.JsonB` | No | Curated list of characteristic ingredients (defaults `[]`). |
| `info`, `dimension` | `Json?` | Yes | Standard metadata. |
| `doc_version` | `Int` | No | Optimistic-lock version. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** `@@unique([name, deleted_at])` map `recipe_cuisines_name_u` — name unique among non-deleted rows. Indexes on `region` and `name`. Reverse relation to `tb_recipe.cuisine_id` with `onDelete: Restrict`.

### 2.2 Enum `enum_cuisine_region`

Values: `ASIA`, `EUROPE`, `AMERICAS`, `AFRICA`, `MIDDLE_EAST`, `OCEANIA`. Recipes inherit region through their cuisine FK; there is no direct recipe-to-region link.

## 3. Usage / Cross-References

- [[recipe]] — every recipe carries `cuisine_id` (required, `onDelete: Restrict`). Cuisine is shown on the recipe header and drives library filtering.
- [[recipe/category]] — sibling taxonomy on a different (functional) axis. A recipe carries one of each.
- [[recipe/01-data-model]] — recipe header fields including the cuisine FK.
- [[recipe/03-user-flow-chef]] — Chef picks a cuisine when composing; the cuisine's `key_ingredients` may surface as suggestions.
- [[recipe/03-user-flow-procurement-fb-ops]] — F&B Ops uses cuisine + region rollups for menu engineering and outlet-fit decisions.

## 4. Configuration UI

Managed by **Chef** (or **Product Admin**) under Operation Plan → Cuisine. The screen is a flat list with an edit dialog for name, description, region (dropdown of the six enum values), active flag, popular-dishes tag editor, and key-ingredients tag editor. No tree view since cuisine is flat.

## 5. Business Rules

- **Uniqueness.** `name` is unique among non-deleted rows (DB-enforced via `@@unique`).
- **Region required.** Every cuisine must be anchored to one of the six `enum_cuisine_region` values — there is no `NULL`/`OTHER` fallback. New regions require a schema migration.
- **Deletion guards.** `onDelete: Restrict` on `tb_recipe.cuisine_id` blocks hard-delete of a cuisine referenced by any recipe. Soft-delete via `deleted_at` plus `is_active=false` to retire.
- **Validation.** `name` and `region` required. `popular_dishes` and `key_ingredients` are free-form string arrays (no FK validation against `tb_product` or `tb_recipe`).
- **Lifecycle.** Inactive cuisines stay readable on historical recipes but are hidden from the picker. No automatic carry-over of region changes — the region field is on the cuisine row only.
- **Rename propagation.** Renaming updates the master record only; recipes store the ID, so display refreshes automatically. The reverse-relation guarantee means cuisine retirement is always safe — historical recipes keep rendering.

## 6. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_recipe_cuisines` (lines ~5192-5224), enum `enum_cuisine_region` (lines ~5157-5164).
- **Frontend route:** `../carmen-inventory-frontend/app/(root)/operation-plan/cuisine/`.
- **Concept docs:** `../carmen/docs/recipe/setup-pages-spec.md`.
- **Cross-module:** see Section 3.

---
title: Cuisine
description: Cuisine catalogue — regional / style label applied to recipes for menu segmentation (Thai, Italian, French, fusion, etc.).
published: true
date: 2026-05-19T23:55:00.000Z
tags: recipe, cuisine, taxonomy, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# Cuisine

> **At a Glance**
> **Owner:** Chef / Product Admin &nbsp;·&nbsp; **Table:** `tb_recipe_cuisines` &nbsp;·&nbsp; **Shape:** Flat list, anchored to 6-value `region` enum &nbsp;·&nbsp; **Used by:** [recipe](/en/inventory/recipe) header, library filter, menu engineering &nbsp;·&nbsp; **Carries:** curated `popular_dishes` + `key_ingredients`

![Cuisine screen](/screenshots/recipe/cuisine.png)

## 1. What & Who

Cuisine is the **flat catalogue** labelling each recipe with its regional / cultural origin (`Thai`, `Italian`, `Japanese`, `French`, etc.). Drives the menu-engineering filter — a Thai-themed outlet pulls only `Thai` and selected fusion entries from the central library.

Distinct from [recipe/category](/en/inventory/recipe/category) which is *functional* and *hierarchical*; cuisine is *geographical* and *flat*. Each row is anchored to a high-level **region** (`ASIA`, `EUROPE`, `AMERICAS`, `AFRICA`, `MIDDLE_EAST`, `OCEANIA`) for region-level rollups. **Maintained by Chef** (or **Product Admin**) under Operation Plan → Cuisine.

## 2. Common Tasks

| Task | Where | Notes |
|---|---|---|
| Add a new cuisine | Operation Plan → Cuisine → **+ New** | Name + region (dropdown of 6) required |
| Curate popular dishes / key ingredients | Edit dialog → tag editors | Free-form strings; no FK validation to product/recipe |
| Rename a cuisine | Edit dialog → `name` | Recipes store the ID, so display refreshes automatically |
| Retire a cuisine | Edit dialog → `is_active = false` | Historical recipes keep rendering; hidden from picker |
| Move a cuisine to a different region | Edit dialog → `region` | Region lives on the cuisine row only — no cascade |

## 3. Validation & Errors

| Symptom / Message | Cause | Action |
|---|---|---|
| "Name already exists" | `@@unique([name, deleted_at])` violation | Pick a different name (or restore the deleted row) |
| "Region is required" | `region` left blank — no NULL fallback | Choose one of the 6 enum values |
| "Region value not allowed" | Tried to set an unknown region | New regions require a schema migration |
| "Cannot delete: recipes still reference this cuisine" | `tb_recipe.cuisine_id` FK `onDelete: Restrict` | Reassign recipes, then soft-delete |
| Recipe library shows blank cuisine on old recipe | Cuisine soft-deleted but row preserved | Reads still work — restore or reassign as needed |

## 4. Edge Cases

- **No `OTHER` region.** Every cuisine must map to one of the six enum values — adding a new region needs a Prisma migration.
- **Soft-delete preserves history.** Recipes referencing a retired cuisine still render correctly; only new pickers hide it.
- **`popular_dishes` / `key_ingredients`** are free-form arrays — not joined to `tb_product` or `tb_recipe`, so renames don't propagate.
- **Recipe region** is derived through the cuisine FK; there is no direct recipe-to-region link.

---

## 5. Data Model (Dev)

Source: tenant schema.

### 5.1 `tb_recipe_cuisines`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `name` | `String @db.VarChar` | No | Display name (e.g. `Thai`, `Northern Italian`). |
| `description`, `note` | `String? @db.VarChar` | Yes | Free text / internal note. |
| `is_active` | `Boolean?` | Yes | Active flag, defaults `true`. |
| `region` | `enum_cuisine_region` | No | `ASIA` / `EUROPE` / `AMERICAS` / `AFRICA` / `MIDDLE_EAST` / `OCEANIA`. |
| `popular_dishes` | `Json @db.JsonB` | No | Curated canonical dishes (defaults `[]`). |
| `key_ingredients` | `Json @db.JsonB` | No | Curated characteristic ingredients (defaults `[]`). |
| `info`, `dimension` | `Json?` | Yes | Standard metadata. |
| `doc_version` | `Int` | No | Optimistic-lock version. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** `@@unique([name, deleted_at])` map `recipe_cuisines_name_u`. Indexes on `region` and `name`. Reverse relation to `tb_recipe.cuisine_id` with `onDelete: Restrict`.

### 5.2 Enum `enum_cuisine_region`

Values: `ASIA`, `EUROPE`, `AMERICAS`, `AFRICA`, `MIDDLE_EAST`, `OCEANIA`.

## 6. Business Rules

- **Uniqueness.** `name` unique among non-deleted rows (DB-enforced).
- **Region required.** No `NULL` / `OTHER` fallback; new regions need a schema migration.
- **Deletion guards.** `onDelete: Restrict` on `tb_recipe.cuisine_id` blocks hard-delete of a referenced cuisine; use soft-delete + inactive.
- **Validation.** `name` and `region` required; `popular_dishes` / `key_ingredients` are free-form string arrays (no FK validation).
- **Rename propagation.** Recipes store the ID, so renames refresh automatically on display.

## 7. Cross-References

- [recipe](/en/inventory/recipe) — every recipe carries `cuisine_id` (required); shown on header and drives library filter.
- [recipe/category](/en/inventory/recipe/category) — sibling taxonomy on a different (functional) axis.
- [recipe/01-data-model](/en/inventory/recipe/01-data-model) — recipe header fields including the cuisine FK.
- [recipe/03-user-flow-chef](/en/inventory/recipe/03-user-flow-chef), [recipe/03-user-flow-procurement-fb-ops](/en/inventory/recipe/03-user-flow-procurement-fb-ops) — Chef picks; F&B Ops uses cuisine + region rollups.

## 8. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_recipe_cuisines` (lines ~5192-5224), enum `enum_cuisine_region` (lines ~5157-5164).
- **Frontend route:** `../carmen-inventory-frontend/app/(root)/operation-plan/cuisine/`.
- **Concept docs:** `../carmen/docs/recipe/setup-pages-spec.md`.

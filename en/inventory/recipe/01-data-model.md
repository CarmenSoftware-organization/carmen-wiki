---
title: Recipe — Data Model
description: Entities, fields, relationships, and enums for the recipe module.
published: true
date: 2026-05-17T11:00:00.000Z
tags: recipe, data-model, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T16:00:00.000Z
---

# Recipe — Data Model

> **At a Glance**
> **Tables:** `tb_recipe` &nbsp;·&nbsp; `tb_recipe_ingredient` &nbsp;·&nbsp; `tb_recipe_preparation_step` &nbsp;·&nbsp; `tb_recipe_yield_variant` &nbsp;·&nbsp; `tb_recipe_version` &nbsp;·&nbsp; `tb_recipe_pricing_history` &nbsp;·&nbsp; `tb_recipe_category` / `tb_recipe_cuisines` (masters)
> **Audience:** Developer / Auditor (dev reference)
> **Key FKs:** recipe `→ tb_recipe_category` / `tb_recipe_cuisines` (Restrict); ingredient `→ tb_product` (when type=product) **OR** `→ tb_recipe` self-ref via `sub_recipe_id` (when type=recipe); ingredient `→ tb_unit` ×2 (recipe + inventory UoM); variant / step / version / pricing-history all `→ tb_recipe` (Cascade)
> **Audit pattern:** standard `created_*` / `updated_*` / `deleted_*`; **no `tb_recipe_comment` and no workflow** — audit comes from `tb_recipe_version` snapshots + `tb_recipe_pricing_history`; 3-state lifecycle `DRAFT / PUBLISHED / ARCHIVED`

> **Source of truth:** Backend Prisma schema. Always read these first when writing or updating this page:
> - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma`
> - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma`
>
> The `generated/client/schema.prisma` files under each package are auto-generated copies and not authoritative.

## 1. Overview

The recipe module owns eight tenant-schema entities plus four module-specific enums. The core trio is the recipe header (`tb_recipe`), its ingredient lines (`tb_recipe_ingredient`), and its preparation steps (`tb_recipe_preparation_step`); two version-history tables capture change over time (`tb_recipe_version` — full snapshot, `tb_recipe_pricing_history` — cost / price snapshots); a yield-variant table (`tb_recipe_yield_variant`) supports recipes that produce multiple sellable sizes from one formula; and three master-data tables (`tb_recipe_category`, `tb_recipe_cuisines`, plus the equipment pair `tb_recipe_equipment_category` / `tb_recipe_equipment`) provide categorical taxonomies referenced by the header and the steps. The four enums (`enum_recipe_status`, `enum_recipe_difficulty`, `enum_ingredient_type`, `enum_temperature_unit`) are recipe-specific; the recipe module does **not** reuse the shared `enum_doc_status` because recipes do not flow through the standard document workflow — they have their own three-state lifecycle (`DRAFT / PUBLISHED / ARCHIVED`).

The recipe sits **upstream of [[inventory]] consumption and downstream of [[product]] catalog data**. Each ingredient line resolves to either a product (`tb_recipe_ingredient.product_id → tb_product`, when `ingredient_type = product`) or a sub-recipe (`sub_recipe_id → tb_recipe`, when `ingredient_type = recipe`); both paths are present on the same model with a single `enum_ingredient_type` discriminator. The ingredient line carries two unit references — `ingredient_unit_id` (the recipe-display UoM) and `inventory_unit_id` (the source's stock UoM) — plus a `conversion_factor` that bridges them; this lets a recipe say "200 g of flour" while inventory holds "1 kg bags" without ambiguity. Cost data is stored on the line (`cost_per_unit`, `wastage_percentage`, `net_cost`, `wastage_cost`) and rolls up onto the header (`total_ingredient_cost`, plus the labor / overhead / per-portion / pricing / margin columns); for sub-recipe ingredients the cost roll-up is recursive — when the sub-recipe's cost changes, every parent recipe's cost re-computes.

A noteworthy structural point: unlike most documents in the system, the recipe is **not** a workflow-driven document — there is no `workflow_id`, no `tb_recipe_comment` table, no `workflow_history` / `workflow_current_stage` columns. State change (`DRAFT → PUBLISHED → ARCHIVED`) is captured as a single enum on the header (`status`), plus two timestamp columns (`published_at`, `archived_at`); auditability comes from the dedicated `tb_recipe_version` table (full versioned snapshots of `recipe_data`, `ingredients_data`, `steps_data`, `variants_data` JSON blobs) and `tb_recipe_pricing_history` (cost / price snapshots with `change_reason` and `effective_date`). The carmen/docs PRD describes a hierarchical recipe / sub-recipe model, ingredient `type` enum, and a `Recipe → Menu Item` linkage; the actual Prisma schema has the recipe / sub-recipe link on `tb_recipe_ingredient.sub_recipe_id`, the discriminator on `enum_ingredient_type`, but **no `tb_menu_item` table** — menu-item linkage is application-layer or in a downstream POS-integration package not present in the tenant schema. See Section 5.

## 2. Entities

### 2.1 tb_recipe

Recipe header. Carries identity, classification, yield, timing, cost rollup, pricing, status, tags, allergens, and audit columns. One header has many ingredients, many steps, many yield variants, many versions, and many pricing-history rows.

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key, generated via `gen_random_uuid()`. |
| `code` | `String @db.VarChar` | No | Human-readable recipe code (e.g. `RCP-HSBURG-001`). Required. |
| `name` | `String @db.VarChar` | No | Recipe display name. Required. |
| `description` | `String? @db.VarChar` | Yes | Free-text description of the dish. |
| `note` | `String? @db.VarChar` | Yes | Internal note for kitchen / cost control. |
| `is_active` | `Boolean?` | Yes | Soft-active flag; default `true`. Distinct from `status`. |
| `images` | `Json? @default("[]") @db.JsonB` | Yes | Array of image refs (main + gallery); default `[]`. |
| `category_id` | `String @db.Uuid` | No | FK to `tb_recipe_category.id`. Required. Restrict-on-delete. |
| `cuisine_id` | `String @db.Uuid` | No | FK to `tb_recipe_cuisines.id`. Required. Restrict-on-delete. |
| `difficulty` | `enum_recipe_difficulty` | No | `EASY` / `MEDIUM` / `HARD`; default `MEDIUM`. |
| `base_yield` | `Decimal @db.Decimal(20, 5)` | No | Base output quantity per one execution of the recipe. |
| `base_yield_unit` | `String @db.VarChar` | No | Unit of `base_yield` (e.g. `portions`, `kg`, `pieces`). |
| `default_variant_id` | `String? @db.Uuid` | Yes | FK to `tb_recipe_yield_variant.id` (named relation `DefaultVariant`); points to the yield variant treated as the default for pricing / display. Nullable because a recipe may have no variants (single yield). |
| `prep_time` | `Int @default(0)` | No | Preparation time in minutes. |
| `cook_time` | `Int @default(0)` | No | Cooking time in minutes. Note: there is **no** persisted `total_time` column; the rollup is computed at display time as `prep_time + cook_time`. |
| `total_ingredient_cost` | `Decimal @default(0) @db.Decimal(20, 5)` | No | Σ of net ingredient line costs (after wastage). |
| `labor_cost` | `Decimal @default(0) @db.Decimal(20, 5)` | No | Recipe labor cost component, typically computed as `(prep_time + cook_time) × labor_rate × labor_cost_percentage`. |
| `overhead_cost` | `Decimal @default(0) @db.Decimal(20, 5)` | No | Recipe overhead cost component. |
| `cost_per_portion` | `Decimal @default(0) @db.Decimal(20, 5)` | No | `(total_ingredient_cost + labor_cost + overhead_cost) / base_yield` (or per-variant yield when a variant is in scope). |
| `suggested_price` | `Decimal? @db.Decimal(20, 5)` | Yes | System-computed price = `cost_per_portion / (1 − target_food_cost_percentage/100)`. |
| `selling_price` | `Decimal? @db.Decimal(20, 5)` | Yes | Actual chosen selling price (may differ from `suggested_price` for menu strategy). |
| `target_food_cost_percentage` | `Decimal? @default(33.00) @db.Decimal(20, 5)` | Yes | Target food-cost % (commonly 28–35); default 33. |
| `actual_food_cost_percentage` | `Decimal? @db.Decimal(20, 5)` | Yes | `cost_per_portion / selling_price × 100` when both are set. |
| `gross_margin` | `Decimal? @db.Decimal(20, 5)` | Yes | `selling_price − cost_per_portion` (absolute amount). |
| `gross_margin_percentage` | `Decimal? @db.Decimal(20, 5)` | Yes | `(selling_price − cost_per_portion) / selling_price × 100`. |
| `labor_cost_percentage` | `Decimal? @default(30.00) @db.Decimal(20, 5)` | Yes | Labor cost as % of total; default 30. |
| `overhead_percentage` | `Decimal? @default(20.00) @db.Decimal(20, 5)` | Yes | Overhead as % of total; default 20. |
| `carbon_footprint` | `Decimal? @default(0) @db.Decimal(20, 5)` | Yes | Per-portion CO₂-equivalent footprint (kg CO₂e); rolls up from ingredient footprints. |
| `deduct_from_stock` | `Boolean @default(true)` | No | Whether menu-sale fires recipe-explosion stock OUT. `false` for menu items priced flat (e.g. service charge "recipes") that should not trigger inventory deduction. |
| `status` | `enum_recipe_status @default(DRAFT)` | No | Lifecycle state; default `DRAFT`. |
| `tags` | `Json @default("[]") @db.JsonB` | No | Free-text tag array (e.g. `["vegan", "halal", "summer-menu"]`). |
| `allergens` | `Json @default("[]") @db.JsonB` | No | Allergen flag array (e.g. `["gluten", "dairy", "nuts"]`); rolled up to menu-item display for front-of-house. |
| `published_at` | `DateTime?` | Yes | Timestamp of `DRAFT → PUBLISHED` transition. |
| `archived_at` | `DateTime?` | Yes | Timestamp of `* → ARCHIVED` transition. |
| `created_at` | `DateTime? @default(now()) @db.Timestamptz(6)` | Yes | Creation timestamp. |
| `created_by_id` | `String? @db.Uuid` | Yes | Creator user id. |
| `updated_at` | `DateTime? @default(now()) @db.Timestamptz(6)` | Yes | Last-update timestamp. |
| `updated_by_id` | `String? @db.Uuid` | Yes | Last-updater user id. |
| `deleted_at` | `DateTime? @db.Timestamptz(6)` | Yes | Soft-delete timestamp. |
| `deleted_by_id` | `String? @db.Uuid` | Yes | Soft-delete actor id. |

**Constraints:** `@id` on `id`. FKs: `category_id → tb_recipe_category.id` (Restrict on delete), `cuisine_id → tb_recipe_cuisines.id` (Restrict), `default_variant_id → tb_recipe_yield_variant.id` (Restrict, named relation `DefaultVariant`). Back-relations: many `tb_recipe_ingredient` (as recipe), many `tb_recipe_ingredient` via `SubRecipeIngredients` (when used as a sub-recipe ingredient elsewhere), many `tb_recipe_preparation_step`, many `tb_recipe_yield_variant` (named relation `RecipeYieldVariants`), many `tb_recipe_version`, many `tb_recipe_pricing_history`.
**Indexes:** `@@unique([code, name, deleted_at])` as `recipe_code_name_u`; `@@index([code])` as `recipe_code_idx`; `@@index([name])` as `recipe_name_idx`; `@@index([code, name])` as `recipe_code_name_idx`. Note: there is **no** `@@unique([code, deleted_at])` — the unique key is the (code, name) pair, so two recipes can share a code if their names differ (uncommon but permitted).

### 2.2 tb_recipe_ingredient

Recipe ingredient line. Identifies what goes into the recipe (a product or another recipe), the quantity, the recipe and inventory units, the conversion factor between them, and the per-line cost components.

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `sequence_no` | `Int?` | Yes | Line ordering within the recipe; default `1`. |
| `name` | `String @db.VarChar` | No | Display name on the recipe (may differ from the product / sub-recipe name — e.g. "diced onion" pointing at the `Onion` product). |
| `note` | `String? @db.VarChar` | Yes | Free-text note on the line (e.g. "use fresh, not dried"). |
| `recipe_id` | `String @db.Uuid` | No | FK to `tb_recipe.id` (Cascade on delete — deleting the recipe deletes its lines). |
| `ingredient_type` | `enum_ingredient_type` | No | Discriminator: `product` (resolves to `product_id → tb_product`) or `recipe` (resolves to `sub_recipe_id → tb_recipe`). |
| `product_id` | `String? @db.Uuid` | Yes | FK to `tb_product.id` (Restrict on delete). Required when `ingredient_type = product`. |
| `sub_recipe_id` | `String? @db.Uuid` | Yes | FK to `tb_recipe.id` via named relation `SubRecipeIngredients` (Restrict on delete). Required when `ingredient_type = recipe`. Self-referential — a recipe can use another recipe as an ingredient (only `PUBLISHED` sub-recipes should be referenced; not enforced at schema level, see business rules). |
| `qty` | `Decimal @db.Decimal(20, 5)` | No | Quantity required in `ingredient_unit_id`. |
| `ingredient_unit_id` | `String @db.Uuid` | No | FK to `tb_unit.id` via named relation `recipe_ingredient_unit` (Restrict on delete). The recipe-display UoM. |
| `inventory_qty` | `Decimal? @db.Decimal(20, 5)` | Yes | Quantity expressed in the inventory UoM. Computed as `qty × conversion_factor` when the units differ. |
| `inventory_unit_id` | `String? @db.Uuid` | Yes | FK to `tb_unit.id` via named relation `recipe_inventory_unit` (Restrict on delete). The source's stock UoM. Nullable when recipe unit = inventory unit. |
| `conversion_factor` | `Decimal? @db.Decimal(20, 5)` | Yes | Multiplier from `ingredient_unit_id` to `inventory_unit_id` (e.g. `0.001` to go from grams to kilograms). |
| `cost_per_unit` | `Decimal @default(0) @db.Decimal(20, 5)` | No | Cost per `ingredient_unit_id` (or per `inventory_unit_id` if the conversion lands costing on stock-unit basis). Sourced from the product's current weighted-average or standard cost; for sub-recipes, sourced from the sub-recipe's `cost_per_portion`. |
| `wastage_percentage` | `Decimal @default(0) @db.Decimal(20, 5)` | No | Trim / peel / evaporation loss as %. Default 0. |
| `net_cost` | `Decimal @default(0) @db.Decimal(20, 5)` | No | `qty × cost_per_unit × (1 + wastage_percentage/100)`. The cost figure that rolls up to `tb_recipe.total_ingredient_cost`. |
| `wastage_cost` | `Decimal @default(0) @db.Decimal(20, 5)` | No | `qty × cost_per_unit × (wastage_percentage/100)`. The component of `net_cost` attributable to wastage; persisted for reporting. |
| `tb_recipe_yield_variantId` | `String? @db.Uuid` | Yes | FK to `tb_recipe_yield_variant.id` (Prisma-style camelCase column name); nullable. When set, the ingredient line applies only to that yield variant (some variants may use different ingredient ratios). |
| `created_at` | `DateTime? @default(now()) @db.Timestamptz(6)` | Yes | Creation timestamp. |
| `created_by_id` | `String? @db.Uuid` | Yes | Creator id. |
| `updated_at` | `DateTime? @default(now()) @db.Timestamptz(6)` | Yes | Last-update timestamp. |
| `updated_by_id` | `String? @db.Uuid` | Yes | Last-updater id. |
| `deleted_at` | `DateTime? @db.Timestamptz(6)` | Yes | Soft-delete timestamp. |
| `deleted_by_id` | `String? @db.Uuid` | Yes | Soft-delete actor id. |

**Constraints:** `@id` on `id`. FKs: `recipe_id → tb_recipe.id` (Cascade); `product_id → tb_product.id` (Restrict, nullable); `sub_recipe_id → tb_recipe.id` (Restrict, nullable, named relation `SubRecipeIngredients`); `ingredient_unit_id → tb_unit.id` (Restrict, named relation `recipe_ingredient_unit`); `inventory_unit_id → tb_unit.id` (Restrict, nullable, named relation `recipe_inventory_unit`); `tb_recipe_yield_variantId → tb_recipe_yield_variant.id` (nullable).
**Indexes:** None declared beyond the primary key. There is **no** unique index on `(recipe_id, product_id)` or `(recipe_id, sub_recipe_id)` — the same product / sub-recipe can appear multiple times on the same recipe (e.g. as two separate lines for two preparation stages), which is intentional.

### 2.3 tb_recipe_preparation_step

Preparation step on a recipe. Ordered, with optional media, timing, temperature, equipment, techniques, and safety / chef notes.

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `recipe_id` | `String @db.Uuid` | No | FK to `tb_recipe.id` (Cascade on delete). |
| `sequence_no` | `Int` | No | Step order within the recipe (1, 2, 3, ...). Required. |
| `title` | `String? @db.VarChar` | Yes | Short title (e.g. "Sear the steak"). |
| `description` | `String @db.Text` | No | Step body — instruction text. Required. |
| `images` | `Json? @default("[]") @db.JsonB` | Yes | Step image refs; default `[]`. |
| `videos` | `Json? @default("[]") @db.JsonB` | Yes | Step video refs; default `[]`. |
| `duration` | `Int?` | Yes | Step duration in minutes. |
| `temperature` | `Decimal? @db.Decimal(20, 5)` | Yes | Required cooking / holding temperature for the step. |
| `temperature_unit` | `enum_temperature_unit?` | Yes | `c` (Celsius) or `f` (Fahrenheit); default `c`. |
| `equipment` | `Json @default("[]")` | No | Equipment references for the step (e.g. `[{equipment_id, name}]`) — may reference `tb_recipe_equipment` rows. |
| `techniques` | `Json @default("[]")` | No | Technique tags (e.g. `["sous-vide", "flambé"]`). |
| `chef_notes` | `String? @db.Text` | Yes | Free-text chef tips and tricks. |
| `safety_warnings` | `String? @db.Text` | Yes | HACCP / food-safety notes (critical control points). |
| `created_at` | `DateTime? @default(now()) @db.Timestamptz(6)` | Yes | Creation timestamp. |
| `created_by_id` | `String? @db.Uuid` | Yes | Creator id. |
| `updated_at` | `DateTime? @default(now()) @db.Timestamptz(6)` | Yes | Last-update timestamp. |
| `updated_by_id` | `String? @db.Uuid` | Yes | Last-updater id. |
| `deleted_at` | `DateTime? @db.Timestamptz(6)` | Yes | Soft-delete timestamp. |
| `deleted_by_id` | `String? @db.Uuid` | Yes | Soft-delete actor id. |

**Constraints:** `@id` on `id`. FK `recipe_id → tb_recipe.id` (Cascade).
**Indexes:** None declared beyond the primary key. There is **no** unique index on `(recipe_id, sequence_no)` — sequence numbers are application-managed; re-ordering rewrites the column on touched rows.

### 2.4 tb_recipe_yield_variant

Yield variant on a recipe. Lets a single recipe produce multiple sellable sizes from the same formula (e.g. "small" / "medium" / "large" portions; "half-tray" / "full-tray"). Carries its own variant-level pricing.

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `recipe_id` | `String @db.Uuid` | No | FK to `tb_recipe.id` via named relation `RecipeYieldVariants` (Cascade on delete). |
| `variant_name` | `String @db.VarChar` | No | Variant display name (e.g. "Half-Portion", "Large"). |
| `variant_unit` | `String @db.VarChar` | No | Unit of `variant_quantity` (e.g. `portions`, `pieces`). |
| `variant_quantity` | `Decimal @db.Decimal(20, 5)` | No | Output quantity for this variant. |
| `conversion_rate` | `Decimal @db.Decimal(20, 5)` | No | Conversion rate from base yield to this variant (e.g. `0.5` for half-portion when base is full). |
| `cost_per_unit` | `Decimal? @db.Decimal(20, 5)` | Yes | Per-variant cost (computed: base cost × conversion_rate, adjusted for variant-specific lines). |
| `selling_price` | `Decimal? @db.Decimal(20, 5)` | Yes | Per-variant selling price. |
| `food_cost_percentage` | `Decimal? @db.Decimal(20, 5)` | Yes | `cost_per_unit / selling_price × 100`. |
| `gross_margin` | `Decimal? @db.Decimal(20, 5)` | Yes | `selling_price − cost_per_unit`. |
| `is_default` | `Boolean @default(false)` | No | Whether this is the default variant for the recipe (also tracked by `tb_recipe.default_variant_id`). |
| `shelf_life` | `Int?` | Yes | Variant-specific shelf life in hours / days (tenant-defined unit). |
| `wastage_rate` | `Decimal? @db.Decimal(20, 5)` | Yes | Variant-specific wastage % (overrides line-level wastage for this variant). |
| `min_order_quantity` | `Int?` | Yes | Minimum order quantity for the variant (used in production planning). |
| `max_order_quantity` | `Int?` | Yes | Maximum order quantity for the variant. |
| `created_at` | `DateTime? @default(now()) @db.Timestamptz(6)` | Yes | Creation timestamp. |
| `created_by_id` | `String? @db.Uuid` | Yes | Creator id. |
| `updated_at` | `DateTime? @default(now()) @db.Timestamptz(6)` | Yes | Last-update timestamp. |
| `updated_by_id` | `String? @db.Uuid` | Yes | Last-updater id. |
| `deleted_at` | `DateTime? @db.Timestamptz(6)` | Yes | Soft-delete timestamp. |
| `deleted_by_id` | `String? @db.Uuid` | Yes | Soft-delete actor id. |

**Constraints:** `@id` on `id`. FK `recipe_id → tb_recipe.id` (Cascade, named relation `RecipeYieldVariants`). Back-relations: many `tb_recipe_ingredient` (variant-scoped ingredients), many `tb_recipe_pricing_history`, many `tb_recipe` via named relation `DefaultVariant` (when a recipe points at this variant as its default).
**Indexes:** None declared beyond the primary key.

### 2.5 tb_recipe_version

Full versioned snapshot of a recipe at a point in time. Captures the four JSON blobs that together describe the recipe: header data, ingredients, steps, and yield variants. One row per saved version.

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `recipe_id` | `String @db.Uuid` | No | FK to `tb_recipe.id` (Cascade on delete). |
| `version_number` | `Int` | No | Sequential version number (1, 2, 3, ...); application-assigned. |
| `recipe_data` | `Json @db.JsonB` | No | Full header snapshot (all columns of `tb_recipe` at the time of versioning). |
| `ingredients_data` | `Json @db.JsonB` | No | Full snapshot of all ingredient lines on the recipe. |
| `steps_data` | `Json @db.JsonB` | No | Full snapshot of all preparation steps. |
| `variants_data` | `Json @db.JsonB` | No | Full snapshot of all yield variants. |
| `change_summary` | `String? @db.Text` | Yes | Free-text summary of what changed since the previous version. |
| `published` | `Boolean @default(false)` | No | Whether this version was published (vs. saved as draft); a recipe's published-history is the subset of versions with `published = true`. |
| `created_at` | `DateTime? @default(now()) @db.Timestamptz(6)` | Yes | Creation timestamp. |
| `created_by_id` | `String? @db.Uuid` | Yes | Author of the version (the user who triggered the save / publish). |
| `updated_at` | `DateTime? @default(now()) @db.Timestamptz(6)` | Yes | Last-update timestamp (usually equal to `created_at` since versions are immutable). |
| `updated_by_id` | `String? @db.Uuid` | Yes | Last-updater id. |
| `deleted_at` | `DateTime? @db.Timestamptz(6)` | Yes | Soft-delete timestamp. |
| `deleted_by_id` | `String? @db.Uuid` | Yes | Soft-delete actor id. |

**Constraints:** `@id` on `id`. FK `recipe_id → tb_recipe.id` (Cascade).
**Indexes:** None declared beyond the primary key. The (recipe_id, version_number) pair is application-managed for monotonicity; no unique constraint at the DB level.

### 2.6 tb_recipe_pricing_history

Cost / price history for a recipe (and optionally a specific yield variant). Each row is a snapshot at an `effective_date` capturing cost-per-portion, selling price, food-cost percentage, and gross margin, plus optional competitor benchmarks.

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `recipe_id` | `String @db.Uuid` | No | FK to `tb_recipe.id` (Cascade on delete). |
| `variant_id` | `String? @db.Uuid` | Yes | FK to `tb_recipe_yield_variant.id` (Cascade on delete); nullable when the snapshot is for the base recipe. |
| `cost_per_portion` | `Decimal @db.Decimal(20, 5)` | No | Snapshot of cost per portion at `effective_date`. |
| `selling_price` | `Decimal @db.Decimal(20, 5)` | No | Snapshot of selling price. |
| `food_cost_percentage` | `Decimal @db.Decimal(20, 5)` | No | Snapshot of `cost / price × 100`. |
| `gross_margin` | `Decimal @db.Decimal(20, 5)` | No | Snapshot of `price − cost`. |
| `competitor_avg_price` | `Decimal? @db.Decimal(20, 5)` | Yes | Market benchmark — average competitor price for comparable dish. |
| `competitor_min_price` | `Decimal? @db.Decimal(20, 5)` | Yes | Market benchmark — min competitor price. |
| `competitor_max_price` | `Decimal? @db.Decimal(20, 5)` | Yes | Market benchmark — max competitor price. |
| `change_reason` | `String? @db.VarChar` | Yes | Reason the snapshot was taken (e.g. "menu refresh", "ingredient cost spike", "competitor price match"). |
| `effective_date` | `DateTime @db.Timestamptz(6)` | No | The date the snapshot applies to. |
| `created_at` | `DateTime? @default(now()) @db.Timestamptz(6)` | Yes | Row creation timestamp. |
| `created_by_id` | `String? @db.Uuid` | Yes | Creator id. |
| `updated_at` | `DateTime? @default(now()) @db.Timestamptz(6)` | Yes | Last-update timestamp. |
| `updated_by_id` | `String? @db.Uuid` | Yes | Last-updater id. |
| `deleted_at` | `DateTime? @db.Timestamptz(6)` | Yes | Soft-delete timestamp. |
| `deleted_by_id` | `String? @db.Uuid` | Yes | Soft-delete actor id. |

**Constraints:** `@id` on `id`. FKs: `recipe_id → tb_recipe.id` (Cascade); `variant_id → tb_recipe_yield_variant.id` (Cascade, nullable).
**Indexes:** None declared beyond the primary key.

### 2.7 tb_recipe_category

Master data for recipe categories. Supports a self-referential hierarchy (parent → subcategories) and per-category default cost / margin settings inherited by new recipes in the category.

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `code` | `String @db.VarChar` | No | Category code. |
| `name` | `String @db.VarChar` | No | Category display name. |
| `description` | `String? @db.VarChar` | Yes | Free-text description. |
| `note` | `String? @db.VarChar` | Yes | Internal note. |
| `is_active` | `Boolean?` | Yes | Active flag; default `true`. |
| `parent_id` | `String? @db.Uuid` | Yes | FK to `tb_recipe_category.id` via named relation `CategoryHierarchy` (Restrict on delete); nullable for root categories. |
| `level` | `Int @default(1)` | No | Hierarchy level (1 = root, 2 = child, ...). Application-managed alongside `parent_id`. |
| `default_cost_settings` | `Json @default("{}") @db.JsonB` | No | Per-category default cost settings (target food-cost %, labor %, overhead %, etc.) that new recipes inherit. |
| `default_margins` | `Json @default("{}") @db.JsonB` | No | Per-category default margin settings. |
| `info` | `Json? @default("{}") @db.JsonB` | Yes | Extension bag. |
| `dimension` | `Json? @default("[]") @db.JsonB` | Yes | Cost-dimension default for category. |
| `doc_version` | `Int @default(0) @db.Integer` | No | Optimistic-concurrency counter. |
| `created_at` | `DateTime? @default(now()) @db.Timestamptz(6)` | Yes | Creation timestamp. |
| `created_by_id` | `String? @db.Uuid` | Yes | Creator id. |
| `updated_at` | `DateTime? @default(now()) @db.Timestamptz(6)` | Yes | Last-update timestamp. |
| `updated_by_id` | `String? @db.Uuid` | Yes | Last-updater id. |
| `deleted_at` | `DateTime? @db.Timestamptz(6)` | Yes | Soft-delete timestamp. |
| `deleted_by_id` | `String? @db.Uuid` | Yes | Soft-delete actor id. |

**Constraints:** `@id` on `id`. FK `parent_id → tb_recipe_category.id` (Restrict, named relation `CategoryHierarchy`). Back-relations: many `tb_recipe_category` (subcategories), many `tb_recipe`.
**Indexes:** None declared beyond the primary key. (Note: no unique index on `code` or `name` — the schema permits duplicate codes / names; uniqueness is application-enforced.)

### 2.8 tb_recipe_cuisines

Master data for cuisine types. Each cuisine carries a region tag (`enum_cuisine_region`) and may declare popular dishes / key ingredients for menu engineering.

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `name` | `String @db.VarChar` | No | Cuisine name (e.g. "Thai", "Italian", "French"). |
| `description` | `String? @db.VarChar` | Yes | Free-text description. |
| `note` | `String? @db.VarChar` | Yes | Internal note. |
| `is_active` | `Boolean?` | Yes | Active flag; default `true`. |
| `region` | `enum_cuisine_region` | No | Region tag — `ASIA`, `EUROPE`, `AMERICAS`, `AFRICA`, `MIDDLE_EAST`, `OCEANIA`. |
| `popular_dishes` | `Json @default("[]")` | No | Array of popular dish names for the cuisine. |
| `key_ingredients` | `Json @default("[]")` | No | Array of signature ingredients. |
| `info` | `Json? @default("{}") @db.JsonB` | Yes | Extension bag. |
| `dimension` | `Json? @default("[]") @db.JsonB` | Yes | Cost-dimension default. |
| `doc_version` | `Int @default(0) @db.Integer` | No | Optimistic-concurrency counter. |
| `created_at` | `DateTime? @default(now()) @db.Timestamptz(6)` | Yes | Creation timestamp. |
| `created_by_id` | `String? @db.Uuid` | Yes | Creator id. |
| `updated_at` | `DateTime? @default(now()) @db.Timestamptz(6)` | Yes | Last-update timestamp. |
| `updated_by_id` | `String? @db.Uuid` | Yes | Last-updater id. |
| `deleted_at` | `DateTime? @db.Timestamptz(6)` | Yes | Soft-delete timestamp. |
| `deleted_by_id` | `String? @db.Uuid` | Yes | Soft-delete actor id. |

**Constraints:** `@id` on `id`. Back-relations: many `tb_recipe`.
**Indexes:** `@@unique([name, deleted_at])` as `recipe_cuisines_name_u`; `@@index([region])`; `@@index([name])` as `recipe_cuisines_name_idx`.

### 2.9 tb_recipe_equipment_category / tb_recipe_equipment (companion masters)

`tb_recipe_equipment_category` is a thin hierarchy of equipment types; `tb_recipe_equipment` is the per-item master (code, name, category, physical details, capacity, station, operational / maintenance schedules, attachments, manuals). Equipment is referenced from preparation steps via the step's `equipment` JSON array, not via a foreign-key column. See Prisma schema lines 5226–5312 for the full field set. These are master data for recipe-side reference; they do not drive inventory.

## 3. Relationships

```
tb_recipe_category ──1──*──► tb_recipe              (Restrict on delete)
tb_recipe_cuisines ──1──*──► tb_recipe              (Restrict on delete)

tb_recipe
    │
    │ 1
    │
    ├──*──► tb_recipe_ingredient (Cascade)
    │             │
    │             ├──► tb_product       (Restrict, when ingredient_type = product)
    │             ├──► tb_recipe        (Restrict, named SubRecipeIngredients,
    │             │                      when ingredient_type = recipe — self-referential)
    │             ├──► tb_unit          (Restrict, recipe_ingredient_unit)
    │             └──► tb_unit          (Restrict, recipe_inventory_unit, nullable)
    │
    ├──*──► tb_recipe_preparation_step  (Cascade)
    │
    ├──*──► tb_recipe_yield_variant     (Cascade, named RecipeYieldVariants)
    │             │
    │             ├──► tb_recipe (DefaultVariant — back-ref via tb_recipe.default_variant_id)
    │             └──► tb_recipe_pricing_history (Cascade)
    │
    ├──*──► tb_recipe_version           (Cascade)
    │
    └──*──► tb_recipe_pricing_history   (Cascade)

tb_recipe_category ──*──*──► tb_recipe_category (self-referential, CategoryHierarchy)

tb_recipe_equipment_category ──1──*──► tb_recipe_equipment
    (equipment is referenced from prep-step JSON, not via FK)
```

Notes:

- **Recipe → ingredient** is 1-to-many with **Cascade on delete** — soft-deleting / hard-deleting the recipe takes its ingredient lines with it. This is intentional: the ingredient line has no meaning without its parent recipe.
- **Recipe → sub-recipe** (recipe-as-ingredient) is a **self-referential 1-to-many** through `tb_recipe_ingredient.sub_recipe_id`. The named relation `SubRecipeIngredients` distinguishes it from the primary `recipe_id` relation. The `tb_recipe_used_in_recipes` back-reference on `tb_recipe` is the inverse — given a recipe, find the parent recipes that use it as a sub-recipe (used by the impact-analysis dashboard when a sub-recipe cost changes).
- **Recipe → preparation step / yield variant / version / pricing history** are all 1-to-many with **Cascade on delete**.
- **Recipe → category / cuisine** are many-to-one with **Restrict on delete** — a category / cuisine cannot be deleted while any recipe references it; the user must reassign first.
- **Ingredient → unit (two paths)** — `ingredient_unit_id` (recipe UoM, required) and `inventory_unit_id` (stock UoM, nullable) are both FKs into `tb_unit` with distinct named relations. The `conversion_factor` on the line bridges the two; for inventory-driven recipe explosions ([[inventory]] OUT movements on menu sale), the stock unit and conversion factor are what matter.
- **Ingredient → product** is Restrict on delete — a product cannot be hard-deleted while any recipe references it. In practice product soft-delete is the operational pattern.
- **There is no `tb_menu_item` or `tb_recipe_menu_item` join table.** The carmen/docs PRD references a Recipe → Menu Item linkage; in the canonical tenant schema, menu-item modelling lives outside the recipe module (likely in the POS-integration layer or an application-layer mapping). See Section 5 for the divergence.
- **There is no `tb_recipe_comment` table** — the recipe module does not have a workflow / comment-thread audit trail in the standard pattern of GRN / SR / PR / PO. Audit comes from `tb_recipe_version` (full snapshots), the per-row audit columns (`created_at` / `created_by_id` / `updated_at` / `updated_by_id`), and `tb_recipe_pricing_history.change_reason`. Free-text discussion is not first-class on the recipe.
- All `Restrict` FKs are pure foreign-key constraints; the application enforces soft-delete cascades through `deleted_at` checks at the service layer rather than relying on Postgres cascade semantics.

## 4. Enums

- **`enum_recipe_status`** — three values, recipe-specific. Default `DRAFT`. Used on `tb_recipe.status`.
  - `DRAFT` — initial editable state; the recipe is being authored. Ingredients, steps, costing may be incomplete. Not eligible for menu-item linkage or for driving theoretical consumption. Cost figures on the header may not yet be valid.
  - `PUBLISHED` — recipe is approved and live. All required fields complete (`base_yield`, `base_yield_unit`, at least one ingredient, at least one prep step, cost calculations valid — see business rules). Eligible for menu-item linkage and theoretical-consumption drives. `published_at` is set on the transition. Edits to a `PUBLISHED` recipe create a new `tb_recipe_version` and may flip the recipe back to `DRAFT` for re-approval (tenant config) or apply directly with versioning trace.
  - `ARCHIVED` — recipe is retired from active use. `archived_at` is set on the transition. The recipe remains readable for audit but is excluded from default search / filter views, cannot be linked to new menu items, and does not drive theoretical consumption on new menu-sale events. Existing menu-item links are typically severed at archive (application policy).
- **`enum_recipe_difficulty`** — three values, recipe-specific. Default `MEDIUM`. Used on `tb_recipe.difficulty`. Display-only / filter-only; carries no business-rule weight.
  - `EASY` — minimal technique; suitable for trainees.
  - `MEDIUM` — standard kitchen execution.
  - `HARD` — advanced technique; senior staff or executive-chef oversight.
- **`enum_ingredient_type`** — two values, recipe-specific. No explicit default at the model level (the application sets it on row insert). Used on `tb_recipe_ingredient.ingredient_type`. The discriminator that decides which FK is populated (`product_id` for `product`, `sub_recipe_id` for `recipe`).
  - `product` — ingredient resolves to a `tb_product` row.
  - `recipe` — ingredient resolves to another `tb_recipe` row (sub-recipe).
- **`enum_temperature_unit`** — two values, recipe-specific. Default `c`. Used on `tb_recipe_preparation_step.temperature_unit`.
  - `c` — Celsius.
  - `f` — Fahrenheit.
- **`enum_cuisine_region`** — six values, recipe-specific. No default. Used on `tb_recipe_cuisines.region`. Region tag for cuisine master data; supports region-based filtering and reporting.
  - `ASIA`, `EUROPE`, `AMERICAS`, `AFRICA`, `MIDDLE_EAST`, `OCEANIA`.

## 5. Divergences from carmen/docs

The `RECIPE-Overview.md`, `RECIPE-PRD.md`, `RECIPE-Business-Requirements.md`, `RECIPE-Component-Structure.md`, `recipe-management.md`, and `recipe-create-edit-page.md` describe a TypeScript interface model and a feature set that differ from the canonical Prisma schema in several material ways. The differences below are catalogued from those sources.

| # | Item | carmen/docs says | Prisma has | Action |
|---|------|------------------|------------|--------|
| 1 | Recipe status values | PRD `status: 'draft' | 'published'` (two-state lifecycle); User-Flow-Diagram shows a third "Archive" state but doesn't list it in the status enum. Business Requirements `REC_ST_001` says "Valid statuses are 'draft' and 'published'". | `tb_recipe.status` uses the three-value `enum_recipe_status { DRAFT, PUBLISHED, ARCHIVED }`. Archived is a first-class state with its own timestamp column (`archived_at`). | Treat Prisma as canonical. Update carmen/docs to reflect the three-state lifecycle. Section 4 of this page lists the three values. |
| 2 | Ingredient type enum | Business Requirements `Ingredient.type: 'product' | 'recipe'` (lowercase, two values, no explicit constraint). | `tb_recipe_ingredient.ingredient_type` uses the `enum_ingredient_type { product, recipe }` (lowercase, two values — matches conceptually but the column name on the model is `ingredient_type` not `type`). | Aligned conceptually; the column name differs from the carmen/docs interface. Document the actual column name. |
| 3 | Total time on the recipe | PRD `Recipe.totalTime: number // Total time in minutes`. Business Requirements treats `totalTime` as a stored field. | `tb_recipe` has **no** `total_time` column. The rollup is computed at display time as `prep_time + cook_time`. | Update carmen/docs to mark `totalTime` as computed / display-only, not a stored column. |
| 4 | Menu Item linkage | RECIPE-Overview.md, RECIPE-Business-Requirements.md, and the wiki index page describe a Recipe → Menu Item linkage where "one recipe can underpin multiple menu items; one menu item can compose several recipes". RECIPE-PRD.md § 5 lists `Recipe to Menu Item` as a key relationship. | The tenant Prisma schema has **no** `tb_menu_item` table or `tb_recipe_menu_item` join table. The only `tb_menu` model in the schema (line 1375) is the navigation-menu config, not a sellable menu item. Menu-item modelling lives outside the recipe module — likely in a POS-integration layer or as an application-resolved mapping. | Document that menu-item linkage is **not** in the canonical tenant schema. The recipe-as-source-of-truth-for-theoretical-consumption pattern still holds, but the menu-item join is application-layer or in a separate module. Wiki overview text describing "menu item linkage" remains conceptually correct as a domain pattern, not as a schema relationship. |
| 5 | Workflow / comments / activity log | RECIPE-Component-Structure.md and the page specs describe recipe approval / review workflows (REC_ST_003 "Status changes must be tracked with timestamp and user") and changelog / audit trail components. | `tb_recipe` has **no** `workflow_id`, no `workflow_history`, no `workflow_current_stage`, and there is **no** `tb_recipe_comment` table. Status-change tracking is via `tb_recipe_version` (full snapshots) plus the per-row audit columns (`created_at`, `created_by_id`, `updated_at`, `updated_by_id`) and the two state-transition timestamps (`published_at`, `archived_at`). | Update carmen/docs to describe versioning (via `tb_recipe_version`) as the audit mechanism, not workflow / comment threads. Approval is an application-layer policy, not a schema-level workflow. |
| 6 | Yield variants | RECIPE-Business-Requirements.md mentions "yield" as a single number + unit on the recipe. PRD describes scaling but not variants. | `tb_recipe_yield_variant` is a first-class entity. A recipe may have 0 or many variants; `tb_recipe.default_variant_id` points to the default. Variants carry their own `cost_per_unit`, `selling_price`, `food_cost_percentage`, `gross_margin`, `wastage_rate`, `shelf_life`, and `min/max_order_quantity`. Ingredients can be variant-scoped via `tb_recipe_ingredient.tb_recipe_yield_variantId`. | Update carmen/docs to describe the yield-variant model. The "single yield" path is the no-variants case (`tb_recipe.base_yield + base_yield_unit` only); the multi-variant path uses the variant table. |
| 7 | Pricing history | RECIPE-Page-Flow.md mentions "Price History" as a display panel in the costing tab; PRD treats price as a single column. | `tb_recipe_pricing_history` is a first-class entity capturing per-effective-date snapshots of cost, price, food-cost %, gross margin, and competitor benchmarks. Each variant can have its own pricing history (`variant_id` nullable on the row). | Document pricing history as a persisted timeline, not a display rollup. Used by the cost-drift dashboard and the variance reporting. |
| 8 | Carbon footprint | RECIPE-Overview.md mentions environmental impact as a feature; PRD `Recipe.carbonFootprint: number`. | `tb_recipe.carbon_footprint` is a `Decimal(20, 5)` with default 0. No per-ingredient footprint column on `tb_recipe_ingredient` — the recipe-level value is the aggregate; per-ingredient rollup is application-computed from product-level footprint (which lives on `tb_product` if at all, or in an external sustainability data source). | Aligned conceptually; document the rollup as application-computed, not schema-stored at the ingredient level. |
| 9 | Equipment linkage | Page-specs describe "Equipment/Tools Required" as a tab on the recipe create / edit page with first-class equipment master. | `tb_recipe_equipment` and `tb_recipe_equipment_category` are first-class master-data tables, but equipment is referenced from `tb_recipe_preparation_step.equipment` (JSON array of equipment refs) rather than via a foreign-key join. There is no `tb_recipe_recipe_equipment` join table. | Document that equipment is per-step JSON, not per-recipe FK. The master tables exist for the equipment catalogue; the recipe-side linkage is denormalised by design. |
| 10 | Unit conversion on ingredients | PRD describes "Unit conversions must be handled for inventory management" (REC_IN_005) as a business rule but doesn't model two unit columns. | `tb_recipe_ingredient` carries **two** unit FKs: `ingredient_unit_id` (recipe-display UoM) and `inventory_unit_id` (stock UoM), bridged by `conversion_factor`. The two-unit model is what lets a recipe say "200 g flour" while inventory holds "1 kg bags". `inventory_qty = qty × conversion_factor`. | Document the two-unit pattern explicitly. Cost-per-unit on the line is in the recipe UoM by default (or in the inventory UoM, depending on tenant convention); the conversion is the schema's commitment to lossless UoM bridging. |
| 11 | Wastage cost vs net cost | Business Requirements `Ingredient` interface has `wastage: number` and `totalCost: number`. Cost calculation rule says `Total Cost = Σ(Ingredient Cost × (1 + Wastage%))`. | `tb_recipe_ingredient` persists **both** `net_cost` (the `(1 + wastage%)` total) and `wastage_cost` (the wastage component alone). The two columns let reporting separate "raw ingredient cost" from "wastage allowance" without recomputation. | Document both columns. `net_cost` is what rolls up to `tb_recipe.total_ingredient_cost`; `wastage_cost` is reporting-only. |

## 6. References

- **Primary (source of truth):** Prisma schemas listed in the header callout — concretely `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` (all eight recipe models at lines 5192–5624, plus the four recipe-specific enums at lines 5166–5186 and `enum_cuisine_region` at lines 5155–5164, and the `tb_product.is_used_in_recipe` flag at line 1477) and `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` (verified to contain no recipe models).
- **Secondary (concept cross-check):**
  - `../carmen/docs/recipe-module/RECIPE-Overview.md` — module purpose, key features, user roles; divergences in Section 5 (items 1, 4, 5, 8).
  - `../carmen/docs/recipe-module/RECIPE-PRD.md` — user stories, feature requirements, data requirements, key relationships; divergences in Section 5 (items 1, 2, 3, 4, 6, 7, 10).
  - `../carmen/docs/recipe-module/RECIPE-Business-Requirements.md` — business rules `REC_CR_001`–`REC_CR_005` (creation), `REC_CO_001`–`REC_CO_005` (costing), `REC_IN_001`–`REC_IN_005` (ingredients), `REC_ST_001`–`REC_ST_004` (status); divergences in Section 5 (items 1, 2, 3, 5, 10, 11).
  - `../carmen/docs/recipe-module/RECIPE-Component-Structure.md` — UI component contracts; divergences in Section 5 (items 5, 9).
  - `../carmen/docs/recipe-module/RECIPE-Page-Flow.md` — page flows and user journeys; divergences in Section 5 (items 5, 7).
  - `../carmen/docs/recipe-module/RECIPE-User-Flow-Diagram.md` — visual flows; divergences in Section 5 (item 1 — three-state vs two-state).
  - `../carmen/docs/recipe/recipe-management.md` — master-list / create-edit / costing-sheet / preparation / media / scaling / category page layouts; layout-level reference for the create-edit and view pages.
  - `../carmen/docs/recipe/recipe-create-edit-page.md` — page-spec source for the recipe form's tabbed interface (Basic Info, Ingredients, Method, Media, Costing, Nutritional).
  - `../carmen/docs/recipe/recipe-list-page.md` — master-list page spec.
  - `../carmen/docs/recipe/recipe-view-page.md` — read-only detail page spec.
- **Sibling reference:** [01-data-model.md](../store-requisition/01-data-model.md) (store-requisition) — describes the downstream side of the recipe → SR auto-create pattern (`info.recipe_id` back-reference on the SR header).
- Related modules: [[product]] (recipe ingredients reference products through `tb_recipe_ingredient.product_id`; `tb_product.is_used_in_recipe` flag distinguishes recipe-eligible products), [[inventory]] (recipe usage drives OUT movements through theoretical consumption on menu-sale events), [[costing]] (per-ingredient `cost_per_unit` is sourced from the product's costing-method valuation), [[store-requisition]] (recipes may auto-generate SR drafts for planned production / banquet events via `info.recipe_id`).

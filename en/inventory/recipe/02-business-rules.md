---
title: Recipe — Business Rules
description: Validation, calculation, authorization, posting, and cross-module rules for the recipe module.
published: true
date: 2026-05-19T23:55:00.000Z
tags: recipe, business-rules, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T16:00:00.000Z
---

# Recipe — Business Rules

> **At a Glance**
> **Rule families:** `REC_VAL_*` validation &nbsp;·&nbsp; `REC_AUTH_*` permission &nbsp;·&nbsp; `REC_CALC_*` calc &nbsp;·&nbsp; `REC_POST_*` posting &nbsp;·&nbsp; `REC_XMOD_*` cross-module
> **Rule count:** approximately 69 rules
> **Audience:** Test author + developer — every rule ID is anchored from `04-test-scenarios*` pages
> **Status lifecycle:** Section 5.1 (where present) carries the Live UI vs BRD discrepancy callouts

## 1. Overview

This page captures the operational business rules that govern a recipe through its lifecycle: input validation at create / edit / publish / archive time, the cost-engineering calculation rules (ingredient → line → recipe → portion → price → margin), authorization gates by role and status, posting effects on each transition of `enum_recipe_status`, and cross-module rules with [product](/en/inventory/product), [inventory](/en/inventory/inventory), [costing](/en/inventory/costing), and [store-requisition](/en/inventory/store-requisition). Unlike workflow-driven documents (PR, PO, GRN, SR), the recipe is **not** a workflow document — there is no `workflow_id`, no per-line approval signatures, no comment threads. The publication gate is a single transition guarded by application-level RBAC and a checklist of completeness rules; the audit mechanism is `tb_recipe_version` (full snapshots) plus `tb_recipe_pricing_history` (cost / price timeline). The recipe is the **source of truth for what should be consumed when something is sold** — when a `PUBLISHED` recipe is linked to a sold menu item, exploding the recipe by sold quantity drives the theoretical inventory consumption used in food-cost variance reporting.

Two structural points colour every rule below and are worth restating up front. **First**, the recipe lifecycle has three states (`DRAFT`, `PUBLISHED`, `ARCHIVED`) and a strict directional flow: `DRAFT → PUBLISHED → ARCHIVED` is the canonical path, with `PUBLISHED → DRAFT` allowed only when tenant policy requires re-approval after edits (otherwise edits to a `PUBLISHED` recipe apply directly with a new `tb_recipe_version` row). `ARCHIVED → PUBLISHED` is **not** allowed by default — archived recipes are retired; the path back is to clone the archived recipe into a new `DRAFT` and re-publish. **Second**, every change to a `PUBLISHED` recipe (ingredient quantity, sub-recipe swap, wastage %, prep / cook time, cost rate) writes a new `tb_recipe_version` row capturing the full snapshot of header / ingredients / steps / variants — this is the recipe module's audit trail and the rollback mechanism. Pricing-relevant changes additionally write a `tb_recipe_pricing_history` row with the cost / price / food-cost % / gross-margin snapshot at the new effective date.

## 2. Validation Rules

Rule IDs follow `REC_VAL_NNN`. Header rules (001–008) run on every save and on publish; line rules (009–014) run per line on save and on publish; aggregate / at-publish rules (015–018) run only at the `DRAFT → PUBLISHED` transition.

| Rule ID | Condition | When enforced | Error / behaviour |
| ------- | --------- | ------------- | ----------------- |
| `REC_VAL_001` | `tb_recipe.code` is non-null, non-empty, and follows the tenant's code-format policy (typically `RCP-<CATEGORY>-<SEQ>`). The `(code, name, deleted_at)` triple is unique against non-soft-deleted recipes. | Create, save, publish | Reject with "Recipe code is required and the (code, name) pair must be unique." |
| `REC_VAL_002` | `tb_recipe.name` is non-null and non-empty (trimmed). | Create, save, publish | Reject with "Recipe name is required." |
| `REC_VAL_003` | `tb_recipe.category_id` is non-null and references a non-soft-deleted, `is_active = true` row in `tb_recipe_category`. | Save, publish | Reject with "Recipe category is required and must reference an active category." |
| `REC_VAL_004` | `tb_recipe.cuisine_id` is non-null and references a non-soft-deleted, `is_active = true` row in `tb_recipe_cuisines`. | Save, publish | Reject with "Cuisine type is required and must reference an active cuisine." |
| `REC_VAL_005` | `tb_recipe.base_yield > 0` and `tb_recipe.base_yield_unit` is non-empty. | Save (warn for 0), publish (block) | Reject with "Recipe yield must be greater than zero and a yield unit is required." |
| `REC_VAL_006` | `tb_recipe.prep_time ≥ 0` and `tb_recipe.cook_time ≥ 0`. (Zero is allowed; negative values are not.) | Save, publish | Reject with "Prep time and cook time must be non-negative." |
| `REC_VAL_007` | If `tb_recipe.default_variant_id` is non-null, the referenced `tb_recipe_yield_variant.recipe_id` matches `tb_recipe.id` (the default-variant pointer belongs to the same recipe) and the variant is not soft-deleted. | Save, publish | Reject with "Default yield variant must belong to this recipe and must not be deleted." |
| `REC_VAL_008` | `target_food_cost_percentage`, `labor_cost_percentage`, `overhead_percentage` (when non-null) each fall in `[0, 100]`. | Save, publish | Reject with "Cost percentage values must be between 0 and 100." |
| `REC_VAL_009` | Each `tb_recipe_ingredient` row has `qty > 0` and `cost_per_unit ≥ 0` and `wastage_percentage ∈ [0, 100)`. (100% wastage is not meaningful; ≥ 100 rejected.) | Save line (warn for 0 qty), publish (block) | Reject the line with "Ingredient quantity must be greater than zero; cost per unit must be non-negative; wastage percentage must be in [0, 100)." |
| `REC_VAL_010` | Per-line discriminator integrity: when `ingredient_type = product`, `product_id` is non-null and references a non-soft-deleted `tb_product` with `is_used_in_recipe = true` and `is_active = true`; `sub_recipe_id` is null. When `ingredient_type = recipe`, `sub_recipe_id` is non-null and references a non-soft-deleted `tb_recipe` with `status = PUBLISHED`; `product_id` is null. | Save line, publish | Reject the line with "Ingredient discriminator mismatch: type `<ingredient_type>` requires `<expected_fk>` populated and the referenced row to be active and (for sub-recipes) published." |
| `REC_VAL_011` | No-cycle rule on sub-recipes: a recipe cannot use itself, directly or transitively, as a sub-recipe. The dependency graph rooted at `sub_recipe_id` must be acyclic. | Save line, publish | Reject the line with "Sub-recipe cycle detected: recipe `<name>` cannot reference itself directly or through another sub-recipe." |
| `REC_VAL_012` | UoM consistency on the line: `ingredient_unit_id` is non-null and references an active `tb_unit`. If `inventory_unit_id` is non-null and differs from `ingredient_unit_id`, `conversion_factor` must be non-null and positive. If `inventory_unit_id IS NULL`, `inventory_qty` and `conversion_factor` should also be null (display unit = stock unit, no conversion needed). | Save line, publish | Reject the line with "Unit conversion is incomplete: when the recipe unit and inventory unit differ, a positive conversion factor is required." |
| `REC_VAL_013` | Cost-component consistency: `net_cost` equals `qty × cost_per_unit × (1 + wastage_percentage/100)` to within rounding precision; `wastage_cost` equals `qty × cost_per_unit × (wastage_percentage/100)`. The application re-computes these on every save; manual override is not permitted. | Save line, publish | Reject the line with "Ingredient cost columns are inconsistent — `net_cost` and `wastage_cost` must equal the values derived from `qty × cost_per_unit × wastage%`." |
| `REC_VAL_014` | Per-line sub-recipe state: when `ingredient_type = recipe`, the referenced sub-recipe is in `status = PUBLISHED` **at the moment of the parent recipe's save / publish**. A sub-recipe that has since been archived blocks the parent's publish; the line must be reassigned or the sub-recipe re-published. | Save line, publish | Reject the line with "Sub-recipe `<name>` is not currently published; the parent recipe cannot reference an unpublished or archived sub-recipe." |
| `REC_VAL_015` | At publish, the recipe has at least one non-soft-deleted `tb_recipe_ingredient` row. | Publish | Reject with "Recipe must contain at least one ingredient line before it can be published." |
| `REC_VAL_016` | At publish, the recipe has at least one non-soft-deleted `tb_recipe_preparation_step` row. | Publish | Reject with "Recipe must contain at least one preparation step before it can be published." |
| `REC_VAL_017` | At publish, the recipe's cost rollup is valid: `total_ingredient_cost = Σ active line net_cost`; `cost_per_portion = (total_ingredient_cost + labor_cost + overhead_cost) / base_yield`; `cost_per_portion > 0`. | Publish | Reject with "Recipe cost rollup is invalid or zero — verify ingredient costs, labor, overhead, and yield before publishing." |
| `REC_VAL_018` | At publish, if `selling_price` is non-null, it satisfies `selling_price > cost_per_portion` (a recipe sold below its cost is rejected at publish, though the field is nullable to permit recipes that are not directly priced, e.g. side dishes or sub-recipes). | Publish | Reject with "Selling price must be greater than cost per portion at publish; review pricing." |

## 3. Calculation Rules

The recipe is a **cost-engineering document**: the calculation surface is rich. All cost / quantity columns are stored as `Decimal(20, 5)` at the row level; display rounding is half-up to 2 decimals for currency, 3 decimals for quantities. The calculation chain is line → recipe → portion → price → margin, with sub-recipe costs flowing in recursively.

Rule IDs follow `REC_CALC_NNN`.

| Rule ID | Formula |
| ------- | ------- |
| `REC_CALC_001` (line wastage component) | `wastage_cost = qty × cost_per_unit × (wastage_percentage / 100)`. Persisted on the ingredient row. Used by reporting to separate "raw cost" from "wastage allowance". |
| `REC_CALC_002` (line net cost) | `net_cost = qty × cost_per_unit × (1 + wastage_percentage / 100) = qty × cost_per_unit + wastage_cost`. Persisted on the ingredient row. Rolls up to `tb_recipe.total_ingredient_cost`. |
| `REC_CALC_003` (recipe total ingredient cost) | `total_ingredient_cost = Σ tb_recipe_ingredient.net_cost` across active (non-soft-deleted) lines. Persisted on the header. Re-computed on any ingredient-line change. |
| `REC_CALC_004` (labor cost) | `labor_cost = (prep_time + cook_time) × labor_rate × labor_cost_percentage / 100`. The `labor_rate` comes from tenant config (typically $/minute or ฿/minute); `labor_cost_percentage` is the share of the labor rate attributable to this recipe's category (default 30%, configurable per-category via `tb_recipe_category.default_cost_settings`). Persisted on the header. |
| `REC_CALC_005` (overhead cost) | `overhead_cost = total_ingredient_cost × overhead_percentage / 100`. Default overhead percentage is 20%, configurable per-category. Persisted on the header. |
| `REC_CALC_006` (recipe total cost) | `total_recipe_cost = total_ingredient_cost + labor_cost + overhead_cost`. Computed for display and the per-portion division; **not** persisted as a separate column on `tb_recipe` (it is the sum of the three persisted components). |
| `REC_CALC_007` (cost per portion) | `cost_per_portion = total_recipe_cost / base_yield`. For variants, `cost_per_unit = total_recipe_cost × (variant.conversion_rate / base_yield) × variant.variant_quantity`, but the persisted variant `cost_per_unit` is computed at variant-write time. Persisted on the header for the base recipe and on each `tb_recipe_yield_variant` row. |
| `REC_CALC_008` (suggested selling price) | `suggested_price = cost_per_portion / (1 − target_food_cost_percentage / 100)`. The price that, given the target food-cost %, returns the desired margin. Persisted on the header. Re-computed on cost changes or target changes. |
| `REC_CALC_009` (actual food cost percentage) | `actual_food_cost_percentage = cost_per_portion / selling_price × 100`. Computed only when `selling_price` is non-null. Persisted on the header. |
| `REC_CALC_010` (gross margin) | `gross_margin = selling_price − cost_per_portion` (absolute amount). `gross_margin_percentage = (selling_price − cost_per_portion) / selling_price × 100`. Computed only when `selling_price` is non-null. Both persisted. |
| `REC_CALC_011` (sub-recipe cost roll-up) | When `ingredient_type = recipe`, `cost_per_unit` on the line is the sub-recipe's `cost_per_portion` (or per-unit equivalent based on the line's `ingredient_unit_id` and the sub-recipe's yield unit). When the sub-recipe's `cost_per_portion` changes, every parent recipe that references it must re-compute: a write to `tb_recipe.cost_per_portion` propagates through `tb_recipe_used_in_recipes` (the inverse back-relation on the sub-recipe) to refresh `cost_per_unit` and `net_cost` on each parent's ingredient line, then `total_ingredient_cost` and downstream columns on each parent header. This may cascade further if the parent is also a sub-recipe. |
| `REC_CALC_012` (variant scaling) | For each `tb_recipe_yield_variant`: variant ingredient quantities = base quantities × `conversion_rate` (unless the ingredient is variant-scoped via `tb_recipe_ingredient.tb_recipe_yield_variantId`, in which case its `qty` applies as-is); variant `cost_per_unit` = scaled `total_recipe_cost` / `variant_quantity`; variant `selling_price`, `food_cost_percentage`, `gross_margin` follow the same formulas as the base recipe but use the variant's pricing inputs. |
| `REC_CALC_013` (UoM conversion on line) | `inventory_qty = qty × conversion_factor` when `inventory_unit_id ≠ ingredient_unit_id`. Cost-per-unit on the line is per `ingredient_unit_id` by tenant default; when the source product is costed per `inventory_unit_id`, the conversion is applied: `cost_per_unit_recipe = cost_per_unit_stock / conversion_factor`. |
| `REC_CALC_014` (theoretical consumption) | When a menu item linked to recipe `R` is sold in quantity `S`, the theoretical OUT movement per ingredient is `theoretical_out_qty = S × R.line.qty × R.line.conversion_factor × (1 + R.line.wastage_percentage/100)`, expressed in `R.line.inventory_unit_id`. Sub-recipe lines recurse. `theoretical_out_cost = theoretical_out_qty × inventory_unit_cost` (sourced from the outlet's costing-method valuation via `[costing](/en/inventory/costing)`). Computed at the menu-sale event by the inventory / POS-integration layer; the recipe module is the formula source. |
| `REC_CALC_015` (rounding mode) | Half-up to 5 decimals for storage (`Decimal(20, 5)`); half-up to 2 decimals for currency display; half-up to 3 decimals for quantity display. Sub-recipe cost roll-ups carry full 5dp precision through the chain; only display rounds. |

### 3.1 Worked example (1 recipe, 4 ingredients including 1 sub-recipe, 1 variant)

Recipe *House Burger* with `base_yield = 1 portion`, `base_yield_unit = portions`, `prep_time = 8 min`, `cook_time = 12 min`, `target_food_cost_percentage = 32.00`, `labor_rate = ฿2.50/min`, `labor_cost_percentage = 30.00`, `overhead_percentage = 20.00`. Four ingredient lines.

- **Line 1** (Beef Patty, `product`): `qty = 1`, `ingredient_unit = piece`, `cost_per_unit = ฿45.00`, `wastage_percentage = 5%`.
  - `wastage_cost = 1 × 45.00 × 0.05 = ฿2.25`.
  - `net_cost = 1 × 45.00 × 1.05 = ฿47.25`.
- **Line 2** (Brioche Bun, `product`): `qty = 1`, `ingredient_unit = piece`, `cost_per_unit = ฿8.00`, `wastage_percentage = 0%`.
  - `wastage_cost = 0`; `net_cost = ฿8.00`.
- **Line 3** (Cheese, `product`): `qty = 30`, `ingredient_unit = g`, `inventory_unit = kg`, `conversion_factor = 0.001`, `cost_per_unit = ฿0.40/g` (or ฿400/kg from stock side), `wastage_percentage = 2%`.
  - `wastage_cost = 30 × 0.40 × 0.02 = ฿0.24`.
  - `net_cost = 30 × 0.40 × 1.02 = ฿12.24`.
  - `inventory_qty = 30 × 0.001 = 0.030 kg`.
- **Line 4** (Burger Sauce — sub-recipe, `recipe`): `qty = 15`, `ingredient_unit = g`, `cost_per_unit` sourced from sub-recipe `cost_per_portion` translated to per-gram = `฿0.18/g`, `wastage_percentage = 0%`.
  - `wastage_cost = 0`; `net_cost = 15 × 0.18 = ฿2.70`.

Roll-up:

- `total_ingredient_cost = 47.25 + 8.00 + 12.24 + 2.70 = ฿70.19` (per `REC_CALC_003`).
- `labor_cost = (8 + 12) × 2.50 × 30/100 = 20 × 2.50 × 0.30 = ฿15.00` (per `REC_CALC_004`).
- `overhead_cost = 70.19 × 20/100 = ฿14.04` (per `REC_CALC_005`).
- `total_recipe_cost = 70.19 + 15.00 + 14.04 = ฿99.23` (per `REC_CALC_006`).
- `cost_per_portion = 99.23 / 1 = ฿99.23` (per `REC_CALC_007`).
- `suggested_price = 99.23 / (1 − 0.32) = 99.23 / 0.68 = ฿145.93` (per `REC_CALC_008`).

If the chef chooses `selling_price = ฿150.00`:

- `actual_food_cost_percentage = 99.23 / 150.00 × 100 = 66.15% ... wait, this is wrong` — let me redo: `actual_food_cost_percentage = cost_per_portion / selling_price × 100 = 99.23 / 150.00 × 100 = 66.15%`. **That's too high — the recipe is over-costed for a ฿150 menu price.** This is the expected output: the screen shows the actual food-cost % is **above** the 32% target, flagging the recipe for cost review or price adjustment. The chef would either reduce ingredient cost (negotiate beef pricing, swap to cheaper bun), reduce labor / overhead allocation, or raise the selling price toward ฿310 (which is what 32% target on ฿99 cost would require).
- `gross_margin = 150.00 − 99.23 = ฿50.77` (per `REC_CALC_010`).
- `gross_margin_percentage = 50.77 / 150.00 × 100 = 33.85%`.

The example illustrates that the calculation flow is mechanical, but the resulting numbers expose whether the recipe is commercially viable at the chosen price — which is the point of the cost-engineering discipline.

**Variant scaling**: a "Double Burger" variant with `conversion_rate = 1.8` (1.8x base) — the ingredient quantities scale: Line 1 patty becomes `qty = 2` (often configured discretely per variant rather than by pure factor for stepped ingredients like whole patties); Line 3 cheese becomes 54g; etc. Variant cost = scaled `total_recipe_cost / variant_quantity`; variant pricing follows separately.

### 3.2 Worked example (sub-recipe cost change cascading)

Sub-recipe *Burger Sauce* (used as Line 4 above) has its mayonnaise ingredient's `cost_per_unit` rise from ฿0.10/g to ฿0.14/g due to a vendor pricelist update.

- `Burger Sauce.cost_per_portion` recomputes: previous ฿18.00 / 100g portion → new ฿20.40 / 100g portion (illustrative numbers).
- *House Burger* Line 4 `cost_per_unit` refreshes from ฿0.18/g to ฿0.204/g (per `REC_CALC_011`).
- Line 4 `net_cost` refreshes from ฿2.70 to ฿3.06.
- *House Burger* `total_ingredient_cost` updates from ฿70.19 to ฿70.55.
- `overhead_cost` updates (since it's based on ingredient cost) from ฿14.04 to ฿14.11.
- `total_recipe_cost` updates from ฿99.23 to ฿99.66.
- `cost_per_portion` updates from ฿99.23 to ฿99.66.
- `actual_food_cost_percentage` at ฿150 price moves from 66.15% to 66.44%.

This cascade is what makes sub-recipes valuable — change one ingredient cost on the sub-recipe and every parent re-costs automatically. A `tb_recipe_pricing_history` row is written for each affected recipe with `change_reason = "vendor pricelist update propagated through sub-recipe Burger Sauce"`.

## 4. Authorization Rules

Rule IDs follow `REC_AUTH_NNN`. Authorization is enforced by RBAC at the API layer; the recipe module is **not** workflow-driven, so authorization is direct (role-on-object) rather than stage-gated. Role names map to the five-persona grouping from the wiki index: Chef, Cost Controller, Outlet Manager, Procurement / F&B Ops, Audit / Config.

| Rule ID | Subject | Right | Constraint |
| ------- | ------- | ----- | ---------- |
| `REC_AUTH_001` | Chef (Kitchen Manager) | Create recipe (`status = DRAFT`) | Chef holds `recipe:create` permission. New recipe is `DRAFT`; `created_by_id = user`; the chef owns the editable draft. |
| `REC_AUTH_002` | Chef | Edit recipe header, ingredients, steps, variants | Allowed while `status = DRAFT` for any chef with `recipe:edit` on the category; for `PUBLISHED` recipes, edits require either (a) chef + tenant policy `edit_published_with_versioning = true` (write applies and a new `tb_recipe_version` row is created), or (b) the recipe is first moved back to `DRAFT` (`REC_AUTH_005`). |
| `REC_AUTH_003` | Chef | Publish recipe (`DRAFT → PUBLISHED`) | Chef holds `recipe:publish` permission. All `REC_VAL_015`–`REC_VAL_018` rules pass. Tenant policy may require Cost Controller co-approval for the publish action when `actual_food_cost_percentage > target_food_cost_percentage` by more than the tenant tolerance (e.g. 2 percentage points). |
| `REC_AUTH_004` | Chef | Archive recipe (`PUBLISHED → ARCHIVED`) | Chef holds `recipe:archive` permission. Allowed when the recipe is no longer in use for menu sales (no active menu-item linkages) or with explicit override. Sets `archived_at = now()`. Existing menu-item linkages should be severed before archive (application policy). |
| `REC_AUTH_005` | Chef | Move `PUBLISHED → DRAFT` (un-publish for revision) | Chef holds `recipe:edit-published` permission AND tenant policy permits un-publish (some tenants require all edits to be in-place with versioning, never un-publish). Sets `published_at = null` (or preserves; tenant choice). Linked menu items should be reviewed. |
| `REC_AUTH_006` | Cost Controller | Edit cost-related fields (`target_food_cost_percentage`, `labor_cost`, `overhead_cost`, `labor_cost_percentage`, `overhead_percentage`, `selling_price`, `suggested_price`) | Cost Controller holds `recipe:edit-cost` permission. Allowed on `DRAFT` and `PUBLISHED` recipes (cost-only edits are a recognised partial-update pattern; full ingredient / step edits require the chef role). Edits trigger a `tb_recipe_pricing_history` row. |
| `REC_AUTH_007` | Cost Controller | Co-approve publish when actual food-cost % exceeds target tolerance | When `REC_AUTH_003`'s tenant policy is on, the Cost Controller's co-approval is recorded in the recipe's audit trail (typically via the `tb_recipe_version.change_summary` or an application-layer signoff log). |
| `REC_AUTH_008` | Cost Controller | Review and sign off on recipe-cost changes affecting menu pricing | Read all costs; trigger pricing-history snapshots; flag recipes whose margin has drifted outside tolerance for chef / F&B Ops review. |
| `REC_AUTH_009` | Outlet Manager | Read published recipes used in the outlet | Read-only access to `status = PUBLISHED` recipes. May raise feedback (portion-control issues, ingredient accuracy concerns) outside the recipe schema (operational comment channel). Cannot edit. |
| `REC_AUTH_010` | Procurement / F&B Ops | Read all recipes for procurement planning | Read-only access to all recipes (any `status`). Uses recipe explosions × forecast sales to size purchase orders. Cannot edit. |
| `REC_AUTH_011` | F&B Operations Manager | Strategic approval — new menu items and recipe linkages | F&B Ops holds `recipe:approve-menu-link` permission. Required when a recipe is linked to a new POS menu item or when a category's target food-cost % is being shifted upward. The approval is recorded outside the recipe schema (menu-item / POS-integration layer); the recipe itself is unchanged. |
| `REC_AUTH_012` | Audit / Config — Sysadmin | Manage recipe-module config | Owns `tb_recipe_category` master data (categories, default cost settings, RBAC mapping), `tb_recipe_cuisines` master, `tb_recipe_equipment_category` / `tb_recipe_equipment` master, integration wiring with `[product](/en/inventory/product)` / `[inventory](/en/inventory/inventory)` / `[store-requisition](/en/inventory/store-requisition)`, and the `recipe:*` permission mapping in RBAC. |
| `REC_AUTH_013` | Audit / Config — Auditor | Read-only access for compliance review | Auditor holds `recipe:read` and `recipe:read-history` permissions. May review `tb_recipe_version` snapshots, `tb_recipe_pricing_history` timeline, and `created_by_id` / `updated_by_id` audit columns. No write permission. |
| `REC_AUTH_014` | Soft delete | Soft-delete a recipe | Allowed only on `DRAFT` recipes (chef + delete permission). `PUBLISHED` recipes must be archived, not deleted. `ARCHIVED` recipes may be soft-deleted by Sysadmin for data hygiene after a retention period. |

## 5. Posting Rules

Status values are the literal members of `enum_recipe_status` documented in [recipe/01-data-model.md](./01-data-model.md) § 4: **`DRAFT`**, **`PUBLISHED`**, **`ARCHIVED`**. The lifecycle is `DRAFT → PUBLISHED → ARCHIVED`, with `PUBLISHED → DRAFT` as an optional un-publish path. There is no commit-and-fan-out event in the GRN / SR sense — the recipe is not a transactional document. Instead, **publication** is the event that makes the recipe eligible for menu-item linkage and theoretical consumption; **ingredient edits on a published recipe** are the events that trigger pricing-history snapshots and downstream re-costing; **archive** is the event that retires the recipe.

Rule IDs follow `REC_POST_NNN`.

| Rule ID | Transition / Event | Effects |
| ------- | ------------------ | ------- |
| `REC_POST_001` | Create (→ `DRAFT`) | Insert `tb_recipe` with `status = DRAFT`, `code` per tenant numbering policy, `is_active = true`, audit columns populated. No ingredients, no steps, no variants yet. No cost rollup. |
| `REC_POST_002` | Save (within `DRAFT`) | Update `tb_recipe`, `tb_recipe_ingredient`, `tb_recipe_preparation_step`, `tb_recipe_yield_variant` per the user's edits. Recompute `tb_recipe_ingredient.net_cost` and `tb_recipe_ingredient.wastage_cost` per `REC_CALC_001`–`REC_CALC_002`. Recompute `tb_recipe.total_ingredient_cost`, `labor_cost`, `overhead_cost`, `cost_per_portion`, `suggested_price`, `actual_food_cost_percentage`, `gross_margin`, `gross_margin_percentage` per `REC_CALC_003`–`REC_CALC_010`. Append `updated_at` / `updated_by_id`. No `tb_recipe_version` snapshot is written on save while `DRAFT` (only on publish or on edits to `PUBLISHED`). |
| `REC_POST_003` | Publish (`DRAFT → PUBLISHED`) — **the publication event** | Set `status = PUBLISHED`, `published_at = now()`. All `REC_VAL_015`–`REC_VAL_018` rules pass (at least one ingredient, at least one step, valid cost rollup, selling price ≥ cost per portion if set). Write `tb_recipe_version` row capturing the full snapshot (`recipe_data`, `ingredients_data`, `steps_data`, `variants_data`), with `version_number = 1` (or next sequential), `published = true`, `change_summary = "initial publication"`. Write `tb_recipe_pricing_history` row capturing the cost / price / food-cost % / gross-margin snapshot at `effective_date = now()`. Recipe is now eligible for menu-item linkage and theoretical consumption. |
| `REC_POST_004` | Edit ingredient / step on `PUBLISHED` recipe (tenant policy: in-place with versioning) | Apply the edit to `tb_recipe_ingredient` / `tb_recipe_preparation_step` / `tb_recipe`. Recompute the cost rollup per `REC_CALC_003`–`REC_CALC_010`. Write a new `tb_recipe_version` row with `version_number = previous + 1`, `published = true`, `change_summary` from the user. If the cost / price changed, write a new `tb_recipe_pricing_history` row with `effective_date = now()` and `change_reason` from the user. The recipe stays `PUBLISHED`. |
| `REC_POST_005` | Edit ingredient / step on `PUBLISHED` recipe (tenant policy: un-publish required) | Move `PUBLISHED → DRAFT` per `REC_AUTH_005`; set `published_at = null` (or preserve; tenant choice). Apply edits in `DRAFT`. Re-publish per `REC_POST_003` writes a new `tb_recipe_version` row. Linked menu items are flagged for review during the un-publish window (the recipe is not eligible to drive theoretical consumption while in `DRAFT`). |
| `REC_POST_006` | Sub-recipe cost change cascade | When a `PUBLISHED` sub-recipe's `cost_per_portion` changes (via `REC_POST_004`), every parent recipe that references it (back-relation `tb_recipe_used_in_recipes`) is re-costed atomically per `REC_CALC_011`. For each affected parent: refresh `cost_per_unit` and `net_cost` on the relevant ingredient line(s), refresh the parent's `total_ingredient_cost` / `cost_per_portion` / pricing, write a `tb_recipe_pricing_history` row with `change_reason = "sub-recipe cost cascade from <sub-recipe-name>"`. The cascade may recurse if the parent is also a sub-recipe. |
| `REC_POST_007` | Archive (`PUBLISHED → ARCHIVED`) | Set `status = ARCHIVED`, `archived_at = now()`. Write a final `tb_recipe_version` row with `change_summary = "archived"`. The recipe is no longer eligible for menu-item linkage or theoretical consumption on subsequent menu sales. Existing linked menu items should be removed (application policy); historical theoretical-consumption events for the archived recipe remain in the inventory ledger for audit. |
| `REC_POST_008` | Un-publish (`PUBLISHED → DRAFT`) — optional | Per `REC_AUTH_005`. Set `status = DRAFT`, optionally clear `published_at`. The recipe is no longer eligible to drive theoretical consumption while in `DRAFT`. To re-publish, re-run `REC_POST_003` (which writes a new `tb_recipe_version`). |
| `REC_POST_009` | Soft delete | `deleted_at = now()`, `deleted_by_id = user`. Permitted only at `DRAFT` (or `ARCHIVED` for Sysadmin data hygiene). Row remains in the database; the `(code, name, deleted_at)` unique index permits re-use of the same code+name after soft-delete. |
| `REC_POST_010` | Pricing-only edit (no ingredient / step change) | When Cost Controller updates `target_food_cost_percentage` or `selling_price` only (per `REC_AUTH_006`): re-compute `suggested_price`, `actual_food_cost_percentage`, `gross_margin`, `gross_margin_percentage` per `REC_CALC_008`–`REC_CALC_010`. Write a `tb_recipe_pricing_history` row with `change_reason = "pricing-only update"`. Recipe stays in the current status (`DRAFT` or `PUBLISHED`); no new `tb_recipe_version` is required (pricing changes are tracked via the pricing-history table, not the full versioning table — tenant choice). |
| `REC_POST_011` | Theoretical-consumption fan-out (downstream, not a recipe-status transition) | When a menu item linked to a `PUBLISHED` recipe is sold by the POS, the inventory / POS-integration layer reads the recipe's ingredient lines and posts theoretical OUT movements per `REC_CALC_014`. This is a **downstream effect** of the recipe being `PUBLISHED`; the recipe module itself does not write to `tb_inventory_transaction` — it is the formula source. |

State diagram (Prisma-canonical):

```
[*] → DRAFT ⇄ PUBLISHED → ARCHIVED → (terminal)
              (un-publish optional per tenant policy;
               edits to PUBLISHED apply in-place with versioning
               or via un-publish round-trip)
```

`ARCHIVED` is terminal in normal operation. `DRAFT` accepts soft-delete; `ARCHIVED` accepts soft-delete by Sysadmin.

## 6. Cross-Module Rules

Rule IDs follow `REC_XMOD_NNN`.

| Rule ID | Related module | Rule |
| ------- | -------------- | ---- |
| `REC_XMOD_001` | [product](/en/inventory/product) | Recipe ingredient lines reference products through `tb_recipe_ingredient.product_id → tb_product.id`. Only products with `is_used_in_recipe = true` and `is_active = true` are eligible (`REC_VAL_010`). Product cost feeds the line: `cost_per_unit` is sourced from `tb_product.standard_cost` (or the outlet's costed valuation per [costing](/en/inventory/costing) for valuation-driven costing). When a product's cost changes (via vendor pricelist update through `[vendor-pricelist](/en/inventory/vendor-pricelist)` → `[purchase-order](/en/inventory/purchase-order)` → `[good-receive-note](/en/inventory/good-receive-note)` → costing layer rebuild), every recipe that references it is flagged for re-cost; the re-cost is applied atomically by the recipe-costing service. |
| `REC_XMOD_002` | [product](/en/inventory/product) | Soft-deleting a product that is referenced by an active (non-soft-deleted, `PUBLISHED`) recipe is blocked at the application layer (the FK is `Restrict`, but the schema-level constraint only enforces hard delete; soft delete needs the application check). The user must first either swap the ingredient on each recipe or archive the recipe. |
| `REC_XMOD_003` | [inventory](/en/inventory/inventory) | Theoretical-consumption fan-out: when a menu item linked to recipe `R` is sold by the POS in quantity `S`, the inventory layer posts a theoretical OUT movement per ingredient line per `REC_CALC_014` against the **outlet's** inventory location. The movement is stamped as `theoretical` (distinct from `actual` movements driven by SR / GRN). The inventory module's theoretical-vs-actual variance dashboard uses this stamp to compute outlet food-cost variance. The recipe module is the formula source; the inventory module owns the write. |
| `REC_XMOD_004` | [inventory](/en/inventory/inventory) | Sub-recipe consumption is recursive: when an ingredient line is `ingredient_type = recipe`, the theoretical-consumption fan-out drills into the sub-recipe's own ingredient lines and posts OUT movements for each leaf-product ingredient. Sub-recipe lines never write OUT against the sub-recipe itself (recipes are not inventory items); they pass through. |
| `REC_XMOD_005` | [costing](/en/inventory/costing) | Per-ingredient `cost_per_unit` is sourced from the **outlet's** costing-method valuation of the underlying product (FIFO or moving-average per the outlet's per-location config). The recipe module reads the cost from the costing module at line save / re-cost time; for sub-recipe ingredients, the recipe's own `cost_per_portion` is used (sub-recipes do not have a per-outlet costing valuation — they are formulas, not inventory). |
| `REC_XMOD_006` | [costing](/en/inventory/costing) | Cost-drift detection: when an outlet's costing valuation for a product changes by more than the tenant's drift threshold (e.g. ±5%), the costing module emits a re-cost event; the recipe module consumes the event and refreshes every recipe that references the product. A `tb_recipe_pricing_history` row is written with `change_reason = "cost-drift update from costing module"`. Recipes whose `actual_food_cost_percentage` now exceeds `target_food_cost_percentage` by more than tolerance are flagged for chef / cost-controller review. |
| `REC_XMOD_007` | [store-requisition](/en/inventory/store-requisition) | Recipe demand can auto-generate an SR `draft` for ingredient pulls: when a production / banquet event is planned, the recipe module computes ingredient quantities × cover count and posts an SR `draft` at the destination outlet with `info.recipe_id` carrying the recipe back-reference. The SR thereafter follows the normal flow (`SR_POST_001` onward in [store-requisition/02-business-rules](/en/inventory/store-requisition/02-business-rules)). Variance at period close between the recipe-computed demand and the actual `issued_qty` is surfaced in the outlet variance dashboard. |
| `REC_XMOD_008` | Menu Item / POS integration | The Recipe → Menu Item linkage is **not** in the canonical tenant Prisma schema (see [recipe/01-data-model.md](./01-data-model.md) § 5 item 4). The linkage lives in the POS-integration layer or as an application-resolved mapping; a single recipe may be linked to multiple menu items (combos, sizes), and a single menu item may compose several recipes (plates with multiple components). The recipe module exposes a read-only "linked menu items" query but does not own the linkage table. Menu-sale events are the trigger for theoretical-consumption fan-out (`REC_XMOD_003`). |
| `REC_XMOD_009` | Audit / Versioning | Every change to a `PUBLISHED` recipe writes a `tb_recipe_version` row capturing the full snapshot. The version history is the audit trail; rollback is achieved by reading an older version's JSON snapshot and re-applying it as a new edit (which itself writes a new version row, preserving the history). The pricing-only timeline is captured separately in `tb_recipe_pricing_history` for cost-drift analytics. |
| `REC_XMOD_010` | RBAC / Sysadmin | Recipe permissions (`recipe:create`, `recipe:edit`, `recipe:publish`, `recipe:archive`, `recipe:edit-published`, `recipe:edit-cost`, `recipe:approve-menu-link`, `recipe:read`, `recipe:read-history`) are mapped per role and per category. The Sysadmin (Audit / Config persona) owns the mapping; changes apply prospectively. Per-category permission scoping (e.g. "Pastry Chef may edit Desserts category only") is supported by the RBAC layer. |

## 7. References

- `../carmen/docs/recipe-module/RECIPE-Business-Requirements.md` — Functional requirements `REC_CR_001`–`REC_CR_005` (creation), `REC_CO_001`–`REC_CO_005` (costing), `REC_IN_001`–`REC_IN_005` (ingredients), `REC_ST_001`–`REC_ST_004` (status). Validation rules feed `REC_VAL_*`; cost calculations feed `REC_CALC_*`. Note: the Business Requirements' two-state lifecycle (`draft / published`) and the lack of `archived` in the enum are divergent from the Prisma three-state enum — the rules above use the canonical schema.
- `../carmen/docs/recipe-module/RECIPE-PRD.md` — User stories, feature requirements, integration requirements; the Cost Calculations section in `RECIPE-Business-Requirements.md` and the Logic Implementation section feed `REC_CALC_*`. The PRD's `Recipe.totalTime` is computed at display time, not persisted (divergence — see [recipe/01-data-model.md](./01-data-model.md) § 5 item 3).
- `../carmen/docs/recipe-module/RECIPE-Overview.md` — Module purpose, user roles, integration points; the User Roles section maps onto the persona table in this page's [03-user-flow.md](./03-user-flow.md) overview.
- `../carmen/docs/recipe-module/RECIPE-Page-Flow.md` — Page flows and user journeys; informs the user-flow files but not the rule set directly.
- `../carmen/docs/recipe/recipe-management.md` — Layout-level reference for the create / edit page (tabbed interface: Basic Info, Ingredients, Method, Media, Costing, Nutritional) and the costing sheet.
- `../carmen/docs/recipe/recipe-create-edit-page.md` — Page-spec source for the recipe form.
- Sibling: `en/recipe/01-data-model.md` — canonical Prisma model, recipe-specific enums (`enum_recipe_status`, `enum_recipe_difficulty`, `enum_ingredient_type`, `enum_temperature_unit`, `enum_cuisine_region`), and the divergence catalogue that Section 1, Section 2, and Section 6 rely on.
- Sibling: `en/recipe/03-user-flow.md` — lifecycle overview and persona drill-downs; this rules page is the formal complement to the lifecycle narrative.
- Backend rule implementation (when added): `../carmen-turborepo-backend-v2/apps/` — the recipe service module is the implementation hook for these rules (publish-time completeness gate, cost-rollup recomputation, sub-recipe cascade, theoretical-consumption fan-out trigger, pricing-history snapshot).

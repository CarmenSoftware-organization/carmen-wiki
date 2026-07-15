---
title: Recipe
description: Recipes (ingredient lists with yields) — the bridge between menu items and inventory consumption.
published: true
date: 2026-07-16T04:00:00.000Z
tags: recipe, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T07:48:00.000Z
---

# Recipe

> **At a Glance**
> **Module purpose:** Costed production-formula catalogue (header costing, sub-recipe references, prep-step API, image gallery) under `/operation-plan/*`; the target design extends this to theoretical consumption and food-cost variance against POS sales (not yet implemented — see status note below) &nbsp;·&nbsp; **Audience:** Chef / Kitchen Manager, Cost Controller, Outlet Manager, F&B Operations, Procurement &nbsp;·&nbsp; **Key entities/tables:** `tb_recipe`, `tb_recipe_ingredient`, `tb_recipe_preparation_step`, `tb_recipe_image`, `tb_recipe_yield_variant`, `tb_recipe_version`, `tb_recipe_pricing_history` &nbsp;·&nbsp; **Sub-pages:** 18

![Recipe screen](/screenshots/recipe/index.png)

![Recipe detail screen](/screenshots/recipe/detail.png)

> **Implementation status (verified against source 2026-07-15).** What is live today is a **header-level recipe catalogue**: list/detail/create/edit/delete at `/operation-plan/recipe` backed by `POST/PUT/PATCH/DELETE /api/config/{bu_code}/recipes` (gateway `config_recipes.controller.ts` → micro-business `recipe.service.ts`), plus recipe images (multipart gallery), preparation-step REST endpoints (`.../recipes/:recipe_id/preparation-steps` — API only, no UI in the recipe form yet), and the four master-data screens (category, cuisine, equipment, equipment category). The ingredient grid on the recipe form is explicitly **preview-only** ("Preview only — ingredients are not yet persisted with the recipe", `messages/en.json` `ingredientsPreviewNote`) and no ingredient write endpoint exists in the backend. `tb_recipe_version`, `tb_recipe_pricing_history`, and `tb_recipe_yield_variant` exist in the schema but no service writes them today. Menu-item linkage, theoretical consumption, POS explosion, food-cost variance, sub-recipe cost cascade, and recipe-driven store requisitions have **no code anywhere** in the frontend or backend — sections below describing them document the design concept from `../carmen/docs/`, not current behaviour.

## 1. Overview

A **Recipe** is the standardised, costed formula for producing a single output of food or beverage. Each recipe carries a header (recipe name and ID, category, cuisine type, course type, yield with quantity and unit, prep time, cook time, difficulty, allergens, tags, status) and one or more ingredient lines that specify the product or sub-recipe, the required quantity, recipe unit, stock unit, wastage percentage, unit cost, and total line cost. Preparation steps — ordered, optionally with images, durations, and equipment — sit alongside the ingredient list and make the recipe a complete production document rather than just a costing sheet. Recipes carry a three-state status (`DRAFT` / `PUBLISHED` / `ARCHIVED`, `enum_recipe_status`); the transition is a plain dropdown on the recipe toolbar (`recipe-toolbar.tsx`) with no completeness gate, and the backend auto-stamps `published_at` / `archived_at` on the transition (`recipe.service.ts`). Full change-versioning is a schema-level design (`tb_recipe_version`) with no writer implemented yet — the current audit trail is the standard `created_*` / `updated_*` columns plus `doc_version` optimistic locking.

Ingredients can be either **products** drawn from the inventory catalogue or **sub-recipes** — other published recipes used as components of a parent recipe (a "mother sauce" used in three mains, a pastry base used in two desserts); this is the `tb_recipe_ingredient` two-FK model (`product_id` / `sub_recipe_id` with `enum_ingredient_type` discriminator), and the one sub-recipe rule enforced in code today is the delete guard — a recipe referenced as a sub-recipe cannot be deleted (`RECIPE_USED_AS_SUB_RECIPE`, `recipe.service.ts`). The automatic parent re-cost when a sub-recipe's cost changes is a design goal with no implementation yet. Recipes are deliberately distinct from **menu items**: a recipe is the production formula and the source of truth for cost; a menu item is the sellable POS entry, which links to one or more recipes (and to add-ons, modifiers, and pricing). One recipe can underpin multiple menu items (a single "House Burger" recipe sold as both a single and a combo); one menu item can compose several recipes (a "Steak Plate" combining a steak recipe, a sauce sub-recipe, and a side recipe).

In the target design (`../carmen/docs/recipe-module/`), recipes are the bridge between menu sales and inventory consumption: when a menu item is sold, the system explodes each linked recipe by the sold quantity, multiplies through the ingredient lines (applying wastage and unit conversion), and posts the resulting **theoretical consumption** as stock OUT movements against the outlet's inventory, driving food-cost reporting, theoretical-vs-actual variance analysis, and recipe-generated store requisitions. **None of this pipeline exists in code today** — there is no menu-item table, no POS integration, no theoretical-consumption write, and no recipe→SR generation anywhere in `carmen-turborepo-backend-v2` or the frontend; the recipe module currently ends at the costed formula record itself.

## 2. Business Context

In a hospitality operation, the recipe is the single artifact that ties together what the kitchen produces, what it costs, and what inventory it consumes. Without standardised recipes, three things break: kitchen staff prepare the same dish differently across shifts and outlets, leading to inconsistent quality and portioning; cost per portion is unknowable, so menu pricing becomes guesswork and margins erode; and inventory cannot be deducted against sales, so food-cost variance reports are meaningless. Standardised, costed recipes are the foundation that lets the F&B operation run on numbers rather than intuition.

The module is built around **food cost engineering** — the discipline of designing each dish to hit a target food-cost percentage while preserving quality, presentation, and consistency. Cost controllers set a target food-cost percentage (commonly 28–35% for casual dining, lower for fine dining), the system computes the recommended selling price from `Cost Per Portion / (1 − Target Food Cost%)`, and the gross margin falls out as `(Selling Price − Cost Per Portion) / Selling Price`. As ingredient prices move — driven by procurement updates from vendor pricelists and GRN postings — the recipe re-costs in real time, surfacing dishes whose margin has drifted outside tolerance and flagging them for review before the next menu refresh.

The other major business function the module supports is **theoretical vs. actual variance analysis**. Theoretical consumption is what the recipes say should have been used to produce the day's sales (POS sales × recipe ingredient lines × wastage). Actual consumption is what physical-count and store-requisition data show was actually drawn from inventory. The variance between the two is the operation's single most important food-cost KPI: a persistent positive variance points to over-portioning, theft, spoilage, or sub-recipe inaccuracy; a persistent negative variance points to recipe error or under-portioning. Recipe accuracy — yield, wastage, unit conversion — is therefore not just a kitchen concern but a financial-control concern. (This whole variance function is design-stage: no variance computation, POS feed, or theoretical-consumption write exists in the current codebase — see the implementation-status note above.)

## 3. Key Concepts

- **Recipe Header**: The top-level metadata for a recipe — code, name, description, note, category, cuisine, yield (`base_yield` + `base_yield_unit`), prep time, cook time, difficulty (`EASY`/`MEDIUM`/`HARD`), allergens, tags, status (`DRAFT`/`PUBLISHED`/`ARCHIVED`), primary image (via `tb_recipe_image`), carbon footprint, and `deduct_from_stock` flag. There is no `course_type` and no persisted `total_time` in the schema. The header is what appears in the recipe library, drives filtering and search (status, cuisine, category, difficulty filters on the list screen), and carries the cost/pricing figures (cost per portion, selling price, gross margin) for the recipe as a whole.
- **Ingredient**: A line item on the recipe that specifies what goes into the dish. In the schema (`tb_recipe_ingredient`), each ingredient has a type (`product` for an inventory item or `recipe` for a sub-recipe), a quantity, a recipe unit, a stock unit, a conversion factor between the two, a wastage percentage, a unit cost, and computed `net_cost` / `wastage_cost`. **No write path exists for this table today** — the recipe form's ingredient grid is a preview-only local table (name, qty, unit, cost, yield %, prep notes) that is not sent with the save payload, and no ingredient endpoint exists in the gateway or Bruno collections.
- **Sub-Recipe (Recipe-as-Ingredient)**: A published recipe used as an ingredient in another recipe — a mother sauce, a stock, a pastry base, a spice mix — via `tb_recipe_ingredient.sub_recipe_id`. The delete guard is implemented (`RECIPE_USED_AS_SUB_RECIPE`); the automatic parent re-cost on sub-recipe cost change is design-stage only.
- **Yield**: The output quantity that one execution of the recipe produces, expressed as a number plus a unit (`base_yield` + `base_yield_unit`, e.g. `12 portions`, `2.5 kg`). Yield drives cost-per-portion (`Total Cost / Yield` — computed client-side in `use-recipe-cost-calc.ts`). There is no scaling calculator and no initial/after-prep/recovery-% field in the current schema or UI.
- **Wastage Percentage**: The trim, peel, evaporation, or spillage loss expected per ingredient, expressed as a percentage. Net cost per ingredient is `Unit Cost × Quantity × (1 + Wastage%)`. Wastage is a per-line setting because different ingredients have very different waste profiles — a whole salmon is 60% usable, a bag of flour is 100% usable — and rolling it up by ingredient is the only way recipe cost reflects reality.
- **Recipe Cost (Total / Per Portion)**: In the current form, `total_ingredient_cost`, `labor_cost`, and `overhead_cost` are **manually-entered** header fields (`recipe-cost-breakdown.tsx`); the form computes **Cost Per Portion** as `(total_ingredient_cost + labor_cost + overhead_cost) / base_yield` client-side (`use-recipe-cost-calc.ts`) and stores the result. There is no automatic re-cost from catalogue price changes — the ingredient grid does not feed `total_ingredient_cost`.
- **Target Food Cost % and Selling Price**: The target food-cost percentage is set per recipe or per category (commonly 28–35% in casual dining). The **Recommended Selling Price** is `Cost Per Portion / (1 − Target Food Cost%)`. Actual selling price may differ (e.g. for menu-pricing strategy, competitor matching), and the system tracks both alongside the resulting **Gross Margin %** = `(Selling Price − Cost Per Portion) / Selling Price × 100`.
- **Preparation Step**: An ordered instruction in the method (`tb_recipe_preparation_step`) with `sequence_no`, optional `title`, required `description`, optional `duration`, `temperature` + unit, `equipment` / `techniques` JSON arrays, `chef_notes`, `safety_warnings`, and images via `tb_recipe_preparation_step_image`. Full REST CRUD + reorder + image endpoints exist (`.../recipes/:recipe_id/preparation-steps`), but the recipe form has no step-editing UI yet — steps are API-only today.
- **Theoretical Consumption** *(design concept — not implemented)*: The inventory the menu's sales *should have* drawn down based on recipes, computed as `Σ over sold menu items (sold_qty × recipe_ingredient_qty × (1 + wastage%) × unit_conversion)`. No POS feed or theoretical OUT write exists in code.
- **Actual Consumption** *(design concept for the variance pairing)*: The inventory the kitchen actually drew down, derived from physical-count posts, store requisitions, and direct issues — these movements are real in the [inventory](/en/inventory/inventory) module, but no recipe-side variance comparison consumes them.
- **Variance (Theoretical − Actual)** *(design concept — not implemented)*: The gap between what recipes say was used and what stock movement says was used. No variance computation or report exists in the current codebase.
- **Menu Item Linkage** *(design concept — not implemented)*: The mapping from POS-sellable menu items to recipes. There is no menu-item table in the tenant schema and no linkage code.
- **Version History** *(schema only)*: `tb_recipe_version` models full snapshots (`recipe_data`, `ingredients_data`, `steps_data`, `variants_data`, `change_summary`), but no service writes or reads it today. The live audit trail is `created_*` / `updated_*` columns and `doc_version` optimistic locking.
- **Status Lifecycle (`DRAFT` / `PUBLISHED` / `ARCHIVED`)**: Recipes start in `DRAFT` (backend default). The status is a free dropdown on the toolbar — the backend applies **no completeness gate** on the transition; it only auto-stamps `published_at` when status changes to `PUBLISHED` and `archived_at` when it changes to `ARCHIVED` (`recipe.service.ts` `update()`/`patch()`).
- **Category and Cuisine Type**: Categorical master data used to organise the recipe library — `Category` (hierarchical, e.g. Appetiser, Main, Dessert) and `Cuisine` (flat, region-tagged, e.g. Thai, Italian, French). Both are required FKs on the recipe header. Categories carry `default_cost_settings` / `default_margins` JSON intended to seed new recipes.
- **Allergens and Tags**: Per-recipe JSON arrays. The form offers a standard allergen checklist (`ALLERGEN_OPTIONS` in `constant/recipe.ts`) plus free-text custom allergens, and free-text tags.
- **Stock Deduction Setting**: A single boolean `deduct_from_stock` on the header (default `true`), edited as a switch on the form's hero section. The richer deduct-on-sale/production/issue policy matrix described in carmen/docs does not exist in the schema.
- **Carbon Footprint**: A per-recipe manually-entered decimal (`carbon_footprint`, default 0). No per-ingredient footprint rollup exists.

## 4. Roles and Personas

| Role | Responsibility |
|------|----------------|
| Chef / Kitchen Manager | Creates new recipes and revises existing ones — defines ingredients, quantities, wastage, method, yield, equipment, prep and cook times. Maintains sub-recipes and ensures consistency across outlets. Approves recipe publication and revisions, and sets standards for plating, portioning, and quality. |
| Cost Controller | Reviews recipe cost, target food-cost percentage, recommended selling price, and gross margin. Monitors cost drift as ingredient prices move, flags recipes whose margin has fallen outside tolerance, signs off on recipe-cost changes that affect menu pricing, and runs theoretical-vs-actual variance reports. |
| Outlet Manager | Orders ingredients from the central store against recipe demand (often via auto-generated store requisitions sized by forecast sales × recipes). Monitors outlet food-cost variance against budget, reviews recipes used in the outlet, and feeds back portion-control or recipe-accuracy issues to the chef. |
| Kitchen Staff | Reads published recipes during service — follows ingredient list, method, equipment, and plating to prepare dishes consistently. May report on recipe execution and flag inaccuracies (wrong quantity, missing step) back to the chef. Accesses recipes on mobile devices in the kitchen. |
| Cost Control Department | Owns the recipe-costing process at portfolio level — sets category-level target food-cost percentages, reconciles outlet variance to the GL, runs monthly cost reviews, and drives the recipe-versioning approval workflow when ingredient prices materially shift. |
| Procurement Department | Consumes recipe demand to inform purchasing — uses recipe explosions × forecast sales to size purchase orders and validate that ingredient availability matches recipe needs. Receives substitution requests when an ingredient cannot be sourced. |
| F&B Operations Manager | Owns the recipe library at the strategic level — approves new menu items and their recipe linkages, signs off on menu engineering against margin and variance data, and ensures recipe documentation supports training and audit. |
| System Administrator | Manages recipe-module configuration — categories, cuisine types, default cost settings, role-based permissions for recipe creation/editing/approval, and integration settings with inventory, POS, and procurement. |

> **RBAC reality check:** the current frontend gates the entire `/operation-plan/*` group behind a single frontend-only placeholder permission `operation_plan.view` (`constant/permissions.ts` — commented "BE catalog ยังไม่มี operation_plan namespace"), which in practice means admin-only access to every recipe screen. None of the per-role capabilities in this table (publish approval, cost sign-off, read-only outlet access) is distinguished by any permission check today; the table documents the target operating model from `../carmen/docs/`.

## 5. Related Modules

**Cross-module flow:**
- [product](/en/inventory/product) — recipe ingredient lines reference products in the schema (`tb_recipe_ingredient.product_id`); no live write path yet
- [inventory](/en/inventory/inventory) — target design: recipe usage drives inventory OUT movements (theoretical consumption — not implemented)
- [costing](/en/inventory/costing) — target design: recipe cost sourced from costed ingredient valuations (currently manually entered on the header)
- [store-requisition](/en/inventory/store-requisition) — target design: recipes auto-generate requisitions (no such code exists)

**Master configuration:**
- [master-data/unit](/en/inventory/master-data/unit) — recipe and stock units of measure plus conversion factor per ingredient
- [master-data/currency](/en/inventory/master-data/currency) — recipe cost and selling price expressed in the property's base currency
- [system-config/application-config](/en/inventory/system-config/application-config) — tenant-level defaults (target food-cost %, rounding, status policy)
- [reporting-audit/activity](/en/inventory/reporting-audit/activity) — recipe create/update/delete events in the shared activity log
- [reporting-audit/attachment](/en/inventory/reporting-audit/attachment) — recipe gallery images (`tb_recipe_image`) and step photos (`tb_recipe_preparation_step_image`) via file tokens

## 6. Reference Sources

- Concepts (PRD/requirements): `../carmen/docs/recipe-module/`
- Concepts (UI/page specs): `../carmen/docs/recipe/`
- Frontend: `../carmen-inventory-frontend-react/`
- Backend: `../carmen-turborepo-backend-v2/`
- API contracts: `../carmen-turborepo-backend-bruno/`
- E2E tests: `../carmen-inventory-frontend-e2e/`

## 7. Pages in This Module

- [01 — Data Model](/en/inventory/recipe/01-data-model) — Prisma entities (`tb_recipe`, `tb_recipe_ingredient`, `tb_recipe_preparation_step`, `tb_recipe_yield_variant`, `tb_recipe_version`, `tb_recipe_pricing_history`, `tb_recipe_category`, `tb_recipe_cuisines`, equipment masters), enums (`enum_recipe_status`, `enum_recipe_difficulty`, `enum_ingredient_type`, `enum_temperature_unit`, `enum_cuisine_region`), relationships (sub-recipe self-relation, two-unit ingredient model), and divergences from carmen/docs.
- [02 — Business Rules](/en/inventory/recipe/02-business-rules) — Validation (`REC_VAL_*`), calculation (`REC_CALC_*`, line → recipe → portion → price → margin chain, sub-recipe cascade), authorization (`REC_AUTH_*`), posting (`REC_POST_*`, publish / edit-published / cascade / archive events), and cross-module rules (`REC_XMOD_*`).
- [03 — User Flow](/en/inventory/recipe/03-user-flow) — Recipe lifecycle overview and persona-specific flow files:
  - [Chef](/en/inventory/recipe/03-user-flow-chef) — Chef / Kitchen Manager (+ Kitchen Staff read-only): creates, revises, publishes, archives.
  - [Cost Controller](/en/inventory/recipe/03-user-flow-cost-controller) — Cost Controller (+ Cost Control Department): reviews cost, signs off, monitors drift, runs variance.
  - [Outlet Manager](/en/inventory/recipe/03-user-flow-outlet-manager) — Outlet Manager: demand-side consumer, raises SRs from recipe demand, feeds back issues.
  - [Procurement / F&B Ops](/en/inventory/recipe/03-user-flow-procurement-fb-ops) — Procurement (PO sizing, substitution) + F&B Ops (menu-item linkage approval, menu engineering).
  - [Audit / Config](/en/inventory/recipe/03-user-flow-audit-config) — Sysadmin (config, RBAC, tenant policy, integration) + Auditor (read-only versioning trace).
- [04 — Test Scenarios](/en/inventory/recipe/04-test-scenarios) — Cross-persona scenarios + E2E coverage status (no dedicated `recipe.spec.ts`; the module's only E2E spec is `121-recipe-equipment-category.spec.ts`), with per-persona drill-downs:
  - [Chef scenarios](/en/inventory/recipe/04-test-scenarios-chef)
  - [Cost Controller scenarios](/en/inventory/recipe/04-test-scenarios-cost-controller)
  - [Outlet Manager scenarios](/en/inventory/recipe/04-test-scenarios-outlet-manager)
  - [Procurement / F&B Ops scenarios](/en/inventory/recipe/04-test-scenarios-procurement-fb-ops)
  - [Audit / Config scenarios](/en/inventory/recipe/04-test-scenarios-audit-config)
- Master-data sub-pages (Operation Plan setup screens):
  - [Recipe Category](/en/inventory/recipe/category) — hierarchical taxonomy (`tb_recipe_category`), `/operation-plan/category`.
  - [Cuisine](/en/inventory/recipe/cuisine) — flat region-tagged catalogue (`tb_recipe_cuisines`), `/operation-plan/cuisine`.
  - [Equipment](/en/inventory/recipe/equipment) — kitchen equipment master (`tb_recipe_equipment`), `/operation-plan/equipment`.
  - [Equipment Category](/en/inventory/recipe/equipment-category) — flat equipment grouping (`tb_recipe_equipment_category`), `/operation-plan/equipment-category` (plus a duplicate `/operation-plan/recipe-equipment-category` screen against the same table).

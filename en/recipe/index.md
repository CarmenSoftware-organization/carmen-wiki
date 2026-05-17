---
title: Recipe
description: Recipes (ingredient lists with yields) — the bridge between menu items and inventory consumption.
published: true
date: 2026-05-17T07:00:16.000Z
tags: recipe, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T07:48:00.000Z
---

# Recipe

> **At a Glance**
> **Module purpose:** Costed, versioned production formulas (with sub-recipes, yield, wastage, prep steps) that drive theoretical consumption and food-cost variance against POS sales &nbsp;·&nbsp; **Audience:** Chef / Kitchen Manager, Cost Controller, Outlet Manager, F&B Operations, Procurement &nbsp;·&nbsp; **Key entities/tables:** `tb_recipe`, `tb_recipe_ingredient`, `tb_recipe_preparation_step`, `tb_recipe_yield_variant`, `tb_recipe_version`, `tb_recipe_pricing_history` &nbsp;·&nbsp; **Sub-pages:** 18

![Recipe screen](/screenshots/recipe/index.png)

## 1. Overview

A **Recipe** is the standardised, costed formula for producing a single output of food or beverage. Each recipe carries a header (recipe name and ID, category, cuisine type, course type, yield with quantity and unit, prep time, cook time, difficulty, allergens, tags, status) and one or more ingredient lines that specify the product or sub-recipe, the required quantity, recipe unit, stock unit, wastage percentage, unit cost, and total line cost. Preparation steps — ordered, optionally with images, durations, and equipment — sit alongside the ingredient list and make the recipe a complete production document rather than just a costing sheet. Recipes progress through a controlled status lifecycle (`Draft` → `Published`) and are version-controlled so every change to ingredients, quantities, method, or costing is captured with timestamp and user for audit.

Ingredients can be either **products** drawn from the inventory catalogue or **sub-recipes** — other published recipes used as components of a parent recipe (a "mother sauce" used in three mains, a pastry base used in two desserts). Sub-recipes let the kitchen build complex dishes from reusable, costed building blocks: when the sub-recipe's ingredient costs change, every parent recipe that references it re-costs automatically. Recipes are deliberately distinct from **menu items**: a recipe is the production formula and the source of truth for cost; a menu item is the sellable POS entry, which links to one or more recipes (and to add-ons, modifiers, and pricing). One recipe can underpin multiple menu items (a single "House Burger" recipe sold as both a single and a combo); one menu item can compose several recipes (a "Steak Plate" combining a steak recipe, a sauce sub-recipe, and a side recipe).

Recipes are the bridge between menu sales and inventory consumption. When a menu item is sold, the system explodes each linked recipe by the sold quantity, multiplies through the ingredient lines (applying wastage and unit conversion), and posts the resulting **theoretical consumption** as stock OUT movements against the outlet's inventory. This drives food-cost reporting per outlet, variance analysis (theoretical vs. actual), and downstream replenishment — recipes can auto-generate store requisitions for the ingredients needed to meet forecast production.

## 2. Business Context

In a hospitality operation, the recipe is the single artifact that ties together what the kitchen produces, what it costs, and what inventory it consumes. Without standardised recipes, three things break: kitchen staff prepare the same dish differently across shifts and outlets, leading to inconsistent quality and portioning; cost per portion is unknowable, so menu pricing becomes guesswork and margins erode; and inventory cannot be deducted against sales, so food-cost variance reports are meaningless. Standardised, costed recipes are the foundation that lets the F&B operation run on numbers rather than intuition.

The module is built around **food cost engineering** — the discipline of designing each dish to hit a target food-cost percentage while preserving quality, presentation, and consistency. Cost controllers set a target food-cost percentage (commonly 28–35% for casual dining, lower for fine dining), the system computes the recommended selling price from `Cost Per Portion / (1 − Target Food Cost%)`, and the gross margin falls out as `(Selling Price − Cost Per Portion) / Selling Price`. As ingredient prices move — driven by procurement updates from vendor pricelists and GRN postings — the recipe re-costs in real time, surfacing dishes whose margin has drifted outside tolerance and flagging them for review before the next menu refresh.

The other major business function the module supports is **theoretical vs. actual variance analysis**. Theoretical consumption is what the recipes say should have been used to produce the day's sales (POS sales × recipe ingredient lines × wastage). Actual consumption is what physical-count and store-requisition data show was actually drawn from inventory. The variance between the two is the operation's single most important food-cost KPI: a persistent positive variance points to over-portioning, theft, spoilage, or sub-recipe inaccuracy; a persistent negative variance points to recipe error or under-portioning. Recipe accuracy — yield, wastage, unit conversion — is therefore not just a kitchen concern but a financial-control concern, which is why every recipe change is versioned and approved.

## 3. Key Concepts

- **Recipe Header**: The top-level metadata for a recipe — name, ID, description, category, cuisine type, course type, yield, yield unit, prep time, cook time, total time, difficulty, allergens, tags, status (`draft` / `published`), main image, carbon footprint. The header is what appears in the recipe library, drives filtering and search, and carries the rolled-up cost figures (cost per portion, selling price, gross margin) for the recipe as a whole.
- **Ingredient**: A line item on the recipe that specifies what goes into the dish. Each ingredient has a type (`product` for an inventory item or `recipe` for a sub-recipe), a quantity, a recipe unit, a stock unit, a conversion factor between the two, a wastage percentage, a unit cost, and a computed total cost. Ingredients can be grouped into sections or components (e.g. "Sauce", "Garnish", "Plate") for readability and modular costing.
- **Sub-Recipe (Recipe-as-Ingredient)**: A published recipe used as an ingredient in another recipe — a mother sauce, a stock, a pastry base, a spice mix. Sub-recipes let the kitchen build complex dishes from reusable costed components; when the sub-recipe's ingredient costs change, every parent recipe re-costs automatically. This avoids duplicating ingredient lists and keeps cost data consistent across the menu.
- **Yield**: The output quantity that one execution of the recipe produces, expressed as a number plus a unit (e.g. `12 portions`, `2.5 kg`, `30 pieces`). Yield drives cost-per-portion (`Total Cost / Yield`), scaling (the scaling calculator multiplies all ingredients by a factor to hit a new yield), and inventory deduction. Yield includes an optional initial vs. after-prep quantity, expected loss %, and recovery % for accurate yield analysis.
- **Wastage Percentage**: The trim, peel, evaporation, or spillage loss expected per ingredient, expressed as a percentage. Net cost per ingredient is `Unit Cost × Quantity × (1 + Wastage%)`. Wastage is a per-line setting because different ingredients have very different waste profiles — a whole salmon is 60% usable, a bag of flour is 100% usable — and rolling it up by ingredient is the only way recipe cost reflects reality.
- **Recipe Cost (Total / Per Portion)**: Two figures roll up from the ingredient grid. **Total Recipe Cost** is `Σ(Ingredient Cost × (1 + Wastage%)) + Labor Cost + Overhead Cost`. **Cost Per Portion** is `Total Recipe Cost / Yield`. These re-compute in real time as ingredient prices change in the inventory catalogue, so the recipe library always reflects current cost.
- **Target Food Cost % and Selling Price**: The target food-cost percentage is set per recipe or per category (commonly 28–35% in casual dining). The **Recommended Selling Price** is `Cost Per Portion / (1 − Target Food Cost%)`. Actual selling price may differ (e.g. for menu-pricing strategy, competitor matching), and the system tracks both alongside the resulting **Gross Margin %** = `(Selling Price − Cost Per Portion) / Selling Price × 100`.
- **Preparation Step**: An ordered instruction in the method, with `order`, `description`, optional `duration`, optional list of required `equipment`, and optional step `image`. Steps are reorderable, and the full step sequence forms the production document used by kitchen staff. Critical control points (food-safety checkpoints) can be flagged on individual steps for HACCP compliance.
- **Theoretical Consumption**: The inventory the menu's sales *should have* drawn down based on recipes. Computed as `Σ over sold menu items (sold_qty × recipe_ingredient_qty × (1 + wastage%) × unit_conversion)`. Posted as theoretical stock OUT movements per outlet per ingredient, this is the demand-side number for the food-cost variance equation.
- **Actual Consumption**: The inventory the kitchen actually drew down, derived from physical-count posts, store requisitions, and direct issues. The supply-side number for variance.
- **Variance (Theoretical − Actual)**: The gap between what recipes say was used and what stock movement says was used. Positive variance (theoretical < actual) means over-consumption — over-portioning, theft, spoilage, or sub-recipe inaccuracy. Negative variance means recipes overstate consumption — under-portioning or recipe error. Variance reporting per ingredient per outlet is the operation's most important food-cost KPI.
- **Menu Item Linkage**: The mapping from POS-sellable menu items to one or more recipes. One recipe can underpin multiple menu items (combos, sizes); one menu item can compose several recipes (a plate combining a main, a sauce sub-recipe, and a side). The linkage is what lets POS sales fire recipe explosions and drive theoretical consumption.
- **Version History**: Every change to a recipe (ingredient added/removed, quantity changed, method edited, cost recalculated, status transition) writes a new version with timestamp, user, change log, and prior values. Old versions remain readable for audit and rollback, and the recipe library shows the current version pointer.
- **Status Lifecycle (Draft / Published)**: Recipes start in `draft` (editable, not yet usable in production or menu-item linkage). Transition to `published` requires all required fields complete, at least one ingredient, at least one prep step, and cost calculations valid. Only published recipes can be linked to menu items and drive theoretical consumption.
- **Category and Cuisine Type**: Categorical master data used to organise the recipe library — `Category` (e.g. Appetiser, Main, Dessert, Beverage), `Cuisine Type` (e.g. Thai, Italian, French), `Course Type`. Categories may carry defaults (target food-cost %, required attributes) that new recipes in the category inherit.
- **Allergens and Tags**: Per-recipe declarations used for guest safety (gluten, dairy, nuts, shellfish, etc.) and for filtering / dietary searches (vegan, vegetarian, halal, kosher). Allergens roll up to menu-item display for front-of-house and printed menus.
- **Stock Deduction Settings**: Per-recipe configuration that controls how the recipe drives inventory: whether to deduct on sale, on production, or on store-requisition issuance; whether to deduct ingredients or only the produced sub-recipe; and how to handle unit conversions between recipe units and stock units.
- **Carbon Footprint**: A per-recipe environmental-impact score computed from ingredient footprints, supporting sustainability reporting and menu engineering against climate KPIs.

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

## 5. Related Modules

**Cross-module flow:**
- [[product]] — recipe ingredients reference products
- [[inventory]] — recipe usage drives inventory OUT movements (theoretical consumption)
- [[costing]] — recipe cost is the sum of costed ingredient quantities
- [[store-requisition]] — recipes may auto-generate requisitions

**Master configuration:**
- [[master-data/unit]] — recipe and stock units of measure plus conversion factor per ingredient
- [[master-data/currency]] — recipe cost and selling price expressed in the property's base currency
- [[system-config/application-config]] — tenant-level defaults (target food-cost %, rounding, status policy)
- [[reporting-audit/activity]] — recipe version-history, publish, and cost-change log for audit
- [[reporting-audit/attachment]] — recipe images and step photos attached to each recipe

## 6. Reference Sources

- Concepts (PRD/requirements): `../carmen/docs/recipe-module/`
- Concepts (UI/page specs): `../carmen/docs/recipe/`
- Frontend: `../carmen-inventory-frontend/`
- Backend: `../carmen-turborepo-backend-v2/`
- API contracts: `../carmen-turborepo-backend-bruno/`
- E2E tests: `../carmen-inventory-frontend-e2e/`

## 7. Pages in This Module

- [01 — Data Model](./01-data-model.md) — Prisma entities (`tb_recipe`, `tb_recipe_ingredient`, `tb_recipe_preparation_step`, `tb_recipe_yield_variant`, `tb_recipe_version`, `tb_recipe_pricing_history`, `tb_recipe_category`, `tb_recipe_cuisines`, equipment masters), enums (`enum_recipe_status`, `enum_recipe_difficulty`, `enum_ingredient_type`, `enum_temperature_unit`, `enum_cuisine_region`), relationships (sub-recipe self-relation, two-unit ingredient model), and divergences from carmen/docs.
- [02 — Business Rules](./02-business-rules.md) — Validation (`REC_VAL_*`), calculation (`REC_CALC_*`, line → recipe → portion → price → margin chain, sub-recipe cascade), authorization (`REC_AUTH_*`), posting (`REC_POST_*`, publish / edit-published / cascade / archive events), and cross-module rules (`REC_XMOD_*`).
- [03 — User Flow](./03-user-flow.md) — Recipe lifecycle overview and persona-specific flow files:
  - [Chef](./03-user-flow-chef.md) — Chef / Kitchen Manager (+ Kitchen Staff read-only): creates, revises, publishes, archives.
  - [Cost Controller](./03-user-flow-cost-controller.md) — Cost Controller (+ Cost Control Department): reviews cost, signs off, monitors drift, runs variance.
  - [Outlet Manager](./03-user-flow-outlet-manager.md) — Outlet Manager: demand-side consumer, raises SRs from recipe demand, feeds back issues.
  - [Procurement / F&B Ops](./03-user-flow-procurement-fb-ops.md) — Procurement (PO sizing, substitution) + F&B Ops (menu-item linkage approval, menu engineering).
  - [Audit / Config](./03-user-flow-audit-config.md) — Sysadmin (config, RBAC, tenant policy, integration) + Auditor (read-only versioning trace).
- [04 — Test Scenarios](./04-test-scenarios.md) — Cross-persona scenarios + E2E coverage status (no dedicated `recipe.spec.ts` yet), with per-persona drill-downs:
  - [Chef scenarios](./04-test-scenarios-chef.md)
  - [Cost Controller scenarios](./04-test-scenarios-cost-controller.md)
  - [Outlet Manager scenarios](./04-test-scenarios-outlet-manager.md)
  - [Procurement / F&B Ops scenarios](./04-test-scenarios-procurement-fb-ops.md)
  - [Audit / Config scenarios](./04-test-scenarios-audit-config.md)

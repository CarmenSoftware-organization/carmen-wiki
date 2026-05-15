---
title: Recipe — Test Scenarios — Outlet Manager
description: Outlet Manager's test cases (read-only consumption, demand explosion, variance, feedback) for the recipe module.
published: true
date: 2026-05-15T16:00:00.000Z
tags: recipe, test-scenarios, outlet-manager, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T16:00:00.000Z
---

# Recipe — Test Scenarios — Outlet Manager

This page captures the test scenarios that the Outlet Manager persona directly drives in the `recipe` module. The Outlet Manager is **read-only on the recipe library** (`recipe:read` per `REC_AUTH_009`); the persona's interaction with the recipe is downstream — using recipe explosions to plan ingredient pulls, monitoring outlet variance driven in part by recipe accuracy, and feeding back portion-control / accuracy issues for the Chef to revise. Scenarios are grouped into **happy paths** (read recipe detail in outlet view; planned-production explosion; auto-create SR from recipe demand; outlet variance review; recipe-feedback submission), **RBAC** (Outlet Manager attempting any write; cross-outlet read scope), **validation** (negative tests around forecast accuracy, demand-zero recipes), and **edge cases** around banquet-event demand, par-level top-up patterns, multi-outlet recipe usage. Cross-persona handoffs that pivot off the Outlet Manager (Scenarios 5, 6 in the parent overview) live in [04-test-scenarios.md](./04-test-scenarios.md), not here.

## 1. Happy Path

| # | Scenario | Pre-condition | Steps | Expected |
| - | -------- | ------------- | ----- | -------- |
| OM-HP-01 | Read `PUBLISHED` recipe detail at outlet | Recipe `House Burger` is `PUBLISHED`; Outlet Manager has `recipe:read` scoped to recipes used in outlet `Main-Kitchen`. | 1. Outlet Manager opens recipe library filtered to outlet. 2. Searches for `House Burger`. 3. Opens recipe detail. 4. Reviews ingredient list, method, equipment, plating, yield. | Recipe detail displays in read-only mode; all fields visible (ingredients with quantities, method steps with media, yield, allergens, tags, cost figures); no edit controls; UI reflects `recipe:read` scope. Kitchen Staff sub-role has the same surface for service execution. |
| OM-HP-02 | Demand explosion for daily production | Outlet has forecast for tomorrow: 50 House Burger + 30 Caesar Salad + 20 Pasta Carbonara; each linked to one `PUBLISHED` recipe. | 1. Open production planning view for outlet. 2. Trigger demand explosion. 3. System reads recipe ingredient lines × forecast quantities per `REC_CALC_014`; aggregates per product. 4. Display pull list (one row per product, total qty in stock UoM, current on-hand at outlet, net demand). | Demand explosion aggregates ingredient quantities correctly across recipes; sub-recipe lines recurse to leaf products per `REC_XMOD_004`; wastage applied; UoM conversion applied; net demand = projected − on-hand − reserved. Pull list is the basis for SR creation. |
| OM-HP-03 | Auto-create SR `draft` from banquet event demand | Outlet has a banquet event booked for 200 covers next Friday; menu items linked to 4 `PUBLISHED` recipes; tenant has auto-create wiring enabled per `REC_XMOD_007`. | 1. Banquet event details persisted with cover count, menu items, recipe linkages. 2. Recipe module computes ingredient demand × 200 covers. 3. Recipe module posts an SR `draft` at outlet `Main-Kitchen` against source `Central Store` with `info.recipe_id = "EVENT-2026-05-22-001"`. 4. Outlet Manager opens the SR draft, reviews quantities, adjusts, and submits. | SR `draft` created with computed ingredient quantities; `info.recipe_id` preserved end-to-end; Outlet Manager flow continues per [[store-requisition]] (`SR_POST_001` onward); variance at period close against the recipe-computed demand surfaces in the outlet variance dashboard. |
| OM-HP-04 | Outlet variance review | All `PUBLISHED` recipes used in outlet `Main-Kitchen` drove theoretical OUT movements during period `2026-05`; SR / physical-count / adjustment posted actual movements. | 1. Open outlet variance dashboard. 2. Filter to outlet `Main-Kitchen`, period `2026-05`. 3. View per-ingredient theoretical vs actual; sort by variance amount. 4. Drill into largest variances. | Dashboard surfaces per-ingredient variance for the outlet; per-recipe drill-down (which recipe contributed to which variance); per-ingredient drill-down (which product had over/under consumption). Outlet Manager assesses whether variance is portion-control (own action) or recipe-attributable (escalate to Chef). |
| OM-HP-05 | Submit recipe-feedback to Chef | Outlet Manager observes persistent positive variance on `Premium Steak` (kitchen plating 250g, recipe specifies 220g). | 1. Open `Premium Steak` recipe in read-only mode. 2. Click **Submit Feedback** (feedback channel — UI varies; outside the recipe schema). 3. Enter: "Persistent variance on steak portion — kitchen plating 250g vs recipe 220g. Either revise recipe to 250g or reinforce 220g plating with kitchen staff." 4. Submit. | Feedback logged in operational channel (in-app comment, ticket, or notification); Chef receives the feedback; the recipe is unchanged from Outlet Manager's action (chef may subsequently revise per `REC_POST_004`); Outlet Manager monitors next-period variance for resolution. |

## 2. Permission / Authorization

| # | Scenario | Expected behaviour (allow/deny + reason) |
| - | -------- | --------------------------------------- |
| OM-PERM-01 | Outlet Manager reads `PUBLISHED` recipes used in outlet | **Allow.** Per `REC_AUTH_009`. UI shows recipe detail in read-only mode. |
| OM-PERM-02 | Outlet Manager attempts to edit recipe header / ingredients / steps | **Deny — read-only.** All edit endpoints reject with `"Outlet Manager role is read-only on the recipe library; submit feedback to the Chef instead."` |
| OM-PERM-03 | Outlet Manager attempts to publish or archive | **Deny.** Status-change endpoints reject with `"You are not authorized to change recipe status; this authority is the Chef's."` |
| OM-PERM-04 | Outlet Manager reads `DRAFT` recipe | **Deny — by default.** Tenant policy typically restricts Outlet Manager read to `PUBLISHED` recipes only (drafts are author-in-progress and not yet ready for outlet view). Some tenants permit read of all statuses; the default is `PUBLISHED` only. |
| OM-PERM-05 | Outlet Manager reads recipe used at a different outlet | **Allow (typically).** Recipe library is generally library-wide read; outlet-scoped view is a filter, not a restriction. Some tenants may restrict cross-outlet read (e.g. for hotels with brand-segmented kitchens); the default is open read. |
| OM-PERM-06 | Outlet Manager creates SR from auto-create demand | **Allow.** The SR is in the [[store-requisition]] module, not the recipe module; the Outlet Manager's SR creation authority is governed by SR's `SR_AUTH_001`. |
| OM-PERM-07 | Kitchen Staff sub-role attempts any write | **Deny — read-only.** Kitchen Staff have `recipe:read` only. UI hides all edit controls; direct API write attempts are rejected. |

## 3. Validation / Error

| # | Scenario | Trigger | Expected error |
| - | -------- | ------- | -------------- |
| OM-VAL-01 | Demand explosion against `ARCHIVED` recipe | Outlet manager's planning view references a menu item linked to a recipe that has since been archived. | **Warn / fallback.** The recipe module returns the archived state with a warning; the production-planning layer either falls back to a previous published version (via `tb_recipe_version`) or excludes the menu item from explosion; Outlet Manager is notified to update the menu linkage. |
| OM-VAL-02 | Demand explosion against `DRAFT` recipe | A recipe was un-published mid-planning-cycle (e.g. for revision). | **Warn / fallback.** Similar to OM-VAL-01; the recipe is not eligible for theoretical-consumption drive while in `DRAFT`; the production-planning layer falls back or excludes. |
| OM-VAL-03 | Forecast inflated → over-sized SR | Outlet Manager enters forecast 500 covers (actual capacity 200) by mistake; demand explosion produces over-sized SR. | **Operational concern, not a system error.** The system computes correctly given the inputs; the SR may be rejected at approval (per `[[store-requisition]]` rules) due to source on-hand or budget constraints. Outlet Manager corrects forecast on the next cycle. |
| OM-VAL-04 | Recipe with `cost_per_portion = 0` | A `PUBLISHED` recipe accidentally has zero cost (data anomaly). | **Variance computation flags the anomaly.** Theoretical consumption fires correctly (the issue is on the cost dimension, not the quantity). Outlet Manager sees the recipe in variance review with cost = 0 and escalates to Cost Controller / Chef. |

## 4. Edge Cases

| # | Scenario | Condition | Expected |
| - | -------- | --------- | -------- |
| OM-EDGE-01 | Banquet event with mixed recipe sources (some new, some legacy) | 200-cover banquet uses 5 menu items: 3 from current menu (`PUBLISHED` recipes), 2 from special / one-off recipes. | Demand explosion handles all 5; auto-create SR (or operational pull list) aggregates correctly; sub-recipe ingredients across the 5 are deduplicated where the same product appears (`Σ qty` per product across recipes). |
| OM-EDGE-02 | Par-level top-up vs recipe-driven SR | Outlet uses par-level top-up for fast-moving commodities (sugar, flour, oil) and recipe-driven SR for high-value items (premium meats, specialty cheeses). | Two SR flows coexist: par-level SR (sized by par − on-hand, ingredient-by-ingredient) and recipe-driven SR (sized by demand × recipe). Outlet Manager decides per ingredient / per outlet. |
| OM-EDGE-03 | Multi-outlet shared recipe — outlet-specific variance | Recipe `House Burger` is `PUBLISHED` and used at 3 outlets; outlet A has variance, outlet B and C don't. | Variance dashboard surfaces per-outlet variance; the recipe is identical across outlets so the variance is operational (portion-control at outlet A) not recipe-attributable. Outlet Manager A owns the corrective action; Chef may receive feedback but is unlikely to revise the recipe (would impact B and C). |
| OM-EDGE-04 | Recipe-driven SR with sub-recipe recursion | Recipe `Composite Plate` uses sub-recipe `Sauce Au Poivre` which uses sub-recipe `Brown Stock`. Banquet demand for 200 covers. | Demand explosion recurses through sub-recipes per `REC_XMOD_004`; final pull list contains the leaf-product quantities; SR is sized correctly even with 3-level nesting. |
| OM-EDGE-05 | Recipe explosion when one ingredient on the recipe is inactive | A line on a `PUBLISHED` recipe references a product that has since been soft-deleted (data anomaly; should have been blocked at recipe-edit time). | **Warn.** Production-planning surfaces the issue: "Recipe `X` references inactive product `Y`; line excluded from demand explosion." Outlet Manager escalates to Chef for recipe revision; chef swaps the ingredient or the recipe is paused. |
| OM-EDGE-06 | Recipe with yield variant — variant-specific demand | Recipe with variants `Small`, `Medium`, `Large`; outlet has forecast: 30 Small + 50 Medium + 20 Large = 100 burgers (variant-specific demand). | Demand explosion respects variant scope: variant-scoped ingredient lines (`tb_recipe_ingredient.tb_recipe_yield_variantId`) apply only to their variant; non-scoped lines scale per variant `conversion_rate`; final pull list correctly reflects variant-specific quantities. |
| OM-EDGE-07 | Kitchen Staff mobile view during service | Kitchen Staff on mobile device, mid-service, reading recipe steps. | Mobile recipe view loads `PUBLISHED` recipe with images, method steps, plating instructions; read-only; sequential step display; no edit controls. Per the mobile-app spec. |

## 5. References

- Parent overview: [04-test-scenarios.md](./04-test-scenarios.md) — cross-persona handoffs that pivot off the Outlet Manager: Scenario 5 (feedback on portion-control), Scenario 6 (recipe-driven SR auto-create for banquet).
- User flow: [03-user-flow-outlet-manager.md](./03-user-flow-outlet-manager.md) — happy-path source for Section 1 above; describes the 8-step primary flow (planning → demand explosion → SR → service → variance → feedback).
- Business rules being verified: [02-business-rules.md](./02-business-rules.md) Section 3 — `REC_CALC_014` (theoretical-consumption / demand-explosion formula); Section 4 — `REC_AUTH_009` (Outlet Manager's read-only scope); Section 6 — `REC_XMOD_003` (theoretical OUT fan-out triggered by menu sale), `REC_XMOD_004` (sub-recipe recursion), `REC_XMOD_007` (auto-create SR from recipe demand).
- E2E spec: **none for recipe internals**; `701-sr.spec.ts` covers the SR-side of the recipe-driven auto-create path (the trigger from recipe → SR is at the test boundary).
- Cross-link: [[store-requisition]] — the primary downstream document the Outlet Manager authors from recipe demand.
- Cross-link: [[inventory]] — outlet on-hand reconciliation against recipe-driven theoretical consumption is the food-cost-variance computation.
- Cross-link: [[inventory-adjustment]] — corrective movements for shrinkage / spoilage flagged by variance investigation.

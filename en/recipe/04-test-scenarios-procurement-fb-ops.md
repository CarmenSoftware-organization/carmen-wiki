---
title: Recipe — Test Scenarios — Procurement / F&B Ops
description: Procurement and F&B Ops test cases (PO sizing, substitution, menu-item linkage approval, menu engineering) for the recipe module.
published: true
date: 2026-05-15T16:00:00.000Z
tags: recipe, test-scenarios, procurement-fb-ops, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T16:00:00.000Z
---

# Recipe — Test Scenarios — Procurement / F&B Ops

This page captures the test scenarios that the Procurement / F&B Ops persona directly drives in the `recipe` module. Procurement is read-only on the recipe (`recipe:read` per `REC_AUTH_010`) — they consume recipe demand to size POs and surface substitution requests, but do not write to the recipe. F&B Ops additionally holds `recipe:approve-menu-link` per `REC_AUTH_011` — they approve menu-item linkages on recipes the Chef has published, and own menu engineering decisions. Scenarios are grouped into **happy paths** (Procurement aggregates portfolio recipe demand → sizes PO; substitution request channel; F&B Ops menu-item linkage approval; menu engineering quarterly review), **RBAC** (Procurement attempting recipe edits; F&B Ops attempting ingredient edits), **validation** (negative tests around incomplete recipe pricing at menu-link approval, missing ingredients at PO sizing), and **edge cases** around portfolio-wide cost drift, multi-recipe menu items, seasonal menu cycle. Cross-persona handoffs that pivot off this persona (Scenarios 1, 4 in the parent overview) live in [04-test-scenarios.md](./04-test-scenarios.md), not here.

## 1. Happy Path

| # | Scenario | Pre-condition | Steps | Expected |
| - | -------- | ------------- | ----- | -------- |
| PF-HP-01 | Procurement aggregates portfolio recipe demand | Tenant has 50 outlets, 200 `PUBLISHED` recipes, forecast sales for next 7 days. | 1. Procurement opens demand-aggregation view. 2. Selects horizon (next 7 days), all outlets. 3. System triggers demand explosion across all outlets × forecast sales × linked recipes per `REC_CALC_014`. 4. Net demand per product (gross − on-hand at central store − in-flight POs − safety stock). | Portfolio-level ingredient demand computed; recursion handles sub-recipes; per-product net demand shown; basis for PO sizing. Performance: aggregation completes in tenant-acceptable time even with 200 recipes × 50 outlets. |
| PF-HP-02 | Procurement raises PO sized by recipe demand | PF-HP-01 produces net demand on `Premium Beef` for 200 kg over 7 days. | 1. Procurement creates PO against `Vendor-Premium-Meats` for 200 kg + safety buffer. 2. PO follows normal procurement flow (outside recipe module per [[purchase-order]]). | PO created with recipe-driven sizing rationale; the recipe module is the demand input; the PO lifecycle is in the procurement module. |
| PF-HP-03 | Substitution request → Chef revises | Vendor flags upcoming stock-out on specialty rice for the next 30 days; rice is used in 5 published recipes. Procurement proposes substitute jasmine rice at +5% cost. | 1. Procurement opens substitution-request channel. 2. Logs: "Vendor X cannot supply specialty rice for 30 days; substitute jasmine rice available at +5%. Affected recipes: A, B, C, D, E." 3. Chef receives the request. 4. Chef evaluates and either revises each recipe per `REC_POST_004` (in-place with versioning, swapping the ingredient) or coordinates a temporary menu pause. | Substitution request logged in operational channel; Chef ownership of recipe revision; affected recipes either swapped (with new `tb_recipe_version` rows and `tb_recipe_pricing_history` rows for the cost change) or paused (no recipe state change; menu impact). |
| PF-HP-04 | F&B Ops approves menu-item linkage on new recipe | Chef has published recipe `Wagyu Burger` (`PUBLISHED`); F&B Ops reviews for menu addition. | 1. F&B Ops opens recipe detail. 2. Reviews cost (`cost_per_portion = ฿380`), margin (`gross_margin_percentage = 31%` with `selling_price = ฿550`), menu fit (fits premium burger niche, complements existing House Burger), brand fit (aligned with hotel's upscale dining concept). 3. Clicks **Approve Menu Linkage**. 4. Menu-item created in POS-integration layer linking to recipe. | Per `REC_AUTH_011`. Linkage approved; recorded outside the recipe schema (per `REC_XMOD_008`); recipe unchanged from F&B Ops's action; recipe now drives theoretical OUT on menu sales of `Wagyu Burger`. |
| PF-HP-05 | F&B Ops rejects menu-item linkage | Chef has published `Experimental Dish`; F&B Ops reviews and decides it doesn't fit the menu. | 1. F&B Ops opens recipe detail. 2. Reviews: cost is fine, margin is OK, but the cuisine fit is wrong (fusion dish on a strictly Italian menu). 3. Clicks **Reject Menu Linkage** with feedback note "Doesn't fit Italian menu concept; reconsider as a special / banquet dish." 4. Chef receives feedback. | Recipe stays `PUBLISHED` but no menu-item linkage created; Chef may submit again with revisions or accept the rejection. |
| PF-HP-06 | F&B Ops quarterly menu engineering review | End of quarter; 200 menu items × recipes; sales and margin data available. | 1. F&B Ops opens menu engineering dashboard. 2. Combines per-recipe data: sales volume, `actual_food_cost_percentage`, `gross_margin_percentage`, variance. 3. Matrix view: high-margin/high-volume (stars), high-margin/low-volume (puzzles), low-margin/high-volume (workhorses), low-margin/low-volume (dogs). 4. Decisions per quadrant: stars preserve, workhorses cost-engineer (escalate to Chef + Cost Controller), dogs drop (archive request to Chef). | Menu engineering decisions recorded in operational dashboard; affected recipes get follow-up actions: Chef revises workhorses for ingredient cost, Cost Controller adjusts prices on stars, Chef archives dogs per `REC_POST_007`. |

## 2. Permission / Authorization

| # | Scenario | Expected behaviour (allow/deny + reason) |
| - | -------- | --------------------------------------- |
| PF-PERM-01 | Procurement reads recipe library | **Allow.** Per `REC_AUTH_010`. Full library read across all statuses (typically); used for PO sizing and substitution planning. |
| PF-PERM-02 | Procurement attempts to edit any recipe field | **Deny — read-only.** Per `REC_AUTH_010`. All edit endpoints reject. Substitution requests are operational-channel, not schema writes. |
| PF-PERM-03 | F&B Ops approves menu-item linkage | **Allow.** Per `REC_AUTH_011`. The approval is recorded in the POS-integration layer (outside the recipe schema). |
| PF-PERM-04 | F&B Ops attempts to edit ingredients | **Deny — Chef-only.** F&B Ops has `recipe:approve-menu-link` but not `recipe:edit`. Direct API call returns `"You are not authorized to edit recipes; that authority is the Chef's."` |
| PF-PERM-05 | F&B Ops attempts to edit pricing | **Deny — Cost-Controller-only.** F&B Ops collaborates with Cost Controller on price decisions but does not edit `selling_price` directly; that is Cost Controller's authority per `REC_AUTH_006`. |
| PF-PERM-06 | F&B Ops attempts to publish a recipe | **Deny — Chef-only.** Publish requires `recipe:publish` which is Chef-side. F&B Ops approves the menu-link, not the publish. |
| PF-PERM-07 | F&B Ops requests recipe archive | **Operational request to Chef.** F&B Ops does not directly archive (per `REC_AUTH_004` — archive is Chef-only); F&B Ops decides to retire the menu item and asks the Chef to archive the recipe. |

## 3. Validation / Error

| # | Scenario | Trigger | Expected error |
| - | -------- | ------- | -------------- |
| PF-VAL-01 | F&B Ops tries to approve menu-link on `DRAFT` recipe | Chef has not yet published; F&B Ops tries to approve. | **Reject — recipe must be `PUBLISHED` first.** Server returns `"Menu-item linkage can only be approved on PUBLISHED recipes; recipe is currently DRAFT."` |
| PF-VAL-02 | F&B Ops tries to approve menu-link on `ARCHIVED` recipe | Recipe was archived; F&B Ops tries to relink. | **Reject.** Server returns `"Archived recipes cannot be linked to menu items. Clone the recipe to a new DRAFT, re-publish, and try again."` |
| PF-VAL-03 | Procurement demand explosion against an `ARCHIVED` recipe still linked to a menu item | Data anomaly: recipe archived but menu-item linkage not severed. | **Warn / fallback.** Recipe module returns the archived state; production-planning layer either falls back to a previous version or excludes the menu item; Procurement is notified to coordinate with F&B Ops on linkage cleanup. |
| PF-VAL-04 | F&B Ops attempts to approve menu-link when recipe pricing is incomplete | Recipe `PUBLISHED` but `selling_price IS NULL` (e.g. ingredients-only recipe meant as a sub-recipe). | **Warn — confirm.** Server returns `"Recipe has no selling price set; confirm this menu link is for a non-priced item (e.g. part of a combo)."` (Sub-recipes typically wouldn't be linked to menu items; this is the edge case.) |
| PF-VAL-05 | Substitution request submitted without affected-recipe list | Procurement raises substitution but doesn't list which recipes are affected. | **Reject (operational validation).** Substitution-request UI requires the affected-recipe list to drive the Chef's evaluation. |

## 4. Edge Cases

| # | Scenario | Condition | Expected |
| - | -------- | --------- | -------- |
| PF-EDGE-01 | Multi-recipe menu item (combo) | Menu item `Combo Burger Meal` composes 3 recipes (burger, fries, drink). | F&B Ops approves the menu-item linkage that references all 3 recipes; menu-sale event explodes all 3 recipes per `REC_CALC_014`; theoretical OUT movements fan out for all ingredients across the 3 recipes. The linkage logic lives in the POS-integration layer. |
| PF-EDGE-02 | Portfolio-wide cost drift triggers menu engineering | Costing module emits drift on multiple staple ingredients (oil, flour, sugar); 80% of recipes' `actual_food_cost_percentage` exceeds target. | F&B Ops triggers extraordinary menu-engineering review; collaboration with Cost Controller on portfolio-wide price strategy (raise prices, accept reduced margins, drop most-impacted items); Chef-side ingredient revision is the longer-cycle response. |
| PF-EDGE-03 | Seasonal menu transition | End of Q3, transition to Q4 menu; 30 recipes retiring (Q3 specials), 30 new recipes being added (Q4 specials). | Chefs archive Q3 recipes per `REC_POST_007`; Chefs publish Q4 recipes per `REC_POST_003`; F&B Ops batch-approves menu-item linkages for Q4; Procurement re-sizes POs for the new ingredient mix. |
| PF-EDGE-04 | Vendor change for a high-fanout ingredient | Procurement switches from Vendor A to Vendor B for `Premium Olive Oil` due to vendor consolidation; cost changes by +3%. | Vendor pricelist update flows through costing module → recipe module cost-drift event per `REC_XMOD_006`; recipes refresh; Cost Controller flags affected recipes; F&B Ops reviews whether to absorb (no menu change) or pass through (price adjustments on affected dishes). |
| PF-EDGE-05 | Approval of new recipe at off-target margin | Chef publishes a `Signature Dish` at 38% actual food-cost % (target 32%); Cost Controller has co-approved per `REC_AUTH_007`; F&B Ops now decides on menu-item linkage. | F&B Ops sees the off-target margin in the recipe detail; reviews the strategic rationale ("signature dish"); approves the menu linkage despite the off-target margin. The approval is documented; the menu item begins driving sales at lower-than-typical margin. |
| PF-EDGE-06 | Demand-explosion performance with deep sub-recipe nesting | Portfolio aggregation across 200 recipes; 50 recipes use sub-recipes; some sub-recipes are 3-level deep. | Aggregation recursion completes in tenant-acceptable time; the recursion is bounded by the per-recipe nesting depth (typically < 4 levels in practice). Performance regression test confirms < 5s for 200-recipe portfolio aggregation. |
| PF-EDGE-07 | F&B Ops requests batch retirement | At end of season, 25 recipes need to be archived. | F&B Ops compiles the retirement list; Chef batch-archives via UI or API per `REC_POST_007`; each archive writes its own `tb_recipe_version` row with `change_summary = "batch-archived — Q3 seasonal retirement"`; menu-item linkages severed for each. |

## 5. References

- Parent overview: [04-test-scenarios.md](./04-test-scenarios.md) — cross-persona handoffs that pivot off Procurement / F&B Ops: Scenario 1 (full happy path includes menu-item linkage approval), Scenario 4 (Procurement substitution request).
- User flow: [03-user-flow-procurement-fb-ops.md](./03-user-flow-procurement-fb-ops.md) — happy-path source for Section 1 above; describes the 10-step primary flow (Procurement: aggregate → validate → raise PO → substitution; F&B Ops: review → approve / reject → menu engineering → signoff).
- Business rules being verified: [02-business-rules.md](./02-business-rules.md) Section 3 — `REC_CALC_014` (demand-explosion formula Procurement uses); Section 4 — `REC_AUTH_010`–`REC_AUTH_011` (Procurement / F&B Ops authority scope); Section 6 — `REC_XMOD_008` (menu-item linkage is application-layer, not in the recipe schema).
- E2E spec: **none for recipe internals**; adjacent automation in `[[purchase-order]]` covers the PO-side of the PF-HP-02 flow.
- Cross-link: [[purchase-order]] — Procurement's primary downstream document; recipe-driven demand sizes the PO.
- Cross-link: [[vendor-pricelist]] — vendor cost data is the upstream input to product cost, then to recipe cost.
- Cross-link: [[costing]] — F&B Ops reviews cost data sourced from the costing module.

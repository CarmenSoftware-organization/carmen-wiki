---
title: Recipe — Test Scenarios
description: Test cases by persona, cross-persona scenarios, and Playwright mapping for the recipe module.
published: true
date: 2026-05-17T11:00:00.000Z
tags: recipe, test-scenarios, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T16:00:00.000Z
---

# Recipe — Test Scenarios

> **At a Glance**
> **Module:** [[recipe]] &nbsp;·&nbsp; **Total scenarios:** ~14 cross-persona + per-persona drill-downs across all personas &nbsp;·&nbsp; **Personas covered:** Chef, Cost Controller, Outlet Manager, Procurement / F&B Ops, Audit / Config
> **Run order:** Audit / Config setup → primary persona happy paths → cross-persona scenarios
> **Each persona's drill-down is `04-test-scenarios-<role>.md`**

## 1. Overview

This page is the **overview entry point** for the test-scenarios set of the `recipe` module. It groups recipe coverage by the five personas that interact with the recipe library across its lifecycle (Chef, Cost Controller, Outlet Manager, Procurement / F&B Ops, Audit / Config), inventories the per-persona test files, captures the cross-persona handoff scenarios that stitch individual paths together, and notes E2E coverage status. The scope is deliberately wider than a pure functional pass: each persona file includes **functional happy paths** (create / save / publish / archive; cost-only edit; substitution flow; menu-item linkage approval; admin config), **RBAC / permission-denial cases** (chef without `recipe:publish`; cost controller attempting ingredient edits; outlet manager attempting any write; auditor attempting any write), **edge cases** (large recipe — many ingredients and steps; sub-recipe deep nesting; yield-variant with stepped quantities; concurrent edits; decimal-precision corner cases), and **versioning / pricing-history traces** (every change to a `PUBLISHED` recipe writes a `tb_recipe_version` row; cost-only edits write `tb_recipe_pricing_history` rows; the audit chain is verifiable from those tables).

The cross-persona scenarios in Section 4 are the integration layer above the per-persona suites. They describe end-to-end journeys that cross a handoff boundary recorded in [03-user-flow.md](./03-user-flow.md) Section 4 — for example, *Chef creates → Cost Controller co-approves off-target publish → Chef publishes → F&B Ops approves menu-item linkage → recipe drives theoretical consumption*. Section 5 then notes the **automated coverage status** — at the time of writing there is **no dedicated `recipe.spec.ts` Playwright file in the carmen-inventory-frontend-e2e suite** (verified by `ls ../carmen-inventory-frontend-e2e/tests/ | grep -i 'recipe\|menu'` returning empty), so the per-persona test files describe scenarios that are currently **manual / planned** for E2E automation. Adjacent automation exists in `[[store-requisition]]` (`701-sr.spec.ts`) which covers the recipe-driven SR auto-create path indirectly (`info.recipe_id` back-reference), but recipe-internal E2E coverage is a gap.

## 2. Personas in Scope

- **Chef**: Chef / Kitchen Manager (+ Kitchen Staff read-only subset); authors recipes; publishes, archives; maintains sub-recipes; revises in response to feedback / cost drift.
- **Cost Controller**: Cost Controller (+ Cost Control Department); reviews cost rollup, target margins, selling prices; monitors drift; co-approves off-target publishes; runs variance reports.
- **Outlet Manager**: Outlet Manager; demand-side consumer; raises SRs from recipe demand; monitors outlet variance; feeds back issues to Chef.
- **Procurement / F&B Ops**: Procurement Department (PO sizing, ingredient availability, substitution requests) + F&B Operations Manager (strategic menu-item linkage approval, menu engineering).
- **Audit / Config**: Sysadmin (categories, cuisines, equipment, RBAC, tenant policy, integration wiring) + Auditor (read-only versioning / pricing-history / signature trace).

## 3. Persona Test Files

- [Chef scenarios](./04-test-scenarios-chef.md)
- [Cost Controller scenarios](./04-test-scenarios-cost-controller.md)
- [Outlet Manager scenarios](./04-test-scenarios-outlet-manager.md)
- [Procurement / F&B Ops scenarios](./04-test-scenarios-procurement-fb-ops.md)
- [Audit / Config scenarios](./04-test-scenarios-audit-config.md)

## 4. Cross-Persona / Handoff Scenarios

The table below is the integration layer. Each row spans at least one handoff from [03-user-flow.md](./03-user-flow.md) Section 4 and ends with the recipe in a terminal or steady state. "Personas in order" lists the actors in execution sequence; "Pre-condition" captures the system state required to begin; "Expected end state" anchors the recipe `status` and the downstream effects (versioning row, pricing-history row, menu-item linkage, theoretical-consumption fan-out).

| # | Scenario | Personas in order | Pre-condition | Expected end state |
| - | -------- | ----------------- | ------------- | ------------------ |
| 1 | Full happy path — new recipe from create to menu-item linkage | Chef → F&B Ops | Tenant has category `Mains` configured with target food-cost % 32; chef has `recipe:create / edit / publish` on `Mains`; F&B Ops has `recipe:approve-menu-link`. | Recipe `PUBLISHED`; `tb_recipe_version` row v1 with `published = true`; `tb_recipe_pricing_history` row at publication snapshot; menu-item linkage approved in the POS-integration layer; recipe begins driving theoretical OUT on menu sales per `REC_XMOD_003`. |
| 2 | Off-target margin publish requires Cost Controller co-approval | Chef → Cost Controller → Chef | Recipe in `DRAFT` with `actual_food_cost_percentage = 38%` vs `target_food_cost_percentage = 32%`, beyond the tenant 2-percentage-point tolerance; tenant policy enables `REC_AUTH_007`. | Initial publish blocked; Cost Controller reviews and co-approves with note in `change_summary`; chef publishes; `tb_recipe_version` row v1 with `change_summary = "co-approved off-target by Cost Controller: signature dish, accept lower margin"`. |
| 3 | Sub-recipe cost cascade triggers re-cost on parent recipes | (System-driven, surfaced to Cost Controller) | Sub-recipe `Burger Sauce` is `PUBLISHED` and used as ingredient on three parent recipes; mayonnaise (product on the sub-recipe) cost rises 40% via vendor pricelist update flowing through to costing. | Sub-recipe `cost_per_portion` re-computes; parent recipes 1–3 re-cost atomically per `REC_POST_006`; each parent gets a `tb_recipe_pricing_history` row with `change_reason = "sub-recipe cost cascade from Burger Sauce"`; Cost Controller dashboard surfaces parents whose `actual_food_cost_percentage` now exceeds tolerance. |
| 4 | Procurement substitution request → Chef revises | Procurement → Chef | A high-volume ingredient (e.g. specialty rice) is flagged by Procurement as unavailable for the next 30 days; affects 5 published recipes; substitute proposed at +5% cost. | Chef receives the substitution request; either (a) swaps the ingredient on each affected recipe via `REC_POST_004` (in-place with versioning; each recipe gets a new `tb_recipe_version` row + `tb_recipe_pricing_history` for the cost change) or (b) coordinates a temporary menu pause on affected dishes; Cost Controller monitors margin impact post-swap. |
| 5 | Outlet Manager feedback on portion-control issue | Outlet Manager → Chef | Recipe `Premium Steak` is `PUBLISHED`; outlet's variance dashboard shows persistent positive variance on the steak ingredient — kitchen plating 250g but recipe specifies 220g. | Outlet Manager logs feedback through the operational channel; Chef investigates with the kitchen, decides whether to (a) revise the recipe to 250g (recipe was under-spec; `REC_POST_004` with new version) or (b) reinforce plating discipline with Kitchen Staff (recipe is correct; corrective action is operational). Outlet variance closes in the next period. |
| 6 | Recipe-driven SR auto-create for banquet event | Recipe module (auto-create) → Outlet Manager → SR flow | Outlet has a banquet event for 200 covers booked next Friday; menu items linked to 4 recipes; recipes are `PUBLISHED`. | Recipe module computes ingredient demand × 200 covers per `REC_CALC_014`; posts an SR `draft` with `info.recipe_id` (or `info.event_id`) at the outlet; Outlet Manager reviews, adjusts, and submits per the [[store-requisition]] flow; SR moves through approval and fulfilment normally; variance at period close vs the auto-computed demand is surfaced in the variance dashboard. |
| 7 | In-place edit on `PUBLISHED` recipe with versioning | Chef | Recipe `House Burger` is `PUBLISHED` at version 1; chef revises the patty quantity from 1 to 1.2 to address portion feedback. | Edit applies in-place per `REC_POST_004`; cost rollup recomputes; `tb_recipe_version` v2 written with `published = true`, `change_summary = "increased patty qty to 1.2 per outlet feedback"`; `tb_recipe_pricing_history` row written with `change_reason = "ingredient qty revision"`; theoretical consumption from the next menu sale onward uses the v2 formula. |
| 8 | Un-publish round-trip for major overhaul | Chef | Recipe `Seasonal Curry` is `PUBLISHED`; chef plans a comprehensive overhaul (rebalance ingredients, rewrite method, new pricing); tenant policy: un-publish required for major edits. | Chef un-publishes (`PUBLISHED → DRAFT` per `REC_POST_008`); makes edits over the next week; re-publishes per `REC_POST_003` (writes new `tb_recipe_version` row v2 with `published = true`, `change_summary = "seasonal refresh — Q3 2026"`); linked menu items handled per POS-integration policy during the `DRAFT` window. |
| 9 | Archive on menu retirement | F&B Ops → Chef | Recipe `Holiday Special` was a limited-time menu item; the holiday season ends; F&B Ops decides to retire. | Chef archives the recipe per `REC_POST_007`: `PUBLISHED → ARCHIVED`, `archived_at = now()`; final `tb_recipe_version` row written with `change_summary = "archived — limited-time menu retired"`; menu-item linkage severed; recipe no longer drives theoretical consumption on new sales; historical theoretical-consumption events in the inventory ledger preserved for audit. |
| 10 | Sysadmin RBAC change affecting in-flight chef work | Sysadmin → all personas | Tenant decides to restrict Pastry Chef to Desserts category only (was previously full library); 3 in-flight `DRAFT` recipes by the Pastry Chef are in `Mains`. | Sysadmin commits the RBAC change; new rules apply prospectively; in-flight `DRAFT` recipes by the Pastry Chef in `Mains` become read-only to them (need an Executive Chef to take over edit); Sysadmin coordinates with Cost Controller / F&B Ops on the transition; affected work either re-assigned or completed via override. |
| 11 | Audit sample — verify versioning chain | Auditor | Sample 30 `PUBLISHED` recipes across the period for compliance review. | Each recipe has a `tb_recipe_version` chain from v1 (publication) through each edit; `published_at` matches v1 timestamp; off-target publishes have co-approval recorded in `change_summary`; cost / price changes have corresponding `tb_recipe_pricing_history` rows with populated `change_reason`; audit columns (`created_by_id` / `updated_by_id`) are consistent. Audit findings logged. |
| 12 | Sub-recipe deep nesting (3 levels) | Chef | Recipe `Composite Plate` uses sub-recipe `Sauce Au Poivre` which itself uses sub-recipe `Brown Stock` which uses leaf-product `Beef Bones`. | Theoretical-consumption fan-out on menu sale recurses 3 levels deep per `REC_XMOD_004`: parent recipe → sub-recipe Sauce Au Poivre → sub-recipe Brown Stock → product `Beef Bones`; OUT movement posted against `Beef Bones` at the outlet. The cost cascade also recurses: a cost change on `Beef Bones` flows up through `Brown Stock` → `Sauce Au Poivre` → `Composite Plate`; each level gets a `tb_recipe_pricing_history` row. |
| 13 | Cost-drift cascade on a high-fanout ingredient | Cost Controller | Single product `Premium Olive Oil` is used in 25 recipes; its cost rises 18%; tenant tolerance for cost-drift trigger is ±5%. | Costing module emits cost-drift event per `REC_XMOD_006`; recipe module refreshes `cost_per_unit` on every line referencing the product (across all 25 recipes); writes `tb_recipe_pricing_history` row per affected recipe with `change_reason = "cost-drift update from costing module"`; 8 recipes whose new `actual_food_cost_percentage` exceeds target+tolerance flagged for Cost Controller review. |
| 14 | Concurrent edit by two chefs on the same `DRAFT` | Chef + deputy | Two chefs (Executive Chef + Sous Chef as deputy) edit the same `DRAFT` recipe simultaneously; both attempt save. | Optimistic-concurrency: the first save wins (writes `updated_at` / `updated_by_id`); the second save is rejected on conflict detection (server returns 409); the second chef refreshes, sees the first save's edits, decides whether to merge or override. The recipe schema does not have a `doc_version` column on `tb_recipe` directly but tenant policy may use the `updated_at` timestamp for concurrency check. |

## 5. E2E Test Mapping

At the time of writing there is **no dedicated `recipe.spec.ts` Playwright file in `../carmen-inventory-frontend-e2e/tests/`** (verified by `ls ../carmen-inventory-frontend-e2e/tests/ | grep -i 'recipe\|menu'` returning empty). The recipe-internal scenarios in this page and the per-persona test files are therefore **manual / planned** for E2E automation; the closest adjacent automated coverage is:

| Adjacent E2E spec | Recipe-related coverage |
| ----------------- | ----------------------- |
| `701-sr.spec.ts` (store-requisition) | Scenario 6 (recipe-driven SR auto-create) is partially covered — the SR side of the flow (`info.recipe_id` back-reference, normal SR lifecycle) is exercised; the recipe-side trigger (recipe module posting the SR draft) is mocked or skipped at the test boundary. |
| (None) | Scenarios 1–5, 7–14 are documented as manual / planned. |

Gaps relative to Section 4: all 14 cross-persona scenarios are gaps for full E2E automation. The persona-level test files document the scenarios with sufficient detail for either manual execution or future Playwright spec development. Priority for future automation: Scenario 1 (full happy path), Scenario 2 (off-target co-approval), Scenario 7 (in-place edit with versioning), Scenario 3 (sub-recipe cascade), Scenario 9 (archive).

## 6. References

- Sibling: [03-user-flow.md](./03-user-flow.md) Section 4 — cross-persona handoffs that drive the integration scenarios above.
- Sibling: [02-business-rules.md](./02-business-rules.md) Section 5 — posting rules invoked at every state transition and downstream effect (publish, edit-published, cost cascade, archive).
- Per-persona detail: [Chef](./04-test-scenarios-chef.md), [Cost Controller](./04-test-scenarios-cost-controller.md), [Outlet Manager](./04-test-scenarios-outlet-manager.md), [Procurement / F&B Ops](./04-test-scenarios-procurement-fb-ops.md), [Audit / Config](./04-test-scenarios-audit-config.md).
- Adjacent E2E coverage: `../carmen-inventory-frontend-e2e/tests/701-sr.spec.ts` (covers SR-side of recipe-driven auto-create indirectly via `info.recipe_id`).
- Related modules: [[product]] (ingredient feed), [[inventory]] (theoretical-consumption fan-out target), [[costing]] (cost-drift upstream), [[store-requisition]] (downstream auto-create).

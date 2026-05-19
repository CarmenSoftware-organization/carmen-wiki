---
title: Recipe — User Flow — Outlet Manager
description: Outlet Manager's flow within the recipe module — consumes recipes for demand planning, monitors outlet food-cost variance, feeds back accuracy / portion-control issues.
published: true
date: 2026-05-17T11:00:00.000Z
tags: recipe, user-flow, outlet-manager, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T16:00:00.000Z
---

# Recipe — User Flow — Outlet Manager

> **At a Glance**
> **Persona:** Outlet Manager &nbsp;·&nbsp; **Module:** [[recipe]] &nbsp;·&nbsp; **Workflow stages:** off-path — consumes PUBLISHED recipes for demand planning and variance monitoring &nbsp;·&nbsp; **Key permissions:** read recipes; author / submit downstream SRs; raise feedback to Chef
> **What this persona does:** Reads recipes to plan production and raise SRs; monitors outlet food-cost variance and feeds back accuracy issues to the Chef.

## 1. Role in This Module

The **Outlet Manager** persona is the manager of a consuming outlet — kitchen, bar, banquet hall, restaurant — that uses recipes for daily production and pulls ingredients from the central store to meet recipe demand. The Outlet Manager is **read-only on the recipe library** (`recipe:read` per `REC_AUTH_009`); they do **not** create or edit recipes. Their engagement with the recipe module flows in three directions: **demand-side** (use recipe explosions × forecast sales to plan ingredient pulls; raise SRs against the central store, often auto-generated from recipe demand per `REC_XMOD_007`); **variance-side** (monitor the outlet's food-cost variance vs budget, which is driven in part by recipe accuracy — recipes with under-stated wastage, over-stated yields, or stale costs create variance); and **feedback-side** (report portion-control issues, ingredient-accuracy problems, missing or wrong prep steps back to the Chef as input for recipe revision per the Chef persona's `REC_POST_004` revision flow). The Outlet Manager is the **primary author of [[store-requisition]] documents** (recipes drive the SR via auto-create or via manual entry against recipe demand); the Outlet Manager is the **destination of issued goods** and the **owner of the outlet-level food-cost variance KPI**. From the recipe module's perspective the Outlet Manager is a downstream consumer, not a producer; from the operational perspective they are the demand signal that drives recipe usage at scale.

## 2. Entry Point and Primary Flow

**Entry point:** Four paths into Outlet Manager work touching the recipe module.

- **Recipe library → outlet-scoped view** — list view filtered to recipes used in the outlet (i.e. recipes linked to menu items sold at the outlet, or recipes for events booked at the outlet); read-only.
- **Production planning → recipe explosion** — the outlet's planned production for the day / week (cover counts, banquet events) is multiplied through recipe ingredient lines per `REC_CALC_014` to produce an ingredient pull list; the list seeds an SR draft per `REC_XMOD_007`.
- **Outlet variance dashboard** — outlet-level food-cost variance (theoretical-vs-actual) for the period, with drill-down into the recipes and ingredients contributing to the variance.
- **Feedback channel → submit recipe issue** — an in-app channel (or external workflow — depends on tenant) where the Outlet Manager (or Kitchen Staff reporting up) flags a portion-control / accuracy / missing-step issue on a `PUBLISHED` recipe.

**Primary flow (8 steps — runs daily / per shift):**

1. **Review the day's planned production.** Open the production-planning view for the outlet: forecast cover count per menu item, banquet events booked, special-occasion volume. Each menu item links to one or more `PUBLISHED` recipes (the linkage lives outside the recipe schema per `REC_XMOD_008`).
2. **Explode recipes to ingredient demand.** For each menu item × forecast quantity, the system explodes the linked recipe(s) per `REC_CALC_014`: ingredient quantities are scaled by sold quantity, wastage % applied, UoM converted to stock units. Sub-recipe ingredients recurse to leaf products per `REC_XMOD_004`. The aggregated ingredient demand is presented as a pull list (one row per product, total quantity in stock UoM).
3. **Reconcile against on-hand at outlet.** For each product on the pull list, compare against the outlet's current on-hand (read from `tb_inventory_status` per outlet location). Net demand = projected demand − current on-hand − reserved by other open SRs.
4. **Generate / review SR draft.** The system either auto-creates an SR `draft` against the central store with the net demand (per `REC_XMOD_007`; the SR carries `info.recipe_id` or `info.production_event_id` as the back-reference) or the Outlet Manager creates the SR manually using the pull list as reference. The Outlet Manager reviews quantities, adjusts if needed, and submits the SR. The SR follows the normal store-requisition flow (`SR_POST_001` onward in [[store-requisition/02-business-rules]]) — approval → fulfilment → receipt at the outlet.
5. **Service execution.** Kitchen Staff at the outlet read the `PUBLISHED` recipes during service to prepare dishes; mobile / station displays surface the recipe header, ingredient list, method steps, plating instructions. Kitchen Staff are read-only on the recipe (`REC_AUTH_009`); issues raised during service are captured in a feedback channel.
6. **Monitor food-cost variance during the period.** The outlet variance dashboard shows theoretical consumption (from recipe-driven menu sales) vs actual consumption (from SR issues, physical-count posts, adjustments). Persistent positive variance (actual > theoretical) means the outlet is consuming more than recipes say it should — over-portioning, theft, spoilage, sub-recipe inaccuracy, or stale recipe costs. Persistent negative variance (theoretical > actual) means recipes overstate consumption — under-portioning, recipe error, or kitchen staff using less than the recipe specifies.
7. **Investigate variance and feed back.** Drill into the largest contributors to the variance. For each: is the variance attributable to (a) portion-control discipline (Outlet Manager owns the corrective action — Kitchen Staff training, plating audits), (b) recipe inaccuracy (escalate to the Chef for `REC_POST_004` revision — wastage % too low, yield too high, missing wastage on a step), or (c) shrinkage / spoilage (escalate to Inventory Controller for investigation through `[[inventory-adjustment]]`)?
8. **Submit recipe-feedback items to Chef.** For recipe-attributable issues, log feedback in the feedback channel (in-app comment, ticket, or operational meeting). The Chef receives the feedback and decides whether to revise the recipe per `REC_POST_004` (in-place with versioning) or `REC_POST_005` (un-publish round-trip). The Outlet Manager monitors the next variance cycle to confirm whether the revision closed the gap.

## 3. Decision Branches

- **Auto-generated SR vs manual SR**: tenant config decides whether the recipe-demand explosion auto-creates an SR `draft` (per `REC_XMOD_007`) or surfaces the pull list for the Outlet Manager to use as reference when creating the SR manually. Auto-create is faster and more accurate (no transcription); manual is preferred when the outlet routinely overrides demand (e.g. emergency buffer stock, par-level top-up). The Outlet Manager may always edit an auto-created draft before submit.
- **Variance attributable to portion-control vs recipe**: when investigating outlet variance, the Outlet Manager assesses whether the gap is a kitchen-discipline issue (Kitchen Staff plating different from recipe — own corrective action via training and audit) or a recipe-accuracy issue (recipe wastage / yield is wrong — escalate to Chef). The distinction is usually visible in the per-ingredient drill-down: a single ingredient with chronic over-consumption suggests portion-control; broad over-consumption on a dish's ingredients suggests recipe under-stating actual usage.
- **Forecast accuracy adjustment**: when the demand explosion produces ingredient quantities that don't match the outlet's actual usage pattern, the issue may be in the **forecast** (cover counts too high or too low) rather than in the recipe. The Outlet Manager refines the forecast in subsequent planning cycles; the recipe is the formula source and is not adjusted.
- **Sub-recipe accuracy**: when a sub-recipe is used in many dishes, its cost / yield accuracy has outsized impact. Variance investigation may surface a sub-recipe with stale costs or wrong yield; the Outlet Manager escalates to the Chef who is responsible for the sub-recipe.
- **Outlet-specific recipe variants**: when a recipe is used at multiple outlets with different equipment / scale, accuracy may differ by outlet. The Outlet Manager flags outlet-specific issues; the Chef decides whether to maintain one recipe (and accept some outlet variance) or create per-outlet variants (yield-variant rows or separate recipes).
- **Banquet vs a-la-carte demand**: for outlets handling banquet events, the demand explosion has higher accuracy needs (large guaranteed cover counts; demand visible weeks in advance). For a-la-carte, demand is probabilistic and SRs are sized to par + buffer rather than per-event. The Outlet Manager makes the methodology choice per outlet operations.

## 4. Exit Point / Handoffs

The Outlet Manager's recipe-related involvement on a given operational cycle ends at one of several boundaries:

- **SR submitted to central store** — handoff to **Approver** and **Fulfiller** in the [[store-requisition]] flow (the SR's lifecycle continues independently); the Outlet Manager monitors but does not advance the SR's status.
- **Recipe-feedback raised to Chef** — handoff to the **Chef** for evaluation and revision per `REC_POST_004`; the Outlet Manager monitors the next variance cycle to confirm closure.
- **Variance attributable to shrinkage** — handoff to **Audit / Config (Inventory Controller)** for investigation through `[[inventory-adjustment]]`; the Outlet Manager provides operational context but the resolution is at the inventory layer.
- **Portion-control corrective action complete** — recipe is unchanged; Kitchen Staff trained or audited; the Outlet Manager owns the corrective action and the follow-up.
- **Period-end signoff** — handoff to **Audit / Config (Finance + Cost Control)** for the outlet's food-cost reconciliation against the GL; the Outlet Manager confirms the operational picture for the period.

The Outlet Manager is a **continuous downstream consumer** of the recipe library — every shift, every service, every banquet event drives recipe usage. The Outlet Manager rarely "exits" the recipe-related flow; the engagement is daily-operational.

## 5. References

- Parent overview: [03-user-flow.md](./03-user-flow.md) — the canonical lifecycle; Section 4 rows "Outlet Manager → Chef (feedback)", "Recipe module → Outlet Manager (auto-create SR)", "Recipe module → Inventory module (theoretical OUT)" frame this persona's interactions.
- `../carmen/docs/recipe-module/RECIPE-Overview.md` § Kitchen Staff (and the user-roles table in the wiki index for Outlet Manager) — carmen/docs source for the operational role.
- `../carmen/docs/recipe-module/RECIPE-PRD.md` § Kitchen Staff user stories — carmen/docs user stories ("As a kitchen staff member, I want to view detailed recipe instructions...", "...see ingredient quantities and preparation steps clearly...").
- `../carmen/docs/recipe-module/mobile-app.md` — mobile-app reference for the kitchen-floor consumption of `PUBLISHED` recipes.
- `../carmen/docs/recipe/recipe-view-page.md` — read-only detail page spec — the Outlet Manager and Kitchen Staff primary surface.
- Sibling: [03-user-flow-chef.md](./03-user-flow-chef.md) — primary recipient of Outlet Manager feedback; revisions flow from Outlet-Manager-raised issues through Chef ownership.
- Sibling: [03-user-flow-cost-controller.md](./03-user-flow-cost-controller.md) — variance investigation collaborator; the Cost Controller looks at portfolio-level variance, the Outlet Manager owns outlet-level variance.
- Sibling: [03-user-flow-procurement-fb-ops.md](./03-user-flow-procurement-fb-ops.md) — Procurement uses outlet-level demand (the same explosion) to size POs; the demand-side feed is shared.
- Sibling: [03-user-flow-audit-config.md](./03-user-flow-audit-config.md) — Inventory Controller investigates shrinkage at the outlet; Sysadmin's RBAC scoping bounds the Outlet Manager's recipe-library view.
- Sibling: [01-data-model.md](./01-data-model.md) — `tb_recipe.status` (only `PUBLISHED` recipes are eligible for outlet consumption), `tb_recipe_ingredient` fields used in the demand explosion (`qty`, `inventory_unit_id`, `conversion_factor`, `wastage_percentage`).
- Sibling: [02-business-rules.md](./02-business-rules.md) — `REC_CALC_014` (theoretical-consumption formula — the demand explosion), `REC_AUTH_009` (Outlet Manager's read-only scope), `REC_XMOD_003` (theoretical OUT fan-out triggered by menu sale), `REC_XMOD_007` (auto-create SR from recipe demand).
- Related: [[store-requisition]] — the primary downstream document the Outlet Manager authors; recipe demand seeds the SR.
- Related: [[inventory]] — outlet on-hand reconciliation against recipe-driven theoretical consumption is the food-cost-variance computation.
- Related: [[inventory-adjustment]] — corrective movements for shrinkage / spoilage flagged by variance investigation.

---
title: Recipe — User Flow — Cost Controller
description: Cost Controller's flow within the recipe module — reviews recipe cost, target margins, selling price, gross margin; monitors drift; signs off changes.
published: true
date: 2026-05-15T16:00:00.000Z
tags: recipe, user-flow, cost-controller, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T16:00:00.000Z
---

# Recipe — User Flow — Cost Controller

## 1. Role in This Module

The **Cost Controller** persona covers two overlapping roles: the **Cost Controller** (transactional — reviews each recipe's cost rollup, target food-cost %, recommended selling price, gross margin; monitors cost drift as ingredient prices move; flags out-of-tolerance margins; signs off cost-related changes affecting menu pricing; runs theoretical-vs-actual variance reports) and the **Cost Control Department** (portfolio-level — owns the recipe-costing process at scale, sets category-level target food-cost percentages via `tb_recipe_category.default_cost_settings`, drives versioning approval when ingredient prices materially shift, reconciles outlet variance to GL at period close). The Cost Controller's authority surface is **read across the recipe library and write on cost / pricing columns only** — per `REC_AUTH_006`, the Cost Controller may edit `target_food_cost_percentage`, `labor_cost`, `overhead_cost`, `labor_cost_percentage`, `overhead_percentage`, `selling_price`, and `suggested_price` on `DRAFT` and `PUBLISHED` recipes; ingredient / step / variant edits remain with the Chef. The Cost Controller is also the **publish co-approver** for off-target margin publications per `REC_AUTH_007` (when `actual_food_cost_percentage > target + tenant tolerance`, the publish is gated on Cost Controller co-approval); the co-approval is recorded in `tb_recipe_version.change_summary` or an application-layer signoff log. Beyond per-recipe work, the Cost Controller owns the **cost-drift dashboard** (recipes whose margin has fallen outside tolerance due to ingredient price moves or sub-recipe cascades per `REC_XMOD_006`) and the **theoretical-vs-actual variance dashboard** (outlet-level food-cost variance computed from the recipe-driven theoretical OUT vs the actual stock movements).

## 2. Entry Point and Primary Flow

**Entry point:** Four paths into Cost Controller work.

- **Cost-drift dashboard** — list view across `PUBLISHED` recipes whose `actual_food_cost_percentage` exceeds `target_food_cost_percentage` by more than tenant tolerance, ranked by drift magnitude. Each row links to the recipe detail and to the affected ingredient(s) whose cost has moved.
- **Pre-publish co-approval queue** — list view of `DRAFT` recipes that the Chef has marked ready for publish but whose actual margin is off-target; the Cost Controller is queued to co-approve or request revisions per `REC_AUTH_007`.
- **Recipe detail → Costing tab** — drilled directly into a single recipe; the Cost Controller can adjust `target_food_cost_percentage`, `selling_price`, `labor_cost_percentage`, `overhead_percentage` per `REC_AUTH_006`.
- **Variance dashboard (theoretical-vs-actual)** — outlet-level food-cost variance dashboard; clicking into an outlet drills into the recipes contributing to the variance.

**Primary flow (10 steps — repeated per period and per drift event):**

1. **Open the cost-drift dashboard.** The dashboard surfaces `PUBLISHED` recipes whose current `actual_food_cost_percentage` exceeds `target_food_cost_percentage` by more than the tenant tolerance (e.g. > 2 percentage points). Filter by category, cuisine, outlet (if recipe-outlet mapping is configured), drift magnitude, last-changed date.
2. **Drill into a flagged recipe.** Open the recipe detail; review the Costing tab: `total_ingredient_cost` rollup with per-line `net_cost` and `wastage_cost`, `labor_cost`, `overhead_cost`, `cost_per_portion`, `selling_price`, `actual_food_cost_percentage`, `gross_margin`, `gross_margin_percentage`. Read the pricing-history timeline (`tb_recipe_pricing_history`) to see how the cost has moved over time.
3. **Identify the drift cause.** Was the drift caused by (a) a vendor pricelist update on a product the recipe uses (visible in `tb_recipe_pricing_history.change_reason = "cost-drift update from costing module"`); (b) a sub-recipe cost cascade (`change_reason = "sub-recipe cost cascade from <name>"`); (c) an actively-revised ingredient (Chef updated `qty` or wastage per `REC_POST_004`); or (d) a target-change (the tenant lowered the target food-cost %)?
4. **Decide on the corrective path.** Four options:
   - **Revise ingredients** — escalate to the Chef to revise (swap to a cheaper ingredient, reduce portion, source from a different vendor). Cost Controller does NOT edit ingredients directly; the Chef does. The Cost Controller logs the request as the trigger.
   - **Adjust price** — edit `selling_price` upward per `REC_AUTH_006` and `REC_POST_010`; the system recomputes `actual_food_cost_percentage`, `gross_margin`, `gross_margin_percentage`; a `tb_recipe_pricing_history` row is written with `change_reason = "price increase to restore margin"`. Coordinate with F&B Ops on the menu-side communication.
   - **Adjust target** — edit `target_food_cost_percentage` upward per `REC_AUTH_006`; the recipe's margin is now within the new target. This is the "accept the new cost reality" path; reserved for situations where the cost increase is industry-wide and unavoidable, with corresponding adjustment at category level via `tb_recipe_category.default_cost_settings`.
   - **Co-approve off-target** — if the Chef proposes to publish or maintain the recipe at off-target margin intentionally (loss leader, signature dish, strategic-priced), the Cost Controller co-approves per `REC_AUTH_007`; the off-target status is documented in `tb_recipe_version.change_summary` for audit.
5. **Co-approve off-target publish (Chef-initiated path).** When a Chef has prepared a `DRAFT` recipe whose actual margin is off-target at publish time, the publish is gated on Cost Controller co-approval. The Cost Controller reviews the recipe (ingredients, costing inputs, intended pricing) and decides: (a) co-approve (publish proceeds; the off-target is documented); (b) request revisions (publish stays gated until Chef revises and re-submits); (c) reject (Chef revises or abandons the recipe).
6. **Edit cost-only fields where appropriate.** Per `REC_AUTH_006`, the Cost Controller may directly edit `target_food_cost_percentage`, `selling_price`, `labor_cost_percentage`, `overhead_percentage`, `suggested_price`. These edits trigger `REC_POST_010` — recompute pricing rollup, write `tb_recipe_pricing_history` row. The recipe stays in its current status; no full `tb_recipe_version` snapshot needed for pricing-only changes.
7. **Run theoretical-vs-actual variance report.** At period end (or on-demand), run the outlet-level variance report. Theoretical consumption is computed from menu sales × recipe ingredient lines per `REC_CALC_014`; actual consumption is from physical-count + SR + adjustment data. Variance per ingredient per outlet is the headline KPI. Persistent positive variance (theoretical < actual; over-consumption) points to over-portioning, theft, spoilage, or recipe accuracy gaps; persistent negative variance points to under-portioning or recipe error.
8. **Investigate material variances.** Drill into outlets with material variance. The Cost Controller does **not** edit the recipe — they raise the issue with the Chef (recipe accuracy) and the Outlet Manager (portion-control discipline, possible shrinkage). Variance investigation is collaborative; the recipe is one input.
9. **Set / adjust category-level targets (portfolio-level, Cost Control Department).** Each quarter (or per tenant cadence), review category-level food-cost targets. For each `tb_recipe_category`, adjust `default_cost_settings` (target food-cost %, labor / overhead percentages) based on portfolio performance, market conditions, and strategic direction. New recipes in the category will inherit; existing recipes can be optionally re-applied (manual operation; not automatic).
10. **Period-end signoff.** At period close, the Cost Control Department signs off on the period's recipe-driven food-cost reports — confirms that the theoretical-vs-actual variance per outlet has been investigated for material gaps, that all cost-drift events in the period have a corresponding revision or co-approval in the audit trail, and that pricing-history snapshots reconcile to the recipe library state at period boundary.

## 3. Decision Branches

- **Cost drift attributable to a single ingredient vs portfolio drift**: when one ingredient's cost spike caused the drift, the Cost Controller can target the response (ingredient swap, negotiate with vendor, price-only adjustment on the affected recipes). When the drift is portfolio-wide (e.g. seasonal commodity price move affecting many ingredients), the response is broader — category-level target adjustment, menu-engineering review with F&B Ops.
- **Price adjustment vs ingredient revision**: when restoring margin, price adjustment is faster and Cost-Controller-owned (`REC_AUTH_006`), but creates menu-side disruption. Ingredient revision is slower and Chef-owned, but preserves menu pricing. The choice depends on (a) competitive pricing pressure, (b) whether the substitute ingredient meets quality standards, (c) how the cost increase compares to competitors.
- **Co-approve vs request revisions for off-target publish**: the Cost Controller co-approves an off-target publish when (a) the recipe is intentionally strategic-priced (signature dish, loss leader), (b) the alternative (forcing margin compliance) would compromise quality or brand, or (c) market analysis shows competitor pricing supports the chosen price even at lower margin. Otherwise revisions are requested.
- **Direct edit vs Chef escalation**: cost-only edits (target %, price, labor / overhead percentages) are Cost-Controller-owned; ingredient / step / variant edits are Chef-owned. When the boundary blurs (e.g. a portion-size change would fix margin but is an ingredient quantity change), the Cost Controller escalates to the Chef rather than reaching into ingredients.
- **Target adjustment vs accept variance**: at portfolio level, when persistent drift affects many recipes in a category, the Cost Control Department decides whether to raise the category target food-cost % (accept the new cost reality) or hold the target and pursue ingredient / pricing changes across the portfolio. The decision is strategic and is documented in category-level change records.
- **Variance investigation depth**: persistent material variance triggers investigation; transient or small variances are noted but not deeply investigated. The threshold is tenant-configured (e.g. > ฿X per outlet per period, or > N% of theoretical for the period).

## 4. Exit Point / Handoffs

The Cost Controller's involvement on a given recipe / cost concern ends at one of several boundaries:

- **Co-approval recorded** — handoff back to the **Chef** to proceed with publish per `REC_POST_003`; the off-target status is documented in `tb_recipe_version.change_summary`.
- **Revision request issued to Chef** — handoff to the **Chef** with the specific concern (ingredient cost, sub-recipe issue, off-target margin); the Chef revises and re-submits. Cost Controller re-reviews on re-submission.
- **Cost-only edit applied** — recipe stays in current state; `tb_recipe_pricing_history` row written; affected menu items may need price communication via F&B Ops. Cost Controller monitors the recipe for further drift.
- **Variance issue escalated to Chef / Outlet Manager** — Cost Controller raises the issue; subsequent investigation and corrective action sits with the Chef (recipe accuracy) and / or the Outlet Manager (portion-control discipline). The Cost Controller monitors for resolution but does not directly drive it.
- **Category target adjusted** — handoff to **Audit / Config (Sysadmin)** to update `tb_recipe_category.default_cost_settings`; new recipes inherit. The Cost Controller (or Cost Control Department) signs off on the category-level decision.
- **Period-end signoff issued** — handoff to **Audit / Config (Finance + Auditor)** for the period close; the signoff is part of the financial period-close package.

The Cost Controller is in continuous engagement with the recipe module — every ingredient cost movement, every menu-pricing decision, every variance investigation flows through this persona. The "exit" from a given recipe is rare; the engagement is ongoing oversight.

## 5. References

- Parent overview: [03-user-flow.md](./03-user-flow.md) — the canonical lifecycle and the cross-persona handoff table; Section 4 rows "Cost Controller → Chef (co-approve / revise)", "Cost Controller → F&B Ops (price adjustment, menu engineering)", "Cost Controller → Audit / Config (period close)" anchor this persona's exits.
- `../carmen/docs/recipe-module/RECIPE-Overview.md` § Cost Control — carmen/docs source for the Cost Controller's responsibility scope.
- `../carmen/docs/recipe-module/RECIPE-PRD.md` § Cost Control user stories — carmen/docs user stories ("As a cost controller, I want to review recipe costs...", "...update ingredient costs and see the impact on recipe pricing...", "...set target food cost percentages...").
- `../carmen/docs/recipe-module/RECIPE-Business-Requirements.md` § Recipe Costing (`REC_CO_001`–`REC_CO_005`) — feeds the calculation rules the Cost Controller reviews; § Logic Implementation § Cost Calculations is the formal formula set.
- `../carmen/docs/recipe/recipe-management.md` § Recipe Costing Sheet — layout-level reference for the cost summary panel, ingredients costing grid, preparation cost section, yield analysis, pricing section, comparative metrics.
- `../carmen/docs/recipe/gross-profit-dashboard-spec.md` — gross-profit dashboard layout the Cost Controller uses for portfolio review.
- `../carmen/docs/recipe/complete-dashboard-spec.md` — comprehensive dashboard layout for portfolio-level cost oversight.
- Sibling: [03-user-flow-chef.md](./03-user-flow-chef.md) — primary collaboration partner; Chef revises ingredients, Cost Controller reviews / co-approves; cost-only edits stay with Cost Controller.
- Sibling: [03-user-flow-procurement-fb-ops.md](./03-user-flow-procurement-fb-ops.md) — F&B Ops collaborates on price-side adjustments and menu engineering decisions driven by cost-drift findings.
- Sibling: [03-user-flow-outlet-manager.md](./03-user-flow-outlet-manager.md) — variance investigation collaborator; portion-control discipline at the outlet is one input to the theoretical-vs-actual variance.
- Sibling: [03-user-flow-audit-config.md](./03-user-flow-audit-config.md) — Sysadmin sets category defaults that the Cost Controller's target adjustments flow through; Auditor reviews `tb_recipe_pricing_history` timeline and co-approval signatures.
- Sibling: [01-data-model.md](./01-data-model.md) — canonical cost columns on `tb_recipe` (`total_ingredient_cost`, `labor_cost`, `overhead_cost`, `cost_per_portion`, `target_food_cost_percentage`, `actual_food_cost_percentage`, `selling_price`, `gross_margin`, `gross_margin_percentage`); `tb_recipe_pricing_history` as the audit trail for cost / price changes.
- Sibling: [02-business-rules.md](./02-business-rules.md) — `REC_CALC_001`–`REC_CALC_015` (the math the Cost Controller reviews and the basis for drift detection), `REC_AUTH_006`–`REC_AUTH_008` (Cost Controller's authority scope), `REC_POST_010` (pricing-only edit posting effects), `REC_XMOD_005`–`REC_XMOD_006` (costing-module coupling), `REC_XMOD_009` (versioning / audit).
- Related: [[costing]] — upstream of every per-ingredient cost feed; cost-drift events flow from `[[costing]]` to the recipe module per `REC_XMOD_006`.
- Related: [[inventory]] — the theoretical-vs-actual variance dashboard joins recipe-driven theoretical OUT movements with actual stock movements.

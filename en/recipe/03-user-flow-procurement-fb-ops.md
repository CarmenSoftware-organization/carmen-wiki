---
title: Recipe — User Flow — Procurement / F&B Ops
description: Procurement and F&B Operations Manager flow within the recipe module — sizes POs from recipe demand, validates ingredient availability, approves menu-item linkages, signs off menu engineering.
published: true
date: 2026-05-17T11:00:00.000Z
tags: recipe, user-flow, procurement-fb-ops, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T16:00:00.000Z
---

# Recipe — User Flow — Procurement / F&B Ops

> **At a Glance**
> **Persona:** Procurement Department + F&B Operations Manager &nbsp;·&nbsp; **Module:** [[recipe]] &nbsp;·&nbsp; **Workflow stages:** off-path — strategic upstream (menu-item linkage approve) + purchasing downstream (PO sizing) &nbsp;·&nbsp; **Key permissions:** read recipes, approve-menu-link (F&B Ops), raise substitution requests (Procurement)
> **What this persona does:** Procurement sizes POs from recipe demand and surfaces substitution requests; F&B Ops approves menu-item linkages and runs menu engineering.

## 1. Role in This Module

The **Procurement / F&B Ops** persona covers two related operational roles: **Procurement** (consumes recipe demand to inform purchasing — uses recipe explosions × forecast sales to size purchase orders, validates that ingredient availability matches recipe needs, receives substitution requests when an ingredient cannot be sourced) and **F&B Operations Manager** (owns the recipe library at the strategic level — approves new menu items and their recipe linkages per `REC_AUTH_011`, signs off menu engineering against margin and variance data, ensures recipe documentation supports training and audit). Both roles are read-mostly against the recipe library (`recipe:read` per `REC_AUTH_010`); F&B Ops additionally holds the menu-item linkage approval right (`recipe:approve-menu-link` per `REC_AUTH_011`). Procurement does not write to the recipe — they may surface a substitution request to the Chef (operational channel, not a schema write); the Chef remains the author of any ingredient swap or recipe revision. F&B Ops does not write to recipe header / ingredients / steps either — their authority is upstream of the recipe (set strategic direction, approve linkages) and downstream of recipe publication (price-side and menu-side decisions driven by recipe cost data, in collaboration with Cost Controller). From the recipe module's perspective, this persona is the **strategic upstream gate** (F&B Ops on menu-item linkage) and the **purchasing-side downstream consumer** (Procurement on PO sizing).

## 2. Entry Point and Primary Flow

**Entry point:** Five paths into Procurement / F&B Ops work touching the recipe module.

- **Procurement → demand explosion** — aggregate recipe explosions across all outlets × forecast sales over the planning horizon (week / month) produce a portfolio-level ingredient demand; this seeds PO sizing for the central store.
- **Procurement → ingredient availability check** — for each `PUBLISHED` recipe (or a candidate `DRAFT` recipe coming up for approval), validate that the ingredients are reliably sourceable from the current vendor list at the cost the recipe assumes.
- **Procurement → substitution request channel** — when an ingredient is unavailable (vendor stock-out, discontinued, vendor change), surface a substitution request to the Chef for recipe revision.
- **F&B Ops → menu-item linkage approval** — when a Chef has published a new recipe and proposes it for menu-item linkage, F&B Ops reviews the recipe (cost, margin, fit with the menu, brand) and approves or rejects the linkage.
- **F&B Ops → menu engineering review** — periodic (typically quarterly) review of the menu vs the recipe library: which dishes are over-margin (raise the price or drop them), which are under-margin (cost-engineer or drop), which are signature dishes (preserve at any margin).

**Primary flow (10 steps — runs continuously across the procurement and menu-planning calendar):**

1. **(Procurement) Aggregate recipe demand.** For the planning horizon, sum recipe explosions × forecast sales across all outlets. Each menu item → linked recipe(s) → ingredient lines × forecast sold quantity × wastage % × unit conversion → portfolio-level ingredient demand. Sub-recipe lines recurse to leaf-product demand.
2. **(Procurement) Compare against on-hand and in-flight POs.** Net demand for the horizon = projected ingredient demand − central store on-hand − in-flight POs (deliveries expected in horizon) − safety stock. The net demand is the basis for new PO sizing.
3. **(Procurement) Validate ingredient availability.** For each high-volume ingredient, confirm vendor availability at the recipe's assumed cost. If a vendor flags an upcoming stock-out (seasonal product, supply-chain disruption), flag the recipes that depend on the ingredient for substitution planning.
4. **(Procurement) Raise PO(s).** Size POs to meet net demand per vendor, per delivery window. The PO lifecycle is owned by the procurement module (not the recipe module); the recipe is the demand input. Recipe accuracy (especially wastage %, conversion factors, and sub-recipe roll-ups) directly impacts PO sizing accuracy.
5. **(Procurement) Surface substitution request.** When an ingredient is unavailable from the current vendor list, raise a substitution request to the Chef: "Vendor X cannot supply Y in the next N days; candidate substitutes are A / B / C at costs $/$/$. Recipe impact: dishes [list] use Y in quantities [list]." The Chef evaluates the substitute and either revises the recipes (per `REC_POST_004` or `REC_POST_005`) or coordinates a temporary menu pause.
6. **(F&B Ops) Review new recipe proposals.** When a Chef publishes a new recipe and proposes it for menu-item linkage, F&B Ops opens the recipe detail; reviews cost (`cost_per_portion`), margin (`actual_food_cost_percentage`, `gross_margin_percentage`), menu fit (does it complement existing items? does it cannibalise sales of existing items?), brand fit (does it align with the cuisine / concept?), and operational fit (does the kitchen have the equipment, skill, throughput?).
7. **(F&B Ops) Approve or reject menu-item linkage.** Per `REC_AUTH_011`. Approval is recorded outside the recipe schema (in the POS-integration layer or an application-layer mapping); the recipe itself is unchanged. Rejection sends the Chef back to revise (commonly: cost too high, doesn't fit the cuisine, duplicates an existing dish) — the recipe stays `PUBLISHED` but is not linked to a menu item.
8. **(F&B Ops) Run menu engineering review.** Periodically (quarterly), review the menu × recipe cost / margin / variance data. The matrix combines popularity (sales volume) with profitability (margin %): high-margin / high-volume = stars (preserve, promote); high-margin / low-volume = puzzles (consider promotion); low-margin / high-volume = workhorses (cost-engineer to improve margin); low-margin / low-volume = dogs (drop or re-conceive).
9. **(F&B Ops) Coordinate price / cost / recipe decisions.** Menu engineering findings drive collaboration: Cost Controller adjusts prices on workhorses (per `REC_AUTH_006`); Chef revises ingredients on dogs to bring cost down; F&B Ops drops linkages for dishes being retired. The recipe module supports the workflow but the strategic decisions are owned by F&B Ops.
10. **(F&B Ops) Sign off period-end menu performance.** At the end of each menu cycle (quarterly / seasonally), F&B Ops signs off on menu performance: which dishes hit margin / sales targets, which under-performed, which decisions (drop / re-cost / re-price) were made. The signoff is part of the strategic operating package.

## 3. Decision Branches

- **PO size — recipe-driven vs par-level**: Procurement may size POs either by recipe-driven demand explosion (accurate for known production volumes — banquet events, set-menu services) or by par-level top-up (default for a-la-carte where demand is probabilistic). The choice is per ingredient / per outlet; high-value, slow-moving ingredients are typically recipe-driven, fast-moving commodities are typically par-level.
- **Substitution approach**: when an ingredient is unavailable, Procurement may propose (a) a direct substitute (similar ingredient, similar cost — Chef confirms and updates wastage/conversion if needed), (b) a different vendor for the same ingredient (no recipe change), (c) a temporary menu pause on affected dishes (no recipe change, demand temporarily zero). Decision is driven by duration of the supply gap and the affected dishes' importance.
- **Menu-link approval — accept-as-is vs request-revisions**: F&B Ops may approve a proposed recipe linkage (publish proceeds to menu listing), request revisions (cost too high, doesn't fit menu — Chef revises), or reject outright (concept doesn't fit). The threshold for "accept-as-is" depends on tenant tolerance and the strategic priority of the new dish.
- **Menu engineering — drop vs re-cost vs re-price**: for an under-performing dish, F&B Ops decides among (a) drop the menu link entirely (no recipe state change; the recipe stays `PUBLISHED` but is no longer linked to a menu item), (b) coordinate with Chef to re-cost (ingredient revision to bring `cost_per_portion` down), (c) coordinate with Cost Controller to re-price (increase `selling_price` to restore margin). Choice is driven by the dish's role on the menu and brand considerations.
- **Cost-drift escalation path**: when Cost Controller flags portfolio-wide cost drift in a category, F&B Ops decides whether to (a) absorb (preserve menu prices, accept margin reduction), (b) pass through (raise menu prices to restore margin — communication / competitor analysis required), or (c) re-engineer (drive ingredient revisions across the category — Chef-side work). The decision is strategic and impacts the relationship with Cost Controller and Chef.

## 4. Exit Point / Handoffs

The Procurement / F&B Ops persona's involvement on a given recipe / menu cycle ends at one of several boundaries:

- **(Procurement) PO raised** — handoff to the procurement module's PO flow (vendor side, [[purchase-order]]); the recipe demand input is preserved as the rationale for PO sizing; the PO advances independently. Procurement returns to the recipe module on the next planning cycle.
- **(Procurement) Substitution request issued to Chef** — handoff to the **Chef** for evaluation and recipe revision per `REC_POST_004` / `REC_POST_005`. Procurement monitors for recipe update or temporary pause confirmation.
- **(F&B Ops) Menu-item linkage approved** — handoff to the **menu / POS-integration layer** (outside the recipe schema per `REC_XMOD_008`); the recipe is now driving theoretical consumption on menu sales. F&B Ops returns to maintenance mode (menu engineering, periodic review).
- **(F&B Ops) Menu-item linkage rejected** — handoff back to the **Chef** (with feedback) for revision and re-proposal; the recipe remains `PUBLISHED` but is unlinked.
- **(F&B Ops) Menu engineering decision recorded** — handoff to the **affected collaborators**: Chef for ingredient revision, Cost Controller for price adjustment, or [retirement]. The recipe module reflects the resulting changes per the per-collaborator persona's flow.
- **(F&B Ops) Period-end menu signoff** — handoff to **Audit / Config (Finance + Auditor)** for the period close; the signoff is part of the financial / operational period-close package.

Procurement is in continuous engagement with the recipe module — every PO sizing exercise touches recipe demand. F&B Ops is in periodic engagement — at recipe-publish approval moments and at menu-engineering review cycles.

## 5. References

- Parent overview: [03-user-flow.md](./03-user-flow.md) — the canonical lifecycle and the cross-persona handoff table; Section 4 rows "Procurement → Chef (substitution request)", "F&B Ops → Chef (menu-item linkage approval)", "F&B Ops → Cost Controller (price / menu engineering)" anchor this persona's exits.
- `../carmen/docs/recipe-module/RECIPE-Overview.md` (and the wiki index `Roles and Personas` table) — Procurement Department and F&B Operations Manager rows.
- `../carmen/docs/recipe-module/RECIPE-PRD.md` § 6 Integration Requirements (Procurement integration; Cost Control integration) — informs the upstream / downstream coupling.
- Sibling: [03-user-flow-chef.md](./03-user-flow-chef.md) — primary collaboration partner for both sub-roles: Procurement raises substitution requests; F&B Ops approves / rejects menu-item linkages on Chef-published recipes.
- Sibling: [03-user-flow-cost-controller.md](./03-user-flow-cost-controller.md) — F&B Ops collaborates on menu engineering: cost-side decisions are Cost Controller; menu-side decisions are F&B Ops.
- Sibling: [03-user-flow-outlet-manager.md](./03-user-flow-outlet-manager.md) — shares the demand-explosion data (outlet-level demand sums into portfolio-level demand for Procurement); the Outlet Manager's SRs are the per-outlet expression of the same recipe-driven need that Procurement aggregates.
- Sibling: [03-user-flow-audit-config.md](./03-user-flow-audit-config.md) — Sysadmin owns RBAC including the `recipe:approve-menu-link` permission F&B Ops uses; Auditor reviews menu-item linkage approvals as part of audit.
- Sibling: [01-data-model.md](./01-data-model.md) — `tb_recipe.cost_per_portion`, `actual_food_cost_percentage`, `gross_margin_percentage` (the figures F&B Ops reviews at menu-engineering); `tb_recipe_pricing_history` (the timeline of cost / price changes informing menu engineering).
- Sibling: [02-business-rules.md](./02-business-rules.md) — `REC_CALC_014` (theoretical-consumption formula — the demand-explosion math Procurement uses), `REC_AUTH_010`–`REC_AUTH_011` (Procurement / F&B Ops authority scope), `REC_XMOD_008` (menu-item linkage is application-layer, not in the recipe schema).
- Related: [[purchase-order]] — Procurement's primary downstream document; recipe-driven demand sizes the PO.
- Related: [[vendor-pricelist]] — vendor cost data is the upstream input to product cost, which is upstream of recipe cost; vendor changes flow through to recipe-cost drift events.
- Related: [[costing]] — F&B Ops reviews cost data sourced from the costing module via the recipe.

---
title: Recipe — User Flow
description: Recipe lifecycle and persona-specific flow files for the recipe module.
published: true
date: 2026-05-19T23:55:00.000Z
tags: recipe, user-flow, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T16:00:00.000Z
---

# Recipe — User Flow

> **At a Glance**
> **Module:** [recipe](/en/inventory/recipe) &nbsp;·&nbsp; **Personas:** Chef &nbsp;·&nbsp; Cost Controller &nbsp;·&nbsp; Outlet Manager &nbsp;·&nbsp; Procurement / F&B Ops &nbsp;·&nbsp; Audit / Config
> **Workflow lifecycle:** DRAFT → PUBLISHED → ARCHIVED (RBAC-gated, direct transitions; versioning + pricing-history audit trail)
> **Drill into per-persona views below for action-level detail**

## 1. Overview

This page is the **overview entry point** for the user-flow set of the `recipe` module. A recipe is the standardised, costed formula for producing one output of a dish or beverage — a header row in `tb_recipe` together with ingredient lines in `tb_recipe_ingredient`, preparation steps in `tb_recipe_preparation_step`, and (optionally) one or more yield variants in `tb_recipe_yield_variant`. Unlike workflow-driven documents (PR, PO, GRN, SR) where every state transition is gated by a workflow stage and signed off per line, the recipe lifecycle is **direct** — three states (`DRAFT`, `PUBLISHED`, `ARCHIVED`) governed by application-level RBAC and completeness rules, with versioning (`tb_recipe_version`) and pricing-history (`tb_recipe_pricing_history`) as the audit mechanism. The recipe is the **source of truth for what should be consumed when something is sold**: when a `PUBLISHED` recipe is linked to a sold menu item, the inventory layer reads its ingredient lines and posts theoretical OUT movements per [02-business-rules.md](./02-business-rules.md) `REC_XMOD_003`. The recipe module is therefore upstream of every food-cost variance computation and every recipe-driven store requisition.

Section 2 below is the **global state machine** — the canonical list of legal transitions across the three values of `enum_recipe_status`, independent of who acts. Each per-persona file (linked from Section 3) describes that persona's *path through* the state machine — their entry point, the actions available to them, the decision branches they face, and the handoff that ends their involvement. Section 4 then summarises the cross-persona handoffs that stitch the individual paths together. The persona grouping collapses the eight raw carmen/docs personas (Chef / Kitchen Manager, Kitchen Staff, Cost Controller, Cost Control Department, Outlet Manager, Procurement Department, F&B Operations Manager, System Administrator + implicit Auditor) into **five operational roles**: Chef, Cost Controller, Outlet Manager, Procurement / F&B Ops, Audit / Config. Read this overview first to anchor the lifecycle, then drill into the persona file that matches your role.

A note on the absence of workflow: the recipe has no `workflow_id`, no `workflow_history`, no per-stage routing. State transitions are direct API calls gated by RBAC; "approval" of a publish (when tenant policy requires Cost Controller co-approval for off-target margins per `REC_AUTH_007`) is an application-layer flag recorded in `tb_recipe_version.change_summary`, not a workflow stage. So the state machine in Section 2 is comparatively short — three states, a handful of transitions — and the cross-persona handoff table in Section 4 captures the **collaboration moments** that happen alongside the state machine rather than within it.

## 2. Recipe Lifecycle

The recipe status is stored on `tb_recipe.status` and constrained to the three values declared in `enum_recipe_status`: `DRAFT` (initial editable state — the chef is authoring; ingredients, steps, and costing may be incomplete; not eligible for menu-item linkage or theoretical consumption), `PUBLISHED` (recipe is live — all completeness rules pass, eligible for menu-item linkage, drives theoretical consumption on menu sales), and `ARCHIVED` (recipe is retired — readable for audit, excluded from default search, does not drive theoretical consumption on new sales). The transitions below cover the legal moves between them; everything else is rejected by the recipe service. Downstream effects (the theoretical-consumption fan-out per `REC_CALC_014` / `REC_XMOD_003`, the sub-recipe cost cascade per `REC_POST_006`, the pricing-history snapshot per `REC_POST_010`) fire on edits and on publication — see [02-business-rules.md](./02-business-rules.md) Section 5 for posting rules.

| From state | Action | To state | Allowed for | Pre-conditions |
| ---------- | ------ | -------- | ----------- | -------------- |
| `(none)` | create | `DRAFT` | Chef | Chef holds `recipe:create` permission; `code` assigned per tenant numbering policy; `category_id` and `cuisine_id` set; `base_yield > 0` and `base_yield_unit` non-empty. Per `REC_AUTH_001` and `REC_VAL_001`–`REC_VAL_005`. |
| `DRAFT` | save (edit header / lines / steps / variants) | `DRAFT` | Chef (owner) | Save-time validation in [02-business-rules.md](./02-business-rules.md) Section 2 passes (warn-only for some); document remains editable. Cost rollup recomputed per `REC_CALC_001`–`REC_CALC_010` on each save (`REC_POST_002`). |
| `DRAFT` | cost-only edit | `DRAFT` | Cost Controller | Per `REC_AUTH_006`. Edits to `target_food_cost_percentage`, `selling_price`, `labor_cost_percentage`, `overhead_percentage` re-compute the pricing rollup and write a `tb_recipe_pricing_history` row (`REC_POST_010`). |
| `DRAFT` | publish | `PUBLISHED` | Chef | Per `REC_AUTH_003`. All publish-time rules pass (`REC_VAL_015`–`REC_VAL_018`): at least one ingredient, at least one prep step, valid cost rollup, `selling_price > cost_per_portion` if set. Tenant policy may require Cost Controller co-approval when `actual_food_cost_percentage > target + tolerance` (`REC_AUTH_007`). Sets `published_at = now()`, writes `tb_recipe_version` with `version_number = 1`, writes `tb_recipe_pricing_history` row at the publication snapshot (`REC_POST_003`). |
| `DRAFT` | soft-delete | `(deleted)` | Chef (owner) + delete permission | Per `REC_AUTH_014`. Sets `deleted_at = now()`. Row remains; the `(code, name, deleted_at)` unique index permits re-use of the same code+name. |
| `PUBLISHED` | edit ingredient / step (in-place with versioning) | `PUBLISHED` | Chef | Per `REC_AUTH_002` (with tenant policy `edit_published_with_versioning = true`). Edit applies; cost rollup recomputed; a new `tb_recipe_version` row is written; if cost / price changed, a `tb_recipe_pricing_history` row is written (`REC_POST_004`). Sub-recipe cost cascade (`REC_POST_006`) fires if this recipe is used as a sub-recipe elsewhere. |
| `PUBLISHED` | edit ingredient / step (un-publish round-trip) | `DRAFT` | Chef | Per `REC_AUTH_005` (tenant policy: un-publish required for edits). Moves to `DRAFT` for edits; re-publish per `REC_POST_003` writes a new `tb_recipe_version` row. Linked menu items are flagged for review during the un-publish window (the recipe is not eligible to drive theoretical consumption while in `DRAFT`). |
| `PUBLISHED` | cost-only edit | `PUBLISHED` | Cost Controller | Per `REC_AUTH_006` and `REC_POST_010`. Re-compute `suggested_price`, `actual_food_cost_percentage`, `gross_margin`, `gross_margin_percentage`. Write `tb_recipe_pricing_history` row. Recipe stays `PUBLISHED`; no full `tb_recipe_version` snapshot (pricing tracked separately). |
| `PUBLISHED` | archive | `ARCHIVED` | Chef | Per `REC_AUTH_004` and `REC_POST_007`. Sets `status = ARCHIVED`, `archived_at = now()`. Writes a final `tb_recipe_version` row with `change_summary = "archived"`. Recipe is no longer eligible for menu-item linkage or theoretical consumption on subsequent sales; existing menu-item linkages should be severed (application policy). |
| `PUBLISHED` | un-publish | `DRAFT` | Chef | Per `REC_AUTH_005` and `REC_POST_008`. Optional path back to `DRAFT` for revision when in-place editing is not permitted by tenant policy. |
| `ARCHIVED` | (no further status transition normally) | `ARCHIVED` | — | Terminal in normal operation. The archived recipe remains readable for audit; historical theoretical-consumption events in the inventory ledger are preserved. To bring an archived recipe back to active use, clone it into a new `DRAFT` and re-publish. |
| `ARCHIVED` | soft-delete (data hygiene after retention period) | `(deleted)` | Sysadmin (Audit / Config) | Per `REC_AUTH_014`. After retention period (tenant-configured), Sysadmin may soft-delete archived recipes for data hygiene; the row remains for audit. |

## 3. Persona Index

Each persona below has a dedicated drill-down file describing their entry point, primary flow, decision branches, and exit point. Slugs match the five-persona grouping; clicking the link opens the per-persona view. The grouping collapses the eight raw carmen/docs personas into the operational roles below.

- [Chef](./03-user-flow-chef.md) — Chef / Kitchen Manager (+ Kitchen Staff subset). Creates new recipes and revises existing ones — defines ingredients, quantities, wastage, method, yield, equipment, prep / cook times. Maintains sub-recipes and ensures consistency across outlets. Approves recipe publication and revisions, sets standards for plating / portioning / quality. Kitchen Staff subset reads published recipes during service for execution (no edit permission).
- [Cost Controller](./03-user-flow-cost-controller.md) — Cost Controller (+ Cost Control Department). Reviews recipe cost, target food-cost percentage, recommended selling price, gross margin. Monitors cost drift as ingredient prices move, flags out-of-tolerance margins, signs off cost changes affecting menu pricing, runs theoretical-vs-actual variance reports. Cost Control Department owns the portfolio-level costing process, sets category-level food-cost targets, drives versioning approval when ingredient prices materially shift.
- [Outlet Manager](./03-user-flow-outlet-manager.md) — Outlet Manager. Orders ingredients from the central store against recipe demand (often via auto-generated SRs sized by forecast sales × recipes). Monitors outlet food-cost variance against budget, reviews recipes used in the outlet, feeds back portion-control / accuracy issues to the chef.
- [Procurement / F&B Ops](./03-user-flow-procurement-fb-ops.md) — Procurement Department (+ F&B Operations Manager). Procurement uses recipe explosions × forecast sales to size POs and validate ingredient availability; receives substitution requests when an ingredient cannot be sourced. F&B Ops owns the recipe library strategically — approves new menu items + recipe linkages, signs off on menu engineering against margin and variance data.
- [Audit / Config](./03-user-flow-audit-config.md) — System Administrator (+ implicit Auditor). Sysadmin manages recipe-module config (categories, cuisine types, default cost settings, RBAC for creation / editing / approval, integration with inventory / POS / procurement). Auditor (implicit) is read-only for compliance review — `tb_recipe_version` snapshots, `tb_recipe_pricing_history` timeline, audit columns.

## 4. Cross-Persona Handoffs

The table below captures the moments where responsibility for a recipe (or for a recipe-related decision) moves from one persona to another. Each handoff is anchored to the recipe state at the point of transfer or to the event that triggers the handoff.

| From persona | Trigger | To persona | Recipe state at handoff |
| ------------ | ------- | ---------- | ----------------------- |
| Chef | Submits new recipe for publication (off-target margin tenant policy triggered) | Cost Controller | `DRAFT` (publish gated on co-approval; recipe stays `DRAFT` until co-approval recorded) |
| Cost Controller | Co-approves publish OR raises a cost concern | Chef | `DRAFT` (if approved, chef publishes per `REC_POST_003`; if concerns raised, chef revises or removes/swaps ingredients) |
| Chef | Publishes recipe | F&B Ops (for menu-item linkage approval) | `PUBLISHED` (recipe is now linkable to menu items; F&B Ops reviews the linkage proposal per `REC_AUTH_011`) |
| Cost Controller | Detects cost drift on a `PUBLISHED` recipe (ingredient price spike, sub-recipe cascade) | Chef + F&B Ops | `PUBLISHED` (with `actual_food_cost_percentage > target + tolerance`; chef revises ingredients or F&B Ops adjusts price / menu) |
| Outlet Manager | Reports portion-control / recipe-accuracy issue from service | Chef | `PUBLISHED` (recipe stays published; chef investigates, may write a corrective edit per `REC_POST_004`) |
| Procurement | Cannot source an ingredient (vendor stock-out, discontinued) | Chef | `PUBLISHED` (chef proposes substitute ingredient; edit per `REC_POST_004` or `REC_POST_005`) |
| F&B Ops | Decides to retire a menu item | Chef | `PUBLISHED → ARCHIVED` (chef archives the recipe per `REC_POST_007`; menu linkages severed) |
| Sysadmin | Changes category default cost settings or RBAC mapping | All personas (prospective) | Any state (new recipes in the category inherit; existing recipes unchanged unless explicitly re-applied) |
| Auditor | Samples committed recipes for compliance review | (no handoff — read-only) | Any state (audit reads `tb_recipe_version` history, audit columns, pricing history) |
| Recipe module | Auto-generates SR `draft` for planned production event | Outlet Manager (Requester role in [store-requisition](/en/inventory/store-requisition)) | `PUBLISHED` (recipe is the source; the SR is created in the SR module with `info.recipe_id` back-reference) |
| Recipe module | Posts theoretical OUT movements on menu sale | Inventory module (downstream, automatic) | `PUBLISHED` (recipe is the formula source; the inventory layer writes the movement) |

## 5. References

- `../carmen/docs/recipe-module/RECIPE-User-Flow-Diagram.md` — carmen/docs user-flow source: lifecycle diagram, creation flow, search / filter flow, detail-view flow, batch operations, mobile flow, integration flows. Note the carmen/docs diagram shows a two-state lifecycle in some panels and a three-state (`Draft → Published → Archive`) in others — this page follows the canonical Prisma three-state enum.
- `../carmen/docs/recipe-module/RECIPE-Page-Flow.md` — carmen/docs page-flow source: recipe list / detail / create flow, tab navigation, mobile user flow, integration points (inventory, cost control), error-handling flows. Maps onto the chef / cost controller / outlet-manager journeys.
- `../carmen/docs/recipe-module/RECIPE-Overview.md` — module purpose, scope, audience, integration points; the user-roles section informs the persona grouping above.
- `../carmen/docs/recipe-module/RECIPE-PRD.md` — user stories per role (Kitchen Management, Kitchen Staff, Cost Control, General Users); the Section 3 persona index maps onto these stories.
- `../carmen/docs/recipe/recipe-management.md` — layout-level reference for the create / edit page, costing sheet, scaling calculator, preparation page, media gallery, and category management; informs the chef and cost controller flows.
- Sibling: [01-data-model.md](./01-data-model.md) — canonical `enum_recipe_status` and the three-state lifecycle referenced throughout Section 2.
- Sibling: [02-business-rules.md](./02-business-rules.md) Section 5 — posting effects and authorization gates referenced by each row of Section 2.
- Related modules: [product](/en/inventory/product) (recipe ingredients reference products with `is_used_in_recipe = true`), [inventory](/en/inventory/inventory) (recipe usage drives theoretical OUT movements on menu sale; sub-recipes recurse through to leaf-product OUTs), [costing](/en/inventory/costing) (per-ingredient `cost_per_unit` is sourced from the outlet's costing-method valuation), [store-requisition](/en/inventory/store-requisition) (recipes may auto-generate SR drafts for planned production / banquet events via `info.recipe_id`).

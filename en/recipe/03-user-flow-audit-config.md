---
title: Recipe — User Flow — Audit / Config
description: System Administrator + Auditor flow within the recipe module — config (categories, cuisines, RBAC, integration), versioning audit, compliance review.
published: true
date: 2026-05-15T16:00:00.000Z
tags: recipe, user-flow, audit-config, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T16:00:00.000Z
---

# Recipe — User Flow — Audit / Config

## 1. Role in This Module

The **Audit / Config** persona covers two roles that govern the recipe module's correctness, completeness, and configuration: the **System Administrator** (owns the recipe-module configuration — `tb_recipe_category` master data including hierarchy and `default_cost_settings`, `tb_recipe_cuisines` master data, `tb_recipe_equipment_category` and `tb_recipe_equipment` masters, the recipe RBAC mapping `recipe:create / edit / publish / archive / edit-published / edit-cost / approve-menu-link / read / read-history`, the publish-gate tenant policy that decides whether off-target margin publishes require Cost Controller co-approval, and the integration wiring with `[[product]]` / `[[inventory]]` / `[[store-requisition]]` for theoretical-consumption fan-out and SR auto-create) and the **Auditor** (read-only review of recipe history — `tb_recipe_version` snapshots, `tb_recipe_pricing_history` timeline, the per-row audit columns `created_by_id` / `updated_by_id` / `created_at` / `updated_at`, the publication / archive timestamps `published_at` / `archived_at`, the comment thread on each `tb_recipe_version.change_summary` — to confirm controls are operating, off-target publishes are co-approved, and the chain of revisions reconciles to the authority model). Neither role acts on the recipe happy path; they act on the **periphery** — before any recipe exists (config), during the lifecycle (RBAC enforcement, integration health), and after publish (audit trace). The Sysadmin holds full read / write on configuration tables and the RBAC mapping; the Auditor is read-only on the recipe library (`recipe:read` + `recipe:read-history`) and on configuration history. There is no "void" or "admin-cancel" path on the recipe — recipes are not transactional documents; data hygiene on archived recipes is the only delete authority, and it sits with the Sysadmin per `REC_AUTH_014`.

## 2. Entry Point and Primary Flow

**Entry points (one per sub-role):**

- **Sysadmin — Config console** — masters editor for categories, cuisines, equipment; RBAC matrix per role / category; tenant-policy settings for publish-gate, edit-published-with-versioning, sub-recipe substitution policy, recipe → SR auto-create wiring.
- **Sysadmin — Integration health dashboard** — surface state of upstream / downstream coupling: vendor pricelist → product cost → recipe cost-drift chain (`REC_XMOD_005` / `REC_XMOD_006`), recipe → SR auto-create wiring (`REC_XMOD_007`), recipe → inventory theoretical-consumption fan-out (`REC_XMOD_003`).
- **Auditor — Recipe history view** — read-only `tb_recipe_version` browser for any recipe; timeline view; per-version diff (header / ingredients / steps / variants JSON snapshots).
- **Auditor — Pricing-history view** — read-only `tb_recipe_pricing_history` timeline; filter by date, change reason, recipe category.

**Primary flow (oversight / configuration, 10 steps — runs continuously across periods, not per-recipe):**

1. **(Sysadmin) Configure category master at tenant onboarding.** Define `tb_recipe_category` hierarchy (Appetiser / Main / Dessert / Beverage / ...; sub-categories below); set `default_cost_settings` per category (target food-cost %, labor / overhead percentages) which new recipes will inherit at create time. Cost Control Department signs off on the category-level targets.
2. **(Sysadmin) Configure cuisine master.** Populate `tb_recipe_cuisines` with the cuisines the operation serves (Thai / Italian / French / Japanese / fusion), each tagged by `enum_cuisine_region`; populate `popular_dishes` and `key_ingredients` for menu engineering context.
3. **(Sysadmin) Configure equipment master.** Populate `tb_recipe_equipment_category` and `tb_recipe_equipment` with the kitchen equipment catalogue (ovens, sous-vide rigs, mixers, etc.) so chefs can reference equipment in prep-step JSON.
4. **(Sysadmin) Configure RBAC.** Map roles → permissions per category (executive chef = all categories, pastry chef = desserts only, cost controller = cost / pricing fields only); assign users to roles; manage delegations (chef on leave → deputy can publish in their category). The recipe permission set is `recipe:create / edit / publish / archive / edit-published / edit-cost / approve-menu-link / read / read-history`.
5. **(Sysadmin) Configure publish-gate and tenant policies.** Decide whether off-target margin publishes (`actual_food_cost_percentage > target + tolerance`) require Cost Controller co-approval per `REC_AUTH_007`; decide whether edits to `PUBLISHED` recipes apply in-place with versioning (`REC_POST_004`) or require un-publish round-trip (`REC_POST_005`); decide the tenant tolerance band for off-target detection (commonly 2 percentage points).
6. **(Sysadmin) Wire integration hooks.** Confirm the upstream chain (vendor pricelist → product cost → recipe cost-drift event) is firing correctly; confirm the downstream chains — recipe → SR auto-create (`REC_XMOD_007`), recipe → inventory theoretical-consumption (`REC_XMOD_003`), recipe → menu-item linkage (`REC_XMOD_008`) — are operational. Failures in any chain show as integration alerts.
7. **(Sysadmin) Manage masters lifecycle.** Soft-delete cuisines / categories that are no longer in use (`Restrict` FK from `tb_recipe` blocks hard delete; soft delete is the operational pattern); merge duplicate categories; reorder hierarchy. Sysadmin coordinates with Cost Control Department on category-level changes that affect target food-cost %.
8. **(Auditor) Periodic audit sample.** Sample committed `PUBLISHED` recipes across the period; for each, verify: (a) the publish event has a corresponding `tb_recipe_version` row with `published = true` and `change_summary` populated; (b) when actual margin was off-target at publish, a Cost Controller co-approval is recorded in the `change_summary` or signoff log per `REC_AUTH_007`; (c) all edits to `PUBLISHED` recipes wrote a new `tb_recipe_version` row per `REC_POST_004`; (d) all cost / price changes wrote a `tb_recipe_pricing_history` row per `REC_POST_010` with a populated `change_reason`; (e) audit columns reconcile (`created_by_id` is a known user; `updated_by_id` chain is consistent).
9. **(Auditor) Compliance review on cost drift and sub-recipe cascades.** Sample recipes whose `tb_recipe_pricing_history.change_reason` indicates a sub-recipe cascade (`REC_POST_006`) or a cost-drift update from costing (`REC_XMOD_006`); verify the cascade chain is internally consistent (the parent recipe's cost change reconciles to the sub-recipe's cost change and the leaf ingredient's cost change); verify the cascade triggered review actions where the resulting margin moved outside tolerance (Cost Controller signoff or Chef revision).
10. **(All sub-roles) Issue findings and corrective actions.** Sysadmin findings (config gap, RBAC anomaly, integration failure) trigger config corrections. Auditor findings (missing version row, missing co-approval, unreconciled cascade) trigger investigation and process improvements; persistent findings may drive policy changes (tighter publish gate, more granular RBAC, stronger integration health monitoring).

## 3. Decision Branches

- **Tenant policy: in-place vs un-publish for `PUBLISHED` edits**: Sysadmin chooses between (a) `edit_published_with_versioning = true` (edits apply immediately to the `PUBLISHED` recipe; `tb_recipe_version` row written; theoretical consumption uses the new formula from edit timestamp onward) and (b) `edit_published_with_versioning = false` (edits require `PUBLISHED → DRAFT` round-trip; recipe doesn't drive theoretical consumption while in `DRAFT`; safer audit but more operational friction).
- **Tenant policy: off-target tolerance**: Sysadmin sets the tolerance band (e.g. 2 percentage points) for when Cost Controller co-approval is required at publish per `REC_AUTH_007`. Tighter tolerance = more co-approvals (more control friction); looser tolerance = fewer co-approvals (more autonomy for chefs).
- **Category default-cost-settings — broad vs granular**: Sysadmin / Cost Control Department choose between (a) broad per-category settings (one target food-cost % for all Mains) or (b) granular per-sub-category settings (different targets for Premium Mains vs Standard Mains, Bar Snacks vs Sit-Down Snacks). Granular is more accurate but harder to maintain.
- **RBAC scope — category-bound vs full**: Sysadmin chooses whether chefs are scoped to specific categories (Pastry Chef → Desserts only) or have full library access. Category-binding aligns RBAC with operational reality but requires per-category user-role assignments.
- **Soft-delete archived recipes after retention**: Sysadmin decides the retention period for `ARCHIVED` recipes before soft-deleting for data hygiene (commonly multi-year for compliance / audit, then soft-deleted). Soft-deleted rows remain in the database (auditable) but disappear from default queries.
- **Audit findings — system gap vs process gap**: Auditor classifies findings as either system gaps (the recipe module's controls didn't enforce a rule that should have been enforced — e.g. an off-target publish without co-approval — requires code / config fix) or process gaps (the rule was enforced but the process around it is weak — e.g. co-approvals are recorded but not reviewed — requires process / training improvement).

## 4. Exit Point / Handoffs

The Audit / Config persona's involvement does not "end" per recipe — it is ongoing oversight. Individual oversight actions have well-defined handoffs:

- **Sysadmin config change applied** — handoff to **all personas (prospective)**; new categories / cuisines / RBAC rules apply to new recipes from save time onward; existing recipes are not retroactively updated unless explicitly re-applied (manual operation). Coordination with Cost Control Department on cost-setting changes; with F&B Ops on RBAC / permission changes that affect strategic authority.
- **Sysadmin master soft-delete (after Restrict-FK clearance)** — handoff to **Chef** to reassign recipes off the to-be-deleted category / cuisine before delete; once cleared, the master is soft-deleted.
- **Auditor finding — system gap** — handoff to **Sysadmin** for code / config fix; the finding is logged and the fix tracked through tenant change management.
- **Auditor finding — process gap** — handoff to **Cost Control Department / F&B Ops / Chef** for process improvement; the finding may trigger policy review (tighter publish gate, more frequent margin review, training on revision process).
- **Auditor finding — clean audit** — no handoff; the period audit is logged as clean and the next cycle proceeds.
- **Integration health alert** — handoff to **Sysadmin** to investigate the failing chain (vendor → product → recipe cost drift; recipe → SR auto-create; recipe → inventory theoretical OUT); resolution flows back through the affected modules.

The Audit / Config persona is the **safety net** of the recipe module — they do not author recipes, but they configure the rails the other personas run on (categories, cuisines, RBAC, policies), verify that the rails were followed at audit time (versioning, co-approval signatures, cost-drift trace), and ensure the integration with upstream cost data and downstream consumption is healthy.

## 5. References

- Parent overview: [03-user-flow.md](./03-user-flow.md) — the canonical lifecycle and the cross-persona handoff table; Section 4 rows "Sysadmin → all personas (config change)", "Auditor — read-only review" anchor this persona's role.
- `../carmen/docs/recipe-module/RECIPE-Overview.md` § General Users (and the wiki index `System Administrator` row) — carmen/docs source for Sysadmin scope; auditor role is implicit in the audit / compliance context.
- `../carmen/docs/recipe-module/RECIPE-Business-Requirements.md` § Maintenance and Governance — Ownership, Review Process, Change Management; informs the Sysadmin / Auditor responsibilities.
- `../carmen/docs/recipe-module/RECIPE-PRD.md` § Non-Functional Requirements (§ Security, § Scalability) — RBAC, audit logging, multi-location support.
- `../carmen/docs/recipe/setup-pages-spec.md` — page-spec source for the setup / config screens the Sysadmin operates.
- `../carmen/docs/recipe/recipe-management.md` § Recipe Categories Management — layout-level reference for category-master administration.
- Sibling: [03-user-flow-chef.md](./03-user-flow-chef.md) — Sysadmin's category RBAC scopes the chef's library; Auditor reviews the chef's `tb_recipe_version` history.
- Sibling: [03-user-flow-cost-controller.md](./03-user-flow-cost-controller.md) — Sysadmin's category `default_cost_settings` affect the Cost Controller's per-recipe targets; Auditor verifies cost-only edits trigger pricing-history rows.
- Sibling: [03-user-flow-outlet-manager.md](./03-user-flow-outlet-manager.md) — Sysadmin's RBAC scopes outlet-manager read access; Auditor reviews recipe-to-outlet usage as part of variance review.
- Sibling: [03-user-flow-procurement-fb-ops.md](./03-user-flow-procurement-fb-ops.md) — Sysadmin owns the `recipe:approve-menu-link` permission F&B Ops uses; Sysadmin wires the substitution-request channel.
- Sibling: [01-data-model.md](./01-data-model.md) — `tb_recipe_version` (full snapshot audit trail), `tb_recipe_pricing_history` (cost / price timeline), audit columns (`created_by_id`, `updated_by_id`, `published_at`, `archived_at`); master-data tables (`tb_recipe_category`, `tb_recipe_cuisines`, `tb_recipe_equipment_category`, `tb_recipe_equipment`).
- Sibling: [02-business-rules.md](./02-business-rules.md) — `REC_AUTH_007` (Cost Controller co-approval gate), `REC_AUTH_011`–`REC_AUTH_014` (F&B Ops / Sysadmin / Auditor authority), `REC_POST_009` (soft-delete), `REC_XMOD_009`–`REC_XMOD_010` (audit / versioning, RBAC).
- Related: [[product]] — Sysadmin owns the `is_used_in_recipe` flag on products that gates whether a product is eligible as a recipe ingredient.
- Related: [[costing]] — the cost-drift integration chain Sysadmin maintains.
- Related: [[inventory]] — the theoretical-consumption integration chain Sysadmin maintains.
- Related: [[store-requisition]] — the recipe → SR auto-create wiring Sysadmin owns.

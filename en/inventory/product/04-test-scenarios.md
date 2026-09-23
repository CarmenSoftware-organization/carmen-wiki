---
title: Product — Test Scenarios
description: Test cases by persona, cross-persona scenarios, and E2E mapping for product.
published: true
date: '2026-09-22T18:00:00.000Z'
tags: product, test-scenarios, carmen-software
editor: markdown
dateCreated: 2026-05-15T15:30:00.000Z
---

# Product — Test Scenarios

> **At a Glance**
> **Module:** [product](/en/inventory/product) &nbsp;·&nbsp; **Total scenarios:** ~17 cross-persona + ~127 per-persona &nbsp;·&nbsp; **Personas covered:** Product Administrator, Purchaser, Store Keeper
> **Run order:** Audit / Config setup → primary persona happy paths → cross-persona scenarios
> **Each persona's drill-down is `04-test-scenarios-<role>.md`**

> **Executable coverage (2026-09-22):** the e2e repo has **no `100-product.spec.ts`** — `/product-management/product` is a catalog-only row (`📄 catalog`) in `../carmen-inventory-frontend-e2e/docs/test-cases/COVERAGE.md:148`, backed by `docs/test-cases/100-product.md` (52 cases, re-audited against the React form on 2026-09-20). Adjacent screens do have specs: `tests/101-product-category.spec.ts` (23 cases; gap report `docs/test-cases/gaps/101-product-category-gap.md`, 39 uncovered) and `tests/044-eco.spec.ts` (19 cases; `gaps/044-eco-gap.md`, 29 uncovered). This page does not mirror those catalogs.

## 1. Overview

This page is the **overview entry point** for the test-scenarios set of the `product` module. It groups coverage by the three personas (Product Administrator, Purchaser, Store Keeper) and surfaces cross-persona / integration scenarios. The scope is shaped by the **master-data nature** of the module — there is no document `doc_status` workflow with draft / submit / approve gates, no posting event with journal-entry fan-out, no period-end window. Test scenarios therefore concentrate on **CRUD + lifecycle** for the Product Administrator (the wide persona) and **lookup + read-side rules** for the Purchaser and Store Keeper (the narrow consumer personas).

The E2E coverage for this module is **partial and oblique**. The direct Playwright specs are `101-product-category.spec.ts` (23 cases — tree browse plus category / sub-category / item-group CRUD per `docs/user-stories/101-product-category.md`) and `044-eco.spec.ts` (eco-label master, now under `/product-management/eco`); unit management is covered from the Configuration side by `020-unit.spec.ts`. There is still no `100-product.spec.ts` covering product CRUD (the 52-case `docs/test-cases/100-product.md` catalog is documentation only) and no spec covering location-policy / shelf assignment. The bulk of the product module's exercise is indirect — every transactional module spec (PR, PO, GRN, SR, count, recipe, pricelist) consumes the product picker and reads `tb_product` rows, so the consumer-side scenarios are validated through those upstream specs. The Product Administrator's CRUD surface is largely manual / planned testing. Section 5 maps the coverage we do have.

The cross-persona scenarios in Section 4 are the integration layer above the per-persona suites. They describe end-to-end journeys that cross a handoff boundary recorded in [03-user-flow.md](./03-user-flow.md) Section 4 — for example, *Product Administrator creates a new product → Purchaser finds it on the PR picker → Store Keeper scans the barcode during receiving → Product Administrator updates a barcode mismatch flagged via comment*. Section 5 maps the E2E specs back to those journeys; note that many product-side scenarios are exercised only via upstream module specs.

## 2. Personas in Scope

- **Product Administrator**: catalogue owner with full CRUD on `tb_product`, classification chain, units, conversions, location mapping, vendor mapping, and lifecycle transitions. Runs bulk imports / exports. The wide persona.
- **Purchaser**: read-only consumer who looks up products for PR / PO composition. References standard cost, last-receiving cost (derived), unit conversions, and vendor mapping. Posts comments for stale entries or new-product requests. The narrow consumer persona at the procurement layer.
- **Store Keeper**: read-only consumer who scans barcodes during receiving / picking / counting and references per-location stock policy and handling notes. Posts comments for barcode mismatches and operational issues. The narrow consumer persona at the operational floor.

## 3. Persona Test Files

- [Product Administrator scenarios](./04-test-scenarios-product-admin.md)
- [Purchaser scenarios](./04-test-scenarios-purchaser.md)
- [Store Keeper scenarios](./04-test-scenarios-store-keeper.md)

## 4. Cross-Persona / Handoff Scenarios

The table below is the integration layer. Each row spans at least one handoff from [03-user-flow.md](./03-user-flow.md) Section 4 and ends with the system in a steady state. "Personas in order" lists the actors in execution sequence; "Pre-condition" captures the state required to begin; "Expected end state" anchors the catalogue state and consumer-side effect.

| # | Scenario | Personas in order | Pre-condition | Expected end state |
| - | -------- | ----------------- | ------------- | ------------------ |
| 1 | New product created and immediately available to consumers | Product Administrator → Purchaser → Store Keeper | Classification chain (category → sub-category → item-group) exists; base inventory unit exists; tax profile configured on at least one classification level. | `tb_product` row inserted with `product_status_type = active`, `is_active = true`. Order-unit conversions and vendor mapping configured. Purchaser sees the product on the PR picker immediately; Store Keeper scans the barcode during receiving and resolves to the new product. No notification fires; pickers read on demand. |
| 2 | Bulk import — dry-run, fix errors, strict-mode commit | Product Administrator | — | **Not testable — no import exists** (verified 2026-09-22: no import route in `config_products.controller.ts`, no Bruno request, frontend has export only). Kept as a numbered placeholder so downstream references stay stable. |
| 3 | Bulk import — partial-success mode | Product Administrator | — | **Not testable — no import exists** (see Scenario 2). |
| 4 | Standard-cost change above SoD threshold routes for approval | Product Administrator → Cost Controller / Finance | Existing active product; new `standard_cost` is 20% above current (above the tenant SoD threshold). | Change staged in activity log (or hard-blocked depending on workflow config) per `PRD_AUTH_012`; Cost Controller / Finance approves. Change commits; activity log records both submitter and approver. |
| 5 | Deactivate product blocked by open PR / PO line | Product Administrator | Active product; one open `tb_purchase_request_detail` line at `doc_status = in_progress` referencing the product. | Deactivate rejected per `PRD_LIFE_002` with `"Product is referenced by 1 open PR line and cannot be deactivated."`; Product Administrator coordinates with Purchaser to cancel / void the PR (or wait for completion). After PR moves to `completed` / `cancelled`, retry succeeds. |
| 6 | Deactivate product referenced by a published recipe — soft-block with override | Product Administrator → Chef (informational) | Active product; one published recipe references it as an ingredient. | Deactivate soft-blocked per `PRD_LIFE_002`; Product Administrator can override with reason text in activity log. On override, the affected recipe is auto-flagged for review (the Chef receives a notification per the recipe module). Product `product_status_type = inactive`; activity log records override + reason. |
| 7 | Soft-delete with non-zero on-hand | Product Administrator → Store Keeper (informational) | Inactive product; current on-hand at one location is 25 units (derived per `PRD_CALC_009`). | **Design intent vs. live behaviour:** `PRD_LIFE_004` says reject; the live `delete()` has no guard and the soft-delete **succeeds**, leaving 25 units of a deleted product on the ledger (verified 2026-09-22, [02-business-rules](/en/inventory/product/02-business-rules) § 5.1). A test written today must expect success and log the orphaned balance as the finding. |
| 8 | Purchaser flags stale catalogue entry via comment | Purchaser → Product Administrator | Active product with `standard_cost = ฿100`; vendor quote is `฿140` — material divergence; Purchaser cannot find a recent matching pricelist. | Purchaser posts `tb_product_comment` on the product with the vendor quote attachment; Product Administrator picks up from comments queue, validates against current vendor pricelist, updates `standard_cost` (potentially routing for SoD approval per Scenario 4), replies on comment thread. Purchaser re-checks and adds the PR line. |
| 9 | Store Keeper flags barcode mismatch via comment | Store Keeper → Product Administrator | Existing product with `barcode = '8851234567890'` mapped to "Spring Water 500ml". Physical bottle in hand is "Spring Water 1L" with the same barcode. | Store Keeper scans, gets the wrong resolved product, posts comment with photo of physical label. Product Administrator validates (against vendor catalog), realises the 1L variant is missing from the catalogue, creates a new `tb_product` with the correct barcode (the old 500ml product gets a `barcode = null` or a new barcode if the original is wrong). Replies on comment; Store Keeper rescans and resolves correctly. |
| 10 | New product needs an unconfigured unit conversion — Purchaser-blocked | Purchaser → Product Administrator | Active product with order-unit conversions `1 CASE = 12 EACH` only; vendor wants to invoice in `1 PALLET = 48 CASES`. PR picker only shows configured conversions. | Purchaser cannot pick `PALLET` on the PR line per `PRD_XMOD_006`; posts comment requesting the conversion be added. Product Administrator adds the `tb_unit_conversion` row (and the `tb_unit` for `PALLET` if it doesn't exist), validates per `PRD_VAL_010` / `PRD_VAL_011`. Purchaser re-opens picker, sees `PALLET`, adds the line. |
| 11 | Classification re-organisation — prospective propagation | Product Administrator | Existing category "Beverages" with a child sub-category being moved to a different parent category. 50 products are classified under the moved sub-category. | Move commits; cascading-default propagation happens at next-read on each downstream consumer per `PRD_LIFE_010`. Open documents that snapshotted the old tax-profile / deviation values retain their snapshot. New documents read the new effective values. Activity log records the move with affected-product count. |
| 12 | Restore soft-deleted product blocked by code re-use | Product Administrator | Soft-deleted product with `code = 'BVR-001'`; a new product has since been created with the same `code = 'BVR-001'`. | Restore rejected per `PRD_LIFE_009` with `"A live product with code 'BVR-001' already exists. Restore is blocked."` Product Administrator either renames the existing product (rare — disruptive) or restores under a new code (by editing the soft-deleted row's `code` before restore — also disruptive). |
| 13 | Hard-disable (`is_active = false`) — product disappears from all views | Product Administrator | Active product; compliance-mandated removal required (e.g. supplier delisted for non-compliance). | Hard-disable sets `is_active = false` and implicitly `product_status_type = inactive` per `PRD_LIFE_005`. Product hidden from all pickers including admin views; appears only on Auditor read scope and in soft-deleted-row reports. Reversible by re-setting `is_active = true`. |
| 14 | Unit deletion blocked by in-use guard | Product Administrator | Existing `tb_unit` "POUND" with 12 products using it as `inventory_unit_id` and 30 `tb_unit_conversion` rows referencing it. | Delete rejected per `PRD_VAL_017` with `"Unit POUND is in use by 12 products / 30 conversions / N document lines and cannot be deleted."` Product Administrator must migrate the dependent products to a different unit (rare — disruptive; usually requires application-layer migration tooling, not just a one-row edit) before retry. |
| 15 | Audit query — view soft-deleted product history | Auditor | Active and soft-deleted products in the catalogue; Auditor needs to investigate a recall traceability question for a deleted product. | Auditor's read scope includes soft-deleted rows per `PRD_AUTH_011`; query returns the full audit log (create, edits, status transitions, soft-delete event). Cross-reference to historical inventory transactions (which retain the `product_id` reference per `PRD_XMOD_002`) provides recall traceability. No write authority; no state change. |
| 16 | Vendor mapping changes — Purchaser-vendor scope filter update | Product Administrator → Purchaser | Product mapped to Vendor A only; Vendor B is added to the mapping. | New `tb_product_tb_vendor` row inserted with `vendor_id = Vendor B`. Purchaser composing a PO against Vendor B now sees the product on the picker per `PRD_AUTH_006`; PO line saves correctly. |
| 17 | Comment thread — closure | Product Administrator | Open comment thread from Purchaser ("standard cost out of date"). | Product Administrator investigates, updates `standard_cost` (subject to SoD threshold per Scenario 4), replies on the thread with the change summary, closes the thread (or marks as resolved per tenant convention). Activity log records the cost change; comment-thread state is "resolved". |

## 5. E2E Test Mapping

The product module's E2E coverage is **distributed across upstream module specs**, with only one direct spec for category browse. Coverage is therefore evaluated by which upstream specs exercise the product side.

| Spec / describe block | Cross-persona scenarios covered (Section 4) |
| --------------------- | ------------------------------------------- |
| `tests/101-product-category.spec.ts` (23 cases) | Direct coverage of the category-tree UI surface incl. CRUD at all three levels; indirect coverage of Scenario 11 (no re-organisation E2E). |
| `tests/044-eco.spec.ts` (19 cases) | Eco-label master CRUD at `/product-management/eco` (not a scenario above). |
| `tests/301-pr.spec.ts`, `302-…-creator`, `304-…-purchaser` | Indirect coverage of Scenario 1 (Purchaser finds new product on picker), Scenario 10 (unit picker on PR line). Scenario 5 is not observable — no deactivation guard exists. |
| `tests/401-po.spec.ts`, `402-…-purchaser` | Indirect coverage of Scenario 16 (vendor-scope filter on PO picker). |
| `tests/501-grn.spec.ts` | Indirect coverage of Scenario 1 (Store Keeper sees new product during receiving) and of the GRN deviation-limit check that consumes `price_deviation_limit` / `qty_deviation_limit` (`PRD_XMOD_007`). No barcode-scan step exists in the spec. |
| `tests/701-sr.spec.ts` | Indirect coverage of Scenario 1 (Store Keeper picks new product during SR dispatch). |

Gaps relative to Section 4:

- **Scenario 1 (product CRUD)** — no direct E2E spec; the 52-case `docs/test-cases/100-product.md` catalog is the manual checklist. **Scenarios 2, 3 (bulk import)** — feature does not exist.
- **Scenarios 4, 6, 7 (lifecycle gates and SoD-routed cost change)** — the gates are not implemented ([02-business-rules](/en/inventory/product/02-business-rules) § 5.1); any E2E would assert design intent against live behaviour that contradicts it.
- **Scenarios 8, 9, 17 (comment threads — feedback and resolution)** — no E2E for product comments; manual / planned.
- **Scenarios 11, 12 (classification re-org and restore)** — no E2E; manual / planned. The category spec covers view-only.
- **Scenario 13 (hard-disable)** — no E2E; manual / planned.
- **Scenario 14 (unit deletion in-use guard)** — no E2E for unit management; manual / planned.
- **Scenario 15 (audit query on soft-deleted)** — no E2E; manual / planned. Auditor scope typically tested at the admin module level, not per content module.
- **Scenario 16 (vendor-mapping update)** — partially exercised through PO module specs when present.

The gap is structural: the **product module is a master-data backbone** with a CRUD UI but not a workflow document, so E2E specs that test "submit → approve → post" patterns don't apply directly. Comprehensive product-side E2E would require a dedicated `100-product.spec.ts` covering create / edit / lifecycle / import / classification / unit-conversion / location-mapping / vendor-mapping; until then, the per-persona test files catalogue manual / planned coverage.

## 6. References

- `../carmen-inventory-frontend-e2e/tests/101-product-category.spec.ts` (23 cases) + `docs/test-cases/gaps/101-product-category-gap.md` (39) — category tree view and three-level CRUD.
- `../carmen-inventory-frontend-e2e/tests/044-eco.spec.ts` (19 cases) + `docs/test-cases/gaps/044-eco-gap.md` (29) — eco-label master.
- `../carmen-inventory-frontend-e2e/docs/test-cases/100-product.md` (52 cases, catalog only, re-audited 2026-09-20 — records the real tab names General / Unit / Location Assignment / Eco Labels, the locked auto-generated Code, the required-field set, the warning toast on invalid submit, and the Shelf column).
- `../carmen-inventory-frontend-e2e/tests/501-grn.spec.ts` — GRN spec; indirect product-side coverage via the product picker.
- Sibling: [03-user-flow.md](./03-user-flow.md) Section 4 — cross-persona handoffs that drive the integration scenarios above.
- Sibling: [02-business-rules.md](./02-business-rules.md) — validation (`PRD_VAL_*`), calculation (`PRD_CALC_*`), authorization (`PRD_AUTH_*`), lifecycle (`PRD_LIFE_*`), and cross-module (`PRD_XMOD_*`) rules invoked by every scenario above.
- Sibling: [01-data-model.md](./01-data-model.md) — canonical entities (`tb_product`, classification chain, `tb_unit`, `tb_unit_conversion`, `tb_product_location`, `tb_product_tb_vendor`) and enums (`enum_product_status_type`, `enum_unit_type`) referenced throughout.
- Per-persona detail: [Product Administrator](./04-test-scenarios-product-admin.md), [Purchaser](./04-test-scenarios-purchaser.md), [Store Keeper](./04-test-scenarios-store-keeper.md).
- Related: [purchase-request](/en/inventory/purchase-request) / [purchase-order](/en/inventory/purchase-order) / [good-receive-note](/en/inventory/good-receive-note) / [store-requisition](/en/inventory/store-requisition) / [recipe](/en/inventory/recipe) / [vendor-pricelist](/en/inventory/vendor-pricelist) — every transactional module's E2E suite indirectly exercises product master read paths.

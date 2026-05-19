---
title: Product — Test Scenarios
description: Test cases by persona, cross-persona scenarios, and E2E mapping for product.
published: true
date: 2026-05-17T11:00:00.000Z
tags: product, test-scenarios, carmen-software
editor: markdown
dateCreated: 2026-05-15T15:30:00.000Z
---

# Product — Test Scenarios

> **At a Glance**
> **Module:** [[product]] &nbsp;·&nbsp; **Total scenarios:** ~17 cross-persona + ~127 per-persona &nbsp;·&nbsp; **Personas covered:** Product Administrator, Purchaser, Store Keeper
> **Run order:** Audit / Config setup → primary persona happy paths → cross-persona scenarios
> **Each persona's drill-down is `04-test-scenarios-<role>.md`**

## 1. Overview

This page is the **overview entry point** for the test-scenarios set of the `product` module. It groups coverage by the three personas (Product Administrator, Purchaser, Store Keeper) and surfaces cross-persona / integration scenarios. The scope is shaped by the **master-data nature** of the module — there is no document `doc_status` workflow with draft / submit / approve gates, no posting event with journal-entry fan-out, no period-end window. Test scenarios therefore concentrate on **CRUD + lifecycle** for the Product Administrator (the wide persona) and **lookup + read-side rules** for the Purchaser and Store Keeper (the narrow consumer personas).

The E2E coverage for this module is **partial and oblique**. The only direct Playwright spec is `101-product-category.spec.ts` (covering category browse / expand / collapse) — there is no `100-product.spec.ts` covering product CRUD, no `102-unit.spec.ts` covering unit / conversion management, and no `103-product-location.spec.ts` covering location-policy mapping. The bulk of the product module's exercise is indirect — every transactional module spec (PR, PO, GRN, SR, count, recipe, pricelist) consumes the product picker and reads `tb_product` rows, so the consumer-side scenarios are validated through those upstream specs. The Product Administrator's CRUD surface is largely manual / planned testing. Section 5 maps the coverage we do have.

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
| 2 | Bulk import — dry-run, fix errors, strict-mode commit | Product Administrator | CSV / Excel file with 500 product rows; mix of valid and invalid (missing classification, duplicate code, invalid unit). | Dry-run reports row-level validation errors per `PRD_VAL_*`; Product Administrator downloads error report, fixes source, re-runs dry-run until clean. Strict-mode commit inserts all 500 rows in one transaction; `created_by_id` is the Administrator. Activity log records the import job. |
| 3 | Bulk import — partial-success mode | Product Administrator | CSV with 100 rows; 90 valid, 10 invalid. Partial-success mode enabled. | 90 rows commit; 10 rows are reported in the error file with per-row failure reason. `created_by_id` is the Administrator. Subsequent re-import of the corrected 10 rows succeeds. |
| 4 | Standard-cost change above SoD threshold routes for approval | Product Administrator → Cost Controller / Finance | Existing active product; new `standard_cost` is 20% above current (above the tenant SoD threshold). | Change staged in activity log (or hard-blocked depending on workflow config) per `PRD_AUTH_012`; Cost Controller / Finance approves. Change commits; activity log records both submitter and approver. |
| 5 | Deactivate product blocked by open PR / PO line | Product Administrator | Active product; one open `tb_purchase_request_detail` line at `doc_status = in_progress` referencing the product. | Deactivate rejected per `PRD_LIFE_002` with `"Product is referenced by 1 open PR line and cannot be deactivated."`; Product Administrator coordinates with Purchaser to cancel / void the PR (or wait for completion). After PR moves to `completed` / `cancelled`, retry succeeds. |
| 6 | Deactivate product referenced by a published recipe — soft-block with override | Product Administrator → Chef (informational) | Active product; one published recipe references it as an ingredient. | Deactivate soft-blocked per `PRD_LIFE_002`; Product Administrator can override with reason text in activity log. On override, the affected recipe is auto-flagged for review (the Chef receives a notification per the recipe module). Product `product_status_type = inactive`; activity log records override + reason. |
| 7 | Soft-delete blocked by non-zero on-hand | Product Administrator → Store Keeper / Inventory Controller (informational) | Inactive product; current on-hand at one location is 25 units (derived per `PRD_CALC_009`). | Soft-delete rejected per `PRD_LIFE_004` with `"Cannot delete product with non-zero on-hand at Loc-A: 25 units."`; Product Administrator coordinates with Store Keeper / Inventory Controller to drain (transfer or write-off). After drain, retry succeeds. |
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
| [`101-product-category.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/101-product-category.spec.ts) | Indirect coverage of Scenario 11 (classification — view / expand / collapse only; no re-organisation E2E). Direct coverage of the category-tree UI surface. |
| `300-pr.spec.ts` (purchase-request, if present) | Indirect coverage of Scenario 1 (Purchaser finds new product on picker), Scenario 5 (open PR line blocks deactivation — observable from the PR side as the product appearing on the PR), Scenario 10 (unit-conversion picker behaviour on PR line). |
| `400-po.spec.ts` (purchase-order, if present) | Indirect coverage of Scenario 16 (vendor-scope filter on PO picker). |
| [`501-grn.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/501-grn.spec.ts) | Indirect coverage of Scenario 9 (barcode scan during receiving — happy path; the mismatch comment flow is not in the GRN spec), Scenario 1 (Store Keeper sees new product during receiving). |
| `701-sr.spec.ts` (store-requisition) | Indirect coverage of Scenario 1 (Store Keeper picks new product during SR dispatch). |

Gaps relative to Section 4:

- **Scenarios 1, 2, 3 (product CRUD and bulk import)** — no direct E2E spec for product create / edit / import; manual / planned tests.
- **Scenarios 4, 6, 7 (lifecycle gates and SoD-routed cost change)** — no direct E2E for lifecycle transitions; manual / planned.
- **Scenarios 8, 9, 17 (comment threads — feedback and resolution)** — no E2E for product comments; manual / planned.
- **Scenarios 11, 12 (classification re-org and restore)** — no E2E; manual / planned. The category spec covers view-only.
- **Scenario 13 (hard-disable)** — no E2E; manual / planned.
- **Scenario 14 (unit deletion in-use guard)** — no E2E for unit management; manual / planned.
- **Scenario 15 (audit query on soft-deleted)** — no E2E; manual / planned. Auditor scope typically tested at the admin module level, not per content module.
- **Scenario 16 (vendor-mapping update)** — partially exercised through PO module specs when present.

The gap is structural: the **product module is a master-data backbone** with a CRUD UI but not a workflow document, so E2E specs that test "submit → approve → post" patterns don't apply directly. Comprehensive product-side E2E would require a dedicated `100-product.spec.ts` covering create / edit / lifecycle / import / classification / unit-conversion / location-mapping / vendor-mapping; until then, the per-persona test files catalogue manual / planned coverage.

## 6. References

- [`../carmen-inventory-frontend-e2e/tests/101-product-category.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/101-product-category.spec.ts) — only direct product-side E2E spec; covers category tree view, expand / collapse, basic CRUD on categories.
- [`../carmen-inventory-frontend-e2e/tests/501-grn.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/501-grn.spec.ts) — GRN spec; indirect product-side coverage via barcode scan and product picker.
- Sibling: [03-user-flow.md](./03-user-flow.md) Section 4 — cross-persona handoffs that drive the integration scenarios above.
- Sibling: [02-business-rules.md](./02-business-rules.md) — validation (`PRD_VAL_*`), calculation (`PRD_CALC_*`), authorization (`PRD_AUTH_*`), lifecycle (`PRD_LIFE_*`), and cross-module (`PRD_XMOD_*`) rules invoked by every scenario above.
- Sibling: [01-data-model.md](./01-data-model.md) — canonical entities (`tb_product`, classification chain, `tb_unit`, `tb_unit_conversion`, `tb_product_location`, `tb_product_tb_vendor`) and enums (`enum_product_status_type`, `enum_unit_type`) referenced throughout.
- Per-persona detail: [Product Administrator](./04-test-scenarios-product-admin.md), [Purchaser](./04-test-scenarios-purchaser.md), [Store Keeper](./04-test-scenarios-store-keeper.md).
- Related: [[purchase-request]] / [[purchase-order]] / [[good-receive-note]] / [[store-requisition]] / [[recipe]] / [[vendor-pricelist]] — every transactional module's E2E suite indirectly exercises product master read paths.

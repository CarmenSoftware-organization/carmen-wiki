---
title: Inventory Adjustment — Test Scenarios — Store Keeper
description: Test cases for entering a Stock-In / Stock-Out adjustment, which posts immediately regardless of which button is clicked.
published: true
date: 2026-07-15T17:02:22.000Z
tags: inventory-adjustment, test-scenarios, store-keeper, carmen-software
editor: markdown
dateCreated: 2026-05-15T13:00:00.000Z
---

# Inventory Adjustment — Test Scenarios — Store Keeper

> **At a Glance**
> **Persona:** Store Keeper &nbsp;·&nbsp; **Module:** [inventory-adjustment](/en/inventory/inventory-adjustment)
> **Categories:** Happy Path &nbsp;·&nbsp; Validation &nbsp;·&nbsp; Edge Case
> **E2E coverage:** none dedicated to this screen — see [04-test-scenarios.md](./04-test-scenarios.md) § 5

This page captures the test scenarios for entering a Stock-In or Stock-Out document. There is no permission section distinct from any other user of the module (see [02-business-rules.md](./02-business-rules.md) § 4) and no pending/approval state to test — every scenario below ends with the document already `completed` and already posted, or with the create/void call rejected outright.

## 1. Happy Path

| # | Scenario | Pre-condition | Steps | Expected |
| - | -------- | ------------- | ----- | -------- |
| SK-HP-01 | Stock-In for existing product, Average costing | Product `P-1` has on-hand at `LOC-A`, current average cost `฿10.00`. | 1. Add Stock-In. 2. Pick a `stock_in`-direction reason. 3. Pick `LOC-A`. 4. Add line: `P-1`, `qty = 10`; `cost_per_unit` pre-fills to `฿10.00` (editable). 5. Click **Save**. | Document created at `doc_status = completed`; `tb_inventory_transaction` written (`inventory_doc_type = stock_in`); new average recomputed via `calculateNewAverageCost`; on-hand at `(LOC-A, P-1)` increases by 10. |
| SK-HP-02 | Stock-In for existing product, Submit instead of Save | Same as SK-HP-01, but click **Submit** instead of **Save**. | Identical result to SK-HP-01 — both buttons call the same `create()`, and the backend ignores the client-sent `doc_status` (see [03-user-flow.md](./03-user-flow.md) § 2.1). |
| SK-HP-03 | Stock-Out for breakage, FIFO product | FIFO product `P-2` has two lots at `LOC-A`: 5 units at `฿10.00` (`lot_seq_no=1`), 3 units at `฿12.00` (`lot_seq_no=2`). | 1. Add Stock-Out. 2. Pick a `stock_out`-direction reason. 3. Pick `LOC-A`. 4. Add line: `P-2`, `qty = 6` — no cost field is shown. 5. Save. | Document `completed`; `createFifoConsumption` consumes 5 units from the older lot and 1 from the newer, writing two outbound cost-layer rows; `tb_stock_out_detail.cost_per_unit`/`total_cost` remain `0` (never written by `create()` for stock-out). |
| SK-HP-04 | Multi-line document | Two products at the same location, below any on-hand limit. | 1. Add lines for both products. 2. Save. | One header, two detail rows, two (or more) `tb_inventory_transaction_detail` rows under one `tb_inventory_transaction` — one transaction per detail line, not one per document. |
| SK-HP-05 | Fractional quantity at or above 1 | Product with fractional UoM (e.g. kg). | Line `qty = 1.5`. | Accepted — `qty >= 1` passes. Contrast with SK-VAL-02 below. |

## 2. Validation / Error

| # | Scenario | Trigger | Expected error |
| - | -------- | ------- | -------------- |
| SK-VAL-01 | Missing location | Submit with `location_id` empty. | Client rejects before submit is possible (Zod `.min(1)`); a direct API call with an empty `location_id` returns `"Location is required for stock in"` / `"...stock out"`. |
| SK-VAL-02 | Fractional quantity below 1 | Line `qty = 0.5`. | Client rejects with the `minNumber` message — `qty` must be `>= 1`, not merely `> 0`. |
| SK-VAL-03 | No line items | Submit with zero lines. | Client rejects (`atLeastOneItem`); a direct API call with an empty `add` array returns `"Stock in detail items are required"` / `"...out..."`. |
| SK-VAL-04 | Unknown product id | A line references a `product_id` with no matching `tb_product` row (direct API call). | `"Product not found: <id>"` — the whole create is rejected, not just the offending line. |
| SK-VAL-05 | Negative cost on Stock-In | Line `cost_per_unit = -1` (direct API bypass). | Client rejects with the `minZero` message; not applicable to Stock-Out, whose cost field isn't shown and isn't persisted regardless. |
| SK-VAL-06 | Insufficient stock on Stock-Out (Average product) | `qty` requested exceeds current on-hand at the location. | Whole create fails with `"Insufficient stock. Requested: <X>, Available: <Y>"` — surfaced to the user via a special-cased error-toast path (`handleMutationError`) that shows the raw server message. **Confirmed for Average-costed products only** — FIFO behavior under the same condition was not independently confirmed this pass. |
| SK-VAL-07 | Date outside the current period | Date picked before `currentPeriod.start_at` or after `currentPeriod.end_at`. | Client rejects with `dateOutsidePeriod`. **Client-side only** — no equivalent backend check was found. |
| SK-VAL-08 | Blank description | Submit with `description` empty. | Accepted — `description` has a `.max(256)` but no `.min()`; it is optional. |

## 3. Edge Cases

| # | Scenario | Condition | Expected |
| - | -------- | --------- | -------- |
| SK-EDGE-01 | Reason/direction mismatch via direct API | A `tb_stock_in` create call references an `adjustment_type_id` whose `type = stock_out`. | Not confirmed to be rejected server-side — `validateAndEnrichHeader` only checks the row exists, not its `type`. Treat as unverified/likely-accepted pending a direct test against a running backend. |
| SK-EDGE-02 | Direct-cost location via direct API | A create call references a `location_id` whose `location_type` is `direct` (not Inventory/Consignment). | Not confirmed to be rejected server-side — only the picker filters by type client-side. |
| SK-EDGE-03 | Stock-In cost suggestion for a brand-new product/location pair | `useProductCostByLocationQty` has no prior data for the `(product, location)` pair. | Suggested `cost_per_unit` behavior in this case (zero vs blank vs error) was not independently confirmed this pass. |
| SK-EDGE-04 | List-view Delete on a completed document | Click Delete from the row menu → Confirm. | Delete dialog opens (the button always renders); the mutation returns `"Cannot delete a completed Stock In — inventory has already been adjusted"` — a 400, surfaced as an error toast, and the row remains. |
| SK-EDGE-05 | Attempt to reach the Edit or Void button | Open a completed document's detail view. | Neither renders — `isReadOnly` is always true for a persisted document, so the Edit button (`isView && !isReadOnly`) is absent, and Void (requires `isEdit`) is consequently unreachable too. |

## 4. References

- Parent overview: [04-test-scenarios.md](./04-test-scenarios.md) — cross-cutting scenarios (Save vs Submit, Edit/Void dead code, list-Delete-always-fails, void-also-soft-deletes).
- User flow: [03-user-flow-store-keeper.md](./03-user-flow-store-keeper.md).
- Business rules: [02-business-rules.md](./02-business-rules.md) — `ADJ_VAL_001`–`ADJ_VAL_013`, `ADJ_CALC_001`–`ADJ_CALC_007`, `ADJ_POST_001`.
- Cross-link: [inventory](/en/inventory/inventory) — ledger-side effects of every posting.
- Cross-link: [costing](/en/inventory/costing) — FIFO/Average cost resolution.

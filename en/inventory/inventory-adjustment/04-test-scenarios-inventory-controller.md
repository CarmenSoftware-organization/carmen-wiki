---
title: Inventory Adjustment — Test Scenarios — Inventory Controller
description: Test cases for the read-only historical view and the direct-API-only void endpoint — there is no approval queue to test.
published: true
date: 2026-07-15T17:02:22.000Z
tags: inventory-adjustment, test-scenarios, inventory-controller, carmen-software
editor: markdown
dateCreated: 2026-05-15T13:00:00.000Z
---

# Inventory Adjustment — Test Scenarios — Inventory Controller

> **At a Glance**
> **Persona:** Inventory Controller (same permission/screen as Store Keeper) &nbsp;·&nbsp; **Module:** [inventory-adjustment](/en/inventory/inventory-adjustment)
> **Categories:** Happy Path (read-only + direct-API void) &nbsp;·&nbsp; Edge Case
> **E2E coverage:** none — see [04-test-scenarios.md](./04-test-scenarios.md) § 5

This page previously catalogued ~30 approval/threshold/count-rollup scenarios for a Controller review queue that does not exist (see [03-user-flow-inventory-controller.md](./03-user-flow-inventory-controller.md)). What remains testable for this persona is: (a) the identical create flow already covered in [04-test-scenarios-store-keeper.md](./04-test-scenarios-store-keeper.md), (b) the read-only list/detail/print views, and (c) the real void endpoint, which is only reachable via a direct API call since its UI trigger never renders.

## 1. Happy Path

| # | Scenario | Pre-condition | Steps | Expected |
| - | -------- | ------------- | ----- | -------- |
| IC-HP-01 | Read the posted document list | At least one Stock-In and one Stock-Out exist. | 1. Open Inventory Adjustment list. 2. Filter by type / status / date / search. | List renders both types merged (via the gateway's `inventory-adjustments` endpoint, which fetches all rows from both the stock-ins and stock-outs microservices and merges/sorts/paginates in memory). |
| IC-HP-02 | Void a document via direct API call | A `completed` `tb_stock_in` at `LOC-A` for `P-1 qty=10`; sufficient on-hand at `(LOC-A, P-1)` to reverse it. | Direct `PATCH` to the stock-in endpoint with `doc_status: "voided"`, `void_reason`, and the current `doc_version` (the same payload `useVoidInventoryAdjustment` would send, if its UI trigger were reachable). | `voidStockIn()` runs: checks not-already-voided, checks sufficient on-hand to reverse, writes a reversing `executeAdjustmentOut` call per line, then sets `doc_status = voided` **and** `deleted_at` on the header in the same update. The document then disappears from the list and detail endpoints (both filter `deleted_at: null`). |
| IC-HP-03 | Print a posted document | Any `completed` document. | Open detail → click **Print**. | Routes to the FastReport viewer via `inventory-adjustments.print-to-report`; the button always renders in view mode (`canPrint = isView && !!id`). |
| IC-HP-04 | Attempt to void a document with insufficient on-hand to reverse | A `completed` `tb_stock_in` for `P-1 qty=10` at `LOC-A`, but on-hand at `(LOC-A, P-1)` has since dropped to 4 (consumed by later postings). | Direct void call. | Rejected: `"Cannot void: product P-1 has insufficient on-hand qty (4) at this location to reverse 10"` — confirmed for the stock-in void path; the stock-out void path's equivalent guard was not independently confirmed this pass. |
| IC-HP-05 | Attempt to void an already-voided document | Document already `doc_status = voided`. | Direct void call again. | Rejected: `"Stock in is already voided"` / `"Stock out is already voided"`. |

## 2. Edge Cases

| # | Scenario | Condition | Expected |
| - | -------- | --------- | -------- |
| IC-EDGE-01 | Void button unreachable in the UI | Open any `completed` document's detail view, click **Edit**. | The Edit button does not render (`isView && !isReadOnly` is false, since `isReadOnly` is always true for `completed`/`voided`), so edit mode is never entered and the Void button (which requires `isEdit`) never appears either. |
| IC-EDGE-02 | List-view Delete on a completed document | Click Delete from the row menu. | Same as SK-EDGE-04 in the Store Keeper scenarios: always renders, always fails server-side with a 400. |
| IC-EDGE-03 | Voided document disappears from reporting | After a successful direct-API void. | The document is gone from both the list and detail endpoints (they filter `deleted_at: null`, and void sets it) — there is no "Voided" badge state visible anywhere in the UI for this module, unlike GRN/PO/SR where a void leaves a visible, badge-flagged row. |

## 3. References

- Parent overview: [04-test-scenarios.md](./04-test-scenarios.md).
- User flow: [03-user-flow-inventory-controller.md](./03-user-flow-inventory-controller.md).
- Business rules: [02-business-rules.md](./02-business-rules.md) `ADJ_POST_004` (void), `ADJ_VAL_012` (void preconditions).
- Cross-link: [inventory](/en/inventory/inventory) — the ledger effect of both posting and void.
